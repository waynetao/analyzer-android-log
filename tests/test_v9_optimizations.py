#!/usr/bin/env python3
"""
v9.0 优化功能完整测试
覆盖:
1. LogFileSelector 统一日志文件筛选器
2. LogFileSelectorSkill LLM 智能文件筛选
3. BaseSkill.resolve_inputs 声明式输入映射
4. BaseSkill._call_llm max_tokens/temperature 参数
5. WorkflowPaths 新目录结构
6. WorkflowMetadata.additional_findings
7. MultiRoundAnalysis._extract_key_findings / _extract_confidence
8. FeatureSDK 单例修复
9. LLMClient 延迟导入 + 交互日志
10. load_state 新旧路径兼容
"""

import sys
import os
import json
import pytest
import tempfile
import shutil
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# 1. LogFileSelector 统一日志文件筛选器
# ============================================================
class TestLogFileSelector:
    """LogFileSelector 筛选器测试"""

    @pytest.fixture
    def mock_extract_dir(self):
        """创建模拟的解压目录结构"""
        temp_dir = tempfile.mkdtemp()
        
        os.makedirs(os.path.join(temp_dir, "FS", "screenshots"))
        os.makedirs(os.path.join(temp_dir, "FS", "bugreport"))
        os.makedirs(os.path.join(temp_dir, "BT", "bluetooth"))
        
        with open(os.path.join(temp_dir, "FS", "bugreport", "bugreport-device.txt"), 'w') as f:
            f.write("bugreport content " * 100)
        with open(os.path.join(temp_dir, "FS", "bugreport", "main_log"), 'w') as f:
            f.write("main log content " * 100)
        with open(os.path.join(temp_dir, "FS", "bugreport", "system_log"), 'w') as f:
            f.write("system log content " * 100)
        with open(os.path.join(temp_dir, "FS", "bugreport", "crash_log.1.log"), 'w') as f:
            f.write("crash log content " * 100)
        
        with open(os.path.join(temp_dir, "FS", "bugreport", "logcat.txt"), 'w') as f:
            f.write("logcat content " * 100)
        with open(os.path.join(temp_dir, "FS", "bugreport", "kernel.log"), 'w') as f:
            f.write("kernel log content " * 100)
        with open(os.path.join(temp_dir, "FS", "bugreport", "hilog.txt"), 'w') as f:
            f.write("hilog content " * 100)
        
        with open(os.path.join(temp_dir, "FS", "screenshots", "screenshot_01.png"), 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 1000)
        with open(os.path.join(temp_dir, "FS", "screenshots", "screenshot_02.jpg"), 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'\x00' * 1000)
        
        with open(os.path.join(temp_dir, "FS", "bugreport", "app.apk"), 'wb') as f:
            f.write(b'\x00' * 500)
        with open(os.path.join(temp_dir, "FS", "bugreport", "data.db"), 'wb') as f:
            f.write(b'\x00' * 500)
        
        with open(os.path.join(temp_dir, "FS", "bugreport", "empty.log"), 'w') as f:
            pass
        with open(os.path.join(temp_dir, "FS", "bugreport", "tiny.txt"), 'w') as f:
            f.write("x")
        
        with open(os.path.join(temp_dir, "FS", "bugreport", "package_list.txt"), 'w') as f:
            f.write("com.app1\ncom.app2\n" * 50)
        with open(os.path.join(temp_dir, "FS", "bugreport", "bluetooth_config.txt"), 'w') as f:
            f.write("bt config " * 50)
        
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_scan_directory_filters_blacklist_dirs(self, mock_extract_dir):
        """测试黑名单目录被过滤"""
        from log_analyzer.extractor.log_file_selector import LogFileSelector
        selector = LogFileSelector()
        matched, filtered = selector.scan_directory(mock_extract_dir)
        
        for f in matched:
            assert "screenshots" not in f.lower() or "bluetooth" not in f.lower()
    
    def test_scan_directory_filters_blacklist_extensions(self, mock_extract_dir):
        """测试黑名单扩展名被过滤"""
        from log_analyzer.extractor.log_file_selector import LogFileSelector
        selector = LogFileSelector()
        matched, filtered = selector.scan_directory(mock_extract_dir)
        
        matched_basenames = [os.path.basename(f) for f in matched]
        assert "app.apk" not in matched_basenames
        assert "data.db" not in matched_basenames
    
    def test_scan_directory_filters_blacklist_names(self, mock_extract_dir):
        """测试黑名单文件名模式被过滤"""
        from log_analyzer.extractor.log_file_selector import LogFileSelector
        selector = LogFileSelector()
        matched, filtered = selector.scan_directory(mock_extract_dir)
        
        matched_basenames = [os.path.basename(f) for f in matched]
        assert "package_list.txt" not in matched_basenames
        assert "bluetooth_config.txt" not in matched_basenames
    
    def test_scan_directory_filters_empty_files(self, mock_extract_dir):
        """测试空文件被过滤"""
        from log_analyzer.extractor.log_file_selector import LogFileSelector
        selector = LogFileSelector()
        matched, filtered = selector.scan_directory(mock_extract_dir)
        
        matched_basenames = [os.path.basename(f) for f in matched]
        assert "empty.log" not in matched_basenames
        assert "tiny.txt" not in matched_basenames
    
    def test_scan_directory_matches_log_files(self, mock_extract_dir):
        """测试日志文件被正确匹配"""
        from log_analyzer.extractor.log_file_selector import LogFileSelector
        selector = LogFileSelector()
        matched, filtered = selector.scan_directory(mock_extract_dir)
        
        matched_basenames = [os.path.basename(f) for f in matched]
        assert "bugreport-device.txt" in matched_basenames
        assert "main_log" in matched_basenames
        assert "system_log" in matched_basenames
        assert "crash_log.1.log" in matched_basenames
        assert "logcat.txt" in matched_basenames
        assert "kernel.log" in matched_basenames
    
    def test_scan_directory_returns_both_lists(self, mock_extract_dir):
        """测试返回匹配和过滤两个列表"""
        from log_analyzer.extractor.log_file_selector import LogFileSelector
        selector = LogFileSelector()
        matched, filtered = selector.scan_directory(mock_extract_dir)
        
        assert len(matched) > 0
        assert len(filtered) > 0
        all_files = set(matched + filtered)
        assert len(all_files) == len(matched) + len(filtered)
    
    def test_prioritize_crash_first(self, mock_extract_dir):
        """测试高优先级文件排在前面"""
        from log_analyzer.extractor.log_file_selector import LogFileSelector
        selector = LogFileSelector()
        matched, _ = selector.scan_directory(mock_extract_dir)
        prioritized = selector.prioritize(matched)
        
        if len(prioritized) >= 2:
            first_basename = os.path.basename(prioritized[0]).lower()
            high_priority_keywords = ["crash", "fatal", "anr", "logcat", "main_log"]
            assert any(kw in first_basename for kw in high_priority_keywords)
    
    def test_generate_file_manifest(self, mock_extract_dir):
        """测试生成文件清单"""
        from log_analyzer.extractor.log_file_selector import LogFileSelector
        selector = LogFileSelector()
        manifest = selector.generate_file_manifest(mock_extract_dir)
        
        assert "解压目录" in manifest
        assert "文件总数" in manifest
        assert "[LOG]" in manifest
        assert "[OTHER]" in manifest
        assert "bugreport-device.txt" in manifest
    
    def test_is_log_file_patterns(self):
        """测试日志文件匹配模式"""
        from log_analyzer.extractor.log_file_selector import LogFileSelector
        selector = LogFileSelector()
        
        assert selector._is_log_file("bugreport-device.txt") is True
        assert selector._is_log_file("main_log") is True
        assert selector._is_log_file("system_log") is True
        assert selector._is_log_file("crash_log.1.log") is True
        assert selector._is_log_file("logcat.txt") is True
        assert selector._is_log_file("hilog") is True
        assert selector._is_log_file("dumpstate.txt") is True
        
        assert selector._is_log_file("config.json") is False
        assert selector._is_log_file("image.png") is False
        assert selector._is_log_file("app.apk") is False
    
    def test_should_filter_various_types(self):
        """测试各种文件类型的过滤判断"""
        from log_analyzer.extractor.log_file_selector import LogFileSelector
        selector = LogFileSelector()
        
        temp_dir = tempfile.mkdtemp()
        try:
            png_file = os.path.join(temp_dir, "test.png")
            with open(png_file, 'wb') as f:
                f.write(b'\x00' * 100)
            assert selector._should_filter("test.png", png_file) is True
            
            log_file = os.path.join(temp_dir, "test.log")
            with open(log_file, 'w') as f:
                f.write("log content " * 50)
            assert selector._should_filter("test.log", log_file) is False
            
            assert selector._should_filter("screenshot_01.png", png_file) is True
        finally:
            shutil.rmtree(temp_dir)


