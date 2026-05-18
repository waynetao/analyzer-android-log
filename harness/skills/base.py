"""
BaseSkill - 所有技能的基类
实现可拆卸性原则，统一技能接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
import os

from harness.core.logging import get_logger

logger = get_logger(__name__)

# 延迟导入 LLMClient 以避免循环导入
_LLMClient = None

def _get_llm_client():
    """延迟获取 LLMClient 类"""
    global _LLMClient
    if _LLMClient is None:
        from log_analyzer.llm.llm_client import LLMClient as _LC
        _LLMClient = _LC
    return _LLMClient

@dataclass
class SkillResult:
    success: bool
    data: Dict[str, Any]
    message: str = ""

class BaseSkill(ABC):
    """技能基类 - 所有技能必须实现此接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass
    
    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """执行技能"""
        pass
    
    def _validate_inputs(self, inputs: Dict[str, Any], required_keys: list) -> tuple[bool, str]:
        """验证输入是否包含必需字段"""
        for key in required_keys:
            if key not in inputs:
                return False, f"缺少必需参数: {key}"
        return True, "OK"


class LLMBasedSkill(BaseSkill):
    """LLM技能基类 - 封装通用的LLM初始化逻辑"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None, scene: str = None):
        """
        初始化LLM技能
        
        Args:
            api_key: LLM API Key（可选，优先使用）
            base_url: LLM Base URL（可选，优先使用）
            model: LLM 模型名称（可选，优先使用）
            scene: 场景名称（用于从环境变量读取场景特定配置）
                   例如: "analysis", "bug_parser", "report"
        """
        self.scene = scene
        
        # 支持场景特定配置 + LLM_ 前缀 + OPENAI_ 前缀（向后兼容）
        if scene:
            # 场景特定配置优先级最高
            self.api_key = api_key or os.environ.get(f"LLM_{scene.upper()}_API_KEY") or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
            self.base_url = base_url or os.environ.get(f"LLM_{scene.upper()}_BASE_URL") or os.environ.get("LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL", "")
            self.model = model or os.environ.get(f"LLM_{scene.upper()}_MODEL") or os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL")
            self.temperature = float(os.environ.get(f"LLM_{scene.upper()}_TEMPERATURE", os.environ.get("LLM_TEMPERATURE", "0.7")))
            self.max_tokens = int(os.environ.get(f"LLM_{scene.upper()}_MAX_TOKENS", os.environ.get("LLM_MAX_TOKENS", "2000")))
        else:
            # 无场景时使用通用配置
            self.api_key = api_key or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
            self.base_url = base_url or os.environ.get("LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL", "")
            self.model = model or os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL")
            self.temperature = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
            self.max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "2000"))
        
        self.client: Optional[Any] = None
        self.use_mock = True
        
        self._init_llm_client()
    
    def _init_llm_client(self) -> None:
        """初始化LLM客户端"""
        try:
            LLMClient = _get_llm_client()
            if LLMClient:
                self.client = LLMClient(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    model=self.model
                )
                self.use_mock = self.client.use_mock
        except Exception as e:
            logger.warning(f"Failed to initialize LLM client: {e}")
            self.use_mock = True
    
    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        调用 LLM，自动传递场景和技能名称用于 Token 统计
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
        
        Returns:
            LLM 响应内容
        """
        if not self.client:
            return self._mock_response(system_prompt, user_prompt)
        
        return self.client.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            scene=self.scene,
            skill=self.name
        )
    
    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        """模拟响应，用于开发测试（向后兼容）"""
        return "模拟响应"
