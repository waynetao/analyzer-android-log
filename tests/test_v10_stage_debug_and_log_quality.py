"""
测试 v10 阶段调试和日志质量优化
- LogParser 上下文感知解析（None 字段继承）
- LogAnalyzer 单词边界匹配（误分类修复）
- LogAnalyzer 互斥分类
- 关键日志上下文块提取
- LLM 提示词格式化（None 不显示）
- 文件清单优化
- StageDebugger 单阶段调试机制
"""
import os
import json
import tempfile
import pytest
from log_analyzer.parser.log_parser import LogEntry, LogParser
from log_analyzer.analyzer.log_analyzer import LogAnalyzer, AnalysisResult
from log_analyzer.bugreport.bugreport_parser import BugReportParser
from log_analyzer.extractor.log_file_selector import LogFileSelector
from harness.skills.log_format_utils import format_critical_logs, format_log_entry_safe
from harness.core.stage_debugger import StageDebugger
from harness.skills.base import SkillResult


class TestContextAwareParsing:
    """测试 LogParser 上下文感知解析 - 解决 None 字段问题"""

    def test_context_inheritance_for_unmatched_lines(self):
        """不匹配格式的行应继承上一行的 timestamp/level/tag"""
        parser = LogParser("/nonexistent")
        
        last_entry = LogEntry(
            timestamp="05-09 19:14:34.627",
            level="E",
            tag="AndroidRuntime",
            message="FATAL EXCEPTION: handlerThread",
            pid=14279,
            tid=3643,
            file_path="/test.log"
        )
        
        entry = parser._parse_line(
            "Process: com.tcl.logger, PID: 14279",
            "/test.log",
            last_entry
        )
        
        assert entry is not None
        assert entry.message == "Process: com.tcl.logger, PID: 14279"
        assert entry.timestamp == "05-09 19:14:34.627"
        assert entry.level == "E"
        assert entry.tag == "AndroidRuntime"

    def test_context_inheritance_for_crash_continuation(self):
        """Crash 堆栈的续行应继承上下文"""
        parser = LogParser("/nonexistent")
        
        last_entry = LogEntry(
            timestamp="05-09 19:14:34.627",
            level="E",
            tag="AndroidRuntime",
            message="FATAL EXCEPTION: handlerThread",
            pid=14279,
            tid=3643,
            file_path="/test.log"
        )
        
        entry = parser._parse_line(
            "    at com.example.MyClass.myMethod(MyClass.java:42)",
            "/test.log",
            last_entry
        )
        
        assert entry.timestamp == "05-09 19:14:34.627"
        assert entry.level == "E"
        assert entry.tag == "AndroidRuntime"

    def test_no_context_inheritance_when_no_last_entry(self):
        """没有上一行时，不匹配的行不应有虚假字段"""
        parser = LogParser("/nonexistent")
        
        entry = parser._parse_line(
            "--------- beginning of crash",
            "/test.log",
            None
        )
        
        assert entry is not None
        assert entry.message == "--------- beginning of crash"
        assert entry.timestamp is None
        assert entry.level is None
        assert entry.tag is None

    def test_full_format_no_context_override(self):
        """完整格式的行不应被上下文覆盖"""
        parser = LogParser("/nonexistent")
        
        last_entry = LogEntry(
            timestamp="05-09 19:14:34.627",
            level="E",
            tag="AndroidRuntime",
            message="old message",
            pid=14279,
            tid=3643,
            file_path="/test.log"
        )
        
        entry = parser._parse_line(
            "05-09 19:14:35.100  1000 2000 I ActivityManager: Start proc",
            "/test.log",
            last_entry
        )
        
        assert entry.timestamp == "05-09 19:14:35.100"
        assert entry.level == "I"
        assert entry.tag == "ActivityManager"
        assert entry.pid == 1000

    def test_parse_file_with_context(self):
        """完整文件解析应正确传递上下文"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("05-09 19:14:34.627  1000 14279  3643 E AndroidRuntime: FATAL EXCEPTION: handlerThread\n")
            f.write("Process: com.tcl.logger, PID: 14279\n")
            f.write("05-09 19:14:35.100  1000 14279  3643 E AndroidRuntime: Caused by: java.lang.NullPointerException\n")
            f.write("    at com.example.MyClass.myMethod(MyClass.java:42)\n")
            f.name
        
        try:
            parser = LogParser(os.path.dirname(f.name))
            entries = parser.parse_file(f.name)
            
            assert len(entries) >= 4
            
            assert entries[0].timestamp == "05-09 19:14:34.627"
            assert entries[0].level == "E"
            assert entries[0].tag == "AndroidRuntime"
            
            assert entries[1].message == "Process: com.tcl.logger, PID: 14279"
            assert entries[1].timestamp == "05-09 19:14:34.627"
            assert entries[1].level == "E"
            assert entries[1].tag == "AndroidRuntime"
            
            assert entries[3].timestamp == "05-09 19:14:35.100"
            assert entries[3].tag == "AndroidRuntime"
        finally:
            os.unlink(f.name)


class TestBugReportParserContext:
    """测试 BugReportParser 上下文感知解析"""

    def test_bugreport_context_inheritance(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("05-09 19:14:34.627  1000 14279  3643 E AndroidRuntime: FATAL EXCEPTION: handlerThread\n")
            f.write("Process: com.tcl.logger, PID: 14279\n")
            f.name
        
        try:
            parser = BugReportParser(os.path.dirname(f.name), use_smart_filter=False)
            entries = parser.parse_file(f.name)
            
            assert len(entries) >= 2
            assert entries[1].message == "Process: com.tcl.logger, PID: 14279"
            assert entries[1].timestamp == "05-09 19:14:34.627"
            assert entries[1].level == "E"
        finally:
            os.unlink(f.name)


class TestLogAnalyzerWordBoundary:
    """测试 LogAnalyzer 单词边界匹配 - 解决误分类问题"""

    def test_anr_word_boundary_no_false_positive(self):
        """'mWifiDisplayScanRequestCount=0' 不应被分类为 ANR"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="D",
            tag="WifiDisplayAdapter",
            message="mWifiDisplayScanRequestCount=0"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.anrs) == 0

    def test_anr_word_boundary_correct_match(self):
        """包含独立 'anr' 单词的日志应被正确分类"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="E",
            tag="ActivityManager",
            message="ANR in com.example.app"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.anrs) == 1

    def test_anr_am_anr_keyword(self):
        """'am_anr' 关键词应正确匹配"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="I",
            tag="am_anr",
            message="com.example.app"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.anrs) == 1

    def test_anr_not_responding(self):
        """'not responding' 应正确匹配 ANR"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="E",
            tag="ActivityManager",
            message="Input dispatching timed out (com.example.app is not responding)"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.anrs) == 1

    def test_exception_no_broad_error_match(self):
        """'error' 子串不应被宽泛匹配为 exception"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="I",
            tag="SomeTag",
            message="mErrorState=0"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.exceptions) == 0

    def test_exception_specific_exception_match(self):
        """具体的 Exception 类名应正确匹配"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="E",
            tag="AndroidRuntime",
            message="java.lang.NullPointerException: attempt to get field"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.exceptions) == 1

    def test_low_memory_no_broad_kill_match(self):
        """'skill' 不应被误匹配为 low_memory (kill 子串)"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="I",
            tag="SomeTag",
            message="skill level updated"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.low_memory) == 0

    def test_low_memory_killed_match(self):
        """'killed' 应正确匹配 low_memory"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="W",
            tag="ActivityManager",
            message="Process com.example.app (pid 12345) has killed"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.low_memory) == 1

    def test_mutually_exclusive_classification(self):
        """分类应是互斥的：一条日志只应属于一个类别"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="E",
            tag="AndroidRuntime",
            message="FATAL EXCEPTION: NullPointerException"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        total = (len(result.crashes) + len(result.anrs) + len(result.low_memory) +
                 len(result.exceptions) + len(result.boot_events) + len(result.power_events) +
                 len(result.other_issues))
        
        assert total == 1
        assert len(result.crashes) == 1

    def test_other_issues_only_error_fatal(self):
        """other_issues 只包含 E 和 F 级别，不包含 W"""
        entry_w = LogEntry(
            timestamp="05-09 19:14:34",
            level="W",
            tag="SomeTag",
            message="some warning"
        )
        
        analyzer = LogAnalyzer([entry_w])
        result = analyzer.analyze()
        
        assert len(result.other_issues) == 0

    def test_boot_event_narrow_keywords(self):
        """'boot' 子串不应误匹配，只有 'bootstat'/'boot_completed' 才匹配"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="I",
            tag="SomeTag",
            message="bootloader version 1.0"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.boot_events) == 0

    def test_power_event_narrow_keywords(self):
        """'power' 子串不应误匹配，只有 'shutdown'/'reboot' 等才匹配"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="I",
            tag="SomeTag",
            message="power adapter connected"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.power_events) == 0


