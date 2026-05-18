"""
配置管理系统
支持 YAML 配置文件和环境特定配置
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import logging

from harness.core.logging import get_logger
from harness.core.paths import PROJECT_ROOT_STR, CONFIG_DIR_STR

logger = get_logger(__name__)


# 敏感字段列表，不会写入配置文件
_SENSITIVE_FIELDS = {"llm_api_key"}


@dataclass
class EnvironmentConfig:
    """环境配置"""
    name: str
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: str = ""
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_max_retries: int = 3
    log_level: str = "INFO"
    log_enable_file: bool = True
    log_enable_console: bool = True
    memory_mode: str = "simple"
    analysis_mode: str = "standard"
    feature_flags: Dict[str, Any] = field(default_factory=dict)


class ConfigManager:
    """配置管理器 - 支持多环境配置"""

    _instance = None

    def __new__(cls, config_dir: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_dir: str = None):
        if self._initialized:
            return

        if config_dir is None:
            config_dir = CONFIG_DIR_STR

        self.config_dir = config_dir
        self.current_env = os.environ.get("ENV", "dev")
        self.configs: Dict[str, EnvironmentConfig] = {}
        self._load_all_configs()
        self._initialized = True

    def _load_all_configs(self):
        """加载所有环境配置"""
        config_file = os.path.join(self.config_dir, "config.yaml")

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self._parse_config_file(data)
                    logger.info(f"从 {config_file} 加载配置")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                self._create_default_config()
        else:
            self._create_default_config()

        self._load_from_env()

    def _parse_config_file(self, data: Dict[str, Any]):
        """解析配置文件"""
        if not data:
            return

        environments = data.get("environments", {})

        for env_name, env_data in environments.items():
            config = EnvironmentConfig(
                name=env_name,
                llm_api_key=env_data.get("llm_api_key"),
                llm_base_url=env_data.get("llm_base_url"),
                llm_model=env_data.get("llm_model", ""),
                llm_temperature=float(env_data.get("llm_temperature", 0.7)),
                llm_max_tokens=int(env_data.get("llm_max_tokens", 2000)),
                llm_max_retries=int(env_data.get("llm_max_retries", 3)),
                log_level=env_data.get("log_level", "INFO"),
                log_enable_file=env_data.get("log_enable_file", True),
                log_enable_console=env_data.get("log_enable_console", True),
                memory_mode=env_data.get("memory_mode", "simple"),
                analysis_mode=env_data.get("analysis_mode", "standard"),
                feature_flags=env_data.get("feature_flags", {})
            )
            self.configs[env_name] = config

        default_config = data.get("default", {})
        if default_config and "dev" not in self.configs:
            self.configs["dev"] = EnvironmentConfig(
                name="dev",
                llm_api_key=default_config.get("llm_api_key"),
                llm_base_url=default_config.get("llm_base_url"),
                llm_model=default_config.get("llm_model", "")
            )

    def _load_from_env(self):
        """从环境变量加载配置（优先级最高）"""
        for env_name in self.configs:
            config = self.configs[env_name]

            if os.getenv("LLM_API_KEY"):
                config.llm_api_key = os.getenv("LLM_API_KEY")
            if os.getenv("LLM_BASE_URL"):
                config.llm_base_url = os.getenv("LLM_BASE_URL")
            if os.getenv("LLM_MODEL"):
                config.llm_model = os.getenv("LLM_MODEL")
            if os.getenv("LLM_TEMPERATURE"):
                config.llm_temperature = float(os.getenv("LLM_TEMPERATURE"))
            if os.getenv("LLM_MAX_TOKENS"):
                config.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS"))
            if os.getenv("LOG_LEVEL"):
                config.log_level = os.getenv("LOG_LEVEL")

    def _create_default_config(self):
        """创建默认配置"""
        self.configs = {
            "dev": EnvironmentConfig(
                name="dev",
                log_level="DEBUG",
                log_enable_file=False,
                log_enable_console=True,
                analysis_mode="deep"
            ),
            "prod": EnvironmentConfig(
                name="prod",
                log_level="INFO",
                log_enable_file=True,
                log_enable_console=False,
                analysis_mode="standard"
            )
        }
        logger.info("使用默认配置")

    def get_current_config(self) -> EnvironmentConfig:
        """获取当前环境的配置"""
        config = self.configs.get(self.current_env)
        if config is None:
            config = self.configs.get("dev", EnvironmentConfig(name="dev"))
            logger.warning(f"环境 '{self.current_env}' 不存在，使用默认配置")
        return config

    def get_config(self, env: str = None) -> EnvironmentConfig:
        """获取指定环境的配置"""
        if env is None:
            return self.get_current_config()
        return self.configs.get(env, self.configs.get("dev", EnvironmentConfig(name=env)))

    def switch_env(self, env: str):
        """切换环境"""
        if env not in self.configs:
            logger.warning(f"环境 '{env}' 不存在，保持当前环境 '{self.current_env}'")
            return False

        self.current_env = env
        logger.info(f"切换到环境: {env}")
        return True

    def list_environments(self) -> List[str]:
        """列出所有可用环境"""
        return list(self.configs.keys())

    def apply_to_environment(self):
        """将当前配置应用到环境变量"""
        config = self.get_current_config()

        if config.llm_api_key:
            os.environ["LLM_API_KEY"] = config.llm_api_key
        if config.llm_base_url:
            os.environ["LLM_BASE_URL"] = config.llm_base_url
        if config.llm_model:
            os.environ["LLM_MODEL"] = config.llm_model

        os.environ["LLM_TEMPERATURE"] = str(config.llm_temperature)
        os.environ["LLM_MAX_TOKENS"] = str(config.llm_max_tokens)
        os.environ["LLM_MAX_RETRIES"] = str(config.llm_max_retries)
        os.environ["LOG_LEVEL"] = config.log_level
        os.environ["LOG_ENABLE_FILE"] = str(config.log_enable_file).lower()
        os.environ["LOG_ENABLE_CONSOLE"] = str(config.log_enable_console).lower()
        os.environ["ENV"] = config.name

        logger.info(f"配置已应用到环境变量 (ENV={config.name})")

    def save_config(self, env: str, updates: Dict[str, Any]):
        """保存配置更新"""
        if env not in self.configs:
            self.configs[env] = EnvironmentConfig(name=env)

        config = self.configs[env]
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self._save_to_file()
        logger.info(f"配置已保存 (环境: {env})")

    def _save_to_file(self):
        """保存配置到文件（敏感字段不写入，仅从环境变量读取）"""
        config_file = os.path.join(self.config_dir, "config.yaml")

        data = {
            "environments": {}
        }

        for env_name, config in self.configs.items():
            env_data = {
                "llm_base_url": config.llm_base_url,
                "llm_model": config.llm_model,
                "llm_temperature": config.llm_temperature,
                "llm_max_tokens": config.llm_max_tokens,
                "llm_max_retries": config.llm_max_retries,
                "log_level": config.log_level,
                "log_enable_file": config.log_enable_file,
                "log_enable_console": config.log_enable_console,
                "memory_mode": config.memory_mode,
                "analysis_mode": config.analysis_mode,
                "feature_flags": config.feature_flags
            }
            # 敏感字段不写入文件
            if config.llm_api_key:
                env_data["llm_api_key"] = "***REDACTED***"
            data["environments"][env_name] = env_data

        os.makedirs(self.config_dir, exist_ok=True)

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def get_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        current = self.get_current_config()
        return {
            "current_environment": self.current_env,
            "available_environments": self.list_environments(),
            "llm_model": current.llm_model,
            "log_level": current.log_level,
            "analysis_mode": current.analysis_mode,
            "memory_mode": current.memory_mode
        }


def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    return ConfigManager()
