"""
Analytics - 数据统计分析模块
收集各阶段数据指标，生成质量报告和趋势分析
"""

import os
import json
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict

from .logging import get_logger
from .paths import PROJECT_ROOT_STR, OUTPUTS_ANALYTICS_DIR_STR

logger = get_logger(__name__)

# 延迟导入 token_stats 以避免循环导入
_token_stats = None

def _get_token_stats():
    """延迟获取 token_stats 实例"""
    global _token_stats
    if _token_stats is None:
        from .token_stats import get_token_stats as _get_ts
        _token_stats = _get_ts()
    return _token_stats


@dataclass
class SkillMetrics:
    """技能执行指标"""
    skill_name: str
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100
    
    @property
    def avg_duration_ms(self) -> float:
        if self.execution_count == 0:
            return 0.0
        return self.total_duration_ms / self.execution_count
    
    def record_duration(self, duration_ms: float):
        """记录一次执行耗时"""
        self.total_duration_ms += duration_ms
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)


@dataclass
class StageMetrics:
    """阶段执行指标"""
    stage_name: str
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration_ms: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100
    
    @property
    def avg_duration_ms(self) -> float:
        if self.execution_count == 0:
            return 0.0
        return self.total_duration_ms / self.execution_count


@dataclass
class WorkflowMetrics:
    """工作流执行指标"""
    workflow_id: str
    workflow_name: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    status: str = "running"  # running, completed, failed
    stage_count: int = 0
    skill_count: int = 0
    validation_passed: int = 0
    validation_failed: int = 0
    error_message: Optional[str] = None
    bug_type: Optional[str] = None
    crash_count: int = 0
    anr_count: int = 0
    exception_count: int = 0
    critical_log_count: int = 0


@dataclass
class SystemMetrics:
    """系统级指标"""
    total_workflows: int = 0
    completed_workflows: int = 0
    failed_workflows: int = 0
    total_execution_time_ms: float = 0.0
    skill_metrics: Dict[str, SkillMetrics] = field(default_factory=dict)
    stage_metrics: Dict[str, StageMetrics] = field(default_factory=dict)
    bug_type_distribution: Dict[str, int] = field(default_factory=dict)
    error_distribution: Dict[str, int] = field(default_factory=dict)


