"""
aloggrep 增强版包装器 - 包含异常检测和多维度分析
这是在alogrep_wrapper.py基础上的增强版本
"""
import json
from typing import Dict, Any, List, Optional
from log_analyzer.aloggrep_wrapper import ALogGrep, LogLevel


class ALogGrepEnhanced(ALogGrep):
    """aloggrep 增强版包装器,添加异常检测和多维度分析"""
    
    def parse_histogram_with_anomalies(self, log_path: str, interval: str = "1m") -> Dict[str, Any]:
        """
        解析直方图并提取异常检测结果
        
        Args:
            log_path: 日志文件路径
            interval: 时间间隔,如 '1m', '5m', '1h'
            
        Returns:
            包含异常时间点的分析结果
        """
        result = self.histogram(log_path, interval)
        
        if not result["success"] or "data" not in result:
            return {
                "success": False,
                "anomalies": [],
                "normal_bins": [],
                "stats": {}
            }
        
        histogram_data = result["data"]
        
        # 提取异常检测结果
        anomalies = []
        normal_bins = []
        
        if "bins" in histogram_data:
            for bin_data in histogram_data["bins"]:
                if bin_data.get("is_anomaly"):
                    anomalies.append({
                        "timestamp": bin_data.get("timestamp"),
                        "count": bin_data.get("count"),
                        "reason": bin_data.get("anomaly_reason", "High activity detected"),
                        "by_level": bin_data.get("by_level", {}),
                        "severity": self._calculate_anomaly_severity(bin_data)
                    })
                else:
                    normal_bins.append(bin_data)
        
        return {
            "success": True,
            "anomalies": anomalies,
            "normal_bins": normal_bins,
            "stats": histogram_data.get("stats", {}),
            "interval": interval,
            "total_anomalies": len(anomalies)
        }
    
    def _calculate_anomaly_severity(self, bin_data: Dict[str, Any], stats: Dict[str, Any] = None) -> str:
        """
        计算异常严重程度
        
        Args:
            bin_data: 直方图的单个bin数据
            stats: 统计信息(可选)
            
        Returns:
            严重程度字符串: critical, high, medium, low
        """
        count = bin_data.get("count", 0)
        
        # 使用stats中的阈值
        if stats:
            mean = stats.get("mean", 0)
            threshold = stats.get("threshold", mean * 1.5)
        else:
            # 简单的启发式计算
            threshold = count * 0.8
        
        # 计算偏离程度
        if stats and "std" in stats:
            std = stats["std"]
            if std > 0:
                z_score = (count - mean) / std
                if z_score > 3:
                    return "critical"
                elif z_score > 2:
                    return "high"
                elif z_score > 1:
                    return "medium"
                else:
                    return "low"
        
        # 基于阈值的判断
        if count > threshold * 2:
            return "critical"
        elif count > threshold * 1.5:
            return "high"
        elif count > threshold:
            return "medium"
        else:
            return "low"
    
    def comprehensive_analysis(self, log_path: str) -> Dict[str, Any]:
        """
        综合分析 - 获取完整分析结果
        
        Args:
            log_path: 日志文件路径
            
        Returns:
            完整的分析结果,包含所有维度的数据
        """
        analysis = {
            "available": self.available,
            "basic_stats": {},
            "crashes": [],
            "anomalies": [],
            "dedupe": {},
            "error_tags": [],
            "time_range": {}
        }
        
        if not self.available:
            return analysis
        
        # 1. 获取摘要
        summary_result = self.summary(log_path)
        if summary_result["success"] and "data" in summary_result:
            analysis["basic_stats"] = summary_result["data"]
            analysis["time_range"] = summary_result["data"].get("time_range", {})
        
        # 2. 获取崩溃
        crashes_result = self.crashes(log_path)
        if crashes_result["success"] and "data" in crashes_result:
            analysis["crashes"] = crashes_result["data"]
        
        # 3. 获取异常时间点
        anomalies_result = self.parse_histogram_with_anomalies(log_path, "1m")
        if anomalies_result["success"]:
            analysis["anomalies"] = anomalies_result["anomalies"]
        
        # 4. 获取去重结果
        dedupe_result = self.dedupe(log_path, 20)
        if dedupe_result["success"] and dedupe_result["stdout"]:
            try:
                analysis["dedupe"] = json.loads(dedupe_result["stdout"])
            except json.JSONDecodeError:
                pass
        
        # 5. 获取错误标签统计
        error_result = self.filter(log_path, level=LogLevel.E, limit=500, format="json")
        if error_result["success"]:
            error_entries = []
            for line in error_result["stdout"].strip().split("\n"):
                if line:
                    try:
                        error_entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            
            # 统计标签
            tag_counts = {}
            for entry in error_entries:
                if isinstance(entry, dict):
                    tag = entry.get("tag", "Unknown")
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            analysis["error_tags"] = sorted(
                [{"tag": k, "count": v} for k, v in tag_counts.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:10]
        
        return analysis
    
    def analyze_by_time_windows(
        self, 
        log_path: str, 
        windows: List[str]
    ) -> Dict[str, Any]:
        """
        按多个时间窗口分析日志
        
        Args:
            log_path: 日志文件路径
            windows: 时间窗口列表,如 ['1m', '5m', '10m']
            
        Returns:
            各时间窗口的分析结果
        """
        results = {}
        
        for window in windows:
            hist_result = self.histogram(log_path, window)
            if hist_result["success"] and "data" in hist_result:
                results[window] = {
                    "bins": hist_result["data"].get("bins", []),
                    "stats": hist_result["data"].get("stats", {}),
                    "anomalies": self._extract_anomalies_from_bins(
                        hist_result["data"].get("bins", [])
                    )
                }
        
        return results
    
    def _extract_anomalies_from_bins(self, bins: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从bins中提取异常"""
        
        anomalies = []
        for bin_data in bins:
            if bin_data.get("is_anomaly"):
                anomalies.append({
                    "timestamp": bin_data.get("timestamp"),
                    "count": bin_data.get("count"),
                    "reason": bin_data.get("anomaly_reason", "Anomaly detected")
                })
        
        return anomalies
    
    def generate_analysis_report(self, log_path: str, format: str = "markdown") -> Dict[str, Any]:
        """
        生成分析报告
        
        Args:
            log_path: 日志文件路径
            format: 报告格式,支持 'markdown', 'json', 'html'
            
        Returns:
            生成的报告内容
        """
        # 执行综合分析
        analysis = self.comprehensive_analysis(log_path)
        
        if format == "json":
            return {
                "success": True,
                "format": "json",
                "content": json.dumps(analysis, indent=2, ensure_ascii=False)
            }
        elif format == "markdown":
            content = self._generate_markdown_report(analysis)
            return {
                "success": True,
                "format": "markdown",
                "content": content
            }
        elif format == "html":
            content = self._generate_html_report(analysis)
            return {
                "success": True,
                "format": "html",
                "content": content
            }
        else:
            return {
                "success": False,
                "error": f"Unsupported format: {format}"
            }
    
    def _generate_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """生成Markdown格式报告"""
        
        md = "# Android日志分析报告\n\n"
        
        # 基本统计
        md += "## 📊 基本统计\n\n"
        stats = analysis.get("basic_stats", {})
        md += f"- 总日志数: {stats.get('total_entries', 'N/A')}\n"
        md += f"- 崩溃数: {len(analysis.get('crashes', []))}\n"
        
        level_dist = stats.get("level_distribution", {})
        md += f"- 错误(W): {level_dist.get('W', 0)}\n"
        md += f"- 错误(E): {level_dist.get('E', 0)}\n"
        md += f"- 致命(F): {level_dist.get('F', 0)}\n\n"
        
        # 异常时间点
        md += "## 🔍 异常时间点\n\n"
        anomalies = analysis.get("anomalies", [])
        if anomalies:
            for anomaly in anomalies[:5]:
                md += f"- **{anomaly['timestamp']}**: {anomaly['count']} 条日志\n"
                md += f"  - 原因: {anomaly['reason']}\n"
        else:
            md += "未发现明显异常时间点\n"
        md += "\n"
        
        # 崩溃详情
        md += "## 💥 崩溃详情\n\n"
        crashes = analysis.get("crashes", [])
        if crashes:
            for i, crash in enumerate(crashes[:5], 1):
                md += f"### {i}. {crash.get('exception', 'Unknown')}\n"
                md += f"- 时间: {crash.get('timestamp', 'N/A')}\n"
                md += f"- 线程: {crash.get('thread', 'N/A')}\n"
                if "message" in crash:
                    md += f"- 消息: {crash['message'][:100]}...\n"
                md += "\n"
        else:
            md += "未发现崩溃\n\n"
        
        # 高频错误标签
        md += "## 🏷️ 高频错误标签\n\n"
        error_tags = analysis.get("error_tags", [])
        if error_tags:
            for tag_info in error_tags[:5]:
                md += f"- {tag_info['tag']}: {tag_info['count']} 次\n"
        else:
            md += "无错误标签统计\n"
        md += "\n"
        
        # 时间范围
        md += "## ⏰ 时间范围\n\n"
        time_range = analysis.get("time_range", {})
        md += f"- 开始: {time_range.get('start', 'N/A')}\n"
        md += f"- 结束: {time_range.get('end', 'N/A')}\n"
        
        return md
    
    def _generate_html_report(self, analysis: Dict[str, Any]) -> str:
        """生成HTML格式报告"""
        
        stats = analysis.get("basic_stats", {})
        crashes = analysis.get("crashes", [])
        anomalies = analysis.get("anomalies", [])
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Android日志分析报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        h1 {{ color: #2196F3; border-bottom: 2px solid #2196F3; }}
        h2 {{ color: #333; margin-top: 30px; }}
        .stat-card {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        .crash {{ background: #ffebee; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #f44336; }}
        .anomaly {{ background: #fff3e0; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #ff9800; }}
    </style>
</head>
<body>
    <h1>📱 Android日志分析报告</h1>
    
    <h2>📊 基本统计</h2>
    <div class="stat-card">
        <p>总日志数: <strong>{stats.get('total_entries', 'N/A')}</strong></p>
        <p>崩溃数: <strong>{len(crashes)}</strong></p>
    </div>
    
    <h2>🔍 异常时间点 ({len(anomalies)} 个)</h2>
"""
        
        for anomaly in anomalies[:5]:
            html += f"""
    <div class="anomaly">
        <strong>{anomaly['timestamp']}</strong>: {anomaly['count']} 条日志
        <p>原因: {anomaly['reason']}</p>
    </div>
"""
        
        html += """
    <h2>💥 崩溃详情</h2>
"""
        
        for i, crash in enumerate(crashes[:5], 1):
            html += f"""
    <div class="crash">
        <h3>{i}. {crash.get('exception', 'Unknown')}</h3>
        <p>时间: {crash.get('timestamp', 'N/A')}</p>
        <p>线程: {crash.get('thread', 'N/A')}</p>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
