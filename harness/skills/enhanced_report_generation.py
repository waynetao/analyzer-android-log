"""
EnhancedReportGenerationSkill - 增强版报告生成技能
整合四阶段分析工作流的结果，生成高质量报告
"""
import os
import json
from datetime import datetime
from typing import Dict, Any
from .base import BaseSkill, SkillResult
from harness.core.paths import OUTPUTS_REPORTS_DIR_STR


class EnhancedReportGenerationSkill(BaseSkill):
    """增强版报告生成技能，整合四阶段分析结果"""
    
    @property
    def name(self) -> str:
        return "enhanced_report_generation"
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """执行增强版报告生成"""
        
        # 检查必要输入
        has_workflow = "aloggrep_workflow" in inputs
        has_bug_desc = "bug_description" in inputs
        
        if not has_workflow and not has_bug_desc:
            return SkillResult(False, {}, "缺少必要输入，需要 aloggrep_workflow 或 bug_description")
        
        try:
            # 获取工作流结果
            workflow_data = inputs.get("aloggrep_workflow", {}).get("data", {})
            
            # 获取bug描述
            bug_desc = inputs.get("bug_description", {"summary": "未提供", "keywords": []})
            
            # 获取其他可选数据
            llm_analysis = inputs.get("llm_analysis", {}).get("data")
            evidence_data = inputs.get("log_evidence_matcher", {}).get("data")
            
            # 输出格式和目录
            output_format = inputs.get("output_format", "markdown")
            workflow_id = inputs.get("workflow_id")
            if workflow_id:
                from harness.core.paths import WorkflowPaths
                wp = WorkflowPaths(workflow_id)
                wp.ensure_dirs()
                output_dir = wp.reports_dir_str
            else:
                output_dir = OUTPUTS_REPORTS_DIR_STR
            
            # 确保输出目录
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 生成报告
            report_files = self._generate_enhanced_report(
                bug_desc=bug_desc,
                workflow_data=workflow_data,
                llm_analysis=llm_analysis,
                evidence_data=evidence_data,
                output_format=output_format,
                output_dir=output_dir
            )
            
            return SkillResult(
                True,
                {
                    "report_files": report_files,
                    "format": output_format,
                    "workflow_included": has_workflow
                },
                f"增强报告生成成功: {', '.join(report_files)}"
            )
            
        except Exception as e:
            return SkillResult(False, {}, f"报告生成失败: {str(e)}")
    
    def _generate_enhanced_report(
        self,
        bug_desc: Dict[str, Any],
        workflow_data: Dict[str, Any],
        llm_analysis: Any,
        evidence_data: Any,
        output_format: str,
        output_dir: str
    ) -> list:
        """生成增强版报告"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"enhanced_report_{timestamp}"
        files = []
        
        if output_format == "markdown":
            files.append(self._generate_markdown(bug_desc, workflow_data, llm_analysis, evidence_data, output_dir, base_name))
        elif output_format == "html":
            files.append(self._generate_html(bug_desc, workflow_data, llm_analysis, evidence_data, output_dir, base_name))
        elif output_format == "json":
            files.append(self._generate_json(bug_desc, workflow_data, llm_analysis, evidence_data, output_dir, base_name))
        elif output_format == "all":
            files.append(self._generate_markdown(bug_desc, workflow_data, llm_analysis, evidence_data, output_dir, base_name))
            files.append(self._generate_html(bug_desc, workflow_data, llm_analysis, evidence_data, output_dir, base_name))
            files.append(self._generate_json(bug_desc, workflow_data, llm_analysis, evidence_data, output_dir, base_name))
        
        return files
    
    def _generate_markdown(
        self,
        bug_desc: Dict[str, Any],
        workflow_data: Dict[str, Any],
        llm_analysis: Any,
        evidence_data: Any,
        output_dir: str,
        base_name: str
    ) -> str:
        """生成Markdown格式增强报告"""
        
        filename = f"{base_name}.md"
        filepath = os.path.join(output_dir, filename)
        
        # 提取各阶段数据
        stages = workflow_data.get("stages", {})
        stage1 = stages.get("stage1_global_overview", {})
        stage2 = stages.get("stage2_locate_problems", {})
        stage3 = stages.get("stage3_deep_dive", {})
        stage4 = stages.get("stage4_structured_report", {})
        
        # 生成报告内容
        content = f"""# 🔍 Android 日志分析报告 (增强版)

