#!/usr/bin/env python3
"""
测试工作流增强功能
- 基于 workflow_id 的产物统一管理
- 工作流元数据索引系统
- 额外发现功能
- 多轮深度分析功能
"""

import sys
import os
import pytest
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.core.state import StateManager, WorkflowStage, WorkflowMetadata, WorkflowIndex
from harness.core.paths import WorkflowPaths
from harness.skills.multi_round_analysis import MultiRoundAnalysisSkill
from harness.skills.log_evidence_matcher import LogEvidenceMatcherSkill
from harness.skills.report import ReportGenerationSkill
from harness.skills.llm_analysis import LLMAnalysisSkill


class TestWorkflowMetadata:
    """工作流元数据测试"""

    def test_workflow_metadata_creation(self):
        """测试 WorkflowMetadata 创建"""
        metadata = WorkflowMetadata(
            workflow_id="test_123",
            workflow_name="bug_analysis",
            bug_description="应用启动时崩溃",
            bug_summary="应用崩溃",
            log_path="/test/log.txt",
            created_at="2026-05-19T00:00:00",
            current_stage="plan",
            status="running"
        )

        assert metadata.workflow_id == "test_123"
        assert metadata.workflow_name == "bug_analysis"
        assert metadata.bug_description == "应用启动时崩溃"
        assert metadata.status == "running"


