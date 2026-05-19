"""
测试 MTK 日志类型知识库
- LogTypeKnowledgeBase 核心功能
- Bug 类型推断
- 文件优先级排序
- LLM 上下文生成
- 集成到 LogFileSelectorSkill
"""
import os
import json
import tempfile
import pytest
from log_analyzer.knowledge.log_type_knowledge import (
    LogTypeKnowledgeBase,
    LogTypeInfo,
    LOG_TYPE_REGISTRY,
    BUG_TYPE_KEYWORDS,
)


class TestLogTypeIdentification:
    """测试日志类型识别"""

    def setup_method(self):
        self.kb = LogTypeKnowledgeBase()

    def test_identify_main_log(self):
        info = self.kb.identify_log_type("main_log_16__2026_0515_132645")
        assert info is not None
        assert info.category == "android_core"
        assert "crash" in info.applicable_bug_types

    def test_identify_crash_log(self):
        info = self.kb.identify_log_type("crash_log_1__2026_0515_132645")
        assert info is not None
        assert info.category == "android_core"
        assert "crash" in info.applicable_bug_types

    def test_identify_kernel_log(self):
        info = self.kb.identify_log_type("kernel_log_1")
        assert info is not None
        assert info.category == "android_core"
        assert "reboot" in info.applicable_bug_types

    def test_identify_adsp_log(self):
        info = self.kb.identify_log_type("adsp_1_log__2026_0515_132645")
        assert info is not None
        assert info.category == "coprocessor"
        assert "audio" in info.applicable_bug_types

    def test_identify_scp_log(self):
        info = self.kb.identify_log_type("scp_log_1__2026_0515_132645")
        assert info is not None
        assert info.category == "coprocessor"
        assert "sensor" in info.applicable_bug_types

    def test_identify_connsys_log(self):
        info = self.kb.identify_log_type("connsys_wifi_log__2026_0515_132645")
        assert info is not None
        assert info.category == "connectivity"
        assert "wifi" in info.applicable_bug_types

    def test_identify_bootprof(self):
        info = self.kb.identify_log_type("bootprof")
        assert info is not None
        assert info.category == "boot"
        assert "boot" in info.applicable_bug_types

    def test_identify_radio_log(self):
        info = self.kb.identify_log_type("radio_log_1")
        assert info is not None
        assert "network" in info.applicable_bug_types

    def test_identify_tombstone(self):
        info = self.kb.identify_log_type("tombstone_01")
        assert info is not None
        assert "crash" in info.applicable_bug_types

    def test_identify_traces(self):
        info = self.kb.identify_log_type("traces.txt")
        assert info is not None
        assert "anr" in info.applicable_bug_types

    def test_identify_unknown_file(self):
        info = self.kb.identify_log_type("random_data.bin")
        assert info is None

    def test_identify_sspm_log(self):
        info = self.kb.identify_log_type("sspm_log_1")
        assert info is not None
        assert "power" in info.applicable_bug_types

    def test_identify_ccci_log(self):
        info = self.kb.identify_log_type("ccci_dpmaif_debug_1")
        assert info is not None
        assert "modem" in info.applicable_bug_types


