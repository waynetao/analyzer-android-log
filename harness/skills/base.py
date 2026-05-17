"""
BaseSkill - 所有技能的基类
实现可拆卸性原则，统一技能接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any

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
