import os
import json
import logging
from typing import Dict, Any, List, Set
from .base import LLMBasedSkill, SkillResult
from log_analyzer.extractor.log_file_selector import LogFileSelector, HIGH_PRIORITY_PATTERNS

logger = logging.getLogger(__name__)

MUST_INCLUDE_PATTERNS = [
    "crash", "fatal", "anr", "tombstone", "watchdog",
    "logcat", "main_log", "system_log", "bugreport",
    "exception", "not_responding",
]


class LogFileSelectorSkill(LLMBasedSkill):
    """LLM 智能日志文件筛选技能
    
    将解压后的目录结构发送给 LLM，让 LLM 根据 Bug 描述
    判断哪些文件是相关的日志文件，避免分析无关文件
    
    可靠性保障:
    1. 规则筛选作为基础（白名单+黑名单）
    2. LLM 筛选作为增强（理解 Bug 语义）
    3. 必选文件校验（crash/ANR/logcat 等关键文件不可遗漏）
    4. 覆盖率校验（LLM 选择结果不能比规则匹配少太多）
    5. 文件存在性校验（LLM 可能返回不存在的路径）
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
            
            must_include = self._find_must_include_files(rule_matched)
            logger.info(f"  必选关键文件: {len(must_include)} 个")
            
            final_selected = rule_matched
            
            if self.client and not self.use_mock:
                llm_selected = self._llm_select_files(selector, extract_dir, bug_summary, rule_matched)
                if llm_selected is not None:
                    validated = self._validate_llm_selection(
                        llm_selected, rule_matched, must_include, extract_dir
                    )
                    final_selected = validated
            
            prioritized = selector.prioritize(final_selected)
            logger.info(f"  最终分析文件数: {len(prioritized)}")
            
            result = {
                "extraction_dir": extract_dir,
                "selected_files": prioritized,
                "total_selected": len(prioritized),
                "total_filtered": len(rule_filtered),
                "must_include_count": len(must_include),
                "selection_method": "llm+rules" if (self.client and not self.use_mock) else "rules_only"
            }
            
            return SkillResult(
                True,
                result,
                f"文件筛选完成: 选中 {len(prioritized)} 个文件, 过滤 {len(rule_filtered)} 个文件"
            )
            
        except Exception as e:
            return SkillResult(False, {}, f"文件筛选失败: {str(e)}")
    
    def _find_must_include_files(self, rule_matched: List[str]) -> List[str]:
        """找出必须包含的关键文件（crash/ANR/logcat 等）"""
        must_include = []
        for file_path in rule_matched:
            filename = os.path.basename(file_path).lower()
            for pattern in MUST_INCLUDE_PATTERNS:
                if pattern in filename:
                    must_include.append(file_path)
                    break
        return must_include
    
    def _validate_llm_selection(
        self,
        llm_selected: List[str],
        rule_matched: List[str],
        must_include: List[str],
        extract_dir: str
    ) -> List[str]:
        """验证 LLM 选择结果，确保可靠性
        
        校验规则:
        1. 必选文件不能遗漏
        2. LLM 选择数量不能少于规则匹配的 30%（否则可能漏选太多）
        3. 所有选择的文件必须存在
        """
        rule_set = set(rule_matched)
        llm_set = set(llm_selected)
        must_set = set(must_include)
        
        existing_files = set()
        for f in llm_selected:
            if os.path.isfile(f):
                existing_files.add(f)
            else:
                abs_path = os.path.join(extract_dir, f)
                if os.path.isfile(abs_path):
                    existing_files.add(abs_path)
        
        missing_must = must_set - existing_files
        if missing_must:
            logger.warning(f"  LLM 遗漏了 {len(missing_must)} 个必选文件，已自动补回")
            existing_files.update(missing_must)
        
        if rule_matched and len(existing_files) < len(rule_matched) * 0.3:
            logger.warning(
                f"  LLM 选择 {len(existing_files)} 个文件，"
                f"仅为规则匹配 {len(rule_matched)} 个的 {len(existing_files)/len(rule_matched)*100:.0f}%，"
                f"可能漏选过多，回退到规则匹配"
            )
            return rule_matched
        
        if missing_must:
            logger.info(f"  验证后文件数: {len(existing_files)} (补回 {len(missing_must)} 个必选文件)")
        
        return list(existing_files)
    
    def _llm_select_files(
        self,
        selector: LogFileSelector,
        extract_dir: str,
        bug_summary: str,
        rule_matched: List[str]
    ) -> List[str]:
        """使用 LLM 从规则匹配的文件中进一步筛选"""
        manifest = selector.generate_file_manifest(extract_dir, matched_files=rule_matched)
        
        if len(manifest) > 15000:
            manifest = manifest[:15000] + "\n... (文件清单过长，已截断)"
        
        system_prompt = """你是一个 Android 日志分析专家。你的任务是根据 Bug 描述，从解压后的 bugreport 目录中筛选出最相关的日志文件。

筛选原则：
1. 优先选择与 Bug 描述直接相关的日志（如崩溃日志、ANR 日志、对应模块日志）
2. 排除与 Bug 无关的文件（如截图、配置备份、蓝牙日志等）
3. 如果不确定，宁可多选不要漏选
4. 注意文件大小，过大的文件可能包含大量无关信息
5. 以下类型的文件必须选择，不可遗漏：crash、fatal、ANR、tombstone、logcat、main_log

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
            
            reasoning = data.get("reasoning", "")
            if reasoning:
                logger.info(f"  LLM 筛选理由: {reasoning[:200]}")
            
            selected_absolute = []
            for rel_path in selected_relative:
                abs_path = os.path.join(extract_dir, rel_path)
                if os.path.isfile(abs_path):
                    selected_absolute.append(abs_path)
                elif os.path.isfile(rel_path):
                    selected_absolute.append(rel_path)
            
            if not selected_absolute:
                logger.warning("LLM 选择的文件均不存在，回退到规则匹配")
                return fallback
            
            return selected_absolute
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"解析 LLM 文件选择结果失败: {e}，回退到规则匹配")
            return fallback