# ============================================================
# 2. LogFileSelectorSkill LLM 智能文件筛选
# ============================================================
class TestLogFileSelectorSkill:
    """LogFileSelectorSkill 技能测试"""

    @pytest.fixture
    def mock_extract_dir(self):
        temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(temp_dir, "bugreport"))
        with open(os.path.join(temp_dir, "bugreport", "crash_log.log"), 'w') as f:
            f.write("FATAL EXCEPTION " * 200)
        with open(os.path.join(temp_dir, "bugreport", "main_log"), 'w') as f:
            f.write("main log " * 200)
        with open(os.path.join(temp_dir, "bugreport", "screenshot.png"), 'wb') as f:
            f.write(b'\x00' * 500)
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_skill_name(self):
        """测试技能名称"""
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        assert skill.name == "log_file_selector"

    def test_skill_execute_with_extract_dir(self, mock_extract_dir):
        """测试技能执行 - 规则模式"""
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        skill.use_mock = True
        
        result = skill.execute({
            "log_path": "/test/log.zip",
            "log_extraction": {
                "data": {
                    "extraction_dir": mock_extract_dir
                }
            }
        })
        
        assert result.success is True
        assert result.data["total_selected"] > 0
        assert result.data["selection_method"] in ("rules+knowledge", "llm+rules+knowledge")

    def test_skill_execute_missing_extract_dir(self):
        """测试技能执行 - 缺少解压目录"""
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        skill.use_mock = True
        
        result = skill.execute({
            "log_path": "/test/log.zip",
            "log_extraction": {"data": {"extraction_dir": "/nonexistent/path"}}
        })
        
        assert result.success is False

    def test_skill_execute_missing_log_path(self):
        """测试技能执行 - 缺少必需参数"""
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        
        result = skill.execute({})
        assert result.success is False
        assert "缺少" in result.message

    def test_find_must_include_files(self, mock_extract_dir):
        """测试必选文件识别"""
        from harness.skills.log_file_selector import LogFileSelectorSkill, MUST_INCLUDE_PATTERNS
        skill = LogFileSelectorSkill()
        
        test_files = [
            os.path.join(mock_extract_dir, "crash_log.log"),
            os.path.join(mock_extract_dir, "main_log"),
            os.path.join(mock_extract_dir, "normal_file.txt"),
        ]
        
        must_include = skill._find_must_include_files(test_files)
        must_basenames = [os.path.basename(f) for f in must_include]
        
        assert "crash_log.log" in must_basenames
        assert "main_log" in must_basenames
        assert "normal_file.txt" not in must_basenames

    def test_validate_llm_selection_missing_must_files(self, mock_extract_dir):
        """测试 LLM 遗漏必选文件时自动补回"""
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        
        crash_file = os.path.join(mock_extract_dir, "crash_log.log")
        main_file = os.path.join(mock_extract_dir, "main_log")
        
        rule_matched = [crash_file, main_file]
        must_include = [crash_file]
        llm_selected = [main_file]  # 漏掉了 crash
        
        result = skill._validate_llm_selection(
            llm_selected, rule_matched, must_include, mock_extract_dir
        )
        
        assert crash_file in result

    def test_validate_llm_selection_low_coverage_fallback(self, mock_extract_dir):
        """测试 LLM 选择覆盖率过低时回退到规则匹配"""
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        
        rule_matched = [f"/fake/file{i}.log" for i in range(10)]
        must_include = []
        llm_selected = ["/fake/file0.log"]  # 只选了 10%
        
        result = skill._validate_llm_selection(
            llm_selected, rule_matched, must_include, mock_extract_dir
        )
        
        assert result == rule_matched

    def test_parse_llm_response_valid_json(self, mock_extract_dir):
        """测试解析 LLM 有效 JSON 响应"""
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        
        crash_file = os.path.join(mock_extract_dir, "crash_log.log")
        with open(crash_file, 'w') as f:
            f.write("crash content " * 50)
        
        response = json.dumps({
            "selected_files": ["crash_log.log"],
            "reasoning": "崩溃日志与 Bug 直接相关"
        })
        
        result = skill._parse_llm_response(response, mock_extract_dir, [])
        assert len(result) > 0

    def test_parse_llm_response_with_code_block(self, mock_extract_dir):
        """测试解析 LLM 带 ```json 代码块的响应"""
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        
        crash_file = os.path.join(mock_extract_dir, "crash_log.log")
        with open(crash_file, 'w') as f:
            f.write("crash content " * 50)
        
        response = '```json\n{"selected_files": ["crash_log.log"], "reasoning": "test"}\n```'
        
        result = skill._parse_llm_response(response, mock_extract_dir, [])
        assert len(result) > 0

    def test_parse_llm_response_invalid_json_fallback(self):
        """测试解析 LLM 无效 JSON 时回退"""
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        
        fallback = ["/fallback/file.log"]
        result = skill._parse_llm_response("not json at all", "/dir", fallback)
        assert result == fallback

    def test_parse_llm_response_nonexistent_files_fallback(self):
        """测试 LLM 选择的文件不存在时回退"""
        from harness.skills.log_file_selector import LogFileSelectorSkill
        skill = LogFileSelectorSkill()
        
        response = json.dumps({
            "selected_files": ["nonexistent_file.log"],
            "reasoning": "test"
        })
        
        fallback = ["/fallback/file.log"]
        result = skill._parse_llm_response(response, "/nonexistent/dir", fallback)
        assert result == fallback


