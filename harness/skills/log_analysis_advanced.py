"""
AdvancedLogAnalysisSkill - 高级日志分析技能
提取关键日志片段、设备状态变化，供LLM深度分析
集成日志类型知识库，根据 Bug 类型智能调整提取策略
"""
import os
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from .base import BaseSkill, SkillResult
from log_analyzer.extractor.extractor import LogExtractor
from log_analyzer.bugreport.bugreport_parser import BugReportParser
from log_analyzer.cleaner.log_cleaner import LogCleaner
from log_analyzer.analyzer.log_analyzer import LogAnalyzer, AnalysisResult
from log_analyzer.knowledge.log_type_knowledge import LogTypeKnowledgeBase

logger = logging.getLogger(__name__)


class AdvancedLogAnalysisSkill(BaseSkill):
    """高级日志分析技能 - 提取高质量日志片段"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._knowledge = LogTypeKnowledgeBase()
    
    @property
    def name(self) -> str:
        return "advanced_log_analysis"
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["log_path"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        log_path = inputs["log_path"]
        bug_desc = inputs.get("bug_description", {})
        bug_raw_text = bug_desc.get("raw_text", "") if isinstance(bug_desc, dict) else str(bug_desc)
        
        bug_types = self._knowledge.get_bug_types_from_description(bug_raw_text)
        logger.info(f"  推断 Bug 类型: {bug_types}")
        
        try:
            prev_output = inputs.get("log_extraction", {})
            if isinstance(prev_output, dict):
                extract_dir = prev_output.get("data", {}).get("extraction_dir")
            else:
                extract_dir = None
            
            if extract_dir:
                logger.info(f"  复用 log_extraction 解压结果: {extract_dir}")
            else:
                logger.info("  未找到已有解压结果，重新解压...")
                extractor = LogExtractor()
                extract_dir = extractor.extract(log_path)
            
            file_selector_output = inputs.get("log_file_selector", {})
            if isinstance(file_selector_output, dict):
                selected_files = file_selector_output.get("data", {}).get("selected_files", [])
            else:
                selected_files = []
            
            if selected_files:
                logger.info(f"  使用 log_file_selector 筛选的 {len(selected_files)} 个文件")
                parser = BugReportParser(extract_dir, use_smart_filter=False)
                log_entries = []
                for file_path in selected_files:
                    if isinstance(file_path, str) and not file_path.startswith('/'):
                        file_path = os.path.join(extract_dir, file_path)
                    log_entries.extend(parser.parse_file(file_path))
            else:
                parser = BugReportParser(extract_dir)
                log_entries = parser.parse_all()
            
            logger.info(f"  解析日志条数: {len(log_entries)}")
            
            cleaner = LogCleaner(log_entries)
            cleaned_logs = cleaner.clean_all()
            logger.info(f"  清洗后日志条数: {len(cleaned_logs)} (过滤 {len(log_entries) - len(cleaned_logs)} 条)")
            
            analyzer = LogAnalyzer(cleaned_logs)
            analysis_result = analyzer.analyze()
            
            critical_logs = self._extract_critical_logs(analysis_result, cleaned_logs, bug_types)
            
            device_state = self._extract_device_state(log_entries)
            
            timeline = self._build_timeline(log_entries, bug_desc)
            
            log_type_summary = {}
            if selected_files:
                for f in selected_files[:10]:
                    filename = os.path.basename(f) if '/' in str(f) else str(f)
                    desc = self._knowledge.get_log_type_description(filename)
                    log_type_summary[filename] = desc
            
            result = {
                "crashes": len(getattr(analysis_result, 'crashes', [])),
                "anrs": len(getattr(analysis_result, 'anrs', [])),
                "low_memory": len(getattr(analysis_result, 'low_memory', [])),
                "exceptions": len(getattr(analysis_result, 'exceptions', [])),
                "critical_logs": critical_logs,
                "device_state": device_state,
                "timeline": timeline,
                "bug_types": bug_types,
                "log_type_summary": log_type_summary,
            }
            
            return SkillResult(
                True,
                result,
                f"高级分析完成: 提取了 {len(critical_logs)} 条关键日志, Bug类型: {bug_types}"
            )
            
        except Exception as e:
            return SkillResult(
                False,
                {},
                f"高级分析失败: {str(e)}"
            )
    
    def _extract_critical_logs(self, analysis_result, all_entries: List = None, bug_types: List[str] = None) -> List[Dict]:
        """提取关键日志片段，根据 Bug 类型调整提取数量和优先级"""
        critical_logs = []
        
        crash_limit = 5 if bug_types and "crash" in bug_types else 3
        anr_limit = 3 if bug_types and "anr" in bug_types else 2
        low_mem_limit = 5 if bug_types and "memory" in bug_types else 3
        exc_limit = 5
        
        for crash in getattr(analysis_result, 'crashes', [])[:crash_limit]:
            context = self._build_context_block(crash, all_entries, "crash")
            critical_logs.append(context)
        
        for anr in getattr(analysis_result, 'anrs', [])[:anr_limit]:
            context = self._build_context_block(anr, all_entries, "anr")
            critical_logs.append(context)
        
        for low_mem in getattr(analysis_result, 'low_memory', [])[:low_mem_limit]:
            context = self._build_context_block(low_mem, all_entries, "low_memory")
            critical_logs.append(context)
        
        for exc in getattr(analysis_result, 'exceptions', [])[:exc_limit]:
            context = self._build_context_block(exc, all_entries, "exception")
            critical_logs.append(context)
        
        return critical_logs
    
    def _build_context_block(self, entry, all_entries: List, log_type: str) -> Dict:
        """将单条日志与其上下文合并为一个上下文块"""
        context_lines = [entry.message]
        
        if all_entries:
            idx = None
            for i, e in enumerate(all_entries):
                if (e.message == entry.message and
                    e.timestamp == entry.timestamp and
                    e.tag == entry.tag):
                    idx = i
                    break
            
            if idx is not None:
                before = []
                for i in range(max(0, idx - 2), idx):
                    e = all_entries[i]
                    if e.message and e.message != entry.message:
                        before.append(e.message)
                
                after = []
                for i in range(idx + 1, min(len(all_entries), idx + 5)):
                    e = all_entries[i]
                    if e.message:
                        after.append(e.message)
                
                all_parts = before + [entry.message] + after
                if len(all_parts) > 1:
                    context_lines = all_parts
        
        result = {
            "type": log_type,
            "message": "\n".join(context_lines),
        }
        
        if entry.timestamp:
            result["timestamp"] = entry.timestamp
        if entry.level:
            result["level"] = entry.level
        if entry.tag:
            result["tag"] = entry.tag
        if entry.pid:
            result["pid"] = entry.pid
        
        return result
    
    def _extract_device_state(self, log_entries) -> Dict:
        """提取设备状态信息"""
        state = {
            "battery_levels": [],
            "memory_states": [],
            "cpu_events": [],
            "thermal_events": []
        }
        
        for entry in log_entries:
            msg = entry.message.lower()
            
            if "battery" in msg and ("level" in msg or "%" in msg):
                state["battery_levels"].append({
                    "timestamp": entry.timestamp,
                    "message": entry.message
                })
            
            if "meminfo" in msg or "low memory" in msg or "oom" in msg:
                state["memory_states"].append({
                    "timestamp": entry.timestamp,
                    "tag": entry.tag,
                    "message": entry.message
                })
            
            if "thermal" in msg or "temperature" in msg or "power" in msg:
                state["thermal_events"].append({
                    "timestamp": entry.timestamp,
                    "tag": entry.tag,
                    "message": entry.message
                })
        
        return state
    
    def _build_timeline(self, log_entries, bug_desc) -> List[Dict]:
        """构建时间线"""
        timeline = []
        
        time_keywords = bug_desc.get("time_points", [])
        
        for entry in log_entries:
            if entry.timestamp:
                timeline.append({
                    "timestamp": entry.timestamp,
                    "level": entry.level,
                    "tag": entry.tag,
                    "snippet": entry.message[:100] + "..." if len(entry.message) > 100 else entry.message
                })
        
        return timeline[:50]
