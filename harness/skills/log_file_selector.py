import os
import json
import logging
from typing import Dict, Any, List
from .base import LLMBasedSkill, SkillResult
from log_analyzer.extractor.log_file_selector import LogFileSelector

logger = logging.getLogger(__name__)


class LogFileSelectorSkill(LLMBasedSkill):
    """LLM 智能日志文件筛选技能
    
    将解压后的目录结构发送给 LLM，让 LLM 根据 Bug 描述
    判断哪些文件是相关的日志文件，避免分析无关文件
    """
    
    input_mapping = {
        "log_path": "input:log_path",
        "bug_description": "input:bug_description",
        "extraction_dir": "output:log_extraction.data.extraction_dir",
    }
    
    @property
    def name(self) -> str:
        return "log_file_selector"
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["log_path"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        log_path = inputs["log_path"]
        bug_description = inputs.get("bug_description", {})
        bug_summary = bug_description.get("summary", "") if isinstance(bug_description, dict) else str(bug_description)
        
        prev_output = inputs.get("log_extraction", {})
        if isinstance(prev_output, dict):
            extract_dir = prev_output.get("data", {}).get("extraction_dir")
        else:
            extract_dir = None
        
        if not extract_dir or not os.path.isdir(extract_dir):
            return SkillResult(False, {}, "未找到解压目录，请先运行 log_extraction")
        
        try:
            selector = LogFileSelector(bug_description=bug_summary)
            
            rule_matched, rule_filtered = selector.scan_directory(extract_dir)
            logger.info(f"  规则匹配日志文件: {len(rule_matched)}, 规则过滤文件: {len(rule_filtered)}")
            
            if self.client and not self.use_mock:
                llm_selected = self._llm_select_files(selector, extract_dir, bug_summary, rule_matched)
                if llm_selected is not None:
                    rule_matched = llm_selected
            
            prioritized = selector.prioritize(rule_matched)
            logger.info(f"  最终分析文件数: {len(prioritized)}")
            
            result = {
                "extraction_dir": extract_dir,
                "selected_files": prioritized,
                "total_selected": len(prioritized),
                "total_filtered": len(rule_filtered),
                "selection_method": "llm+rules" if (self.client and not self.use_mock) else "rules_only"
            }
            
            return SkillResult(
                True,
                result,
                f"文件筛选完成: 选中 {len(prioritized)} 个文件, 过滤 {len(rule_filtered)} 个文件"
            )
            
        except Exception as e:
            return SkillResult(False, {}, f"文件筛选失败: {str(e)}")
    
    def _llm_select_files(
        self,
        selector: LogFileSelector,
        extract_dir: str,
        bug_summary: str,
        rule_matched: List[str]
    ) -> List[str]:
        """使用 LLM 从规则匹配的文件中进一步筛选"""
        manifest = selector.generate_file_manifest(extract_dir)
        
        if len(manifest) > 15000:
            manifest = manifest[:15000] + "\n... (文件清单过长，已截断)"
        
        system_prompt = """你是一个 Android 日志分析专家。你的任务是根据 Bug 描述，从解压后的 bugreport 目录中筛选出最相关的日志文件。

筛选原则：
1. 优先选择与 Bug 描述直接相关的日志（如崩溃日志、ANR 日志、对应模块日志）
2. 排除与 Bug 无关的文件（如截图、配置备份、蓝牙日志等）
3. 如果不确定，宁可多选不要漏选
4. 注意文件大小，过大的文件可能包含大量无关信息

请以 JSON 格式返回，格式如下：
{
  "selected_files": ["relative/path/to/file1", "relative/path/to/file2"],
  "reasoning": "选择这些文件的原因"
}"""

        user_prompt = f"""Bug 描述: {bug_summary}

解压后的文件清单:
{manifest}

请从上述文件中筛选出与 Bug 分析最相关的日志文件。返回 JSON 格式。"""

        try:
            response = self._call_llm(system_prompt, user_prompt, max_tokens=2000)
            return self._parse_llm_response(response, extract_dir, rule_matched)
        except Exception as e:
            logger.warning(f"LLM 文件筛选失败，回退到规则匹配: {e}")
            return None
    
    def _parse_llm_response(
        self,
        response: str,
        extract_dir: str,
        fallback: List[str]
    ) -> List[str]:
        """解析 LLM 返回的文件列表"""
        try:
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            
            data = json.loads(json_str.strip())
            selected_relative = data.get("selected_files", [])
            
            selected_absolute = []
            for rel_path in selected_relative:
                abs_path = os.path.join(extract_dir, rel_path)
                if os.path.isfile(abs_path):
                    selected_absolute.append(abs_path)
            
            if not selected_absolute:
                logger.warning("LLM 选择的文件均不存在，回退到规则匹配")
                return fallback
            
            return selected_absolute
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"解析 LLM 文件选择结果失败: {e}，回退到规则匹配")
            return fallback
