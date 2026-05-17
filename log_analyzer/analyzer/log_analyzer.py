from typing import List, Dict, Any
from dataclasses import dataclass, field
from log_analyzer.parser.log_parser import LogEntry


@dataclass
class AnalysisResult:
    crashes: List[LogEntry] = field(default_factory=list)
    anrs: List[LogEntry] = field(default_factory=list)
    low_memory: List[LogEntry] = field(default_factory=list)
    exceptions: List[LogEntry] = field(default_factory=list)
    boot_events: List[LogEntry] = field(default_factory=list)
    power_events: List[LogEntry] = field(default_factory=list)
    other_issues: List[LogEntry] = field(default_factory=list)


class LogAnalyzer:
    def __init__(self, entries: List[LogEntry]):
        self.entries = entries

    def analyze(self) -> AnalysisResult:
        result = AnalysisResult()
        for entry in self.entries:
            self._check_entry(entry, result)
        return result

    def _check_entry(self, entry: LogEntry, result: AnalysisResult):
        msg_lower = entry.message.lower()
        tag_lower = entry.tag.lower() if entry.tag else ""

        # 检查所有条件，不是互斥的
        added = False
        
        # 检查崩溃
        if self._is_crash(entry, msg_lower, tag_lower):
            result.crashes.append(entry)
            added = True
        
        # 检查ANR
        if self._is_anr(entry, msg_lower, tag_lower):
            result.anrs.append(entry)
            added = True
        
        # 检查低内存
        if self._is_low_memory(entry, msg_lower, tag_lower):
            result.low_memory.append(entry)
            added = True
        
        # 检查异常
        if self._is_exception(entry, msg_lower):
            result.exceptions.append(entry)
            added = True
        
        # 检查启动事件
        if self._is_boot_event(entry, msg_lower, tag_lower):
            result.boot_events.append(entry)
        
        # 检查电源事件
        if self._is_power_event(entry, msg_lower, tag_lower):
            result.power_events.append(entry)
        
        # 检查其他问题（如果还没有被归类到其他任何类别）
        if not added and self._is_other_issue(entry, msg_lower, tag_lower):
            result.other_issues.append(entry)

    def _is_crash(self, entry: LogEntry, msg_lower: str, tag_lower: str) -> bool:
        crash_keywords = [
            "crash",
            "fatal",
            "am_crash",
            "AndroidRuntime",
            "FATAL EXCEPTION",
        ]
        return any(
            keyword.lower() in msg_lower or keyword.lower() in tag_lower
            for keyword in crash_keywords
        )

    def _is_anr(self, entry: LogEntry, msg_lower: str, tag_lower: str) -> bool:
        anr_keywords = ["anr", "am_anr", "not responding"]
        return any(
            keyword.lower() in msg_lower or keyword.lower() in tag_lower
            for keyword in anr_keywords
        )

    def _is_low_memory(self, entry: LogEntry, msg_lower: str, tag_lower: str) -> bool:
        low_memory_keywords = [
            "low_memory",
            "am_low_memory",
            "oom",
            "out of memory",
            "kill",
        ]
        return any(
            keyword.lower() in msg_lower or keyword.lower() in tag_lower
            for keyword in low_memory_keywords
        )

    def _is_exception(self, entry: LogEntry, msg_lower: str) -> bool:
        exception_keywords = ["exception", "error", "nullpointer", "arrayindex"]
        return any(keyword.lower() in msg_lower for keyword in exception_keywords)

    def _is_boot_event(self, entry: LogEntry, msg_lower: str, tag_lower: str) -> bool:
        boot_keywords = [
            "boot",
            "bootstat",
            "start",
            "init",
            "zygote",
            "system_server",
        ]
        return any(
            keyword.lower() in msg_lower or keyword.lower() in tag_lower
            for keyword in boot_keywords
        )

    def _is_power_event(self, entry: LogEntry, msg_lower: str, tag_lower: str) -> bool:
        power_keywords = [
            "power",
            "shutdown",
            "reboot",
            "battery",
            "sleep",
            "wake",
        ]
        return any(
            keyword.lower() in msg_lower or keyword.lower() in tag_lower
            for keyword in power_keywords
        )

    def _is_other_issue(self, entry: LogEntry, msg_lower: str, tag_lower: str) -> bool:
        # 检查严重级别的日志
        if entry.level in ["E", "F", "W"]:  # Error, Fatal, Warning
            return True
        return False

    def generate_report(self, result: AnalysisResult) -> str:
        report = []
        report.append("=" * 60)
        report.append("ANDROID 日志分析报告")
        report.append("=" * 60)
        report.append("")

        # 崩溃
        report.append(f"【崩溃信息】({len(result.crashes)})")
        for entry in result.crashes[:20]:  # 只显示前20个
            report.append(self._format_entry(entry))
        report.append("")

        # ANR
        report.append(f"【ANR信息】({len(result.anrs)})")
        for entry in result.anrs[:20]:
            report.append(self._format_entry(entry))
        report.append("")

        # 低内存
        report.append(f"【低内存信息】({len(result.low_memory)})")
        for entry in result.low_memory[:20]:
            report.append(self._format_entry(entry))
        report.append("")

        # 异常
        report.append(f"【异常信息】({len(result.exceptions)})")
        for entry in result.exceptions[:20]:
            report.append(self._format_entry(entry))
        report.append("")

        # 其他问题
        report.append(f"【其他问题】({len(result.other_issues)})")
        for entry in result.other_issues[:30]:
            report.append(self._format_entry(entry))
        report.append("")

        report.append("=" * 60)
        return "\n".join(report)

    def _format_entry(self, entry: LogEntry) -> str:
        parts = []
        if entry.timestamp:
            parts.append(f"[{entry.timestamp}]")
        if entry.level:
            parts.append(f"[{entry.level}]")
        if entry.tag:
            parts.append(f"[{entry.tag}]")
        if entry.pid:
            parts.append(f"(PID:{entry.pid})")
        parts.append(entry.message[:200])  # 只显示前200个字符
        return " ".join(parts)