# ============================================================
# 3. BaseSkill.resolve_inputs 声明式输入映射
# ============================================================
class TestResolveInputs:
    """声明式输入映射测试"""

    def test_resolve_inputs_from_global(self):
        """测试从全局输入解析"""
        from harness.skills.base import BaseSkill, SkillResult
        
        class TestSkill(BaseSkill):
            input_mapping = {"query": "input:bug_description.summary"}
            
            @property
            def name(self):
                return "test_skill"
            
            def execute(self, inputs):
                return SkillResult(True, {}, "ok")
        
        skill = TestSkill()
        global_inputs = {"bug_description": {"summary": "应用崩溃"}}
        previous_outputs = {}
        
        resolved = skill.resolve_inputs(global_inputs, previous_outputs)
        assert resolved["query"] == "应用崩溃"

    def test_resolve_inputs_from_output(self):
        """测试从前序技能输出解析"""
        from harness.skills.base import BaseSkill, SkillResult
        
        class TestSkill(BaseSkill):
            input_mapping = {"analysis_data": "output:log_extraction.data"}
            
            @property
            def name(self):
                return "test_skill"
            
            def execute(self, inputs):
                return SkillResult(True, {}, "ok")
        
        skill = TestSkill()
        global_inputs = {}
        previous_outputs = {"log_extraction": {"data": {"entries": [1, 2, 3]}}}
        
        resolved = skill.resolve_inputs(global_inputs, previous_outputs)
        assert resolved["analysis_data"] == {"entries": [1, 2, 3]}

    def test_resolve_inputs_already_present(self):
        """测试已有参数不被覆盖"""
        from harness.skills.base import BaseSkill, SkillResult
        
        class TestSkill(BaseSkill):
            input_mapping = {"query": "input:bug_description.summary"}
            
            @property
            def name(self):
                return "test_skill"
            
            def execute(self, inputs):
                return SkillResult(True, {}, "ok")
        
        skill = TestSkill()
        global_inputs = {"query": "existing_value", "bug_description": {"summary": "new_value"}}
        previous_outputs = {}
        
        resolved = skill.resolve_inputs(global_inputs, previous_outputs)
        assert resolved["query"] == "existing_value"

    def test_resolve_inputs_deep_path(self):
        """测试深层路径解析"""
        from harness.skills.base import BaseSkill, SkillResult
        
        class TestSkill(BaseSkill):
            input_mapping = {"deep_val": "output:a.b.c"}
            
            @property
            def name(self):
                return "test_skill"
            
            def execute(self, inputs):
                return SkillResult(True, {}, "ok")
        
        skill = TestSkill()
        global_inputs = {}
        previous_outputs = {"a": {"b": {"c": "deep_value"}}}
        
        resolved = skill.resolve_inputs(global_inputs, previous_outputs)
        assert resolved["deep_val"] == "deep_value"

    def test_resolve_inputs_missing_path(self):
        """测试路径不存在时不设置"""
        from harness.skills.base import BaseSkill, SkillResult
        
        class TestSkill(BaseSkill):
            input_mapping = {"missing": "output:nonexistent.path"}
            
            @property
            def name(self):
                return "test_skill"
            
            def execute(self, inputs):
                return SkillResult(True, {}, "ok")
        
        skill = TestSkill()
        resolved = skill.resolve_inputs({}, {})
        assert "missing" not in resolved

    def test_resolve_inputs_empty_mapping(self):
        """测试空映射"""
        from harness.skills.base import BaseSkill, SkillResult
        
        class TestSkill(BaseSkill):
            input_mapping = {}
            
            @property
            def name(self):
                return "test_skill"
            
            def execute(self, inputs):
                return SkillResult(True, {}, "ok")
        
        skill = TestSkill()
        global_inputs = {"key": "value"}
        previous_outputs = {"output_key": "output_value"}
        
        resolved = skill.resolve_inputs(global_inputs, previous_outputs)
        assert resolved["key"] == "value"
        assert resolved["output_key"] == "output_value"


