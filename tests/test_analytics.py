"""
Analytics 模块单元测试
测试统计分析功能的各个组件
"""

import pytest
import time
from datetime import datetime

from harness.core.analytics import (
    AnalyticsCollector,
    SkillMetrics,
    StageMetrics,
    WorkflowMetrics,
    SystemMetrics
)


class TestSkillMetrics:
    """技能指标测试"""

    def test_skill_metrics_initialization(self):
        """测试技能指标初始化"""
        metrics = SkillMetrics(skill_name="test_skill")
        assert metrics.skill_name == "test_skill"
        assert metrics.execution_count == 0
        assert metrics.success_count == 0
        assert metrics.failure_count == 0
        assert metrics.success_rate == 0.0

    def test_success_rate_calculation(self):
        """测试成功率计算"""
        metrics = SkillMetrics(skill_name="test_skill")
        metrics.execution_count = 10
        metrics.success_count = 8
        metrics.failure_count = 2
        assert metrics.success_rate == 80.0

    def test_avg_duration_calculation(self):
        """测试平均耗时计算"""
        metrics = SkillMetrics(skill_name="test_skill")
        metrics.execution_count = 3
        metrics.total_duration_ms = 300.0
        assert metrics.avg_duration_ms == 100.0

    def test_min_max_duration_tracking(self):
        """测试最长最短耗时跟踪"""
        metrics = SkillMetrics(skill_name="test_skill")
        metrics.record_duration(100.0)
        metrics.record_duration(200.0)
        metrics.record_duration(150.0)
        assert metrics.min_duration_ms == 100.0
        assert metrics.max_duration_ms == 200.0

    def test_success_rate_with_zero_executions(self):
        """测试零执行时的成功率"""
        metrics = SkillMetrics(skill_name="test_skill")
        assert metrics.success_rate == 0.0
        assert metrics.avg_duration_ms == 0.0


class TestStageMetrics:
    """阶段指标测试"""

    def test_stage_metrics_initialization(self):
        """测试阶段指标初始化"""
        metrics = StageMetrics(stage_name="PLAN")
        assert metrics.stage_name == "PLAN"
        assert metrics.execution_count == 0
        assert metrics.success_rate == 0.0


class TestWorkflowMetrics:
    """工作流指标测试"""

    def test_workflow_metrics_initialization(self):
        """测试工作流指标初始化"""
        metrics = WorkflowMetrics(
            workflow_id="test_001",
            workflow_name="test_workflow",
            start_time=datetime.now().isoformat()
        )
        assert metrics.workflow_id == "test_001"
        assert metrics.workflow_name == "test_workflow"
        assert metrics.status == "running"

    def test_workflow_metrics_with_analysis_result(self):
        """测试包含分析结果的工作流指标"""
        metrics = WorkflowMetrics(
            workflow_id="test_001",
            workflow_name="test_workflow",
            start_time=datetime.now().isoformat()
        )
        metrics.bug_type = "crash"
        metrics.crash_count = 5
        metrics.anr_count = 2

        assert metrics.bug_type == "crash"
        assert metrics.crash_count == 5
        assert metrics.anr_count == 2


