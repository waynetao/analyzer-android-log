#!/usr/bin/env python3
"""
Android 日志分析 AI Agent - 统一 CLI 入口
支持完整工作流、分阶段执行、独立技能调用、状态管理等功能
"""
# 重要：必须在所有 import 之前设置路径
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# 加载 .env 文件（从项目根目录加载）
from dotenv import load_dotenv
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path, override=True)
print(f"📄 从 {dotenv_path} 加载 .env 文件")

import argparse
import json
from datetime import datetime

# 导入日志系统
from harness.core.logging import get_logger
from harness.core.paths import OUTPUTS_REPORTS_DIR_STR, OUTPUTS_STATE_DIR_STR
logger = get_logger(__name__)

# 导入Harness系统
from harness.core import ContextEngine, StateManager, Orchestrator
from harness.core.feature_flags import FeatureSDK
from harness.core.analytics import get_analytics_collector
from harness.skills import LogExtractionSkill, BugAnalysisSkill, ReportGenerationSkill
from harness.policies import ValidationPolicy, QualityPolicy, FormatPolicy

# 导入新的高级技能
from harness.skills.log_analysis_advanced import AdvancedLogAnalysisSkill
from harness.skills.llm_analysis import LLMAnalysisSkill
from harness.skills.log_extraction_aloggrep import LogExtractionWithAloggrepSkill, ALogGrepAnalysisSkill, ALogGrepFilterSkill
from harness.skills.log_evidence_matcher import LogEvidenceMatcherSkill, TimelineBuilderSkill
from harness.skills.knowledge_retrieval import KnowledgeRetrievalSkill
from harness.skills.bug_type_analysis_skill import BugTypeAnalysisSkill
from harness.skills.case_library_skill import CaseLibrarySkill
from harness.skills.log_file_selector import LogFileSelectorSkill


