"""
AdvancedLogAnalysisSkill - 高级日志分析技能
提取关键日志片段、设备状态变化，供LLM深度分析
"""
from typing import Dict, Any, List
from dataclasses import dataclass
from .base import BaseSkill, SkillResult
from log_analyzer.extractor.extractor import LogExtractor
from log_analyzer.bugreport.bugreport_parser import BugReportParser
from log_analyzer.cleaner.log_cleaner import LogCleaner
from log_analyzer.analyzer.log_analyzer import LogAnalyzer, AnalysisResult

@dataclass
class CriticalLogEntry:
    timestamp: str
    level: str
    tag: str
    message: str
    pid: int = None
    tid: int = None

class AdvancedLogAnalysisSkill(BaseSkill):
    """高级日志分析技能 - 提取高质量日志片段"""
    
    @property
    def name(self) -> str:
        return "advanced_log_analysis"
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["log_path"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        log_path = inputs["log_path"]
        bug_desc = inputs.get("bug_description", {})
        
        try:
            # 解析日志
            extractor = LogExtractor()
            extract_dir = extractor.extract(log_path)
            parser = BugReportParser(extract_dir)
            log_entries = parser.parse_all()
            
            # 清洗日志
            cleaner = LogCleaner(log_entries)
            cleaned_logs = cleaner.clean_all()
            
            # 分析日志
            analyzer = LogAnalyzer(cleaned_logs)
            analysis_result = analyzer.analyze()
            
            # 提取关键日志片段
            critical_logs = self._extract_critical_logs(analysis_result)
            
            # 提取设备状态
            device_state = self._extract_device_state(log_entries)
            
            # 提取时间线
            timeline = self._build_timeline(log_entries, bug_desc)
            
            result = {
                "crashes": len(getattr(analysis_result, 'crashes', [])),
                "anrs": len(getattr(analysis_result, 'anrs', [])),
                "low_memory": len(getattr(analysis_result, 'low_memory', [])),
                "exceptions": len(getattr(analysis_result, 'exceptions', [])),
                "critical_logs": critical_logs,
                "device_state": device_state,
                "timeline": timeline
            }
            
            return SkillResult(
                True,
                result,
                f"高级分析完成: 提取了 {len(critical_logs)} 条关键日志"
            )
            
        except Exception as e:
            return SkillResult(
                False,
                {},
                f"高级分析失败: {str(e)}"
            )
    
    def _extract_critical_logs(self, analysis_result) -> List[Dict]:
        """提取关键日志片段"""
        critical_logs = []
        
        # 提取崩溃日志（取前3个，每个最多5行上下文）
        for crash in getattr(analysis_result, 'crashes', [])[:3]:
            critical_logs.append({
                "type": "crash",
                "timestamp": crash.timestamp,
                "level": crash.level,
                "tag": crash.tag,
                "message": crash.message,
                "pid": crash.pid
            })
        
        # 提取ANR日志（取前2个）
        for anr in getattr(analysis_result, 'anrs', [])[:2]:
            critical_logs.append({
                "type": "anr",
                "timestamp": anr.timestamp,
                "level": anr.level,
                "tag": anr.tag,
                "message": anr.message,
                "pid": anr.pid
            })
        
        # 提取低内存日志（取前3个）
        for low_mem in getattr(analysis_result, 'low_memory', [])[:3]:
            critical_logs.append({
                "type": "low_memory",
                "timestamp": low_mem.timestamp,
                "level": low_mem.level,
                "tag": low_mem.tag,
                "message": low_mem.message
            })
        
        # 提取异常日志（取前5个）
        for exc in getattr(analysis_result, 'exceptions', [])[:5]:
            critical_logs.append({
                "type": "exception",
                "timestamp": exc.timestamp,
                "level": exc.level,
                "tag": exc.tag,
                "message": exc.message
            })
        
        return critical_logs
    
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
            
            # 电池信息
            if "battery" in msg and ("level" in msg or "%" in msg):
                state["battery_levels"].append({
                    "timestamp": entry.timestamp,
                    "message": entry.message
                })
            
            # 内存信息
            if "meminfo" in msg or "low memory" in msg or "oom" in msg:
                state["memory_states"].append({
                    "timestamp": entry.timestamp,
                    "tag": entry.tag,
                    "message": entry.message
                })
            
            # 功耗/热信息
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
        
        # 提取时间点
        time_keywords = bug_desc.get("time_points", [])
        
        for entry in log_entries:
            if entry.timestamp:
                timeline.append({
                    "timestamp": entry.timestamp,
                    "level": entry.level,
                    "tag": entry.tag,
                    "snippet": entry.message[:100] + "..." if len(entry.message) > 100 else entry.message
                })
        
        # 只取前50个时间点
        return timeline[:50]
