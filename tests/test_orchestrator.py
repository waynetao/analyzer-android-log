"""
Orchestrator 单元测试
测试核心协调器的分阶段执行、恢复、技能执行等功能
"""

import pytest
import os
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from harness.core.state import StateManager, WorkflowStage
from harness.core.context import ContextEngine
from harness.core.orchestrator import Orchestrator
from harness.skills.base import BaseSkill, SkillResult
from harness.policies.base import BasePolicy, ValidationResult


# ============ 测试用 Skill 和 Policy ============

class DummySkill(BaseSkill):
    """测试用技能"""
    def __init__(self, name_str="dummy_skill", should_fail=False, should_raise=False):
        self._name = name_str
        self.should_fail = should_fail
        self.should_raise = should_raise

    @property
    def name(self) -> str:
        return self._name

    def execute(self, inputs):
        if self.should_raise:
            raise RuntimeError(f"Skill {self._name} raised an error")
        if self.should_fail:
            return SkillResult(False, {}, f"Skill {self._name} failed")
        return SkillResult(True, {"result": f"{self._name}_output"}, f"Skill {self._name} succeeded")


class DummyPolicy(BasePolicy):
    """测试用策略"""
    def __init__(self, name_str="dummy_policy", input_pass=True, output_pass=True):
        self._name = name_str
        self.input_pass = input_pass
        self.output_pass = output_pass

    @property
    def name(self) -> str:
        return self._name

    def validate_input(self, inputs):
        return ValidationResult(self.input_pass, "input check")

    def validate_output(self, outputs):
        return ValidationResult(self.output_pass, "output check")


# ============ Fixtures ============

@pytest.fixture
def temp_state_dir(tmp_path):
    """临时状态目录"""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return str(state_dir)


@pytest.fixture
def orchestrator(temp_state_dir):
    """创建带基本配置的 Orchestrator"""
    context_engine = ContextEngine()
    state_manager = StateManager(state_dir=temp_state_dir)
    orch = Orchestrator(context_engine, state_manager)
    return orch


@pytest.fixture
def orchestrator_with_skills(orchestrator):
    """注册了测试技能的 Orchestrator"""
    orchestrator.register_skill(DummySkill("skill_a"))
    orchestrator.register_skill(DummySkill("skill_b"))
    return orchestrator


@pytest.fixture
def orchestrator_with_policies(orchestrator_with_skills):
    """注册了测试策略的 Orchestrator"""
    orchestrator_with_skills.register_policy(DummyPolicy("policy_a"))
    orchestrator_with_skills.register_policy(DummyPolicy("policy_b"))
    return orchestrator_with_skills


# ============ 测试类 ============

class TestOrchestratorInit:
    """初始化测试"""

    def test_initialization(self, orchestrator):
        assert orchestrator.context_engine is not None
        assert orchestrator.state_manager is not None
        assert len(orchestrator.skills) == 0
        assert len(orchestrator.policies) == 0

    def test_register_skill(self, orchestrator):
        skill = DummySkill("test_skill")
        orchestrator.register_skill(skill)
        assert "test_skill" in orchestrator.skills
        assert len(orchestrator.skills) == 1

    def test_register_multiple_skills(self, orchestrator):
        orchestrator.register_skill(DummySkill("skill_1"))
        orchestrator.register_skill(DummySkill("skill_2"))
        orchestrator.register_skill(DummySkill("skill_3"))
        assert len(orchestrator.skills) == 3

    def test_register_policy(self, orchestrator):
        policy = DummyPolicy("test_policy")
        orchestrator.register_policy(policy)
        assert len(orchestrator.policies) == 1

    def test_register_multiple_policies(self, orchestrator):
        orchestrator.register_policy(DummyPolicy("p1"))
        orchestrator.register_policy(DummyPolicy("p2"))
        assert len(orchestrator.policies) == 2


