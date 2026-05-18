#!/usr/bin/env python3
"""
测试 Bug 类型差异化优化功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.skills.bug_type import (
    PromptTemplateManager,
    BugType,
    CrashAnalyzer,
    ANRAnalyzer,
    MemoryAnalyzer,
    PerformanceAnalyzer,
    NetworkAnalyzer,
    PowerAnalyzer
)

def test_bug_type_detection():
    """测试 Bug 类型检测"""
    print("="*60)
    print("测试 Bug 类型检测")
    print("="*60)
    
    # 测试 Crash 检测
    crash_logs = {
        "crashes": 1,
        "critical_logs": [
            {"type": "crash", "message": "FATAL EXCEPTION: main"}
        ]
    }
    bug_type = PromptTemplateManager.detect_bug_type(crash_logs)
    assert bug_type == BugType.CRASH, f"期望 CRASH，实际 {bug_type}"
    print(f"✓ Crash 检测: {bug_type}")
    
    # 测试 ANR 检测
    anr_logs = {
        "anrs": 1,
        "critical_logs": [
            {"type": "anr", "message": "ANR in com.example.app"}
        ]
    }
    bug_type = PromptTemplateManager.detect_bug_type(anr_logs)
    assert bug_type == BugType.ANR, f"期望 ANR，实际 {bug_type}"
    print(f"✓ ANR 检测: {bug_type}")
    
    # 测试 Memory Leak 检测
    memory_logs = {
        "low_memory": 3,
        "critical_logs": [
            {"type": "memory", "message": "Out of memory"}
        ]
    }
    bug_type = PromptTemplateManager.detect_bug_type(memory_logs)
    assert bug_type == BugType.MEMORY_LEAK, f"期望 MEMORY_LEAK，实际 {bug_type}"
    print(f"✓ Memory Leak 检测: {bug_type}")
    
    print("\n✅ Bug 类型检测测试通过\n")

def test_analyzers():
    """测试所有分析器"""
    print("="*60)
    print("测试所有分析器")
    print("="*60)
    
    analyzers = [
        CrashAnalyzer(),
        ANRAnalyzer(),
        MemoryAnalyzer(),
        PerformanceAnalyzer(),
        NetworkAnalyzer(),
        PowerAnalyzer()
    ]
    
    bug_desc = {"raw_text": "应用崩溃了"}
    log_analysis = {"crashes": 1}
    
    for analyzer in analyzers:
        print(f"\n测试 {analyzer.name}...")
        
        # 测试获取 system prompt
        system_prompt = analyzer.get_system_prompt()
        assert len(system_prompt) > 0, f"{analyzer.name} system prompt 为空"
        print(f"  ✓ System Prompt: {len(system_prompt)} 字符")
        
        # 测试获取 user prompt
        user_prompt = analyzer.get_user_prompt(bug_desc, log_analysis)
        assert len(user_prompt) > 0, f"{analyzer.name} user prompt 为空"
        print(f"  ✓ User Prompt: {len(user_prompt)} 字符")
        
        # 测试格式化输出
        test_content = "测试分析内容"
        formatted = analyzer.format_output(test_content)
        assert len(formatted) > 0, f"{analyzer.name} 格式化输出为空"
        print(f"  ✓ 输出格式化: OK ({len(formatted)} 字符)")
    
    print("\n✅ 所有分析器测试通过\n")

def test_prompt_template_manager():
    """测试 PromptTemplateManager"""
    print("="*60)
    print("测试 PromptTemplateManager")
    print("="*60)
    
    # 测试获取分析器（只测试有分析器的类型）
    testable_types = [
        BugType.CRASH,
        BugType.ANR,
        BugType.MEMORY_LEAK,
        BugType.PERFORMANCE,
        BugType.NETWORK,
        BugType.POWER
    ]
    
    for bug_type in testable_types:
        analyzer = PromptTemplateManager.get_analyzer(bug_type)
        assert analyzer is not None, f"{bug_type} 没有对应的分析器"
        print(f"✓ {bug_type} -> {analyzer.name}")
    
    # 测试 UNKNOWN 和 GENERAL 类型应该返回 None
    assert PromptTemplateManager.get_analyzer(BugType.UNKNOWN) is None
    assert PromptTemplateManager.get_analyzer(BugType.GENERAL) is None
    print("✓ UNKNOWN 和 GENERAL 类型正确返回 None")
    
    print("\n✅ PromptTemplateManager 测试通过\n")

def test_bug_type_analysis_skill():
    """测试 BugTypeAnalysisSkill"""
    print("="*60)
    print("测试 BugTypeAnalysisSkill")
    print("="*60)
    
    from harness.skills.bug_type_analysis_skill import BugTypeAnalysisSkill
    
    skill = BugTypeAnalysisSkill()
    
    # 测试输入验证（缺少必需字段）
    result = skill.execute({})
    assert not result.success, "技能应该验证失败"
    print("✓ 输入验证: 缺少字段时正确失败")
    
    # 测试正常执行
    inputs = {
        "bug_description": {"raw_text": "应用崩溃了"},
        "advanced_log_analysis": {
            "data": {
                "crashes": 1,
                "critical_logs": [
                    {"type": "crash", "message": "FATAL EXCEPTION"}
                ]
            }
        }
    }
    result = skill.execute(inputs)
    assert result.success, f"技能执行失败: {result.message}"
    print(f"✓ 技能执行: {result.message}")
    assert result.data.get("bug_type") == "crash", f"期望 'crash'，实际 {result.data.get('bug_type')}"
    print(f"✓ Bug 类型识别: {result.data.get('bug_type')}")
    
    print("\n✅ BugTypeAnalysisSkill 测试通过\n")

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Bug 类型差异化优化功能 - 完整测试套件")
    print("="*60 + "\n")
    
    try:
        test_bug_type_detection()
        test_analyzers()
        test_prompt_template_manager()
        test_bug_type_analysis_skill()
        
        print("="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
