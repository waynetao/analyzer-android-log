"""
LLMAnalysisSkill - LLM 驱动的高质量分析技能
使用关键日志证据进行精准定位和修复建议
支持 Bug 类型差异化提示词和模板
"""
from typing import Dict, Any, Optional
from .base import BaseSkill, SkillResult, LLMBasedSkill
from harness.skills.bug_type import PromptTemplateManager
import sys
import os
import json
from datetime import datetime

class LLMAnalysisSkill(LLMBasedSkill):
    """LLM 高级分析技能 - 高质量、有证据支撑
    支持 Bug 类型差异化提示词和模板优化
    """
    
    @property
    def name(self) -> str:
        return "llm_analysis"
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None, enable_bug_type_optimization: bool = True):
        super().__init__(api_key, base_url, model)
        self.enable_bug_type_optimization = enable_bug_type_optimization
        
        if not self.use_mock:
            print(f"✅ LLM 客户端已初始化 (模型: {self.model})")
            if self.enable_bug_type_optimization:
                print(f"✅ Bug 类型差异化优化已启用")
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["bug_description", "advanced_log_analysis"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        try:
            bug_desc = inputs["bug_description"]
            log_analysis = inputs["advanced_log_analysis"]["data"]
            
            # 检查是否使用 Bug 类型差异化优化
            use_bug_type_optimization = self.enable_bug_type_optimization and inputs.get("bug_type_analysis", {}).get("data", {}).get("enabled", False)
            
            if use_bug_type_optimization:
                print(f"🎯 使用 Bug 类型差异化分析")
                prompt, system_prompt = self._build_optimized_prompt(bug_desc, log_analysis, inputs.get("bug_type_analysis", {}).get("data", {}))
            else:
                print(f"📝 使用标准分析模式")
                prompt = self._build_prompt(bug_desc, log_analysis)
                system_prompt = "你是一位资深的Android技术支持专家，擅长日志分析和问题定位。"
            
            # 获取分析结果
            analysis = self._call_llm(prompt, system_prompt)
            
            result = {
                "analysis": analysis,
                "has_llm": not self.use_mock,
                "model": self.model if not self.use_mock else "mock",
                "bug_type_optimization": use_bug_type_optimization
            }
            
            return SkillResult(
                True,
                result,
                "LLM 分析完成"
            )
            
        except Exception as e:
            return SkillResult(
                False,
                {},
                f"LLM 分析失败: {str(e)}"
            )
    
    def _build_prompt(self, bug_desc: Dict, log_analysis: Dict) -> str:
        """构建详细的分析提示词"""
        
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
        
        # 格式化设备状态
        device_state_str = f"""
【设备状态】
- 电池事件: {len(log_analysis.get('device_state', {}).get('battery_levels', []))} 条
- 内存事件: {len(log_analysis.get('device_state', {}).get('memory_states', []))} 条
- 热事件: {len(log_analysis.get('device_state', {}).get('thermal_events', []))} 条
"""
        
        # 构建完整提示词
        prompt = f"""你是一位资深的Android技术支持专家，擅长日志分析和问题定位。

请基于以下信息，提供精准、高质量的分析报告，所有结论必须有日志证据支撑。

【用户问题描述】
{bug_desc.get('raw_text', '未知')}

【日志分析摘要】
- 崩溃数: {log_analysis.get('crashes', 0)}
- ANR数: {log_analysis.get('anrs', 0)}
- 低内存: {log_analysis.get('low_memory', 0)}
- 异常数: {log_analysis.get('exceptions', 0)}

{critical_logs_str}

{device_state_str}

【任务要求】
请提供以下内容：

1. 问题定位（需要引用具体日志证据）
2. 根因分析（基于日志推断）
3. 修复建议（具体、可操作）
4. 预防措施

请使用中文回答，保持专业和准确。
"""
        return prompt
    
    def _build_optimized_prompt(self, bug_desc: Dict, log_analysis: Dict, bug_type_data: Dict) -> tuple:
        """构建基于 Bug 类型的优化提示词"""
        
        bug_type = bug_type_data.get("bug_type", "unknown")
        analyzer = PromptTemplateManager.get_analyzer(bug_type)
        
        if analyzer:
            print(f"🔍 使用 {analyzer.name} 分析器")
            system_prompt = analyzer.get_system_prompt()
            user_prompt = analyzer.get_user_prompt(bug_desc, log_analysis)
            return user_prompt, system_prompt
        else:
            print(f"⚠️ 未找到对应分析器，使用标准模式")
            return self._build_prompt(bug_desc, log_analysis), "你是一位资深的Android技术支持专家，擅长日志分析和问题定位。"
    
    def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """调用LLM（或模拟）"""
        if self.use_mock:
            return self._get_mock_analysis()
        
        try:
            if system_prompt is None:
                system_prompt = "你是一位资深的Android技术支持专家，擅长日志分析和问题定位。"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return self._get_mock_analysis()
    
    def _get_mock_analysis(self) -> str:
        """模拟高质量分析结果"""
        return """# 高质量分析报告

## 1. 问题定位（有日志证据）

根据日志分析，问题主要发生在应用启动阶段。

【证据】
- 时间: 03-29 11:25:32.894
- 日志: "am_crash: [9337,0,com.example.app,954744388,java.lang.NullPointerException,Attempt to invoke virtual method 'void android.view.View.setVisibility(int)' on a null object reference,MainActivity.java,36]"

## 2. 根因分析

问题出在 MainActivity.java 的第 36 行，发生了 NullPointerException。
具体是在调用某个 View 的 setVisibility 方法时，该 View 对象为 null。

可能的原因：
1. View 初始化顺序问题
2. XML 布局文件中 View ID 不匹配
3. View 在调用前被提前释放

## 3. 修复建议（具体可操作）

1. 检查 MainActivity.java 第 36 行
   - 添加空值检查
   ```java
   if (myView != null) {
       myView.setVisibility(View.VISIBLE);
   }
   ```

2. 确认 XML 布局文件中正确定义了对应 ID 的 View

3. 检查 View 的初始化时机，确保在调用前已完成初始化

## 4. 预防措施

1. 在代码中增加空值检查
2. 使用静态代码分析工具（如 Lint）
3. 增加单元测试覆盖关键路径
"""
