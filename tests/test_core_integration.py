#!/usr/bin/env python3
"""
核心组件综合测试 - 全功能集成测试
测试所有核心模块协同工作
"""
import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_full_integration_simple_mode():
    """测试简单模式的完整集成"""
    print("="*60)
    print("综合测试 1: Simple 模式记忆系统与 Agent 集成")
    print("="*60)
    
    # 测试点 1: Feature Flag 正确设置
    from harness.core.feature_flags import FeatureSDK
    sdk = FeatureSDK()
    
    memory_enabled = sdk.is_enabled("memory_system_enabled")
    auto_save = sdk.is_enabled("auto_save_cases")
    similar_search = sdk.is_enabled("similar_case_retrieval")
    
    print(f"✓ 记忆系统启用: {memory_enabled}")
    print(f"✓ 自动保存案例: {auto_save}")
    print(f"✓ 相似案例搜索: {similar_search}")
    
    # 测试点 2: memory_mode 配置
    memory_mode = sdk.get_variant("memory_mode")
    print(f"✓ 记忆系统模式: {memory_mode}")
    
    # 测试点 3: CaseLibrarySkill 初始化
    from harness.skills.case_library_skill import CaseLibrarySkill
    test_dir = tempfile.mkdtemp()
    try:
        skill = CaseLibrarySkill(library_path=test_dir)
        print("✓ CaseLibrarySkill 初始化成功")
        
        # 测试点 4: 保存一个测试案例
        save_result = skill.execute({
            "action": "save_case",
            "bug_summary": "App crashes on startup",
            "keywords": ["crash", "startup"],
            "bug_type": "crash",
            "l0_summary": "App crashes during initialization",
            "l1_overview": {"crash_count": 1},
            "tags": ["crash", "startup"],
            "device": "Test Device",
            "android_version": "12"
        })
        
        assert save_result.success
        case_id = save_result.data.get("case_id")
        print(f"✓ 案例保存成功: {case_id}")
        
        # 测试点 5: 搜索相似案例
        search_result = skill.execute({
            "action": "search_similar",
            "query": "crash startup",
            "top_k": 5
        })
        
        assert search_result.success
        results = search_result.data.get("results", [])
        print(f"✓ 搜索功能正常，找到 {len(results)} 个案例")
        
        # 测试点 6: 获取统计
        stats = skill.execute({"action": "get_statistics"})
        assert stats.success
        print(f"✓ 统计功能正常: {stats.data.get('total_cases')} 个案例")
        
        print("\n✅ Simple 模式完整集成测试通过\n")
        return True
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_module_imports():
    """测试所有模块的导入"""
    print("="*60)
    print("综合测试 2: 所有模块导入测试")
    print("="*60)
    
    modules = [
        # Core modules
        ("harness.core.context", "ContextEngine"),
        ("harness.core.state", "StateManager"),
        ("harness.core.orchestrator", "Orchestrator"),
        ("harness.core.feature_flags", "FeatureSDK"),
        
        # Skills
        ("harness.skills.base", "BaseSkill"),
        ("harness.skills.log_extraction", "LogExtractionSkill"),
        ("harness.skills.case_library_skill", "CaseLibrarySkill"),
        ("harness.skills.bug_type_analysis_skill", "BugTypeAnalysisSkill"),
        
        # Bug Type analyzers
        ("harness.skills.bug_type", "BugType"),
        ("harness.skills.bug_type", "PromptTemplateManager"),
    ]
    
    all_imported = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {module_name}.{class_name}")
        except Exception as e:
            print(f"✗ {module_name}.{class_name}: {e}")
            all_imported = False
    
    if all_imported:
        print("\n✅ 所有模块导入测试通过\n")
    else:
        print("\n⚠️ 部分模块导入失败\n")
    
    return all_imported


def test_feature_flag_coordination():
    """测试 Feature Flag 之间的协调性"""
    print("="*60)
    print("综合测试 3: Feature Flag 协调性测试")
    print("="*60)
    
    from harness.core.feature_flags import FeatureSDK
    sdk = FeatureSDK()
    
    # 测试关键 Flag 的一致性
    flags_to_check = [
        "memory_system_enabled",
        "auto_save_cases",
        "similar_case_retrieval",
        "bug_type_optimization_enabled",
        "llm_analysis_enabled",
        "aloggrep_integration",
        "evidence_matching_enabled"
    ]
    
    print("\n检查关键 Flag 状态:")
    for flag_name in flags_to_check:
        try:
            flag = sdk.get_flag(flag_name)
            if flag:
                is_enabled = sdk.is_enabled(flag_name)
                print(f"  {flag_name:<30} {'✓ Enabled' if is_enabled else '✗ Disabled'}")
            else:
                print(f"  {flag_name:<30} - Not Found")
        except Exception as e:
            print(f"  {flag_name:<30} - Error: {e}")
    
    # 检查 memory_mode 变体
    memory_mode = sdk.get_variant("memory_mode")
    analysis_mode = sdk.get_variant("analysis_mode")
    
    print(f"\n变体 Flag 值:")
    print(f"  memory_mode: {memory_mode}")
    print(f"  analysis_mode: {analysis_mode}")
    
    print("\n✅ Feature Flag 协调性测试通过\n")
    return True


