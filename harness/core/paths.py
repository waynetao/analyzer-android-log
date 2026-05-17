"""
路径配置模块 - 解决硬编码路径问题
支持在任意目录运行项目
"""
import os
from pathlib import Path

# 项目根目录（根据当前文件位置自动计算）
# 这个文件在 harness/core/，所以项目根目录是 ../..
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

# 核心目录
CONFIG_DIR = PROJECT_ROOT / "config"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_REPORTS_DIR = OUTPUTS_DIR / "reports"
OUTPUTS_STATE_DIR = OUTPUTS_DIR / "state"
DATA_DIR = PROJECT_ROOT / "data"
BUG_DATA_DIR = DATA_DIR / "bug_data"

# 确保必要目录存在
def ensure_dirs():
    """确保所有必要的目录存在"""
    dirs_to_create = [
        OUTPUTS_DIR,
        OUTPUTS_REPORTS_DIR,
        OUTPUTS_STATE_DIR,
        BUG_DATA_DIR,
    ]
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

# 初始化目录
ensure_dirs()

# 导出为字符串，保持兼容性
PROJECT_ROOT_STR = str(PROJECT_ROOT)
CONFIG_DIR_STR = str(CONFIG_DIR)
KNOWLEDGE_BASE_DIR_STR = str(KNOWLEDGE_BASE_DIR)
OUTPUTS_DIR_STR = str(OUTPUTS_DIR)
OUTPUTS_REPORTS_DIR_STR = str(OUTPUTS_REPORTS_DIR)
OUTPUTS_STATE_DIR_STR = str(OUTPUTS_STATE_DIR)
DATA_DIR_STR = str(DATA_DIR)
BUG_DATA_DIR_STR = str(BUG_DATA_DIR)
