"""
Log Evidence Matcher - 日志证据匹配器
将用户描述的现象和日志证据进行对照，提升报告置信度
"""
from typing import Dict, Any, List
from .base import BaseSkill, SkillResult, LLMBasedSkill
import os
import json
from datetime import datetime

from harness.core.logging import get_logger

logger = get_logger(__name__)


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
        
        # 使用 LLM 进行证据匹配
        try:
            return self._llm_match(bug_desc, critical_logs, device_state)
        except Exception as e:
            logger.warning(f"LLM 证据匹配失败，降级到规则匹配: {e}")
            return self._rule_based_match(bug_desc, critical_logs, device_state)
    
    def _llm_match(self, bug_desc: Dict, critical_logs: List, device_state: Dict) -> Dict:
        """使用 LLM 进行智能证据匹配"""
        import json
        
        logs_summary = []
        for idx, log in enumerate(critical_logs[:20]):
            if isinstance(log, dict):
                logs_summary.append(f"[{idx}] {log.get('timestamp', '')} {log.get('level', '')} {log.get('tag', '')}: {log.get('message', '')[:200]}")
            else:
                logs_summary.append(f"[{idx}] {str(log)[:200]}")
        
        user_desc = bug_desc.get("raw_text", str(bug_desc))
        
        prompt = f"""你是一位资深的Android日志分析专家。请对照用户描述的现象和日志证据进行匹配分析。

【用户问题描述】
{user_desc}

【关键日志（最多20条）】
{chr(10).join(logs_summary)}

【设备状态】
- 电池事件: {len(device_state.get('battery_levels', []))} 条
- 内存事件: {len(device_state.get('memory_states', []))} 条
- 热事件: {len(device_state.get('thermal_events', []))} 条

请返回JSON格式的匹配结果：
{{
    "confidence_score": 0.0到1.0的置信度,
    "timeline_match": [
        {{
            "user_description": "用户描述的现象",
            "log_evidence": "对应的日志证据",
            "matched": true或false,
            "confidence": 0.0到1.0,
            "log_idx": 对应的日志索引（从0开始的数字）
        }}
    ],
    "what_we_saw_in_logs": ["在日志中观察到的关键事件列表"],
    "what_happened": ["按时间顺序的事件描述"],
    "matched_logs_indices": [与用户问题匹配的日志索引列表],
    "additional_findings_indices": [额外发现的严重问题的日志索引列表]
}}

只返回JSON，不要其他文字。"""
        
        response = super()._call_llm(
            system_prompt="你是一位资深的Android日志分析专家，擅长对照用户描述和日志证据进行精准匹配。只返回JSON格式数据。",
            user_prompt=prompt
        )
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response[json_start:json_end])
                # 处理匹配和额外发现的日志
                matched_indices = result.get("matched_logs_indices", [])
                additional_indices = result.get("additional_findings_indices", [])
                
                # 转换为实际日志对象
                result["matched_logs"] = [critical_logs[idx] for idx in matched_indices if idx < len(critical_logs)]
                result["additional_findings"] = [critical_logs[idx] for idx in additional_indices if idx < len(critical_logs)]
                
                return result
        except (json.JSONDecodeError, ValueError, Exception) as e:
            logger.warning(f"LLM匹配处理失败，降级到规则匹配: {e}")
            pass
        
        return self._rule_based_match(bug_desc, critical_logs, device_state)
    
    def _rule_based_match(self, bug_desc: Dict, critical_logs: List, device_state: Dict) -> Dict:
        """基于规则的证据匹配（降级方案）"""
        user_desc = bug_desc.get("raw_text", str(bug_desc)).lower()
        
        timeline_match = []
        matched_count = 0
        total_confidence = 0.0
        
        # 关键词匹配
        keywords = bug_desc.get("keywords", []) or []
        search_terms = keywords + [word for word in user_desc.split() if len(word) > 2]
        
        # 跟踪匹配和未匹配的问题
        matched_logs_idx = set()
        unmatched_logs = []
        
        for idx, log in enumerate(critical_logs[:20]):
            if isinstance(log, dict):
                msg = log.get("message", "").lower()
            else:
                msg = str(log).lower()
            
            matched_terms = [t for t in search_terms if t.lower() in msg]
            if matched_terms:
                confidence = min(0.5 + 0.1 * len(matched_terms), 0.95)
                timeline_match.append({
                    "user_description": user_desc[:100],
                    "log_evidence": msg[:200],
                    "matched": True,
                    "confidence": confidence,
                    "log_idx": idx
                })
                matched_count += 1
                total_confidence += confidence
                matched_logs_idx.add(idx)
            else:
                # 收集未匹配的日志
                unmatched_logs.append({
                    "log_idx": idx,
                    "log": log
                })
        
        avg_confidence = total_confidence / max(matched_count, 1)
        
        return {
            "confidence_score": round(avg_confidence, 2),
            "timeline_match": timeline_match,
            "scene_changes": [],
            "what_we_saw_in_logs": [f"找到 {matched_count} 条与用户描述相关的日志"],
            "what_happened": [],
            "confidence_explanation": f"基于规则匹配，共匹配 {matched_count} 条日志，平均置信度 {avg_confidence:.2f}",
            # 新增：区分匹配和未匹配的问题
            "matched_logs": [critical_logs[idx] for idx in matched_logs_idx if idx < len(critical_logs)],
            "additional_findings": [item["log"] for item in unmatched_logs]
        }
    
    def _mock_match(self, bug_desc: Dict, critical_logs: List, device_state: Dict) -> Dict:
        """模拟证据匹配"""
        # 模拟拆分匹配和额外发现
        crash_logs = [log for log in critical_logs if log.get("type") == "crash"]
        other_logs = [log for log in critical_logs if log.get("type") != "crash"]
        
        return {
            "confidence_score": 0.92,
            "timeline_match": [
                {
                    "user_description": "应用打开主页面时崩溃",
                    "log_evidence": "找到了对应时间的崩溃日志",
                    "matched": True,
                    "confidence": 0.95,
                    "log_entries": crash_logs[:2]
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
""",
            # 新增：区分匹配和未匹配的问题
            "matched_logs": crash_logs,
            "additional_findings": other_logs
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
