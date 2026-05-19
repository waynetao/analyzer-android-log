import os
import json
import logging
from typing import Dict, Any, List, Set
from .base import LLMBasedSkill, SkillResult
from log_analyzer.extractor.log_file_selector import LogFileSelector, HIGH_PRIORITY_PATTERNS
from log_analyzer.knowledge.log_type_knowledge import LogTypeKnowledgeBase, Confidence

logger = logging.getLogger(__name__)

MUST_INCLUDE_PATTERNS = [
    "crash", "fatal", "anr", "tombstone", "watchdog",
    "logcat", "main_log", "system_log", "bugreport",
    "exception", "not_responding",
]


class LogFileSelectorSkill(LLMBasedSkill):
    """智能日志文件筛选技能 — 规则先行 + LLM 兜底

    三层筛选架构:
    1. 规则筛选（LogFileSelector）: 白名单/黑名单过滤，593→16
    2. 知识库识别（LogTypeKnowledgeBase）: 已知模式高置信直接用，未知文件标记
    3. LLM 兜底: 仅对未知/低置信文件调 LLM 识别，结果缓存自学习

    这样主流场景零 LLM 成本，长尾场景有 LLM 兜底。
    """
    
    input_mapping = {
        "log_path": "input:log_path",
        "bug_description": "input:bug_description",
        "extraction_dir": "output:log_extraction.data.extraction_dir",
    }
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        super().__init__(api_key, base_url, model, scene="file_selector")
        self._knowledge = LogTypeKnowledgeBase()
    
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
        bug_raw_text = bug_description.get("raw_text", bug_summary) if isinstance(bug_description, dict) else bug_summary
        
        bug_types = self._knowledge.get_bug_types_from_description(bug_raw_text)
        logger.info(f"  推断 Bug 类型: {bug_types}")
        
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
            
            identified, needs_llm = self._knowledge.identify_files_batch(rule_matched)
            logger.info(
                f"  知识库识别: {len(identified)} 个已知类型(高/中置信), "
                f"{len(needs_llm)} 个未知类型(需LLM识别)"
            )
            
            must_include = self._find_must_include_files(rule_matched)
            logger.info(f"  必选关键文件: {len(must_include)} 个")
            
            if needs_llm and self.client and not self.use_mock:
                llm_identified = self._llm_identify_unknown_files(needs_llm, bug_types)
                if llm_identified:
                    identified.extend(llm_identified)
                    needs_llm_remaining = [f for f in needs_llm if f.filename not in
                                           {r.filename for r in llm_identified}]
                    logger.info(f"  LLM 识别了 {len(llm_identified)} 个未知文件, "
                                f"剩余 {len(needs_llm_remaining)} 个无法识别")
            
            final_selected = rule_matched
            
            if self.client and not self.use_mock and identified:
                relevant_files = [
                    f.file_path for f in identified
                    if f.file_path and self._is_relevant_to_bug(f, bug_types)
                ]
                if relevant_files:
                    validated = self._validate_selection(relevant_files, rule_matched, must_include, extract_dir)
                    if validated:
                        final_selected = validated
            
            prioritized = self._prioritize_with_knowledge(final_selected, bug_types)
            logger.info(f"  最终分析文件数: {len(prioritized)}")
            
            file_type_info = {}
            for f in prioritized[:10]:
                filename = os.path.basename(f)
                ident = self._knowledge.identify_file(filename)
                conf_str = ident.confidence.value if ident.confidence else "unknown"
                file_type_info[filename] = f"[{ident.category}|{conf_str}] {ident.description}"
            
            id_summary = self._knowledge.get_identification_summary(rule_matched, bug_types)
            
            result = {
                "extraction_dir": extract_dir,
                "selected_files": prioritized,
                "total_selected": len(prioritized),
                "total_filtered": len(rule_filtered),
                "must_include_count": len(must_include),
                "identification_summary": id_summary,
                "selection_method": self._get_selection_method(),
                "bug_types": bug_types,
                "file_type_info": file_type_info,
            }
            
            return SkillResult(
                True,
                result,
                f"文件筛选完成: 选中 {len(prioritized)} 个, "
                f"过滤 {len(rule_filtered)} 个, "
                f"识别[{id_summary['high_confidence']}高/{id_summary['medium_confidence']}中/"
                f"{id_summary['unknown_needs_llm']}未知], "
                f"Bug类型: {bug_types}"
            )
            
        except Exception as e:
            return SkillResult(False, {}, f"文件筛选失败: {str(e)}")
    
    def _is_relevant_to_bug(self, ident, bug_types: List[str]) -> bool:
        """判断文件是否与当前 Bug 相关"""
        if ident.confidence == Confidence.HIGH:
            if not bug_types or not ident.applicable_bug_types:
                return True
            return bool(set(bug_types) & set(ident.applicable_bug_types))
        
        if ident.confidence == Confidence.MEDIUM:
            if ident.llm_identified:
                return bool(set(bug_types) & set(ident.applicable_bug_types)) if bug_types else True
            return True
        
        return True
    
    def _find_must_include_files(self, rule_matched: List[str]) -> List[str]:
        must_include = []
        for file_path in rule_matched:
            filename = os.path.basename(file_path).lower()
            for pattern in MUST_INCLUDE_PATTERNS:
                if pattern in filename:
                    must_include.append(file_path)
                    break
        return must_include
    
    def _prioritize_with_knowledge(self, files: List[str], bug_types: List[str]) -> List[str]:
        def score(file_path: str) -> int:
            filename = os.path.basename(file_path)
            score = self._knowledge.get_priority_for_file(filename, bug_types)
            try:
                file_size = os.path.getsize(file_path)
                if file_size > 1024 * 1024:
                    score += 2
                elif file_size > 100 * 1024:
                    score += 1
            except OSError:
                pass
            return score
        return sorted(files, key=score, reverse=True)
    
    def _validate_selection(
        self,
        selected: List[str],
        rule_matched: List[str],
        must_include: List[str],
        extract_dir: str
    ) -> List[str]:
        existing = set()
        for f in selected:
            if os.path.isfile(f):
                existing.add(f)
            else:
                abs_path = os.path.join(extract_dir, f)
                if os.path.isfile(abs_path):
                    existing.add(abs_path)
        
        must_set = set(must_include)
        missing_must = must_set - existing
        if missing_must:
            existing.update(missing_must)
            logger.info(f"  补回 {len(missing_must)} 个必选文件")
        
        if rule_matched and len(existing) < len(rule_matched) * 0.3:
            logger.warning("  选择文件过少，回退到规则匹配全量")
            return rule_matched
        
        return list(existing)
    
    def _llm_identify_unknown_files(
        self,
        unknown_files: List,
        bug_types: List[str]
    ) -> List:
        """LLM 识别未知文件类型（仅对未知文件调用，节省 Token）"""
        knowledge_context = self._knowledge.generate_llm_context(bug_types)
        system_prompt, user_prompt = self._knowledge.generate_llm_identification_prompt(
            unknown_files, bug_types, knowledge_context
        )
        
        try:
            response = self._call_llm(system_prompt, user_prompt, max_tokens=2000)
            results = self._knowledge.parse_llm_identification_response(response)
            
            if results:
                self._knowledge.apply_llm_results(results)
                
                llm_identified = []
                for item in results:
                    filename = item.get("filename", "")
                    is_relevant = item.get("is_relevant", True)
                    for uf in unknown_files:
                        if uf.filename == filename:
                            uf.category = item.get("category", "unknown")
                            uf.description = item.get("description", "")
                            uf.applicable_bug_types = item.get("applicable_bug_types", [])
                            uf.priority = item.get("priority", 3)
                            uf.confidence = Confidence.MEDIUM
                            uf.llm_identified = True
                            uf.identified_by = "llm"
                            llm_identified.append(uf)
                            break
                
                logger.info(f"  LLM 识别了 {len(llm_identified)} 个未知文件")
                return llm_identified
            
        except Exception as e:
            logger.warning(f"LLM 识别未知文件失败: {e}")
        
        return []
    
    def _get_selection_method(self) -> str:
        has_llm = self.client and not self.use_mock
        if has_llm:
            return "rules+knowledge+llm"
        return "rules+knowledge"