class AnalyticsCollector:
    """数据收集器 - 收集各阶段执行数据"""
    
    def __init__(self, analytics_dir: str = None):
        if analytics_dir is None:
            analytics_dir = OUTPUTS_ANALYTICS_DIR_STR
        
        self.analytics_dir = analytics_dir
        os.makedirs(analytics_dir, exist_ok=True)
        
        self.current_workflow: Optional[WorkflowMetrics] = None
        self.system_metrics = SystemMetrics()
        
        logger.info(f"AnalyticsCollector 初始化完成: {analytics_dir}")
    
    def start_workflow(self, workflow_name: str) -> str:
        """开始跟踪工作流"""
        workflow_id = f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_workflow = WorkflowMetrics(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            start_time=datetime.now().isoformat()
        )
        
        self.system_metrics.total_workflows += 1
        logger.info(f"开始跟踪工作流: {workflow_id}")
        return workflow_id
    
    def end_workflow(self, status: str = "completed", error_message: str = None):
        """结束工作流跟踪"""
        if not self.current_workflow:
            logger.warning("没有正在跟踪的工作流")
            return
        
        self.current_workflow.end_time = datetime.now().isoformat()
        self.current_workflow.status = status
        self.current_workflow.error_message = error_message
        
        # 计算耗时
        start = datetime.fromisoformat(self.current_workflow.start_time)
        end = datetime.fromisoformat(self.current_workflow.end_time)
        self.current_workflow.duration_ms = (end - start).total_seconds() * 1000
        
        # 更新系统指标
        self.system_metrics.total_execution_time_ms += self.current_workflow.duration_ms
        
        if status == "completed":
            self.system_metrics.completed_workflows += 1
        else:
            self.system_metrics.failed_workflows += 1
        
        # 保存工作流报告
        self._save_workflow_report()
        
        # 保存 Token 统计
        _get_token_stats().save_session(f"token_stats_{self.current_workflow.workflow_id}.json")
        
        logger.info(f"工作流结束: {self.current_workflow.workflow_id}, 状态: {status}, 耗时: {self.current_workflow.duration_ms:.2f}ms")
        
        self.current_workflow = None
    
    def record_skill_execution(
        self,
        skill_name: str,
        success: bool,
        duration_ms: float,
        error: str = None
    ):
        """记录技能执行"""
        # 更新当前工作流
        if self.current_workflow:
            self.current_workflow.skill_count += 1
        
        # 更新系统技能指标
        if skill_name not in self.system_metrics.skill_metrics:
            self.system_metrics.skill_metrics[skill_name] = SkillMetrics(skill_name=skill_name)
        
        metrics = self.system_metrics.skill_metrics[skill_name]
        metrics.execution_count += 1
        
        if success:
            metrics.success_count += 1
        else:
            metrics.failure_count += 1
            if error:
                self.system_metrics.error_distribution[error] = \
                    self.system_metrics.error_distribution.get(error, 0) + 1
        
        metrics.total_duration_ms += duration_ms
        metrics.min_duration_ms = min(metrics.min_duration_ms, duration_ms)
        metrics.max_duration_ms = max(metrics.max_duration_ms, duration_ms)
        
        logger.debug(f"技能执行记录: {skill_name}, 成功: {success}, 耗时: {duration_ms}ms")
    
    def record_stage_execution(
        self,
        stage_name: str,
        success: bool,
        duration_ms: float
    ):
        """记录阶段执行"""
        # 更新当前工作流
        if self.current_workflow:
            self.current_workflow.stage_count += 1
        
        # 更新系统阶段指标
        if stage_name not in self.system_metrics.stage_metrics:
            self.system_metrics.stage_metrics[stage_name] = StageMetrics(stage_name=stage_name)
        
        metrics = self.system_metrics.stage_metrics[stage_name]
        metrics.execution_count += 1
        
        if success:
            metrics.success_count += 1
        else:
            metrics.failure_count += 1
        
        metrics.total_duration_ms += duration_ms
    
    def record_validation(self, passed: bool):
        """记录验证结果"""
        if not self.current_workflow:
            return
        
        if passed:
            self.current_workflow.validation_passed += 1
        else:
            self.current_workflow.validation_failed += 1
    
    def record_analysis_result(
        self,
        bug_type: str = None,
        crash_count: int = 0,
        anr_count: int = 0,
        exception_count: int = 0,
        critical_log_count: int = 0
    ):
        """记录分析结果"""
        if not self.current_workflow:
            return
        
        if bug_type:
            self.current_workflow.bug_type = bug_type
            self.system_metrics.bug_type_distribution[bug_type] = \
                self.system_metrics.bug_type_distribution.get(bug_type, 0) + 1
        
        self.current_workflow.crash_count = crash_count
        self.current_workflow.anr_count = anr_count
        self.current_workflow.exception_count = exception_count
        self.current_workflow.critical_log_count = critical_log_count
    
    def _save_workflow_report(self):
        """保存单个工作流报告"""
        if not self.current_workflow:
            return
        
        report_file = os.path.join(
            self.analytics_dir,
            f"workflow_{self.current_workflow.workflow_id}.json"
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.current_workflow), f, ensure_ascii=False, indent=2)
    
    def generate_system_report(self) -> Dict[str, Any]:
        """生成系统级统计报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_workflows": self.system_metrics.total_workflows,
                "completed": self.system_metrics.completed_workflows,
                "failed": self.system_metrics.failed_workflows,
                "success_rate": self._calc_success_rate(),
                "total_execution_time_ms": self.system_metrics.total_execution_time_ms,
                "avg_execution_time_ms": self._calc_avg_execution_time()
            },
            "token_usage": _get_token_stats().get_summary(),
            "token_cost_estimate": _get_token_stats().estimate_cost(),
            "skill_performance": self._get_skill_performance(),
            "stage_performance": self._get_stage_performance(),
            "bug_type_distribution": self.system_metrics.bug_type_distribution,
            "error_distribution": self.system_metrics.error_distribution,
            "recommendations": self._generate_recommendations()
        }
        
        # 保存报告
        report_file = os.path.join(self.analytics_dir, "system_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"系统报告已生成: {report_file}")
        return report
    
    def generate_markdown_report(self) -> str:
        """生成 Markdown 格式的统计报告"""
        report = self.generate_system_report()
        
        md = f"""# Android Log Analyzer - 系统运行报告

