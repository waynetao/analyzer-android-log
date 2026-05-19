"""
MultiRoundAnalysisSkill - 多轮深度分析技能
采用三轮对话流程，实现深度日志分析
"""
from typing import Dict, Any, List
from .base import BaseSkill, SkillResult, LLMBasedSkill
from harness.core.logging import get_logger

logger = get_logger(__name__)


class MultiRoundAnalysisSkill(LLMBasedSkill):
    """多轮深度分析技能 - 三轮对话实现高质量分析
    
    第一轮：全景扫描 - 快速定位问题类型和范围
    第二轮：深度挖掘 - 深入验证假设，构建证据链
    第三轮：验证优化 - 验证结论，提供最佳修复方案
    """
    
    @property
    def name(self) -> str:
        return "multi_round_analysis"
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        super().__init__(api_key, base_url, model, scene="multi_round_analysis")
        # 三轮分析的配置
        self.max_tokens_rounds = [8000, 12000, 8000]  # 每轮的最大token数
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["bug_description", "advanced_log_analysis"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        try:
            bug_desc = inputs["bug_description"]
            
            # 处理不同的输入格式
            advanced_log_analysis = inputs["advanced_log_analysis"]
            if isinstance(advanced_log_analysis, dict) and "data" in advanced_log_analysis:
                log_analysis = advanced_log_analysis["data"]
            elif isinstance(advanced_log_analysis, dict):
                log_analysis = advanced_log_analysis
            else:
                log_analysis = advanced_log_analysis
            
            # 执行三轮分析
            results = self._run_multi_round_analysis(bug_desc, log_analysis)
            
            # 整合结果
            final_result = self._compile_results(results, bug_desc, log_analysis)
            
            return SkillResult(
                True,
                final_result,
                f"多轮分析完成：{len(results)} 轮分析"
            )
            
        except Exception as e:
            logger.error(f"多轮分析失败: {e}", exc_info=True)
            return SkillResult(False, {}, f"多轮分析失败: {str(e)}")
    
    def _run_multi_round_analysis(self, bug_desc: Dict, log_analysis: Dict) -> List[Dict[str, Any]]:
        """执行三轮分析"""
        results = []
        
        # ========== 第一轮：全景扫描 ==========
        logger.info("开始第一轮分析：全景扫描")
        round1_result = self._round1_broad_scan(bug_desc, log_analysis)
        results.append(round1_result)
        
        # ========== 第二轮：深度挖掘 ==========
        logger.info("开始第二轮分析：深度挖掘")
        round2_result = self._round2_deep_dive(bug_desc, log_analysis, round1_result)
        results.append(round2_result)
        
        # ========== 第三轮：验证优化 ==========
        logger.info("开始第三轮分析：验证优化")
        round3_result = self._round3_validation(bug_desc, log_analysis, round1_result, round2_result)
        results.append(round3_result)
        
        return results
    
    def _round1_broad_scan(self, bug_desc: Dict, log_analysis: Dict) -> Dict[str, Any]:
        """第一轮：全景扫描"""
        
        # 格式化日志摘要
        logs_summary = self._format_log_summary(log_analysis)
        
        system_prompt = """你是一位经验丰富的Android问题诊断专家，擅长从海量日志中快速定位问题。

你的任务是全面扫描日志，识别所有异常模式。
请自由分析，不要受任何模板限制，用你最擅长的方式进行分析。"""
        
        user_prompt = f"""【用户问题描述】
{bug_desc.get('raw_text', '未知')}

【日志分析摘要】
- 崩溃数: {log_analysis.get('crashes', 0)}
- ANR数: {log_analysis.get('anrs', 0)}
- 低内存: {log_analysis.get('low_memory', 0)}
- 异常数: {log_analysis.get('exceptions', 0)}

【关键日志片段】
{logs_summary}

【分析任务】
请全面分析这份日志，回答以下问题：

1. 这份日志中有哪些异常模式？（崩溃、ANR、内存、异常等）
2. 哪些问题与用户描述的现象最相关？
3. 问题的严重程度如何？
4. 初步判断可能的根因方向是什么？
5. 有没有发现其他值得关注的问题？

请详细分析，不要省略任何重要发现。"""
        
        if self.use_mock:
            response = self._get_mock_round1()
        else:
            response = super()._call_llm(
                system_prompt,
                user_prompt,
                max_tokens=self.max_tokens_rounds[0]
            )
        
        return {
            "round": 1,
            "name": "全景扫描",
            "analysis": response,
            "key_findings": self._extract_key_findings(response)
        }
    
    def _round2_deep_dive(self, bug_desc: Dict, log_analysis: Dict, 
                         round1_result: Dict[str, Any]) -> Dict[str, Any]:
        """第二轮：深度挖掘"""
        
        # 格式化详细日志
        detailed_logs = self._format_detailed_logs(log_analysis)
        
        system_prompt = """你是一位资深的Android技术专家，精通源码和系统机制。
请基于第一轮的发现，深入挖掘问题的根因。"""
        
        user_prompt = f"""【用户问题描述】
{bug_desc.get('raw_text', '未知')}

【第一轮分析结果】
{round1_result['analysis']}

【第一轮关键发现】
{chr(10).join(f"- {finding}" for finding in round1_result['key_findings'])}

【详细日志片段】
{detailed_logs}

【深度分析任务】
请深入分析，回答以下问题：

1. 详细追踪问题的完整发生过程（从用户操作到最终崩溃）
2. 找出所有相关的日志证据，构建证据链
3. 分析问题的真正根因（不仅仅是表面现象）
4. 重建事件时间线（精确到秒）
5. 分析这个问题涉及哪些系统组件或代码模块
6. 评估修复这个问题需要修改哪些代码

请详细分析，你可以自由发挥，不要省略任何重要细节。"""
        
        if self.use_mock:
            response = self._get_mock_round2()
        else:
            response = super()._call_llm(
                system_prompt,
                user_prompt,
                max_tokens=self.max_tokens_rounds[1]
            )
        
        return {
            "round": 2,
            "name": "深度挖掘",
            "analysis": response,
            "key_findings": self._extract_key_findings(response),
            "evidence_chain": self._extract_evidence_chain(response)
        }
    
    def _round3_validation(self, bug_desc: Dict, log_analysis: Dict,
                           round1_result: Dict[str, Any],
                           round2_result: Dict[str, Any]) -> Dict[str, Any]:
        """第三轮：验证优化"""
        
        system_prompt = """你是一位顶级的Android技术专家，负责代码审查和问题诊断。
你的任务是验证前两轮的分析，并提供最终的修复方案。"""
        
        user_prompt = f"""【用户问题描述】
{bug_desc.get('raw_text', '未知')}

【第一轮全景扫描结果】
{round1_result['analysis']}

【第二轮深度挖掘结果】
{round2_result['analysis']}

【分析任务】
请验证和优化前两轮的分析，回答以下问题：

1. 前两轮的分析是否有遗漏或矛盾？
2. 置信度评估：
   - 根因分析的置信度（0-100%）
   - 修复方案的可行性（0-100%）
3. 最可能的根因是什么？（如果还有不确定性，请说明）
4. 最具体的修复步骤是什么？
   - 需要修改哪些文件
   - 需要修改哪些代码
   - 修改的具体逻辑是什么
5. 如何预防类似问题？
6. 这个问题的影响范围有多大？
7. 修复的优先级是什么？

最后，用一段话（200字以内）总结这个问题。

请结构化输出你的分析。"""
        
        if self.use_mock:
            response = self._get_mock_round3()
        else:
            response = super()._call_llm(
                system_prompt,
                user_prompt,
                max_tokens=self.max_tokens_rounds[2]
            )
        
        return {
            "round": 3,
            "name": "验证优化",
            "analysis": response,
            "confidence": self._extract_confidence(response)
        }
    
    def _format_log_summary(self, log_analysis: Dict) -> str:
        """格式化日志摘要"""
        summary_parts = []
        
        for log in log_analysis.get("critical_logs", [])[:10]:
            if isinstance(log, dict):
                summary_parts.append(f"[{log.get('timestamp', '')}] {log.get('level', '')} {log.get('tag', '')}: {log.get('message', '')[:150]}")
            else:
                summary_parts.append(str(log)[:150])
        
        return "\n".join(summary_parts) if summary_parts else "无关键日志"
    
    def _format_detailed_logs(self, log_analysis: Dict) -> str:
        """格式化详细日志"""
        detailed_parts = []
        
        for idx, log in enumerate(log_analysis.get("critical_logs", [])[:20], 1):
            if isinstance(log, dict):
                detailed_parts.append(f"""
【日志 {idx}】
- 类型: {log.get('type', 'unknown')}
- 时间: {log.get('timestamp', 'N/A')}
- 级别: {log.get('level', 'N/A')}
- 标签: {log.get('tag', 'N/A')}
- 内容: {log.get('message', '')}
""")
        
        return "\n".join(detailed_parts) if detailed_parts else "无详细日志"
    
    def _extract_key_findings(self, text: str) -> List[str]:
        """提取关键发现"""
        # 简单的关键词提取
        findings = []
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if line and (line.startswith("1.") or line.startswith("2.") or 
                        line.startswith("3.") or "发现" in line or 
                        ":" in line):
                findings.append(line[:100])
        return findings[:5]
    
    def _extract_evidence_chain(self, text: str) -> List[str]:
        """提取证据链"""
        evidence = []
        if "时间线" in text:
            start = text.find("时间线")
            evidence.append(text[start:start+500])
        return evidence
    
    def _extract_confidence(self, text: str) -> Dict[str, float]:
        """提取置信度"""
        confidence = {"root_cause": 0.85, "fix_feasibility": 0.80}
        if "置信度" in text:
            import re
            match = re.search(r'(\d+)%', text)
            if match:
                confidence["root_cause"] = int(match.group(1)) / 100
        return confidence
    
    def _compile_results(self, results: List[Dict[str, Any]], 
                        bug_desc: Dict, log_analysis: Dict) -> Dict[str, Any]:
        """整合三轮分析结果"""
        
        compiled = {
            "multi_round_enabled": True,
            "total_rounds": len(results),
            "rounds": results,
            "summary": self._generate_summary(results),
            "key_insights": self._compile_key_insights(results),
            "recommended_fix": self._compile_recommended_fix(results),
            "confidence": results[-1].get("confidence", {"root_cause": 0.85, "fix_feasibility": 0.80})
        }
        
        return compiled
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> str:
        """生成总结"""
        summaries = []
        for result in results:
            summaries.append(f"【{result['name']}】\n{result['analysis'][:300]}...")
        return "\n\n".join(summaries)
    
    def _compile_key_insights(self, results: List[Dict[str, Any]]) -> List[str]:
        """编译关键洞察"""
        insights = []
        for result in results:
            insights.extend(result.get('key_findings', []))
        return list(set(insights))[:10]
    
    def _compile_recommended_fix(self, results: List[Dict[str, Any]]) -> str:
        """编译推荐修复方案"""
        # 从第三轮提取修复建议
        if len(results) >= 3:
            round3 = results[-1]['analysis']
            # 简单提取修复相关部分
            if "修复" in round3 or "fix" in round3.lower():
                return round3
        return "请参考详细分析"
    
    def _get_mock_round1(self) -> str:
        """模拟第一轮分析结果"""
        return """## 第一轮：全景扫描分析

### 异常模式识别

通过扫描日志，我发现了以下异常模式：

1. **崩溃问题** (最严重)
   - 发现1个Fatal Exception
   - 类型：NullPointerException
   - 发生位置：MainActivity.java 第36行
   - 影响：应用启动时立即崩溃

2. **内存问题** (次要)
   - 发现多个low memory warning
   - 堆内存使用率达到90%以上
   - 可能与崩溃有间接关系

3. **ANR问题** (轻微)
   - 发现1个ANR事件
   - 发生在崩溃之后（后续问题）

### 相关性分析

**与用户描述高度相关**：
- 用户描述："应用打开就崩溃"
- 日志显示：MainActivity启动时NullPointerException
- 时间吻合：都是在应用启动阶段

**额外发现**：
- 系统存在内存压力，可能加剧了崩溃的发生

### 初步根因假设

最可能的根因：
1. MainActivity.onCreate()中访问了未初始化的View
2. findViewById()可能返回了null
3. 内存压力可能加速了这个问题的暴露

### 严重程度评估

- **严重程度**：高
- **影响范围**：应用完全无法使用
- **复现概率**：100%（必现）
- **修复优先级**：P0"""
    
    def _get_mock_round2(self) -> str:
        """模拟第二轮分析结果"""
        return """## 第二轮：深度挖掘分析

### 完整事件追踪

通过深入分析，我重建了以下事件序列：

```
11:25:30.123 - 用户点击应用图标
11:25:30.156 - ActivityManager 启动应用进程
11:25:30.234 - MainActivity.onCreate() 开始执行
11:25:30.267 - setContentView(R.layout.activity_main) 被调用
11:25:30.289 - findViewById(R.id.button_submit) 被调用
11:25:30.290 - findViewById 返回 null ⚠️
11:25:30.291 - button.setVisibility() 被调用 → NullPointerException 💥
11:25:30.292 - 应用崩溃
```

### 根因分析

**真正根因**：
`activity_main.xml` 布局文件中，`button_submit` 这个ID不存在或者名称不匹配。

**证据链**：
1. R.id.button_submit 返回 null
2. Android在findViewById时找不到对应View
3. 代码中没有进行null检查就直接使用

### 涉及组件

- **Activity**: MainActivity
- **Layout**: activity_main.xml  
- **View**: button_submit
- **Android Framework**: findViewById机制

### 修复分析

需要修改的文件和位置：
1. `activity_main.xml` - 检查button_submit ID
2. `MainActivity.java:36` - 添加null检查"""
    
    def _get_mock_round3(self) -> str:
        """模拟第三轮分析结果"""
        return """## 第三轮：验证与优化

### 分析验证

**前两轮分析一致性**：✅ 高
- 两轮分析都指向同一个根因
- 没有发现明显矛盾

**置信度评估**：
- 根因分析置信度：**92%**
- 修复方案可行性：**88%**

### 根因确认

**最可能的根因**：
activity_main.xml中缺少button_submit的定义，或者ID名称不匹配（可能使用了buttonSubmit命名）。

### 具体修复步骤

#### 步骤1：检查布局文件
打开 `res/layout/activity_main.xml`，确认是否有以下代码：
```xml
<Button
    android:id="@+id/button_submit"
    ... />
```

如果ID是`buttonSubmit`，需要改为`button_submit`；如果完全没有这个Button，需要添加。

#### 步骤2：修改Activity代码
在 `MainActivity.java` 第36行添加null检查：
```java
Button button = findViewById(R.id.button_submit);
if (button != null) {
    button.setVisibility(View.VISIBLE);
}
```

### 预防措施

1. 使用Android Studio的布局预览功能验证ID
2. 添加lint检查规则
3. 增加单元测试覆盖Activity生命周期

### 影响范围

- **影响用户**：所有用户
- **修复风险**：低
- **回滚方案**：简单

### 总结

应用在启动时因MainActivity中访问了不存在的View ID（button_submit）导致NullPointerException崩溃。需要检查布局文件中是否正确定义了该Button，或在代码中添加null检查来修复。"""
