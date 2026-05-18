"""
StateManager - Harness Engineering状态管理系统
负责管理Agent执行状态、工作流进度和验证检查点
"""
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

class WorkflowStage(Enum):
    PLAN = "plan"
    BUILD = "build"
    VERIFY = "verify"
    FIX = "fix"
    COMPLETED = "completed"

class StateManager:
    def __init__(self, state_dir: str = None):
        # 自动计算项目根目录
        if state_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            state_dir = os.path.join(project_root, "outputs", "state")
        self.state_dir = state_dir
        self.current_state: Dict[str, Any] = {}
        self.checkpoints: List[Dict[str, Any]] = []
        self._ensure_dir()
    
    def _ensure_dir(self):
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)
    
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
        
        self._save_state()
        return workflow_id
    
    def transition_stage(self, next_stage: WorkflowStage, success: bool = True):
        """状态转换"""
        if success:
            self.current_state["stages_completed"].append(self.current_state["current_stage"])
        
        self.current_state["current_stage"] = next_stage.value
        self._add_checkpoint(f"Transitioned to {next_stage.value}")
        self._save_state()
    
    def update_context(self, key: str, value: Any):
        """更新上下文信息"""
        self.current_state["context"][key] = value
        self._save_state()
    
    def update_output(self, key: str, value: Any):
        """更新输出"""
        self.current_state["outputs"][key] = value
        self._save_state()
    
    def add_validation_result(self, check_name: str, passed: bool, details: str):
        """添加验证结果"""
        self.current_state["validation_results"].append({
            "check_name": check_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        self._save_state()
    
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
    
    def _save_state(self):
        """持久化保存状态"""
        if "workflow_id" not in self.current_state:
            return
        state_file = os.path.join(self.state_dir, f"{self.current_state['workflow_id']}.json")
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_state, f, ensure_ascii=False, indent=2)
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.current_state.copy()
    
    def is_verification_passed(self) -> bool:
        """检查是否所有验证都通过"""
        results = self.current_state.get("validation_results", [])
        if not results:
            return False
        return all(r["passed"] for r in results)
    
    def get_failed_validations(self) -> List[Dict[str, Any]]:
        """获取失败的验证"""
        return [r for r in self.current_state.get("validation_results", []) if not r["passed"]]