class UnifiedAgent:
    """统一的Agent类，支持分阶段执行和独立技能调用"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        print("="*60)
        print("Android 日志分析 AI Agent - 统一 CLI (Harness Engineering)")
        print("="*60)
        logger.info("Unified Agent 启动")
        
        # 初始化 Feature Flag SDK
        self.feature_sdk = FeatureSDK()
        print(f"📦 已加载 {len(self.feature_sdk.get_all_flags())} 个 Feature Flags")
        logger.info(f"Feature Flags 加载完成: {len(self.feature_sdk.get_all_flags())} 个")
        
        # 初始化核心组件
        self.context_engine = ContextEngine()
        self.state_manager = StateManager()
        self.orchestrator = Orchestrator(self.context_engine, self.state_manager)
        logger.info("核心组件初始化完成")
        
        # 初始化高级技能
        self.llm_skill = LLMAnalysisSkill(api_key, base_url, model)
        
        # 初始化记忆系统
        self.case_library = None
        if self.feature_sdk.is_enabled("memory_system_enabled"):
            memory_mode = self.feature_sdk.get_variant("memory_mode")
            if memory_mode == "openviking":
                self.case_library = self._init_openviking_skill()
            else:
                self.case_library = CaseLibrarySkill()
                print(f"✅ 使用 simple 模式记忆系统")
                logger.info("记忆系统: simple 模式")
        
        # 注册技能
        self._register_skills()
        
        # 注册策略
        self._register_policies()
    
    def _init_openviking_skill(self):
        """初始化 OpenViking 模式"""
        try:
            from harness.skills.openviking_memory_skill import OpenVikingMemorySkill
            skill = OpenVikingMemorySkill()
            if skill.is_available:
                print("✅ 使用 OpenViking 模式记忆系统")
                return skill
            else:
                print("⚠️  OpenViking 不可用，回退到 simple 模式")
                return CaseLibrarySkill()
        except Exception as e:
            print(f"⚠️  OpenViking 初始化失败 ({str(e)})，使用 simple 模式")
            return CaseLibrarySkill()
    
    def _register_skills(self):
        """根据 Feature Flag 注册可插拔技能"""
        print("\n🔧 注册技能（基于 Feature Flag）:")
        
        # 基础技能（始终注册）
        self.orchestrator.register_skill(LogExtractionSkill())
        print("  ✅ LogExtractionSkill (基础技能)")
        
        # LLM 智能文件筛选（在 log_extraction 之后执行）
        if self.feature_sdk.is_enabled("llm_analysis_enabled"):
            self.orchestrator.register_skill(LogFileSelectorSkill(
                api_key=self.llm_skill.api_key,
                base_url=self.llm_skill.base_url,
                model=self.llm_skill.model
            ))
            print("  ✅ LogFileSelectorSkill (LLM 智能筛选)")
        else:
            print("  ⏭️ LogFileSelectorSkill (LLM 未启用，使用规则筛选)")
        
        self.orchestrator.register_skill(AdvancedLogAnalysisSkill())
        print("  ✅ AdvancedLogAnalysisSkill (基础技能)")
        
        # 条件注册：aloggrep 集成
        if self.feature_sdk.is_enabled("aloggrep_integration"):
            self.orchestrator.register_skill(LogExtractionWithAloggrepSkill())
            self.orchestrator.register_skill(ALogGrepAnalysisSkill())
            self.orchestrator.register_skill(ALogGrepFilterSkill())
            print("  ✅ LogExtractionWithAloggrepSkill (已启用)")
            print("  ✅ ALogGrepAnalysisSkill (已启用)")
            print("  ✅ ALogGrepFilterSkill (已启用)")
        else:
            print("  ⏭️ LogExtractionWithAloggrepSkill (已禁用)")
            print("  ⏭️ ALogGrepAnalysisSkill (已禁用)")
            print("  ⏭️ ALogGrepFilterSkill (已禁用)")
        
        # 条件注册：知识库检索
        if self.feature_sdk.is_enabled("knowledge_base_enabled"):
            self.orchestrator.register_skill(KnowledgeRetrievalSkill())
            print("  ✅ KnowledgeRetrievalSkill (已启用)")
        else:
            print("  ⏭️ KnowledgeRetrievalSkill (已禁用)")
        
        # 条件注册：Bug 类型差异化优化
        if self.feature_sdk.is_enabled("bug_type_optimization_enabled"):
            self.orchestrator.register_skill(BugTypeAnalysisSkill())
            print("  ✅ BugTypeAnalysisSkill (已启用)")
        else:
            print("  ⏭️ BugTypeAnalysisSkill (已禁用)")
        
        # 显示记忆系统状态
        if self.feature_sdk.is_enabled("memory_system_enabled") and self.case_library:
            memory_mode = self.feature_sdk.get_variant("memory_mode")
            print(f"  ✅ 记忆系统: {memory_mode} 模式")
        
        # 条件注册：LLM 分析
        if self.feature_sdk.is_enabled("llm_analysis_enabled"):
            self.orchestrator.register_skill(self.llm_skill)
            print("  ✅ LLMAnalysisSkill (已启用)")
        else:
            print("  ⏭️ LLMAnalysisSkill (已禁用)")
        
        # 条件注册：证据匹配
        if self.feature_sdk.is_enabled("evidence_matching_enabled"):
            self.orchestrator.register_skill(LogEvidenceMatcherSkill(self.llm_skill.api_key, self.llm_skill.base_url, self.llm_skill.model))
            self.orchestrator.register_skill(TimelineBuilderSkill())
            print("  ✅ LogEvidenceMatcherSkill (已启用)")
            print("  ✅ TimelineBuilderSkill (已启用)")
        else:
            print("  ⏭️ LogEvidenceMatcherSkill (已禁用)")
            print("  ⏭️ TimelineBuilderSkill (已禁用)")
        
        # 报告生成（始终注册）
        self.orchestrator.register_skill(ReportGenerationSkill())
        print("  ✅ ReportGenerationSkill (基础技能)")
    
    def _register_policies(self):
        """注册策略"""
        self.orchestrator.register_policy(ValidationPolicy())
        self.orchestrator.register_policy(QualityPolicy())
        self.orchestrator.register_policy(FormatPolicy())
    
    def _parse_bug_description(self, bug_text: str):
        """解析bug描述"""
        desc = {
            "raw_text": bug_text,
            "summary": bug_text[:100] + "..." if len(bug_text) > 100 else bug_text,
            "keywords": []
        }
        
        if "crash" in bug_text.lower() or "崩溃" in bug_text:
            desc["keywords"].append("crash")
        if "anr" in bug_text.lower() or "无响应" in bug_text:
            desc["keywords"].append("anr")
        
        return desc
    
    def get_available_skills(self) -> list:
        """获取所有可用的技能名称"""
        return list(self.orchestrator.skills.keys())
    
    def full_analysis(self, bug_text: str, log_path: str, output_format: str = "markdown"):
        """完整的bug分析工作流"""
        # 获取分析模式
        analysis_mode = self.feature_sdk.get_variant("analysis_mode")
        print(f"\n🎯 分析模式: {analysis_mode}")
        
        print(f"\n📝 解析bug描述...")
        
        # 解析bug描述
        bug_desc = self._parse_bug_description(bug_text)
        
        # 准备输入
        inputs = {
            "bug_description": bug_desc,
            "log_path": log_path,
            "output_format": output_format,
            "analysis_mode": analysis_mode
        }
        
        # --- 记忆系统：检索相似案例
        similar_cases = None
        if self.case_library and self.feature_sdk.is_enabled("similar_case_retrieval"):
            print(f"\n🔍 记忆系统：检索相似案例...")
            search_result = self.case_library.execute({
                "action": "search_similar",
                "query": bug_text,
                "bug_type": None,
                "top_k": 3
            })
            
            if search_result.success:
                similar_cases = search_result.data.get("results", [])
                if similar_cases:
                    print(f"✅ 找到 {len(similar_cases)} 个相似案例")
                    # 将相似案例添加到输入中
                    inputs["similar_cases"] = similar_cases
                else:
                    print("ℹ️  未找到相似案例")
        
        # --- 执行主要工作流
        print(f"\n🚀 启动完整工作流...")
        result = self.orchestrator.execute_workflow("bug_analysis_advanced", inputs)
        
        # --- 记忆系统：保存新案例
        saved_case_id = None
        if self.case_library and self.feature_sdk.is_enabled("auto_save_cases"):
            print(f"\n💾 记忆系统：保存分析案例...")
            
            advanced_analysis = result.get("advanced_log_analysis", {})
            bug_type_analysis = result.get("bug_type_analysis", {})
            llm_analysis = result.get("llm_analysis", {})
            
            l0_summary = bug_desc["summary"]
            l1_overview = {}
            if advanced_analysis:
                data = advanced_analysis.get("data", {})
                l1_overview = {
                    "crash_count": data.get("crashes", 0),
                    "anr_count": data.get("anrs", 0),
                    "low_memory": data.get("low_memory", 0),
                }
            
            bug_type = "unknown"
            if bug_type_analysis:
                bug_type = bug_type_analysis.get("data", {}).get("bug_type", "unknown")
            
            save_result = self.case_library.execute({
                "action": "save_case",
                "bug_summary": bug_desc["summary"],
                "keywords": bug_desc["keywords"],
                "l0_summary": l0_summary,
                "l1_overview": l1_overview,
                "bug_type": bug_type,
                "root_cause": llm_analysis.get("data", {}).get("analysis", "")[:500] if llm_analysis else "",
                "tags": bug_desc["keywords"] + [bug_type] if bug_type else bug_desc["keywords"],
                "device": "",
                "android_version": ""
            })
            
            if save_result.success:
                saved_case_id = save_result.data.get("case_id")
                print(f"✅ 案例已保存: {saved_case_id}")
        
        # 附加结果信息
        if saved_case_id:
            result["saved_case_id"] = saved_case_id
        
        return result
    
    def print_state(self, state: dict):
        """打印工作流状态"""
        print("\n" + "="*60)
        print("📊 当前状态")
        print("="*60)
        print(f"工作流ID: {state.get('workflow_id')}")
        print(f"名称: {state.get('workflow_name')}")
        print(f"当前阶段: {state.get('current_stage')}")
        print(f"已完成阶段: {', '.join(state.get('stages_completed', []))}")
        print(f"验证结果数: {len(state.get('validation_results', []))}")
        print(f"输出数: {len(state.get('outputs', {}))}")


def load_bug_text(path_or_text: str) -> str:
    """加载bug描述，如果是文件则读取内容"""
    if os.path.exists(path_or_text):
        with open(path_or_text, 'r', encoding='utf-8') as f:
            return f.read()
    return path_or_text


def main():
    parser = argparse.ArgumentParser(
        description="Android 日志分析 AI Agent - 统一 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 完整分析
  python scripts/cli.py full --bug bug.txt --log app.log
  
  # 分阶段执行
  python scripts/cli.py plan --bug bug.txt --log app.log
  python scripts/cli.py build --workflow-id <ID>
  python scripts/cli.py verify --workflow-id <ID>
  
  # 从检查点恢复
  python scripts/cli.py resume --workflow-id <ID>
  
  # 执行单独技能
  python scripts/cli.py skill --list
  python scripts/cli.py skill --name log_extraction --log app.log
  
  # 查看状态
  python scripts/cli.py status --workflow-id <ID>
  python scripts/cli.py list
        """
    )
    
    subparsers = parser.add_subparsers(title="命令", dest="command")
    
    _add_full_subparser(subparsers)
    _add_plan_subparser(subparsers)
    _add_build_subparser(subparsers)
    _add_verify_subparser(subparsers)
    _add_fix_subparser(subparsers)
    _add_resume_subparser(subparsers)
    _add_skill_subparser(subparsers)
    _add_status_subparser(subparsers)
    _add_list_subparser(subparsers)
    _add_search_subparser(subparsers)
    _add_info_subparser(subparsers)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    agent = UnifiedAgent(
        api_key=getattr(args, "api_key", None),
        base_url=getattr(args, "base_url", None),
        model=getattr(args, "model", None)
    )
    
    _dispatch_command(args, agent)


