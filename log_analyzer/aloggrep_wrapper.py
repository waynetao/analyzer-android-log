"""
aloggrep 包装器 - 提供 Python 接口调用 aloggrep CLI 工具
轻量级 Android logcat/xlog/HarmonyOS hilog 日志过滤与分析
"""
import subprocess
import json
import os
from typing import List, Dict, Any, Optional
from enum import Enum


class LogLevel(Enum):
    """日志级别"""
    V = "V"  # Verbose
    D = "D"  # Debug
    I = "I"  # Info
    W = "W"  # Warning
    E = "E"  # Error
    F = "F"  # Fatal


class ALogGrep:
    """aloggrep CLI 工具包装器"""
    
    def __init__(self, binary_path: str = "aloggrep"):
        """
        初始化 ALogGrep 包装器
        
        Args:
            binary_path: aloggrep 可执行文件路径，默认从 PATH 中查找
        """
        self.binary_path = binary_path
        self._check_available()
    
    def _check_available(self):
        """检查 aloggrep 是否可用"""
        try:
            result = subprocess.run(
                [self.binary_path, "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            self.available = result.returncode in [0, 1]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.available = False
    
    def is_available(self) -> bool:
        """检查 aloggrep 是否可用"""
        return self.available
    
    def _run_command(self, args: List[str]) -> Dict[str, Any]:
        """
        运行 aloggrep 命令
        
        Args:
            args: 命令参数列表
            
        Returns:
            包含输出、错误、返回码的字典
        """
        cmd = [self.binary_path] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode in [0, 1]
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": 124,
                "success": False
            }
    
    def filter(
        self,
        log_path: str,
        tags: Optional[List[str]] = None,
        level: Optional[LogLevel] = None,
        message: Optional[str] = None,
        pid: Optional[int] = None,
        tid: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: Optional[int] = None,
        fields: Optional[List[str]] = None,
        use_and: bool = False,
        format: str = "text"
    ) -> Dict[str, Any]:
        """
        过滤日志
        
        Args:
            log_path: 日志文件路径或目录
            tags: 标签列表
            level: 最低日志级别
            message: 消息关键词
            pid: 进程 ID
            tid: 线程 ID
            since: 起始时间
            until: 结束时间
            limit: 限制输出数量
            fields: 输出字段列表
            use_and: 多条件使用 AND 而非 OR
            format: 输出格式 (text/json/csv)
            
        Returns:
            过滤结果
        """
        args = []
        
        # 文件或管道输入
        if log_path:
            args.extend(["-f", log_path])
        
        # 标签过滤
        if tags:
            for tag in tags:
                args.extend(["--tag", tag])
            if use_and and len(tags) > 1:
                args.append("--and")
        
        # 级别过滤
        if level:
            args.extend(["--level", level.value])
        
        # 消息过滤
        if message:
            args.extend(["--msg", message])
        
        # PID/TID 过滤
        if pid:
            args.extend(["--pid", str(pid)])
        if tid:
            args.extend(["--tid", str(tid)])
        
        # 时间范围
        if since:
            args.extend(["--since", since])
        if until:
            args.extend(["--until", until])
        
        # 输出限制
        if limit:
            args.extend(["--limit", str(limit)])
        
        # 字段选择
        if fields:
            args.extend(["--fields", ",".join(fields)])
        
        # 输出格式
        args.extend(["--format", format])
        
        return self._run_command(args)
    
    def filter_expr(self, log_path: str, expr: str, limit: Optional[int] = None, format: str = "text") -> Dict[str, Any]:
        """
        使用布尔表达式过滤
        
        Args:
            log_path: 日志文件路径
            expr: 布尔表达式，如 'msg ~ timeout and tag ~ OkHttp'
            limit: 限制输出数量
            format: 输出格式
            
        Returns:
            过滤结果
        """
        args = ["-f", log_path, "-e", expr]
        if limit:
            args.extend(["--limit", str(limit)])
        args.extend(["--format", format])
        return self._run_command(args)
    
    def summary(self, log_path: str) -> Dict[str, Any]:
        """
        生成日志摘要
        
        Args:
            log_path: 日志文件路径
            
        Returns:
            摘要信息 (JSON)
        """
        result = self._run_command(["-f", log_path, "--summary", "--format", "json"])
        if result["success"] and result["stdout"]:
            try:
                result["data"] = json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return result
    
    def histogram(self, log_path: str, interval: str = "1m") -> Dict[str, Any]:
        """
        生成时间分布直方图
        
        Args:
            log_path: 日志文件路径
            interval: 时间间隔，如 1m/5m/1h
            
        Returns:
            直方图数据 (JSON)
        """
        result = self._run_command(["-f", log_path, "--histogram", interval, "--format", "json"])
        if result["success"] and result["stdout"]:
            try:
                result["data"] = json.loads(result["stdout"])
            except json.JSONDecodeError:
                pass
        return result
    
    def crashes(self, log_path: str) -> Dict[str, Any]:
        """
        提取崩溃信息
        
        Args:
            log_path: 日志文件路径
            
        Returns:
            崩溃信息 (JSON)
        """
        result = self._run_command(["-f", log_path, "--crashes", "--format", "json"])
        if result["success"] and result["stdout"]:
            try:
                # aloggrep 的 --crashes 输出是 JSON 行格式
                crashes = []
                for line in result["stdout"].strip().split("\n"):
                    if line:
                        crashes.append(json.loads(line))
                result["data"] = crashes
            except json.JSONDecodeError:
                result["data"] = []
        return result
    
    def dedupe(self, log_path: str, limit: int = 20) -> Dict[str, Any]:
        """
        去重归并日志
        
        Args:
            log_path: 日志文件路径
            limit: 返回数量限制
            
        Returns:
            去重结果
        """
        args = ["-f", log_path, "--dedupe", "--limit", str(limit), "--format", "json"]
        result = self._run_command(args)
        return result
    
    def context(
        self,
        log_path: str,
        tag: Optional[str] = None,
        level: Optional[LogLevel] = None,
        lines: int = 3,
        time_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取上下文日志
        
        Args:
            log_path: 日志文件路径
            tag: 标签过滤
            level: 级别过滤
            lines: 前后行数
            time_context: 时间上下文，如 5s
            
        Returns:
            上下文日志
        """
        args = ["-f", log_path]
        
        if tag:
            args.extend(["--tag", tag])
        if level:
            args.extend(["--level", level.value])
        
        if time_context:
            args.extend(["--time-context", time_context])
        else:
            args.extend(["-C", str(lines)])
        
        return self._run_command(args)
    
    def tail(self, log_path: str, n: int = 50) -> Dict[str, Any]:
        """
        获取最后 N 条日志
        
        Args:
            log_path: 日志文件路径
            n: 条数
            
        Returns:
            日志内容
        """
        return self._run_command(["-f", log_path, "--tail", str(n)])
    
    def sample(self, log_path: str, n: int = 100) -> Dict[str, Any]:
        """
        抽样日志
        
        Args:
            log_path: 日志文件路径
            n: 抽样数量
            
        Returns:
            抽样结果
        """
        return self._run_command(["-f", log_path, "--sample", str(n)])
    
    def merge_multiline(self, log_path: str, tag: Optional[str] = None) -> Dict[str, Any]:
        """
        合并多行日志（如堆栈追踪）
        
        Args:
            log_path: 日志文件路径
            tag: 标签过滤
            
        Returns:
            合并后的日志
        """
        args = ["-f", log_path, "-M"]
        if tag:
            args.extend(["--tag", tag])
        return self._run_command(args)
    
    def sort_time(self, log_pattern: str) -> Dict[str, Any]:
        """
        多文件按时间归并排序
        
        Args:
            log_pattern: 文件模式，如 'logs/*.log'
            
        Returns:
            排序后的日志
        """
        return self._run_command(["-f", log_pattern, "--sort-time"])
    
    def count(self, log_path: str, **kwargs) -> int:
        """
        统计匹配的日志数量
        
        Args:
            log_path: 日志文件路径
            **kwargs: 过滤条件，同 filter 方法
            
        Returns:
            匹配数量
        """
        args = ["-f", log_path, "--count"]
        
        # 添加过滤条件
        if "tags" in kwargs and kwargs["tags"]:
            for tag in kwargs["tags"]:
                args.extend(["--tag", tag])
            if kwargs.get("use_and") and len(kwargs["tags"]) > 1:
                args.append("--and")
        
        if "level" in kwargs and kwargs["level"]:
            args.extend(["--level", kwargs["level"].value])
        
        if "message" in kwargs and kwargs["message"]:
            args.extend(["--msg", kwargs["message"]])
        
        result = self._run_command(args)
        if result["success"] and result["stdout"].strip():
            try:
                return int(result["stdout"].strip())
            except ValueError:
                pass
        return 0
    
    def quick_analyze(self, log_path: str) -> Dict[str, Any]:
        """
        快速分析日志（一站式获取摘要、崩溃、直方图）
        
        Args:
            log_path: 日志文件路径
            
        Returns:
            综合分析结果
        """
        analysis = {
            "available": self.available,
            "summary": None,
            "crashes": [],
            "histogram": None,
            "error_count": 0
        }
        
        if not self.available:
            return analysis
        
        # 获取摘要
        summary_result = self.summary(log_path)
        if summary_result["success"] and "data" in summary_result:
            analysis["summary"] = summary_result["data"]
        
        # 获取崩溃
        crashes_result = self.crashes(log_path)
        if crashes_result["success"] and "data" in crashes_result:
            analysis["crashes"] = crashes_result["data"]
        
        # 获取直方图
        hist_result = self.histogram(log_path)
        if hist_result["success"] and "data" in hist_result:
            analysis["histogram"] = hist_result["data"]
        
        # 统计错误数量
        analysis["error_count"] = self.count(log_path, level=LogLevel.E)
        
        return analysis
