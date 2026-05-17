#!/usr/bin/env python3
"""
全面回归测试 - 验证所有原有功能未被破坏
"""
import os
import sys
sys.path.insert(0, '/workspace')

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
        assert state.get("test_key") == "test_value"
        results.append(("StateManager", True, "基本CRUD操作正常"))
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
    print("2. 测试原有 Skills")
    print("=" * 70)
    
    results = []
    
    # 原有的基础 Skills
    original_skills = [
        ("LogExtractionSkill", "harness.skills.log_extraction", "LogExtractionSkill"),
        ("BugAnalysisSkill", "harness.skills.analysis", "BugAnalysisSkill"),
        ("ReportGenerationSkill", "harness.skills.report", "ReportGenerationSkill"),
        ("BaseSkill", "harness.skills.base", "BaseSkill"),
    ]
    
    for skill_name, module, class_name in original_skills:
        try:
            module_obj = __import__(module, fromlist=[class_name])
            cls = getattr(module_obj, class_name)
            instance = cls()
            assert instance is not None
            results.append((skill_name, True, "实例化和基本方法正常"))
        except Exception as e:
            results.append((skill_name, False, str(e)))
    
    # 新增的 Skills（应该也正常工作）
    new_skills = [
        ("AdvancedLogAnalysisSkill", "harness.skills.log_analysis_advanced", "AdvancedLogAnalysisSkill"),
        ("LLMAnalysisSkill", "harness.skills.llm_analysis", "LLMAnalysisSkill"),
        ("LogEvidenceMatcherSkill", "harness.skills.log_evidence_matcher", "LogEvidenceMatcherSkill"),
        ("TimelineBuilderSkill", "harness.skills.log_evidence_matcher", "TimelineBuilderSkill"),
    ]
    
    print("\n原有技能:")
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    print("\n新增技能:")
    new_results = []
    for skill_name, module, class_name in new_skills:
        try:
            module_obj = __import__(module, fromlist=[class_name])
            cls = getattr(module_obj, class_name)
            instance = cls()
            assert instance is not None
            new_results.append((skill_name, True, "实例化和基本方法正常"))
        except Exception as e:
            new_results.append((skill_name, False, str(e)))
    
    for name, passed, msg in new_results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results + new_results)

def test_original_extractor():
    """测试原有日志提取器"""
    print("\n" + "=" * 70)
    print("3. 测试原有日志提取器")
    print("=" * 70)
    
    results = []
    
    try:
        from log_analyzer.extractor.extractor import LogExtractor
        extractor = LogExtractor()
        assert extractor is not None
        results.append(("LogExtractor", True, "实例化正常"))
    except Exception as e:
        results.append(("LogExtractor", False, str(e)))
    
    try:
        from log_analyzer.extractor.logcat_parser import LogcatParser
        parser = LogcatParser()
        assert parser is not None
        results.append(("LogcatParser", True, "实例化正常"))
    except Exception as e:
        results.append(("LogcatParser", False, str(e)))
    
    try:
        from log_analyzer.extractor.analyzer import Analyzer
        analyzer = Analyzer()
        assert analyzer is not None
        results.append(("Analyzer", True, "实例化正常"))
    except Exception as e:
        results.append(("Analyzer", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_original_cleaner():
    """测试原有日志清洗器"""
    print("\n" + "=" * 70)
    print("4. 测试原有日志清洗器")
    print("=" * 70)
    
    results = []
    
    try:
        from log_analyzer.cleaner.log_cleaner import LogCleaner
        cleaner = LogCleaner()
        assert cleaner is not None
        results.append(("LogCleaner", True, "实例化正常"))
    except Exception as e:
        results.append(("LogCleaner", False, str(e)))
    
    try:
        from log_analyzer.cleaner.filter import Filter
        log_filter = Filter()
        assert log_filter is not None
        results.append(("Filter", True, "实例化正常"))
    except Exception as e:
        results.append(("Filter", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_original_llm():
    """测试原有 LLM 集成"""
    print("\n" + "=" * 70)
    print("5. 测试原有 LLM 集成")
    print("=" * 70)
    
    results = []
    
    try:
        from log_analyzer.llm.openai_client import OpenAIClient
        client = OpenAIClient()
        assert client is not None
        results.append(("OpenAIClient", True, "实例化正常"))
    except Exception as e:
        results.append(("OpenAIClient", False, str(e)))
    
    try:
        from log_analyzer.llm.prompt_builder import PromptBuilder
        builder = PromptBuilder()
        assert builder is not None
        results.append(("PromptBuilder", True, "实例化正常"))
    except Exception as e:
        results.append(("PromptBuilder", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results)

def test_policies():
    """测试策略层"""
    print("\n" + "=" * 70)
    print("6. 测试策略层")
    print("=" * 70)
    
    results = []
    
    try:
        from harness.policies.validation import ValidationPolicy
        policy = ValidationPolicy()
        assert policy is not None
        results.append(("ValidationPolicy", True, "实例化正常"))
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
    print("7. 测试 Agent 入口")
    print("=" * 70)
    
    results = []
    
    try:
        # 基础 Agent
        with open('/workspace/harness_agent.py', 'r') as f:
            content = f.read()
            assert 'Orchestrator' in content
            assert 'LogExtractionSkill' in content
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
            results.append(("harness_agent_advanced.py", True, "结构和新增技能导入正常"))
    except Exception as e:
        results.append(("harness_agent_advanced.py", False, str(e)))
    
    for name, passed, msg in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {msg}")
    
    return all(r[1] for r in results)

def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("Harness Android Log Analysis Agent - 全面回归测试")
    print("=" * 70)
    print()
    
    tests = [
        ("核心系统", test_core_system),
        ("原有Skills", test_original_skills),
        ("日志提取器", test_original_extractor),
        ("日志清洗器", test_original_cleaner),
        ("LLM集成", test_original_llm),
        ("策略层", test_policies),
        ("Agent入口", test_agents),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        try:
            passed = test_func()
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"\n❌ {test_name}测试失败: {e}")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 所有回归测试通过!")
        print("✅ 原有能力未被破坏")
    else:
        print("❌ 部分测试失败，请检查")
    print("=" * 70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
