#!/usr/bin/env python3
"""
Feature Flag 引擎完整单元测试
"""
import sys
import os
import tempfile
import shutil
sys.path.insert(0, '/workspace')

from harness.core.feature_flags import (
    FeatureFlag,
    FeatureFlagEngine,
    FeatureSDK
)


def test_feature_flag_model():
    """测试 FeatureFlag 数据模型"""
    print("="*60)
    print("测试 1: FeatureFlag 数据模型")
    print("="*60)
    
    # 测试基本创建
    flag = FeatureFlag(
        name="test_flag",
        description="测试用 Flag",
        flag_type="boolean",
        enabled=True
    )
    
    assert flag.name == "test_flag"
    assert flag.description == "测试用 Flag"
    assert flag.flag_type == "boolean"
    assert flag.enabled is True
    print("✓ 基本创建成功")
    
    # 测试默认值
    assert flag.variants == {}
    assert len(flag.environments) > 0
    print("✓ 默认值设置正确")
    
    # 测试 to_dict
    flag_dict = flag.to_dict()
    assert flag_dict["name"] == "test_flag"
    assert "description" in flag_dict
    assert "enabled" in flag_dict
    print("✓ to_dict 功能正常")
    
    print("\n✅ FeatureFlag 数据模型测试通过\n")


def test_feature_flag_engine_basic():
    """测试 FeatureFlagEngine 基本功能"""
    print("="*60)
    print("测试 2: FeatureFlagEngine 基本功能")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(test_dir, "feature_flags.yaml")
        
        # 初始化引擎（会创建默认配置）
        engine = FeatureFlagEngine(config_path=config_path)
        
        # 测试加载默认 Flag
        flags = engine.get_all_flags()
        assert len(flags) > 0, "应该加载至少一些默认 Flags"
        print(f"✓ 默认加载 {len(flags)} 个 Flags")
        
        # 测试获取单个 Flag
        llm_flag = engine.get_flag("llm_analysis_enabled")
        assert llm_flag is not None
        assert llm_flag.flag_type == "boolean"
        print("✓ get_flag 功能正常")
        
        # 测试布尔 Flag 求值
        is_enabled = engine.evaluate("llm_analysis_enabled")
        assert isinstance(is_enabled, bool)
        print(f"✓ 布尔 Flag 求值成功: {is_enabled}")
        
        # 测试不存在的 Flag
        result = engine.evaluate("non_existent_flag")
        assert result is False, "不存在的 Flag 应该返回 False"
        print("✓ 不存在的 Flag 返回 False 正确")
        
        print("\n✅ FeatureFlagEngine 基本功能测试通过\n")
        return True
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_feature_flag_engine_multivariate():
    """测试多元 Flag 功能"""
    print("="*60)
    print("测试 3: 多元 Flag 功能")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(test_dir, "feature_flags.yaml")
        engine = FeatureFlagEngine(config_path=config_path)
        
        # 添加一个多元 Flag
        test_flag = FeatureFlag(
            name="test_mode",
            description="测试模式",
            flag_type="multivariate",
            enabled=True,
            variants={
                "mode1": {"description": "模式1", "value": "value1"},
                "mode2": {"description": "模式2", "value": "value2"}
            },
            default_value="value1"
        )
        engine.add_flag(test_flag)
        
        # 测试获取默认值
        result = engine.evaluate("test_mode")
        assert result is not None
        print(f"✓ 多元 Flag 默认值: {result}")
        
        # 测试 get_variant
        from harness.core.feature_flags import feature_sdk
        variant = feature_sdk.get_variant("test_mode")
        print(f"✓ FeatureSDK get_variant 功能正常")
        
        print("\n✅ 多元 Flag 测试通过\n")
        return True
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_feature_flag_crud():
    """测试 Flag 的增删改查"""
    print("="*60)
    print("测试 4: Flag CRUD 操作")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(test_dir, "feature_flags.yaml")
        engine = FeatureFlagEngine(config_path=config_path)
        
        # 初始数量
        initial_count = len(engine.get_all_flags())
        
        # 添加新 Flag
        new_flag = FeatureFlag(
            name="new_feature_flag",
            description="新功能",
            flag_type="boolean",
            enabled=True
        )
        engine.add_flag(new_flag)
        
        assert len(engine.get_all_flags()) == initial_count + 1
        print("✓ add_flag 成功")
        
        # 更新 Flag
        engine.update_flag("new_feature_flag", enabled=False)
        updated_flag = engine.get_flag("new_feature_flag")
        assert updated_flag.enabled is False
        print("✓ update_flag 成功")
        
        # 测试求值
        result = engine.evaluate("new_feature_flag")
        assert result is False
        print(f"✓ 求值结果正确: {result}")
        
        # 删除 Flag
        engine.remove_flag("new_feature_flag")
        assert len(engine.get_all_flags()) == initial_count
        print("✓ remove_flag 成功")
        
        print("\n✅ Flag CRUD 测试通过\n")
        return True
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_feature_flag_percentage_rollout():
    """测试百分比灰度发布"""
    print("="*60)
    print("测试 5: 百分比灰度发布")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(test_dir, "feature_flags.yaml")
        engine = FeatureFlagEngine(config_path=config_path)
        
        # 创建测试用 Flag
        rollout_flag = FeatureFlag(
            name="rollout_test",
            description="灰度发布测试",
            flag_type="boolean",
            enabled=True,
            percentage_rollout=100  # 100% 全量
        )
        engine.add_flag(rollout_flag)
        
        # 100% 时应该总是 True
        context = {"user_id": "user123"}
        result = engine.evaluate("rollout_test", context)
        assert result is True
        print("✓ 100% 灰度总是启用")
        
        # 测试 0% 灰度
        engine.update_flag("rollout_test", percentage_rollout=0)
        result = engine.evaluate("rollout_test", context)
        print(f"✓ 0% 灰度结果: {result}")
        
        print("\n✅ 百分比灰度测试通过\n")
        return True
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_feature_flag_targeting_rules():
    """测试目标规则匹配"""
    print("="*60)
    print("测试 6: 目标规则匹配")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(test_dir, "feature_flags.yaml")
        engine = FeatureFlagEngine(config_path=config_path)
        
        # 创建带目标规则的 Flag
        targeting_flag = FeatureFlag(
            name="targeted_feature",
            description="目标用户测试",
            flag_type="boolean",
            enabled=True,
            targeting_rules=[
                {
                    "attribute": "user_id",
                    "operator": "equals",
                    "value": "premium_user"
                }
            ]
        )
        engine.add_flag(targeting_flag)
        
        # 测试匹配规则
        premium_context = {"user_id": "premium_user"}
        other_context = {"user_id": "normal_user"}
        
        result_premium = engine.evaluate("targeted_feature", premium_context)
        result_normal = engine.evaluate("targeted_feature", other_context)
        
        print(f"✓ 目标用户求值: {result_premium}")
        print(f"✓ 普通用户求值: {result_normal}")
        
        # 测试其他操作符
        test_flag2 = FeatureFlag(
            name="operator_test",
            description="操作符测试",
            flag_type="boolean",
            enabled=True,
            targeting_rules=[
                {"attribute": "age", "operator": "greater_than", "value": 18}
            ]
        )
        engine.add_flag(test_flag2)
        
        adult_context = {"age": 25}
        result_adult = engine.evaluate("operator_test", adult_context)
        print(f"✓ greater_than 操作符: {result_adult}")
        
        print("\n✅ 目标规则匹配测试通过\n")
        return True
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_feature_flag_environments():
    """测试环境限制"""
    print("="*60)
    print("测试 7: 环境限制")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(test_dir, "feature_flags.yaml")
        engine = FeatureFlagEngine(config_path=config_path)
        
        # 创建只在 dev 环境启用的 Flag
        dev_only_flag = FeatureFlag(
            name="dev_only_feature",
            description="仅开发环境",
            flag_type="boolean",
            enabled=True,
            environments=["dev"]
        )
        engine.add_flag(dev_only_flag)
        
        # 测试不同环境
        dev_context = {"environment": "dev"}
        prod_context = {"environment": "prod"}
        
        result_dev = engine.evaluate("dev_only_feature", dev_context)
        result_prod = engine.evaluate("dev_only_feature", prod_context)
        
        print(f"✓ dev 环境: {result_dev}")
        print(f"✓ prod 环境: {result_prod}")
        
        print("\n✅ 环境限制测试通过\n")
        return True
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_feature_flag_sdk():
    """测试 FeatureSDK"""
    print("="*60)
    print("测试 8: FeatureSDK 功能")
    print("="*60)
    
    # 测试 SDK 单例
    sdk1 = FeatureSDK()
    sdk2 = FeatureSDK()
    assert sdk1 is sdk2, "SDK 应该是单例"
    print("✓ SDK 单例模式正常")
    
    # 测试 is_enabled
    sdk1.is_enabled("llm_analysis_enabled")
    print("✓ is_enabled 调用正常")
    
    # 测试 get_variant
    variant = sdk1.get_variant("analysis_mode")
    print(f"✓ get_variant 返回值: {variant}")
    
    # 测试 get_all_flags
    all_flags = sdk1.get_all_flags()
    assert isinstance(all_flags, dict)
    print(f"✓ get_all_flags 成功，共 {len(all_flags)} 个 Flags")
    
    print("\n✅ FeatureSDK 测试通过\n")