class TestAnalyticsCollector:
    """统计分析收集器测试"""

    def test_collector_initialization(self, temp_analytics_dir):
        """测试收集器初始化"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)
        assert collector.analytics_dir == temp_analytics_dir
        assert collector.current_workflow is None

    def test_start_workflow(self, temp_analytics_dir):
        """测试开始工作流"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)
        workflow_id = collector.start_workflow("test_workflow")

        assert workflow_id.startswith("test_workflow")
        assert collector.current_workflow is not None
        assert collector.current_workflow.workflow_name == "test_workflow"
        assert collector.system_metrics.total_workflows == 1

    def test_record_skill_execution_success(self, temp_analytics_dir):
        """测试记录技能执行成功"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)
        collector.start_workflow("test_workflow")

        collector.record_skill_execution(
            skill_name="log_extraction",
            success=True,
            duration_ms=1000.0
        )

        assert "log_extraction" in collector.system_metrics.skill_metrics
        metrics = collector.system_metrics.skill_metrics["log_extraction"]
        assert metrics.execution_count == 1
        assert metrics.success_count == 1
        assert metrics.success_rate == 100.0

    def test_record_skill_execution_failure(self, temp_analytics_dir):
        """测试记录技能执行失败"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)
        collector.start_workflow("test_workflow")

        collector.record_skill_execution(
            skill_name="log_extraction",
            success=False,
            duration_ms=500.0,
            error="File not found"
        )

        metrics = collector.system_metrics.skill_metrics["log_extraction"]
        assert metrics.failure_count == 1
        assert "File not found" in collector.system_metrics.error_distribution

    def test_record_stage_execution(self, temp_analytics_dir):
        """测试记录阶段执行"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)
        collector.start_workflow("test_workflow")

        collector.record_stage_execution(
            stage_name="BUILD",
            success=True,
            duration_ms=2000.0
        )

        assert "BUILD" in collector.system_metrics.stage_metrics
        metrics = collector.system_metrics.stage_metrics["BUILD"]
        assert metrics.execution_count == 1
        assert metrics.success_count == 1

    def test_record_validation(self, temp_analytics_dir):
        """测试记录验证结果"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)
        collector.start_workflow("test_workflow")

        collector.record_validation(True)
        collector.record_validation(True)
        collector.record_validation(False)

        assert collector.current_workflow.validation_passed == 2
        assert collector.current_workflow.validation_failed == 1

    def test_record_analysis_result(self, temp_analytics_dir):
        """测试记录分析结果"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)
        collector.start_workflow("test_workflow")

        collector.record_analysis_result(
            bug_type="crash",
            crash_count=5,
            anr_count=2,
            exception_count=10,
            critical_log_count=15
        )

        assert collector.current_workflow.bug_type == "crash"
        assert collector.current_workflow.crash_count == 5
        assert collector.current_workflow.anr_count == 2
        assert "crash" in collector.system_metrics.bug_type_distribution

    def test_end_workflow_completed(self, temp_analytics_dir):
        """测试结束工作流 - 成功"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)
        collector.start_workflow("test_workflow")

        time.sleep(0.01)  # 确保有时间差
        collector.end_workflow(status="completed")

        assert collector.current_workflow is None
        assert collector.system_metrics.completed_workflows == 1
        assert collector.system_metrics.failed_workflows == 0

    def test_end_workflow_failed(self, temp_analytics_dir):
        """测试结束工作流 - 失败"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)
        collector.start_workflow("test_workflow")

        collector.end_workflow(status="failed", error_message="Test error")

        assert collector.current_workflow is None
        assert collector.system_metrics.completed_workflows == 0
        assert collector.system_metrics.failed_workflows == 1

    def test_generate_system_report(self, temp_analytics_dir):
        """测试生成系统报告"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)
        collector.start_workflow("test_workflow")
        collector.record_skill_execution("skill1", True, 1000.0)
        collector.end_workflow("completed")

        report = collector.generate_system_report()

        assert "summary" in report
        assert "skill_performance" in report
        assert "stage_performance" in report
        assert report["summary"]["total_workflows"] == 1

    def test_generate_markdown_report(self, temp_analytics_dir):
        """测试生成 Markdown 报告"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)
        collector.start_workflow("test_workflow")
        collector.record_skill_execution("skill1", True, 1000.0)
        collector.end_workflow("completed")

        md = collector.generate_markdown_report()

        assert "# Android Log Analyzer" in md
        assert "📊 概览" in md
        assert "技能性能" in md

    def test_recommendations_generation(self, temp_analytics_dir):
        """测试优化建议生成"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)

        # 添加一个失败率高的技能
        collector.start_workflow("test1")
        for _ in range(5):
            collector.record_skill_execution("unstable_skill", False, 1000.0, error="Timeout")
        collector.end_workflow("failed")

        # 添加一个耗时长的技能
        collector.start_workflow("test2")
        for _ in range(3):
            collector.record_skill_execution("slow_skill", True, 10000.0)
        collector.end_workflow("completed")

        report = collector.generate_system_report()

        assert len(report["recommendations"]) > 0
        assert any("unstable_skill" in rec for rec in report["recommendations"])

    def test_multiple_workflows_tracking(self, temp_analytics_dir):
        """测试多工作流跟踪"""
        collector = AnalyticsCollector(analytics_dir=temp_analytics_dir)

        # 执行多个工作流
        for i in range(3):
            collector.start_workflow(f"workflow_{i}")
            collector.record_skill_execution("skill1", True, 1000.0)
            collector.record_skill_execution("skill2", True, 2000.0)
            collector.end_workflow("completed")

        assert collector.system_metrics.total_workflows == 3
        assert collector.system_metrics.completed_workflows == 3
        assert len(collector.system_metrics.skill_metrics) == 2

    def test_get_analytics_collector_singleton(self, temp_analytics_dir):
        """测试全局收集器单例"""
        from harness.core.analytics import get_analytics_collector

        collector1 = get_analytics_collector()
        collector2 = get_analytics_collector()

        assert collector1 is collector2
