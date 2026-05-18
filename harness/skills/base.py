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

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

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
            self.model = model or os.environ.get(f"LLM_{scene.upper()}_MODEL") or os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            self.temperature = float(os.environ.get(f"LLM_{scene.upper()}_TEMPERATURE", os.environ.get("LLM_TEMPERATURE", "0.7")))
            self.max_tokens = int(os.environ.get(f"LLM_{scene.upper()}_MAX_TOKENS", os.environ.get("LLM_MAX_TOKENS", "2000")))
        else:
            # 无场景时使用通用配置
            self.api_key = api_key or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
            self.base_url = base_url or os.environ.get("LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL", "")
            self.model = model or os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
            self.temperature = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
            self.max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "2000"))
        
        self.client: Optional[Any] = None
        self.use_mock = True
        
        self._init_llm_client()
    
    def _init_llm_client(self) -> None:
        """初始化LLM客户端"""
        if HAS_OPENAI and self.api_key:
            try:
                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self.client = OpenAI(**kwargs)
                self.use_mock = False
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")
                self.use_mock = True
