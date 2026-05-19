"""
log_format_utils - 统一的日志格式化工具
解决 None 字段直接输出到 LLM 提示词的问题
将零散日志行合并为有上下文的结构化块
"""
from typing import Dict, List, Any


def format_critical_logs(critical_logs: List[Dict], max_logs: int = 15) -> str:
    """格式化关键日志列表，None 字段不显示，合并上下文块

    Args:
        critical_logs: 关键日志列表，每条包含 type/message/timestamp/level/tag 等字段
        max_logs: 最大显示条数

    Returns:
        格式化后的字符串，适合嵌入 LLM 提示词
    """
    if not critical_logs:
        return "无关键日志"

    parts = []
    for idx, log in enumerate(critical_logs[:max_logs], 1):
        if not isinstance(log, dict):
            parts.append(f"【日志 {idx}】{str(log)[:300]}")
            continue

        log_type = log.get("type", "unknown")
        message = log.get("message", "")
        timestamp = log.get("timestamp")
        level = log.get("level")
        tag = log.get("tag")
        pid = log.get("pid")

        header_parts = [f"【{log_type.upper()} 日志 {idx}】"]

        meta_parts = []
        if timestamp:
            meta_parts.append(f"时间: {timestamp}")
        if level:
            meta_parts.append(f"级别: {level}")
        if tag:
            meta_parts.append(f"标签: {tag}")
        if pid:
            meta_parts.append(f"PID: {pid}")

        if meta_parts:
            header_parts.append(" | ".join(meta_parts))

        if "\n" in message:
            parts.append(f"{header_parts[0]}\n{' | '.join(meta_parts) if meta_parts else ''}\n{message}")
        else:
            if meta_parts:
                parts.append(f"{header_parts[0]} {' | '.join(meta_parts)}\n  {message}")
            else:
                parts.append(f"{header_parts[0]}\n  {message}")

    return "\n\n".join(parts)


def format_log_entry_safe(log: Dict) -> str:
    """安全格式化单条日志，None 字段不显示

    Args:
        log: 日志字典

    Returns:
        格式化后的单行字符串
    """
    parts = []

    timestamp = log.get("timestamp")
    level = log.get("level")
    tag = log.get("tag")
    message = log.get("message", "")

    if timestamp:
        parts.append(f"[{timestamp}]")
    if level:
        parts.append(f"[{level}]")
    if tag:
        parts.append(f"[{tag}]")

    parts.append(message[:200])
    return " ".join(parts)