def _add_full_subparser(subparsers):
    full_parser = subparsers.add_parser("full", help="执行完整工作流分析")
    full_parser.add_argument("--bug", "-b", required=True, help="Bug描述文本或文件")
    full_parser.add_argument("--log", "-l", required=True, help="日志文件/目录路径")
    full_parser.add_argument("--format", "-f", default="markdown", choices=["markdown", "html", "json", "all"], help="输出格式")
    full_parser.add_argument("--api-key", help="OpenAI API Key")
    full_parser.add_argument("--base-url", help="OpenAI API Base URL")
    full_parser.add_argument("--model", default=None, help="使用的LLM模型（默认读取 .env 配置）")


def _add_plan_subparser(subparsers):
    plan_parser = subparsers.add_parser("plan", help="仅执行 PLAN 阶段（输入验证）")
    plan_parser.add_argument("--bug", "-b", required=True, help="Bug描述文本或文件")
    plan_parser.add_argument("--log", "-l", required=True, help="日志文件/目录路径")
    plan_parser.add_argument("--format", "-f", default="markdown", choices=["markdown", "html", "json", "all"], help="输出格式")
    plan_parser.add_argument("--name", default="bug_analysis", help="工作流名称")
    plan_parser.add_argument("--api-key", help="OpenAI API Key")
    plan_parser.add_argument("--base-url", help="OpenAI API Base URL")
    plan_parser.add_argument("--model", default=None, help="使用的LLM模型（默认读取 .env 配置）")


