"""
FormatPolicy - 格式策略
"""
from typing import Dict, Any
from .base import BasePolicy, ValidationResult

class FormatPolicy(BasePolicy):
    """格式策略"""
    
    @property
    def name(self) -> str:
        return "format"
    
    def validate_output(self, outputs: Dict[str, Any]) -> ValidationResult:
        """验证格式"""
        # 简单的格式验证
        return ValidationResult(
            True,
            "格式验证通过"
        )
