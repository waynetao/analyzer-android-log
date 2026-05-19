"""
ReportGenerationSkill - 报告生成技能
支持多种输出格式，集成LLM高质量分析
"""
import os
import json
from datetime import datetime
from typing import Dict, Any
from .base import BaseSkill, SkillResult
from harness.core.paths import OUTPUTS_REPORTS_DIR_STR

class ReportGenerationSkill(BaseSkill):
    """报告生成技能 - 支持多格式，集成LLM分析"""
    
    @property
    def name(self) -> str:
        return "report_generation"
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        # 验证输入（兼容新旧两种方式）
        has_llm = "llm_analysis" in inputs
        has_advanced = "advanced_log_analysis" in inputs
        has_evidence = "log_evidence_matcher" in inputs
        has_timeline = "timeline_builder" in inputs
        has_aloggrep = "aloggrep_analysis" in inputs
        has_log_extraction_aloggrep = "log_extraction_aloggrep" in inputs
        
        valid = ("bug_description" in inputs and 
                (("log_extraction" in inputs and "bug_analysis" in inputs) or has_advanced or has_log_extraction_aloggrep))
        if not valid:
            return SkillResult(False, {}, "缺少必要输入")
        
        try:
            # 准备数据
            bug_desc = inputs["bug_description"]
            
            if has_advanced:
                log_data = inputs["advanced_log_analysis"]["data"]
            elif has_log_extraction_aloggrep:
                aloggrep_extraction_data = inputs["log_extraction_aloggrep"]["data"]
                log_data = self._convert_aloggrep_to_log_data(aloggrep_extraction_data)
            else:
                log_data = inputs["log_extraction"]["data"]
            
            if has_llm:
                llm_analysis = inputs["llm_analysis"]["data"]
            else:
                llm_analysis = None
            
            if has_evidence:
                evidence_data = inputs["log_evidence_matcher"]["data"]
            else:
                evidence_data = None
            
            if has_timeline:
                timeline_data = inputs["timeline_builder"]["data"]
            else:
                timeline_data = None
            
            if has_aloggrep:
                aloggrep_analysis_data = inputs["aloggrep_analysis"]["data"]
            else:
                aloggrep_analysis_data = None
            
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
            report_files = self._generate_report(
                bug_desc, log_data, llm_analysis, evidence_data, timeline_data,
                aloggrep_analysis_data,
                output_format, output_dir
            )
            
            return SkillResult(
                True,
                {"report_files": report_files, "format": output_format, "has_llm": has_llm},
                f"成功生成报告: {', '.join(report_files)}"
            )
            
        except Exception as e:
            return SkillResult(
                False,
                {},
                f"报告生成失败: {str(e)}"
            )
    
    def _convert_aloggrep_to_log_data(self, aloggrep_data: Dict[str, Any]) -> Dict[str, Any]:
        """将 aloggrep 数据转换为标准 log_data 格式"""
        log_data = {
            "crashes": 0,
            "anrs": 0,
            "low_memory": 0,
            "exceptions": 0,
            "log_count": 0,
            "log_files": aloggrep_data.get('log_files', []),
            "critical_logs": []
        }
        
        # 从 aloggrep 分析中提取崩溃信息
        if 'all_crashes' in aloggrep_data:
            log_data['crashes'] = len(aloggrep_data['all_crashes'])
            for crash in aloggrep_data['all_crashes'][:5]:  # 取前5个
                log_data['critical_logs'].append({
                    'type': 'crash',
                    'timestamp': crash.get('timestamp', ''),
                    'level': 'F',
                    'tag': 'AndroidRuntime',
                    'message': str(crash)
                })
        
        log_data['exceptions'] = aloggrep_data.get('total_error_count', 0)
        
        return log_data
    
    def _generate_multi_round_section(self, multi_round_data: Dict[str, Any]) -> str:
        """生成多轮分析章节"""
        rounds = multi_round_data.get("rounds", [])
        confidence = multi_round_data.get("confidence", {})
        
        content = """
## 🤖 多轮深度分析

"""
        
        # 添加置信度信息
        if confidence:
            root_cause_conf = confidence.get("root_cause", 0) * 100
            fix_conf = confidence.get("fix_feasibility", 0) * 100
            content += f"""
### 分析置信度

- **根因分析置信度**: {root_cause_conf:.0f}%
- **修复方案可行性**: {fix_conf:.0f}%

"""
        
        # 添加每轮的分析结果
        for round_data in rounds:
            round_num = round_data.get("round", 0)
            round_name = round_data.get("name", f"第{round_num}轮")
            round_analysis = round_data.get("analysis", "")
            
            content += f"""
### 第{round_num}轮：{round_name}

{round_analysis}

---
"""
        
        # 添加推荐修复方案
        recommended_fix = multi_round_data.get("recommended_fix", "")
        if recommended_fix and recommended_fix != "请参考详细分析":
            content += f"""

### 💡 推荐修复方案

{recommended_fix}

"""
        
        return content
    
    def _generate_aloggrep_section(self, aloggrep_data: Dict[str, Any]) -> str:
        """生成 aloggrep 分析章节的 Markdown 部分"""
        if not aloggrep_data:
            return ""
        
        section = "## 🔍 aloggrep 分析\n\n"
        
        # 检查是否有 aloggrep 可用
        if 'available' in aloggrep_data and not aloggrep_data['available']:
            section += "aloggrep 不可用，使用基础分析\n\n"
            return section
        
        # 添加崩溃信息
        if 'all_crashes' in aloggrep_data and aloggrep_data['all_crashes']:
            section += f"### 发现的崩溃 ({len(aloggrep_data['all_crashes'])}个)\n\n"
            i = 1
            for crash in aloggrep_data['all_crashes'][:5]:
                section += f"#### 崩溃 {i}\n"
                if isinstance(crash, dict):
                    section += f"- 文件: {crash.get('source_file', 'Unknown')}\n"
                section += f"- 详情: {str(crash)[:200]}...\n\n"
                i += 1
        
        # 添加分析摘要
        if 'aloggrep_analysis' in aloggrep_data:
            section += "### 各文件分析\n\n"
            for file_path, analysis in aloggrep_data['aloggrep_analysis'].items():
                if isinstance(analysis, dict):
                    section += f"#### {file_path}\n"
                    if 'error_count' in analysis:
                        section += f"- 错误数: {analysis['error_count']}\n"
                if 'crashes' in analysis:
                    section += f"- 崩溃数: {len(analysis['crashes'])}\n"
                section += "\n"
        
        return section
    
    def _generate_aloggrep_html_section(self, aloggrep_data: Dict[str, Any]) -> str:
        """生成 aloggrep 分析章节的 HTML 部分"""
        if not aloggrep_data:
            return ""
        
        section = "        <h2>🔍 aloggrep 分析</h2>\n\n"
        
        # 检查是否有 aloggrep 可用
        if 'available' in aloggrep_data and not aloggrep_data['available']:
            section += "        <p>aloggrep 不可用，使用基础分析</p>\n"
            return section
        
        # 添加崩溃信息
        if 'all_crashes' in aloggrep_data and aloggrep_data['all_crashes']:
            section += f"        <h3>发现的崩溃 ({len(aloggrep_data['all_crashes'])}个)</h3>\n"
            for crash in aloggrep_data['all_crashes'][:5]:
                section += "        <div class=\"log-evidence\">\n"
                if isinstance(crash, dict):
                    section += f"            <div class=\"log-header\">💥 {crash.get('source_file', 'Unknown')}</div>\n"
                section += f"            <p><strong>详情:</strong> {str(crash)[:300]}...</p>\n"
                section += "        </div>\n"
        
        return section
    
    def _generate_report(
        self,
        bug_desc: Dict[str, Any],
        log_data: Dict[str, Any],
        llm_analysis: Dict[str, Any],
        evidence_data: Dict[str, Any],
        timeline_data: Dict[str, Any],
        aloggrep_data: Dict[str, Any],
        output_format: str,
        output_dir: str
    ) -> list:
        """生成报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"bug_report_{timestamp}"
        files = []
        
        # 支持多种格式
        if output_format == "markdown":
            files.append(self._generate_markdown(bug_desc, log_data, llm_analysis, evidence_data, timeline_data, aloggrep_data, output_dir, base_name))
        elif output_format == "html":
            files.append(self._generate_html(bug_desc, log_data, llm_analysis, evidence_data, timeline_data, aloggrep_data, output_dir, base_name))
        elif output_format == "json":
            files.append(self._generate_json(bug_desc, log_data, llm_analysis, evidence_data, timeline_data, aloggrep_data, output_dir, base_name))
        elif output_format == "all":
            files.append(self._generate_markdown(bug_desc, log_data, llm_analysis, evidence_data, timeline_data, aloggrep_data, output_dir, base_name))
            files.append(self._generate_html(bug_desc, log_data, llm_analysis, evidence_data, timeline_data, aloggrep_data, output_dir, base_name))
            files.append(self._generate_json(bug_desc, log_data, llm_analysis, evidence_data, timeline_data, aloggrep_data, output_dir, base_name))
        
        return files
    
    def _generate_markdown(self, bug_desc, log_data, llm_analysis, evidence_data, timeline_data, aloggrep_data, output_dir, base_name):
        filename = f"{base_name}.md"
        filepath = os.path.join(output_dir, filename)
        
        llm_section = ""
        if llm_analysis and "analysis" in llm_analysis:
            # 检查是否是多轮分析结果
            if "multi_round_analysis" in llm_analysis:
                # 多轮分析模式
                multi_round_data = llm_analysis.get("multi_round_analysis", {})
                llm_section = self._generate_multi_round_section(multi_round_data)
            else:
                # 标准分析模式
                llm_section = f"""