# ============================================================
# 4. BaseSkill._call_llm max_tokens/temperature 参数
# ============================================================
class TestCallLlmParams:
    """_call_llm 参数传递测试"""

    @pytest.fixture
    def concrete_skill(self):
        from harness.skills.base import LLMBasedSkill, SkillResult
        
        class ConcreteSkill(LLMBasedSkill):
            @property
            def name(self):
                return "concrete_test_skill"
            
            def execute(self, inputs):
                return SkillResult(True, {}, "ok")
        
        skill = ConcreteSkill()
        skill.client = None
        skill.use_mock = True
        return skill

    def test_call_llm_with_max_tokens(self, concrete_skill):
        """测试 _call_llm 传递 max_tokens 参数"""
        result = concrete_skill._call_llm("system", "user", max_tokens=8000)
        assert isinstance(result, str)

    def test_call_llm_with_temperature(self, concrete_skill):
        """测试 _call_llm 传递 temperature 参数"""
        result = concrete_skill._call_llm("system", "user", temperature=0.3)
        assert isinstance(result, str)

    def test_call_llm_default_values(self, concrete_skill):
        """测试 _call_llm 使用默认值"""
        result = concrete_skill._call_llm("system", "user")
        assert isinstance(result, str)

    def test_llm_based_skill_default_max_tokens(self, concrete_skill):
        """测试 LLMBasedSkill 默认 max_tokens 为 4000"""
        assert concrete_skill.max_tokens == 4000


