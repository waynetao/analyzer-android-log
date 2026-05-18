"""
CLI 模块单元测试
测试 scripts/cli.py 中的 load_bug_text 和命令分发等功能
"""

import pytest
import os
import json
import tempfile
from unittest.mock import MagicMock, patch


from scripts.cli import load_bug_text


class TestLoadBugText:
    """load_bug_text 函数测试"""

    def test_load_from_file(self, tmp_path):
        """从文件加载 bug 描述"""
        bug_file = tmp_path / "bug.txt"
        bug_file.write_text("应用在启动时崩溃", encoding="utf-8")
        result = load_bug_text(str(bug_file))
        assert result == "应用在启动时崩溃"

    def test_load_from_direct_text(self):
        """直接传入文本"""
        result = load_bug_text("应用ANR无响应")
        assert result == "应用ANR无响应"

    def test_load_nonexistent_file_returns_text(self):
        """不存在的文件路径直接作为文本返回"""
        text = "/nonexistent/path/to/bug.txt"
        result = load_bug_text(text)
        assert result == text

    def test_load_empty_file(self, tmp_path):
        """加载空文件"""
        bug_file = tmp_path / "empty.txt"
        bug_file.write_text("", encoding="utf-8")
        result = load_bug_text(str(bug_file))
        assert result == ""

    def test_load_file_with_special_chars(self, tmp_path):
        """加载含特殊字符的文件"""
        bug_file = tmp_path / "special.txt"
        bug_file.write_text("崩溃 @#$% 中文测试 🎉", encoding="utf-8")
        result = load_bug_text(str(bug_file))
        assert "崩溃" in result
        assert "🎉" in result


class TestCLIParsing:
    """CLI 参数解析测试"""

    def test_full_command_args(self):
        """测试 full 命令参数解析"""
        import argparse
        from scripts.cli import _add_full_subparser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        _add_full_subparser(subparsers)

        args = parser.parse_args(["full", "--bug", "test_bug", "--log", "/tmp/test.log"])
        assert args.bug == "test_bug"
        assert args.log == "/tmp/test.log"
        assert args.format == "markdown"

    def test_plan_command_args(self):
        """测试 plan 命令参数解析"""
        import argparse
        from scripts.cli import _add_plan_subparser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        _add_plan_subparser(subparsers)

        args = parser.parse_args(["plan", "--bug", "bug.txt", "--log", "test.log"])
        assert args.command == "plan"
        assert args.bug == "bug.txt"
        assert args.name == "bug_analysis"

    def test_build_command_args(self):
        """测试 build 命令参数解析"""
        import argparse
        from scripts.cli import _add_build_subparser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        _add_build_subparser(subparsers)

        args = parser.parse_args(["build", "--workflow-id", "wf_123"])
        assert args.command == "build"
        assert args.workflow_id == "wf_123"

    def test_skill_list_flag(self):
        """测试 skill --list 参数"""
        import argparse
        from scripts.cli import _add_skill_subparser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        _add_skill_subparser(subparsers)

        args = parser.parse_args(["skill", "--list"])
        assert args.list is True

    def test_status_requires_workflow_id(self):
        """测试 status 命令需要 workflow-id"""
        import argparse
        from scripts.cli import _add_status_subparser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        _add_status_subparser(subparsers)

        args = parser.parse_args(["status", "--workflow-id", "wf_456"])
        assert args.workflow_id == "wf_456"


class TestDispatchCommand:
    """命令分发测试"""

    def test_unknown_command_shows_help(self, capsys):
        """未知命令不触发任何 handler"""
        from scripts.cli import _dispatch_command

        mock_agent = MagicMock()
        mock_args = MagicMock()
        mock_args.command = "nonexistent"
        # _dispatch_command 对未知命令不做任何事
        _dispatch_command(mock_args, mock_agent)
        mock_agent.full_analysis.assert_not_called()

    def test_full_handler_calls_full_analysis(self):
        """full 命令调用 full_analysis"""
        from scripts.cli import _handle_full

        mock_agent = MagicMock()
        mock_args = MagicMock()
        mock_args.bug = "test bug"
        mock_args.log = "/tmp/test.log"
        mock_args.format = "markdown"

        _handle_full(mock_args, mock_agent)
        mock_agent.full_analysis.assert_called_once_with("test bug", "/tmp/test.log", "markdown")

    def test_plan_handler_calls_orchestrator_plan(self):
        """plan 命令调用 orchestrator.plan"""
        from scripts.cli import _handle_plan

        mock_agent = MagicMock()
        mock_args = MagicMock()
        mock_args.bug = "test bug"
        mock_args.log = "/tmp/test.log"
        mock_args.format = "markdown"
        mock_args.name = "test_workflow"

        _handle_plan(mock_args, mock_agent)
        mock_agent.orchestrator.plan.assert_called_once()

    def test_skill_list_handler(self, capsys):
        """skill --list 列出可用技能"""
        from scripts.cli import _handle_skill

        mock_agent = MagicMock()
        mock_agent.get_available_skills.return_value = ["skill_a", "skill_b"]
        mock_args = MagicMock()
        mock_args.list = True
        mock_args.name = None

        _handle_skill(mock_args, mock_agent)
        captured = capsys.readouterr()
        assert "skill_a" in captured.out
        assert "skill_b" in captured.out
