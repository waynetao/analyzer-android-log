"""
BaseBugAnalyzer - Bug类型分析器基类
提示词模板和共享逻辑
"""
from typing import Dict, Any, Optional
from enum import Enum


class BugType(Enum):
    """Bug类型枚举"""
    UNKNOWN = "unknown"
    CRASH = "crash"
    ANR = "anr"
    MEMORY_LEAK = "memory_leak"
    PERFORMANCE = "performance"
    NETWORK = "network"
    POWER = "power"
    GENERAL = "general"


class BaseBugAnalyzer:
    """Bug分析器基类"""
    
    @property
    def name(self) -> str:
        """分析器名称"""
        raise NotImplementedError
    
    @property
    def bug_type(self) -> BugType:
        """支持的Bug类型"""
        raise NotImplementedError
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        raise NotImplementedError
    
    def get_user_prompt(self, bug_desc: Dict, log_analysis: Dict) -> str:
        """获取用户提示词"""
        raise NotImplementedError
    
    def format_output(self, analysis: str) -> str:
        """格式化输出"""
        raise NotImplementedError
    
    def detect(self, log_analysis: Dict) -> bool:
        """检测是否适用"""
        raise NotImplementedError


class PromptTemplateManager:
    """
    提示词模板管理器
    """
    
    @staticmethod
    def get_analyzer(bug_type: BugType) -> Optional[BaseBugAnalyzer]:
        """根据Bug类型获取对应的分析器"""
        from .crash_analyzer import CrashAnalyzer
        from .anr_analyzer import ANRAnalyzer
        from .memory_analyzer import MemoryAnalyzer
        from .other_analyzers import PerformanceAnalyzer, NetworkAnalyzer, PowerAnalyzer
        
        analyzers = {
            BugType.CRASH: CrashAnalyzer(),
            BugType.ANR: ANRAnalyzer(),
            BugType.MEMORY_LEAK: MemoryAnalyzer(),
            BugType.PERFORMANCE: PerformanceAnalyzer(),
            BugType.NETWORK: NetworkAnalyzer(),
            BugType.POWER: PowerAnalyzer(),
        }
        
        return analyzers.get(bug_type)
    
    @staticmethod
    def detect_bug_type(log_analysis: Dict) -> BugType:
        """
        智能检测Bug类型
        基于日志分析结果
        """
        from .crash_analyzer import CrashAnalyzer
        from .anr_analyzer import ANRAnalyzer
        from .memory_analyzer import MemoryAnalyzer
        from .other_analyzers import PerformanceAnalyzer, NetworkAnalyzer, PowerAnalyzer
        
        analyzers = [
            CrashAnalyzer(),
            ANRAnalyzer(),
            MemoryAnalyzer(),
            PerformanceAnalyzer(),
            NetworkAnalyzer(),
            PowerAnalyzer(),
        ]
        
        for analyzer in analyzers:
            if analyzer.detect(log_analysis):
                return analyzer.bug_type
        
        return BugType.GENERAL
