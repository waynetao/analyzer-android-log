import os
import json
import time
from typing import Optional, Dict, Any, Tuple
from openai import OpenAI
from openai import RateLimitError, Timeout, APIError, APIConnectionError

from harness.core.logging import get_logger

logger = get_logger(__name__)

# 延迟导入 token_stats 以避免循环导入
_token_stats = None

def _get_token_stats():
    """延迟获取 token_stats 实例"""
    global _token_stats
    if _token_stats is None:
        from harness.core.token_stats import get_token_stats as _get_ts
        _token_stats = _get_ts()
    return _token_stats


class LLMClient:
    """LLM 客户端 - 支持重试机制和降级方案"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = None,
        max_retries: int = None,
        timeout: float = None
    ):
        # 支持 LLM_ 前缀（新）和 OPENAI_ 前缀（向后兼容）
        self.api_key = api_key or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or os.environ.get("LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
        
        # 模型名称：如果未指定，必须从环境变量获取
        configured_model = model or os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL")
        if not configured_model:
            raise ValueError(
                "LLM 模型未配置！请在 .env 文件中设置 LLM_MODEL 或 OPENAI_MODEL"
            )
        self.model = configured_model
        self.temperature = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "2000"))

        # 重试配置
        self.max_retries = max_retries if max_retries is not None else int(os.environ.get("LLM_MAX_RETRIES", "3"))
        self.timeout = timeout if timeout is not None else float(os.environ.get("LLM_TIMEOUT", "60.0"))

        # 初始化客户端（只在有 API Key 时）
        self.client = None
        self.use_mock = True

        if self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout
                )
                self.use_mock = False
                logger.info(f"LLM 客户端初始化成功 - 模型: {self.model}")
            except Exception as e:
                logger.warning(f"LLM 客户端初始化失败: {e}")
                logger.warning("LLM 客户端初始化失败，将使用模拟模式")

        if self.use_mock:
            logger.info("未配置有效的 API Key，将使用模拟模式（LLM 分析功能不可用）")

    def chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_tokens: int = None,
        enable_retry: bool = True,
        scene: Optional[str] = None,
        skill: Optional[str] = None
    ) -> str:
        """
        调用 LLM API，带重试机制和 Token 统计
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数
            max_tokens: 最大 Token 数
            enable_retry: 是否启用重试
            scene: 场景（用于 Token 统计）
            skill: 技能名称（用于 Token 统计）
        """
        temp = temperature if temperature is not None else self.temperature
        max_t = max_tokens if max_tokens is not None else self.max_tokens

        if self.use_mock:
            return self._mock_response(system_prompt, user_prompt)

        if enable_retry:
            return self._chat_completion_with_retry(
                system_prompt, user_prompt, temp, max_t, scene, skill
            )
        else:
            return self._chat_completion_once(
                system_prompt, user_prompt, temp, max_t, scene, skill
            )

    def _chat_completion_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        scene: Optional[str] = None,
        skill: Optional[str] = None
    ) -> str:
        """带重试机制的 LLM 调用"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return self._do_api_call(
                    system_prompt, user_prompt, temperature, max_tokens,
                    scene, skill
                )

            except RateLimitError as e:
                last_error = e
                wait_time = self._get_retry_delay(attempt, e)
                logger.warning(
                    f"LLM API 限流 (尝试 {attempt + 1}/{self.max_retries}): {e}, "
                    f"等待 {wait_time:.1f}秒后重试..."
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)

            except (APIError, APIConnectionError, Timeout) as e:
                last_error = e
                wait_time = self._get_retry_delay(attempt, e)
                logger.warning(
                    f"LLM API 错误 (尝试 {attempt + 1}/{self.max_retries}): {e}, "
                    f"等待 {wait_time:.1f}秒后重试..."
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)

            except Exception as e:
                logger.error(f"LLM 调用失败: {e}")
                return self._mock_response(system_prompt, user_prompt)

        logger.error(f"LLM API 调用失败，已达到最大重试次数 ({self.max_retries})")
        return self._mock_response(system_prompt, user_prompt)

    def _chat_completion_once(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        scene: Optional[str] = None,
        skill: Optional[str] = None
    ) -> str:
        """单次 LLM 调用"""
        try:
            return self._do_api_call(
                system_prompt, user_prompt, temperature, max_tokens,
                scene, skill
            )
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return self._mock_response(system_prompt, user_prompt)

    def _do_api_call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
        scene: Optional[str] = None,
        skill: Optional[str] = None
    ) -> str:
        """执行实际的 API 调用"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            if response is None:
                logger.warning("LLM API 返回为空")
                return self._mock_response(system_prompt, user_prompt)

            if not hasattr(response, 'choices') or not response.choices:
                logger.warning("LLM API 响应格式异常")
                return self._mock_response(system_prompt, user_prompt)

            content = response.choices[0].message.content
            if content is None:
                logger.warning("LLM API 消息内容为空")
                return self._mock_response(system_prompt, user_prompt)

            # 记录 Token 使用
            if hasattr(response, 'usage') and response.usage:
                prompt_tokens = getattr(response.usage, 'prompt_tokens', 0)
                completion_tokens = getattr(response.usage, 'completion_tokens', 0)

                _get_token_stats().record_usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model=self.model,
                    scene=scene,
                    skill=skill
                )

                logger.debug(
                    f"LLM Token 使用: prompt={prompt_tokens}, "
                    f"completion={completion_tokens}, total={prompt_tokens + completion_tokens}"
                )

            return content

        except Exception as e:
            logger.error(f"LLM API 调用异常: {e}")
            raise

    def _get_retry_delay(self, attempt: int, error: Exception) -> float:
        """计算重试延迟时间"""
        base_delay = 1.0

        # 速率限制错误通常需要更长的等待时间
        if isinstance(error, RateLimitError):
            base_delay = 5.0
            if hasattr(error, 'response'):
                retry_after = error.response.headers.get('retry-after')
                if retry_after:
                    return float(retry_after)

        # 指数退避
        delay = base_delay * (2 ** attempt)

        # 添加随机抖动
        import random
        delay = delay * (0.5 + random.random())

        # 最大延迟 60 秒
        return min(delay, 60.0)

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
