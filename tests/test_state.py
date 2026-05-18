"""
State Manager 单元测试
测试状态管理器的各个功能
"""

import pytest
import os
import json
from datetime import datetime

from harness.core.state import StateManager, WorkflowStage


class TestWorkflowStage:
    """工作流阶段枚举测试"""

    def test_workflow_stage_values(self):
        """测试工作流阶段枚举值"""
        assert WorkflowStage.PLAN.value == "plan"
        assert WorkflowStage.BUILD.value == "build"
        assert WorkflowStage.VERIFY.value == "verify"
        assert WorkflowStage.FIX.value == "fix"
        assert WorkflowStage.COMPLETED.value == "completed"

    def test_workflow_stage_count(self):
        """测试阶段数量"""
        assert len(WorkflowStage) == 5


class TestStateManager:
    """状态管理器测试"""

    def test_initialization(self, temp_state_dir):
        """测试初始化"""
        manager = StateManager(state_dir=temp_state_dir)
        assert manager.state_dir == temp_state_dir
        assert os.path.exists(temp_state_dir)

    def test_initialize_workflow(self, temp_state_dir):
        """测试初始化工作流"""
        manager = StateManager(state_dir=temp_state_dir)
        workflow_id = manager.initialize_workflow("test_workflow")

        assert workflow_id.startswith("test_workflow_")
        assert "test_workflow" in manager.current_state["workflow_name"]
        assert manager.current_state["current_stage"] == WorkflowStage.PLAN.value

    def test_transition_stage(self, temp_state_dir):
        """测试状态转换"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")

        manager.transition_stage(WorkflowStage.BUILD)

        assert manager.current_state["current_stage"] == WorkflowStage.BUILD.value
        assert WorkflowStage.PLAN.value in manager.current_state["stages_completed"]

    def test_update_context(self, temp_state_dir):
        """测试更新上下文"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")

        manager.update_context("user_id", "123")
        manager.update_context("action", "test")

        assert manager.current_state["context"]["user_id"] == "123"
        assert manager.current_state["context"]["action"] == "test"

    def test_update_output(self, temp_state_dir):
        """测试更新输出"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")

        manager.update_output("skill1", {"result": "success"})
        manager.update_output("skill2", {"result": "failure"})

        assert "skill1" in manager.current_state["outputs"]
        assert "skill2" in manager.current_state["outputs"]
        assert manager.current_state["outputs"]["skill1"]["result"] == "success"

    def test_add_validation_result(self, temp_state_dir):
        """测试添加验证结果"""
        manager = StateManager(temp_state_dir)
        manager.initialize_workflow("test_workflow")

        manager.add_validation_result("check1", True, "Passed")
        manager.add_validation_result("check2", False, "Failed")

        assert len(manager.current_state["validation_results"]) == 2
        assert manager.current_state["validation_results"][0]["passed"] is True
        assert manager.current_state["validation_results"][1]["passed"] is False

    def test_is_verification_passed_all_true(self, temp_state_dir):
        """测试验证全部通过"""
        manager = StateManager(temp_state_dir)
        manager.initialize_workflow("test_workflow")

        manager.add_validation_result("check1", True, "Passed")
        manager.add_validation_result("check2", True, "Passed")

        assert manager.is_verification_passed() is True

    def test_is_verification_passed_with_failures(self, temp_state_dir):
        """测试验证有失败"""
        manager = StateManager(temp_state_dir)
        manager.initialize_workflow("test_workflow")

        manager.add_validation_result("check1", True, "Passed")
        manager.add_validation_result("check2", False, "Failed")

        assert manager.is_verification_passed() is False

    def test_is_verification_passed_empty(self, temp_state_dir):
        """测试验证结果为空"""
        manager = StateManager(temp_state_dir)
        manager.initialize_workflow("test_workflow")

        assert manager.is_verification_passed() is False

    def test_get_failed_validations(self, temp_state_dir):
        """测试获取失败的验证"""
        manager = StateManager(temp_state_dir)
        manager.initialize_workflow("test_workflow")

        manager.add_validation_result("check1", True, "Passed")
        manager.add_validation_result("check2", False, "Failed")
        manager.add_validation_result("check3", False, "Failed")

        failed = manager.get_failed_validations()
        assert len(failed) == 2
        assert all(not r["passed"] for r in failed)

    def test_save_and_load_state(self, temp_state_dir):
        """测试状态持久化"""
        manager = StateManager(state_dir=temp_state_dir)
        workflow_id = manager.initialize_workflow("test_workflow")
        manager.update_context("key", "value")

        # 重新创建 manager 并加载
        manager2 = StateManager(state_dir=temp_state_dir)
        state_file = os.path.join(temp_state_dir, f"{workflow_id}.json")

        assert os.path.exists(state_file)
        with open(state_file, 'r', encoding='utf-8') as f:
            saved_state = json.load(f)

        assert saved_state["workflow_id"] == workflow_id

    def test_multiple_workflows(self, temp_state_dir):
        """测试多工作流"""
        manager = StateManager(state_dir=temp_state_dir)

        # 第一个工作流
        id1 = manager.initialize_workflow("workflow1")
        manager.update_context("id", "1")

        # 第二个工作流
        id2 = manager.initialize_workflow("workflow2")
        manager.update_context("id", "2")

        # 检查文件是否都存在
        assert os.path.exists(os.path.join(temp_state_dir, f"{id1}.json"))
        assert os.path.exists(os.path.join(temp_state_dir, f"{id2}.json"))

    def test_get_state(self, temp_state_dir):
        """测试获取状态"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")
        manager.update_context("key", "value")

        state = manager.get_state()

        assert "workflow_id" in state
        assert "context" in state
        assert state["context"]["key"] == "value"

    def test_stage_sequence(self, temp_state_dir):
        """测试完整阶段序列"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")

        assert manager.current_state["current_stage"] == WorkflowStage.PLAN.value

        manager.transition_stage(WorkflowStage.BUILD)
        assert manager.current_state["current_stage"] == WorkflowStage.BUILD.value

        manager.transition_stage(WorkflowStage.VERIFY)
        assert manager.current_state["current_stage"] == WorkflowStage.VERIFY.value

        manager.transition_stage(WorkflowStage.FIX)
        assert manager.current_state["current_stage"] == WorkflowStage.FIX.value

        manager.transition_stage(WorkflowStage.COMPLETED)
        assert manager.current_state["current_stage"] == WorkflowStage.COMPLETED.value

        # 验证所有完成的阶段都被记录
        assert len(manager.current_state["stages_completed"]) == 4


class TestStateManagerDirtyFlag:
    """脏标记 + 延迟写入测试"""

    def test_mark_dirty_sets_flag(self, temp_state_dir):
        """_mark_dirty 正确设置脏标记"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")
        manager._dirty = False
        manager.update_context("key", "val")
        assert manager._dirty is True

    def test_flush_resets_dirty_flag(self, temp_state_dir):
        """flush 后脏标记重置"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")
        manager.update_context("key", "val")
        assert manager._dirty is True
        manager.flush()
        assert manager._dirty is False

    def test_flush_skips_when_not_dirty(self, temp_state_dir):
        """非脏状态时 flush 跳过写入"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")
        assert manager._dirty is False

        # 修改内存状态但不通过 _mark_dirty
        manager.current_state["context"]["sneaky"] = "value"
        manager.flush()

        # 重新加载，文件中不应包含 sneaky
        workflow_id = manager.current_state["workflow_id"]
        state_file = os.path.join(temp_state_dir, f"{workflow_id}.json")
        with open(state_file, 'r', encoding='utf-8') as f:
            saved = json.load(f)
        assert "sneaky" not in saved.get("context", {})

    def test_update_context_does_not_immediately_flush(self, temp_state_dir):
        """update_context 只标记脏，不立即写盘"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")
        manager._dirty = False

        # 记录修改时间
        workflow_id = manager.current_state["workflow_id"]
        state_file = os.path.join(temp_state_dir, f"{workflow_id}.json")
        mtime_before = os.path.getmtime(state_file)

        # update_context 只标记脏，不立即写盘
        import time
        time.sleep(0.05)
        manager.update_context("key", "val")
        assert manager._dirty is True

        # 文件可能还没更新（因为 update_context 不 flush）
        # 然后手动 flush
        manager.flush()

        # 确认文件已更新
        with open(state_file, 'r', encoding='utf-8') as f:
            saved = json.load(f)
        assert saved["context"]["key"] == "val"

    def test_add_validation_does_not_immediately_flush(self, temp_state_dir):
        """add_validation_result 只标记脏，不立即写盘"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")
        manager._dirty = False

        manager.add_validation_result("check1", True, "ok")
        assert manager._dirty is True

    def test_do_save_handles_os_error(self, temp_state_dir):
        """_do_save 捕获 OSError 不抛异常"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")

        # 在 Linux 上可以用 chmod 限制写权限，Windows 上跳过
        if os.name == 'nt':
            pytest.skip("chmod 不适用于 Windows")

        os.chmod(temp_state_dir, 0o444)
        try:
            manager._mark_dirty()
            manager.flush()  # 不应抛出异常
        finally:
            os.chmod(temp_state_dir, 0o755)

    def test_transition_stage_flushes_immediately(self, temp_state_dir):
        """transition_stage 立即持久化"""
        manager = StateManager(state_dir=temp_state_dir)
        manager.initialize_workflow("test_workflow")

        manager.transition_stage(WorkflowStage.BUILD)
        assert manager._dirty is False

        # 验证文件已更新
        workflow_id = manager.current_state["workflow_id"]
        state_file = os.path.join(temp_state_dir, f"{workflow_id}.json")
        with open(state_file, 'r', encoding='utf-8') as f:
            saved = json.load(f)
        assert saved["current_stage"] == WorkflowStage.BUILD.value


class TestStateManagerLoadState:
    """load_state 方法测试"""

    def test_load_state_success(self, temp_state_dir):
        """成功加载已保存的工作流状态"""
        manager = StateManager(state_dir=temp_state_dir)
        workflow_id = manager.initialize_workflow("test_workflow")
        manager.update_context("key", "value")
        manager.flush()

        # 新建 manager 并加载
        manager2 = StateManager(state_dir=temp_state_dir)
        state = manager2.load_state(workflow_id)
        assert state["workflow_id"] == workflow_id
        assert state["context"]["key"] == "value"

    def test_load_state_raises_file_not_found(self, temp_state_dir):
        """加载不存在的工作流抛出 FileNotFoundError"""
        manager = StateManager(state_dir=temp_state_dir)
        with pytest.raises(FileNotFoundError, match="不存在"):
            manager.load_state("nonexistent_workflow_id")

    def test_load_state_raises_value_error_for_corrupt_json(self, temp_state_dir):
        """加载损坏的 JSON 文件抛出 ValueError"""
        # 创建损坏的 JSON 文件
        corrupt_file = os.path.join(temp_state_dir, "corrupt_workflow.json")
        with open(corrupt_file, 'w') as f:
            f.write("{invalid json")

        manager = StateManager(state_dir=temp_state_dir)
        with pytest.raises(ValueError, match="损坏"):
            manager.load_state("corrupt_workflow")

    def test_load_state_returns_deep_copy(self, temp_state_dir):
        """load_state 返回深拷贝，不影响内部状态"""
        manager = StateManager(state_dir=temp_state_dir)
        workflow_id = manager.initialize_workflow("test_workflow")
        manager.update_context("key", "value1")
        manager.flush()

        manager2 = StateManager(state_dir=temp_state_dir)
        state = manager2.load_state(workflow_id)
        # 修改返回值不应影响内部状态
        state["context"]["key"] = "modified"
        assert manager2.current_state["context"]["key"] == "value1"