## 🤖 LLM 高级分析

{llm_analysis['analysis']}
"""
        
        evidence_section = ""
        additional_findings_section = ""
        if evidence_data:
            confidence = evidence_data.get('confidence_score', 0)
            what_we_saw = '\n'.join(f'- {item}' for item in evidence_data.get('what_we_saw_in_logs', []))
            what_happened = '\n'.join(evidence_data.get('what_happened', []))
            confidence_exp = evidence_data.get('confidence_explanation', '')
            
            scene_changes = ''
            for scene in evidence_data.get('scene_changes', []):
                scene_changes += f"- **{scene.get('time_point')}**: {scene.get('scene')} - {scene.get('log_summary')}\n"
            
            timeline_match = ''
            for match in evidence_data.get('timeline_match', []):
                status = "✅" if match.get('matched') else "❌"
                timeline_match += f"{status} **{match.get('user_description')}**\n  - {match.get('log_evidence')} (置信度: {match.get('confidence', 0):.0%})\n"
            
            evidence_section = f"""
## 🎯 日志证据匹配

### 报告置信度
**{confidence:.0%}**

{confidence_exp}

### 用户现象与日志对照
{timeline_match}

### 场景变化
{scene_changes}

### 我们在日志中看到了什么
{what_we_saw}

### 发生了什么
{what_happened}
"""
            
            # ============ 新增：额外发现的问题章节 ============
            additional_findings = evidence_data.get('additional_findings', [])
            if additional_findings:
                additional_content = ""
                for idx, log in enumerate(additional_findings[:10], 1):
                    if isinstance(log, dict):
                        log_type = log.get('type', 'unknown').upper()
                        timestamp = log.get('timestamp', 'N/A')
                        level = log.get('level', 'N/A')
                        tag = log.get('tag', 'N/A')
                        message = log.get('message', '')
                    else:
                        log_type = "UNKNOWN"
                        timestamp = "N/A"
                        level = "N/A"
                        tag = "N/A"
                        message = str(log)
                    
                    additional_content += f"""
