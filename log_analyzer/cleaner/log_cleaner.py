from typing import List, Set
from log_analyzer.parser.log_parser import LogEntry


class LogCleaner:
    def __init__(self, entries: List[LogEntry]):
        self.entries = entries

    def remove_duplicates(self) -> List[LogEntry]:
        seen: Set[str] = set()
        unique_entries = []
        for entry in self.entries:
            key = f"{entry.timestamp}-{entry.tag}-{entry.message[:100]}"
            if key not in seen:
                seen.add(key)
                unique_entries.append(entry)
        return unique_entries

    def filter_by_level(self, levels: List[str]) -> List[LogEntry]:
        return [entry for entry in self.entries if entry.level in levels]

    def filter_by_tag(self, tags: List[str]) -> List[LogEntry]:
        return [entry for entry in self.entries if entry.tag in tags]

    def filter_by_keyword(self, keywords: List[str]) -> List[LogEntry]:
        return [
            entry
            for entry in self.entries
            if any(keyword.lower() in entry.message.lower() for keyword in keywords)
        ]

    def exclude_by_keyword(self, keywords: List[str]) -> List[LogEntry]:
        return [
            entry
            for entry in self.entries
            if all(keyword.lower() not in entry.message.lower() for keyword in keywords)
        ]

    def clean_all(self) -> List[LogEntry]:
        cleaned = self.remove_duplicates()
        # 可以添加更多默认清洗规则
        return cleaned