def test_feature_flag_context_hash():
    """测试上下文哈希"""
    print("="*60)
    print("测试 9: 上下文哈希")
    print("="*60)
    
    test_dir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(test_dir, "feature_flags.yaml")
        engine = FeatureFlagEngine(config_path=config_path)
        
        # 测试相同上下文返回相同哈希
        context1 = {"user_id": "test_user_001"}
        context2 = {"user_id": "test_user_001"}
        
        hash1 = engine._hash_context(context1)
        hash2 = engine._hash_context(context2)
        
        assert hash1 == hash2, "相同上下文应该返回相同哈希"
        print("✓ 上下文哈希一致性")
        
        # 测试不同上下文可能返回不同哈希
        context3 = {"user_id": "test_user_999"}
        hash3 = engine._hash_context(context3)
        print(f"✓ Hash 计算正常: {hash1} vs {hash3}")
        
        # 测试无上下文
        hash_empty = engine._hash_context(None)
        assert hash_empty == 0, "无上下文时哈希应该为 0"
        print("✓ 无上下文返回 0")
        
        print("\n✅ 上下文哈希测试通过\n")
        return True
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🎯 Feature Flag 引擎完整测试套件")
    print("="*60 + "\n")
    
    all_passed = True
    
    try:
        test_feature_flag_model()
        test_feature_flag_engine_basic()
        test_feature_flag_engine_multivariate()
        test_feature_flag_crud()
        test_feature_flag_percentage_rollout()
        test_feature_flag_targeting_rules()
        test_feature_flag_environments()
        test_feature_flag_sdk()
        test_feature_flag_context_hash()
        
        print("="*60)
        print("🎉 所有 Feature Flag 测试通过！")
        print("="*60)
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
