"""
重试机制模块
提供 API 调用重试、超时处理等稳定性功能
"""

import time
import functools
from typing import Callable, Any, Optional, Tuple, Type
from dataclasses import dataclass
from harness.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    initial_delay: float = 1.0  # 初始延迟（秒）
    max_delay: float = 60.0  # 最大延迟（秒）
    exponential_base: float = 2.0  # 指数退避基数
    jitter: bool = True  # 是否添加随机抖动
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)


class RetryExhaustedException(Exception):
    """重试次数耗尽异常"""
    def __init__(self, func_name: str, last_error: Exception):
        self.func_name = func_name
        self.last_error = last_error
        super().__init__(f"重试 {func_name} 失败 {last_error}")


def calculate_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """计算重试延迟时间（使用指数退避）"""
    delay = min(
        config.initial_delay * (config.exponential_base ** attempt),
        config.max_delay
    )

    if config.jitter:
        import random
        delay = delay * (0.5 + random.random())

    return delay


def retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数退避基数
        jitter: 是否添加随机抖动
        retryable_exceptions: 可重试的异常类型元组
        on_retry: 重试时的回调函数

    Example:
        @retry(max_retries=3, initial_delay=1.0)
        def api_call():
            return requests.get(url)
    """

    config = RetryConfig(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions
    )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_error = e

                    if attempt < max_retries - 1:
                        delay = calculate_delay(attempt, config)
                        logger.warning(
                            f"执行 {func.__name__} 失败 (尝试 {attempt + 1}/{max_retries}): {e}, "
                            f"{delay:.2f}秒后重试..."
                        )

                        if on_retry:
                            on_retry(attempt, e)

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"执行 {func.__name__} 失败，已达到最大重试次数 ({max_retries})"
                        )

            raise RetryExhaustedException(func.__name__, last_error)

        return wrapper

    return decorator


def retry_with_fallback(
    max_retries: int = 3,
    fallback: Optional[Any] = None,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    带降级方案的重试装饰器

    Args:
        max_retries: 最大重试次数
        fallback: 降级方案（函数或值）
        retryable_exceptions: 可重试的异常类型

    Example:
        @retry_with_fallback(max_retries=2, fallback="default_value")
        def api_call():
            return requests.get(url)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    if attempt < max_retries - 1:
                        delay = calculate_delay(
                            attempt,
                            RetryConfig(max_retries=max_retries)
                        )
                        logger.warning(
                            f"{func.__name__} 失败 (尝试 {attempt + 1}/{max_retries}): {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__} 失败，已达到最大重试次数，使用降级方案"
                        )

                        if callable(fallback):
                            return fallback(*args, **kwargs)
                        return fallback

            return fallback

        return wrapper

    return decorator


class RateLimiter:
    """速率限制器 - 防止 API 调用过于频繁"""

    def __init__(self, calls_per_second: float = 10.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0.0

    def wait(self):
        """等待以满足速率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_call_time

        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)

        self.last_call_time = time.time()


class CircuitBreaker:
    """熔断器 - 防止级联故障"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行函数，带熔断保护"""

        if self.state == "open":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                logger.info("熔断器进入半开状态")
                self.state = "half_open"
            else:
                raise Exception("熔断器已触发，拒绝请求")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """成功回调"""
        if self.state == "half_open":
            logger.info("熔断器关闭，服务已恢复")
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self):
        """失败回调"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            logger.warning(f"熔断器触发，已连续失败 {self.failure_count} 次")
            self.state = "open"

    def get_state(self) -> dict:
        """获取熔断器状态"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time
        }


class TimeoutManager:
    """超时管理器 - 跨平台兼容（Windows/Linux/macOS）"""

    @staticmethod
    def with_timeout(seconds: float, default: Any = None):
        """
        超时装饰器（使用 concurrent.futures 实现跨平台兼容）

        Args:
            seconds: 超时时间（秒）
            default: 超时时的默认值

        Example:
            @TimeoutManager.with_timeout(5.0, default="timeout")
            def slow_operation():
                return api_call()
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(func, *args, **kwargs)
                    try:
                        return future.result(timeout=seconds)
                    except concurrent.futures.TimeoutError:
                        logger.warning(f"{func.__name__} 执行超时 ({seconds}秒)")
                        return default

            return wrapper

        return decorator
