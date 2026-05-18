#!/usr/bin/env python3
"""
Harness Android Log Analysis Agent
基于Harness Engineering架构的AI Agent
完整的Plan-Build-Verify-Fix工作流
"""
# 重要：必须在所有 import 之前设置路径
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# 加载 .env 文件（从项目根目录加载）
from dotenv import load_dotenv
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path, override=True)
print(f"📄 从 {dotenv_path} 加载 .env 文件")

import argparse
from datetime import datetime

# 导入Harness系统
from harness.core import ContextEngine, StateManager, Orchestrator
from harness.skills import LogExtractionSkill, BugAnalysisSkill, ReportGenerationSkill
from harness.policies import ValidationPolicy, QualityPolicy, FormatPolicy
from log_analyzer.llm.bug_description_parser import BugDescriptionParser
from log_analyzer.llm.llm_client import LLMClient

class AndroidLogAgent:
    """Android日志分析Agent - Harness架构实现"""
    
    def __init__(self):
        print("="*60)
        print("Android 日志分析 AI Agent (Harness Engineering)")
        print("="*60)
        
        # 1. 初始化Harness核心组件
        self.context_engine = ContextEngine()
        self.state_manager = StateManager()
        self.orchestrator = Orchestrator(self.context_engine, self.state_manager)
        
        # 2. 注册可插拔技能
        self._register_skills()
        
        # 3. 注册策略
        self._register_policies()
    
    def _register_skills(self):
        """注册可插拔的技能"""
        self.orchestrator.register_skill(LogExtractionSkill())
        self.orchestrator.register_skill(BugAnalysisSkill())
        self.orchestrator.register_skill(ReportGenerationSkill())
    
    def _register_policies(self):
        """注册约束和验证策略"""
        self.orchestrator.register_policy(ValidationPolicy())
        self.orchestrator.register_policy(QualityPolicy())
        self.orchestrator.register_policy(FormatPolicy())
    
    def process_bug(self, bug_text: str, log_path: str, output_format: str = "markdown"):
        """处理bug的完整工作流"""
        print(f"\n📝 解析bug描述...")
        
        # 解析bug描述
        bug_desc = self._parse_bug_description(bug_text)
        
        # 准备输入
        inputs = {
            "bug_description": bug_desc,
            "log_path": log_path,
            "output_format": output_format
        }
        
        # 执行完整的Plan-Build-Verify-Fix工作流
        print(f"\n🚀 启动Harness工作流...")
        result = self.orchestrator.execute_workflow("bug_analysis", inputs)
        
        return result
    
    def _parse_bug_description(self, bug_text: str):
        """解析bug描述（使用规则而非LLM，确保可靠性）"""
        # 使用规则解析
        desc = {
            "raw_text": bug_text,
            "summary": bug_text[:100] + "..." if len(bug_text) > 100 else bug_text,
            "keywords": []
        }
        
        # 简单的规则提取
        if "crash" in bug_text.lower() or "崩溃" in bug_text:
            desc["keywords"].append("crash")
        if "anr" in bug_text.lower() or "无响应" in bug_text:
            desc["keywords"].append("anr")
        
        return desc


def main():
    parser = argparse.ArgumentParser(
        description="Android 日志分析 AI Agent (Harness Engineering)"
    )
    parser.add_argument(
        "--bug", "-b", required=True,
        help="Bug描述文本或文件"
    )
    parser.add_argument(
        "--log", "-l", required=True,
        help="日志文件/目录路径"
    )
    parser.add_argument(
        "--format", "-f", default="markdown",
        choices=["markdown", "html", "json", "all"],
        help="输出格式"
    )
    
    args = parser.parse_args()
    
    # 读取bug描述
    bug_text = args.bug
    if os.path.exists(args.bug):
        with open(args.bug, 'r', encoding='utf-8') as f:
            bug_text = f.read()
    
    # 运行Agent
    agent = AndroidLogAgent()
    result = agent.process_bug(
        bug_text=bug_text,
        log_path=args.log,
        output_format=args.format
    )
    
    # 输出结果
    print("\n" + "="*60)
    print("✅ 处理完成!")
    print("="*60)
    print(f"报告保存在: {os.path.abspath('outputs/reports')}")


if __name__ == "__main__":
    main()
