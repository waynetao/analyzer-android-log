#!/usr/bin/env python3
"""
Harness Android Log Analysis Agent - Advanced Version
高质量、精准的分析，有日志证据支撑
集成记忆系统（支持 simple 和 openviking 模式无缝切换
"""
# 重要：必须在所有 import 之前设置路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入Harness系统
from harness.core import ContextEngine, StateManager, Orchestrator
from harness.core.feature_flags import FeatureSDK
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


class AdvancedAndroidLogAgent:
    """高级Android日志分析Agent"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        print("="*60)
        print("Android 日志分析 AI Agent - 高级版 (Harness Engineering)")
        print("="*60)
        
        # 初始化 Feature Flag SDK
        self.feature_sdk = FeatureSDK()
        print(f"📦 已加载 {len(self.feature_sdk.get_all_flags())} 个 Feature Flags")
        
        # 初始化核心组件
        self.context_engine = ContextEngine()
        self.state_manager = StateManager()
        self.orchestrator = Orchestrator(self.context_engine, self.state_manager)
        
        # 初始化高级技能
        self.llm_skill = LLMAnalysisSkill(api_key, base_url, model)
        
        # 初始化记忆系统（根据 memory_mode Flag 选择）
        self.case_library = None
        if self.feature_sdk.is_enabled("memory_system_enabled"):
            memory_mode = self.feature_sdk.get_variant("memory_mode")
            if memory_mode == "openviking":
                self.case_library = self._init_openviking_skill()
            else:
                self.case_library = CaseLibrarySkill()
                print(f"✅ 使用 simple 模式记忆系统")
        
        # 注册技能（基于 Feature Flag）
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
        
        # 条件注册：Bug 类型差异化优化（必须在 LLM 分析之前）
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
    
    def _generate_l0_l1_summaries(self, bug_desc, advanced_analysis):
        """从分析结果中生成L0和L1摘要"""
        # L0 摘要（一句话）
        l0_summary = bug_desc["summary"]
        
        # L1 概览（结构化）
        l1_overview = {}
        if advanced_analysis:
            data = advanced_analysis.get("data", {})
            l1_overview = {
                "crash_count": data.get("crashes", 0),
                "anr_count": data.get("anrs", 0),
                "low_memory": data.get("low_memory", 0),
                "critical_logs_count": len(data.get("critical_logs", [])),
            }
        
        return l0_summary, l1_overview
    
    def process_bug(self, bug_text: str, log_path: str, output_format: str = "markdown"):
        """处理bug的完整工作流"""
        # 获取分析模式
        analysis_mode = self.feature_sdk.get_variant("analysis_mode")
        print(f"\n🎯 分析模式: {analysis_mode}")
        
        print(f"\n📝 解析bug描述...")
        
        # 解析bug描述
        bug_desc = self._parse_bug_description(bug_text)
        
        # 准备输入（包含分析模式）
        inputs = {
            "bug_description": bug_desc,
            "log_path": log_path,
            "output_format": output_format,
            "analysis_mode": analysis_mode
        }
        
        # 根据模式调整日志级别和输出详细程度
        if analysis_mode == "fast":
            print("💨 快速模式：跳过部分耗时分析步骤")
        elif analysis_mode == "deep":
            print("🔍 深度模式：执行完整分析流程")
        else:
            print("⚡ 标准模式：平衡速度和深度")
        
        # --- 记忆系统：检索相似案例（在主要工作流之前）
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
                    for i, case in enumerate(similar_cases, 1):
                        case_id = case.get("case_id", f"案例{i}")
                        bug_type = case.get("analysis", {}).get("bug_type", "unknown")
                        print(f"    - {case_id}")
                    # 将相似案例添加到输入中
                    inputs["similar_cases"] = similar_cases
                else:
                    print("ℹ️  未找到相似案例")
        
        # 获取统计信息（可选）
        if self.case_library:
            stats_result = self.case_library.execute({
                "action": "get_statistics"
            })
            if stats_result.success:
                total = stats_result.data.get("total_cases", 0)
                print(f"📊 记忆库统计: {total} 个案例")
        
        # --- 执行主要工作流
        print(f"\n🚀 启动Harness工作流...")
        result = self.orchestrator.execute_workflow("bug_analysis_advanced", inputs)
        
        # --- 记忆系统：保存新案例（在主要工作流之后）
        saved_case_id = None
        if self.case_library and self.feature_sdk.is_enabled("auto_save_cases"):
            print(f"\n💾 记忆系统：保存分析案例...")
            
            # 从结果中提取分析数据
            advanced_analysis = result.get("advanced_log_analysis", {})
            bug_type_analysis = result.get("bug_type_analysis", {})
            llm_analysis = result.get("llm_analysis", {})
            
            # 生成 L0/L1 摘要
            l0_summary, l1_overview = self._generate_l0_l1_summaries(bug_desc, advanced_analysis)
            
            # 提取 Bug 类型
            bug_type = "unknown"
            if bug_type_analysis:
                bug_type = bug_type_analysis.get("data", {}).get("bug_type", "unknown")
            
            # 保存案例
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
                print(f"✅ 案例已保存")
            else:
                print(f"⚠️  案例保存失败: {save_result.message}")
        
        # 附加结果信息
        if saved_case_id:
            result["saved_case_id"] = saved_case_id
        
        return result


def main():
    parser = argparse.ArgumentParser(
        description="Android 日志分析 AI Agent - 高级版"
    )
    parser.add_argument(
        "--bug", "-b", required=True,
        help="Bug描述文本或文件"
    )
    parser.add_argument(
        "--log", "-l", dest="log_path", required=True,
        help="日志文件/目录路径"
    )
    parser.add_argument(
        "--format", "-f", default="markdown",
        choices=["markdown", "html", "json", "all"],
        help="输出格式"
    )
    parser.add_argument(
        "--api-key", help="OpenAI API Key"
    )
    parser.add_argument(
        "--base-url", help="OpenAI API Base URL"
    )
    parser.add_argument(
        "--model", default="gpt-4o-mini",
        help="使用的LLM模型"
    )
    parser.add_argument(
        "--list-cases", action="store_true",
        help="列出所有案例（不进行分析）"
    )
    parser.add_argument(
        "--memory-mode", choices=["simple", "openviking"],
        help="强制使用指定的记忆系统模式（覆盖Feature Flag）"
    )
    
    args = parser.parse_args()
    
    # 如果用户只是想查看案例列表
    if args.list_cases:
        print("📋 案例库统计...")
        # 根据模式选择 Skill
        if args.memory_mode == "openviking":
            from harness.skills.openviking_memory_skill import OpenVikingMemorySkill
            case_library = OpenVikingMemorySkill()
        else:
            case_library = CaseLibrarySkill()
        stats = case_library.execute({"action": "get_statistics"})
        if stats.success:
            print(f"总案例数: {stats.data.get('total_cases', '未知')}")
            if 'bug_type_distribution' in stats.data:
                print(f"Bug类型分布: {stats.data.get('bug_type_distribution')}")
        return
    
    # 读取bug描述
    bug_text = args.bug
    if os.path.exists(args.bug):
        with open(args.bug, 'r', encoding='utf-8') as f:
            bug_text = f.read()
    
    # 运行Agent
    agent = AdvancedAndroidLogAgent(
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model
    )
    
    agent.process_bug(
        bug_text=bug_text,
        log_path=args.log_path,
        output_format=args.format
    )
    
    # 输出结果
    print("\n" + "="*60)
    print("✅ 处理完成!")
    print("="*60)
    print("报告保存在: /workspace/outputs/reports/")
    print("工作流状态保存在: /workspace/outputs/state/")


if __name__ == "__main__":
    main()