### {idx}. ⚠️ {log_type}
- **时间**: {timestamp}
- **级别**: {level}
- **标签**: {tag}
- **内容**: {message}
"""
                
                additional_findings_section = f"""
## ⚠️ 额外发现的严重问题

> **说明**: 以下问题与您描述的bug可能不直接相关，但在日志中发现了这些严重问题，请注意关注。

{additional_content}
"""
        
        timeline_section = ""
        if timeline_data:
            critical_events = '\n'.join(f"- **{e['timestamp']}**: [{e['event_type']}] {e['summary']}" for e in timeline_data.get('critical_events', []))
            timeline_section = f"""
## 📊 事件时间线

### 关键事件
{critical_events}

### 完整时间线
(共 {timeline_data.get('total_events', 0)} 个事件)
"""
        
        aloggrep_section = self._generate_aloggrep_section(aloggrep_data)
        
        content = f"""# Android Bug 分析报告

📅 生成时间: {datetime.now().isoformat()}

## 1. 问题概览

- 摘要: {bug_desc.get('summary', 'N/A')}
- 关键词: {', '.join(bug_desc.get('keywords', []))}

## 2. 分析结果摘要

| 问题类型 | 数量 |
|----------|------|
| 崩溃数 | {log_data.get('crashes', 0)} |
| ANR数 | {log_data.get('anrs', 0)} |
| 低内存 | {log_data.get('low_memory', 0)} |
| 异常数 | {log_data.get('exceptions', 0)} |

{llm_section}
{evidence_section}
{additional_findings_section}
{timeline_section}
{aloggrep_section}

## 3. 日志基础信息