## 📊 概览

| 指标 | 数值 |
|------|------|
| 总工作流数 | {report['summary']['total_workflows']} |
| 成功完成 | {report['summary']['completed']} |
| 执行失败 | {report['summary']['failed']} |
| 成功率 | {report['summary']['success_rate']:.1f}% |
| 总执行时间 | {report['summary']['total_execution_time_ms']:.2f}ms |
| 平均执行时间 | {report['summary']['avg_execution_time_ms']:.2f}ms |

## 🪙 Token 使用统计

### 总览
| 指标 | 数值 |
|------|------|
| Prompt Tokens | {report['token_usage']['total']['prompt_tokens']} |
| Completion Tokens | {report['token_usage']['total']['completion_tokens']} |
| **Total Tokens** | **{report['token_usage']['total']['total_tokens']}** |
"""
        if report['token_cost_estimate']:
            md += f"| 预估费用 (USD) | ${report['token_cost_estimate']['estimated_cost_usd']:.4f} |\n"
            md += f"| 预估费用 (CNY) | ¥{report['token_cost_estimate']['estimated_cost_cny']:.4f} |\n"

        # 按场景统计
        if report['token_usage']['by_scene']:
            md += f"""
### 按场景统计
| 场景 | Prompt | Completion | Total |
|------|--------|------------|-------|
"""
            for scene, stats in sorted(report['token_usage']['by_scene'].items()):
                md += f"| {scene} | {stats['prompt_tokens']} | {stats['completion_tokens']} | {stats['total_tokens']} |\n"

        # 按技能统计
        if report['token_usage']['by_skill']:
            md += f"""
### 按技能统计
| 技能 | Prompt | Completion | Total |
|------|--------|------------|-------|
"""
            for skill, stats in sorted(report['token_usage']['by_skill'].items()):
                md += f"| {skill} | {stats['prompt_tokens']} | {stats['completion_tokens']} | {stats['total_tokens']} |\n"

        # 按模型统计
        if report['token_usage']['by_model']:
            md += f"""
### 按模型统计
| 模型 | Prompt | Completion | Total |
|------|--------|------------|-------|
"""
            for model, stats in sorted(report['token_usage']['by_model'].items()):
                md += f"| {model} | {stats['prompt_tokens']} | {stats['completion_tokens']} | {stats['total_tokens']} |\n"

        md += f"""
## 🔧 技能性能

| 技能名称 | 执行次数 | 成功 | 失败 | 成功率 | 平均耗时 |
|----------|---------|------|------|--------|----------|
"""
        
        for skill_name, metrics in report['skill_performance'].items():
            md += f"| {skill_name} | {metrics['execution_count']} | {metrics['success_count']} | {metrics['failure_count']} | {metrics['success_rate']:.1f}% | {metrics['avg_duration_ms']:.2f}ms |\n"
        
        md += f"""
## 📋 阶段性能

| 阶段 | 执行次数 | 成功 | 失败 | 成功率 | 平均耗时 |
|------|---------|------|------|--------|----------|
"""
        
        for stage_name, metrics in report['stage_performance'].items():
            md += f"| {stage_name} | {metrics['execution_count']} | {metrics['success_count']} | {metrics['failure_count']} | {metrics['success_rate']:.1f}% | {metrics['avg_duration_ms']:.2f}ms |\n"
        
        md += f"""
## 🐛 Bug 类型分布
"""
        
        if report['bug_type_distribution']:
            for bug_type, count in sorted(report['bug_type_distribution'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / report['summary']['total_workflows']) * 100
                md += f"- {bug_type}: {count} ({percentage:.1f}%)\n"
        else:
            md += "- 暂无数据\n"
        
        md += f"""
## ⚠️ 错误分布
"""
        
        if report['error_distribution']:
            for error, count in sorted(report['error_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
                md += f"- {error}: {count} 次\n"
        else:
            md += "- 无错误\n"
        
        md += f"""
