"""
StateManager - Harness Engineering状态管理系统
负责管理Agent执行状态、工作流进度和验证检查点
"""
import os
import json
import copy
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from .logging import get_logger
from .paths import OUTPUTS_STATE_DIR_STR

logger = get_logger(__name__)


class WorkflowStage(Enum):
    PLAN = "plan"
    BUILD = "build"
    VERIFY = "verify"
    FIX = "fix"
    COMPLETED = "completed"


class StateManager:
    def __init__(self, state_dir: str = None):
        # 使用统一路径配置
        if state_dir is None:
            state_dir = OUTPUTS_STATE_DIR_STR
        self.state_dir = state_dir
        self.current_state: Dict[str, Any] = {}
        self.checkpoints: List[Dict[str, Any]] = []
        self._dirty: bool = False  # 脏标记：是否需要持久化
        self._ensure_dir()
        logger.info(f"StateManager 初始化完成，状态目录: {state_dir}")
    
    def _ensure_dir(self):
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)
            logger.info(f"创建状态目录: {self.state_dir}")
    
    def initialize_workflow(self, workflow_name: str) -> str:
        """初始化工作流状态"""
        workflow_id = f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        self.current_state = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "start_time": datetime.now().isoformat(),
            "current_stage": WorkflowStage.PLAN.value,
            "stages_completed": [],
            "validation_results": [],
            "context": {},
            "outputs": {}
        }
        
        self._mark_dirty()
        self.flush()
        logger.info(f"工作流初始化: {workflow_name}, ID: {workflow_id}")
        return workflow_id
    
    def transition_stage(self, next_stage: WorkflowStage, success: bool = True):
        """状态转换"""
        old_stage = self.current_state.get("current_stage")
        if success:
            self.current_state["stages_completed"].append(self.current_state["current_stage"])
        
        self.current_state["current_stage"] = next_stage.value
        self._add_checkpoint(f"Transitioned to {next_stage.value}")
        self._mark_dirty()
        self.flush()
        
        logger.info(f"状态转换: {old_stage} -> {next_stage.value}")
    
    def update_context(self, key: str, value: Any):
        """更新上下文信息"""
        self.current_state["context"][key] = value
        self._mark_dirty()
        logger.debug(f"上下文更新: {key}")
    
    def update_output(self, key: str, value: Any):
        """更新输出"""
        self.current_state["outputs"][key] = value
        self._mark_dirty()
        logger.debug(f"输出更新: {key}")
    
    def add_validation_result(self, check_name: str, passed: bool, details: str):
        """添加验证结果"""
        self.current_state["validation_results"].append({
            "check_name": check_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        self._mark_dirty()
        
        status = "通过" if passed else "失败"
        logger.info(f"验证结果: {check_name} - {status}")
    
    def _add_checkpoint(self, message: str):
        """添加检查点（用于调试和审计）"""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "current_stage": self.current_state.get("current_stage")
        }
        self.checkpoints.append(checkpoint)
        
        if len(self.checkpoints) > 100:  # 熵治理：限制检查点数量
            self.checkpoints = self.checkpoints[-50:]
    
    def _mark_dirty(self):
        """标记状态为脏（需要持久化）"""
        self._dirty = True

    def flush(self):
        """将脏状态持久化到磁盘（延迟写入）"""
        if not self._dirty:
            return
        self._do_save()
        self._dirty = False

    def _do_save(self):
        """实际执行持久化保存"""
        if "workflow_id" not in self.current_state:
            return
        state_file = os.path.join(self.state_dir, f"{self.current_state['workflow_id']}.json")
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_state, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.error(f"状态持久化失败: {e}")

    def _save_state(self):
        """兼容旧调用：标记脏并立即持久化"""
        self._mark_dirty()
        self.flush()
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态（深拷贝，防止外部修改影响内部状态）"""
        return copy.deepcopy(self.current_state)
    
    def is_verification_passed(self) -> bool:
        """检查是否所有验证都通过"""
        results = self.current_state.get("validation_results", [])
        if not results:
            return False
        return all(r["passed"] for r in results)
    
    def get_failed_validations(self) -> List[Dict[str, Any]]:
        """获取失败的验证"""
        return [r for r in self.current_state.get("validation_results", []) if not r["passed"]]
    
    def load_state(self, workflow_id: str) -> Dict[str, Any]:
        """从文件加载指定工作流的状态"""
        state_file = os.path.join(self.state_dir, f"{workflow_id}.json")
        if not os.path.exists(state_file):
            logger.error(f"工作流状态文件不存在: {workflow_id}")
            raise FileNotFoundError(f"工作流 '{workflow_id}' 不存在")
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                self.current_state = json.load(f)
            logger.info(f"工作流状态已加载: {workflow_id}")
            return copy.deepcopy(self.current_state)
        except json.JSONDecodeError as e:
            logger.error(f"工作流状态文件损坏: {workflow_id}, 错误: {e}")
            raise ValueError(f"工作流 '{workflow_id}' 状态文件损坏")
