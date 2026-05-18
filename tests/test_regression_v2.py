#!/usr/bin/env python3
"""
全面回归测试 v2 - 验证所有原有功能未被破坏
"""
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def test_core_system():
    """测试 Harness 核心系统"""
    print("=" * 70)
    print("1. 测试 Harness 核心系统")
    print("=" * 70)
    
    results = []
    
    try:
        # 测试 StateManager
        from harness.core.state import StateManager
        state = StateManager()
        state.set("test_key", "test_value")
        value = state.get("test_key")
        assert value == "test_value"
        results.append(("StateManager", True, "CRUD操作正常"))
    except Exception as e:
        results.append(("StateManager", False, str(e)))
    
    try:
        # 测试 ContextEngine
        from harness.core.context import ContextEngine
        ctx = ContextEngine()
        assert ctx is not None
        results.append(("ContextEngine", True, "实例化正常"))
    except Exception as e:
        results.append(("ContextEngine", False, str(e)))
    
    try:
        # 测试 Orchestrator
        from harness.core.orchestrator import Orchestrator
        orch = Orchestrator()
        assert orch is not None
        results.append(("Orchestrator", True, "实例化正常"))
    except Exception as e:
        results.append(("Orchestrator", False, str(e)))
    
    # 打印结果
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_original_skills():
    """测试原有的 Skills"""
    print("\n" + "=" * 70)
    print("2. 测试 Skills")
    print("=" * 70)
    
    results = []
    
    # 可实例化的 Skills
    test_cases = [
        ("LogExtractionSkill", "harness.skills.log_extraction", "LogExtractionSkill"),
        ("BugAnalysisSkill", "harness.skills.analysis", "BugAnalysisSkill"),
        ("ReportGenerationSkill", "harness.skills.report", "ReportGenerationSkill"),
        ("AdvancedLogAnalysisSkill", "harness.skills.log_analysis_advanced", "AdvancedLogAnalysisSkill"),
        ("LLMAnalysisSkill", "harness.skills.llm_analysis", "LLMAnalysisSkill"),
        ("LogEvidenceMatcherSkill", "harness.skills.log_evidence_matcher", "LogEvidenceMatcherSkill"),
        ("TimelineBuilderSkill", "harness.skills.log_evidence_matcher", "TimelineBuilderSkill"),
        ("LogExtractionWithAloggrepSkill", "harness.skills.log_extraction_aloggrep", "LogExtractionWithAloggrepSkill"),
        ("ALogGrepAnalysisSkill", "harness.skills.log_extraction_aloggrep", "ALogGrepAnalysisSkill"),
        ("AloggrepWorkflowSkill", "harness.skills.log_extraction_aloggrep_workflow", "AloggrepWorkflowSkill"),
        ("EnhancedReportGenerationSkill", "harness.skills.enhanced_report_generation", "EnhancedReportGenerationSkill"),
    ]
    
    for skill_name, module, class_name in test_cases:
        try:
            module_obj = __import__(module, fromlist=[class_name])
            cls = getattr(module_obj, class_name)
            instance = cls()
            assert instance is not None
            assert hasattr(instance, 'execute')
            assert hasattr(instance, 'name')
            results.append((skill_name, True, "实例化和基本方法正常"))
        except Exception as e:
            results.append((skill_name, False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_original_extractor():
    """测试原有日志提取器"""
    print("\n" + "=" * 70)
    print("3. 测试日志提取器")
    print("=" * 70)
    
    results = []
    
    try:
        from log_analyzer.extractor.extractor import LogExtractor
        extractor = LogExtractor()
        assert extractor is not None
        assert hasattr(extractor, 'extract')
        assert hasattr(extractor, 'find_log_files')
        results.append(("LogExtractor", True, "实例化和基本方法正常"))
    except Exception as e:
        results.append(("LogExtractor", False, str(e)))
    
    try:
        from log_analyzer.log_entry import LogEntry
        entry = LogEntry(
            timestamp="2026-03-04 10:23:28",
            level="E",
            tag="AndroidRuntime",
            message="Test crash"
        )
        assert entry is not None
        assert entry.level == "E"
        results.append(("LogEntry", True, "实例化和基本属性正常"))
    except Exception as e:
        results.append(("LogEntry", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_policies():
    """测试策略层"""
    print("\n" + "=" * 70)
    print("4. 测试策略层")
    print("=" * 70)
    
    results = []
    
    try:
        from harness.policies.validation import ValidationPolicy
        policy = ValidationPolicy()
        assert policy is not None
        assert hasattr(policy, 'validate')
        results.append(("ValidationPolicy", True, "实例化和基本方法正常"))
    except Exception as e:
        results.append(("ValidationPolicy", False, str(e)))
    
    try:
        from harness.policies.quality import QualityPolicy
        policy = QualityPolicy()
        assert policy is not None
        results.append(("QualityPolicy", True, "实例化正常"))
    except Exception as e:
        results.append(("QualityPolicy", False, str(e)))
    
    try:
        from harness.policies.format import FormatPolicy
        policy = FormatPolicy()
        assert policy is not None
        results.append(("FormatPolicy", True, "实例化正常"))
    except Exception as e:
        results.append(("FormatPolicy", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_agents():
    """测试 Agent 入口"""
    print("\n" + "=" * 70)
    print("5. 测试 Agent 入口文件")
    print("=" * 70)
    
    results = []
    
    try:
        # 基础 Agent
        with open(os.path.join(PROJECT_ROOT, 'scripts/harness_agent.py'), 'r') as f:
            content = f.read()
            assert 'Orchestrator' in content
            assert 'LogExtractionSkill' in content
            assert 'BugAnalysisSkill' in content
            assert 'ReportGenerationSkill' in content
            results.append(("harness_agent.py", True, "基本结构和导入正常"))
    except Exception as e:
        results.append(("harness_agent.py", False, str(e)))
    
    try:
        # 高级 Agent
        with open('/workspace/harness_agent_advanced.py', 'r') as f:
            content = f.read()
            assert 'Orchestrator' in content
            assert 'LogExtractionSkill' in content
            assert 'AdvancedLogAnalysisSkill' in content
            assert 'LLMAnalysisSkill' in content
            assert 'LogEvidenceMatcherSkill' in content
            assert 'TimelineBuilderSkill' in content
            assert 'AloggrepWorkflowSkill' in content
            results.append(("harness_agent_advanced.py", True, "结构和所有技能导入正常"))
    except Exception as e:
        results.append(("harness_agent_advanced.py", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_aloggrep_integration():
    """测试 aloggrep 集成"""
    print("\n" + "=" * 70)
    print("6. 测试 aloggrep 集成")
    print("=" * 70)
    
    results = []
    
    try:
        from log_analyzer.aloggrep_wrapper import ALogGrep, LogLevel
        wrapper = ALogGrep()
        assert wrapper is not None
        assert hasattr(wrapper, 'filter')
        assert hasattr(wrapper, 'summary')
        assert hasattr(wrapper, 'crashes')
        results.append(("ALogGrep (基础)", True, "实例化和基本方法正常"))
    except Exception as e:
        results.append(("ALogGrep (基础)", False, str(e)))
    
    try:
        from log_analyzer.alogrep_wrapper_enhanced import ALogGrepEnhanced
        wrapper = ALogGrepEnhanced()
        assert wrapper is not None
        assert hasattr(wrapper, 'parse_histogram_with_anomalies')
        assert hasattr(wrapper, 'comprehensive_analysis')
        results.append(("ALogGrepEnhanced (增强)", True, "实例化和增强方法正常"))
    except Exception as e:
        results.append(("ALogGrepEnhanced (增强)", False, str(e)))
    
    try:
        from log_analyzer.aloggrep_wrapper import LogLevel
        levels = list(LogLevel)
        assert len(levels) == 6
        results.append(("LogLevel 枚举", True, f"包含 {len(levels)} 个级别"))
    except Exception as e:
        results.append(("LogLevel 枚举", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_skill_files():
    """测试 Skill 文件"""
    print("\n" + "=" * 70)
    print("7. 测试 Skill 文件")
    print("=" * 70)
    
    results = []
    
    files_to_check = [
        ("SKILL.md", os.path.join(PROJECT_ROOT, ".claude/skills/loggrep-analyzer/SKILL.md")),
        ("commands.md", os.path.join(PROJECT_ROOT, ".claude/skills/loggrep-analyzer/references/commands.md")),
    ]
    
    for name, path in files_to_check:
        exists = os.path.exists(path)
        if exists:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert len(content) > 100
            results.append((name, True, f"存在且内容完整 ({len(content)} 字符)"))
        else:
            results.append((name, False, "文件不存在"))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results)

def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("Harness Android Log Analysis Agent - 全面回归测试 v2")
    print("=" * 70)
    print()
    
    tests = [
        ("核心系统", test_core_system),
        ("Skills", test_original_skills),
        ("日志提取器", test_original_extractor),
        ("策略层", test_policies),
        ("Agent入口", test_agents),
        ("aloggrep集成", test_aloggrep_integration),
        ("Skill文件", test_skill_files),
    ]
    
    all_passed = True
    test_results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            test_results.append((test_name, passed))
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"\n❌ {test_name}测试异常: {e}")
            test_results.append((test_name, False))
            all_passed = False
    
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    if all_passed:
        print("🎉 所有回归测试通过!")
        print("✅ 原有能力未被破坏，所有新增功能正常")
    else:
        print("❌ 部分测试失败，请检查")
    
    print("=" * 70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
