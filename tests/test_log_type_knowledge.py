"""
测试日志类型知识库 — 规则先行 + LLM 兜底
- 置信度评分机制
- 两阶段识别流程
- LLM 缓存自学习
- Bug 类型感知优先级
- 集成测试
"""
import os
import json
import tempfile
import pytest
from log_analyzer.knowledge.log_type_knowledge import (
    LogTypeKnowledgeBase,
    LogTypeInfo,
    FileIdentification,
    Confidence,
    LOG_TYPE_REGISTRY,
    BUG_TYPE_KEYWORDS,
)


class TestConfidenceMechanism:
    """测试置信度评分机制"""

    def setup_method(self):
        self.kb = LogTypeKnowledgeBase()

    def test_known_pattern_high_confidence(self):
        ident = self.kb.identify_file("main_log_16__2026_0515_132645")
        assert ident.confidence == Confidence.HIGH
        assert ident.identified_by == "rule:known_pattern"

    def test_crash_log_high_confidence(self):
        ident = self.kb.identify_file("crash_log_1")
        assert ident.confidence == Confidence.HIGH
        assert ident.category == "android_core"

    def test_adsp_log_high_confidence(self):
        ident = self.kb.identify_file("adsp_1_log__2026_0515_132645")
        assert ident.confidence == Confidence.HIGH
        assert ident.category == "coprocessor"

    def test_log_extension_medium_confidence(self):
        ident = self.kb.identify_file("some_unknown.log")
        assert ident.confidence == Confidence.MEDIUM
        assert ident.identified_by == "rule:extension_heuristic"

    def test_txt_extension_low_confidence(self):
        ident = self.kb.identify_file("notes.txt")
        assert ident.confidence == Confidence.LOW

    def test_dmesg_high_confidence(self):
        ident = self.kb.identify_file("dmesg")
        assert ident.confidence == Confidence.HIGH
        assert ident.category == "kernel"

    def test_kmsg_high_confidence(self):
        ident = self.kb.identify_file("kmsg")
        assert ident.confidence == Confidence.HIGH
        assert ident.category == "kernel"

    def test_unknown_file_no_confidence(self):
        ident = self.kb.identify_file("xyz_abc_data")
        assert ident.confidence == Confidence.UNKNOWN
        assert ident.identified_by == "unknown"

    def test_known_pattern_takes_priority_over_extension(self):
        ident = self.kb.identify_file("crash_log_1.log")
        assert ident.confidence == Confidence.HIGH
        assert ident.category == "android_core"


class TestTwoStageIdentification:
    """测试两阶段识别流程"""

    def setup_method(self):
        self.kb = LogTypeKnowledgeBase()

    def test_batch_identification_split(self):
        files = [
            "/tmp/main_log_1",
            "/tmp/crash_log_1",
            "/tmp/unknown_data_file",
            "/tmp/adsp_1_log",
            "/tmp/random.bin",
        ]
        identified, needs_llm = self.kb.identify_files_batch(files)
        
        assert len(identified) >= 3
        assert len(needs_llm) >= 1
        
        identified_names = [f.filename for f in identified]
        assert "main_log_1" in identified_names
        assert "crash_log_1" in identified_names
        
        needs_llm_names = [f.filename for f in needs_llm]
        assert "random.bin" in needs_llm_names

    def test_batch_all_known(self):
        files = ["/tmp/main_log_1", "/tmp/crash_log_1", "/tmp/kernel_log_1"]
        identified, needs_llm = self.kb.identify_files_batch(files)
        assert len(identified) == 3
        assert len(needs_llm) == 0

    def test_batch_all_unknown(self):
        files = ["/tmp/abc", "/tmp/xyz", "/tmp/qqq"]
        identified, needs_llm = self.kb.identify_files_batch(files)
        assert len(identified) == 0
        assert len(needs_llm) == 3

    def test_llm_cache_hit(self):
        self.kb.apply_llm_results([{
            "filename": "custom_sensor_log",
            "category": "coprocessor",
            "description": "自定义传感器日志",
            "applicable_bug_types": ["sensor"],
            "priority": 6,
        }])
        
        ident = self.kb.identify_file("custom_sensor_log")
        assert ident.confidence == Confidence.MEDIUM
        assert ident.category == "coprocessor"
        assert ident.identified_by == "llm:cached"
        assert ident.llm_identified is True

    def test_llm_cache_miss_still_unknown(self):
        ident = self.kb.identify_file("never_seen_before_file")
        assert ident.confidence == Confidence.UNKNOWN


