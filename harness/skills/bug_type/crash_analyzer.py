"""
CrashAnalyzer - Crash类型Bug分析器
"""
from typing import Dict, Any
from .base_analyzer import BaseBugAnalyzer, BugType


class CrashAnalyzer(BaseBugAnalyzer):
    """Crash 分析器"""
    
    @property
    def name(self) -> str:
        return "crash_analyzer"
    
    @property
    def bug_type(self) -> BugType:
        return BugType.CRASH
    
    def get_system_prompt(self) -> str:
        return """你是一位资深的Android Crash分析专家。

你的任务是：
1. 分析 Crash 堆栈，找到真正的根因
2. 定位问题代码的具体位置（包名、类、方法、行号）
3. 解释 Crash 的直接原因和间接原因
4. 提供可操作的修复建议
5. 给出预防检查清单

请始终保持专业、准确、有深度。所有结论必须有日志证据支撑！"""
    
    def get_user_prompt(self, bug_desc: Dict, log_analysis: Dict) -> str:
        # 格式化关键日志
        critical_logs_str = ""
        for idx, log in enumerate(log_analysis.get("critical_logs", []), 1):
            critical_logs_str += f"""
【关键日志 {idx}】
- 类型: {log['type']}
- 时间: {log['timestamp']}
- 级别: {log['level']}
- 标签: {log['tag']}
- 内容: {log['message']}
"""
        
        prompt = f"""请分析以下 Crash 问题，提供专业的分析报告。

【用户问题描述】
{bug_desc.get('raw_text', '未知')}

【Crash 日志分析摘要】
- 崩溃数: {log_analysis.get('crashes', 0)}
- ANR数: {log_analysis.get('anrs', 0)}
- 低内存: {log_analysis.get('low_memory', 0)}
- 异常数: {log_analysis.get('exceptions', 0)}

{critical_logs_str}

【Crash 分析任务】
请提供以下内容：

1. **崩溃概要**
   - 崩溃类型（Java Crash / Native Crash / Tombstone）
   - 具体异常类名
   - 进程和线程信息

2. **堆栈分析**
   - 找到并高亮崩溃的第一行（"Caused by"）
   - 分析具体类、方法和行号
   - 判断是我们的代码还是第三方SDK代码
   
3. **根因分析**
   - 直接原因（具体发生了什么）
   - 间接原因（为什么会这样）
   - 可能的触发场景
   
4. **修复方案**
   - 方案1（推荐）
   - 方案2（备选）
   - 具体的代码修改建议
   
5. **预防检查清单**
   - [ ] 代码检查项1
   - [ ] 代码检查项2
   - [ ] 测试建议
   
请使用中文回答，保持专业和准确。"""
        
        return prompt
    
    def format_output(self, analysis: str) -> str:
        """格式化输出，确保是标准的 Crash 报告格式"""
        output = f"""# Crash 分析报告

---

## 1. 崩溃概要
{self._extract_summary(analysis)}

## 2. 崩溃堆栈分析
```
{self._extract_stacktrace(analysis)}
```

## 3. 根因分析
{self._extract_root_cause(analysis)}

## 4. 修复方案
{self._extract_fix_suggestions(analysis)}

## 5. 预防检查
{self._extract_prevention_checklist(analysis)}
"""
        return output
    
    def detect(self, log_analysis: Dict) -> bool:
        """检测是否是 Crash 类型"""
        crashes = log_analysis.get("crashes", 0)
        anrs = log_analysis.get("anrs", 0)
        
        # 如果有 crash 且 crash 数量 > anr，优先判断为 crash
        return crashes > 0 and crashes > anrs
    
    def _extract_summary(self, analysis: str) -> str:
        """从分析中提取概要"""
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "崩溃概要" in line or "1." in line:
                return '\n'.join(lines[i:i+10])
        return analysis[:200]
    
    def _extract_stacktrace(self, analysis: str) -> str:
        """提取堆栈跟踪"""
        if "```" in analysis:
            parts = analysis.split("```")
            for i in range(len(parts)-1):
                if "at " in parts[i] or "Caused by" in parts[i]:
                    return parts[i].strip()
        return "堆栈信息需要从原日志中提取"
    
    def _extract_root_cause(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "根因分析" in line or "3." in line:
                return '\n'.join(lines[i:i+15])
        return "根因分析"
    
    def _extract_fix_suggestions(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "修复方案" in line or "4." in line:
                return '\n'.join(lines[i:i+15])
        return "修复建议"
    
    def _extract_prevention_checklist(self, analysis: str) -> str:
        lines = analysis.split('\n')
        for i, line in enumerate(lines):
            if "预防检查" in line or "5." in line or "checklist" in line:
                return '\n'.join(lines[i:])
        return "- [ ] 检查空指针"
