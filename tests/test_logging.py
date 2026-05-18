"""
日志系统单元测试
测试统一日志系统的各个组件
"""

import pytest
import os
import tempfile
import logging
from datetime import datetime

from harness.core.logging import (
    LoggerManager,
    LogContext,
    get_logger,
    setup_logging_from_env
)


class TestLoggerManager:
    """日志管理器测试"""

    def test_initialize_with_defaults(self):
        """测试默认初始化"""
        LoggerManager._initialized = False  # 重置状态
        LoggerManager.initialize(
            log_level="INFO",
            log_dir=None,
            enable_file=False,
            enable_console=True
        )

        assert LoggerManager._initialized is True
        assert LoggerManager._log_level == logging.INFO

    def test_initialize_idempotent(self):
        """测试初始化幂等性"""
        LoggerManager._initialized = True
        LoggerManager.initialize()  # 应该直接返回

        assert LoggerManager._initialized is True

    def test_get_logger(self):
        """测试获取日志记录器"""
        LoggerManager._initialized = False
        LoggerManager.initialize(enable_console=True, enable_file=False)

        logger = LoggerManager.get_logger("test_module")
        assert logger is not None
        assert logger.name == "test_module"

    def test_get_logger_auto_name(self):
        """测试自动命名"""
        LoggerManager._initialized = False
        LoggerManager.initialize(enable_console=True, enable_file=False)

        logger = LoggerManager.get_logger()
        assert logger is not None


class TestLogContext:
    """日志上下文测试"""

    def test_context_initialization(self):
        """测试上下文初始化"""
        context = LogContext(user_id="123", action="test")
        assert context.context["user_id"] == "123"
        assert context.context["action"] == "test"

    def test_add_context(self):
        """测试添加上下文"""
        context = LogContext(user_id="123")
        context.add_context(action="test", result="success")

        assert context.context["user_id"] == "123"
        assert context.context["action"] == "test"
        assert context.context["result"] == "success"

    def test_get_context(self):
        """测试获取上下文"""
        context = LogContext(user_id="123", action="test")
        retrieved = context.get_context()

        assert retrieved == {"user_id": "123", "action": "test"}

    def test_context_manager(self):
        """测试上下文管理器"""
        with LogContext(user_id="456") as ctx:
            assert ctx.context["user_id"] == "456"


class TestGetLogger:
    """get_logger 便捷函数测试"""

    def test_get_logger_function(self):
        """测试便捷函数"""
        LoggerManager._initialized = False
        LoggerManager.initialize(enable_console=True, enable_file=False)

        logger = get_logger("test_function")
        assert logger is not None
        assert logger.name == "test_function"


class TestSetupLoggingFromEnv:
    """环境变量配置测试"""

    def test_setup_with_env_vars(self, monkeypatch):
        """测试从环境变量读取配置"""
        LoggerManager._initialized = False

        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("LOG_ENABLE_FILE", "false")
        monkeypatch.setenv("LOG_ENABLE_CONSOLE", "true")

        # 创建临时目录用于测试
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv("LOG_DIR", tmpdir)
            setup_logging_from_env()

            assert LoggerManager._initialized is True
            assert LoggerManager._log_level == logging.DEBUG