## 💡 优化建议
"""
        
        for i, rec in enumerate(report['recommendations'], 1):
            md += f"{i}. {rec}\n"
        
        md += f"""
---
*报告生成时间: {report['generated_at']}*
"""
        
        # 保存 Markdown 报告
        report_file = os.path.join(self.analytics_dir, "system_report.md")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(md)
        
        logger.info(f"Markdown 报告已生成: {report_file}")
        return md
    
    def _calc_success_rate(self) -> float:
        """计算成功率"""
        if self.system_metrics.total_workflows == 0:
            return 0.0
        return (self.system_metrics.completed_workflows / self.system_metrics.total_workflows) * 100
    
    def _calc_avg_execution_time(self) -> float:
        """计算平均执行时间"""
        if self.system_metrics.total_workflows == 0:
            return 0.0
        return self.system_metrics.total_execution_time_ms / self.system_metrics.total_workflows
    
    def _get_skill_performance(self) -> Dict[str, Dict]:
        """获取技能性能数据"""
        result = {}
        for name, metrics in self.system_metrics.skill_metrics.items():
            result[name] = {
                "execution_count": metrics.execution_count,
                "success_count": metrics.success_count,
                "failure_count": metrics.failure_count,
                "success_rate": metrics.success_rate,
                "avg_duration_ms": metrics.avg_duration_ms,
                "min_duration_ms": metrics.min_duration_ms if metrics.min_duration_ms != float('inf') else 0,
                "max_duration_ms": metrics.max_duration_ms
            }
        return result
    
    def _get_stage_performance(self) -> Dict[str, Dict]:
        """获取阶段性能数据"""
        result = {}
        for name, metrics in self.system_metrics.stage_metrics.items():
            result[name] = {
                "execution_count": metrics.execution_count,
                "success_count": metrics.success_count,
                "failure_count": metrics.failure_count,
                "success_rate": metrics.success_rate,
                "avg_duration_ms": metrics.avg_duration_ms
            }
        return result
    
    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 检查失败率高的技能
        for name, metrics in self.system_metrics.skill_metrics.items():
            if metrics.execution_count >= 3 and metrics.success_rate < 70:
                recommendations.append(f"技能 '{name}' 成功率较低 ({metrics.success_rate:.1f}%)，建议检查实现")
        
        # 检查执行时间长的技能
        for name, metrics in self.system_metrics.skill_metrics.items():
            if metrics.execution_count >= 3 and metrics.avg_duration_ms > 5000:
                recommendations.append(f"技能 '{name}' 平均耗时较长 ({metrics.avg_duration_ms:.0f}ms)，建议优化")
        
        # 检查常见错误
        for error, count in self.system_metrics.error_distribution.items():
            if count >= 3:
                recommendations.append(f"错误 '{error}' 出现 {count} 次，建议排查原因")
        
        # 检查失败率高的阶段
        for name, metrics in self.system_metrics.stage_metrics.items():
            if metrics.execution_count >= 3 and metrics.success_rate < 80:
                recommendations.append(f"阶段 '{name}' 成功率较低 ({metrics.success_rate:.1f}%)，建议检查流程")
        
        if not recommendations:
            recommendations.append("系统运行良好，所有指标均在正常范围内")
        
        return recommendations
    
    def load_historical_reports(self, limit: int = 10) -> List[Dict]:
        """加载历史工作流报告"""
        reports = []
        
        if not os.path.exists(self.analytics_dir):
            return reports
        
        files = sorted(
            [f for f in os.listdir(self.analytics_dir) if f.startswith('workflow_')],
            reverse=True
        )[:limit]
        
        for file in files:
            try:
                with open(os.path.join(self.analytics_dir, file), 'r', encoding='utf-8') as f:
                    reports.append(json.load(f))
            except Exception as e:
                logger.warning(f"加载报告失败 {file}: {e}")
        
        return reports


# 全局单例
_analytics_collector: Optional[AnalyticsCollector] = None
_analytics_lock = threading.Lock()


def get_analytics_collector() -> AnalyticsCollector:
    """获取全局数据收集器实例（线程安全）"""
    global _analytics_collector
    if _analytics_collector is None:
        with _analytics_lock:
            if _analytics_collector is None:
                _analytics_collector = AnalyticsCollector()
    return _analytics_collector
