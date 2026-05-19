"""
Token 统计管理器
用于跟踪和统计 LLM 的 Token 使用情况
"""
import os
import json
import threading
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict

from harness.core.logging import get_logger
from harness.core.paths import OUTPUTS_TOKEN_STATS_DIR_STR

logger = get_logger(__name__)


@dataclass
class TokenUsage:
    """Token 使用记录"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    timestamp: str = ""
    scene: Optional[str] = None  # 场景，如 'analysis', 'bug_parser'
    skill: Optional[str] = None  # 技能名称

    def add(self, prompt: int, completion: int):
        """累加 Token 使用"""
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.total_tokens += prompt + completion


class TokenStatsManager:
    """Token 统计管理器"""

    _instance: Optional['TokenStatsManager'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化"""
        if hasattr(self, '_initialized'):
            return

        with self._lock:
            if hasattr(self, '_initialized'):
                return

            self._storage_dir = os.environ.get(
                "TOKEN_STATS_DIR",
                OUTPUTS_TOKEN_STATS_DIR_STR
            )
            os.makedirs(self._storage_dir, exist_ok=True)

            self._session_stats: Dict[str, TokenUsage] = {}
            self._total_stats = TokenUsage()

            self._load_history()

            self._initialized = True
            logger.info("TokenStatsManager 初始化完成")

    def set_workflow_dir(self, workflow_id: str):
        """切换到 workflow 专属存储目录"""
        from .paths import WorkflowPaths
        wp = WorkflowPaths(workflow_id)
        wp.ensure_dirs()
        self._storage_dir = wp.analytics_dir_str
        os.makedirs(self._storage_dir, exist_ok=True)
        logger.info(f"TokenStats 切换到 workflow 目录: {self._storage_dir}")

    def record_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
        scene: Optional[str] = None,
        skill: Optional[str] = None
    ):
        """
        记录一次 Token 使用
        
        Args:
            prompt_tokens: 提示词 Token 数量
            completion_tokens: 完成内容 Token 数量
            model: 使用的模型名称
            scene: 场景（可选）
            skill: 技能名称（可选）
        """
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=model,
            timestamp=datetime.now().isoformat(),
            scene=scene,
            skill=skill
        )

        # 更新会话统计
        key = self._get_key(scene, skill)
        if key not in self._session_stats:
            self._session_stats[key] = TokenUsage(
                model=model,
                scene=scene,
                skill=skill
            )

        self._session_stats[key].add(prompt_tokens, completion_tokens)
        self._total_stats.add(prompt_tokens, completion_tokens)

        logger.debug(
            f"Token 使用记录: {key} - "
            f"prompt={prompt_tokens}, completion={completion_tokens}, total={usage.total_tokens}"
        )

    def _get_key(self, scene: Optional[str], skill: Optional[str]) -> str:
        """生成统计键"""
        if scene and skill:
            return f"{scene}:{skill}"
        elif scene:
            return scene
        elif skill:
            return skill
        else:
            return "global"

    def get_session_stats(self) -> Dict[str, TokenUsage]:
        """获取当前会话统计"""
        return self._session_stats.copy()

    def get_total_stats(self) -> TokenUsage:
        """获取总统计"""
        return self._total_stats

    def get_scene_stats(self, scene: str) -> Optional[TokenUsage]:
        """获取指定场景的统计"""
        return self._session_stats.get(scene)

    def get_skill_stats(self, skill: str) -> Optional[TokenUsage]:
        """获取指定技能的统计"""
        for key, stats in self._session_stats.items():
            if stats.skill == skill:
                return stats
        return None

    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        summary = {
            "total": asdict(self._total_stats),
            "by_scene": {},
            "by_skill": {},
            "by_model": {}
        }

        # 按场景分组
        for key, stats in self._session_stats.items():
            if stats.scene:
                if stats.scene not in summary["by_scene"]:
                    summary["by_scene"][stats.scene] = TokenUsage()
                summary["by_scene"][stats.scene].add(
                    stats.prompt_tokens, stats.completion_tokens
                )

            # 按技能分组
            if stats.skill:
                if stats.skill not in summary["by_skill"]:
                    summary["by_skill"][stats.skill] = TokenUsage()
                summary["by_skill"][stats.skill].add(
                    stats.prompt_tokens, stats.completion_tokens
                )

            # 按模型分组
            if stats.model:
                if stats.model not in summary["by_model"]:
                    summary["by_model"][stats.model] = TokenUsage()
                summary["by_model"][stats.model].add(
                    stats.prompt_tokens, stats.completion_tokens
                )

        # 转换为字典
        summary["by_scene"] = {k: asdict(v) for k, v in summary["by_scene"].items()}
        summary["by_skill"] = {k: asdict(v) for k, v in summary["by_skill"].items()}
        summary["by_model"] = {k: asdict(v) for k, v in summary["by_model"].items()}

        return summary

    def estimate_cost(self) -> Dict[str, float]:
        """
        估算成本（基于常见模型价格）
        
        注意：这只是估算，实际成本可能因 API 提供商而异
        """
        # 常见模型的价格（美元 / 1K tokens）
        # 参考价：GPT-4o: $0.015/1K input, $0.06/1K output
        # GPT-4o-mini: $0.0015/1K input, $0.006/1K output
        price_ranges = {
            "gpt-4o": {"input": 0.015, "output": 0.06},
            "gpt-4o-mini": {"input": 0.0015, "output": 0.006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.006},
            "glm-4": {"input": 0.01, "output": 0.03},
            "glm-4-flash": {"input": 0.001, "output": 0.003},
            "qwen-plus": {"input": 0.004, "output": 0.012},
            "default": {"input": 0.01, "output": 0.03}
        }

        total_cost = 0.0

        # 按模型估算
        summary = self.get_summary()
        for model, stats in summary["by_model"].items():
            price = None
            for key in price_ranges:
                if key in model.lower():
                    price = price_ranges[key]
                    break

            if not price:
                price = price_ranges["default"]

            input_cost = (stats["prompt_tokens"] / 1000) * price["input"]
            output_cost = (stats["completion_tokens"] / 1000) * price["output"]
            total_cost += input_cost + output_cost

        return {
            "estimated_cost_usd": round(total_cost, 4),
            "estimated_cost_cny": round(total_cost * 7.2, 4)
        }

    def save_session(self, filename: Optional[str] = None):
        """保存当前会话统计"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"token_stats_{timestamp}.json"

        filepath = os.path.join(self._storage_dir, filename)

        data = {
            "session_start": self._total_stats.timestamp,
            "session_end": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "estimated_cost": self.estimate_cost()
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Token 统计已保存: {filepath}")
        except Exception as e:
            logger.error(f"保存 Token 统计失败: {e}")

    def _load_history(self):
        """加载历史统计（可选）"""
        # 暂不加载历史统计，每次会话重新开始
        pass

    def reset(self):
        """重置统计"""
        self._session_stats.clear()
        self._total_stats = TokenUsage()
        self._total_stats.timestamp = datetime.now().isoformat()
        logger.info("Token 统计已重置")


def get_token_stats() -> TokenStatsManager:
    """获取 Token 统计管理器实例"""
    return TokenStatsManager()