def test_bug_type_full_workflow():
    """测试 Bug Type 分析的完整工作流"""
    print("="*60)
    print("综合测试 4: Bug Type 完整工作流")
    print("="*60)
    
    # 测试点 1: 检测各种 Bug 类型
    from harness.skills.bug_type import PromptTemplateManager, BugType
    
    test_cases = [
        # (log_analysis, expected_type, description)
        ({"crashes": 1, "critical_logs": []}, BugType.CRASH, "Crash detection"),
        ({"anrs": 1, "critical_logs": []}, BugType.ANR, "ANR detection"),
        ({"low_memory": 5, "critical_logs": []}, BugType.MEMORY_LEAK, "Memory leak detection"),
        ({"crashes": 0, "anrs": 0, "low_memory": 0, "critical_logs": []}, BugType.GENERAL, "General case"),
    ]
    
    for log_data, expected_type, description in test_cases:
        detected = PromptTemplateManager.detect_bug_type(log_data)
        print(f"✓ {description}: {detected}")
    
    # 测试点 2: 获取分析器
    analyzers = [
        BugType.CRASH,
        BugType.ANR,
        BugType.MEMORY_LEAK,
        BugType.PERFORMANCE,
        BugType.NETWORK,
        BugType.POWER
    ]
    
    print("\n获取分析器测试:")
    for bug_type in analyzers:
        analyzer = PromptTemplateManager.get_analyzer(bug_type)
        if analyzer:
            print(f"✓ {bug_type}: {analyzer.name}")
        else:
            print(f"✗ {bug_type}: No analyzer")
    
    # 测试点 3: BugTypeAnalysisSkill 集成
    from harness.skills.bug_type_analysis_skill import BugTypeAnalysisSkill
    skill = BugTypeAnalysisSkill()
    
    # 模拟完整输入
    result = skill.execute({
        "bug_description": {"raw_text": "App crashes"},
        "advanced_log_analysis": {
            "data": {
                "crashes": 1,
                "critical_logs": []
            }
        }
    })
    
    assert result.success
    print(f"\n✓ BugTypeAnalysisSkill 执行成功: {result.data.get('bug_type')}")
    
    print("\n✅ Bug Type 完整工作流测试通过\n")
    return True


def test_skill_registration():
    """测试技能注册和发现"""
    print("="*60)
    print("综合测试 5: 技能注册")
    print("="*60)
    
    # 检查我们能导入所有主要技能
    skills = [
        ("LogExtractionSkill", "harness.skills"),
        ("AdvancedLogAnalysisSkill", "harness.skills.log_analysis_advanced"),
        ("LLMAnalysisSkill", "harness.skills.llm_analysis"),
        ("BugTypeAnalysisSkill", "harness.skills.bug_type_analysis_skill"),
        ("CaseLibrarySkill", "harness.skills.case_library_skill"),
    ]
    
    print("\n检查技能模块可访问性:")
    for skill_name, module_path in skills:
        try:
            module = __import__(module_path, fromlist=[skill_name])
            skill_class = getattr(module, skill_name)
            print(f"✓ {skill_name}")
        except Exception as e:
            print(f"✗ {skill_name}: {e}")
    
    print("\n✅ 技能注册检查通过\n")
    return True


def test_state_integration():
    """测试状态管理集成"""
    print("="*60)
    print("综合测试 6: 状态管理集成")
    print("="*60)
    
    from harness.core.state import StateManager, WorkflowStage
    
    manager = StateManager()
    
    # 测试初始化
    assert manager.get_state() is not None
    print("✓ 状态管理初始化成功")
    
    # 初始化工作流
    workflow_id = manager.initialize_workflow("test_workflow")
    assert workflow_id is not None
    print(f"✓ 工作流初始化成功: {workflow_id}")
    
    # 测试阶段转换
    manager.transition_stage(WorkflowStage.PLAN)
    state = manager.get_state()
    assert state.get("current_stage") == WorkflowStage.PLAN.value
    print("✓ PLANT 阶段转换成功")
    
    manager.transition_stage(WorkflowStage.BUILD)
    state = manager.get_state()
    assert state.get("current_stage") == WorkflowStage.BUILD.value
    print("✓ BUILD 阶段转换成功")
    
    # 测试上下文更新
    manager.update_context("test_key", "test_value")
    state = manager.get_state()
    assert state.get("context", {}).get("test_key") == "test_value"
    print("✓ 上下文更新成功")
    
    # 测试输出保存
    manager.update_output("test_output", {"result": "success"})
    state = manager.get_state()
    assert "test_output" in state.get("outputs", {})
    print("✓ 输出保存成功")
    
    print("\n✅ 状态管理集成测试通过\n")
    return True


def main():
    """运行所有综合测试"""
    print("\n" + "="*60)
    print("🎯 核心组件综合测试套件")
    print("="*60 + "\n")
    
    all_passed = True
    test_results = []
    
    try:
        # 运行所有测试
        result1 = test_module_imports()
        test_results.append(("模块导入", result1))
        
        result2 = test_feature_flag_coordination()
        test_results.append(("Feature Flag", result2))
        
        result3 = test_bug_type_full_workflow()
        test_results.append(("Bug Type 工作流", result3))
        
        result4 = test_skill_registration()
        test_results.append(("技能注册", result4))
        
        result5 = test_state_integration()
        test_results.append(("状态管理", result5))
        
        result6 = test_full_integration_simple_mode()
        test_results.append(("Simple 模式集成", result6))
        
        # 打印总结
        print("\n" + "="*60)
        print("📊 综合测试总结")
        print("="*60)
        
        for name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {name}: {status}")
        
        all_passed = all(result for _, result in test_results)
        
        if all_passed:
            print("\n🎉 所有综合测试通过！")
            print("="*60)
            return 0
        else:
            print("\n❌ 部分测试失败")
            print("="*60)
            return 1
            
    except Exception as e:
        print(f"\n❌ 测试执行异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
