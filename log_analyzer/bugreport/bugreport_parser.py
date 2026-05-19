"""
BugReportParser - Bugreport 解析器
解析 Android bugreport 文件，提取日志和元数据
"""
import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
from log_analyzer.parser.log_parser import LogEntry
from log_analyzer.extractor.log_file_selector import LogFileSelector

from harness.core.logging import get_logger

logger = get_logger(__name__)


class BugReportParser:
    """Android bugreport 解析器"""
    
    def __init__(self, log_dir: str, use_smart_filter: bool = True):
        self.log_dir = log_dir
        self.log_files = []
        self._selector = LogFileSelector()
        self._use_smart_filter = use_smart_filter
        self._find_log_files()

    def _find_log_files(self):
        """查找bugreport相关文件，使用统一筛选器"""
        if self._use_smart_filter:
            matched, filtered = self._selector.scan_directory(self.log_dir)
            self.log_files = matched
            if filtered:
                logger.info(f"  智能过滤: 选中 {len(matched)} 个日志文件, 过滤 {len(filtered)} 个无关文件")
        else:
            for root, _, files in os.walk(self.log_dir):
                for file in files:
                    if self._is_bugreport_file(file):
                        self.log_files.append(os.path.join(root, file))

    def _is_bugreport_file(self, filename: str) -> bool:
        """判断是否为bugreport相关文件"""
        patterns = [
            r'bugreport.*\.txt',
            r'main_log.*',
            r'system_log.*',
            r'radio_log.*',
            r'events_log.*',
            r'kernel_log.*',
            r'crash_log.*',
            r'\.log$',
            r'\.txt$',
            r'_log$'
        ]
        for pattern in patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        return False

    def parse_all(self) -> List[LogEntry]:
        """解析所有bugreport文件"""
        all_entries = []
        for log_file in self.log_files:
            all_entries.extend(self.parse_file(log_file))
        return all_entries

    def parse_file(self, file_path: str) -> List[LogEntry]:
        entries = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                last_entry = None
                for line in f:
                    entry = self._parse_line(line, file_path, last_entry)
                    if entry:
                        entries.append(entry)
                        last_entry = entry
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"解析文件 {file_path} 失败: {e}")
        return entries

    def _parse_line(self, line: str, file_path: str, last_entry: Optional[LogEntry] = None) -> Optional[LogEntry]:
        line = line.strip()
        if not line:
            return None

        match1 = re.match(
            r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([VDIWEF])\s+([^:]+):\s*(.*)',
            line
        )
        if match1:
            return LogEntry(
                timestamp=match1.group(1),
                pid=int(match1.group(3)),
                tid=int(match1.group(4)),
                level=match1.group(5),
                tag=match1.group(6).strip(),
                message=match1.group(7),
                file_path=file_path
            )

        match2 = re.match(
            r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+(\d+)\s+(\d+)\s+([VDIWEF])\s+(\S+)\s*:\s*(.*)',
            line
        )
        if match2:
            return LogEntry(
                timestamp=match2.group(1),
                pid=int(match2.group(2)),
                tid=int(match2.group(3)),
                level=match2.group(4),
                tag=match2.group(5),
                message=match2.group(6),
                file_path=file_path
            )

        match3 = re.match(r'([VDIWEF])/([^(]+)\(\s*(\d+)\):\s*(.*)', line)
        if match3:
            return LogEntry(
                level=match3.group(1),
                tag=match3.group(2).strip(),
                pid=int(match3.group(3)),
                message=match3.group(4),
                file_path=file_path
            )

        match4 = re.match(r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*(.*)', line)
        if match4:
            return LogEntry(
                timestamp=match4.group(1),
                message=match4.group(2),
                file_path=file_path
            )

        entry = LogEntry(message=line, file_path=file_path)

        if last_entry:
            if not entry.timestamp and last_entry.timestamp:
                entry.timestamp = last_entry.timestamp
            if not entry.level and last_entry.level:
                entry.level = last_entry.level
            if not entry.tag and last_entry.tag:
                entry.tag = last_entry.tag
            if not entry.pid and last_entry.pid:
                entry.pid = last_entry.pid
            if not entry.tid and last_entry.tid:
                entry.tid = last_entry.tid

        return entry

    def extract_metadata(self) -> Dict[str, str]:
        """从bugreport中提取元数据"""
        metadata = {}
        for log_file in self.log_files:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(10000)  # 只读取前10KB
                    
                    # 提取设备信息
                    device_match = re.search(r'Product:?\s*([^\n]+)', content, re.IGNORECASE)
                    if device_match:
                        metadata['device'] = device_match.group(1).strip()
                    
                    # 提取Android版本
                    version_match = re.search(r'Version:?\s*([^\n]+)', content, re.IGNORECASE)
                    if version_match:
                        metadata['android_version'] = version_match.group(1).strip()
                    
                    # 提取Build信息
                    build_match = re.search(r'Build:?\s*([^\n]+)', content, re.IGNORECASE)
                    if build_match:
                        metadata['build'] = build_match.group(1).strip()
            except Exception as e:
                logger.warning(f"Failed to extract metadata from {log_file}: {e}")
        return metadata
