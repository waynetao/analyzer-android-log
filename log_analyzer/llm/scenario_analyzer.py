from typing import List
from log_analyzer.models import ScenarioQuery
from log_analyzer.parser.log_parser import LogEntry
from log_analyzer.llm.llm_client import LLMClient


class ScenarioAnalyzer:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def analyze(
        self,
        query: str,
        logs: List[LogEntry],
        context: str = ""
    ) -> ScenarioQuery:
        # 首先过滤相关日志
        relevant_logs = self._filter_relevant_logs(query, logs)
        
        system_prompt = """你是一个专业的Android日志分析专家。请根据用户的问题和提供的日志片段，给出详细的分析和解释。

回答应该包含：
1. 对问题的理解
2. 基于日志的分析过程
3. 发现的关键信息
4. 结论和建议

请用中文回答，保持专业和清晰。"""

        # 构建日志上下文
        log_context = self._build_log_context(relevant_logs)
        
        user_prompt = f"""用户问题：{query}

附加上下文：{context}

相关日志：
{log_context}

请根据以上信息进行分析。"""

        analysis = self.llm_client.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=2000
        )

        return ScenarioQuery(
            query=query,
            context=context,
            relevant_logs=relevant_logs,
            analysis_result=analysis
        )

    def _filter_relevant_logs(self, query: str, logs: List[LogEntry]) -> List[LogEntry]:
        """简单的关键词过滤，找到相关日志"""
        query_words = set(query.lower().split())
        relevant = []
        
        for log in logs:
            log_text = log.message.lower()
            if log.tag:
                log_text += " " + log.tag.lower()
            
            # 检查是否有共同关键词
            for word in query_words:
                if len(word) > 1 and word in log_text:
                    relevant.append(log)
                    break
                    
        return relevant[:50]  # 最多50条

    def _build_log_context(self, logs: List[LogEntry]) -> str:
        lines = []
        for log in logs:
            parts = []
            if log.timestamp:
                parts.append(log.timestamp)
            if log.level:
                parts.append(log.level)
            if log.tag:
                parts.append(log.tag)
            parts.append(log.message)
            lines.append(" | ".join(parts))
        return "\n".join(lines)