def _add_build_subparser(subparsers):
    build_parser = subparsers.add_parser("build", help="从当前状态执行 BUILD 阶段")
    build_parser.add_argument("--workflow-id", "-w", required=True, help="工作流ID")


def _add_verify_subparser(subparsers):
    verify_parser = subparsers.add_parser("verify", help="从当前状态执行 VERIFY 阶段")
    verify_parser.add_argument("--workflow-id", "-w", required=True, help="工作流ID")


def _add_fix_subparser(subparsers):
    fix_parser = subparsers.add_parser("fix", help="从当前状态执行 FIX 阶段")
    fix_parser.add_argument("--workflow-id", "-w", required=True, help="工作流ID")


def _add_resume_subparser(subparsers):
    resume_parser = subparsers.add_parser("resume", help="从检查点恢复执行到完成")
    resume_parser.add_argument("--workflow-id", "-w", required=True, help="工作流ID")


def _add_skill_subparser(subparsers):
    skill_parser = subparsers.add_parser("skill", help="技能操作")
    skill_parser.add_argument("--list", action="store_true", help="列出所有可用技能")
    skill_parser.add_argument("--name", help="要执行的技能名称")
    skill_parser.add_argument("--log", help="日志文件路径（技能输入）")
    skill_parser.add_argument("--bug", help="Bug描述（技能输入）")
    skill_parser.add_argument("--input-json", help="技能输入JSON文件或字符串")


