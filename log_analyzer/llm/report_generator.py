from typing import List
from log_analyzer.models import BugDescription, StandardizedBugData
from log_analyzer.parser.log_parser import LogEntry
from log_analyzer.analyzer.log_analyzer import AnalysisResult
from log_analyzer.llm.llm_client import LLMClient


class ReportGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate_report(
        self,
        bug_data: StandardizedBugData,
        analysis_result: AnalysisResult,
        relevant_logs: List[LogEntry]
    ) -> str:
        # 准备上下文
        bug_desc = bug_data.bug_description
        
        # 构建分析摘要
        analysis_summary = self._build_analysis_summary(analysis_result)
        
        # 构建关键日志片段
        log_snippets = self._build_log_snippets(relevant_logs)
        
        system_prompt = """你是一个专业的Android技术支持工程师。请根据bug描述和日志分析结果，生成一份完整、专业的分析报告。

报告应该包含以下部分：
1. 问题概述 - 用简洁的语言总结问题
2. 环境信息 - 设备、系统版本等信息
3. 问题复现 - 复现步骤
4. 日志分析 - 基于日志的分析结果
5. 根因分析 - 问题的根本原因
6. 修复建议 - 具体的修复建议

请使用Markdown格式，保持专业、清晰的风格。"""

        user_prompt = f"""请生成一份bug分析报告。

Bug描述：
{bug_desc.raw_text}

提取的关键信息：
- 摘要：{bug_desc.summary}
- 包名：{bug_desc.package_name}
- 设备：{bug_desc.device_model}
- Android版本：{bug_desc.android_version}
- 预期行为：{bug_desc.expected_behavior}
- 实际行为：{bug_desc.actual_behavior}

日志分析结果：
{analysis_summary}

关键日志片段：
{log_snippets}"""

        report = self.llm_client.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=3000
        )

        return report

    def _build_analysis_summary(self, result: AnalysisResult) -> str:
        summary = []
        if result.crashes:
            summary.append(f"- 崩溃: {len(result.crashes)} 次")
        if result.anrs:
            summary.append(f"- ANR: {len(result.anrs)} 次")
        if result.low_memory:
            summary.append(f"- 低内存: {len(result.low_memory)} 次")
        if result.exceptions:
            summary.append(f"- 异常: {len(result.exceptions)} 次")
        return "\n".join(summary) if summary else "无明显异常"

    def _build_log_snippets(self, logs: List[LogEntry]) -> str:
        snippets = []
        for log in logs[:20]:  # 最多显示20条
            parts = []
            if log.timestamp:
                parts.append(f"[{log.timestamp}]")
            if log.level:
                parts.append(f"[{log.level}]")
            if log.tag:
                parts.append(f"[{log.tag}]")
            parts.append(log.message[:150])
            snippets.append(" ".join(parts))
        return "\n".join(snippets)
