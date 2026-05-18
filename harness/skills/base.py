"""
BaseSkill - 所有技能的基类
实现可拆卸性原则，统一技能接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

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
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
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