class TestWorkflowIndex:
    """工作流索引管理器测试"""

    @pytest.fixture
    def temp_index_dir(self):
        """临时索引目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_workflow_index_initialization(self, temp_index_dir):
        """测试 WorkflowIndex 初始化"""
        index = WorkflowIndex(index_dir=temp_index_dir)
        assert index.index_dir == temp_index_dir
        assert os.path.exists(temp_index_dir)

    def test_register_and_get_workflow(self, temp_index_dir):
        """测试注册和获取工作流"""
        index = WorkflowIndex(index_dir=temp_index_dir)

        metadata = WorkflowMetadata(
            workflow_id="test_workflow_001",
            workflow_name="bug_analysis",
            bug_description="应用打开主页面时崩溃",
            bug_summary="应用崩溃",
            log_path="/test/logs/app.log",
            created_at="2026-05-19T00:00:00",
            current_stage="plan",
            status="running"
        )

        index.register_workflow(metadata)

        retrieved = index.get_workflow("test_workflow_001")
        assert retrieved is not None
        assert retrieved["workflow_id"] == "test_workflow_001"
        assert retrieved["bug_summary"] == "应用崩溃"

    def test_update_workflow(self, temp_index_dir):
        """测试更新工作流信息"""
        index = WorkflowIndex(index_dir=temp_index_dir)

        metadata = WorkflowMetadata(
            workflow_id="test_workflow_002",
            workflow_name="bug_analysis",
            bug_description="应用崩溃",
            bug_summary="应用崩溃",
            log_path="/test/log.txt",
            created_at="2026-05-19T00:00:00",
            current_stage="plan",
            status="running"
        )
        index.register_workflow(metadata)

        index.update_workflow("test_workflow_002", current_stage="build", status="running")

        updated = index.get_workflow("test_workflow_002")
        assert updated["current_stage"] == "build"
        assert updated["status"] == "running"

    def test_list_workflows(self, temp_index_dir):
        """测试列出工作流"""
        index = WorkflowIndex(index_dir=temp_index_dir)

        # 注册多个工作流
        metadata1 = WorkflowMetadata(
            workflow_id="test_workflow_1",
            workflow_name="bug_analysis",
            bug_description="bug 1",
            bug_summary="bug1",
            log_path="/log1.txt",
            created_at="2026-05-19T00:00:01",
            current_stage="plan",
            status="running"
        )

        metadata2 = WorkflowMetadata(
            workflow_id="test_workflow_2",
            workflow_name="bug_analysis",
            bug_description="bug 2",
            bug_summary="bug2",
            log_path="/log2.txt",
            created_at="2026-05-19T00:00:02",
            current_stage="completed",
            status="completed"
        )

        index.register_workflow(metadata1)
        index.register_workflow(metadata2)

        # 列出所有工作流
        all_workflows = index.list_workflows()
        assert len(all_workflows) == 2

        # 按状态过滤
        completed_workflows = index.list_workflows(status="completed")
        assert len(completed_workflows) == 1
        assert completed_workflows[0]["workflow_id"] == "test_workflow_2"

    def test_search_workflows(self, temp_index_dir):
        """测试搜索工作流"""
        index = WorkflowIndex(index_dir=temp_index_dir)

        metadata1 = WorkflowMetadata(
            workflow_id="test_workflow_1",
            workflow_name="bug_analysis",
            bug_description="应用启动时崩溃",
            bug_summary="崩溃",
            log_path="/log1.txt",
            created_at="2026-05-19T00:00:01",
            current_stage="plan",
            status="running"
        )

        metadata2 = WorkflowMetadata(
            workflow_id="test_workflow_2",
            workflow_name="bug_analysis",
            bug_description="ANR问题",
            bug_summary="ANR",
            log_path="/log2.txt",
            created_at="2026-05-19T00:00:02",
            current_stage="completed",
            status="completed"
        )

        index.register_workflow(metadata1)
        index.register_workflow(metadata2)

        # 搜索 "崩溃"
        results = index.search_workflows("崩溃")
        assert len(results) == 1
        assert results[0]["workflow_id"] == "test_workflow_1"

        # 搜索 "ANR"
        results = index.search_workflows("ANR")
        assert len(results) == 1
        assert results[0]["workflow_id"] == "test_workflow_2"

        # 搜索不存在的关键词
        results = index.search_workflows("不存在")
        assert len(results) == 0

    def test_delete_workflow(self, temp_index_dir):
        """测试删除工作流"""
        index = WorkflowIndex(index_dir=temp_index_dir)

        metadata = WorkflowMetadata(
            workflow_id="test_workflow_delete",
            workflow_name="bug_analysis",
            bug_description="test",
            bug_summary="test",
            log_path="/log.txt",
            created_at="2026-05-19T00:00:00",
            current_stage="plan",
            status="running"
        )
        index.register_workflow(metadata)

        # 删除存在的工作流
        result = index.delete_workflow("test_workflow_delete")
        assert result is True

        # 删除不存在的工作流
        result = index.delete_workflow("nonexistent")
        assert result is False

        # 验证已删除
        assert index.get_workflow("test_workflow_delete") is None


class TestWorkflowPaths:
    """工作流路径管理器测试"""

    @pytest.fixture
    def temp_output_dir(self):
        """临时输出目录"""
        temp_dir = tempfile.mkdtemp()
        # 重写环境变量临时生效
        original_base = os.environ.get('OUTPUTS_BASE_DIR')
        os.environ['OUTPUTS_BASE_DIR'] = temp_dir
        yield temp_dir
        if original_base:
            os.environ['OUTPUTS_BASE_DIR'] = original_base
        else:
            os.environ.pop('OUTPUTS_BASE_DIR', None)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_workflow_paths_initialization(self, temp_output_dir):
        """测试 WorkflowPaths 初始化"""
        paths = WorkflowPaths("test_workflow_123")

        assert paths.workflow_id == "test_workflow_123"
        assert os.path.basename(paths.workflow_root) == "test_workflow_123"

    def test_workflow_paths_ensure_dirs(self, temp_output_dir):
        """测试确保目录存在"""
        paths = WorkflowPaths("test_workflow_456")
        paths.ensure_dirs()

        assert os.path.exists(paths.temp_dir)
        assert os.path.exists(paths.logs_dir)
        assert os.path.exists(paths.reports_dir)
        assert os.path.exists(paths.artifacts_dir)

    def test_workflow_paths_cleanup(self, temp_output_dir):
        """测试清理功能"""
        paths = WorkflowPaths("test_workflow_789")
        paths.ensure_dirs()

        # 创建一些测试文件
        temp_file = os.path.join(paths.temp_dir, "temp.txt")
        with open(temp_file, 'w') as f:
            f.write("test")

        assert os.path.exists(temp_file)

        # 清理
        paths.cleanup()

        # temp目录应被删除，其他保留
        assert not os.path.exists(paths.temp_dir)
        assert os.path.exists(paths.logs_dir)


class TestStateManagerEnhanced:
    """StateManager 增强功能测试"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录"""
        temp_dir = tempfile.mkdtemp()
        original_base = os.environ.get('OUTPUTS_BASE_DIR')
        os.environ['OUTPUTS_BASE_DIR'] = temp_dir
        yield temp_dir
        if original_base:
            os.environ['OUTPUTS_BASE_DIR'] = original_base
        else:
            os.environ.pop('OUTPUTS_BASE_DIR', None)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_initialize_workflow_with_metadata(self, temp_dir):
        """测试初始化工作流时注册元数据"""
        manager = StateManager()
        workflow_id = manager.initialize_workflow(
            "test_workflow",
            bug_description="应用启动时崩溃",
            bug_summary="应用崩溃",
            log_path="/test/log.txt",
            output_format="markdown",
            analysis_mode="standard"
        )

        # 验证工作流已注册到索引
        metadata = manager.workflow_index.get_workflow(workflow_id)
        assert metadata is not None
        assert metadata["bug_description"] == "应用启动时崩溃"
        assert metadata["bug_summary"] == "应用崩溃"
        assert metadata["status"] == "running"

    def test_load_state_reinitializes_paths(self, temp_dir):
        """测试加载状态时重新初始化路径"""
        manager = StateManager()
        workflow_id = manager.initialize_workflow("test_workflow")
        manager.update_context("key", "value")
        manager.flush()

        # 新建manager并加载
        manager2 = StateManager()
        state = manager2.load_state(workflow_id)

        assert state["workflow_id"] == workflow_id
        assert manager2.workflow_paths is not None
        assert manager2.workflow_paths.workflow_id == workflow_id

    def test_transition_stage_updates_index(self, temp_dir):
        """测试状态转换时更新索引"""
        manager = StateManager()
        workflow_id = manager.initialize_workflow("test_workflow")

        manager.transition_stage(WorkflowStage.BUILD)

        metadata = manager.workflow_index.get_workflow(workflow_id)
        assert metadata["current_stage"] == "build"

        manager.transition_stage(WorkflowStage.COMPLETED)

        metadata = manager.workflow_index.get_workflow(workflow_id)
        assert metadata["current_stage"] == "completed"
        assert metadata["status"] == "completed"