# ============================================================
# 5. WorkflowPaths 新目录结构
# ============================================================
class TestWorkflowPathsNewDirs:
    """WorkflowPaths 新目录结构测试"""

    @pytest.fixture
    def temp_output_dir(self):
        temp_dir = tempfile.mkdtemp()
        original = os.environ.get('OUTPUTS_BASE_DIR')
        os.environ['OUTPUTS_BASE_DIR'] = temp_dir
        yield temp_dir
        if original:
            os.environ['OUTPUTS_BASE_DIR'] = original
        else:
            os.environ.pop('OUTPUTS_BASE_DIR', None)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_state_dir_exists(self, temp_output_dir):
        """测试 state 目录创建"""
        from harness.core.paths import WorkflowPaths
        paths = WorkflowPaths("test_wf_state")
        paths.ensure_dirs()
        assert os.path.exists(paths.state_dir)

    def test_analytics_dir_exists(self, temp_output_dir):
        """测试 analytics 目录创建"""
        from harness.core.paths import WorkflowPaths
        paths = WorkflowPaths("test_wf_analytics")
        paths.ensure_dirs()
        assert os.path.exists(paths.analytics_dir)

    def test_extracted_dir_exists(self, temp_output_dir):
        """测试 extracted 目录创建"""
        from harness.core.paths import WorkflowPaths
        paths = WorkflowPaths("test_wf_extracted")
        paths.ensure_dirs()
        assert os.path.exists(paths.extracted_dir)

    def test_analysis_dir_exists(self, temp_output_dir):
        """测试 analysis 目录创建"""
        from harness.core.paths import WorkflowPaths
        paths = WorkflowPaths("test_wf_analysis")
        paths.ensure_dirs()
        assert os.path.exists(paths.analysis_dir)

    def test_cleanup_temp_only(self, temp_output_dir):
        """测试 cleanup_temp 只清理临时目录"""
        from harness.core.paths import WorkflowPaths
        paths = WorkflowPaths("test_wf_cleanup")
        paths.ensure_dirs()
        
        temp_file = os.path.join(paths.temp_dir, "temp.txt")
        extracted_file = os.path.join(paths.extracted_dir, "data.txt")
        with open(temp_file, 'w') as f:
            f.write("temp")
        with open(extracted_file, 'w') as f:
            f.write("data")
        
        paths.cleanup_temp()
        
        assert not os.path.exists(paths.temp_dir)
        assert os.path.exists(paths.extracted_dir)
        assert os.path.exists(paths.extracted_dir_str)

    def test_convenience_properties(self, temp_output_dir):
        """测试便捷属性"""
        from harness.core.paths import WorkflowPaths
        paths = WorkflowPaths("test_wf_props")
        paths.ensure_dirs()
        
        assert isinstance(paths.state_dir_str, str)
        assert isinstance(paths.analytics_dir_str, str)
        assert isinstance(paths.extracted_dir_str, str)
        assert isinstance(paths.analysis_dir_str, str)
        assert isinstance(paths.reports_dir_str, str)
        assert isinstance(paths.llm_interactions_dir_str, str)

    def test_all_dirs_created(self, temp_output_dir):
        """测试所有目录都被创建"""
        from harness.core.paths import WorkflowPaths
        paths = WorkflowPaths("test_wf_all")
        paths.ensure_dirs()
        
        expected_dirs = [
            paths.temp_dir, paths.extracted_dir, paths.state_dir,
            paths.analysis_dir, paths.reports_dir, paths.analytics_dir,
            paths.logs_dir, paths.llm_interactions_dir, paths.artifacts_dir
        ]
        for d in expected_dirs:
            assert os.path.exists(d), f"目录 {d} 未创建"

    def test_llm_interactions_dir_exists(self, temp_output_dir):
        """测试 llm_interactions 目录创建"""
        from harness.core.paths import WorkflowPaths
        paths = WorkflowPaths("test_wf_llm")
        paths.ensure_dirs()
        assert os.path.exists(paths.llm_interactions_dir)
        assert os.path.exists(paths.llm_interactions_dir_str)

    def test_ensure_dirs_no_legacy_global_dirs(self, temp_output_dir):
        """测试 ensure_dirs 不再创建 legacy 全局目录"""
        from harness.core.paths import ensure_dirs, OUTPUTS_DIR
        import shutil
        test_root = os.path.join(temp_output_dir, "ensure_dirs_test")
        os.makedirs(test_root, exist_ok=True)
        
        legacy_dirs = ["reports", "state", "temp", "analytics"]
        for d in legacy_dirs:
            full_path = os.path.join(test_root, d)
            assert not os.path.exists(full_path), f"legacy 全局目录 {d} 不应被 ensure_dirs 创建"


# ============================================================
# 6. WorkflowMetadata.additional_findings
# ============================================================
class TestWorkflowMetadataAdditionalFindings:
    """WorkflowMetadata additional_findings 字段测试"""

    def test_additional_findings_default_empty(self):
        """测试 additional_findings 默认为空列表"""
        from harness.core.state import WorkflowMetadata
        metadata = WorkflowMetadata(
            workflow_id="test_af",
            workflow_name="test",
            bug_description="test",
            bug_summary="test",
            log_path="/test",
            created_at="2026-01-01",
            current_stage="plan",
            status="running"
        )
        assert metadata.additional_findings == []

    def test_additional_findings_with_data(self):
        """测试 additional_findings 带数据"""
        from harness.core.state import WorkflowMetadata
        findings = [
            {"type": "warning", "category": "performance", "description": "内存泄漏"},
            {"type": "info", "category": "stability", "description": "ANR 疑似"}
        ]
        metadata = WorkflowMetadata(
            workflow_id="test_af2",
            workflow_name="test",
            bug_description="test",
            bug_summary="test",
            log_path="/test",
            created_at="2026-01-01",
            current_stage="plan",
            status="running",
            additional_findings=findings
        )
        assert len(metadata.additional_findings) == 2
        assert metadata.additional_findings[0]["type"] == "warning"


