"""
ANRAnalyzer - ANR类型Bug分析器
"""
from typing import Dict, Any
from .base_analyzer import BaseBugAnalyzer, BugType
from harness.skills.log_format_utils import format_critical_logs


class ANRAnalyzer(BaseBugAnalyzer):
    """ANR 分析器"""
    
    @property
    def name(self) -> str:
        return "anr_analyzer"
    
    @property
    def bug_type(self) -> BugType:
        return BugType.ANR
    
    def get_system_prompt(self) -> str:
        return """你是一位资深的Android ANR分析专家。

ANR (Application Not Responding) 通常是因为主线程被阻塞：
- Input dispatching timed out (5秒)
- Service timeout (20秒)
- Broadcast timeout (10秒)
- ContentProvider timeout

你的任务是：
1. 判断 ANR 类型
2. 分析主线程被阻塞的原因
3. 找到耗时操作和阻塞点
4. 分析锁竞争（如果有）
5. 提供具体的修复方案

请始终保持专业、准确、有深度！"""
    
    def get_user_prompt(self, bug_desc: Dict, log_analysis: Dict) -> str:
        critical_logs_str = format_critical_logs(log_analysis.get("critical_logs", []))
        
        prompt = f"""请分析以下 ANR 问题，提供专业的分析报告。

【用户问题描述】
{bug_desc.get('raw_text', '未知')}

【ANR 日志分析摘要】
- 崩溃数: {log_analysis.get('crashes', 0)}
- ANR数: {log_analysis.get('anrs', 0)}
- 低内存: {log_analysis.get('low_memory', 0)}
- 异常数: {log_analysis.get('exceptions', 0)}

{critical_logs_str}

【ANR 分析任务】
请提供以下内容：

1. **ANR 概要**
   - ANR 类型（Input / Service / Broadcast / Provider）
   - 进程信息
   - 超时时间（估算）
   
2. **主线程分析**
   - 主线程状态（RUNNING / WAITING / BLOCKED）
   - 阻塞原因（I/O / 锁等待 / 计算密集）
   - 等待的锁（如果有）
   
3. **阻塞点定位**
   - 找到耗时操作（耗时 > 100ms 的方法）
   - 列出关键耗时
   - 主线程调用栈
   
4. **根因分析**
   - 直接原因（具体说明）
   - 间接原因
   - 代码位置（文件:行号）
   
5. **修复方案**
   - 方案1：将耗时操作移到后台线程（推荐）
   - 方案2：优化锁使用
   - 方案3：优化I/O操作
   
6. **预防检查清单**
   - [ ] StrictMode 启用检查
   - [ ] 主线程I/O检查
   - [ ] 锁使用检查
   - [ ] 测试建议

请使用中文回答，保持专业和准确。"""
        
        return prompt
    
    def format_output(self, analysis: str) -> str:
        return f"""# ANR 分析报告

---

## 1. ANR 概要
{self._extract_anr_summary(analysis)}

## 2. 主线程分析
{self._extract_main_thread_analysis(analysis)}

## 3. 阻塞点定位
```
{self._extract_blocking_points(analysis)}
```

## 4. 根因分析
{self._extract_root_cause(analysis)}

## 5. 修复方案
{self._extract_fix_suggestions(analysis)}

## 6. 预防检查
{self._extract_prevention_checklist(analysis)}
"""
    
    def detect(self, log_analysis: Dict) -> bool:
        """检测是否是 ANR 类型"""
        anrs = log_analysis.get("anrs", 0)
        crashes = log_analysis.get("crashes", 0)
        
        return anrs > 0 and anrs > crashes
    
    def _extract_anr_summary(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "ANR 概要" in line or "1." in line:
                return '\n'.join(lines[i:i+10])
        return "ANR概要"
    
    def _extract_main_thread_analysis(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "主线程分析" in line or "2." in line:
                return '\n'.join(lines[i:i+12])
        return "主线程分析"
    
    def _extract_blocking_points(self, analysis: str) -> str:
        if "```" in analysis:
            parts = analysis.split("```")
            for i in range(len(parts)-1):
                if "main" in parts[i].lower() or "线程" in parts[i]:
                    return parts[i].strip()
        return "阻塞点信息需要从原日志中提取"
    
    def _extract_root_cause(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "根因分析" in line or "4." in line:
                return '\n'.join(lines[i:i+12])
        return "根因分析"
    
    def _extract_fix_suggestions(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "修复方案" in line or "5." in line:
                return '\n'.join(lines[i:i+12])
        return "修复建议"
    
    def _extract_prevention_checklist(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "预防检查" in line or "6." in line or "checklist" in line:
                return '\n'.join(lines[i:])
        return "- [ ] StrictMode 检查"