def _add_status_subparser(subparsers):
    status_parser = subparsers.add_parser("status", help="查看工作流状态")
    status_parser.add_argument("--workflow-id", "-w", required=True, help="工作流ID")


def _add_list_subparser(subparsers):
    list_parser = subparsers.add_parser("list", help="列出所有工作流")
    list_parser.add_argument("--detailed", "-d", action="store_true", help="显示详细信息")
    list_parser.add_argument("--limit", "-l", type=int, help="限制显示数量")
    list_parser.add_argument("--status", choices=["running", "completed", "failed"], help="按状态过滤")


def _add_search_subparser(subparsers):
    search_parser = subparsers.add_parser("search", help="搜索工作流")
    search_parser.add_argument("keyword", help="搜索关键词")


def _add_info_subparser(subparsers):
    info_parser = subparsers.add_parser("info", help="查看工作流详情")
    info_parser.add_argument("--workflow-id", "-w", required=True, help="工作流ID")


def _dispatch_command(args, agent: UnifiedAgent):
    handlers = {
        "full": _handle_full,
        "plan": _handle_plan,
        "build": _handle_build,
        "verify": _handle_verify,
        "fix": _handle_fix,
        "resume": _handle_resume,
        "skill": _handle_skill,
        "status": _handle_status,
        "list": _handle_list,
        "search": _handle_search,
        "info": _handle_info,
    }
    handler = handlers.get(args.command)
    if handler:
        handler(args, agent)


def _handle_full(args, agent: UnifiedAgent):
    bug_text = load_bug_text(args.bug)
    agent.full_analysis(bug_text, args.log, args.format)
    
    print("\n" + "="*60)
    print("✅ 完整分析完成!")
    print("="*60)
    print(f"报告保存在: {OUTPUTS_REPORTS_DIR_STR}")
    print(f"工作流状态保存在: {OUTPUTS_STATE_DIR_STR}")


def _handle_plan(args, agent: UnifiedAgent):
    bug_text = load_bug_text(args.bug)
    bug_desc = agent._parse_bug_description(bug_text)
    inputs = {
        "bug_description": bug_desc,
        "log_path": args.log,
        "output_format": args.format,
        "analysis_mode": agent.feature_sdk.get_variant("analysis_mode")
    }
    state = agent.orchestrator.plan(args.name, inputs)
    agent.print_state(state)


def _handle_build(args, agent: UnifiedAgent):
    agent.orchestrator.load_workflow(args.workflow_id)
    state = agent.orchestrator.build()
    agent.print_state(state)


def _handle_verify(args, agent: UnifiedAgent):
    agent.orchestrator.load_workflow(args.workflow_id)
    state = agent.orchestrator.verify()
    agent.print_state(state)


def _handle_fix(args, agent: UnifiedAgent):
    agent.orchestrator.load_workflow(args.workflow_id)
    state = agent.orchestrator.fix()
    agent.print_state(state)


def _handle_resume(args, agent: UnifiedAgent):
    agent.orchestrator.load_workflow(args.workflow_id)
    result = agent.orchestrator.resume()
    print("\n✅ 工作流恢复执行完成!")


def _handle_skill(args, agent: UnifiedAgent):
    if args.list:
        print("\n" + "="*60)
        print("🔧 可用技能")
        print("="*60)
        for name in agent.get_available_skills():
            print(f"  - {name}")
        print("\n提示: 使用 `--name <skill-name>` 执行特定技能")
    elif args.name:
        inputs = {}
        if args.log:
            inputs["log_path"] = args.log
        if args.bug:
            inputs["bug_description"] = agent._parse_bug_description(load_bug_text(args.bug))
        if args.input_json:
            if os.path.exists(args.input_json):
                with open(args.input_json, 'r', encoding='utf-8') as f:
                    inputs.update(json.load(f))
            else:
                inputs.update(json.loads(args.input_json))
        
        print(f"\n🔧 执行技能: {args.name}")
        print(f"输入: {inputs}")
        
        result = agent.orchestrator.execute_skill(args.name, inputs)
        
        print(f"\n✅ 技能执行完成!")
        print(f"成功: {result.get('success')}")
        print(f"消息: {result.get('message')}")
        print(f"数据: {json.dumps(result.get('data', {}), ensure_ascii=False, indent=2)[:2000]}")
    else:
        print("⚠️ 请指定 `--list` 列出技能或 `--name <skill-name>` 执行技能")


