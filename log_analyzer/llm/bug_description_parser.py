import json
import re
from typing import Optional
from log_analyzer.models import BugDescription
from log_analyzer.llm.llm_client import LLMClient


class BugDescriptionParser:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def parse(self, bug_text: str) -> BugDescription:
        # 优先使用简单规则解析，不依赖LLM
        result = self._parse_with_rules(bug_text)
        
        # 如果规则解析失败，再尝试LLM
        if not result.summary and self.llm_client and not self.llm_client.use_mock:
            try:
                result = self._parse_with_llm(bug_text)
            except:
                pass
                
        return result

    def _parse_with_rules(self, bug_text: str) -> BugDescription:
        """使用规则解析bug描述"""
        desc = BugDescription(raw_text=bug_text)
        
        # 提取包名
        package_match = re.search(r'包名[：:]\s*([a-zA-Z0-9_.]+)', bug_text)
        if package_match:
            desc.package_name = package_match.group(1)
        else:
            # 尝试匹配常见包名格式
            package_match2 = re.search(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9_.]+)', bug_text)
            if package_match2:
                desc.package_name = package_match2.group(1)
        
        # 提取版本号
        version_match = re.search(r'版本[：:]\s*([\d.]+)', bug_text)
        if version_match:
            desc.app_version = version_match.group(1)
        
        # 提取Android版本
        android_match = re.search(r'Android\s*版本[：:]\s*([\d]+)', bug_text)
        if android_match:
            desc.android_version = android_match.group(1)
        
        # 提取设备型号
        device_match = re.search(r'设备[：:]\s*([^\n]+)', bug_text)
        if device_match:
            desc.device_model = device_match.group(1).strip()
        
        # 提取时间点
        time_matches = re.findall(r'(\d{1,2}:\d{2})', bug_text)
        desc.time_points = time_matches
        
        # 提取关键词
        keywords = []
        keyword_candidates = [
            '崩溃', 'crash', 'CRASH',
            'ANR', 'anr', '无响应', 'not responding',
            '启动', 'start', 'launch',
            '闪退',
            'NullPointerException', 'NPE',
            'Exception', 'exception',
            'Error', 'error',
            'FATAL', 'fatal',
            'low memory', 'LowMemory', 'OOM', 'oom',
            'AndroidRuntime'
        ]
        for kw in keyword_candidates:
            if kw.lower() in bug_text.lower() and kw not in keywords:
                keywords.append(kw)
        desc.keywords = keywords
        
        # 简单摘要（取前50字符）
        lines = bug_text.strip().split('\n')
        if lines:
            desc.summary = lines[0][:100]
        
        # 尝试提取预期/实际行为
        expected_match = re.search(r'预期[：:]\s*([^\n]+)', bug_text)
        if expected_match:
            desc.expected_behavior = expected_match.group(1).strip()
            
        actual_match = re.search(r'实际[：:]\s*([^\n]+)', bug_text)
        if actual_match:
            desc.actual_behavior = actual_match.group(1).strip()
        
        # 设置默认值
        if not desc.summary:
            desc.summary = "Android应用问题"
        if not desc.keywords:
            desc.keywords = ["Android", "bug"]
            
        return desc

    def _parse_with_llm(self, bug_text: str) -> BugDescription:
        """使用LLM解析bug描述"""
        system_prompt = """你是一个专业的Android bug分析专家。请解析用户提供的bug描述，提取关键信息并以JSON格式返回。

返回格式必须包含以下字段：
{
    "summary": "bug的简短摘要",
    "package_name": "应用包名（如果有）",
    "app_version": "应用版本（如果有）",
    "android_version": "Android系统版本（如果有）",
    "device_model": "设备型号（如果有）",
    "time_points": ["提到的时间点列表"],
    "reproduction_steps": ["复现步骤列表"],
    "keywords": ["相关关键词列表（用于日志搜索）"],
    "user_scenarios": ["用户使用场景描述"],
    "expected_behavior": "预期行为",
    "actual_behavior": "实际行为",
    "frequency": "问题出现频率（如：总是、偶尔、仅一次等）"
}

注意：
1. 如果某个信息不存在，对应字段可以为空字符串或空数组
2. 关键词应该包含中文和英文的相关词汇
3. 时间点要提取所有提到的具体时间
4. 只返回JSON，不要有其他文字"""

        user_prompt = f"请解析以下bug描述：\n\n{bug_text}"

        response = self.llm_client.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=1500
        )

        return self._parse_response(bug_text, response)

    def _parse_response(self, raw_text: str, llm_response: str) -> BugDescription:
        try:
            # 尝试提取JSON
            json_str = self._extract_json(llm_response)
            data = json.loads(json_str)
            
            return BugDescription(
                raw_text=raw_text,
                summary=data.get("summary", ""),
                package_name=data.get("package_name"),
                app_version=data.get("app_version"),
                android_version=data.get("android_version"),
                device_model=data.get("device_model"),
                time_points=data.get("time_points", []),
                reproduction_steps=data.get("reproduction_steps", []),
                keywords=data.get("keywords", []),
                user_scenarios=data.get("user_scenarios", []),
                expected_behavior=data.get("expected_behavior"),
                actual_behavior=data.get("actual_behavior"),
                frequency=data.get("frequency")
            )
        except Exception as e:
            print(f"解析LLM响应失败: {e}")
            # 返回基础对象
            return BugDescription(raw_text=raw_text)

    def _extract_json(self, text: str) -> str:
        """从文本中提取JSON字符串"""
        # 查找第一个 { 和最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return text[start:end+1]
        return text
