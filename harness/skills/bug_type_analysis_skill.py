"""
BugTypeAnalysisSkill - Bug类型差异化分析Skill
根据不同Bug类型使用不同的提示词和输出模板
"""
from typing import Dict, Any
import sys
import os
sys.path.insert(0, '/workspace')

from harness.skills.base import BaseSkill, SkillResult
from harness.core.feature_flags import FeatureSDK


class BugTypeAnalysisSkill(BaseSkill):
    """Bug类型差异化分析Skill - 检测Bug类型并准备差异化分析数据"""
    
    @property
    def name(self) -> str:
        return "bug_type_analysis"
    
    def __init__(self):
        self.feature_sdk = FeatureSDK()
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """执行分析 - 主要是检测Bug类型，为LLMAnalysisSkill做准备"""
        valid, msg = self._validate_inputs(inputs, ["bug_description", "advanced_log_analysis"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        bug_desc = inputs.get("bug_description", {})
        log_analysis = inputs.get("advanced_log_analysis", {}).get("data", {})
        
        try:
            from harness.skills.bug_type import PromptTemplateManager, BugType
            
            enabled = self.feature_sdk.is_enabled("bug_type_optimization_enabled")
            
            if not enabled:
                # Feature Flag关闭
                return SkillResult(
                    True,
                    {"enabled": False},
                    "Bug类型差异化优化已禁用"
                )
            
            # 检测Bug类型
            bug_type = PromptTemplateManager.detect_bug_type(log_analysis)
            analyzer = PromptTemplateManager.get_analyzer(bug_type)
            
            result = {
                "enabled": True,
                "bug_type": bug_type.value,
                "analyzer_used": analyzer.name if analyzer else None,
                "description": bug_desc.get("raw_text", "")
            }
            
            return SkillResult(
                True,
                result,
                f"Bug类型检测完成: {bug_type.value}"
            )
        except Exception as e:
            return SkillResult(False, {}, f"Bug类型检测失败: {str(e)}")