class TestBugTypeInference:
    """测试从 Bug 描述推断 Bug 类型"""

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

    def test_power_bug_type(self):
        types = self.kb.get_bug_types_from_description("手机耗电快待机功耗高")
        assert "power" in types

    def test_boot_bug_type(self):
        types = self.kb.get_bug_types_from_description("开机慢卡logo重启")
        assert "boot" in types

    def test_sensor_bug_type(self):
        types = self.kb.get_bug_types_from_description("传感器不工作陀螺仪失效")
        assert "sensor" in types

    def test_multiple_bug_types(self):
        types = self.kb.get_bug_types_from_description("应用崩溃后网络断连")
        assert "crash" in types
        assert "network" in types

    def test_default_bug_types(self):
        types = self.kb.get_bug_types_from_description("something went wrong")
        assert "crash" in types
        assert "anr" in types

    def test_english_bug_description(self):
        types = self.kb.get_bug_types_from_description("App crashed with fatal exception")
        assert "crash" in types

    def test_call_bug_type(self):
        types = self.kb.get_bug_types_from_description("通话断线电话打不进来")
        assert "call" in types

    def test_memory_bug_type(self):
        types = self.kb.get_bug_types_from_description("内存泄漏OOM低内存")
        assert "memory" in types


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

    def test_network_bug_prioritizes_connsys_log(self):
        connsys_score = self.kb.get_priority_for_file("connsys_wifi_log", ["network"])
        scp_score = self.kb.get_priority_for_file("scp_log_1", ["network"])
        assert connsys_score > scp_score

    def test_base_priority_without_bug_types(self):
        crash_score = self.kb.get_priority_for_file("crash_log_1")
        assert crash_score == 10

    def test_unknown_file_low_priority(self):
        score = self.kb.get_priority_for_file("random_data.bin")
        assert score == 1

    def test_recommended_files_ordering(self):
        files = [
            "/tmp/main_log_1",
            "/tmp/adsp_1_log",
            "/tmp/crash_log_1",
            "/tmp/scp_log_1",
            "/tmp/connsys_wifi_log",
        ]
        recommended = self.kb.get_recommended_files(files, ["crash", "audio"], max_files=3)
        
        filenames = [os.path.basename(f) for f in recommended]
        assert "crash_log_1" in filenames
        assert "main_log_1" in filenames

    def test_recommended_files_max_limit(self):
        files = [f"/tmp/file_{i}" for i in range(20)]
        recommended = self.kb.get_recommended_files(files, ["crash"], max_files=5)
        assert len(recommended) <= 5


class TestLLMContextGeneration:
    """测试 LLM 上下文生成"""

    def setup_method(self):
        self.kb = LogTypeKnowledgeBase()

    def test_generate_context_without_bug_types(self):
        context = self.kb.generate_llm_context()
        assert "MTK/Android 日志类型参考" in context
        assert "main_log" in context
        assert "crash_log" in context
        assert "adsp" in context

    def test_generate_context_with_bug_types(self):
        context = self.kb.generate_llm_context(["crash", "audio"])
        assert "⭐" in context
        assert "crash" in context
        assert "audio" in context

    def test_context_includes_categories(self):
        context = self.kb.generate_llm_context()
        assert "Android 系统核心日志" in context
        assert "启动与早期阶段日志" in context
        assert "协处理器" in context
        assert "连接子系统日志" in context


class TestLogTypeDescription:
    """测试日志类型描述"""

    def setup_method(self):
        self.kb = LogTypeKnowledgeBase()

    def test_known_file_description(self):
        desc = self.kb.get_log_type_description("main_log_1")
        assert "android_core" in desc
        assert "logcat" in desc.lower() or "main" in desc.lower()

    def test_unknown_file_description(self):
        desc = self.kb.get_log_type_description("random.bin")
        assert "未知类型" in desc


class TestKnowledgeBaseRegistry:
    """测试知识库注册表的完整性"""

    def test_all_entries_have_required_fields(self):
        for info in LOG_TYPE_REGISTRY:
            assert info.pattern, f"Missing pattern"
            assert info.category, f"Missing category for {info.pattern}"
            assert info.description, f"Missing description for {info.pattern}"
            assert isinstance(info.applicable_bug_types, list), f"applicable_bug_types not list for {info.pattern}"
            assert info.priority_base > 0, f"priority_base <= 0 for {info.pattern}"

    def test_all_entries_have_compiled_patterns(self):
        for info in LOG_TYPE_REGISTRY:
            assert info.compiled_pattern is not None, f"compiled_pattern is None for {info.pattern}"

    def test_bug_type_keywords_coverage(self):
        assert "crash" in BUG_TYPE_KEYWORDS
        assert "anr" in BUG_TYPE_KEYWORDS
        assert "network" in BUG_TYPE_KEYWORDS
        assert "audio" in BUG_TYPE_KEYWORDS
        assert "power" in BUG_TYPE_KEYWORDS
        assert "boot" in BUG_TYPE_KEYWORDS
        assert "sensor" in BUG_TYPE_KEYWORDS

    def test_no_duplicate_patterns(self):
        patterns = [info.pattern for info in LOG_TYPE_REGISTRY]
        assert len(patterns) == len(set(patterns)), "Duplicate patterns found"

    def test_mtk_specific_log_types_covered(self):
        kb = LogTypeKnowledgeBase()
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
            info = kb.identify_log_type(filename)
            if info:
                identified += 1
        
        assert identified >= 13, f"Only {identified}/15 MTK log types identified"


class TestIntegrationWithSelector:
    """测试知识库与 LogFileSelectorSkill 的集成"""

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