class TestLLMSelfLearning:
    """测试 LLM 缓存自学习"""

    def setup_method(self):
        self.kb = LogTypeKnowledgeBase()

    def test_apply_llm_results(self):
        results = [
            {
                "filename": "mdlog_1",
                "category": "modem",
                "description": "Modem 调试日志",
                "applicable_bug_types": ["modem", "network", "call"],
                "priority": 7,
            },
            {
                "filename": "sensor_hub_debug",
                "category": "coprocessor",
                "description": "Sensor Hub 调试日志",
                "applicable_bug_types": ["sensor"],
                "priority": 5,
            },
        ]
        
        self.kb.apply_llm_results(results)
        
        ident1 = self.kb.identify_file("mdlog_1")
        assert ident1.confidence == Confidence.MEDIUM
        assert ident1.category == "modem"
        assert "network" in ident1.applicable_bug_types
        
        ident2 = self.kb.identify_file("sensor_hub_debug")
        assert ident2.confidence == Confidence.MEDIUM
        assert ident2.category == "coprocessor"

    def test_llm_cached_file_in_batch(self):
        self.kb.apply_llm_results([{
            "filename": "mdlog_1",
            "category": "modem",
            "description": "Modem 调试日志",
            "applicable_bug_types": ["modem"],
            "priority": 7,
        }])
        
        files = ["/tmp/mdlog_1", "/tmp/unknown_file"]
        identified, needs_llm = self.kb.identify_files_batch(files)
        
        identified_names = [f.filename for f in identified]
        assert "mdlog_1" in identified_names
        
        needs_llm_names = [f.filename for f in needs_llm]
        assert "unknown_file" in needs_llm_names

    def test_parse_llm_identification_response(self):
        response = json.dumps({
            "results": [
                {
                    "filename": "custom_log",
                    "category": "android_core",
                    "description": "自定义日志",
                    "applicable_bug_types": ["crash"],
                    "priority": 5,
                    "is_relevant": True,
                }
            ]
        })
        
        results = self.kb.parse_llm_identification_response(response)
        assert len(results) == 1
        assert results[0]["filename"] == "custom_log"
        assert results[0]["is_relevant"] is True

    def test_parse_llm_response_with_markdown(self):
        response = '```json\n{"results": [{"filename": "test", "category": "boot", "description": "test", "applicable_bug_types": [], "priority": 3, "is_relevant": false}]}\n```'
        results = self.kb.parse_llm_identification_response(response)
        assert len(results) == 1

    def test_parse_llm_response_defaults(self):
        response = json.dumps({
            "results": [{"filename": "test"}]
        })
        results = self.kb.parse_llm_identification_response(response)
        assert results[0]["applicable_bug_types"] == []
        assert results[0]["priority"] == 3


class TestLLMIdentificationPrompt:
    """测试 LLM 识别提示词生成"""

    def setup_method(self):
        self.kb = LogTypeKnowledgeBase()

    def test_generate_identification_prompt(self):
        unknown_files = [
            FileIdentification(filename="mdlog_1", file_path="/tmp/mdlog_1", confidence=Confidence.UNKNOWN),
            FileIdentification(filename="custom_debug", file_path="/tmp/custom_debug", confidence=Confidence.UNKNOWN),
        ]
        
        system_prompt, user_prompt = self.kb.generate_llm_identification_prompt(
            unknown_files, ["crash", "audio"]
        )
        
        assert "mdlog_1" in user_prompt
        assert "custom_debug" in user_prompt
        assert "crash" in user_prompt
        assert "audio" in user_prompt
        assert "JSON" in system_prompt

    def test_identification_prompt_includes_knowledge(self):
        unknown_files = [
            FileIdentification(filename="test_file", confidence=Confidence.UNKNOWN),
        ]
        
        knowledge_context = self.kb.generate_llm_context(["crash"])
        system_prompt, user_prompt = self.kb.generate_llm_identification_prompt(
            unknown_files, ["crash"], knowledge_context
        )
        
        assert "MTK/Android 日志类型参考" in system_prompt


class TestBugTypeInference:
    """测试 Bug 类型推断"""

    def setup_method(self):
        self.kb = LogTypeKnowledgeBase()

    def test_crash_bug_type(self):
        types = self.kb.get_bug_types_from_description("应用崩溃闪退")
        assert "crash" in types

    def test_anr_bug_type(self):
        types = self.kb.get_bug_types_from_description("应用无响应ANR")
        assert "anr" in types

    def test_network_bug_type(self):
        types = self.kb.get_bug_types_from_description("WiFi断网无法连接")
        assert "network" in types

    def test_audio_bug_type(self):
        types = self.kb.get_bug_types_from_description("录音无声播放卡顿")
        assert "audio" in types

    def test_multiple_bug_types(self):
        types = self.kb.get_bug_types_from_description("应用崩溃后网络断连")
        assert "crash" in types
        assert "network" in types

    def test_default_bug_types(self):
        types = self.kb.get_bug_types_from_description("something went wrong")
        assert "crash" in types


