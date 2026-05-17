"""
Orchestrator - Harness Engineering核心协调器
实现Plan-Build-Verify-Fix工作流，协调整个系统
"""
import sys
from typing import Dict, Any, List, Optional
from .context import ContextEngine
from .state import StateManager, WorkflowStage
from ..skills.base import BaseSkill
from ..policies.base import BasePolicy

class Orchestrator:
    def __init__(
        self,
        context_engine: ContextEngine,
        state_manager: StateManager
    ):
        self.context_engine = context_engine
        self.state_manager = state_manager
        self.skills: Dict[str, BaseSkill] = {}
        self.policies: List[BasePolicy] = []
    
    def register_skill(self, skill: BaseSkill):
        """注册技能（可插拔）"""
        self.skills[skill.name] = skill
        print(f"✅ 技能已注册: {skill.name}")
    
    def register_policy(self, policy: BasePolicy):
        """注册策略（约束和验证）"""
        self.policies.append(policy)
        print(f"📋 策略已加载: {policy.name}")
    
    def execute_workflow(
        self,
        workflow_name: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行完整工作流（Plan-Build-Verify-Fix）
        """
        print(f"\n🚀 开始执行工作流: {workflow_name}")
        
        # 1. 初始化
        workflow_id = self.state_manager.initialize_workflow(workflow_name)
        print(f"   工作流ID: {workflow_id}")
        
        try:
            # 2. PLAN - 规划阶段
            self._plan_phase(inputs)
            
            # 3. BUILD - 构建阶段
            self._build_phase(inputs)
            
            # 4. VERIFY - 验证阶段
            self._verify_phase()
            
            # 5. FIX - 如果需要修复
            if not self.state_manager.is_verification_passed():
                self._fix_phase()
            
            # 完成
            self.state_manager.transition_stage(WorkflowStage.COMPLETED)
            
            result = self.state_manager.get_state()["outputs"]
            print(f"\n✅ 工作流执行成功!")
            return result
            
        except Exception as e:
            print(f"\n❌ 工作流执行失败: {str(e)}")
            self.state_manager.add_validation_result(
                "workflow_exception", False, f"Exception: {str(e)}"
            )
            raise
    
    def _plan_phase(self, inputs: Dict[str, Any]):
        """PLAN阶段"""
        print("\n📋 === 阶段 1/4: PLAN (规划) ===")
        self.state_manager.transition_stage(WorkflowStage.PLAN)
        
        # 1. 验证输入
        for policy in self.policies:
            if hasattr(policy, 'validate_input'):
                result = policy.validate_input(inputs)
                self.state_manager.add_validation_result(
                    f"input_{policy.name}",
                    result.passed,
                    result.details
                )
        
        # 2. 更新状态
        self.state_manager.update_context("inputs", inputs)
        print("   ✓ 输入验证完成")
    
    def _build_phase(self, inputs: Dict[str, Any]):
        """BUILD阶段"""
        print("\n🔨 === 阶段 2/4: BUILD (构建) ===")
        self.state_manager.transition_stage(WorkflowStage.BUILD)
        
        # 执行技能链
        for skill_name, skill in self.skills.items():
            print(f"\n   执行技能: {skill_name}")
            
            try:
                skill_inputs = self._prepare_skill_inputs(skill_name, inputs)
                result = skill.execute(skill_inputs)
                
                # 只保存数据，不是整个SkillResult对象
                output_data = {
                    "success": result.success,
                    "data": result.data,
                    "message": result.message
                }
                self.state_manager.update_output(skill_name, output_data)
                
                if result.success:
                    print(f"   ✓ 技能 {skill_name} 执行完成: {result.message}")
                else:
                    print(f"   ⚠️ 技能 {skill_name}: {result.message}")
                
            except Exception as e:
                print(f"   ✗ 技能 {skill_name} 执行失败: {e}")
                raise
    
    def _verify_phase(self):
        """VERIFY阶段"""
        print("\n🔍 === 阶段 3/4: VERIFY (验证) ===")
        self.state_manager.transition_stage(WorkflowStage.VERIFY)
        
        outputs = self.state_manager.get_state()["outputs"]
        
        # 应用所有验证策略
        for policy in self.policies:
            if hasattr(policy, 'validate_output'):
                result = policy.validate_output(outputs)
                self.state_manager.add_validation_result(
                    f"output_{policy.name}",
                    result.passed,
                    result.details
                )
                status = "✅" if result.passed else "❌"
                print(f"   {status} {policy.name}: {result.details}")
    
    def _fix_phase(self):
        """FIX阶段"""
        print("\n🔧 === 阶段 4/4: FIX (修复) ===")
        self.state_manager.transition_stage(WorkflowStage.FIX)
        
        failed_tests = self.state_manager.get_failed_validations()
        print(f"   需要修复: {len(failed_tests)} 项")
        
        # 这里可以添加自动修复逻辑
        for failed in failed_tests:
            print(f"   - {failed['check_name']}: {failed['details']}")
    
    def _prepare_skill_inputs(self, skill_name: str, global_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """为技能准备输入"""
        state = self.state_manager.get_state()
        previous_outputs = state["outputs"]
        
        skill_inputs = {
            **global_inputs,
            **previous_outputs,
            "context": self.context_engine.get_core_context()
        }
        return skill_inputs
