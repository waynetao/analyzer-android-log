"""
LogExtractionWithAloggrepSkill - 使用 aloggrep 进行日志提取和分析的技能
轻量级 Android logcat/xlog/HarmonyOS hilog 日志过滤与分析
"""
import os
import json
from typing import Dict, Any, List
from .base import BaseSkill, SkillResult
from log_analyzer.aloggrep_wrapper import ALogGrep, LogLevel
from log_analyzer.extractor.extractor import LogExtractor


class LogExtractionWithAloggrepSkill(BaseSkill):
    """使用 aloggrep 的日志提取和分析技能"""
    
    @property
    def name(self) -> str:
        return "log_extraction_aloggrep"
    
    def __init__(self, binary_path: str = "aloggrep"):
        """
        初始化技能
        
        Args:
            binary_path: aloggrep 可执行文件路径
        """
        self.aloggrep = ALogGrep(binary_path)
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["log_path"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        log_path = inputs["log_path"]
        use_aloggrep = inputs.get("use_aloggrep", True)
        
        try:
            # 1. 解压和提取日志文件
            extractor = LogExtractor()
            extract_dir = extractor.extract(log_path)
            
            # 找到实际的日志文件
            log_files = self._find_log_files(extract_dir)
            
            result = {
                "extraction_dir": extract_dir,
                "log_files": log_files,
                "use_aloggrep": use_aloggrep and self.aloggrep.is_available(),
                "aloggrep_available": self.aloggrep.is_available()
            }
            
            # 如果 aloggrep 可用且启用，进行快速分析
            if result["use_aloggrep"]:
                aloggrep_analysis = self._analyze_with_aloggrep(log_files)
                result.update(aloggrep_analysis)
            else:
                result["aloggrep_skipped"] = "aloggrep not available or disabled"
            
            return SkillResult(
                True,
                result,
                f"日志提取成功，aloggrep{'已' if result['use_aloggrep'] else '未'}使用"
            )
            
        except Exception as e:
            return SkillResult(
                False,
                {},
                f"日志提取失败: {str(e)}"
            )
    
    def _find_log_files(self, extract_dir: str) -> List[str]:
        """
        在提取目录中找到日志文件
        
        Args:
            extract_dir: 提取目录
            
        Returns:
            日志文件路径列表
        """
        log_files = []
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                # 常见的日志文件扩展名
                if file.endswith(('.log', '.txt', '.logcat', '.xlog')) or '.' not in file:
                    log_files.append(os.path.join(root, file))
        return log_files
    
    def _analyze_with_aloggrep(self, log_files: List[str]) -> Dict[str, Any]:
        """
        使用 aloggrep 分析日志文件
        
        Args:
            log_files: 日志文件列表
            
        Returns:
            分析结果
        """
        analysis = {
            "aloggrep_analysis": {},
            "all_crashes": [],
            "total_error_count": 0
        }
        
        for log_file in log_files:
            try:
                # 快速分析每个文件
                file_analysis = self.aloggrep.quick_analyze(log_file)
                analysis["aloggrep_analysis"][log_file] = file_analysis
                
                # 汇总崩溃信息
                if file_analysis.get("crashes"):
                    for crash in file_analysis["crashes"]:
                        crash["source_file"] = log_file
                        analysis["all_crashes"].append(crash)
                
                # 汇总错误计数
                analysis["total_error_count"] += file_analysis.get("error_count", 0)
                
            except Exception as e:
                analysis["aloggrep_analysis"][log_file] = {
                    "error": str(e)
                }
        
        return analysis


class ALogGrepAnalysisSkill(BaseSkill):
    """使用 aloggrep 进行高级分析的技能"""
    
    @property
    def name(self) -> str:
        return "aloggrep_analysis"
    
    def __init__(self, binary_path: str = "aloggrep"):
        """
        初始化技能
        
        Args:
            binary_path: aloggrep 可执行文件路径
        """
        self.aloggrep = ALogGrep(binary_path)
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["log_path"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        log_path = inputs["log_path"]
        analysis_type = inputs.get("analysis_type", "quick")
        
        if not self.aloggrep.is_available():
            return SkillResult(False, {}, "aloggrep is not available")
        
        try:
            result = {}
            
            if analysis_type == "quick":
                result = self.aloggrep.quick_analyze(log_path)
            elif analysis_type == "summary":
                summary_result = self.aloggrep.summary(log_path)
                if summary_result["success"] and "data" in summary_result:
                    result = summary_result["data"]
            elif analysis_type == "crashes":
                crashes_result = self.aloggrep.crashes(log_path)
                if crashes_result["success"] and "data" in crashes_result:
                    result = {"crashes": crashes_result["data"]}
            elif analysis_type == "histogram":
                interval = inputs.get("interval", "1m")
                hist_result = self.aloggrep.histogram(log_path, interval)
                if hist_result["success"] and "data" in hist_result:
                    result = {"histogram": hist_result["data"]}
            elif analysis_type == "custom":
                # 自定义分析
                result = self._custom_analysis(inputs)
            else:
                return SkillResult(False, {}, f"Unknown analysis type: {analysis_type}")
            
            result["analysis_type"] = analysis_type
            
            return SkillResult(
                True,
                result,
                f"aloggrep 分析完成: {analysis_type}"
            )
            
        except Exception as e:
            return SkillResult(
                False,
                {},
                f"aloggrep 分析失败: {str(e)}"
            )
    
    def _custom_analysis(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        自定义分析
        
        Args:
            inputs: 输入参数
            
        Returns:
            分析结果
        """
        log_path = inputs["log_path"]
        result = {}
        
        # 过滤条件
        filter_kwargs = {}
        if "tags" in inputs:
            filter_kwargs["tags"] = inputs["tags"]
        if "level" in inputs:
            filter_kwargs["level"] = LogLevel(inputs["level"])
        if "message" in inputs:
            filter_kwargs["message"] = inputs["message"]
        if "limit" in inputs:
            filter_kwargs["limit"] = inputs["limit"]
        
        # 执行过滤
        if filter_kwargs:
            filter_result = self.aloggrep.filter(
                log_path,
                format="json",
                **filter_kwargs
            )
            if filter_result["success"]:
                result["filtered_logs"] = filter_result["stdout"]
                try:
                    # 尝试解析 JSON
                    result["filtered_data"] = [
                        json.loads(line) 
                        for line in filter_result["stdout"].strip().split("\n") 
                        if line
                    ]
                except json.JSONDecodeError:
                    pass
        
        # 布尔表达式过滤
        if "expr" in inputs:
            expr_result = self.aloggrep.filter_expr(
                log_path,
                inputs["expr"],
                limit=inputs.get("limit"),
                format="json"
            )
            if expr_result["success"]:
                result["expr_result"] = expr_result["stdout"]
        
        return result


class ALogGrepFilterSkill(BaseSkill):
    """使用 aloggrep 进行日志过滤的技能"""
    
    @property
    def name(self) -> str:
        return "aloggrep_filter"
    
    def __init__(self, binary_path: str = "aloggrep"):
        """
        初始化技能
        
        Args:
            binary_path: aloggrep 可执行文件路径
        """
        self.aloggrep = ALogGrep(binary_path)
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["log_path"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        log_path = inputs["log_path"]
        
        if not self.aloggrep.is_available():
            return SkillResult(False, {}, "aloggrep is not available")
        
        try:
            # 从输入中获取过滤参数
            filter_kwargs = {}
            
            if "tags" in inputs:
                filter_kwargs["tags"] = inputs["tags"]
            if "level" in inputs:
                filter_kwargs["level"] = LogLevel(inputs["level"])
            if "message" in inputs:
                filter_kwargs["message"] = inputs["message"]
            if "pid" in inputs:
                filter_kwargs["pid"] = inputs["pid"]
            if "tid" in inputs:
                filter_kwargs["tid"] = inputs["tid"]
            if "since" in inputs:
                filter_kwargs["since"] = inputs["since"]
            if "until" in inputs:
                filter_kwargs["until"] = inputs["until"]
            if "limit" in inputs:
                filter_kwargs["limit"] = inputs["limit"]
            if "fields" in inputs:
                filter_kwargs["fields"] = inputs["fields"]
            if "use_and" in inputs:
                filter_kwargs["use_and"] = inputs["use_and"]
            
            # 输出格式
            output_format = inputs.get("format", "text")
            filter_kwargs["format"] = output_format
            
            # 执行过滤
            result = self.aloggrep.filter(log_path, **filter_kwargs)
            
            output = {
                "filtered_output": result["stdout"],
                "stderr": result["stderr"],
                "returncode": result["returncode"],
                "success": result["success"],
                "filter_params": filter_kwargs
            }
            
            # 如果是 JSON 格式，尝试解析
            if output_format == "json" and result["stdout"].strip():
                try:
                    output["parsed_data"] = [
                        json.loads(line) 
                        for line in result["stdout"].strip().split("\n") 
                        if line
                    ]
                except json.JSONDecodeError:
                    pass
            
            return SkillResult(
                True,
                output,
                "日志过滤完成"
            )
            
        except Exception as e:
            return SkillResult(
                False,
                {},
                f"日志过滤失败: {str(e)}"
            )
