import os
import re
from pathlib import Path
from typing import List, Set, Tuple, Optional
from harness.core.logging import get_logger

logger = get_logger(__name__)

LOG_FILE_PATTERNS = [
    re.compile(r'bugreport.*\.txt', re.IGNORECASE),
    re.compile(r'main_log', re.IGNORECASE),
    re.compile(r'system_log', re.IGNORECASE),
    re.compile(r'radio_log', re.IGNORECASE),
    re.compile(r'events_log', re.IGNORECASE),
    re.compile(r'kernel_log', re.IGNORECASE),
    re.compile(r'crash_log', re.IGNORECASE),
    re.compile(r'logcat', re.IGNORECASE),
    re.compile(r'hilog', re.IGNORECASE),
    re.compile(r'xlog', re.IGNORECASE),
    re.compile(r'\.log$', re.IGNORECASE),
    re.compile(r'\.logcat$', re.IGNORECASE),
    re.compile(r'_log$', re.IGNORECASE),
    re.compile(r'\.sysprop$', re.IGNORECASE),
    re.compile(r'dumpstate', re.IGNORECASE),
]

BLACKLIST_DIRS = {
    'screenshots', 'screenshot', 'images', 'image',
    'video', 'videos', 'audio', 'music',
    'thumbnails', 'thumb', 'cache',
    'backup', 'backups',
    'apk', 'apks', 'app', 'apps',
    'fonts', 'font',
    'ringtones', 'notifications',
    'wallpaper', 'wallpapers',
    'icons', 'icon',
}

BLACKLIST_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg',
    '.mp4', '.mp3', '.wav', '.ogg', '.flac', '.aac',
    '.apk', '.dex', '.odex', '.oat', '.art', '.vdex',
    '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
    '.so', '.db', '.sqlite', '.json_proto',
    '.proto', '.pb',
}

BLACKLIST_NAME_PATTERNS = [
    re.compile(r'screenshot', re.IGNORECASE),
    re.compile(r'screen_capture', re.IGNORECASE),
    re.compile(r'screenrecord', re.IGNORECASE),
    re.compile(r'proto[-_]?dump', re.IGNORECASE),
    re.compile(r'package[-_]?list', re.IGNORECASE),
    re.compile(r'service[-_]?list', re.IGNORECASE),
    re.compile(r'permission', re.IGNORECASE),
    re.compile(r'carrier[-_]?config', re.IGNORECASE),
    re.compile(r'wifi[-_]?config', re.IGNORECASE),
    re.compile(r'bluetooth', re.IGNORECASE),
]

HIGH_PRIORITY_PATTERNS = [
    re.compile(r'crash', re.IGNORECASE),
    re.compile(r'fatal', re.IGNORECASE),
    re.compile(r'anr', re.IGNORECASE),
    re.compile(r'tombstone', re.IGNORECASE),
    re.compile(r'watchdog', re.IGNORECASE),
    re.compile(r'exception', re.IGNORECASE),
    re.compile(r'logcat', re.IGNORECASE),
    re.compile(r'main_log', re.IGNORECASE),
    re.compile(r'system_log', re.IGNORECASE),
    re.compile(r'bugreport', re.IGNORECASE),
]


class LogFileSelector:
    """统一的日志文件筛选器"""
    
    def __init__(self, use_llm_filter: bool = False, bug_description: str = ""):
        self.use_llm_filter = use_llm_filter
        self.bug_description = bug_description
    
    def scan_directory(self, extract_dir: str) -> Tuple[List[str], List[str]]:
        """扫描目录，返回 (匹配的日志文件, 被过滤掉的文件)"""
        matched = []
        filtered_out = []
        
        for root, dirs, files in os.walk(extract_dir):
            dirs[:] = [d for d in dirs if d.lower() not in BLACKLIST_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                if self._should_filter(file, file_path):
                    filtered_out.append(file_path)
                    continue
                
                if self._is_log_file(file):
                    matched.append(file_path)
                else:
                    filtered_out.append(file_path)
        
        return matched, filtered_out
    
    def _should_filter(self, filename: str, file_path: str) -> bool:
        """判断文件是否应该被过滤掉"""
        ext = Path(filename).suffix.lower()
        if ext in BLACKLIST_EXTENSIONS:
            return True
        
        for pattern in BLACKLIST_NAME_PATTERNS:
            if pattern.search(filename):
                return True
        
        try:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return True
            if file_size < 50:
                return True
        except OSError:
            pass
        
        return False
    
    def _is_log_file(self, filename: str) -> bool:
        """判断文件是否为日志文件"""
        for pattern in LOG_FILE_PATTERNS:
            if pattern.search(filename):
                return True
        return False
    
    def prioritize(self, log_files: List[str]) -> List[str]:
        """按优先级排序日志文件，高优先级文件排前面"""
        def priority_score(file_path: str) -> int:
            filename = os.path.basename(file_path)
            score = 0
            for pattern in HIGH_PRIORITY_PATTERNS:
                if pattern.search(filename):
                    score += 10
            
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 1024 * 1024:
                    score += 5
                elif file_size > 100 * 1024:
                    score += 3
                elif file_size > 10 * 1024:
                    score += 1
            except OSError:
                pass
            
            return score
        
        return sorted(log_files, key=priority_score, reverse=True)
    
    def generate_file_manifest(self, extract_dir: str, matched_files: List[str] = None) -> str:
        """生成文件清单，供 LLM 判断哪些文件需要分析
        
        Args:
            extract_dir: 解压目录
            matched_files: 规则匹配后的文件列表。如果提供，只包含这些文件；
                          如果不提供，包含所有文件（可能很大）
        
        Returns:
            格式化的文件清单字符串，包含文件路径、大小、类型
        """
        lines = []
        lines.append(f"解压目录: {extract_dir}")
        lines.append("=" * 80)
        lines.append("")
        
        total_files = 0
        files_to_list = matched_files if matched_files is not None else None
        
        if files_to_list is not None:
            for file_path in files_to_list:
                rel_path = os.path.relpath(file_path, extract_dir)
                
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > 1024 * 1024:
                        size_str = f"{file_size / (1024*1024):.1f}MB"
                    elif file_size > 1024:
                        size_str = f"{file_size / 1024:.1f}KB"
                    else:
                        size_str = f"{file_size}B"
                except OSError:
                    size_str = "N/A"
                
                filename = os.path.basename(file_path)
                is_log = self._is_log_file(filename)
                tag = "[LOG]" if is_log else "[OTHER]"
                
                lines.append(f"  {tag} {size_str:>10s}  {rel_path}")
                total_files += 1
        else:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, extract_dir)
                    
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > 1024 * 1024:
                            size_str = f"{file_size / (1024*1024):.1f}MB"
                        elif file_size > 1024:
                            size_str = f"{file_size / 1024:.1f}KB"
                        else:
                            size_str = f"{file_size}B"
                    except OSError:
                        size_str = "N/A"
                    
                    ext = Path(file).suffix.lower()
                    is_log = self._is_log_file(file)
                    tag = "[LOG]" if is_log else "[OTHER]"
                    
                    lines.append(f"  {tag} {size_str:>10s}  {rel_path}")
                    total_files += 1
        
        lines.insert(2, f"文件总数: {total_files}")
        lines.insert(3, "")
        return "\n".join(lines)