class TestFilePriority:
    """测试 Bug 类型感知的文件优先级"""

    def setup_method(self):
        self.kb = LogTypeKnowledgeBase()

    def test_crash_bug_prioritizes_crash_log(self):
        crash_score = self.kb.get_priority_for_file("crash_log_1", ["crash"])
        adsp_score = self.kb.get_priority_for_file("adsp_1_log", ["crash"])
        assert crash_score > adsp_score

    def test_audio_bug_prioritizes_adsp_log(self):
        adsp_score = self.kb.get_priority_for_file("adsp_1_log", ["audio"])
        main_score = self.kb.get_priority_for_file("main_log_1", ["audio"])
        assert adsp_score >= main_score

    def test_unknown_file_low_priority(self):
        score = self.kb.get_priority_for_file("random_data.bin")
        assert score == 1

    def test_llm_cached_file_priority(self):
        self.kb.apply_llm_results([{
            "filename": "custom_log",
            "category": "android_core",
            "description": "自定义日志",
            "applicable_bug_types": ["crash"],
            "priority": 7,
        }])
        
        score = self.kb.get_priority_for_file("custom_log", ["crash"])
        assert score >= 7


class TestIdentificationSummary:
    """测试识别摘要统计"""

    def setup_method(self):
        self.kb = LogTypeKnowledgeBase()

    def test_summary_counts(self):
        files = [
            "/tmp/main_log_1",
            "/tmp/crash_log_1",
            "/tmp/unknown_file",
        ]
        
        summary = self.kb.get_identification_summary(files)
        assert summary["total"] == 3
        assert summary["high_confidence"] >= 2
        assert summary["unknown_needs_llm"] >= 1

    def test_summary_categories(self):
        files = ["/tmp/main_log_1", "/tmp/adsp_1_log"]
        summary = self.kb.get_identification_summary(files)
        assert "android_core" in summary["categories"]
        assert "coprocessor" in summary["categories"]


class TestMTKSpecificLogTypes:
    """测试 MTK 特定日志类型覆盖"""

    def setup_method(self):
        self.kb = LogTypeKnowledgeBase()

    def test_mtk_files_coverage(self):
        mtk_files = [
            "main_log_16__2026_0515_132645",
            "events_log_16__2026_0515_132645",
            "kernel_log_1__2026_0515_132645",
            "crash_log_1__2026_0515_132645",
            "radio_log_1__2026_0515_132645",
            "adsp_1_log__2026_0515_132645",
            "scp_log_1__2026_0515_132645",
            "sspm_log_1__2026_0515_132645",
            "mcupm_log_1__2026_0515_132645",
            "connsys_wifi_log__2026_0515_132645",
            "ccci_dpmaif_debug__2026_0515_132645",
            "atf_log_1__2026_0515_132645",
            "gz_log_1__2026_0515_132645",
            "bootprof",
            "pl_lk",
        ]
        
        identified = 0
        for filename in mtk_files:
            ident = self.kb.identify_file(filename)
            if ident.confidence == Confidence.HIGH:
                identified += 1
        
        assert identified >= 13, f"Only {identified}/15 MTK log types identified with HIGH confidence"


class TestRegistryIntegrity:
    """测试注册表完整性"""

    def test_all_entries_have_required_fields(self):
        for info in LOG_TYPE_REGISTRY:
            assert info.pattern
            assert info.category
            assert info.description
            assert isinstance(info.applicable_bug_types, list)
            assert info.priority_base > 0

    def test_all_entries_have_compiled_patterns(self):
        for info in LOG_TYPE_REGISTRY:
            assert info.compiled_pattern is not None

    def test_no_duplicate_patterns(self):
        patterns = [info.pattern for info in LOG_TYPE_REGISTRY]
        assert len(patterns) == len(set(patterns))


class TestIntegrationWithSelector:
    """测试与 LogFileSelectorSkill 的集成"""

    def test_selector_skill_has_knowledge(self):
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        assert hasattr(skill, '_knowledge')
        assert isinstance(skill._knowledge, LogTypeKnowledgeBase)

    def test_selector_skill_infers_bug_types(self):
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        bug_types = skill._knowledge.get_bug_types_from_description("应用崩溃ANR")
        assert "crash" in bug_types
        assert "anr" in bug_types

    def test_selector_skill_prioritizes(self):
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["crash_log_1.log", "main_log_1.log", "adsp_1.log"]:
                with open(os.path.join(tmpdir, name), 'w') as f:
                    f.write("x" * 100)
            
            files = [os.path.join(tmpdir, n) for n in ["crash_log_1.log", "main_log_1.log", "adsp_1.log"]]
            prioritized = skill._prioritize_with_knowledge(files, ["crash"])
            
            assert len(prioritized) == 3
            assert "crash_log" in prioritized[0]

    def test_selector_identification_summary_in_result(self):
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        skill.use_mock = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            extract_dir = os.path.join(tmpdir, "extracted")
            os.makedirs(extract_dir)
            
            log_file = os.path.join(extract_dir, "crash.log")
            with open(log_file, 'w') as f:
                f.write("05-09 19:14:34 E AndroidRuntime: FATAL EXCEPTION\n" * 100)
            
            result = skill.execute({
                "log_path": tmpdir,
                "log_extraction": {"data": {"extraction_dir": extract_dir}},
                "bug_description": {"raw_text": "应用崩溃", "summary": "崩溃"},
            })
            
            assert result.success
            assert "identification_summary" in result.data
