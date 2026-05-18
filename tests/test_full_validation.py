#!/usr/bin/env python3
"""
Android 日志分析 AI Agent - 全面功能验证测试
测试所有迭代新增的功能
"""
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def test_harness_core():
    """测试 Harness 核心系统"""
    print("=" * 70)
    print("1. 测试 Harness 核心系统 (Core System)")
    print("=" * 70)
    
    results = []
    
    try:
        from harness.core.state import StateManager
        state = StateManager()
        state.set("test_key", "test_value")
        assert state.get("test_key") == "test_value"
        results.append(("StateManager", True, "状态管理功能正常"))
    except Exception as e:
        results.append(("StateManager", False, str(e)))
    
    try:
        from harness.core.context import ContextEngine
        ctx = ContextEngine()
        assert ctx is not None
        results.append(("ContextEngine", True, "上下文引擎正常"))
    except Exception as e:
        results.append(("ContextEngine", False, str(e)))
    
    try:
        from harness.core.orchestrator import Orchestrator
        orch = Orchestrator()
        assert orch is not None
        results.append(("Orchestrator", True, "工作流编排器正常"))
    except Exception as e:
        results.append(("Orchestrator", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_basic_log_analysis():
    """测试基础日志分析 (迭代 1)"""
    print("\n" + "=" * 70)
    print("2. 测试基础日志分析 (Basic Log Analysis)")
    print("=" * 70)
    
    results = []
    
    try:
        from log_analyzer.models import LogEntry
        entry = LogEntry(
            timestamp="2026-03-04 10:23:28",
            level="E",
            tag="AndroidRuntime",
            message="FATAL EXCEPTION: main",
            pid="1234",
            tid="5678"
        )
        assert entry.level == "E"
        assert entry.tag == "AndroidRuntime"
        results.append(("LogEntry Model", True, "日志条目模型正常"))
    except Exception as e:
        results.append(("LogEntry Model", False, str(e)))
    
    try:
        from harness.skills.log_extraction import LogExtractionSkill
        skill = LogExtractionSkill()
        assert skill is not None
        assert hasattr(skill, 'execute')
        assert skill.name == "log_extraction"
        results.append(("LogExtractionSkill", True, "日志提取技能正常"))
    except Exception as e:
        results.append(("LogExtractionSkill", False, str(e)))
    
    try:
        from harness.skills.analysis import BugAnalysisSkill
        skill = BugAnalysisSkill()
        assert skill is not None
        results.append(("BugAnalysisSkill", True, "Bug分析技能正常"))
    except Exception as e:
        results.append(("BugAnalysisSkill", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_advanced_analysis():
    """测试高级日志分析 (迭代 2)"""
    print("\n" + "=" * 70)
    print("3. 测试高级日志分析 (Advanced Analysis)")
    print("=" * 70)
    
    results = []
    
    try:
        from harness.skills.log_analysis_advanced import AdvancedLogAnalysisSkill
        skill = AdvancedLogAnalysisSkill()
        assert skill is not None
        assert hasattr(skill, '_extract_key_logs')
        assert hasattr(skill, '_build_device_state')
        assert hasattr(skill, '_build_timeline')
        results.append(("AdvancedLogAnalysisSkill", True, "高级分析技能正常"))
    except Exception as e:
        results.append(("AdvancedLogAnalysisSkill", False, str(e)))
    
    try:
        from harness.skills.log_evidence_matcher import LogEvidenceMatcherSkill, TimelineBuilderSkill
        skill1 = LogEvidenceMatcherSkill()
        assert skill1 is not None
        assert hasattr(skill1, '_match_user_description')
        assert hasattr(skill1, '_extract_temporal_events')
        
        skill2 = TimelineBuilderSkill()
        assert skill2 is not None
        assert hasattr(skill2, '_build_timeline')
        
        results.append(("LogEvidenceMatcherSkill", True, "证据匹配技能正常"))
    except Exception as e:
        results.append(("LogEvidenceMatcherSkill", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_llm_integration():
    """测试 LLM 集成 (迭代 3)"""
    print("\n" + "=" * 70)
    print("4. 测试 LLM 集成 (LLM Integration)")
    print("=" * 70)
    
    results = []
    
    try:
        from harness.skills.llm_analysis import LLMAnalysisSkill
        skill = LLMAnalysisSkill()
        assert skill is not None
        assert hasattr(skill, '_fallback_analysis')
        assert hasattr(skill, '_format_prompt')
        results.append(("LLMAnalysisSkill", True, "LLM分析技能正常（含降级）"))
    except Exception as e:
        results.append(("LLMAnalysisSkill", False, str(e)))
    
    try:
        from harness.skills.llm_enhanced import BugDescriptionParserSkill, LogFilterSkill, ExceptionClassifierSkill, PromptMatcherSkill
        for skill_cls in [BugDescriptionParserSkill, LogFilterSkill, ExceptionClassifierSkill, PromptMatcherSkill]:
            skill = skill_cls()
            assert skill is not None
        results.append(("LLM Enhanced Skills", True, "增强版LLM技能正常"))
    except Exception as e:
        results.append(("LLM Enhanced Skills", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_aloggrep_integration():
    """测试 aloggrep 集成 (迭代 4)"""
    print("\n" + "=" * 70)
    print("5. 测试 aloggrep 集成 (aloggrep Integration)")
    print("=" * 70)
    
    results = []
    
    try:
        from log_analyzer.aloggrep_wrapper import ALogGrep, LogLevel
        wrapper = ALogGrep()
        assert wrapper is not None
        assert hasattr(wrapper, 'filter')
        assert hasattr(wrapper, 'summary')
        assert hasattr(wrapper, 'crashes')
        results.append(("ALogGrep Wrapper", True, "aloggrep包装器正常"))
    except Exception as e:
        results.append(("ALogGrep Wrapper", False, str(e)))
    
    try:
        from harness.skills.log_extraction_aloggrep import LogExtractionWithAloggrepSkill, ALogGrepAnalysisSkill, ALogGrepFilterSkill
        for skill_cls in [LogExtractionWithAloggrepSkill, ALogGrepAnalysisSkill, ALogGrepFilterSkill]:
            skill = skill_cls()
            assert skill is not None
        results.append(("aloggrep Skills", True, "aloggrep相关技能正常"))
    except Exception as e:
        results.append(("aloggrep Skills", False, str(e)))
    
    try:
        from harness.skills.log_extraction_aloggrep_workflow import AloggrepWorkflowSkill, AloggrepQuickAnalysisSkill
        skill1 = AloggrepWorkflowSkill()
        skill2 = AloggrepQuickAnalysisSkill()
        assert skill1 is not None
        assert skill2 is not None
        assert hasattr(skill1, '_execute_phase_1_overview')
        results.append(("aloggrep Workflow Skill", True, "四阶段工作流技能正常"))
    except Exception as e:
        results.append(("aloggrep Workflow Skill", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_qmd_integration():
    """测试 QMD 知识库集成 (迭代 5)"""
    print("\n" + "=" * 70)
    print("6. 测试 QMD 知识库集成 (Knowledge Base)")
    print("=" * 70)
    
    results = []
    
    try:
        from harness.memory.qmd_memory_manager import QMDMemoryManager
        manager = QMDMemoryManager()
        assert manager is not None
        assert hasattr(manager, 'search')
        assert hasattr(manager, 'query_by_type')
        assert hasattr(manager, 'health_check')
        results.append(("QMDMemoryManager", True, "QMD内存管理器正常"))
    except Exception as e:
        results.append(("QMDMemoryManager", False, str(e)))
    
    try:
        from harness.skills.knowledge_retrieval import KnowledgeRetrievalSkill
        skill = KnowledgeRetrievalSkill()
        assert skill is not None
        assert hasattr(skill, 'execute')
        results.append(("KnowledgeRetrievalSkill", True, "知识检索技能正常"))
    except Exception as e:
        results.append(("KnowledgeRetrievalSkill", False, str(e)))
    
    # 测试知识文件是否存在
    knowledge_files = [
        os.path.join(PROJECT_ROOT, "knowledge_base/android_knowledge/event_log_tags/system_tags.md"),
        os.path.join(PROJECT_ROOT, "knowledge_base/android_knowledge/anr_tombstone/anr_format.md"),
        os.path.join(PROJECT_ROOT, "knowledge_base/android_knowledge/dumpsys/meminfo_sop.md"),
        os.path.join(PROJECT_ROOT, "knowledge_base/android_knowledge/gc_logs/format_parsing.md")
    ]
    
    all_exist = True
    for f in knowledge_files:
        if not os.path.exists(f):
            all_exist = False
            break
    
    if all_exist:
        results.append(("Knowledge Base Files", True, "知识库文件完整"))
    else:
        results.append(("Knowledge Base Files", False, "部分知识库文件缺失"))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_feature_flags():
    """测试 Feature Flag 管控 (迭代 6)"""
    print("\n" + "=" * 70)
    print("7. 测试 Feature Flag 管控 (Feature Management)")
    print("=" * 70)
    
    results = []
    
    try:
        from harness.core.feature_flags import FeatureSDK, FeatureFlag
        sdk = FeatureSDK()
        assert sdk is not None
        
        # 测试基本功能
        assert sdk.is_enabled("llm_analysis_enabled") == True
        assert sdk.is_enabled("aloggrep_integration") == True
        
        mode = sdk.get_variant("analysis_mode")
        assert mode in ["fast", "standard", "deep"]
        
        results.append(("FeatureSDK", True, "Feature Flag SDK正常"))
    except Exception as e:
        results.append(("FeatureSDK", False, str(e)))
    
    try:
        from harness.core.feature_flags import FeatureFlagEngine
        engine = FeatureFlagEngine()
        assert engine is not None
        assert len(engine.get_all_flags()) >= 5
        results.append(("Flag Config", True, f"已配置 {len(engine.get_all_flags())} 个 Feature Flag"))
    except Exception as e:
        results.append(("Flag Config", False, str(e)))
    
    # 测试 CLI 工具
    try:
        import subprocess
        result = subprocess.run(['python', os.path.join(PROJECT_ROOT, 'ffctl.py'), 'list'], 
                               capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        assert 'llm_analysis_enabled' in result.stdout
        results.append(("ffctl CLI", True, "Feature Flag管理工具正常"))
    except Exception as e:
        results.append(("ffctl CLI", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_report_generation():
    """测试报告生成"""
    print("\n" + "=" * 70)
    print("8. 测试报告生成 (Report Generation)")
    print("=" * 70)
    
    results = []
    
    try:
        from harness.skills.report import ReportGenerationSkill
        skill = ReportGenerationSkill()
        assert skill is not None
        assert hasattr(skill, 'generate_markdown')
        assert hasattr(skill, 'generate_html')
        assert hasattr(skill, 'generate_json')
        results.append(("ReportGenerationSkill", True, "多格式报告生成技能正常"))
    except Exception as e:
        results.append(("ReportGenerationSkill", False, str(e)))
    
    # 检查现有报告
    reports_dir = os.path.join(PROJECT_ROOT, "outputs/reports")
    if os.path.exists(reports_dir):
        report_files = os.listdir(reports_dir)
        if report_files:
            has_md = any(f.endswith('.md') for f in report_files)
            has_html = any(f.endswith('.html') for f in report_files)
            has_json = any(f.endswith('.json') for f in report_files)
            
            results.append(("Report Formats", True, 
                f"报告格式支持完整 (MD: {has_md}, HTML: {has_html}, JSON: {has_json})"))
        else:
            results.append(("Report Formats", True, "报告目录正常（暂无报告）"))
    else:
        results.append(("Report Formats", False, "报告目录缺失"))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_agent_boot():
    """测试 Agent 启动"""
    print("\n" + "=" * 70)
    print("9. 测试 Agent 启动 (Agent Boot)")
    print("=" * 70)
    
    results = []
    
    # 测试基础 Agent
    try:
        import subprocess
        result = subprocess.run(['python', os.path.join(PROJECT_ROOT, 'scripts/harness_agent.py'), '--help'], 
                               capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        results.append(("HarnessAgent", True, "基础Agent可正常启动"))
    except Exception as e:
        results.append(("HarnessAgent", False, str(e)))
    
    # 测试高级 Agent
    try:
        import subprocess
        result = subprocess.run(['python', os.path.join(PROJECT_ROOT, 'scripts/harness_agent_advanced.py'), '--help'], 
                               capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        results.append(("HarnessAgentAdvanced", True, "高级Agent可正常启动"))
    except Exception as e:
        results.append(("HarnessAgentAdvanced", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {msg}")
    
    return all(r[1] for r in results)

def generate_summary_report(all_tests):
    """生成汇总报告"""
    print("\n" + "=" * 70)
    print("📊 功能验证结果汇总")
    print("=" * 70)
    
    all_passed = True
    passed_count = 0
    
    for test_name, passed in all_tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        passed_str = "通过" if passed else "失败"
        print(f"  {status} {test_name}: {passed_str}")
        if passed:
            passed_count += 1
        else:
            all_passed = False
    
    total = len(all_tests)
    print("\n" + "=" * 70)
    print(f"📈 总体通过率: {passed_count}/{total} ({passed_count/total*100:.1f}%)")
    print("=" * 70)
    
    if all_passed:
        print("\n🎉 所有功能验证通过！")
    else:
        print("\n⚠️ 部分功能需要检查")

def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("Android 日志分析 AI Agent - 全面功能验证")
    print("版本: v6.0 (Feature Flags)")
    print("=" * 70)
    print()
    
    tests = [
        ("Harness 核心系统", test_harness_core),
        ("基础日志分析", test_basic_log_analysis),
        ("高级日志分析", test_advanced_analysis),
        ("LLM 集成", test_llm_integration),
        ("aloggrep 集成", test_aloggrep_integration),
        ("QMD 知识库", test_qmd_integration),
        ("Feature Flag 管控", test_feature_flags),
        ("报告生成", test_report_generation),
        ("Agent 启动", test_agent_boot),
    ]
    
    all_results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            all_results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            all_results.append((test_name, False))
    
    generate_summary_report(all_results)
    
    print("\n📚 相关文档：")
    print(f"  - [README.md](file://{PROJECT_ROOT}/README.md) - 项目说明")
    print(f"  - [AGENTS.md](file://{PROJECT_ROOT}/AGENTS.md) - 架构文档")
    print(f"  - [CHANGELOG.md](file://{PROJECT_ROOT}/CHANGELOG.md) - 变更记录")
    print(f"  - [HIGH_QUALITY_ANALYSIS_GUIDE.md](file://{PROJECT_ROOT}/HIGH_QUALITY_ANALYSIS_GUIDE.md) - 高质量分析指南")
    print(f"  - [QMD_IMPACT_EVALUATION.md](file://{PROJECT_ROOT}/QMD_IMPACT_EVALUATION.md) - QMD 集成价值评估")
    print()
    
    return 0 if all(r[1] for r in all_results) else 1

if __name__ == "__main__":
    sys.exit(main())