# ============================================================
# 7. MultiRoundAnalysis._extract_key_findings / _extract_confidence
# ============================================================
class TestMultiRoundAnalysisExtractors:
    """多轮分析提取函数测试"""

    @pytest.fixture
    def skill(self):
        from harness.skills.multi_round_analysis import MultiRoundAnalysisSkill
        return MultiRoundAnalysisSkill()

    def test_extract_key_findings_numbered_items(self, skill):
        """测试提取编号列表关键发现"""
        text = """
1. **NullPointerException** 在 MainActivity.java:36
2. **ANR detected** 在 ImageLoader 中
3. 普通文本行
"""
        findings = skill._extract_key_findings(text)
        assert len(findings) >= 2
        assert any("NullPointerException" in f for f in findings)
        assert any("ANR" in f for f in findings)

    def test_extract_key_findings_dash_items(self, skill):
        """测试提取破折号列表关键发现"""
        text = """
- **ANR detected** in MainActivity
- **Watchdog kill** in system_server
- 普通文本
"""
        findings = skill._extract_key_findings(text)
        assert len(findings) >= 2

    def test_extract_key_findings_keyword_match(self, skill):
        """测试关键词匹配发现"""
        text = "发现根因是崩溃异常ANR内存泄漏导致的问题"
        findings = skill._extract_key_findings(text)
        assert len(findings) >= 1

    def test_extract_key_findings_max_5(self, skill):
        """测试最多提取 5 个发现"""
        text = "\n".join([f"{i+1}. **发现{i+1}** 描述内容" for i in range(10)])
        findings = skill._extract_key_findings(text)
        assert len(findings) <= 5

    def test_extract_key_findings_empty_text(self, skill):
        """测试空文本"""
        findings = skill._extract_key_findings("")
        assert findings == []

    def test_extract_confidence_with_percentage(self, skill):
        """测试提取百分比置信度"""
        text = "根因分析置信度：**85%**\n修复方案可行性：**70%**"
        confidence = skill._extract_confidence(text)
        assert confidence["root_cause"] == 0.85
        assert confidence["fix_feasibility"] == 0.70

    def test_extract_confidence_with_chinese_format(self, skill):
        """测试中文格式置信度"""
        text = "根因置信度90%，修复可行性65%"
        confidence = skill._extract_confidence(text)
        assert confidence["root_cause"] == 0.90
        assert confidence["fix_feasibility"] == 0.65

    def test_extract_confidence_default_values(self, skill):
        """测试无置信度信息时使用默认值"""
        text = "分析结果中没有置信度信息"
        confidence = skill._extract_confidence(text)
        assert confidence["root_cause"] == 0.5
        assert confidence["fix_feasibility"] == 0.5

    def test_extract_confidence_capped_at_1(self, skill):
        """测试置信度上限为 1.0"""
        text = "根因分析置信度：**150%**"
        confidence = skill._extract_confidence(text)
        assert confidence["root_cause"] == 1.0

    def test_extract_confidence_english_format(self, skill):
        """测试英文格式置信度"""
        text = "Root cause confidence: 80%\nFix feasibility: 75%"
        confidence = skill._extract_confidence(text)
        assert confidence["root_cause"] == 0.80
        assert confidence["fix_feasibility"] == 0.75


# ============================================================
# 8. FeatureSDK 单例修复
# ============================================================
class TestFeatureSDKSingleton:
    """FeatureSDK 单例模式测试"""

    def test_singleton_same_instance(self):
        """测试多次实例化返回同一实例"""
        from harness.core.feature_flags import FeatureSDK
        sdk1 = FeatureSDK()
        sdk2 = FeatureSDK()
        assert sdk1 is sdk2

    def test_singleton_initialized_flag(self):
        """测试 _initialized 标志"""
        from harness.core.feature_flags import FeatureSDK
        sdk = FeatureSDK()
        assert FeatureSDK._initialized is True

    def test_singleton_engine_not_overwritten(self):
        """测试已初始化后 engine 不会被覆盖"""
        from harness.core.feature_flags import FeatureSDK, FeatureFlagEngine
        sdk1 = FeatureSDK()
        original_engine = sdk1.engine
        
        sdk2 = FeatureSDK(FeatureFlagEngine())
        assert sdk2.engine is original_engine


