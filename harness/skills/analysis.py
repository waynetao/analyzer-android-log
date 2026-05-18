"""
BugAnalysisSkill - 问题分析技能
负责日志清洗、异常检测和分析
"""
from typing import Dict, Any
from .base import BaseSkill, SkillResult
from log_analyzer.extractor.extractor import LogExtractor
from log_analyzer.bugreport.bugreport_parser import BugReportParser
from log_analyzer.cleaner.log_cleaner import LogCleaner
from log_analyzer.analyzer.log_analyzer import LogAnalyzer

class BugAnalysisSkill(BaseSkill):
    """问题分析技能"""
    
    @property
    def name(self) -> str:
        return "bug_analysis"
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["log_path"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        log_path = inputs["log_path"]
        
        try:
            # 重新解析日志
            extractor = LogExtractor()
            extract_dir = extractor.extract(log_path)
            parser = BugReportParser(extract_dir)
            log_entries = parser.parse_all()
            
            # 1. 清洗日志
            cleaner = LogCleaner(log_entries)
            cleaned_logs = cleaner.clean_all()
            
            # 2. 分析日志
            analyzer = LogAnalyzer(cleaned_logs)
            analysis_result = analyzer.analyze()
            
            # 3. 整理结果
            result = {
                "crashes": len(getattr(analysis_result, 'crashes', [])),
                "anrs": len(getattr(analysis_result, 'anrs', [])),
                "low_memory": len(getattr(analysis_result, 'low_memory', [])),
                "exceptions": len(getattr(analysis_result, 'exceptions', [])),
            }
            
            return SkillResult(
                True,
                result,
                f"分析完成: 发现 {result['crashes']} 个崩溃, {result['anrs']} 个ANR"
            )
            
        except Exception as e:
            return SkillResult(
                False,
                {},
                f"分析失败: {str(e)}"
            )
