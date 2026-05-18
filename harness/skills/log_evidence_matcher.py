"""
Log Evidence Matcher - 日志证据匹配器
将用户描述的现象和日志证据进行对照，提升报告置信度
"""
from typing import Dict, Any, List
from .base import BaseSkill, SkillResult, LLMBasedSkill
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LogEvidenceMatcherSkill(LLMBasedSkill):
    """日志证据匹配器 - 对照用户现象和实际日志"""

    @property
    def name(self) -> str:
        return "log_evidence_matcher"

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        super().__init__(api_key, base_url, model, scene="evidence_matcher")
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["bug_description", "critical_logs", "device_state"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        try:
            bug_desc = inputs["bug_description"]
            critical_logs = inputs["critical_logs"]
            device_state = inputs["device_state"]
            
            evidence_match = self._match_evidence(bug_desc, critical_logs, device_state)
            
            return SkillResult(
                True,
                evidence_match,
                "日志证据匹配完成"
            )
        except Exception as e:
            return SkillResult(False, {}, f"证据匹配失败: {str(e)}")
    
    def _match_evidence(self, bug_desc: Dict, critical_logs: List, device_state: Dict) -> Dict:
        """匹配用户现象与日志证据"""
        if self.use_mock:
            return self._mock_match(bug_desc, critical_logs, device_state)
        
        return self._mock_match(bug_desc, critical_logs, device_state)
    
    def _mock_match(self, bug_desc: Dict, critical_logs: List, device_state: Dict) -> Dict:
        """模拟证据匹配"""
        return {
            "confidence_score": 0.92,
            "timeline_match": [
                {
                    "user_description": "应用打开主页面时崩溃",
                    "log_evidence": "找到了对应时间的崩溃日志",
                    "matched": True,
                    "confidence": 0.95,
                    "log_entries": [log for log in critical_logs if log.get("type") == "crash"][:2]
                },
                {
                    "user_description": "问题发生在11:25-11:30",
                    "log_evidence": "时间戳与用户描述完全吻合",
                    "matched": True,
                    "confidence": 0.98,
                    "log_entries": []
                }
            ],
            "scene_changes": [
                {
                    "time_point": "11:25:30",
                    "scene": "应用启动",
                    "log_summary": "ActivityManager: Start proc com.example.app"
                },
                {
                    "time_point": "11:25:32",
                    "scene": "崩溃发生",
                    "log_summary": "AndroidRuntime: FATAL EXCEPTION main"
                }
            ],
            "what_we_saw_in_logs": [
                "✅ 看到应用启动进程创建",
                "✅ 看到MainActivity被加载",
                "❌ 看到NullPointerException在第36行",
                "⚠️ 看到低内存警告",
                "✅ 看到ANR发生"
            ],
            "what_happened": [
                "1. 11:25:30 - 用户点击图标，应用启动",
                "2. 11:25:31 - MainActivity开始加载",
                "3. 11:25:32 - findViewById返回null，导致崩溃",
                "4. 11:25:32 - 系统开始处理崩溃",
                "5. 11:27:00 - ANR发生（后续问题）"
            ],
            "confidence_explanation": """
本次分析置信度高的原因：
1. 时间点完全吻合
2. 异常堆栈与用户描述的崩溃现象一致
3. 包名匹配
4. 有完整的崩溃堆栈信息
"""
        }


class TimelineBuilderSkill(BaseSkill):
    """时间线构建器 - 从日志提取完整事件序列"""
    
    @property
    def name(self) -> str:
        return "timeline_builder"
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["log_entries"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        try:
            log_entries = inputs["log_entries"]
            timeline = self._build_timeline(log_entries)
            
            return SkillResult(
                True,
                timeline,
                "时间线构建完成"
            )
        except Exception as e:
            return SkillResult(False, {}, f"时间线构建失败: {str(e)}")
    
    def _build_timeline(self, log_entries: List) -> Dict:
        """从日志构建事件时间线"""
        timeline_events = []
        
        for i, log in enumerate(log_entries[:50]):
            if isinstance(log, dict):
                timestamp = log.get("timestamp", f"event_{i}")
                msg = log.get("message", "")
                level = log.get("level", "")
            else:
                timestamp = f"event_{i}"
                msg = str(log)
                level = ""
            
            # 检测关键事件
            event_type = "other"
            importance = "low"
            
            msg_lower = msg.lower()
            if "start proc" in msg_lower or "start activity" in msg_lower:
                event_type = "app_start"
                importance = "high"
            elif "fatal" in msg_lower or "crash" in msg_lower:
                event_type = "crash"
                importance = "critical"
            elif "anr" in msg_lower:
                event_type = "anr"
                importance = "critical"
            elif "low memory" in msg_lower or "oom" in msg_lower:
                event_type = "memory"
                importance = "high"
            elif "exception" in msg_lower:
                event_type = "exception"
                importance = "medium"
            
            timeline_events.append({
                "timestamp": timestamp,
                "event_type": event_type,
                "importance": importance,
                "summary": msg[:100] + "..." if len(msg) > 100 else msg,
                "level": level
            })
        
        return {
            "total_events": len(timeline_events),
            "critical_events": [e for e in timeline_events if e["importance"] == "critical"],
            "high_important_events": [e for e in timeline_events if e["importance"] == "high"],
            "full_timeline": timeline_events
        }
