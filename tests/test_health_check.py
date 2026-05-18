#!/usr/bin/env python3
"""
项目健康检查测试
- 检查所有核心模块能否正常导入
- 检查脚本入口能否正常运行
- 检查基本依赖是否安装
"""
import sys
import os
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def test_core_modules_import():
    """测试核心模块导入"""
    print("="*60)
    print("1. 测试核心模块导入")
    print("="*60)
    
    modules = [
        # Harness Core
        'harness.core',
        'harness.core.context',
        'harness.core.state',
        'harness.core.orchestrator',
        'harness.core.feature_flags',
        # Harness Skills
        'harness.skills',
        'harness.skills.base',
        'harness.skills.llm_enhanced',
        'harness.skills.llm_analysis',
        'harness.skills.log_evidence_matcher',
        'harness.skills.case_library_skill',
        'harness.skills.knowledge_retrieval',
        'harness.skills.bug_type_analysis_skill',
        # Harness Policies
        'harness.policies',
        # Log Analyzer
        'log_analyzer',
    ]
    
    all_passed = True
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except Exception as e:
            print(f"  ❌ {module}: {e}")
            all_passed = False
    
    return all_passed

def test_script_help():
    """测试脚本能否正常显示帮助（不执行实际功能）"""
    print("\n" + "="*60)
    print("2. 测试脚本入口")
    print("="*60)
    
    scripts = [
        'scripts/harness_agent.py',
        'scripts/harness_agent_advanced.py',
        'scripts/ffctl.py',
    ]
    
    all_passed = True
    for script_path in scripts:
        full_path = os.path.join(PROJECT_ROOT, script_path)
        if not os.path.exists(full_path):
            print(f"  ⚠️ {script_path}: 文件不存在")
            continue
        
        try:
            result = subprocess.run(
                ['python', full_path, '--help'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print(f"  ✅ {script_path}")
            else:
                print(f"  ❌ {script_path}: 退出码 {result.returncode}")
                if result.stderr:
                    print(f"     stderr: {result.stderr[:200]}")
                all_passed = False
        except Exception as e:
            print(f"  ❌ {script_path}: {e}")
            all_passed = False
    
    return all_passed

def test_basic_imports():
    """测试基本工具库导入"""
    print("\n" + "="*60)
    print("3. 测试基础依赖")
    print("="*60)
    
    dependencies = [
        ('yaml', 'PyYAML'),
        ('dotenv', 'python-dotenv'),
    ]
    
    all_passed = True
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}: 未安装")
            all_passed = False
    
    return all_passed

def main():
    print("\n" + "="*60)
    print("项目健康检查")
    print("="*60)
    
    results = []
    
    results.append(('核心模块导入', test_core_modules_import()))
    results.append(('脚本入口', test_script_help()))
    results.append(('基础依赖', test_basic_imports()))
    
    print("\n" + "="*60)
    print("健康检查结果")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ 所有检查通过！")
        return 0
    else:
        print("❌ 部分检查失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())

