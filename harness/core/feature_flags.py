"""Feature Flag 核心模块 - 参考 Harness FME 设计"""

from typing import Dict, Any, Optional, List
import yaml
import os
import hashlib
from dataclasses import dataclass
from datetime import datetime

from harness.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class FeatureFlag:
    """Feature Flag 数据模型"""
    name: str
    description: str
    flag_type: str = "boolean"
    enabled: bool = False
    variants: Dict[str, Any] = None
    targeting_rules: List[Dict] = None
    percentage_rollout: int = 0
    environments: List[str] = None
    default_value: Any = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.variants is None:
            self.variants = {}
        if self.targeting_rules is None:
            self.targeting_rules = []
        if self.environments is None:
            self.environments = ["dev", "prod"]
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "flag_type": self.flag_type,
            "enabled": self.enabled,
            "variants": self.variants,
            "targeting_rules": self.targeting_rules,
            "percentage_rollout": self.percentage_rollout,
            "environments": self.environments,
            "default_value": self.default_value,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class FeatureFlagEngine:
    """Feature Flag 求值引擎"""
    
    def __init__(self, config_path: str = None):
        # 自动计算项目根目录和配置文件路径
        if config_path:
            self.config_path = config_path
        else:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.config_path = os.path.join(project_root, "config", "feature_flags.yaml")
        self.flags: Dict[str, FeatureFlag] = {}
        self._load_flags()
    
    def _load_flags(self):
        """从配置文件加载所有 flags"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and 'flags' in data:
                        for name, flag_data in data['flags'].items():
                            self.flags[name] = FeatureFlag(**flag_data)
                logger.info(f"Loaded {len(self.flags)} feature flags")
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                self._create_default_config()
        except Exception as e:
            logger.error(f"Failed to load feature flags: {e}")
    
    def _create_default_config(self):
        """创建默认配置文件"""
        default_flags = {
            "flags": {
                "llm_analysis_enabled": {
                    "name": "llm_analysis_enabled",
                    "description": "是否启用 LLM 分析功能",
                    "flag_type": "boolean",
                    "enabled": True,
                    "environments": ["dev", "prod"],
                    "percentage_rollout": 100
                },
                "aloggrep_integration": {
                    "name": "aloggrep_integration",
                    "description": "是否启用 aloggrep 集成",
                    "flag_type": "boolean",
                    "enabled": True,
                    "environments": ["dev", "prod"],
                    "percentage_rollout": 100
                },
                "knowledge_base_enabled": {
                    "name": "knowledge_base_enabled",
                    "description": "是否启用 QMD 知识库检索",
                    "flag_type": "boolean",
                    "enabled": True,
                    "environments": ["dev", "prod"],
                    "percentage_rollout": 100
                },
                "evidence_matching_enabled": {
                    "name": "evidence_matching_enabled",
                    "description": "是否启用日志证据匹配",
                    "flag_type": "boolean",
                    "enabled": True,
                    "environments": ["dev", "prod"],
                    "percentage_rollout": 100
                },
                "bug_type_optimization_enabled": {
                    "name": "bug_type_optimization_enabled",
                    "description": "是否启用 Bug 类型差异化提示词和模板优化",
                    "flag_type": "boolean",
                    "enabled": True,
                    "environments": ["dev", "prod"],
                    "percentage_rollout": 100
                },
                "analysis_mode": {
                    "name": "analysis_mode",
                    "description": "分析模式：fast/standard/deep",
                    "flag_type": "multivariate",
                    "enabled": True,
                    "variants": {
                        "fast": {"description": "快速分析", "value": "fast"},
                        "standard": {"description": "标准分析", "value": "standard"},
                        "deep": {"description": "深度分析", "value": "deep"}
                    },
                    "default_value": "standard",
                    "environments": ["dev", "prod"],
                    "percentage_rollout": 100
                }
            }
        }
        
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_flags, f, indent=2, allow_unicode=True)
        
        self._load_flags()
    
    def evaluate(self, flag_name: str, context: Dict = None) -> Any:
        """
        求值 Flag 值
        
        Args:
            flag_name: Flag 名称
            context: 上下文（用户、环境、属性等）
        
        Returns:
            Flag 值（boolean 或变体值）
        """
        flag = self.flags.get(flag_name)
        if not flag:
            logger.warning(f"Flag not found: {flag_name}")
            return False
        
        # 1. 检查全局开关
        if not flag.enabled:
            logger.debug(f"Flag {flag_name} is globally disabled")
            return self._get_default_value(flag)
        
        # 2. 检查环境
        if context and 'environment' in context:
            env = context['environment']
            if env not in flag.environments:
                logger.debug(f"Flag {flag_name} not available in environment: {env}")
                return self._get_default_value(flag)
        
        # 3. 匹配目标规则
        if self._match_targeting_rules(flag, context):
            return self._get_variant_value(flag, context)
        
        # 4. 百分比灰度
        percentage = flag.percentage_rollout
        if percentage > 0:
            hash_value = self._hash_context(context)
            if hash_value < percentage:
                logger.debug(f"Flag {flag_name} matched percentage rollout: {hash_value}% < {percentage}%")
                return self._get_variant_value(flag, context)
        
        # 5. 返回默认值
        return self._get_default_value(flag)
    
    def _get_default_value(self, flag: FeatureFlag) -> Any:
        """获取默认值"""
        if flag.flag_type == "boolean":
            return flag.enabled
        elif flag.flag_type == "multivariate":
            return flag.default_value
        else:
            return flag.default_value
    
    def _get_variant_value(self, flag: FeatureFlag, context: Dict = None) -> Any:
        """获取变体值"""
        if flag.flag_type == "boolean":
            return True
        elif flag.flag_type == "multivariate":
            # 如果有变体配置，返回第一个变体或默认值
            if flag.variants:
                # 根据上下文哈希选择变体
                if context:
                    hash_val = self._hash_context(context)
                    variant_names = list(flag.variants.keys())
                    idx = hash_val % len(variant_names)
                    return flag.variants[variant_names[idx]]['value']
                return flag.default_value
            return flag.default_value
        else:
            return flag.default_value
    
    def _match_targeting_rules(self, flag: FeatureFlag, context: Dict) -> bool:
        """匹配目标规则"""
        if not context:
            return False
        
        rules = flag.targeting_rules
        for rule in rules:
            if self._evaluate_rule(rule, context):
                return True
        return False
    
    def _evaluate_rule(self, rule: Dict, context: Dict) -> bool:
        """评估单个规则"""
        try:
            attribute = rule.get('attribute')
            operator = rule.get('operator')
            value = rule.get('value')
            
            if attribute not in context:
                return False
            
            context_value = context[attribute]
            
            # 支持的操作符
            if operator == 'equals':
                return context_value == value
            elif operator == 'contains':
                return value in str(context_value)
            elif operator == 'greater_than':
                return context_value > value
            elif operator == 'less_than':
                return context_value < value
            elif operator == 'in':
                return context_value in value
            elif operator == 'not_equals':
                return context_value != value
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating rule: {e}")
            return False
    
    def _hash_context(self, context: Dict = None) -> int:
        """基于上下文计算确定性哈希"""
        if not context:
            return 0
        
        # 使用用户 ID 或其他唯一标识计算哈希
        user_id = context.get('user_id', context.get('request_id', 'default'))
        return int(hashlib.md5(str(user_id).encode()).hexdigest(), 16) % 100
    
    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """获取单个 Flag"""
        return self.flags.get(flag_name)
    
    def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """获取所有 Flags"""
        return self.flags
    
    def update_flag(self, flag_name: str, **kwargs):
        """更新 Flag"""
        if flag_name not in self.flags:
            raise ValueError(f"Flag not found: {flag_name}")
        
        flag = self.flags[flag_name]
        for key, value in kwargs.items():
            if hasattr(flag, key):
                setattr(flag, key, value)
        
        flag.updated_at = datetime.now().isoformat()
        self._save_flags()
    
    def add_flag(self, flag: FeatureFlag):
        """添加新 Flag"""
        self.flags[flag.name] = flag
        self._save_flags()
    
    def remove_flag(self, flag_name: str):
        """删除 Flag"""
        if flag_name in self.flags:
            del self.flags[flag_name]
            self._save_flags()
    
    def _save_flags(self):
        """保存所有 Flags 到配置文件"""
        data = {
            "flags": {name: flag.to_dict() for name, flag in self.flags.items()}
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, indent=2, allow_unicode=True)
        
        logger.info(f"Saved {len(self.flags)} feature flags")
    
    def reload(self):
        """重新加载配置"""
        self.flags.clear()
        self._load_flags()

class FeatureSDK:
    """Feature Flag SDK - 简化接入"""
    
    _instance = None
    
    def __new__(cls, engine: FeatureFlagEngine = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.engine = engine or FeatureFlagEngine()
        return cls._instance
    
    def is_enabled(self, flag_name: str, context: Dict = None) -> bool:
        """检查 Flag 是否启用"""
        return bool(self.engine.evaluate(flag_name, context))
    
    def get_variant(self, flag_name: str, context: Dict = None) -> Any:
        """获取 Flag 变体值"""
        return self.engine.evaluate(flag_name, context)
    
    def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """获取所有 Flag 状态"""
        return self.engine.get_all_flags()
    
    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """获取单个 Flag"""
        return self.engine.get_flag(flag_name)
    
    def update_flag(self, flag_name: str, **kwargs):
        """更新 Flag"""
        self.engine.update_flag(flag_name, **kwargs)
    
    def reload(self):
        """重新加载配置"""
        self.engine.reload()

# 全局 SDK 实例
feature_sdk = FeatureSDK()