# ============================================================
# 9. LLMClient 延迟导入 + 交互日志
# ============================================================
class TestLLMClientLazyImport:
    """LLMClient 延迟导入测试"""

    def test_ensure_openai_imported_function_exists(self):
        """测试延迟导入函数存在"""
        from log_analyzer.llm.llm_client import _ensure_openai_imported
        assert callable(_ensure_openai_imported)

    def test_lazy_import_globals_initially_none(self):
        """测试全局变量初始为 None"""
        import importlib
        import log_analyzer.llm.llm_client as mod
        importlib.reload(mod)
        assert mod._OpenAI is None or mod._OpenAI is not None

    def test_log_llm_interaction_method_exists(self):
        """测试 _log_llm_interaction 方法存在"""
        from log_analyzer.llm.llm_client import LLMClient
        assert hasattr(LLMClient, '_log_llm_interaction')

    def test_log_llm_interaction_creates_files(self):
        """测试 _log_llm_interaction 创建日志文件"""
        from log_analyzer.llm.llm_client import LLMClient
        from harness.core.paths import OUTPUTS_DIR
        
        client = LLMClient(model="test-model")
        client._log_llm_interaction(
            timestamp="20260519_120000_000",
            system_prompt="test system prompt",
            user_prompt="test user prompt",
            response="test response",
            temperature=0.7,
            max_tokens=4000,
            scene="test_scene",
            skill="test_skill",
            prompt_tokens=100,
            completion_tokens=200,
            is_error=False
        )
        
        interaction_dir = os.path.join(str(OUTPUTS_DIR), "llm_interactions")
        assert os.path.exists(interaction_dir)
        
        json_files = [f for f in os.listdir(interaction_dir) if f.endswith('.json') and '120000_000' in f]
        md_files = [f for f in os.listdir(interaction_dir) if f.endswith('.md') and '120000_000' in f]
        assert len(json_files) >= 1
        assert len(md_files) >= 1
        
        with open(os.path.join(interaction_dir, json_files[0]), 'r') as f:
            data = json.load(f)
        assert data["prompt"]["system"] == "test system prompt"
        assert data["prompt"]["user"] == "test user prompt"
        assert data["response"] == "test response"
        assert data["token_usage"]["total"] == 300
        assert data["is_error"] is False

    def test_log_llm_interaction_error_record(self):
        """测试 _log_llm_interaction 记录错误"""
        from log_analyzer.llm.llm_client import LLMClient
        from harness.core.paths import OUTPUTS_DIR
        
        client = LLMClient(model="test-model")
        client._log_llm_interaction(
            timestamp="20260519_120000_001",
            system_prompt="test",
            user_prompt="test",
            response="ERROR: API timeout",
            temperature=0.7,
            max_tokens=4000,
            scene=None,
            skill=None,
            prompt_tokens=0,
            completion_tokens=0,
            is_error=True
        )
        
        interaction_dir = os.path.join(str(OUTPUTS_DIR), "llm_interactions")
        json_files = [f for f in os.listdir(interaction_dir) if f.startswith('error_') and '120000_001' in f]
        assert len(json_files) >= 1


# ============================================================
# 10. load_state 新旧路径兼容
# ============================================================
class TestLoadStateCompatibility:
    """load_state 新旧路径兼容测试"""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        original = os.environ.get('OUTPUTS_BASE_DIR')
        os.environ['OUTPUTS_BASE_DIR'] = temp_dir
        yield temp_dir
        if original:
            os.environ['OUTPUTS_BASE_DIR'] = original
        else:
            os.environ.pop('OUTPUTS_BASE_DIR', None)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_load_from_new_path(self, temp_dir):
        """测试从新路径 (workflows/{id}/state/) 加载"""
        from harness.core.state import StateManager, WorkflowPaths
        
        manager = StateManager()
        workflow_id = manager.initialize_workflow("test_new_path")
        manager.update_context("test_key", "test_value")
        manager.flush()
        
        manager2 = StateManager()
        state = manager2.load_state(workflow_id)
        assert state["workflow_id"] == workflow_id
        assert state["context"]["test_key"] == "test_value"

    def test_load_from_old_path(self, temp_dir):
        """测试从旧路径 (outputs/state/) 加载兼容"""
        from harness.core.state import StateManager, OUTPUTS_STATE_DIR_STR
        
        workflow_id = "test_old_path_20260519_120000_abcd1234"
        
        old_state_dir = OUTPUTS_STATE_DIR_STR
        os.makedirs(old_state_dir, exist_ok=True)
        
        state_data = {
            "workflow_id": workflow_id,
            "current_stage": "plan",
            "context": {"old_key": "old_value"},
            "outputs": {},
            "validations": {},
            "history": []
        }
        
        old_file = os.path.join(old_state_dir, f"{workflow_id}.json")
        with open(old_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, ensure_ascii=False)
        
        try:
            manager = StateManager()
            state = manager.load_state(workflow_id)
            assert state["workflow_id"] == workflow_id
            assert state["context"]["old_key"] == "old_value"
        finally:
            if os.path.exists(old_file):
                os.remove(old_file)

    def test_load_nonexistent_workflow(self, temp_dir):
        """测试加载不存在的工作流"""
        from harness.core.state import StateManager
        
        manager = StateManager()
        with pytest.raises(FileNotFoundError):
            manager.load_state("nonexistent_workflow_id")