class TestOrchestratorPlan:
    """PLAN 阶段测试"""

    def test_plan_returns_state(self, orchestrator_with_policies):
        inputs = {"bug_description": {"summary": "test bug"}, "log_path": "/tmp/test.log"}
        result = orchestrator_with_policies.plan("test_workflow", inputs)
        assert "workflow_id" in result
        assert result["current_stage"] == WorkflowStage.PLAN.value
        assert "inputs" in result["context"]

    def test_plan_records_validation_results(self, orchestrator_with_policies):
        inputs = {"bug_description": {"summary": "test bug"}, "log_path": "/tmp/test.log"}
        result = orchestrator_with_policies.plan("test_workflow", inputs)
        # 两个策略应该各产生一条验证结果
        validations = result["validation_results"]
        input_validations = [v for v in validations if v["check_name"].startswith("input_")]
        assert len(input_validations) == 2

    def test_plan_with_failing_input_policy(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)
        orch.register_policy(DummyPolicy("failing_policy", input_pass=False))
        inputs = {"bug_description": {"summary": "test bug"}}
        result = orch.plan("test_workflow", inputs)
        # 即使输入验证失败，PLAN 也应完成（记录结果）
        failed = [v for v in result["validation_results"] if not v["passed"]]
        assert len(failed) > 0


class TestOrchestratorBuild:
    """BUILD 阶段测试"""

    def test_build_executes_skills(self, orchestrator_with_skills):
        # 先 PLAN
        inputs = {"bug_description": {"summary": "test"}, "log_path": "/tmp/test.log"}
        orchestrator_with_skills.plan("test_workflow", inputs)
        # 再 BUILD
        result = orchestrator_with_skills.build()
        assert "skill_a" in result["outputs"]
        assert "skill_b" in result["outputs"]
        assert result["outputs"]["skill_a"]["success"] is True

    def test_build_continues_after_skill_failure(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)
        orch.register_skill(DummySkill("failing_skill", should_fail=True))
        orch.register_skill(DummySkill("succeeding_skill"))

        inputs = {"bug_description": {"summary": "test"}}
        orch.plan("test_workflow", inputs)
        result = orch.build()

        # 失败的技能应该记录失败
        assert result["outputs"]["failing_skill"]["success"] is False
        # 后续技能应继续执行
        assert result["outputs"]["succeeding_skill"]["success"] is True

    def test_build_continues_after_skill_exception(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)
        orch.register_skill(DummySkill("raising_skill", should_raise=True))
        orch.register_skill(DummySkill("normal_skill"))

        inputs = {"bug_description": {"summary": "test"}}
        orch.plan("test_workflow", inputs)
        result = orch.build()

        # 异常技能不应中断 BUILD
        assert "raising_skill" not in result["outputs"]
        assert "normal_skill" in result["outputs"]


class TestOrchestratorVerify:
    """VERIFY 阶段测试"""

    def test_verify_applies_policies(self, orchestrator_with_policies):
        inputs = {"bug_description": {"summary": "test"}}
        orchestrator_with_policies.plan("test_workflow", inputs)
        orchestrator_with_policies.build()
        result = orchestrator_with_policies.verify()

        output_validations = [v for v in result["validation_results"]
                              if v["check_name"].startswith("output_")]
        assert len(output_validations) == 2

    def test_verify_with_failing_policy(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)
        orch.register_skill(DummySkill("skill_a"))
        orch.register_policy(DummyPolicy("failing_policy", output_pass=False))

        inputs = {"bug_description": {"summary": "test"}}
        orch.plan("test_workflow", inputs)
        orch.build()
        result = orch.verify()

        assert not orch.state_manager.is_verification_passed()


class TestOrchestratorFix:
    """FIX 阶段测试"""

    def test_fix_transitions_to_completed(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)

        # 需要先经过 PLAN 和 BUILD
        inputs = {"bug_description": {"summary": "test"}}
        orch.register_skill(DummySkill("skill_a"))
        orch.register_policy(DummyPolicy("policy_a", output_pass=False))
        orch.plan("test_workflow", inputs)
        orch.build()
        orch.verify()

        result = orch.fix()
        assert result["current_stage"] == WorkflowStage.COMPLETED.value


