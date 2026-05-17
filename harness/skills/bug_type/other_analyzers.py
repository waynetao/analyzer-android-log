"""
PerformanceAnalyzer - 性能问题分析器
NetworkAnalyzer - 网络问题分析器
PowerAnalyzer - 功耗问题分析器
"""
from typing import Dict, Any
from .base_analyzer import BaseBugAnalyzer, BugType


class PerformanceAnalyzer(BaseBugAnalyzer):
    """性能问题分析器"""
    
    @property
    def name(self) -> str:
        return "performance_analyzer"
    
    @property
    def bug_type(self) -> BugType:
        return BugType.PERFORMANCE
    
    def get_system_prompt(self) -> str:
        return """你是一位资深的Android性能优化专家。

性能问题包括：
1. 卡顿/掉帧（Choreographer帧率低于60fps）
2. 启动慢（超过1秒）
3. 响应慢（超过100ms）

你的任务是：
1. 分析性能指标（帧率、启动时间、响应时间）
2. 定位瓶颈（布局/渲染/逻辑/IO）
3. 提供具体的优化建议
4. 计算预期改善效果"""
    
    def get_user_prompt(self, bug_desc: Dict, log_analysis: Dict) -> str:
        prompt = f"""请分析以下性能问题，提供专业的分析报告。

【用户问题描述】
{bug_desc.get('raw_text', '未知')}

【性能日志分析摘要】
- 崩溃数: {log_analysis.get('crashes', 0)}
- ANR数: {log_analysis.get('anrs', 0)}

【性能分析任务】
请提供以下内容：

1. **性能概要**
   - 问题类型（卡顿/启动慢/响应慢）
   - 严重程度（P0/P1/P2）
   
2. **性能指标**
   - 帧率、启动时间、响应时间的表格
   - 对比标准值
   
3. **瓶颈分析**
   - 主要耗时操作（Top3）
   - 关键调用栈
   
4. **根因分析**
   - 直接原因和间接原因
   
5. **优化方案**
   - 具体优化建议（带代码示例）
   - 预期改善效果

请使用中文回答。"""
        return prompt
    
    def format_output(self, analysis: str) -> str:
        return f"""# 性能问题分析报告

---

## 1. 性能概要
{analysis[:300]}

## 2. 性能指标
{analysis[300:600]}

## 3. 瓶颈分析
{analysis[600:1000]}

## 4. 根因分析
{analysis[1000:1300]}

## 5. 优化方案
{analysis[1300:1800]}
"""
    
    def detect(self, log_analysis: Dict) -> bool:
        """检测是否是性能问题（简化版）"""
        exceptions = log_analysis.get("exceptions", [])
        keywords = ["choreographer", "jank", "fps", "卡顿", "启动慢", "响应慢"]
        for exc in exceptions:
            text = str(exc).lower()
            if any(kw in text for kw in keywords):
                return True
        return False


class NetworkAnalyzer(BaseBugAnalyzer):
    """网络问题分析器"""
    
    @property
    def name(self) -> str:
        return "network_analyzer"
    
    @property
    def bug_type(self) -> BugType:
        return BugType.NETWORK
    
    def get_system_prompt(self) -> str:
        return """你是一位资深的Android网络问题分析专家。

网络问题包括：
1. 请求超时（connect/read/write timeout）
2. 连接失败（Connection refused/reset）
3. 协议错误（HTTP 4xx/5xx）
4. 数据异常"""
    
    def get_user_prompt(self, bug_desc: Dict, log_analysis: Dict) -> str:
        prompt = f"""请分析以下网络问题。

【用户问题】
{bug_desc.get('raw_text', '未知')}

【网络分析任务】
1. **问题概要** - 错误类型、影响接口、错误码
2. **请求详情** - URL、Method、Headers、Body
3. **响应详情** - 状态码、响应时间
4. **根因分析**
5. **修复方案**
6. **预防措施**

请使用中文回答。"""
        return prompt
    
    def format_output(self, analysis: str) -> str:
        return f"# 网络问题分析报告\n\n{analysis}"
    
    def detect(self, log_analysis: Dict) -> bool:
        """检测网络问题"""
        exceptions = log_analysis.get("exceptions", [])
        keywords = ["timeout", "connection", "http", "network", "socket"]
        for exc in exceptions:
            text = str(exc).lower()
            if any(kw in text for kw in keywords):
                return True
        return False


class PowerAnalyzer(BaseBugAnalyzer):
    """功耗问题分析器"""
    
    @property
    def name(self) -> str:
        return "power_analyzer"
    
    @property
    def bug_type(self) -> BugType:
        return BugType.POWER
    
    def get_system_prompt(self) -> str:
        return """你是一位资深的Android功耗优化专家。

功耗问题包括：
1. WakeLock未释放
2. 后台服务耗电
3. GPS/网络频繁唤醒
4. AlarmManager频繁触发"""
    
    def get_user_prompt(self, bug_desc: Dict, log_analysis: Dict) -> str:
        prompt = f"""请分析以下功耗问题。

【用户问题】
{bug_desc.get('raw_text', '未知')}

【功耗分析任务】
1. **问题概要** - 问题类型、耗电程度
2. **Battery Stats分析** - 各组件耗电表格
3. **WakeLock分析** - 持有者、时长
4. **根因分析**
5. **修复方案**
6. **预防措施**

请使用中文回答。"""
        return prompt
    
    def format_output(self, analysis: str) -> str:
        return f"# 功耗问题分析报告\n\n{analysis}"
    
    def detect(self, log_analysis: Dict) -> bool:
        """检测功耗问题"""
        exceptions = log_analysis.get("exceptions", [])
        keywords = ["wakelock", "battery", "power", "alarm"]
        for exc in exceptions:
            text = str(exc).lower()
            if any(kw in text for kw in keywords):
                return True
        return False
