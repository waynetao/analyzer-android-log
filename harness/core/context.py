"""
ContextEngine - Harness Engineering上下文引擎
精确管理Agent的上下文，对抗上下文稀缺，实现"地图而非百科全书"
"""
import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path

class ContextEngine:
    def __init__(self, project_root: str = None):
        # 自动计算项目根目录
        if project_root is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.project_root = Path(project_root)
        self.context_cache: Dict[str, Any] = {}
        self._load_static_context()
    
    def _load_static_context(self):
        """加载静态上下文文档（地图而非百科全书）"""
        # 1. 加载AGENTS.md（核心导航地图）
        agents_md = self.project_root / "AGENTS.md"
        if agents_md.exists():
            with open(agents_md, 'r', encoding='utf-8') as f:
                self.context_cache["agents_md"] = f.read()
        
        # 2. 加载配置文件
        config_dir = self.project_root / "config"
        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                with open(config_file, 'r', encoding='utf-8') as f:
                    key = f"config_{config_file.stem}"
                    self.context_cache[key] = yaml.safe_load(f)
    
    def get_core_context(self) -> str:
        """获取核心上下文（导航地图）"""
        core_parts = []
        
        if "agents_md" in self.context_cache:
            core_parts.append(self.context_cache["agents_md"])
        
        return "\n\n".join(core_parts)
    
    def get_relevant_context(self, query: str) -> Dict[str, Any]:
        """根据查询智能检索相关上下文"""
        context = {
            "core": self.get_core_context(),
            "relevant_configs": self._get_relevant_configs(query)
        }
        return context
    
    def _get_relevant_configs(self, query: str) -> Dict[str, Any]:
        """获取相关配置"""
        relevant = {}
        query_lower = query.lower()
        
        # 检查配置关键词
        for key, value in self.context_cache.items():
            if key.startswith("config_"):
                if "report" in query_lower and "report" in key:
                    relevant[key] = value
                elif "bug" in query_lower and "bug" in key:
                    relevant[key] = value
        
        return relevant
    
    def get_report_formats_config(self) -> Dict[str, Any]:
        """获取报告格式配置"""
        return self.context_cache.get("config_report_formats", {})
