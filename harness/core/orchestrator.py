"""
Orchestrator - Harness Engineering核心协调器
实现Plan-Build-Verify-Fix工作流，协调整个系统
"""
import sys
import os
import time
from typing import Dict, Any, List, Optional
from .context import ContextEngine
from .state import StateManager, WorkflowStage
from .logging import get_logger
from .analytics import get_analytics_collector

logger = get_logger(__name__)

# 延迟导入以避免循环导入
_BaseSkill = None
_BasePolicy = None

def _get_base_skill():
    """延迟获取 BaseSkill 类"""
    global _BaseSkill
    if _BaseSkill is None:
        from ..skills.base import BaseSkill as _BS
        _BaseSkill = _BS
    return _BaseSkill

def _get_base_policy():
    """延迟获取 BasePolicy 类"""
    global _BasePolicy
    if _BasePolicy is None:
        from ..policies.base import BasePolicy as _BP
        _BasePolicy = _BP
    return _BasePolicy


class Orchestrator:
    def __init__(
        self,
        context_engine: ContextEngine,
        state_manager: StateManager
    ):
        self.context_engine = context_engine
        self.state_manager = state_manager
        self.skills: Dict[str, Any] = {}
        self.policies: List[Any] = []
        self.analytics = get_analytics_collector()
        logger.info("Orchestrator 已初始化")
    
    def register_skill(self, skill: Any):
        """注册技能（可插拔）"""
        self.skills[skill.name] = skill
        print(f"✅ 技能已注册: {skill.name}")
        logger.info(f"技能注册成功: {skill.name} (共 {len(self.skills)} 个技能)")
    
    def register_policy(self, policy: Any):
        """注册策略（约束和验证）"""
        self.policies.append(policy)
        print(f"📋 策略已加载: {policy.name}")
        logger.info(f"策略加载成功: {policy.name}")
    
    def execute_workflow(
        self,
        workflow_name: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行完整工作流（Plan-Build-Verify-Fix）
        """
        print(f"\n🚀 开始执行工作流: {workflow_name}")
        logger.info(f"开始执行工作流: {workflow_name}")
        
        # 启动统计分析
        workflow_id = self.state_manager.initialize_workflow(workflow_name)
        self.analytics.start_workflow(workflow_name)
        print(f"   工作流ID: {workflow_id}")
        logger.info(f"工作流ID: {workflow_id}")
        
        try:
            # 2. PLAN - 规划阶段
            self._plan_phase(inputs)
            
            # 3. BUILD - 构建阶段
            self._build_phase(inputs)
            
            # 4. VERIFY - 验证阶段
            self._verify_phase()
            
            # 5. FIX - 如果需要修复
            if not self.state_manager.is_verification_passed():
                logger.warning("验证未通过，进入修复阶段")
                self._fix_phase()
            else:
                logger.info("验证通过")
            
            # 完成
            self.state_manager.transition_stage(WorkflowStage.COMPLETED)
            self.analytics.end_workflow(status="completed")
            
            result = self.state_manager.get_state()["outputs"]
            print(f"\n✅ 工作流执行成功!")
            logger.info(f"工作流执行成功: {workflow_name}, 输出数量: {len(result)}")
            return result
            
        except Exception as e:
            print(f"\n❌ 工作流执行失败: {str(e)}")
            logger.error(f"工作流执行失败: {workflow_name}, 错误: {str(e)}", exc_info=True)
            self.state_manager.add_validation_result(
                "workflow_exception", False, f"Exception: {str(e)}"
            )
            self.analytics.end_workflow(status="failed", error_message=str(e))
            raise
    
    def _plan_phase(self, inputs: Dict[str, Any]):
        """PLAN阶段"""
        print("\n📋 === 阶段 1/4: PLAN (规划) ===")
        logger.info("开始 PLAN 阶段")
        stage_start_time = time.time()
        self.state_manager.transition_stage(WorkflowStage.PLAN)
        
        # 1. 验证输入
        validation_passed = 0
        validation_failed = 0
        for policy in self.policies:
            if hasattr(policy, 'validate_input'):
                result = policy.validate_input(inputs)
                self.state_manager.add_validation_result(
                    f"input_{policy.name}",
                    result.passed,
                    result.details
                )
                self.analytics.record_validation(result.passed)
                if result.passed:
                    validation_passed += 1
                else:
                    validation_failed += 1
        
        # 2. 更新状态
        self.state_manager.update_context("inputs", inputs)
        print("   ✓ 输入验证完成")
        
        stage_duration_ms = (time.time() - stage_start_time) * 1000
        self.analytics.record_stage_execution(
            stage_name="PLAN",
            success=(validation_failed == 0),
            duration_ms=stage_duration_ms
        )
        logger.info(f"PLAN 阶段完成: 验证通过 {validation_passed}, 失败 {validation_failed}, 耗时: {stage_duration_ms:.2f}ms")
    
    def _build_phase(self, inputs: Dict[str, Any]):
        """BUILD阶段"""
        print("\n🔨 === 阶段 2/4: BUILD (构建) ===")
        logger.info("开始 BUILD 阶段")
        stage_start_time = time.time()
        self.state_manager.transition_stage(WorkflowStage.BUILD)
        
        # 执行技能链
        success_count = 0
        failed_count = 0
        for skill_name, skill in self.skills.items():
            print(f"\n   执行技能: {skill_name}")
            logger.info(f"开始执行技能: {skill_name}")
            
            skill_start_time = time.time()
            
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
                
                skill_duration_ms = (time.time() - skill_start_time) * 1000
                self.analytics.record_skill_execution(
                    skill_name=skill_name,
                    success=result.success,
                    duration_ms=skill_duration_ms
                )
                
                if result.success:
                    print(f"   ✓ 技能 {skill_name} 执行完成: {result.message}")
                    logger.info(f"技能执行成功: {skill_name}, 耗时: {skill_duration_ms:.2f}ms")
                    success_count += 1
                else:
                    print(f"   ⚠️ 技能 {skill_name}: {result.message}")
                    logger.warning(f"技能执行警告: {skill_name} - {result.message}")
                    failed_count += 1
                
            except Exception as e:
                skill_duration_ms = (time.time() - skill_start_time) * 1000
                self.analytics.record_skill_execution(
                    skill_name=skill_name,
                    success=False,
                    duration_ms=skill_duration_ms,
                    error=str(e)
                )
                print(f"   ✗ 技能 {skill_name} 执行失败: {e}")
                logger.error(f"技能执行失败: {skill_name}, 错误: {str(e)}", exc_info=True)
                failed_count += 1
                raise
        
        stage_duration_ms = (time.time() - stage_start_time) * 1000
        self.analytics.record_stage_execution(
            stage_name="BUILD",
            success=True,
            duration_ms=stage_duration_ms
        )
        logger.info(f"BUILD 阶段完成: 成功 {success_count}, 失败 {failed_count}, 耗时: {stage_duration_ms:.2f}ms")
    
    def _verify_phase(self):
        """VERIFY阶段"""
        print("\n🔍 === 阶段 3/4: VERIFY (验证) ===")
        logger.info("开始 VERIFY 阶段")
        stage_start_time = time.time()
        self.state_manager.transition_stage(WorkflowStage.VERIFY)
        
        outputs = self.state_manager.get_state()["outputs"]
        
        # 应用所有验证策略
        passed_count = 0
        failed_count = 0
        for policy in self.policies:
            if hasattr(policy, 'validate_output'):
                result = policy.validate_output(outputs)
                self.state_manager.add_validation_result(
                    f"output_{policy.name}",
                    result.passed,
                    result.details
                )
                self.analytics.record_validation(result.passed)
                status = "✅" if result.passed else "❌"
                print(f"   {status} {policy.name}: {result.details}")
                if result.passed:
                    passed_count += 1
                    logger.info(f"验证通过: {policy.name}")
                else:
                    failed_count += 1
                    logger.warning(f"验证失败: {policy.name} - {result.details}")
        
        stage_duration_ms = (time.time() - stage_start_time) * 1000
        self.analytics.record_stage_execution(
            stage_name="VERIFY",
            success=(failed_count == 0),
            duration_ms=stage_duration_ms
        )
        logger.info(f"VERIFY 阶段完成: 通过 {passed_count}, 失败 {failed_count}, 耗时: {stage_duration_ms:.2f}ms")
    
    def _fix_phase(self):
        """FIX阶段"""
        print("\n🔧 === 阶段 4/4: FIX (修复) ===")
        logger.info("开始 FIX 阶段")
        stage_start_time = time.time()
        self.state_manager.transition_stage(WorkflowStage.FIX)
        
        failed_tests = self.state_manager.get_failed_validations()
        print(f"   需要修复: {len(failed_tests)} 项")
        logger.warning(f"需要修复的项目: {len(failed_tests)}")
        
        # 这里可以添加自动修复逻辑
        for failed in failed_tests:
            print(f"   - {failed['check_name']}: {failed['details']}")
            logger.warning(f"待修复: {failed['check_name']} - {failed['details']}")
        
        stage_duration_ms = (time.time() - stage_start_time) * 1000
        self.analytics.record_stage_execution(
            stage_name="FIX",
            success=True,
            duration_ms=stage_duration_ms
        )
        logger.info(f"FIX 阶段完成, 耗时: {stage_duration_ms:.2f}ms")
    
    def _prepare_skill_inputs(self, skill_name: str, global_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """为技能准备输入"""
        state = self.state_manager.get_state()
        previous_outputs = state["outputs"]
        
        skill_inputs = {
            **global_inputs,
            **previous_outputs,
            "context": self.context_engine.get_core_context()
        }

        # 特定技能的参数映射 - 基于前面技能的输出
        if skill_name == "knowledge_retrieval":
            # 从日志分析结果中提取关键信息作为查询
            advanced_analysis = previous_outputs.get("advanced_log_analysis", {})
            if isinstance(advanced_analysis, dict):
                analysis_data = advanced_analysis.get("data", {})
                if analysis_data:
                    skill_inputs["query"] = analysis_data.get("summary", global_inputs.get("bug_description", {}).get("summary", ""))
                    skill_inputs["bug_type"] = analysis_data.get("bug_type", "unknown")

        elif skill_name == "log_evidence_matcher":
            # 从日志提取结果中获取关键日志
            log_extraction = previous_outputs.get("log_extraction", {})
            advanced_analysis = previous_outputs.get("advanced_log_analysis", {})
            if isinstance(log_extraction, dict) and isinstance(advanced_analysis, dict):
                skill_inputs["critical_logs"] = advanced_analysis.get("data", {}).get("critical_logs", [])

        elif skill_name == "timeline_builder":
            # 从日志提取结果中获取日志条目
            log_extraction = previous_outputs.get("log_extraction", {})
            advanced_analysis = previous_outputs.get("advanced_log_analysis", {})
            if isinstance(log_extraction, dict):
                skill_inputs["log_entries"] = log_extraction.get("data", {}).get("entries", [])
                if not skill_inputs["log_entries"]:
                    skill_inputs["log_entries"] = advanced_analysis.get("data", {}).get("critical_logs", [])

        return skill_inputs

    # ============ 分阶段执行公开 API ============

    def load_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """从保存的状态加载工作流"""
        return self.state_manager.load_state(workflow_id)

    def get_current_state(self) -> Dict[str, Any]:
        """获取当前工作流状态"""
        return self.state_manager.get_state()

    def list_workflows(self) -> List[str]:
        """列出所有已保存的工作流"""
        state_dir = self.state_manager.state_dir
        if not os.path.exists(state_dir):
            return []
        return [f.replace('.json', '') for f in os.listdir(state_dir) if f.endswith('.json')]

    def plan(self, workflow_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """仅执行 PLAN 阶段"""
        workflow_id = self.state_manager.initialize_workflow(workflow_name)
        self.analytics.start_workflow(workflow_name)
        print(f"   工作流ID: {workflow_id}")
        logger.info(f"开始 PLAN 阶段，工作流: {workflow_name}")

        try:
            self._plan_phase(inputs)
            result = self.state_manager.get_state()
            logger.info(f"PLAN 阶段完成，工作流: {workflow_id}")
            return result
        except Exception as e:
            print(f"\n❌ PLAN 阶段失败: {str(e)}")
            logger.error(f"PLAN 阶段失败: {str(e)}", exc_info=True)
            self.state_manager.add_validation_result(
                "plan_exception", False, f"Exception: {str(e)}"
            )
            self.analytics.end_workflow(status="failed", error_message=str(e))
            raise

    def build(self) -> Dict[str, Any]:
        """从当前状态继续执行 BUILD 阶段"""
        state = self.state_manager.get_state()
        inputs = state.get("context", {}).get("inputs", {})

        try:
            self._build_phase(inputs)
            result = self.state_manager.get_state()
            logger.info("BUILD 阶段完成")
            return result
        except Exception as e:
            print(f"\n❌ BUILD 阶段失败: {str(e)}")
            logger.error(f"BUILD 阶段失败: {str(e)}", exc_info=True)
            self.state_manager.add_validation_result(
                "build_exception", False, f"Exception: {str(e)}"
            )
            raise

    def verify(self) -> Dict[str, Any]:
        """从当前状态继续执行 VERIFY 阶段"""
        try:
            self._verify_phase()
            result = self.state_manager.get_state()
            logger.info("VERIFY 阶段完成")
            return result
        except Exception as e:
            print(f"\n❌ VERIFY 阶段失败: {str(e)}")
            logger.error(f"VERIFY 阶段失败: {str(e)}", exc_info=True)
            self.state_manager.add_validation_result(
                "verify_exception", False, f"Exception: {str(e)}"
            )
            raise

    def fix(self) -> Dict[str, Any]:
        """从当前状态继续执行 FIX 阶段"""
        try:
            self._fix_phase()
            self.state_manager.transition_stage(WorkflowStage.COMPLETED)
            self.analytics.end_workflow(status="completed")
            result = self.state_manager.get_state()
            logger.info("FIX 阶段完成")
            print(f"\n✅ 工作流执行完成!")
            return result
        except Exception as e:
            print(f"\n❌ FIX 阶段失败: {str(e)}")
            logger.error(f"FIX 阶段失败: {str(e)}", exc_info=True)
            self.state_manager.add_validation_result(
                "fix_exception", False, f"Exception: {str(e)}"
            )
            self.analytics.end_workflow(status="failed", error_message=str(e))
            raise

    def resume(self) -> Dict[str, Any]:
        """从当前检查点恢复并继续执行到完成"""
        state = self.state_manager.get_state()
        current_stage = state.get("current_stage")
        stages_completed = state.get("stages_completed", [])

        logger.info(f"恢复工作流，当前阶段: {current_stage}，已完成: {stages_completed}")

        inputs = state.get("context", {}).get("inputs", {})

        if current_stage == WorkflowStage.PLAN.value:
            self._plan_phase(inputs)
            if not self.state_manager.is_verification_passed():
                return self.state_manager.get_state()

        if current_stage in [WorkflowStage.PLAN.value, WorkflowStage.BUILD.value]:
            self._build_phase(inputs)

        if current_stage in [WorkflowStage.PLAN.value, WorkflowStage.BUILD.value, WorkflowStage.VERIFY.value]:
            self._verify_phase()

        if not self.state_manager.is_verification_passed():
            self._fix_phase()

        self.state_manager.transition_stage(WorkflowStage.COMPLETED)
        self.analytics.end_workflow(status="completed")
        result = self.state_manager.get_state()["outputs"]
        print(f"\n✅ 工作流恢复执行完成!")
        logger.info(f"工作流恢复完成")
        return result

    def execute_skill(self, skill_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """单独执行指定技能"""
        if skill_name not in self.skills:
            raise ValueError(f"技能 '{skill_name}' 未注册，可用技能: {list(self.skills.keys())}")

        print(f"\n🔧 单独执行技能: {skill_name}")
        logger.info(f"单独执行技能: {skill_name}")

        skill = self.skills[skill_name]
        skill_start_time = time.time()

        try:
            skill_inputs = self._prepare_skill_inputs(skill_name, inputs)
            result = skill.execute(skill_inputs)

            output_data = {
                "success": result.success,
                "data": result.data,
                "message": result.message
            }
            self.state_manager.update_output(skill_name, output_data)

            skill_duration_ms = (time.time() - skill_start_time) * 1000
            self.analytics.record_skill_execution(
                skill_name=skill_name,
                success=result.success,
                duration_ms=skill_duration_ms
            )

            if result.success:
                print(f"   ✓ 技能 {skill_name} 执行完成: {result.message}")
                logger.info(f"技能 {skill_name} 执行成功，耗时: {skill_duration_ms:.2f}ms")
            else:
                print(f"   ⚠️ 技能 {skill_name}: {result.message}")
                logger.warning(f"技能 {skill_name} 执行警告: {result.message}")

            return output_data

        except Exception as e:
            skill_duration_ms = (time.time() - skill_start_time) * 1000
            self.analytics.record_skill_execution(
                skill_name=skill_name,
                success=False,
                duration_ms=skill_duration_ms,
                error=str(e)
            )
            print(f"   ✗ 技能 {skill_name} 执行失败: {e}")
            logger.error(f"技能执行失败: {skill_name}, 错误: {str(e)}", exc_info=True)
            raise

    