- 日志总数: {log_data.get('log_count', 0)}
- 日志文件: {', '.join(str(f) for f in log_data.get('log_files', []))}

## 4. 关键日志证据

"""
        
        # 添加关键日志（如果有）
        if "critical_logs" in log_data:
            for idx, log in enumerate(log_data["critical_logs"][:5], 1):
                content += f"""
### {idx}. {log['type'].upper()}
- 时间: {log['timestamp']}
- 级别: {log['level']}
- 标签: {log['tag']}
- 内容: {log['message']}
"""
        
        content += """
---
*本报告由 Harness Engineering AI Agent 生成*
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def _generate_html(self, bug_desc, log_data, llm_analysis, evidence_data, timeline_data, aloggrep_data, output_dir, base_name):
        filename = f"{base_name}.html"
        filepath = os.path.join(output_dir, filename)
        
        llm_section = ""
        if llm_analysis and "analysis" in llm_analysis:
            llm_section = f"""
        <h2>🤖 LLM 高级分析</h2>
        <div style="background: #fffbe6; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
            <pre style="white-space: pre-wrap; margin: 0;">{llm_analysis['analysis']}</pre>
        </div>
"""
        
        evidence_section = ""
        additional_findings_html = ""
        if evidence_data:
            confidence = evidence_data.get('confidence_score', 0)
            confidence_color = "#4caf50" if confidence >= 0.8 else "#ff9800" if confidence >= 0.5 else "#f44336"
            
            timeline_match_html = ""
            for match in evidence_data.get('timeline_match', []):
                status_icon = "✅" if match.get('matched') else "❌"
                timeline_match_html += f"""
            <div style="margin: 10px 0; padding: 10px; background: #fafafa; border-radius: 4px;">
                <div style="font-weight: bold;">{status_icon} {match.get('user_description')}</div>
                <div style="color: #616161; margin-top: 5px;">{match.get('log_evidence')} (置信度: {match.get('confidence', 0):.0%})</div>
            </div>
"""
            
            scene_changes_html = ""
            for scene in evidence_data.get('scene_changes', []):
                scene_changes_html += f"""
            <div style="margin: 8px 0;">
                <strong>{scene.get('time_point')}</strong>: {scene.get('scene')} - <span style="color: #616161;">{scene.get('log_summary')}</span>
            </div>
"""
            
            what_we_saw_html = ""
            for item in evidence_data.get('what_we_saw_in_logs', []):
                what_we_saw_html += f"<li>{item}</li>"
            
            what_happened_html = ""
            for item in evidence_data.get('what_happened', []):
                what_happened_html += f"<li>{item}</li>"
            
            evidence_section = f"""
        <h2>🎯 日志证据匹配</h2>
        
        <div style="background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 15px 0;">
            <h3 style="margin-top: 0; color: #2e7d32;">报告置信度</h3>
            <div style="font-size: 2.5em; font-weight: bold; color: {confidence_color};">{confidence:.0%}</div>
            <div style="margin-top: 10px; color: #424242; white-space: pre-wrap;">{evidence_data.get('confidence_explanation', '')}</div>
        </div>
        
        <h3>用户现象与日志对照</h3>
        {timeline_match_html}
        
        <h3>场景变化</h3>
        {scene_changes_html}
        
        <h3>我们在日志中看到了什么</h3>
        <ul>
            {what_we_saw_html}
        </ul>
        
        <h3>发生了什么</h3>
        <ol>
            {what_happened_html}
        </ol>
"""
            
            # ============ 新增：额外发现的问题HTML章节 ============
            additional_findings_html = ""
            additional_findings = evidence_data.get('additional_findings', [])
            if additional_findings:
                additional_logs_html = ""
                for idx, log in enumerate(additional_findings[:10], 1):
                    if isinstance(log, dict):
                        log_type = log.get('type', 'unknown').upper()
                        timestamp = log.get('timestamp', 'N/A')
                        level = log.get('level', 'N/A')
                        tag = log.get('tag', 'N/A')
                        message = log.get('message', '')
                    else:
                        log_type = "UNKNOWN"
                        timestamp = "N/A"
                        level = "N/A"
                        tag = "N/A"
                        message = str(log)
                    
                    additional_logs_html += f"""
            <div class="log-evidence" style="background: #fff3e0; border-left: 4px solid #ff9800;">
                <div class="log-header" style="color: #e65100;">⚠️ {idx}. {log_type}</div>
                <p><strong>时间:</strong> {timestamp}</p>
                <p><strong>级别:</strong> {level}</p>
                <p><strong>标签:</strong> {tag}</p>
                <p><strong>内容:</strong> {message}</p>
            </div>
"""
                
                additional_findings_html = f"""
        <h2>⚠️ 额外发现的严重问题</h2>
        <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <strong>说明:</strong> 以下问题与您描述的bug可能不直接相关，但在日志中发现了这些严重问题，请注意关注。
        </div>
        {additional_logs_html}
"""
        
        timeline_section = ""
        if timeline_data:
            critical_events_html = ""
            for e in timeline_data.get('critical_events', []):
                critical_events_html += f"""
            <div style="background: #ffebee; padding: 12px; border-radius: 4px; margin: 8px 0; border-left: 4px solid #f44336;">
                <strong>{e['timestamp']}</strong>: [{e['event_type']}] {e['summary']}
            </div>
"""
            
            timeline_section = f"""
        <h2>📊 事件时间线</h2>
        
        <h3>关键事件</h3>
        {critical_events_html}
        
        <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
            <strong>完整时间线</strong>: 共 {timeline_data.get('total_events', 0)} 个事件
        </div>
"""
        
        aloggrep_html_section = self._generate_aloggrep_html_section(aloggrep_data)
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Android Bug 分析报告</title>
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
        .log-evidence {{ background: #fafafa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 10px 0; }}
        .log-header {{ font-weight: bold; color: #d32f2f; margin-bottom: 10px; }}
        .footer {{ margin-top: 40px; color: #9e9e9e; border-top: 1px solid #e0e0e0; padding-top: 15px; }}
    </style>
</head>
<body>
    <h1>📱 Android Bug 分析报告</h1>
    <p style="color: #757575;">📅 生成时间: {datetime.now().isoformat()}</p>
    
    <div class="summary">
        <h2>1. 问题概览</h2>
        <p><strong>摘要:</strong> {bug_desc.get('summary', 'N/A')}</p>
        <p><strong>关键词:</strong> {', '.join(bug_desc.get('keywords', []))}</p>
    </div>
    
    <h2>2. 分析结果摘要</h2>
    <div class="stats">
        <div class="stat">
            <div class="stat-value">{log_data.get('crashes', 0)}</div>
            <div class="stat-label">崩溃</div>
        </div>
        <div class="stat">
            <div class="stat-value">{log_data.get('anrs', 0)}</div>
            <div class="stat-label">ANR</div>
        </div>
        <div class="stat">
            <div class="stat-value">{log_data.get('low_memory', 0)}</div>
            <div class="stat-label">低内存</div>
        </div>
        <div class="stat">
            <div class="stat-value">{log_data.get('exceptions', 0)}</div>
            <div class="stat-label">异常</div>
        </div>
    </div>
    
    {llm_section}
    {evidence_section}
    {additional_findings_html}
    {timeline_section}
    {aloggrep_html_section}
    
    <h2>3. 日志基础信息</h2>
    <p><strong>日志总数:</strong> {log_data.get('log_count', 0)}</p>
    <p><strong>日志文件:</strong> {', '.join(str(f) for f in log_data.get('log_files', []))}</p>
    
    <h2>4. 关键日志证据</h2>
"""
        
        if "critical_logs" in log_data:
            for idx, log in enumerate(log_data["critical_logs"][:5], 1):
                html_content += f"""
        <div class="log-evidence">
            <div class="log-header">📌 {idx}. {log['type'].upper()} ({log['timestamp']})</div>
            <p><strong>级别:</strong> {log['level']}</p>
            <p><strong>标签:</strong> {log['tag']}</p>
            <p><strong>内容:</strong> {log['message']}</p>
        </div>
"""
        
        html_content += """
    <div class="footer">
        <p>🤖 本报告由 Harness Engineering AI Agent 生成</p>
    </div>
</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filepath
    
    def _generate_json(self, bug_desc, log_data, llm_analysis, evidence_data, timeline_data, aloggrep_data, output_dir, base_name):
        filename = f"{base_name}.json"
        filepath = os.path.join(output_dir, filename)
        
        report_data = {
            "version": "4.0",
            "generated_at": datetime.now().isoformat(),
            "bug_description": bug_desc,
            "analysis": log_data,
            "llm_analysis": llm_analysis,
            "evidence_matching": evidence_data,
            "timeline": timeline_data,
            "aloggrep_analysis": aloggrep_data,
            "log_info": {
                "count": log_data.get('log_count', 0),
                "files": log_data.get('log_files', [])
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        return filepath
