"""
Feature Flag 单元测试
测试 Feature Flag 引擎的各个功能
"""

import pytest
import os
import yaml
from datetime import datetime

from harness.core.feature_flags import (
    FeatureFlagEngine,
    FeatureSDK,
    FeatureFlag
)


class TestFeatureFlag:
    """Feature Flag 数据模型测试"""

    def test_feature_flag_creation(self):
        """测试 Feature Flag 创建"""
        flag = FeatureFlag(
            name="test_flag",
            description="测试标志",
            flag_type="boolean",
            enabled=True
        )

        assert flag.name == "test_flag"
        assert flag.flag_type == "boolean"
        assert flag.enabled is True

    def test_feature_flag_defaults(self):
        """测试默认值"""
        flag = FeatureFlag(name="test", description="测试")

        assert flag.variants == {}
        assert flag.targeting_rules == []
        assert flag.environments == ["dev", "prod"]
        assert flag.created_at is not None
        assert flag.updated_at is not None

    def test_to_dict(self):
        """测试转换为字典"""
        flag = FeatureFlag(
            name="test",
            description="测试",
            flag_type="boolean",
            enabled=True
        )

        data = flag.to_dict()

        assert data["name"] == "test"
        assert data["enabled"] is True


class TestFeatureFlagEngine:
    """Feature Flag 引擎测试"""

    def test_engine_initialization_with_config(self, tmp_path):
        """测试带配置的引擎初始化"""
        config_file = tmp_path / "flags.yaml"
        config_data = {
            "flags": {
                "test_flag": {
                    "name": "test_flag",
                    "description": "测试",
                    "flag_type": "boolean",
                    "enabled": True
                }
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)

        engine = FeatureFlagEngine(config_path=str(config_file))

        assert len(engine.flags) == 1
        assert "test_flag" in engine.flags

    def test_engine_initialization_without_config(self, tmp_path):
        """测试无配置文件时创建默认配置"""
        config_file = tmp_path / "non_existent.yaml"

        engine = FeatureFlagEngine(config_path=str(config_file))

        # 应该创建默认配置
        assert len(engine.flags) > 0

    def test_evaluate_boolean_flag(self, tmp_path):
        """测试布尔标志求值"""
        config_file = tmp_path / "flags.yaml"
        config_data = {
            "flags": {
                "test_flag": {
                    "name": "test_flag",
                    "description": "测试",
                    "flag_type": "boolean",
                    "enabled": True
                }
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)

        engine = FeatureFlagEngine(config_path=str(config_file))

        assert engine.evaluate("test_flag") is True

    def test_evaluate_disabled_flag(self, tmp_path):
        """测试禁用的标志"""
        config_file = tmp_path / "flags.yaml"
        config_data = {
            "flags": {
                "test_flag": {
                    "name": "test_flag",
                    "description": "测试",
                    "flag_type": "boolean",
                    "enabled": False
                }
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)

        engine = FeatureFlagEngine(config_path=str(config_file))

        assert engine.evaluate("test_flag") is False

    def test_evaluate_nonexistent_flag(self, tmp_path):
        """测试不存在的标志"""
        engine = FeatureFlagEngine(config_path=str(tmp_path / "empty.yaml"))
        result = engine.evaluate("nonexistent_flag")

        assert result is False

    def test_evaluate_multivariate_flag(self, tmp_path):
        """测试多变量标志"""
        config_file = tmp_path / "flags.yaml"
        config_data = {
            "flags": {
                "mode": {
                    "name": "mode",
                    "description": "模式",
                    "flag_type": "multivariate",
                    "enabled": True,
                    "variants": {
                        "fast": {"description": "快速", "value": "fast"},
                        "slow": {"description": "慢速", "value": "slow"}
                    },
                    "default_value": "fast"
                }
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)

        engine = FeatureFlagEngine(config_path=str(config_file))
        result = engine.evaluate("mode")

        assert result in ["fast", "slow"]

    def test_get_flag(self, tmp_path):
        """测试获取标志"""
        config_file = tmp_path / "flags.yaml"
        config_data = {
            "flags": {
                "test_flag": {
                    "name": "test_flag",
                    "description": "测试",
                    "flag_type": "boolean",
                    "enabled": True
                }
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)

        engine = FeatureFlagEngine(config_path=str(config_file))
        flag = engine.get_flag("test_flag")

        assert flag is not None
        assert flag.name == "test_flag"

    def test_get_all_flags(self, tmp_path):
        """测试获取所有标志"""
        config_file = tmp_path / "flags.yaml"
        config_data = {
            "flags": {
                "flag1": {"name": "flag1", "description": "测试1", "flag_type": "boolean"},
                "flag2": {"name": "flag2", "description": "测试2", "flag_type": "boolean"}
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)

        engine = FeatureFlagEngine(config_path=str(config_file))
        flags = engine.get_all_flags()

        assert len(flags) == 2

    def test_update_flag(self, tmp_path):
        """测试更新标志"""
        config_file = tmp_path / "flags.yaml"
        config_data = {
            "flags": {
                "test_flag": {
                    "name": "test_flag",
                    "description": "测试",
                    "flag_type": "boolean",
                    "enabled": False
                }
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)

        engine = FeatureFlagEngine(config_path=str(config_file))
        engine.update_flag("test_flag", enabled=True)

        flag = engine.get_flag("test_flag")
        assert flag.enabled is True


class TestFeatureSDK:
    """Feature SDK 测试"""

    def test_sdk_singleton(self):
        """测试 SDK 单例"""
        sdk1 = FeatureSDK()
        sdk2 = FeatureSDK()

        assert sdk1 is sdk2

    def test_is_enabled(self):
        """测试检查启用状态"""
        sdk = FeatureSDK()
        result = sdk.is_enabled("test_flag")

        # 应该返回布尔值
        assert isinstance(result, bool)

    def test_get_variant(self):
        """测试获取变体值"""
        sdk = FeatureSDK()
        result = sdk.get_variant("mode")

        # 返回值应该是配置的值或默认值
        assert result is not None
