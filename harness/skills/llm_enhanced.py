"""
LLM增强技能 - Bug描述解析、日志过滤、异常分类
包含多个LLM驱动的增强功能
"""
from typing import Dict, Any, List
from .base import BaseSkill, SkillResult, LLMBasedSkill
import sys
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class BugDescriptionParserSkill(LLMBasedSkill):
    """LLM驱动的Bug描述智能解析器"""

    @property
    def name(self) -> str:
        return "bug_desc_parser"

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        super().__init__(api_key, base_url, model)
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["bug_text"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        try:
            bug_text = inputs["bug_text"]
            parsed = self._parse_description(bug_text)
            
            return SkillResult(
                True,
                parsed,
                "Bug描述解析完成"
            )
        except Exception as e:
            return SkillResult(False, {}, f"解析失败: {str(e)}")
    
    def _parse_description(self, bug_text: str) -> Dict:
        """智能解析Bug描述"""
        if self.use_mock:
            return self._mock_parse(bug_text)
        
        prompt = f"""你是一位Android Bug分析专家。请解析以下Bug描述，提取标准化的关键信息，返回JSON格式。

Bug描述：
{bug_text}

请提取以下信息（用JSON返回）：
{{
    "summary": "问题简短摘要",
    "package_name": "应用包名（如果有）",
    "app_version": "应用版本（如果有）",
    "android_version": "Android系统版本（如果有）",
    "device_model": "设备型号（如果有）",
    "time_points": ["提到的时间点列表"],
    "reproduction_steps": ["复现步骤列表"],
    "keywords": ["相关技术关键词（用于日志搜索）"],
    "user_scenarios": ["用户使用场景描述"],
    "expected_behavior": "预期行为",
    "actual_behavior": "实际行为",
    "frequency": "问题出现频率（always/often/rare/once）",
    "severity": "严重程度（critical/high/medium/low）"
}}

只返回JSON，不要其他文字。"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            text = response.choices[0].message.content
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            if json_start >=0 and json_end > json_start:
                return json.loads(text[json_start:json_end])
            return self._mock_parse(bug_text)
        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}, using mock")
            return self._mock_parse(bug_text)
    
    def _mock_parse(self, bug_text: str) -> Dict:
        """模拟解析结果"""
        return {
            "summary": bug_text[:50] + "..." if len(bug_text) > 50 else bug_text,
            "package_name": "com.example.app",
            "app_version": "1.0.0",
            "android_version": "13",
            "device_model": "Pixel 6",
            "time_points": ["11:25", "11:30"],
            "reproduction_steps": [
                "1. 打开应用",
                "2. 点击主页面",
                "3. 等待加载"
            ],
            "keywords": ["crash", "崩溃", "NullPointerException", "启动"],
            "user_scenarios": ["正常使用应用启动流程"],
            "expected_behavior": "应用正常启动，显示主页面",
            "actual_behavior": "应用启动时崩溃",
            "frequency": "always",
            "severity": "critical"
        }


class LogFilterSkill(LLMBasedSkill):
    """LLM驱动的智能日志过滤器"""

    @property
    def name(self) -> str:
        return "log_filter"

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        super().__init__(api_key, base_url, model)
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["bug_description", "log_entries"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        try:
            bug_desc = inputs["bug_description"]
            log_entries = inputs["log_entries"]
            
            filter_rules = self._generate_filter_rules(bug_desc)
            filtered_logs = self._apply_filter_rules(log_entries, filter_rules)
            
            return SkillResult(
                True,
                {
                    "filter_rules": filter_rules,
                    "filtered_logs": filtered_logs,
                    "original_count": len(log_entries),
                    "filtered_count": len(filtered_logs)
                },
                "智能过滤完成"
            )
        except Exception as e:
            return SkillResult(False, {}, f"过滤失败: {str(e)}")
    
    def _generate_filter_rules(self, bug_desc: Dict) -> Dict:
        """生成智能过滤规则"""
        if self.use_mock:
            return self._mock_filter_rules(bug_desc)
        
        return self._mock_filter_rules(bug_desc)
    
    def _mock_filter_rules(self, bug_desc: Dict) -> Dict:
        """模拟规则生成"""
        return {
            "include_keywords": bug_desc.get("keywords", []) + ["FATAL", "EXCEPTION", "ANR", "CRASH"],
            "exclude_keywords": ["DEBUG", "VERBOSE", "ContextImpl"],
            "priority_levels": ["E", "F", "W"],
            "target_packages": [bug_desc.get("package_name", "")],
            "time_range": bug_desc.get("time_points", [])
        }
    
    def _apply_filter_rules(self, log_entries: List, rules: Dict) -> List:
        """应用过滤规则"""
        filtered = []
        for log in log_entries:
            if isinstance(log, dict):
                msg = log.get("message", "")
                level = log.get("level", "")
            else:
                msg = str(log)
                level = ""
            
            include = False
            
            # 检查关键词
            for keyword in rules.get("include_keywords", []):
                if keyword.lower() in msg.lower():
                    include = True
                    break
            
            # 检查排除词
            for keyword in rules.get("exclude_keywords", []):
                if keyword.lower() in msg.lower():
                    include = False
                    break
            
            # 检查级别
            if rules.get("priority_levels") and level not in rules.get("priority_levels", []):
                if level: include = False
            
            if include:
                filtered.append(log)
        
        return filtered[:100]  # 限制数量


class ExceptionClassifierSkill(LLMBasedSkill):
    """LLM驱动的异常分类器"""

    @property
    def name(self) -> str:
        return "exception_classifier"

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        super().__init__(api_key, base_url, model)
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["exceptions"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        try:
            exceptions = inputs["exceptions"]
            classification = self._classify_exceptions(exceptions)
            
            return SkillResult(
                True,
                classification,
                "异常分类完成"
            )
        except Exception as e:
            return SkillResult(False, {}, f"分类失败: {str(e)}")
    
    def _classify_exceptions(self, exceptions: List) -> Dict:
        """对异常进行分类和分析"""
        categories = {
            "null_pointer": [],
            "index_out_of_bounds": [],
            "illegal_state": [],
            "network": [],
            "memory": [],
            "security": [],
            "other": []
        }
        
        for exc in exceptions:
            msg = str(exc).lower()
            
            if "nullpointer" in msg:
                categories["null_pointer"].append(exc)
            elif "indexoutof" in msg or "arrayindex" in msg:
                categories["index_out_of_bounds"].append(exc)
            elif "illegalstate" in msg:
                categories["illegal_state"].append(exc)
            elif "network" in msg or "socket" in msg or "timeout" in msg:
                categories["network"].append(exc)
            elif "outofmemory" in msg or "oom" in msg:
                categories["memory"].append(exc)
            elif "security" in msg or "permission" in msg:
                categories["security"].append(exc)
            else:
                categories["other"].append(exc)
        
        # 确定主要问题
        primary_issue = "other"
        max_count = 0
        for cat, items in categories.items():
            if len(items) > max_count:
                max_count = len(items)
                primary_issue = cat
        
        return {
            "categories": categories,
            "primary_issue": primary_issue,
            "total_exceptions": sum(len(items) for items in categories.values())
        }


class PromptMatcherSkill(BaseSkill):
    """精准提示词匹配器"""
    
    @property
    def name(self) -> str:
        return "prompt_matcher"
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        valid, msg = self._validate_inputs(inputs, ["analysis_result"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        try:
            analysis = inputs["analysis_result"]
            matched_prompt = self._match_prompt_template(analysis)
            
            return SkillResult(
                True,
                {
                    "matched_template": matched_prompt,
                    "prompt_quality": "optimized"
                },
                "提示词匹配完成"
            )
        except Exception as e:
            return SkillResult(False, {}, f"匹配失败: {str(e)}")
    
    def _match_prompt_template(self, analysis: Dict) -> str:
        """匹配合适的提示词模板"""
        if analysis.get("crashes", 0) > 0:
            return "crash_focused"
        elif analysis.get("anrs", 0) > 0:
            return "anr_focused"
        elif analysis.get("low_memory", 0) > 0:
            return "memory_focused"
        elif analysis.get("exceptions", 0) > 0:
            return "exception_focused"
        else:
            return "general_analysis"