class TestLogFormatUtils:
    """测试日志格式化工具 - None 不显示"""

    def test_format_critical_logs_none_fields_hidden(self):
        """None 字段不应出现在格式化输出中"""
        logs = [
            {
                "type": "crash",
                "message": "--------- beginning of crash",
                "timestamp": None,
                "level": None,
                "tag": None,
            }
        ]
        
        result = format_critical_logs(logs)
        
        assert "None" not in result
        assert "CRASH" in result
        assert "beginning of crash" in result

    def test_format_critical_logs_with_all_fields(self):
        """所有字段都有值时应正确显示"""
        logs = [
            {
                "type": "crash",
                "message": "FATAL EXCEPTION: handlerThread",
                "timestamp": "05-09 19:14:34",
                "level": "E",
                "tag": "AndroidRuntime",
                "pid": 14279,
            }
        ]
        
        result = format_critical_logs(logs)
        
        assert "05-09 19:14:34" in result
        assert "E" in result
        assert "AndroidRuntime" in result
        assert "14279" in result
        assert "FATAL EXCEPTION" in result

    def test_format_critical_logs_context_block(self):
        """上下文块（多行 message）应正确显示"""
        logs = [
            {
                "type": "crash",
                "message": "FATAL EXCEPTION: handlerThread\nProcess: com.tcl.logger, PID: 14279\nCaused by: NullPointerException",
                "timestamp": "05-09 19:14:34",
                "level": "E",
                "tag": "AndroidRuntime",
            }
        ]
        
        result = format_critical_logs(logs)
        
        assert "FATAL EXCEPTION" in result
        assert "Process: com.tcl.logger" in result
        assert "NullPointerException" in result

    def test_format_critical_logs_empty(self):
        """空日志列表应返回提示信息"""
        result = format_critical_logs([])
        assert "无关键日志" in result

    def test_format_log_entry_safe(self):
        """format_log_entry_safe 应隐藏 None 字段"""
        log = {
            "timestamp": None,
            "level": None,
            "tag": None,
            "message": "some message"
        }
        
        result = format_log_entry_safe(log)
        
        assert "None" not in result
        assert "some message" in result

    def test_format_log_entry_safe_with_fields(self):
        """format_log_entry_safe 有值字段应正确显示"""
        log = {
            "timestamp": "05-09 19:14:34",
            "level": "E",
            "tag": "AndroidRuntime",
            "message": "FATAL EXCEPTION"
        }
        
        result = format_log_entry_safe(log)
        
        assert "[05-09 19:14:34]" in result
        assert "[E]" in result
        assert "[AndroidRuntime]" in result
        assert "FATAL EXCEPTION" in result


