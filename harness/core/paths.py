"""
路径配置模块 - 解决硬编码路径问题
支持在任意目录运行项目

所有运行时产物统一归入 outputs/ 目录，按 workflowID 隔离，
方便清理和 .gitignore 管理，避免多工作流冲突
"""
import os
from pathlib import Path
from typing import Optional

# 项目根目录（根据当前文件位置自动计算）
# 这个文件在 harness/core/，所以项目根目录是 ../..
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

# 核心目录（源码/配置，应纳入版本管理）
CONFIG_DIR = PROJECT_ROOT / "config"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
DATA_DIR = PROJECT_ROOT / "data"

# 运行时产物目录（全部归入 outputs/，不纳入版本管理）
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_REPORTS_DIR = OUTPUTS_DIR / "reports"
OUTPUTS_STATE_DIR = OUTPUTS_DIR / "state"
OUTPUTS_INDEX_DIR = OUTPUTS_DIR / "index"        # 工作流索引目录
OUTPUTS_TEMP_DIR = OUTPUTS_DIR / "temp"         # 全局临时目录
OUTPUTS_LOGS_DIR = OUTPUTS_DIR / "logs"         # 应用日志
OUTPUTS_ANALYTICS_DIR = OUTPUTS_DIR / "analytics"  # 统计分析
OUTPUTS_CASE_LIBRARY_DIR = OUTPUTS_DIR / "case_library"  # 案例库
OUTPUTS_OPENVIKING_DIR = OUTPUTS_DIR / "openviking_data"  # OpenViking 记忆
OUTPUTS_TOKEN_STATS_DIR = OUTPUTS_DIR / "analytics"  # Token 统计（与 analytics 共用）
BUG_DATA_DIR = DATA_DIR / "bug_data"


class WorkflowPaths:
    """按 workflowID 隔离的路径管理器
    
    为每个工作流提供独立的临时目录、报告目录等，避免冲突
    """
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        
        # 工作流专属目录
        self.workflow_root = OUTPUTS_DIR / "workflows" / workflow_id
        self.temp_dir = self.workflow_root / "temp"           # 工作流临时文件（解压等）
        self.logs_dir = self.workflow_root / "logs"           # 工作流专属日志
        self.reports_dir = self.workflow_root / "reports"     # 工作流报告
        self.artifacts_dir = self.workflow_root / "artifacts" # 其他产物
        
    def ensure_dirs(self):
        """确保工作流所有目录存在"""
        dirs_to_create = [
            self.workflow_root,
            self.temp_dir,
            self.logs_dir,
            self.reports_dir,
            self.artifacts_dir,
        ]
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
        return self
    
    def cleanup(self):
        """清理工作流临时目录"""
        if self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
    
    # 便捷属性（字符串格式）
    @property
    def temp_dir_str(self) -> str:
        return str(self.temp_dir)
    
    @property
    def reports_dir_str(self) -> str:
        return str(self.reports_dir)


# 确保必要目录存在
def ensure_dirs():
    """确保所有必要的目录存在"""
    dirs_to_create = [
        OUTPUTS_DIR,
        OUTPUTS_REPORTS_DIR,
        OUTPUTS_STATE_DIR,
        OUTPUTS_INDEX_DIR,
        OUTPUTS_TEMP_DIR,
        OUTPUTS_LOGS_DIR,
        OUTPUTS_ANALYTICS_DIR,
        OUTPUTS_CASE_LIBRARY_DIR,
        OUTPUTS_OPENVIKING_DIR,
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
OUTPUTS_INDEX_DIR_STR = str(OUTPUTS_INDEX_DIR)
OUTPUTS_TEMP_DIR_STR = str(OUTPUTS_TEMP_DIR)
OUTPUTS_LOGS_DIR_STR = str(OUTPUTS_LOGS_DIR)
OUTPUTS_ANALYTICS_DIR_STR = str(OUTPUTS_ANALYTICS_DIR)
OUTPUTS_CASE_LIBRARY_DIR_STR = str(OUTPUTS_CASE_LIBRARY_DIR)
OUTPUTS_OPENVIKING_DIR_STR = str(OUTPUTS_OPENVIKING_DIR)
OUTPUTS_TOKEN_STATS_DIR_STR = str(OUTPUTS_TOKEN_STATS_DIR)
DATA_DIR_STR = str(DATA_DIR)
BUG_DATA_DIR_STR = str(BUG_DATA_DIR)