📅 生成时间: {datetime.now().isoformat()}

## 1. 问题概览

- **摘要**: {bug_desc.get('summary', 'N/A')}
- **关键词**: {', '.join(bug_desc.get('keywords', []))}

---

## 2. 四阶段分析工作流

"""
        
        # 阶段1：全局概览
        content += self._generate_stage1_section(stage1)
        
        # 阶段2：定位问题
        content += self._generate_stage2_section(stage2)
        
        # 阶段3：深入追踪
        content += self._generate_stage3_section(stage3)
        
        # 阶段4：结构化报告
        content += self._generate_stage4_section(stage4)
        
        # LLM分析
        if llm_analysis:
            content += self._generate_llm_section(llm_analysis)
        
        # 证据匹配
        if evidence_data:
            content += self._generate_evidence_section(evidence_data)
        
        # 执行摘要
        executive_summary = workflow_data.get("executive_summary", "")
        if executive_summary:
            content += f"""
---

## 📋 执行摘要

{executive_summary}

"""
        
        content += """
---

*本报告由 Harness Engineering AI Agent 生成 (增强版)*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def _generate_stage1_section(self, stage1: Dict[str, Any]) -> str:
        """生成阶段1内容：全局概览"""
        
        section = """### 阶段1：全局概览 (Global Overview)

**目标**: 了解日志整体状况，建立问题规模认知

"""
        
        key_metrics = stage1.get("key_metrics", {})
        section += f"""
| 指标 | 数值 |
|------|------|
| 总日志数 | {key_metrics.get('total_entries', 0):,} |
| 崩溃数 | {key_metrics.get('crash_count', 0)} |
| 错误数 | {key_metrics.get('error_count', 0)} |
| 警告数 | {key_metrics.get('warning_count', 0)} |
| 时间跨度 | {key_metrics.get('time_span', 'N/A')} |

"""
        
        # 异常时间点
        anomalies = stage1.get("anomalies", [])
        if anomalies:
            section += "#### 🔴 异常时间点\n\n"
            for anomaly in anomalies[:5]:
                section += f"- **{anomaly.get('timestamp', 'N/A')}**: {anomaly.get('count', 0)} 条日志\n"
                section += f"  - 原因: {anomaly.get('reason', 'High activity')}\n"
            section += "\n"
        
        # Top标签
        top_tags = key_metrics.get("top_tags", [])
        if top_tags:
            section += "#### 🏷️ 高频标签\n\n"
            for tag_info in top_tags[:5]:
                if isinstance(tag_info, dict):
                    section += f"- {tag_info.get('tag', 'N/A')}: {tag_info.get('count', 0)} 次\n"
                elif isinstance(tag_info, list):
                    section += f"- {tag_info[0]}: {tag_info[1]} 次\n"
            section += "\n"
        
        section += "---\n\n"
        return section
    
    def _generate_stage2_section(self, stage2: Dict[str, Any]) -> str:
        """生成阶段2内容：定位问题"""
        
        section = """### 阶段2：定位问题 (Locate Problems)

**目标**: 过滤出需要关注的问题日志

"""
        
        section += f"""
| 问题类型 | 数量 |
|----------|------|
| 错误日志 | {len(stage2.get('errors', []))} |
| 警告日志 | {len(stage2.get('warnings', []))} |
| 高频问题标签 | {len(stage2.get('problem_tags', []))} |

"""
        
        # 问题标签
        problem_tags = stage2.get("problem_tags", [])
        if problem_tags:
            section += "#### ⚠️ 高频问题标签\n\n"
            for tag_info in problem_tags[:5]:
                section += f"- **{tag_info.get('tag', 'N/A')}**: {tag_info.get('count', 0)} 次\n"
            section += "\n"
        
        # 错误模式
        patterns = stage2.get("patterns", {})
        if patterns and "patterns" in patterns:
            section += "#### 📊 错误模式\n\n"
            for pattern in patterns["patterns"][:5]:
                section += f"- 出现 {pattern.get('count', 0)} 次: {pattern.get('message', 'N/A')[:80]}...\n"
            section += "\n"
        
        section += "---\n\n"
        return section
    
    def _generate_stage3_section(self, stage3: Dict[str, Any]) -> str:
        """生成阶段3内容：深入追踪"""
        
        section = """### 阶段3：深入追踪 (Deep Dive)

**目标**: 提取关键问题的详细上下文

"""
        
        crashes = stage3.get("crashes", [])
        anr_events = stage3.get("anr_events", [])
        critical_errors = stage3.get("critical_errors", [])
        
        section += f"""
| 类型 | 数量 |
|------|------|
| 崩溃 | {len(crashes)} |
| ANR | {len(anr_events)} |
| Fatal错误 | {len(critical_errors)} |

"""
        
        # 崩溃详情
        if crashes:
            section += "#### 💥 崩溃详情\n\n"
            for i, crash in enumerate(crashes[:3], 1):
                section += f"**{i}. {crash.get('exception', 'Unknown') if isinstance(crash, dict) else 'Unknown'}**\n"
                if isinstance(crash, dict):
                    section += f"- 时间: {crash.get('timestamp', 'N/A')}\n"
                    section += f"- 线程: {crash.get('thread', 'N/A')}\n"
                    section += f"- 进程: {crash.get('process', 'N/A')}\n"
                    if crash.get('message'):
                        section += f"- 消息: {crash['message'][:100]}...\n"
                section += "\n"
        
        # ANR事件
        if anr_events:
            section += "#### ⏱️ ANR事件\n\n"
            for i, anr in enumerate(anr_events[:3], 1):
                if isinstance(anr, dict):
                    section += f"**{i}. {anr.get('timestamp', 'N/A')}**\n"
                    section += f"- {anr.get('message', 'ANR')[:100]}...\n\n"
            section += "\n"
        
        section += "---\n\n"
        return section
    
    def _generate_stage4_section(self, stage4: Dict[str, Any]) -> str:
        """生成阶段4内容：结构化报告"""
        
        section = """### 阶段4：结构化报告 (Structured Report)

"""
        
        report = stage4.get("report", {})
        
        # 建议
        recommendations = report.get("recommendations", [])
        if recommendations:
            section += "#### 💡 修复建议\n\n"
            for i, rec in enumerate(recommendations, 1):
                section += f"{i}. {rec}\n"
            section += "\n"
        
        # 问题摘要
        problems = report.get("problems", {})
        if problems:
            section += "#### 📋 问题摘要\n\n"
            section += f"- 错误数: {problems.get('error_count', 0)}\n"
            section += f"- 警告数: {problems.get('warning_count', 0)}\n"
            section += f"- ANR数: {problems.get('anr_count', 0)}\n\n"
        
        section += "---\n\n"
        return section
    
    def _generate_llm_section(self, llm_analysis: Any) -> str:
        """生成LLM分析章节"""
        
        if not llm_analysis or not isinstance(llm_analysis, dict):
            return ""
        
        section = """## 🤖 LLM 高级分析

"""
        
        if "analysis" in llm_analysis:
            section += f"{llm_analysis['analysis']}\n\n"
        
        return section
    
    def _generate_evidence_section(self, evidence_data: Dict[str, Any]) -> str:
        """生成证据匹配章节"""
        
        section = """## 🎯 日志证据匹配

"""
        
        confidence = evidence_data.get("confidence_score", 0)
        section += f"**置信度**: {confidence:.0%}\n\n"
        
        # 用户现象与日志对照
        timeline_match = evidence_data.get("timeline_match", [])
        if timeline_match:
            section += "### 用户现象与日志对照\n\n"
            for match in timeline_match:
                status = "✅" if match.get("matched") else "❌"
                section += f"{status} **{match.get('user_description', 'N/A')}**\n"
                section += f"- {match.get('log_evidence', 'N/A')}\n"
                section += f"- 置信度: {match.get('confidence', 0):.0%}\n\n"
        
        # 场景变化
        scene_changes = evidence_data.get("scene_changes", [])
        if scene_changes:
            section += "### 场景变化\n\n"
            for scene in scene_changes:
                section += f"- **{scene.get('time_point', 'N/A')}**: {scene.get('scene', 'N/A')}\n"
                section += f"  - {scene.get('log_summary', 'N/A')}\n"
            section += "\n"
        
        return section
    
    def _generate_html(
        self,
        bug_desc: Dict[str, Any],
        workflow_data: Dict[str, Any],
        llm_analysis: Any,
        evidence_data: Any,
        output_dir: str,
        base_name: str
    ) -> str:
        """生成HTML格式报告"""
        
        filename = f"{base_name}.html"
        filepath = os.path.join(output_dir, filename)
        
        stages = workflow_data.get("stages", {})
        stage1 = stages.get("stage1_global_overview", {})
        stage2 = stages.get("stage2_locate_problems", {})
        stage3 = stages.get("stage3_deep_dive", {})
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Android日志分析报告 (增强版)</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #1976d2; border-bottom: 2px solid #1976d2; padding-bottom: 10px; }}
        h2 {{ color: #424242; margin-top: 30px; }}
        h3 {{ color: #616161; margin-top: 20px; }}
        .summary {{ background: #e3f2fd; padding: 20px; border-radius: 8px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat {{ background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 2.5em; font-weight: bold; color: #1976d2; margin-bottom: 5px; }}
        .stat-label {{ color: #616161; }}
        .crash {{ background: #ffebee; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #f44336; }}
        .anomaly {{ background: #fff3e0; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #ff9800; }}
        .footer {{ margin-top: 40px; color: #9e9e9e; border-top: 1px solid #e0e0e0; padding-top: 15px; }}
    </style>
</head>
<body>
    <h1>🔍 Android日志分析报告 (增强版)</h1>
    <p style="color: #757575;">📅 生成时间: {datetime.now().isoformat()}</p>
    
    <div class="summary">
        <h2>1. 问题概览</h2>
        <p><strong>摘要:</strong> {bug_desc.get('summary', 'N/A')}</p>
        <p><strong>关键词:</strong> {', '.join(bug_desc.get('keywords', []))}</p>
    </div>
    
    <h2>2. 分析结果</h2>
    <div class="stats">
        <div class="stat">
            <div class="stat-value">{stage1.get('key_metrics', {}).get('total_entries', 0):,}</div>
            <div class="stat-label">总日志数</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(stage3.get('crashes', []))}</div>
            <div class="stat-label">崩溃数</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(stage2.get('errors', []))}</div>
            <div class="stat-label">错误数</div>
        </div>
        <div class="stat">
            <div class="stat-value">{len(stage2.get('warnings', []))}</div>
            <div class="stat-label">警告数</div>
        </div>
    </div>
    
    <div class="footer">
        <p>🤖 本报告由 Harness Engineering AI Agent 生成</p>
    </div>
</body>
</html>
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filepath
    
    def _generate_json(
        self,
        bug_desc: Dict[str, Any],
        workflow_data: Dict[str, Any],
        llm_analysis: Any,
        evidence_data: Any,
        output_dir: str,
        base_name: str
    ) -> str:
        """生成JSON格式报告"""
        
        filename = f"{base_name}.json"
        filepath = os.path.join(output_dir, filename)
        
        report_data = {
            "version": "5.0",
            "generated_at": datetime.now().isoformat(),
            "bug_description": bug_desc,
            "workflow_analysis": workflow_data,
            "llm_analysis": llm_analysis,
            "evidence_matching": evidence_data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        return filepath
