import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LogEntry:
    timestamp: Optional[str] = None
    level: Optional[str] = None
    tag: Optional[str] = None
    message: str = ""
    pid: Optional[int] = None
    tid: Optional[int] = None
    file_path: Optional[str] = None


class LogParser:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        self.log_files = self._find_log_files()

    def _find_log_files(self) -> List[str]:
        log_files = []
        for root, dirs, files in os.walk(self.log_dir):
            for file in files:
                if self._is_log_file(file):
                    log_files.append(os.path.join(root, file))
        return log_files

    def _is_log_file(self, filename: str) -> bool:
        log_extensions = [
            ".log",
            ".txt",
            ".localtime",
            "main_log",
            "sys_log",
            "events_log",
            "kernel_log",
            "radio_log",
            "crash_log",
        ]
        for ext in log_extensions:
            if filename.endswith(ext) or ext in filename:
                return True
        return False

    def parse_all(self) -> List[LogEntry]:
        all_entries = []
        for log_file in self.log_files:
            all_entries.extend(self.parse_file(log_file))
        return all_entries

    def parse_file(self, file_path: str) -> List[LogEntry]:
        entries = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    entry = self._parse_line(line, file_path)
                    if entry:
                        entries.append(entry)
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
        return entries

    def _parse_line(self, line: str, file_path: str) -> Optional[LogEntry]:
        line = line.strip()
        if not line:
            return None

        # 尝试匹配常见的Android日志格式
        # 格式1: 03-29 11:25:32.894092  939  949 I am_crash: [...]
        match1 = re.match(
            r"(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+(\d+)\s+(\d+)\s+([VDIWEF])\s+(\S+)\s*:\s*(.*)",
            line,
        )
        if match1:
            return LogEntry(
                timestamp=match1.group(1),
                pid=int(match1.group(2)),
                tid=int(match1.group(3)),
                level=match1.group(4),
                tag=match1.group(5),
                message=match1.group(6),
                file_path=file_path,
            )

        # 格式2: I/ActivityManager(  939): Displayed ...
        match2 = re.match(r"([VDIWEF])/([^(]+)\(\s*(\d+)\):\s*(.*)", line)
        if match2:
            return LogEntry(
                level=match2.group(1),
                tag=match2.group(2).strip(),
                pid=int(match2.group(3)) if match2.group(3) else None,
                message=match2.group(4),
                file_path=file_path,
            )

        # 格式3: 简单的时间戳 + 消息
        match3 = re.match(r"(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*(.*)", line)
        if match3:
            return LogEntry(
                timestamp=match3.group(1),
                message=match3.group(2),
                file_path=file_path,
            )

        # 默认情况，只保存消息
        return LogEntry(message=line, file_path=file_path)