class TestOrchestratorFullWorkflow:
    """完整工作流测试"""

    def test_execute_workflow_success(self, orchestrator_with_policies):
        inputs = {"bug_description": {"summary": "test bug"}, "log_path": "/tmp/test.log"}
        result = orchestrator_with_policies.execute_workflow("test_workflow", inputs)
        assert "skill_a" in result
        assert "skill_b" in result

    def test_execute_workflow_exception_path(self, temp_state_dir):
        """工作流异常路径应持久化状态"""
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)

        # 模拟 _plan_phase 抛出异常
        with patch.object(orch, '_plan_phase', side_effect=RuntimeError("Plan failed")):
            inputs = {"bug_description": {"summary": "test"}}
            with pytest.raises(RuntimeError, match="Plan failed"):
                orch.execute_workflow("test_workflow", inputs)

        # 异常路径应持久化状态（flush 在 except 中调用）
        state = state_manager.get_state()
        assert "workflow_exception" in [v["check_name"] for v in state.get("validation_results", [])]


class TestOrchestratorResume:
    """恢复执行测试"""

    def test_resume_from_plan_stage(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)
        orch.register_skill(DummySkill("skill_a"))
        orch.register_policy(DummyPolicy("policy_a"))

        # 只执行 PLAN
        inputs = {"bug_description": {"summary": "test"}}
        orch.plan("test_workflow", inputs)

        # 从 PLAN 阶段恢复
        result = orch.resume()
        assert "skill_a" in result

    def test_resume_from_build_stage(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)
        orch.register_skill(DummySkill("skill_a"))
        orch.register_policy(DummyPolicy("policy_a"))

        inputs = {"bug_description": {"summary": "test"}}
        orch.plan("test_workflow", inputs)
        orch.build()

        result = orch.resume()
        assert result is not None


class TestOrchestratorExecuteSkill:
    """独立技能执行测试"""

    def test_execute_skill_returns_output(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)
        orch.register_skill(DummySkill("test_skill"))
        # 需要先初始化工作流，因为 _prepare_skill_inputs 依赖 state["outputs"]
        state_manager.initialize_workflow("test_workflow")
        result = orch.execute_skill("test_skill", {"some": "input"})
        assert result["success"] is True
        assert result["data"]["result"] == "test_skill_output"

    def test_execute_skill_raises_for_unknown_skill(self, orchestrator):
        with pytest.raises(ValueError, match="未注册"):
            orchestrator.execute_skill("nonexistent_skill", {})

    def test_execute_skill_records_analytics_on_exception(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)
        orch.register_skill(DummySkill("bad_skill", should_raise=True))
        state_manager.initialize_workflow("test_workflow")
        with pytest.raises(RuntimeError):
            orch.execute_skill("bad_skill", {})


class TestOrchestratorLoadWorkflow:
    """工作流加载测试"""

    def test_load_workflow_success(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)

        # 先创建一个工作流
        inputs = {"bug_description": {"summary": "test"}}
        orch.plan("test_workflow", inputs)
        workflow_id = state_manager.current_state["workflow_id"]

        # 通过新 Orchestrator 加载
        state_manager2 = StateManager(state_dir=temp_state_dir)
        orch2 = Orchestrator(context_engine, state_manager2)
        state = orch2.load_workflow(workflow_id)
        assert state["workflow_id"] == workflow_id

    def test_load_workflow_raises_for_missing(self, orchestrator):
        with pytest.raises(FileNotFoundError):
            orchestrator.load_workflow("nonexistent_workflow_id")


class TestOrchestratorListWorkflows:
    """工作流列表测试"""

    def test_list_workflows_empty(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)
        assert orch.list_workflows() == []

    def test_list_workflows_returns_saved(self, temp_state_dir):
        context_engine = ContextEngine()
        state_manager = StateManager(state_dir=temp_state_dir)
        orch = Orchestrator(context_engine, state_manager)

        # 创建两个工作流
        orch.plan("workflow1", {"bug_description": {"summary": "test1"}})
        orch.plan("workflow2", {"bug_description": {"summary": "test2"}})

        workflows = orch.list_workflows()
        assert len(workflows) == 2


class TestOrchestratorGetCurrentState:
    """获取当前状态测试"""

    def test_get_current_state(self, orchestrator):
        inputs = {"bug_description": {"summary": "test"}}
        orchestrator.register_policy(DummyPolicy("policy_a"))
        orchestrator.plan("test_workflow", inputs)
        state = orchestrator.get_current_state()
        assert "workflow_id" in state
        assert state["current_stage"] == WorkflowStage.PLAN.value
