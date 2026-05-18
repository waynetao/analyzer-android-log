"""
统一日志系统 - 提供标准化的日志配置和工具

特性：
1. 统一的日志格式
2. 支持控制台和文件输出
3. 日志级别可配置
4. 结构化日志支持（JSON格式）
5. 支持日志轮转
6. 统一的日志上下文
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any


class LoggerManager:
    """日志管理器 - 提供统一的日志配置和获取接口"""
    
    _initialized = False
    _log_level = logging.INFO
    
    @classmethod
    def initialize(
        cls,
        log_level: str = "INFO",
        log_dir: str = None,
        enable_file: bool = True,
        enable_console: bool = True,
        json_format: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        初始化日志系统
        
        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: 日志文件目录
            enable_file: 是否启用文件日志
            enable_console: 是否启用控制台日志
            json_format: 是否使用JSON格式
            max_file_size: 单个日志文件最大大小（字节）
            backup_count: 保留的日志文件数量
        """
        if cls._initialized:
            return
        
        # 设置日志级别
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        cls._log_level = level_map.get(log_level.upper(), logging.INFO)
        
        # 构建日志配置
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {},
            "handlers": {},
            "loggers": {
                "": {
                    "level": cls._log_level,
                    "handlers": [],
                    "propagate": True
                }
            }
        }
        
        # 添加格式化器
        if json_format:
            config["formatters"]["standard"] = {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d"
            }
        else:
            config["formatters"]["standard"] = {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        
        config["formatters"]["simple"] = {
            "format": "%(asctime)s [%(levelname)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
        
        # 添加控制台处理器
        if enable_console:
            config["handlers"]["console"] = {
                "class": "logging.StreamHandler",
                "level": cls._log_level,
                "formatter": "simple",
                "stream": sys.stdout
            }
            config["loggers"][""]["handlers"].append("console")
        
        # 添加文件处理器
        if enable_file and log_dir:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
            
            config["handlers"]["file"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": cls._log_level,
                "formatter": "standard",
                "filename": log_file,
                "maxBytes": max_file_size,
                "backupCount": backup_count,
                "encoding": "utf-8"
            }
            config["loggers"][""]["handlers"].append("file")
        
        # 应用配置
        logging.config.dictConfig(config)
        cls._initialized = True
        
        logger = logging.getLogger(__name__)
        logger.info(f"日志系统初始化完成 - 级别: {log_level}, 文件日志: {enable_file}, 控制台日志: {enable_console}")
    
    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称，默认为调用模块名称
        
        Returns:
            logging.Logger 实例
        """
        if not cls._initialized:
            cls.initialize()
        
        if name is None:
            import inspect
            caller_frame = inspect.stack()[1]
            name = caller_frame.filename.split('/')[-1].replace('.py', '')
        
        return logging.getLogger(name)


class LogContext:
    """日志上下文管理器 - 用于在日志中添加额外上下文信息"""
    
    def __init__(self, **kwargs):
        self.context = kwargs
    
    def __enter__(self):
        """进入上下文，设置日志上下文"""
        # 可以在这里添加上下文到日志记录
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文，清理日志上下文"""
        pass
    
    def add_context(self, **kwargs):
        """添加上下文信息"""
        self.context.update(kwargs)
    
    def get_context(self) -> Dict[str, Any]:
        """获取上下文信息"""
        return self.context


def setup_logging_from_env():
    """从环境变量读取日志配置并初始化"""
    from harness.core.paths import PROJECT_ROOT_STR, OUTPUTS_LOGS_DIR_STR
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    log_dir = os.environ.get("LOG_DIR", OUTPUTS_LOGS_DIR_STR)
    enable_file = os.environ.get("LOG_ENABLE_FILE", "true").lower() == "true"
    enable_console = os.environ.get("LOG_ENABLE_CONSOLE", "true").lower() == "true"
    json_format = os.environ.get("LOG_JSON_FORMAT", "false").lower() == "true"
    
    LoggerManager.initialize(
        log_level=log_level,
        log_dir=log_dir,
        enable_file=enable_file,
        enable_console=enable_console,
        json_format=json_format
    )


# 全局便捷函数
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """便捷函数：获取日志记录器"""
    return LoggerManager.get_logger(name)


def log_method_call(func):
    """装饰器：记录方法调用（过滤敏感参数）"""
    _SENSITIVE_KEYS = {"api_key", "secret", "password", "token", "llm_api_key", "openai_api_key"}

    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        class_name = args[0].__class__.__name__ if args else ""
        # 过滤敏感参数值
        safe_kwargs = {
            k: ("***" if any(s in k.lower() for s in _SENSITIVE_KEYS) else v)
            for k, v in kwargs.items()
        }
        logger.debug(f"调用: {class_name}.{func.__name__}(args=..., kwargs={safe_kwargs})")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"完成: {class_name}.{func.__name__} -> {type(result).__name__}")
            return result
        except Exception as e:
            logger.error(f"失败: {class_name}.{func.__name__} -> {type(e).__name__}: {e}", exc_info=True)
            raise
    return wrapper


# 初始化默认日志配置
try:
    setup_logging_from_env()
except Exception as e:
    # 如果初始化失败，使用简单配置
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.warning(f"日志系统初始化失败，使用默认配置: {e}")