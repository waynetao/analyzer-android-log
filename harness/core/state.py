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
from dataclasses import dataclass, asdict
from .logging import get_logger
from .paths import OUTPUTS_STATE_DIR_STR, OUTPUTS_INDEX_DIR_STR, WorkflowPaths

logger = get_logger(__name__)


class WorkflowStage(Enum):
    PLAN = "plan"
    BUILD = "build"
    VERIFY = "verify"
    FIX = "fix"
    COMPLETED = "completed"


@dataclass
class WorkflowMetadata:
    """工作流元数据"""
    workflow_id: str
    workflow_name: str
    bug_description: str
    bug_summary: str
    log_path: str
    created_at: str
    current_stage: str
    status: str  # "running", "completed", "failed"
    output_format: Optional[str] = None
    analysis_mode: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    additional_findings: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self):
        if self.additional_findings is None:
            self.additional_findings = []


class WorkflowIndex:
    """工作流索引管理器
    
    记录所有工作流的元数据，方便查询和追溯
    """
    
    def __init__(self, index_dir: str = None):
        self.index_dir = index_dir or OUTPUTS_INDEX_DIR_STR
        self._index_file = os.path.join(self.index_dir, "workflow_index.json")
        self._ensure_dir()
        self._index: Dict[str, Dict[str, Any]] = self._load_index()
    
    def _ensure_dir(self):
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            logger.info(f"创建工作流索引目录: {self.index_dir}")
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """加载索引文件"""
        if os.path.exists(self._index_file):
            try:
                with open(self._index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"加载索引文件失败: {e}, 将创建新索引")
                return {}
        return {}
    
    def _save_index(self):
        """保存索引文件"""
        try:
            with open(self._index_file, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"保存索引文件失败: {e}")
    
    def register_workflow(self, metadata: WorkflowMetadata):
        """注册新工作流"""
        self._index[metadata.workflow_id] = asdict(metadata)
        self._save_index()
        logger.info(f"工作流已注册到索引: {metadata.workflow_id}")
    
    def update_workflow(self, workflow_id: str, **kwargs):
        """更新工作流信息"""
        if workflow_id in self._index:
            self._index[workflow_id].update(kwargs)
            if 'updated_at' not in kwargs:
                self._index[workflow_id]['updated_at'] = datetime.now().isoformat()
            self._save_index()
            logger.debug(f"工作流索引已更新: {workflow_id}")
    
    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取单个工作流信息"""
        return self._index.get(workflow_id)
    
    def list_workflows(self, limit: int = None, status: str = None) -> List[Dict[str, Any]]:
        """列出所有工作流
        
        Args:
            limit: 限制返回数量（最新的）
            status: 按状态过滤
        """
        workflows = list(self._index.values())
        
        # 按创建时间倒序排列
        workflows.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 按状态过滤
        if status:
            workflows = [w for w in workflows if w.get('status') == status]
        
        # 限制数量
        if limit:
            workflows = workflows[:limit]
        
        return workflows
    
    def search_workflows(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索工作流（按 bug 描述或摘要）"""
        keyword = keyword.lower()
        results = []
        for workflow in self._index.values():
            desc = workflow.get('bug_description', '').lower()
            summary = workflow.get('bug_summary', '').lower()
            if keyword in desc or keyword in summary:
                results.append(workflow)
        
        # 按时间倒序排列
        results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return results
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """从索引中删除工作流"""
        if workflow_id in self._index:
            del self._index[workflow_id]
            self._save_index()
            logger.info(f"工作流已从索引删除: {workflow_id}")
            return True
        return False
    
    def cleanup_old_workflows(self, days: int = 30):
        """清理旧工作流索引"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        to_delete = []
        
        for workflow_id, workflow in self._index.items():
            created_at = workflow.get('created_at')
            if created_at:
                try:
                    created_ts = datetime.fromisoformat(created_at).timestamp()
                    if created_ts < cutoff:
                        to_delete.append(workflow_id)
                except (ValueError, TypeError):
                    continue
        
        for workflow_id in to_delete:
            self.delete_workflow(workflow_id)
        
        logger.info(f"清理了 {len(to_delete)} 个旧工作流索引")


class StateManager:
    def __init__(self, state_dir: str = None):
        if state_dir is None: state_dir = OUTPUTS_STATE_DIR_STR
        self.state_dir = state_dir
        self.current_state: Dict[str, Any] = {}
        self.checkpoints: List[Dict[str, Any]] = []
        self._dirty: bool = False
        self._workflow_paths: Optional[WorkflowPaths] = None
        self.workflow_index = WorkflowIndex()
        logger.info(f"StateManager 初始化完成，状态目录: {state_dir}")
    
    def _ensure_dir(self):
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)
            logger.info(f"创建状态目录: {self.state_dir}")
    
    @property
    def workflow_paths(self) -> Optional[WorkflowPaths]:
        """获取当前工作流的路径管理器"""
        return self._workflow_paths
    
    def initialize_workflow(self, workflow_name: str, bug_description: str = "", 
                           bug_summary: str = "", log_path: str = "", 
                           output_format: str = None, analysis_mode: str = None) -> str:
        workflow_id = f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        self._workflow_paths = WorkflowPaths(workflow_id).ensure_dirs()
        
        if self.state_dir == OUTPUTS_STATE_DIR_STR:
            self.state_dir = self._workflow_paths.state_dir_str
            self._ensure_dir()
        
        logger.info(f"工作流专属目录初始化: {self._workflow_paths.workflow_root}")
        
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
        
        # 注册到工作流索引
        metadata = WorkflowMetadata(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            bug_description=bug_description,
            bug_summary=bug_summary or (bug_description[:100] + "..." if len(bug_description) > 100 else bug_description),
            log_path=log_path,
            created_at=datetime.now().isoformat(),
            current_stage=WorkflowStage.PLAN.value,
            status="running",
            output_format=output_format,
            analysis_mode=analysis_mode
        )
        self.workflow_index.register_workflow(metadata)
        
        self._mark_dirty()
        self.flush()
        logger.info(f"工作流初始化: {workflow_name}, ID: {workflow_id}")
        return workflow_id
    
    def load_state(self, workflow_id: str) -> Dict[str, Any]:
        """从文件加载指定工作流的状态
        
        查找顺序:
        1. workflows/{id}/state/{id}.json (新路径)
        2. {self.state_dir}/{id}.json (旧路径兼容)
        """
        state_file = None
        
        wp = WorkflowPaths(workflow_id)
        new_path = os.path.join(str(wp.state_dir), f"{workflow_id}.json")
        if os.path.exists(new_path):
            state_file = new_path
        else:
            old_path = os.path.join(self.state_dir, f"{workflow_id}.json")
            if os.path.exists(old_path):
                state_file = old_path
        
        if not state_file:
            logger.error(f"工作流状态文件不存在: {workflow_id}")
            raise FileNotFoundError(f"工作流 '{workflow_id}' 不存在")
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                self.current_state = json.load(f)
            
            self._workflow_paths = WorkflowPaths(workflow_id).ensure_dirs()
            self.state_dir = self._workflow_paths.state_dir_str
            
            logger.info(f"工作流状态已加载: {workflow_id}")
            return copy.deepcopy(self.current_state)
        except json.JSONDecodeError as e:
            logger.error(f"工作流状态文件损坏: {workflow_id}, 错误: {e}")
            raise ValueError(f"工作流 '{workflow_id}' 状态文件损坏")
    
    def cleanup_workflow(self):
        """清理当前工作流的临时文件"""
        if self._workflow_paths:
            self._workflow_paths.cleanup()
            logger.info(f"工作流临时文件已清理: {self._workflow_paths.workflow_id}")
    
    def transition_stage(self, next_stage: WorkflowStage, success: bool = True):
        """状态转换"""
        old_stage = self.current_state.get("current_stage")
        workflow_id = self.current_state.get("workflow_id")
        
        if success:
            self.current_state["stages_completed"].append(self.current_state["current_stage"])
        
        self.current_state["current_stage"] = next_stage.value
        
        # 更新工作流索引
        if workflow_id:
            status = "running"
            if next_stage == WorkflowStage.COMPLETED:
                status = "completed"
            self.workflow_index.update_workflow(
                workflow_id,
                current_stage=next_stage.value,
                status=status
            )
        
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
        os.makedirs(self.state_dir, exist_ok=True)
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
