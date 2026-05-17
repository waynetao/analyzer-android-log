#!/usr/bin/env python3
"""Feature Flag 功能测试脚本"""
import sys
sys.path.insert(0, '/workspace')

def test_feature_flags():
    """测试 Feature Flag 核心模块"""
    print("=" * 60)
    print("1. 测试 Feature Flag 核心模块")
    print("=" * 60)
    
    from harness.core.feature_flags import FeatureSDK, FeatureFlag, FeatureFlagEngine
    
    try:
        # 测试 SDK 初始化
        sdk = FeatureSDK()
        assert sdk is not None
        print("✅ FeatureSDK 初始化成功")
        
        # 测试获取所有 flags
        flags = sdk.get_all_flags()
        assert len(flags) > 0
        print(f"✅ 获取到 {len(flags)} 个 Feature Flags")
        
        # 测试 is_enabled
        assert sdk.is_enabled("llm_analysis_enabled") == True
        assert sdk.is_enabled("aloggrep_integration") == True
        print("✅ is_enabled() 方法正常")
        
        # 测试 get_variant
        mode = sdk.get_variant("analysis_mode")
        assert mode in ["fast", "standard", "deep"]
        print(f"✅ get_variant() 方法正常，当前模式: {mode}")
        
        # 测试上下文求值
        context = {"user_id": "test_user", "environment": "dev"}
        value = sdk.is_enabled("llm_analysis_enabled", context)
        assert value == True
        print("✅ 上下文求值正常")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flag_management():
    """测试 Flag 管理功能"""
    print("\n" + "=" * 60)
    print("2. 测试 Flag 管理功能")
    print("=" * 60)
    
    from harness.core.feature_flags import FeatureSDK
    
    try:
        sdk = FeatureSDK()
        
        # 测试更新 flag
        sdk.update_flag("analysis_mode", default_value="fast")
        mode = sdk.get_variant("analysis_mode")
        assert mode == "fast"
        print("✅ 更新 Flag 成功")
        
        # 恢复默认值
        sdk.update_flag("analysis_mode", default_value="standard")
        mode = sdk.get_variant("analysis_mode")
        assert mode == "standard"
        print("✅ 恢复 Flag 成功")
        
        # 测试灰度设置
        sdk.update_flag("llm_analysis_enabled", percentage_rollout=50)
        flag = sdk.get_flag("llm_analysis_enabled")
        assert flag.percentage_rollout == 50
        print("✅ 灰度设置成功")
        
        # 恢复灰度
        sdk.update_flag("llm_analysis_enabled", percentage_rollout=100)
        print("✅ 灰度恢复成功")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_integration():
    """测试 Agent 集成"""
    print("\n" + "=" * 60)
    print("3. 测试 Agent 集成")
    print("=" * 60)
    
    try:
        # 检查 Agent 文件是否导入了 FeatureSDK
        with open('/workspace/harness_agent_advanced.py', 'r') as f:
            content = f.read()
            assert 'from harness.core.feature_flags import FeatureSDK' in content
            assert 'self.feature_sdk = FeatureSDK()' in content
            assert 'self.feature_sdk.is_enabled' in content
            assert 'self.feature_sdk.get_variant' in content
        print("✅ Agent 已正确集成 Feature Flag")
        
        # 测试条件注册逻辑
        from harness.core.feature_flags import FeatureSDK
        sdk = FeatureSDK()
        
        # 临时禁用一个功能
        sdk.update_flag("knowledge_base_enabled", enabled=False)
        assert sdk.is_enabled("knowledge_base_enabled") == False
        print("✅ 功能禁用测试成功")
        
        # 恢复
        sdk.update_flag("knowledge_base_enabled", enabled=True)
        assert sdk.is_enabled("knowledge_base_enabled") == True
        print("✅ 功能恢复测试成功")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cli_tool():
    """测试命令行工具"""
    print("\n" + "=" * 60)
    print("4. 测试命令行工具")
    print("=" * 60)
    
    import subprocess
    
    try:
        # 测试 list 命令
        result = subprocess.run(['python', '/workspace/ffctl.py', 'list'], 
                               capture_output=True, text=True)
        assert result.returncode == 0
        assert 'llm_analysis_enabled' in result.stdout
        print("✅ ffctl list 命令正常")
        
        # 测试 show 命令
        result = subprocess.run(['python', '/workspace/ffctl.py', 'show', 'analysis_mode'], 
                               capture_output=True, text=True)
        assert result.returncode == 0
        assert 'multivariate' in result.stdout
        print("✅ ffctl show 命令正常")
        
        # 测试 evaluate 命令
        result = subprocess.run(['python', '/workspace/ffctl.py', 'evaluate', 'llm_analysis_enabled'], 
                               capture_output=True, text=True)
        assert result.returncode == 0
        assert '启用:' in result.stdout
        print("✅ ffctl evaluate 命令正常")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Feature Flag 功能测试")
    print("=" * 60)
    print()
    
    tests = [
        ("核心模块", test_feature_flags),
        ("管理功能", test_flag_management),
        ("Agent集成", test_agent_integration),
        ("CLI工具", test_cli_tool),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 所有测试通过!")
        print("✅ Feature Flag 系统已完成")
    else:
        print("❌ 部分测试失败")
    
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