def _handle_status(args, agent: UnifiedAgent):
    state = agent.orchestrator.load_workflow(args.workflow_id)
    agent.print_state(state)
    print("\n📋 详细验证结果:")
    for vr in state.get("validation_results", []):
        status = "✅" if vr["passed"] else "❌"
        print(f"  {status} {vr['check_name']}: {vr['details']}")


def _handle_list(args, agent: UnifiedAgent):
    # 支持详细列表（使用新索引）
    if hasattr(args, 'detailed') and args.detailed:
        status = getattr(args, 'status', None)
        workflows = agent.state_manager.workflow_index.list_workflows(
            limit=getattr(args, 'limit', None),
            status=status
        )
        print_workflow_list_detailed(workflows)
    else:
        workflows = agent.orchestrator.list_workflows()
        print("\n" + "=" * 60)
        print(f"📋 已保存工作流 ({len(workflows)} 个)")
        print("=" * 60)
        for wf in sorted(workflows):
            print(f"  - {wf}")


def print_workflow_list_detailed(workflows):
    """打印详细的工作流列表"""
    if not workflows:
        print("\n没有找到工作流")
        return
    
    print("\n" + "=" * 100)
    print(f"📋 工作流列表 ({len(workflows)} 个)")
    print("=" * 100)
    
    for i, wf in enumerate(workflows, 1):
        status_icon = {
            "running": "🔄",
            "completed": "✅",
            "failed": "❌"
        }.get(wf.get('status'), "❓")
        
        print(f"\n{i}. {status_icon} {wf.get('workflow_id')}")
        print(f"   名称: {wf.get('workflow_name', '')}")
        print(f"   摘要: {wf.get('bug_summary', '')}")
        print(f"   日志: {wf.get('log_path', '')}")
        print(f"   状态: {wf.get('status', '')}")
        print(f"   阶段: {wf.get('current_stage', '')}")
        print(f"   创建: {wf.get('created_at', '')}")
        if wf.get('analysis_mode'):
            print(f"   模式: {wf.get('analysis_mode')}")


def _handle_search(args, agent: UnifiedAgent):
    """搜索工作流"""
    keyword = args.keyword
    workflows = agent.state_manager.workflow_index.search_workflows(keyword)
    print(f"\n🔍 搜索关键词: '{keyword}'")
    print_workflow_list_detailed(workflows)


def _handle_info(args, agent: UnifiedAgent):
    """查看单个工作流详情"""
    workflow_id = args.workflow_id
    workflow = agent.state_manager.workflow_index.get_workflow(workflow_id)
    
    if not workflow:
        print(f"\n❌ 未找到工作流: {workflow_id}")
        return
    
    print("\n" + "=" * 100)
    print(f"📋 工作流详情")
    print("=" * 100)
    print(f"\nID:        {workflow.get('workflow_id')}")
    print(f"名称:      {workflow.get('workflow_name')}")
    print(f"状态:      {workflow.get('status')}")
    print(f"当前阶段:  {workflow.get('current_stage')}")
    print(f"创建时间:  {workflow.get('created_at')}")
    if 'updated_at' in workflow:
        print(f"更新时间:  {workflow.get('updated_at')}")
    print(f"\nBug 摘要:  {workflow.get('bug_summary')}")
    print(f"\nBug 描述:  {workflow.get('bug_description')}")
    print(f"\n日志路径:  {workflow.get('log_path')}")
    if workflow.get('output_format'):
        print(f"输出格式:  {workflow.get('output_format')}")
    if workflow.get('analysis_mode'):
        print(f"分析模式:  {workflow.get('analysis_mode')}")
    if workflow.get('tags'):
        print(f"标签:      {', '.join(workflow.get('tags'))}")
    if workflow.get('notes'):
        print(f"\n备注:      {workflow.get('notes')}")
    print("")


if __name__ == "__main__":
    main()
