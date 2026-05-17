"""
ValidationPolicy - 输入输出验证策略
Harness Engineering 架构约束实现
"""
from typing import Dict, Any
from .base import BasePolicy, ValidationResult

class ValidationPolicy(BasePolicy):
    """输入输出验证策略"""
    
    @property
    def name(self) -> str:
        return "validation"
    
    def validate_input(self, inputs: Dict[str, Any]) -> ValidationResult:
        """验证输入"""
        required_fields = ["bug_description", "log_path"]
        missing = []
        
        for field in required_fields:
            if field not in inputs:
                missing.append(field)
        
        if missing:
            return ValidationResult(
                False,
                f"缺少必需字段: {', '.join(missing)}",
                ["请确保提供 bug_description 和 log_path"]
            )
        
        # 验证日志路径
        log_path = inputs.get("log_path", "")
        import os
        if not os.path.exists(log_path):
            return ValidationResult(
                False,
                f"日志路径不存在: {log_path}",
                ["请检查日志文件路径是否正确"]
            )
        
        return ValidationResult(
            True,
            "输入验证通过"
        )
    
    def validate_output(self, outputs: Dict[str, Any]) -> ValidationResult:
        """验证输出"""
        required_outputs = ["log_extraction", "bug_analysis", "report_generation"]
        
        missing_outputs = []
        for output in required_outputs:
            if output not in outputs:
                missing_outputs.append(output)
        
        if missing_outputs:
            return ValidationResult(
                False,
                f"缺少输出: {', '.join(missing_outputs)}"
            )
        
        # 验证报告生成
        report_output = outputs.get("report_generation", {})
        if not report_output.get("success", False):
            return ValidationResult(
                False,
                "报告生成失败"
            )
        
        return ValidationResult(
            True,
            "输出验证通过"
        )