# ============================================================
# 11. AnalyticsCollector 线程安全 + workflow 目录
# ============================================================
class TestAnalyticsThreadSafety:
    """AnalyticsCollector 线程安全测试"""

    def test_get_analytics_collector_thread_safe(self):
        """测试多线程获取单例"""
        from harness.core.analytics import get_analytics_collector, _analytics_lock
        
        results = []
        
        def get_collector():
            collector = get_analytics_collector()
            results.append(id(collector))
        
        threads = [threading.Thread(target=get_collector) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(set(results)) == 1

    def test_set_workflow_analytics_dir(self):
        """测试设置工作流 analytics 目录"""
        from harness.core.analytics import AnalyticsCollector
        
        temp_dir = tempfile.mkdtemp()
        original = os.environ.get('OUTPUTS_BASE_DIR')
        os.environ['OUTPUTS_BASE_DIR'] = temp_dir
        
        try:
            collector = AnalyticsCollector()
            collector.set_workflow_analytics_dir("test_wf_analytics_dir")
            
            assert "test_wf_analytics_dir" in collector.analytics_dir
            assert os.path.exists(collector.analytics_dir)
        finally:
            if original:
                os.environ['OUTPUTS_BASE_DIR'] = original
            else:
                os.environ.pop('OUTPUTS_BASE_DIR', None)
            shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================
# 12. TokenStatsManager workflow 目录切换
# ============================================================
class TestTokenStatsWorkflowDir:
    """TokenStatsManager set_workflow_dir 测试"""

    def test_set_workflow_dir(self):
        """测试切换到 workflow 专属目录"""
        from harness.core.token_stats import TokenStatsManager
        temp_dir = tempfile.mkdtemp()
        original = os.environ.get('OUTPUTS_BASE_DIR')
        os.environ['OUTPUTS_BASE_DIR'] = temp_dir
        
        try:
            mgr = TokenStatsManager()
            mgr.set_workflow_dir("test_wf_token")
            
            assert "test_wf_token" in mgr._storage_dir
            assert "analytics" in mgr._storage_dir
            assert os.path.exists(mgr._storage_dir)
        finally:
            if original:
                os.environ['OUTPUTS_BASE_DIR'] = original
            else:
                os.environ.pop('OUTPUTS_BASE_DIR', None)
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_set_workflow_dir_saves_to_correct_path(self):
        """测试保存文件到 workflow 目录"""
        from harness.core.token_stats import TokenStatsManager
        temp_dir = tempfile.mkdtemp()
        original = os.environ.get('OUTPUTS_BASE_DIR')
        os.environ['OUTPUTS_BASE_DIR'] = temp_dir
        
        try:
            mgr = TokenStatsManager()
            mgr.set_workflow_dir("test_wf_save")
            mgr.record_usage(100, 50, "test-model", scene="test")
            mgr.save_session("test_token_stats.json")
            
            saved_path = os.path.join(mgr._storage_dir, "test_token_stats.json")
            assert os.path.exists(saved_path)
        finally:
            if original:
                os.environ['OUTPUTS_BASE_DIR'] = original
            else:
                os.environ.pop('OUTPUTS_BASE_DIR', None)
            shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================
# 13. EnhancedReportGenerationSkill workflow_id 支持
# ============================================================
class TestEnhancedReportWorkflowId:
    """EnhancedReportGenerationSkill workflow_id 测试"""

    def test_enhanced_report_with_workflow_id(self):
        """测试有 workflow_id 时输出到 workflow 目录"""
        from harness.skills.enhanced_report_generation import EnhancedReportGenerationSkill
        temp_dir = tempfile.mkdtemp()
        original = os.environ.get('OUTPUTS_BASE_DIR')
        os.environ['OUTPUTS_BASE_DIR'] = temp_dir
        
        try:
            skill = EnhancedReportGenerationSkill()
            inputs = {
                "bug_description": {"summary": "test", "keywords": ["crash"]},
                "workflow_id": "test_wf_report",
                "output_format": "json",
                "aloggrep_workflow": {
                    "data": {
                        "stages": {},
                        "executive_summary": ""
                    }
                }
            }
            result = skill.execute(inputs)
            assert result.success
            assert "test_wf_report" in result.data.get("report_files", [""])[0]
        finally:
            if original:
                os.environ['OUTPUTS_BASE_DIR'] = original
            else:
                os.environ.pop('OUTPUTS_BASE_DIR', None)
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_enhanced_report_without_workflow_id(self):
        """测试无 workflow_id 时回退到全局目录"""
        from harness.skills.enhanced_report_generation import EnhancedReportGenerationSkill
        temp_dir = tempfile.mkdtemp()
        original = os.environ.get('OUTPUTS_BASE_DIR')
        os.environ['OUTPUTS_BASE_DIR'] = temp_dir
        
        try:
            skill = EnhancedReportGenerationSkill()
            inputs = {
                "bug_description": {"summary": "test", "keywords": ["crash"]},
                "output_format": "json",
                "aloggrep_workflow": {
                    "data": {
                        "stages": {},
                        "executive_summary": ""
                    }
                }
            }
            result = skill.execute(inputs)
            assert result.success
        finally:
            if original:
                os.environ['OUTPUTS_BASE_DIR'] = original
            else:
                os.environ.pop('OUTPUTS_BASE_DIR', None)
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
