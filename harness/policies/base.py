"""
BasePolicy - 所有策略的基类
架构约束的机械性执行
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ValidationResult:
    passed: bool
    details: str
    suggestions: list = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

class BasePolicy(ABC):
    """策略基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    def validate_input(self, inputs: Dict[str, Any]) -> ValidationResult:
        """验证输入（可选实现）"""
        return ValidationResult(True, "默认通过")
    
    def validate_output(self, outputs: Dict[str, Any]) -> ValidationResult:
        """验证输出（可选实现）"""
        return ValidationResult(True, "默认通过")
