import os
import json
import logging
from typing import Optional, Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = None
    ):
        # 支持 LLM_ 前缀（新）和 OPENAI_ 前缀（向后兼容）
        self.api_key = api_key or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
        self.model = model or os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "2000"))

        # 初始化客户端（只在有 API Key 时）
        self.client = None
        self.use_mock = True

        if self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                self.use_mock = False
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")
                print("警告：LLM 客户端初始化失败，将使用模拟模式")

        if self.use_mock:
            print("提示：未配置有效的 API Key，将使用模拟模式（LLM 分析功能不可用）")

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        # 使用实例默认值，或者传入的参数
        temp = temperature if temperature is not None else self.temperature
        max_t = max_tokens if max_tokens is not None else self.max_tokens
        
        if self.use_mock:
            return self._mock_response(system_prompt, user_prompt)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temp,
                max_tokens=max_t
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return self._mock_response(system_prompt, user_prompt)

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        """模拟响应，用于开发测试"""
        if "parse" in system_prompt.lower() and "bug" in user_prompt.lower():
            return json.dumps({
                "summary": "应用启动时崩溃",
                "package_name": "com.example.app",
                "app_version": "1.0.0",
                "android_version": "13",
                "device_model": "Pixel 6",
                "time_points": ["11:25", "11:27"],
                "reproduction_steps": [
                    "打开应用",
                    "点击主界面按钮",
                    "应用崩溃"
                ],
                "keywords": ["崩溃", "crash", "启动", "NullPointerException"],
                "user_scenarios": ["正常使用应用启动流程"],
                "expected_behavior": "应用正常启动并显示主界面",
                "actual_behavior": "应用启动时立即崩溃",
                "frequency": "每次启动必现"
            })
        elif "report" in system_prompt.lower():
            return """# Android Bug 分析报告

## 问题概述
应用在启动过程中出现崩溃问题。

## 关键信息
- 包名: com.example.app
- 问题时间: 11:25-11:27

## 根因分析
根据日志分析，发现了 NullPointerException 异常，这是导致崩溃的主要原因。

## 建议修复
1. 检查MainActivity.java第36行的空指针问题
2. 添加必要的空值检查
3. 完善错误处理逻辑"""
        
        return "模拟响应"
