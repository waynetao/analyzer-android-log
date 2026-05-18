"""
AloggrepWorkflowSkill - 四阶段日志分析工作流
基于aloggrep工具的智能分析流程
"""
import json
from typing import Dict, Any, List, Optional
from .base import BaseSkill, SkillResult
from log_analyzer.aloggrep_wrapper import ALogGrep, LogLevel


class AloggrepWorkflowSkill(BaseSkill):
    """四阶段日志分析工作流技能"""
    
    @property
    def name(self) -> str:
        return "aloggrep_workflow"
    
    def __init__(self, binary_path: str = "aloggrep"):
        """
        初始化工作流技能
        
        Args:
            binary_path: aloggrep可执行文件路径
        """
        self.aloggrep = ALogGrep(binary_path)
        self.workflow_stages = [
            "global_overview",
            "locate_problems",
            "deep_dive",
            "structured_report"
        ]
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """
        执行四阶段分析工作流
        
        Args:
            inputs: {
                "log_path": str,           # 日志文件路径
                "stage": str,              # 可选：执行特定阶段
                "focus_areas": List[str],  # 可选：重点关注领域
                "output_format": str        # 可选：输出格式
            }
        """
        valid, msg = self._validate_inputs(inputs, ["log_path"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        if not self.aloggrep.is_available():
            return SkillResult(False, {}, "aloggrep is not available")
        
        log_path = inputs["log_path"]
        stage = inputs.get("stage", "all")
        output_format = inputs.get("output_format", "structured")
        
        try:
            if stage == "all":
                # 执行完整工作流
                result = self._run_full_workflow(log_path, output_format)
            else:
                # 执行特定阶段
                result = self._run_single_stage(log_path, stage, output_format)
            
            return SkillResult(
                True,
                result,
                f"四阶段工作流{'完成' if stage == 'all' else '执行'}: {stage if stage != 'all' else '全局'}"
            )
            
        except Exception as e:
            return SkillResult(False, {}, f"工作流执行失败: {str(e)}")
    
    def _run_full_workflow(self, log_path: str, output_format: str) -> Dict[str, Any]:
        """执行完整的四阶段工作流"""
        
        workflow_result = {
            "workflow": "aloggrep_four_stage",
            "log_path": log_path,
            "stages": {},
            "executive_summary": ""
        }
        
        # 阶段1：全局概览
        workflow_result["stages"]["stage1_global_overview"] = self._stage1_global_overview(log_path)
        
        # 阶段2：定位问题区域
        workflow_result["stages"]["stage2_locate_problems"] = self._stage2_locate_problems(log_path)
        
        # 阶段3：深入追踪
        workflow_result["stages"]["stage3_deep_dive"] = self._stage3_deep_dive(log_path)
        
        # 阶段4：结构化报告
        workflow_result["stages"]["stage4_structured_report"] = self._stage4_structured_report(
            log_path, 
            workflow_result["stages"],
            output_format
        )
        
        # 生成执行摘要
        workflow_result["executive_summary"] = self._generate_executive_summary(
            workflow_result["stages"]
        )
        
        return workflow_result
    
    def _run_single_stage(self, log_path: str, stage: str, output_format: str) -> Dict[str, Any]:
        """执行单个阶段"""
        
        stage_methods = {
            "global_overview": self._stage1_global_overview,
            "locate_problems": self._stage2_locate_problems,
            "deep_dive": self._stage3_deep_dive,
            "structured_report": lambda lp: self._stage4_structured_report(lp, {}, output_format)
        }
        
        if stage not in stage_methods:
            return {"error": f"Unknown stage: {stage}"}
        
        return {
            "workflow": "aloggrep_single_stage",
            "stage": stage,
            "result": stage_methods[stage](log_path)
        }
    
    def _stage1_global_overview(self, log_path: str) -> Dict[str, Any]:
        """阶段1：全局概览"""
        
        result = {
            "stage": "global_overview",
            "summary": None,
            "histogram": None,
            "key_metrics": {}
        }
        
        # 获取摘要统计
        summary_result = self.aloggrep.summary(log_path)
        if summary_result["success"] and "data" in summary_result:
            result["summary"] = summary_result["data"]
        
        # 获取时间直方图（含异常检测）
        hist_result = self.aloggrep.histogram(log_path, "1m")
        if hist_result["success"] and "data" in hist_result:
            result["histogram"] = hist_result["data"]
            # 提取异常时间点
            anomalies = self._extract_anomalies(hist_result["data"])
            result["anomalies"] = anomalies
        
        # 计算关键指标
        if result["summary"]:
            summary = result["summary"]
            result["key_metrics"] = {
                "total_entries": summary.get("total_entries", 0),
                "crash_count": summary.get("crashes", 0),
                "error_count": summary.get("level_distribution", {}).get("E", 0),
                "warning_count": summary.get("level_distribution", {}).get("W", 0),
                "time_span": self._calculate_time_span(summary),
                "top_tags": summary.get("top_tags", [])[:5]
            }
        
        return result
    
    def _stage2_locate_problems(self, log_path: str) -> Dict[str, Any]:
        """阶段2：定位问题区域"""
        
        result = {
            "stage": "locate_problems",
            "errors": [],
            "warnings": [],
            "problem_tags": [],
            "patterns": {}
        }
        
        # 提取错误日志
        error_result = self.aloggrep.filter(
            log_path,
            level=LogLevel.E,
            limit=100,
            format="json"
        )
        if error_result["success"]:
            result["errors"] = self._parse_json_lines(error_result["stdout"])
        
        # 提取警告日志
        warning_result = self.aloggrep.filter(
            log_path,
            level=LogLevel.W,
            limit=100,
            format="json"
        )
        if warning_result["success"]:
            result["warnings"] = self._parse_json_lines(warning_result["stdout"])
        
        # 获取错误分布
        dedupe_result = self.aloggrep.dedupe(log_path, 20)
        if dedupe_result["success"] and dedupe_result["stdout"]:
            try:
                result["patterns"] = json.loads(dedupe_result["stdout"])
            except json.JSONDecodeError:
                pass
        
        # 识别高频问题标签
        result["problem_tags"] = self._identify_problem_tags(result["errors"], result["warnings"])
        
        return result
    
    def _stage3_deep_dive(self, log_path: str) -> Dict[str, Any]:
        """阶段3：深入追踪"""
        
        result = {
            "stage": "deep_dive",
            "crashes": [],
            "anr_events": [],
            "critical_errors": []
        }
        
        # 提取崩溃信息
        crashes_result = self.aloggrep.crashes(log_path)
        if crashes_result["success"] and "data" in crashes_result:
            result["crashes"] = crashes_result["data"]
        
        # 提取ANR事件（通过布尔表达式）
        anr_result = self.aloggrep.filter_expr(
            log_path,
            "msg ~ ANR or msg ~ 'not responding'",
            format="json"
        )
        if anr_result["success"]:
            result["anr_events"] = self._parse_json_lines(anr_result["stdout"])
        
        # 提取Fatal错误详情
        fatal_result = self.aloggrep.filter(
            log_path,
            level=LogLevel.F,
            limit=50,
            format="json"
        )
        if fatal_result["success"]:
            result["critical_errors"] = self._parse_json_lines(fatal_result["stdout"])
        
        return result
    
    def _stage4_structured_report(
        self, 
        log_path: str, 
        previous_stages: Dict[str, Any],
        output_format: str
    ) -> Dict[str, Any]:
        """阶段4：结构化报告"""
        
        result = {
            "stage": "structured_report",
            "format": output_format,
            "report": {}
        }
        
        # 构建报告结构
        if output_format == "structured":
            result["report"] = self._build_structured_report(previous_stages)
        elif output_format == "json":
            result["report"] = self._build_json_report(previous_stages)
        elif output_format == "markdown":
            result["report"] = self._build_markdown_report(previous_stages)
        
        return result
    
    def _extract_anomalies(self, histogram_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从直方图数据中提取异常时间点"""
        
        anomalies = []
        
        if "bins" in histogram_data:
            for bin_data in histogram_data["bins"]:
                if bin_data.get("is_anomaly"):
                    anomalies.append({
                        "timestamp": bin_data.get("timestamp"),
                        "count": bin_data.get("count"),
                        "reason": bin_data.get("anomaly_reason", "High activity"),
                        "by_level": bin_data.get("by_level", {})
                    })
        
        return anomalies
    
    def _calculate_time_span(self, summary: Dict[str, Any]) -> str:
        """计算时间跨度"""
        
        time_range = summary.get("time_range", {})
        start = time_range.get("start", "N/A")
        end = time_range.get("end", "N/A")
        
        if start != "N/A" and end != "N/A":
            return f"{start} - {end}"
        
        return "Unknown"
    
    def _identify_problem_tags(
        self, 
        errors: List[Any], 
        warnings: List[Any]
    ) -> List[Dict[str, Any]]:
        """识别高频问题标签"""
        
        tag_counts = {}
        
        for entry in errors + warnings:
            if isinstance(entry, dict):
                tag = entry.get("tag", "Unknown")
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 排序并返回Top 10
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {"tag": tag, "count": count}
            for tag, count in sorted_tags[:10]
        ]
    
    def _parse_json_lines(self, text: str) -> List[Any]:
        """解析JSON行格式"""
        
        results = []
        for line in text.strip().split("\n"):
            if line:
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return results
    
    def _build_structured_report(self, stages: Dict[str, Any]) -> Dict[str, Any]:
        """构建结构化报告"""
        
        report = {
            "overview": {},
            "problems": {},
            "crashes": [],
            "anomalies": [],
            "recommendations": []
        }
        
        # 汇总概览
        if "stage1_global_overview" in stages:
            overview = stages["stage1_global_overview"]
            report["overview"] = overview.get("key_metrics", {})
            report["anomalies"] = overview.get("anomalies", [])
        
        # 汇总问题
        if "stage2_locate_problems" in stages:
            problems = stages["stage2_locate_problems"]
            report["problems"] = {
                "error_count": len(problems.get("errors", [])),
                "warning_count": len(problems.get("warnings", [])),
                "high_frequency_tags": problems.get("problem_tags", [])[:5],
                "patterns": problems.get("patterns", {})
            }
        
        # 汇总崩溃
        if "stage3_deep_dive" in stages:
            deep_dive = stages["stage3_deep_dive"]
            report["crashes"] = deep_dive.get("crashes", [])
            report["problems"]["anr_count"] = len(deep_dive.get("anr_events", []))
        
        # 生成建议
        report["recommendations"] = self._generate_recommendations(report)
        
        return report
    
    def _build_json_report(self, stages: Dict[str, Any]) -> str:
        """构建JSON格式报告"""
        
        return json.dumps(self._build_structured_report(stages), indent=2, ensure_ascii=False)
    
    def _build_markdown_report(self, stages: Dict[str, Any]) -> str:
        """构建Markdown格式报告"""
        
        report = self._build_structured_report(stages)
        
        md = "# Android日志分析报告\n\n"
        
        # 概览
        md += "## 📊 全局概览\n\n"
        overview = report["overview"]
        md += f"- 总日志数: {overview.get('total_entries', 0)}\n"
        md += f"- 崩溃数: {overview.get('crash_count', 0)}\n"
        md += f"- 错误数: {overview.get('error_count', 0)}\n"
        md += f"- 警告数: {overview.get('warning_count', 0)}\n"
        md += f"- 时间跨度: {overview.get('time_span', 'N/A')}\n\n"
        
        # 问题摘要
        md += "## ⚠️ 问题摘要\n\n"
        problems = report["problems"]
        md += f"- 错误日志: {problems.get('error_count', 0)} 条\n"
        md += f"- 警告日志: {problems.get('warning_count', 0)} 条\n"
        md += f"- ANR事件: {problems.get('anr_count', 0)} 条\n\n"
        
        # 高频问题标签
        md += "### 高频问题标签\n\n"
        for tag_info in report["problems"].get("high_frequency_tags", [])[:5]:
            md += f"- {tag_info['tag']}: {tag_info['count']} 次\n"
        md += "\n"
        
        # 异常时间点
        if report["anomalies"]:
            md += "## 🔍 异常时间点\n\n"
            for anomaly in report["anomalies"][:5]:
                md += f"- **{anomaly['timestamp']}**: {anomaly['count']} 条日志 ("
                md += f"{anomaly['reason']})\n"
            md += "\n"
        
        # 崩溃详情
        if report["crashes"]:
            md += "## 💥 崩溃详情\n\n"
            for i, crash in enumerate(report["crashes"][:5], 1):
                md += f"### {i}. {crash.get('exception', 'Unknown')}\n"
                md += f"- 时间: {crash.get('timestamp', 'N/A')}\n"
                md += f"- 线程: {crash.get('thread', 'N/A')}\n"
                md += f"- 进程: {crash.get('process', 'N/A')}\n"
                if "message" in crash:
                    md += f"- 消息: {crash['message'][:100]}...\n"
                md += "\n"
        
        # 建议
        md += "## 💡 建议\n\n"
        for i, rec in enumerate(report["recommendations"], 1):
            md += f"{i}. {rec}\n"
        
        return md
    
    def _generate_executive_summary(self, stages: Dict[str, Any]) -> str:
        """生成执行摘要"""
        
        summary_parts = []
        
        # 概览数据
        if "stage1_global_overview" in stages:
            metrics = stages["stage1_global_overview"].get("key_metrics", {})
            summary_parts.append(
                f"日志共 {metrics.get('total_entries', 0)} 条，"
                f"发现 {metrics.get('crash_count', 0)} 个崩溃，"
                f"{metrics.get('error_count', 0)} 个错误。"
            )
        
        # 问题数据
        if "stage2_locate_problems" in stages:
            problems = stages["stage2_locate_problems"]
            summary_parts.append(
                f"问题主要集中在 {len(problems.get('problem_tags', []))} 个标签。"
            )
        
        # 崩溃数据
        if "stage3_deep_dive" in stages:
            deep_dive = stages["stage3_deep_dive"]
            crash_count = len(deep_dive.get("crashes", []))
            anr_count = len(deep_dive.get("anr_events", []))
            if crash_count > 0 or anr_count > 0:
                summary_parts.append(
                    f"详细分析发现 {crash_count} 个崩溃事件，{anr_count} 个ANR事件。"
                )
        
        return " ".join(summary_parts) if summary_parts else "分析完成，未发现明显问题。"
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """根据分析结果生成建议"""
        
        recommendations = []
        
        # 基于崩溃
        if report["crashes"]:
            recommendations.append(
                f"发现 {len(report['crashes'])} 个崩溃，建议优先处理。"
            )
            # 提取常见异常类型
            exception_types = set()
            for crash in report["crashes"]:
                if isinstance(crash, dict) and "exception" in crash:
                    exception_types.add(crash["exception"])
            if exception_types:
                recommendations.append(
                    f"常见异常类型: {', '.join(list(exception_types)[:3])}。"
                )
        
        # 基于错误数量
        error_count = report["problems"].get("error_count", 0)
        if error_count > 100:
            recommendations.append(
                "错误数量较多，建议进行错误聚合分析找出根本原因。"
            )
        elif error_count > 0:
            recommendations.append(
                "错误数量可控，建议按时间顺序逐个排查。"
            )
        
        # 基于ANR
        anr_count = report["problems"].get("anr_count", 0)
        if anr_count > 0:
            recommendations.append(
                "存在ANR事件，建议检查主线程阻塞问题。"
            )
        
        # 基于异常时间点
        if report["anomalies"]:
            recommendations.append(
                f"发现 {len(report['anomalies'])} 个异常时间点，建议重点关注。"
            )
        
        # 基于高频标签
        high_freq_tags = report["problems"].get("high_frequency_tags", [])
        if high_freq_tags:
            top_tag = high_freq_tags[0]
            recommendations.append(
                f"'{top_tag['tag']}' 标签出现频率最高({top_tag['count']}次)，建议重点排查。"
            )
        
        if not recommendations:
            recommendations.append("日志分析未发现明显问题，应用运行正常。")
        
        return recommendations


class AloggrepQuickAnalysisSkill(BaseSkill):
    """快速分析技能 - 用于快速获取日志概览"""
    
    @property
    def name(self) -> str:
        return "aloggrep_quick_analysis"
    
    def __init__(self, binary_path: str = "aloggrep"):
        self.aloggrep = ALogGrep(binary_path)
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """快速分析入口"""
        
        valid, msg = self._validate_inputs(inputs, ["log_path"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        if not self.aloggrep.is_available():
            return SkillResult(False, {}, "aloggrep is not available")
        
        log_path = inputs["log_path"]
        
        try:
            # 并行执行summary和crashes
            summary = self.aloggrep.quick_analyze(log_path)
            
            result = {
                "quick_summary": {
                    "total_entries": summary.get("summary", {}).get("total_entries", 0) if summary.get("summary") else 0,
                    "crash_count": len(summary.get("crashes", [])),
                    "error_count": summary.get("error_count", 0),
                    "available": summary.get("available", False)
                },
                "crashes": summary.get("crashes", []),
                "histogram": summary.get("histogram")
            }
            
            return SkillResult(
                True,
                result,
                f"快速分析完成: {result['quick_summary']['crash_count']} 崩溃, "
                f"{result['quick_summary']['error_count']} 错误"
            )
            
        except Exception as e:
            return SkillResult(False, {}, f"快速分析失败: {str(e)}")