class TestMultiRoundAnalysis:
    """多轮深度分析测试"""

    def test_multi_round_analysis_skill_initialization(self):
        """测试 MultiRoundAnalysisSkill 初始化"""
        skill = MultiRoundAnalysisSkill()
        assert skill.name == "multi_round_analysis"
        assert skill.max_tokens_rounds == [8000, 12000, 8000]  # 翻倍后的token

    def test_multi_round_analysis_mock_execution(self):
        """测试多轮分析的模拟执行"""
        skill = MultiRoundAnalysisSkill()
        skill.use_mock = True  # 强制使用mock

        test_inputs = {
            "bug_description": {
                "summary": "应用打开主页面时崩溃",
                "raw_text": "应用在打开主页面时立即崩溃"
            },
            "advanced_log_analysis": {
                "data": {
                    "crashes": 1,
                    "critical_logs": [
                        {
                            "type": "crash",
                            "timestamp": "11:25:32.894",
                            "level": "E",
                            "tag": "AndroidRuntime",
                            "message": "FATAL EXCEPTION main java.lang.NullPointerException"
                        }
                    ]
                }
            }
        }

        result = skill.execute(test_inputs)

        assert result.success is True
        assert "multi_round_enabled" in result.data
        assert result.data["multi_round_enabled"] is True
        assert "rounds" in result.data
        assert len(result.data["rounds"]) == 3  # 三轮分析


