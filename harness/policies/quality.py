"""
QualityPolicy - 质量策略
"""
from typing import Dict, Any
from .base import BasePolicy, ValidationResult

class QualityPolicy(BasePolicy):
    """质量检查策略"""
    
    @property
    def name(self) -> str:
        return "quality"
    
    def validate_output(self, outputs: Dict[str, Any]) -> ValidationResult:
        """验证质量"""
        issues = []
        
        log_extraction = outputs.get("log_extraction", {}).get("data", {})
        if log_extraction.get("log_count", 0) == 0:
            issues.append("日志数量为0，请检查日志文件")
        
        bug_analysis = outputs.get("bug_analysis", {}).get("data", {})
        total_issues = sum([
            bug_analysis.get("crashes", 0),
            bug_analysis.get("anrs", 0),
            bug_analysis.get("low_memory", 0),
            bug_analysis.get("exceptions", 0)
        ])
        
        if total_issues == 0:
            return ValidationResult(
                True,
                "未发现严重问题，质量良好"
            )
        elif total_issues < 5:
            return ValidationResult(
                True,
                f"发现 {total_issues} 个问题，质量尚可"
            )
        else:
            return ValidationResult(
                True,
                f"发现 {total_issues} 个问题，建议优先修复"
            )
