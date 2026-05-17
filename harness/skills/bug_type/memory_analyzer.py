"""
MemoryAnalyzer - 内存泄漏类型Bug分析器
"""
from typing import Dict, Any
from .base_analyzer import BaseBugAnalyzer, BugType


class MemoryAnalyzer(BaseBugAnalyzer):
    """Memory Leak 分析器"""
    
    @property
    def name(self) -> str:
        return "memory_analyzer"
    
    @property
    def bug_type(self) -> BugType:
        return BugType.MEMORY_LEAK
    
    def get_system_prompt(self) -> str:
        return """你是一位资深的Android内存泄漏分析专家。

内存泄漏类型：
1. Java堆泄漏 - 对象未释放
2. Native堆泄漏 - malloc/new 未释放
3. FD泄漏 - 文件/套接字未关闭

你的任务是：
1. 判断泄漏类型
2. 分析GC日志和内存趋势
3. 定位泄漏点和引用链
4. 提供修复方案
5. 给出预防措施

请始终保持专业、准确、有深度！"""
    
    def get_user_prompt(self, bug_desc: Dict, log_analysis: Dict) -> str:
        critical_logs_str = ""
        for idx, log in enumerate(log_analysis.get("critical_logs", []), 1):
            critical_logs_str += f"""
【关键日志 {idx}】
- 类型: {log['type']}
- 内容: {log['message']}
"""
        
        prompt = f"""请分析以下内存泄漏问题，提供专业的分析报告。

【用户问题描述】
{bug_desc.get('raw_text', '未知')}

【内存日志分析摘要】
- 崩溃数: {log_analysis.get('crashes', 0)}
- ANR数: {log_analysis.get('anrs', 0)}
- 低内存: {log_analysis.get('low_memory', 0)}
- 异常数: {log_analysis.get('exceptions', 0)}

{critical_logs_str}

【内存泄漏分析任务】
请提供以下内容：

1. **内存问题概要**
   - 泄漏类型（Java Heap / Native Heap / FD）
   - 泄漏大小（估算）
   - 泄漏速率（估算）
   
2. **内存使用分析**
   - 当前使用 / 可用内存 / 峰值
   - GC日志分析（GC频率、GC后释放情况）
   - Allocation Tracker（主要分配者）
   
3. **泄漏点定位**
   - 可疑对象类型和数量
   - 引用链（GC Root → ... → 泄漏对象）
   
4. **根因分析**
   - 直接原因（具体说明）
   - 常见场景（Activity/Fragment/Callback等）
   
5. **修复方案**
   - 方案1：使用WeakReference（推荐）
   - 方案2：onDestroy中清理资源
   - 方案3：使用LeakCanary
   
6. **预防检查清单**
   - [ ] 内存监控
   - [ ] LeakCanary集成
   - [ ] 测试建议

请使用中文回答，保持专业和准确。"""
        
        return prompt
    
    def format_output(self, analysis: str) -> str:
        return f"""# Memory Leak 分析报告

---

## 1. 内存问题概要
{self._extract_memory_summary(analysis)}

## 2. 内存使用分析
{self._extract_memory_usage(analysis)}

## 3. GC 日志分析
{self._extract_gc_analysis(analysis)}

## 4. 泄漏点定位
```
{self._extract_leak_points(analysis)}
```

## 5. 根因分析
{self._extract_root_cause(analysis)}

## 6. 修复方案
{self._extract_fix_suggestions(analysis)}

## 7. 预防检查
{self._extract_prevention_checklist(analysis)}
"""
    
    def detect(self, log_analysis: Dict) -> bool:
        """检测是否是 Memory Leak 类型"""
        low_memory = log_analysis.get("low_memory", 0)
        exceptions = log_analysis.get("exceptions", [])
        
        has_oom = any("OutOfMemory" in str(exc) for exc in exceptions)
        
        return low_memory > 0 or has_oom
    
    def _extract_memory_summary(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "内存问题概要" in line or "1." in line:
                return '\n'.join(lines[i:i+10])
        return "内存问题概要"
    
    def _extract_memory_usage(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "内存使用" in line or "2." in line:
                return '\n'.join(lines[i:i+10])
        return "内存使用分析"
    
    def _extract_gc_analysis(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "GC" in line and "分析" in line or "3." in line:
                return '\n'.join(lines[i:i+10])
        return "GC日志分析"
    
    def _extract_leak_points(self, analysis: str) -> str:
        if "```" in analysis:
            parts = analysis.split("```")
            for i in range(len(parts)-1):
                if "引用链" in parts[i] or "GC Root" in parts[i]:
                    return parts[i].strip()
        return "泄漏点信息需要从原日志中提取"
    
    def _extract_root_cause(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "根因分析" in line or "5." in line:
                return '\n'.join(lines[i:i+12])
        return "根因分析"
    
    def _extract_fix_suggestions(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "修复方案" in line or "6." in line:
                return '\n'.join(lines[i:i+12])
        return "修复建议"
    
    def _extract_prevention_checklist(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "预防检查" in line or "7." in line or "checklist" in line:
                return '\n'.join(lines[i:])
        return "- [ ] 内存监控"