class TestFileManifestOptimization:
    """测试文件清单优化"""

    def test_manifest_with_matched_files_only(self):
        """generate_file_manifest 应支持只包含规则匹配的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "crash.log")
            with open(log_file, 'w') as f:
                f.write("test content that is long enough to pass the 50 byte filter threshold for log files")
            
            other_file = os.path.join(tmpdir, "screenshot.png")
            with open(other_file, 'w') as f:
                f.write("fake png content that is also long enough")
            
            selector = LogFileSelector()
            matched, filtered = selector.scan_directory(tmpdir)
            
            full_manifest = selector.generate_file_manifest(tmpdir)
            filtered_manifest = selector.generate_file_manifest(tmpdir, matched_files=matched)
            
            assert len(matched) >= 1
            assert len(filtered_manifest) <= len(full_manifest)
            assert "crash.log" in filtered_manifest

    def test_manifest_smaller_with_matched_files(self):
        """使用 matched_files 参数应产生更小的清单"""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(10):
                with open(os.path.join(tmpdir, f"test_{i}.log"), 'w') as f:
                    f.write(f"content {i}")
                with open(os.path.join(tmpdir, f"screenshot_{i}.png"), 'w') as f:
                    f.write(f"fake png {i}")
            
            selector = LogFileSelector()
            matched, filtered = selector.scan_directory(tmpdir)
            
            full_manifest = selector.generate_file_manifest(tmpdir)
            filtered_manifest = selector.generate_file_manifest(tmpdir, matched_files=matched)
            
            assert len(filtered_manifest) < len(full_manifest)


class TestStageDebugger:
    """测试单阶段调试机制"""

    def test_debugger_init(self):
        """StageDebugger 应正确初始化"""
        debugger = StageDebugger(workflow_id="test_debug_001")
        assert debugger.debug_dir is not None
        assert "test_debug_001" in str(debugger.debug_dir)

    def test_debugger_execute_stage(self):
        """execute_stage 应正确执行技能并保存调试数据"""
        debugger = StageDebugger(workflow_id="test_debug_002")
        
        class MockSkill:
            name = "mock_skill"
            def execute(self, inputs):
                return SkillResult(True, {"key": "value"}, "mock success")
        
        skill = MockSkill()
        result = debugger.execute_stage(skill, {"input_key": "input_val"}, stage_name="mock_skill")
        
        assert result["success"] is True
        assert result["data"]["key"] == "value"
        assert result["debug_info"]["stage_name"] == "mock_skill"
        assert result["debug_info"]["success"] is True
        
        stage_dir = os.path.join(debugger.debug_dir, "mock_skill")
        assert os.path.exists(os.path.join(stage_dir, "input.json"))
        assert os.path.exists(os.path.join(stage_dir, "output.json"))
        assert os.path.exists(os.path.join(stage_dir, "summary.md"))

    def test_debugger_execute_stage_with_error(self):
        """execute_stage 应正确处理异常"""
        debugger = StageDebugger(workflow_id="test_debug_003")
        
        class FailingSkill:
            name = "failing_skill"
            def execute(self, inputs):
                raise ValueError("test error")
        
        skill = FailingSkill()
        result = debugger.execute_stage(skill, {}, stage_name="failing_skill")
        
        assert result["success"] is False
        assert "test error" in result["message"]
        assert result["debug_info"]["success"] is False

    def test_debugger_load_stage_output(self):
        """load_stage_output 应能加载之前保存的输出"""
        debugger = StageDebugger(workflow_id="test_debug_004")
        
        class MockSkill:
            name = "mock_skill"
            def execute(self, inputs):
                return SkillResult(True, {"result": "hello"}, "ok")
        
        skill = MockSkill()
        debugger.execute_stage(skill, {"test": "data"}, stage_name="mock_skill")
        
        loaded = debugger.load_stage_output("mock_skill")
        assert loaded is not None
        assert loaded["data"]["result"] == "hello"

    def test_debugger_load_stage_input(self):
        """load_stage_input 应能加载之前保存的输入"""
        debugger = StageDebugger(workflow_id="test_debug_005")
        
        class MockSkill:
            name = "mock_skill"
            def execute(self, inputs):
                return SkillResult(True, {}, "ok")
        
        skill = MockSkill()
        debugger.execute_stage(skill, {"test_key": "test_val"}, stage_name="mock_skill")
        
        loaded = debugger.load_stage_input("mock_skill")
        assert loaded is not None
        assert loaded["test_key"] == "test_val"

    def test_debugger_list_stages(self):
        """list_stages 应列出所有已调试的阶段"""
        debugger = StageDebugger(workflow_id="test_debug_006")
        
        class MockSkill:
            name = "skill_a"
            def execute(self, inputs):
                return SkillResult(True, {}, "ok a")
        
        class MockSkillB:
            name = "skill_b"
            def execute(self, inputs):
                return SkillResult(False, {}, "failed b")
        
        debugger.execute_stage(MockSkill(), {}, stage_name="skill_a")
        debugger.execute_stage(MockSkillB(), {}, stage_name="skill_b")
        
        stages = debugger.list_stages()
        assert len(stages) == 2
        names = [s["name"] for s in stages]
        assert "skill_a" in names
        assert "skill_b" in names

    def test_debugger_get_stage_summary(self):
        """get_stage_summary 应返回 Markdown 格式的摘要"""
        debugger = StageDebugger(workflow_id="test_debug_007")
        
        class MockSkill:
            name = "mock_skill"
            def execute(self, inputs):
                return SkillResult(True, {"count": 5}, "ok")
        
        debugger.execute_stage(MockSkill(), {"input": "data"}, stage_name="mock_skill")
        
        summary = debugger.get_stage_summary("mock_skill")
        assert summary is not None
        assert "mock_skill" in summary
        assert "成功" in summary

    def test_debugger_generate_pipeline_summary(self):
        """generate_pipeline_summary 应生成整体流水线摘要"""
        debugger = StageDebugger(workflow_id="test_debug_008")
        
        class MockSkill:
            name = "mock_skill"
            def execute(self, inputs):
                return SkillResult(True, {}, "ok")
        
        debugger.execute_stage(MockSkill(), {}, stage_name="mock_skill")
        
        summary = debugger.generate_pipeline_summary()
        assert "调试流水线摘要" in summary
        assert "mock_skill" in summary
        
        assert os.path.exists(os.path.join(debugger.debug_dir, "pipeline_summary.md"))

    def test_debugger_stage_data_interop(self):
        """阶段间数据传递：前一阶段输出可作为后一阶段输入"""
        debugger = StageDebugger(workflow_id="test_debug_009")
        
        class Stage1:
            name = "stage1"
            def execute(self, inputs):
                return SkillResult(True, {"extraction_dir": "/tmp/extracted"}, "stage1 done")
        
        class Stage2:
            name = "stage2"
            def execute(self, inputs):
                return SkillResult(True, {"analysis": "done"}, "stage2 done")
        
        debugger.execute_stage(Stage1(), {"log_path": "/test.log"}, stage_name="stage1")
        
        stage1_output = debugger.load_stage_output("stage1")
        assert stage1_output["data"]["extraction_dir"] == "/tmp/extracted"
        
        stage2_inputs = {"log_extraction": stage1_output}
        debugger.execute_stage(Stage2(), stage2_inputs, stage_name="stage2")
        
        stage2_output = debugger.load_stage_output("stage2")
        assert stage2_output["data"]["analysis"] == "done"


class TestEndToEndLogQuality:
    """端到端测试：验证日志质量问题已修复"""

    def test_crash_stack_no_none_fields(self):
        """Crash 堆栈在提示词中不应有 None 字段"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("--------- beginning of crash\n")
            f.write("05-09 19:14:34.627  1000 14279  3643 E AndroidRuntime: FATAL EXCEPTION: handlerThread\n")
            f.write("05-09 19:14:34.627  1000 14279  3643 E AndroidRuntime: Process: com.tcl.logger, PID: 14279\n")
            f.write("05-09 19:14:34.627  1000 14279  3643 E AndroidRuntime: java.lang.NullPointerException\n")
            f.name
        
        try:
            parser = BugReportParser(os.path.dirname(f.name), use_smart_filter=False)
            entries = parser.parse_file(f.name)
            
            assert len(entries) >= 3
            
            for entry in entries[1:]:
                assert entry.timestamp is not None, f"Entry '{entry.message}' should have timestamp"
                assert entry.level is not None, f"Entry '{entry.message}' should have level"
                assert entry.tag is not None, f"Entry '{entry.message}' should have tag"
        finally:
            os.unlink(f.name)

    def test_no_anr_false_positive_in_wifi_scan(self):
        """mWifiDisplayScanRequestCount=0 不应被分类为 ANR"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="D",
            tag="WifiDisplayAdapter",
            message="mWifiDisplayScanRequestCount=0"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.anrs) == 0, "mWifiDisplayScanRequestCount should NOT be classified as ANR"

    def test_no_anr_false_positive_in_scan_requested(self):
        """mScanRequested=false 不应被分类为 ANR"""
        entry = LogEntry(
            timestamp="05-09 19:14:34",
            level="D",
            tag="WifiDisplayAdapter",
            message="mScanRequested=false"
        )
        
        analyzer = LogAnalyzer([entry])
        result = analyzer.analyze()
        
        assert len(result.anrs) == 0, "mScanRequested should NOT be classified as ANR"

    def test_critical_logs_format_no_none(self):
        """格式化后的关键日志不应包含 None"""
        logs = [
            {
                "type": "crash",
                "message": "--------- beginning of crash\nFATAL EXCEPTION: handlerThread",
                "timestamp": "05-09 19:14:34",
                "level": "E",
                "tag": "AndroidRuntime",
            },
            {
                "type": "anr",
                "message": "ANR in com.example.app",
                "timestamp": "05-09 19:15:00",
                "level": "E",
                "tag": "ActivityManager",
            },
        ]
        
        result = format_critical_logs(logs)
        
        assert "None" not in result
        assert "CRASH" in result
        assert "ANR" in result
        assert "05-09 19:14:34" in result
        assert "05-09 19:15:00" in result
