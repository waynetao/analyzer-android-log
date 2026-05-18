"""
测试配置文件
pytest 配置和 fixtures
"""

import os
import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("LOG_ENABLE_FILE", "false")
os.environ.setdefault("LOG_ENABLE_CONSOLE", "false")


@pytest.fixture
def sample_bug_description():
    """示例 Bug 描述"""
    return {
        "raw_text": "应用在启动时崩溃，包名：com.example.app，版本：1.0.0",
        "summary": "应用在启动时崩溃",
        "keywords": ["crash", "崩溃", "启动"],
        "package_name": "com.example.app",
        "app_version": "1.0.0",
        "android_version": "13",
        "device_model": "Pixel 6",
        "time_points": ["11:25", "11:27"],
        "reproduction_steps": ["打开应用", "点击主界面按钮", "应用崩溃"],
        "user_scenarios": ["正常使用应用启动流程"],
        "expected_behavior": "应用正常启动并显示主界面",
        "actual_behavior": "应用启动时立即崩溃",
        "frequency": "每次启动必现",
        "severity": "critical"
    }


@pytest.fixture
def sample_log_entries():
    """示例日志条目"""
    return [
        {
            "timestamp": "01-01 12:00:00.000",
            "pid": 1234,
            "tid": 5678,
            "level": "F",
            "tag": "AndroidRuntime",
            "message": "FATAL EXCEPTION: main",
            "type": "crash"
        },
        {
            "timestamp": "01-01 12:00:01.000",
            "pid": 1234,
            "tid": 5678,
            "level": "E",
            "tag": "AndroidRuntime",
            "message": "java.lang.NullPointerException",
            "type": "exception"
        },
        {
            "timestamp": "01-01 12:00:02.000",
            "pid": 1000,
            "tid": 1000,
            "level": "W",
            "tag": "ActivityManager",
            "message": "ANR in com.example.app",
            "type": "anr"
        }
    ]


@pytest.fixture
def temp_output_dir(tmp_path):
    """临时输出目录"""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return str(output_dir)


@pytest.fixture
def temp_state_dir(tmp_path):
    """临时状态目录"""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return str(state_dir)


@pytest.fixture
def temp_analytics_dir(tmp_path):
    """临时统计分析目录"""
    analytics_dir = tmp_path / "analytics"
    analytics_dir.mkdir()
    return str(analytics_dir)


@pytest.fixture
def sample_workflow_inputs(sample_bug_description, tmp_path):
    """示例工作流输入"""
    # 创建临时日志文件
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "test.log"
    log_file.write_text("01-01 12:00:00.000 1234 5678 F AndroidRuntime: FATAL EXCEPTION\n")

    return {
        "bug_description": sample_bug_description,
        "log_path": str(log_dir),
        "output_format": "markdown",
        "analysis_mode": "standard"
    }