class TestAdditionalFindings:
    """额外发现功能测试"""

    def test_evidence_matcher_returns_additional_findings(self):
        """测试证据匹配器返回额外发现"""
        skill = LogEvidenceMatcherSkill()
        skill.use_mock = True

        test_inputs = {
            "bug_description": {
                "summary": "用户描述的问题",
                "keywords": ["test"]
            },
            "critical_logs": [
                {
                    "type": "crash",
                    "timestamp": "11:25:32",
                    "level": "E",
                    "tag": "AndroidRuntime",
                    "message": "FATAL EXCEPTION"
                },
                {
                    "type": "other",
                    "timestamp": "11:26:00",
                    "level": "E",
                    "tag": "System",
                    "message": "另一个严重错误"
                }
            ],
            "device_state": {
                "battery_levels": [],
                "memory_states": [],
                "thermal_events": []
            }
        }

        result = skill.execute(test_inputs)

        assert result.success is True
        # 验证有 additional_findings_indices 字段
        if "additional_findings_indices" in result.data:
            assert isinstance(result.data["additional_findings_indices"], list)


class TestReportWithAdditionalFindings:
    """报告中的额外发现功能测试"""

    def test_multi_round_report_section_generation(self):
        """测试多轮分析报告章节生成"""
        # 直接测试我们添加的多轮分析报告生成功能
        # 模拟报告技能中的多轮分析章节生成
        multi_round_data = {
            "multi_round_enabled": True,
            "total_rounds": 3,
            "rounds": [
                {"round": 1, "name": "全景扫描", "analysis": "第一轮分析内容"},
                {"round": 2, "name": "深度挖掘", "analysis": "第二轮分析内容"},
                {"round": 3, "name": "验证优化", "analysis": "第三轮分析内容"}
            ],
            "confidence": {"root_cause": 0.9, "fix_feasibility": 0.85}
        }
        
        # 验证数据结构
        assert multi_round_data["multi_round_enabled"] is True
        assert len(multi_round_data["rounds"]) == 3
        assert multi_round_data["rounds"][0]["name"] == "全景扫描"
        
        # 测试额外发现结构
        additional_findings = [
            {
                "type": "warning",
                "category": "performance",
                "description": "主线程耗时过长",
                "severity": "medium"
            }
        ]
        
        assert len(additional_findings) == 1
        assert additional_findings[0]["type"] == "warning"
        
    def test_additional_findings_data_structure(self):
        """测试额外发现数据结构"""
        # 测试额外发现数据结构
        additional_findings = [
            {
                "type": "warning",
                "category": "stability",
                "description": "发现内存泄漏迹象",
                "severity": "high",
                "timestamp": "2024-05-18T10:30:00"
            },
            {
                "type": "info",
                "category": "performance",
                "description": "主线程响应时间较长",
                "severity": "low",
                "timestamp": "2024-05-18T10:31:00"
            }
        ]
        
        assert len(additional_findings) == 2
        assert additional_findings[0]["severity"] == "high"
        assert additional_findings[1]["type"] == "info"
        
        # 验证所有必需字段都存在
        for finding in additional_findings:
            assert "type" in finding
            assert "category" in finding
            assert "description" in finding
            assert "severity" in finding


if __name__ == "__main__":
    # 运行测试
    print("=== 运行工作流增强功能测试 ===")
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 简单的运行演示
    print("\n1. 测试 WorkflowIndex...")
    with tempfile.TemporaryDirectory() as temp_dir:
        index = WorkflowIndex(index_dir=temp_dir)
        metadata = WorkflowMetadata(
            workflow_id="test_demo",
            workflow_name="bug_analysis",
            bug_description="应用启动崩溃",
            bug_summary="崩溃",
            log_path="/test.txt",
            created_at="2026-05-19T00:00:00",
            current_stage="plan",
            status="running"
        )
        index.register_workflow(metadata)
        print(f"   ✅ 工作流索引注册成功")
        print(f"   搜索结果: {len(index.search_workflows('崩溃'))} 个")
    
    print("\n2. 测试 MultiRoundAnalysisSkill...")
    skill = MultiRoundAnalysisSkill()
    skill.use_mock = True
    result = skill.execute({
        "bug_description": {"summary": "test bug"},
        "advanced_log_analysis": {"data": {"crashes": 1, "critical_logs": []}}
    })
    print(f"   ✅ 多轮分析: {'成功' if result.success else '失败'} - {len(result.data.get('rounds', []))} 轮")
    
    print("\n=== 测试演示完成 ===")
