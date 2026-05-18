"""
LogExtractionSkill - 日志提取和解析技能
可插拔的技能模块，支持多种日志格式
"""
import os
from typing import Dict, Any, List
from .base import BaseSkill, SkillResult
from log_analyzer.extractor.extractor import LogExtractor
from log_analyzer.bugreport.bugreport_parser import BugReportParser

class LogExtractionSkill(BaseSkill):
    """日志提取和解析技能"""
    
    @property
    def name(self) -> str:
        return "log_extraction"
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["log_path"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        log_path = inputs["log_path"]
        
        try:
            # 1. 解压和提取
            extractor = LogExtractor()
            extract_dir = extractor.extract(log_path)
            
            # 2. 解析日志
            parser = BugReportParser(extract_dir)
            log_entries = parser.parse_all()
            metadata = parser.extract_metadata()
            
            result = {
                "extraction_dir": extract_dir,
                "log_count": len(log_entries),
                "metadata": metadata,
                "log_files": [str(f) for f in parser.log_files]
            }
            
            return SkillResult(
                True,
                result,
                f"成功提取并解析 {len(log_entries)} 条日志"
            )
            
        except Exception as e:
            return SkillResult(
                False,
                {},
                f"日志提取失败: {str(e)}"
            )
