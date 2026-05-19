"""
LogTypeKnowledgeBase - 日志类型领域知识库

将 LLM 对 MTK/Android 日志类型的领域知识结构化，
用于指导文件筛选优先级、LLM 提示词增强、日志分析策略选择。

知识来源：LLM 对 MTKLogger 日志体系的深度理解
"""
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class LogTypeInfo:
    pattern: str
    compiled_pattern: re.Pattern = None
    category: str = ""
    description: str = ""
    applicable_bug_types: List[str] = field(default_factory=list)
    priority_base: int = 5

    def __post_init__(self):
        if self.compiled_pattern is None:
            self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE)


LOG_TYPE_REGISTRY: List[LogTypeInfo] = [
    LogTypeInfo(
        pattern=r"main_log",
        category="android_core",
        description="Android main logcat 缓冲区，应用程序和 Java/Native 服务输出",
        applicable_bug_types=["crash", "anr", "functional", "ui", "performance", "boot", "memory", "network"],
        priority_base=10,
    ),
    LogTypeInfo(
        pattern=r"events_log",
        category="android_core",
        description="Android events logcat 缓冲区，系统事件（Activity 状态、进程调度、电池变化）",
        applicable_bug_types=["anr", "boot", "performance", "power", "ui"],
        priority_base=9,
    ),
    LogTypeInfo(
        pattern=r"sys_log|system_log",
        category="android_core",
        description="系统信息快照，包含 dumpsys 输出的服务状态（内存、CPU、进程）",
        applicable_bug_types=["memory", "performance", "anr", "power", "crash"],
        priority_base=8,
    ),
    LogTypeInfo(
        pattern=r"kernel_log",
        category="android_core",
        description="内核日志（dmesg/kmsg），驱动报错、OOM、看门狗、panic、reboot 原因",
        applicable_bug_types=["crash", "reboot", "kernel", "memory", "boot", "hardware"],
        priority_base=9,
    ),
    LogTypeInfo(
        pattern=r"radio_log",
        category="android_core",
        description="Android radio logcat 缓冲区，通话、短信、数据网络、RIL 与 Modem 交互",
        applicable_bug_types=["network", "call", "sms", "signal", "sim", "modem"],
        priority_base=7,
    ),
    LogTypeInfo(
        pattern=r"crash_log",
        category="android_core",
        description="Native/Tombstone/ANR 专项日志，崩溃调用栈和寄存器信息",
        applicable_bug_types=["crash", "anr", "native_crash", "tombstone"],
        priority_base=10,
    ),
    LogTypeInfo(
        pattern=r"bugreport",
        category="android_core",
        description="Android bugreport 完整系统快照",
        applicable_bug_types=["crash", "anr", "performance", "memory", "boot", "power", "network", "functional"],
        priority_base=10,
    ),
    LogTypeInfo(
        pattern=r"logcat",
        category="android_core",
        description="Android logcat 日志缓冲区",
        applicable_bug_types=["crash", "anr", "functional", "ui", "performance"],
        priority_base=9,
    ),
    LogTypeInfo(
        pattern=r"bootprof",
        category="boot",
        description="启动性能分析，各阶段耗时（bootloader、kernel、init、zygote）",
        applicable_bug_types=["boot", "performance"],
        priority_base=8,
    ),
    LogTypeInfo(
        pattern=r"pl_lk|preloader",
        category="boot",
        description="Preloader/Little Kernel 日志，引导加载前阶段",
        applicable_bug_types=["boot", "hardware"],
        priority_base=6,
    ),
    LogTypeInfo(
        pattern=r"mblog_history",
        category="boot",
        description="Modem Boot Log 历史，Modem 侧启动/重启信息",
        applicable_bug_types=["reboot", "modem", "network"],
        priority_base=5,
    ),
    LogTypeInfo(
        pattern=r"adsp.*log",
        category="coprocessor",
        description="音频 DSP 日志，录音/播放/通话语音数字信号处理",
        applicable_bug_types=["audio", "call", "recording", "playback"],
        priority_base=7,
    ),
    LogTypeInfo(
        pattern=r"scp_log",
        category="coprocessor",
        description="系统控制处理器 (Sensor Hub) 日志，传感器管理与低功耗运动检测",
        applicable_bug_types=["sensor", "gyroscope", "accelerometer", "proximity", "display"],
        priority_base=6,
    ),
    LogTypeInfo(
        pattern=r"sspm_log",
        category="coprocessor",
        description="系统服务电源管理器日志，底层电源状态控制",
        applicable_bug_types=["power", "suspend", "resume", "battery"],
        priority_base=6,
    ),
    LogTypeInfo(
        pattern=r"mcupm_log",
        category="coprocessor",
        description="微控制器电源管理日志，深度睡眠唤醒异常",
        applicable_bug_types=["power", "suspend", "battery", "deep_sleep"],
        priority_base=5,
    ),
    LogTypeInfo(
        pattern=r"connsys.*log",
        category="connectivity",
        description="连接子系统日志（WiFi/BT/GNSS），连接状态与协议信息",
        applicable_bug_types=["wifi", "bluetooth", "gps", "location", "network"],
        priority_base=7,
    ),
    LogTypeInfo(
        pattern=r"apusys_log",
        category="coprocessor",
        description="APU (AI 处理单元) 系统日志",
        applicable_bug_types=["ai", "npu", "ml"],
        priority_base=4,
    ),
    LogTypeInfo(
        pattern=r"ccci_dpmaif|ccci",
        category="connectivity",
        description="跨核通信接口 (CCCI) 调试日志，AP 与 Modem 通信链路",
        applicable_bug_types=["modem", "network", "call", "signal", "ril"],
        priority_base=6,
    ),
    LogTypeInfo(
        pattern=r"atf_log",
        category="security",
        description="ARM 可信固件 (TrustZone) 日志，安全启动与 TEE",
        applicable_bug_types=["security", "drm", "payment", "tee"],
        priority_base=4,
    ),
    LogTypeInfo(
        pattern=r"gz_log",
        category="coprocessor",
        description="GZ (Genie Zone) 守护进程日志，省电/网络/RCS 管理",
        applicable_bug_types=["power", "network", "rcs"],
        priority_base=4,
    ),
    LogTypeInfo(
        pattern=r"tombstone",
        category="android_core",
        description="Native 进程崩溃的详细堆栈和寄存器信息",
        applicable_bug_types=["crash", "native_crash"],
        priority_base=10,
    ),
    LogTypeInfo(
        pattern=r"traces",
        category="android_core",
        description="ANR traces 文件，记录各线程堆栈",
        applicable_bug_types=["anr"],
        priority_base=10,
    ),
    LogTypeInfo(
        pattern=r"properties|build\.prop|\.sysprop",
        category="metadata",
        description="系统属性文件，固件版本与配置参数",
        applicable_bug_types=["boot", "version", "config"],
        priority_base=3,
    ),
    LogTypeInfo(
        pattern=r"dumpstate",
        category="android_core",
        description="系统状态 dump，包含所有服务状态快照",
        applicable_bug_types=["crash", "anr", "performance", "memory", "power"],
        priority_base=8,
    ),
    LogTypeInfo(
        pattern=r"hilog",
        category="android_core",
        description="HarmonyOS/OpenHarmony 分布式日志",
        applicable_bug_types=["crash", "anr", "functional"],
        priority_base=7,
    ),
    LogTypeInfo(
        pattern=r"watchdog",
        category="android_core",
        description="Watchdog 超时日志，系统服务死锁检测",
        applicable_bug_types=["anr", "watchdog", "system_hang"],
        priority_base=9,
    ),
]

BUG_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "crash": ["crash", "crashed", "崩溃", "闪退", "fatal", "exception", "died", "tombstone"],
    "anr": ["anr", "not responding", "无响应", "卡死", "frozen", "hang", "卡顿"],
    "boot": ["boot", "启动", "开机", "reboot", "重启", "卡logo", "slow boot"],
    "network": ["network", "网络", "wifi", "bluetooth", "蓝牙", "信号", "signal", "data", "数据", "断网"],
    "call": ["call", "通话", "电话", "dial", "ring", "来电", "去电", "断线"],
    "power": ["power", "功耗", "耗电", "battery", "电池", "suspend", "sleep", "休眠", "wakelock"],
    "audio": ["audio", "音频", "录音", "播放", "声音", "speaker", "mic", "耳机", "音量"],
    "sensor": ["sensor", "传感器", "陀螺仪", "accelerometer", "proximity", "接近光", "重力", "旋转"],
    "display": ["display", "屏幕", "亮度", "flicker", "闪烁", "黑屏", "白屏", "花屏"],
    "memory": ["memory", "内存", "oom", "low memory", "内存泄漏", "leak", "oom_adj"],
    "performance": ["performance", "性能", "慢", "slow", "lag", "卡", "耗时", "jank"],
    "camera": ["camera", "相机", "拍照", "录像", "preview", "flash", "闪光灯"],
    "gps": ["gps", "定位", "location", "gnss", "导航"],
    "modem": ["modem", "基带", "射频", "rf", "nvram"],
    "security": ["security", "安全", "drm", "tee", "加密", "decrypt", "lockscreen"],
    "reboot": ["reboot", "重启", "restart", "reset", "panic", "watchdog"],
    "ui": ["ui", "界面", "显示", "动画", "animation", "layout", "渲染"],
    "functional": ["functional", "功能", "异常", "失效", "不工作", "无法"],
}


class LogTypeKnowledgeBase:
    """日志类型领域知识库
    
    核心能力:
    1. 根据文件名识别日志类型和用途
    2. 根据 Bug 类型推荐相关日志文件
    3. 生成 Bug 类型感知的文件优先级
    4. 生成 LLM 提示词中的日志类型参考信息
    """
    
    def __init__(self):
        self._registry = LOG_TYPE_REGISTRY
        self._bug_keywords = BUG_TYPE_KEYWORDS
    
    def identify_log_type(self, filename: str) -> Optional[LogTypeInfo]:
        """根据文件名识别日志类型"""
        for info in self._registry:
            if info.compiled_pattern.search(filename):
                return info
        return None
    
    def get_bug_types_from_description(self, bug_description: str) -> List[str]:
        """从 Bug 描述中推断 Bug 类型"""
        bug_lower = bug_description.lower()
        matched_types = []
        
        for bug_type, keywords in self._bug_keywords.items():
            for keyword in keywords:
                if keyword in bug_lower:
                    matched_types.append(bug_type)
                    break
        
        if not matched_types:
            matched_types = ["crash", "anr", "functional"]
        
        return matched_types
    
    def get_priority_for_file(self, filename: str, bug_types: List[str] = None) -> int:
        """计算文件优先级分数（Bug 类型感知）
        
        Args:
            filename: 文件名
            bug_types: Bug 类型列表，为空时使用基础优先级
        
        Returns:
            优先级分数，越高越优先
        """
        info = self.identify_log_type(filename)
        if info is None:
            return 1
        
        score = info.priority_base
        
        if bug_types:
            for bug_type in bug_types:
                if bug_type in info.applicable_bug_types:
                    score += 5
        
        return score
    
    def get_recommended_files(
        self,
        available_files: List[str],
        bug_types: List[str],
        max_files: int = 10
    ) -> List[str]:
        """根据 Bug 类型推荐最相关的日志文件
        
        Args:
            available_files: 可用文件路径列表
            bug_types: Bug 类型列表
            max_files: 最大推荐数量
        
        Returns:
            按优先级排序的推荐文件列表
        """
        scored = []
        for file_path in available_files:
            filename = os.path.basename(file_path) if '/' in file_path else file_path
            score = self.get_priority_for_file(filename, bug_types)
            scored.append((file_path, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [f for f, s in scored[:max_files]]
    
    def generate_llm_context(self, bug_types: List[str] = None) -> str:
        """生成 LLM 提示词中的日志类型参考信息
        
        Args:
            bug_types: Bug 类型列表，为空时包含所有类型
        
        Returns:
            格式化的日志类型参考文本
        """
        lines = ["【MTK/Android 日志类型参考】", ""]
        
        categories = {}
        for info in self._registry:
            cat = info.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(info)
        
        category_names = {
            "android_core": "Android 系统核心日志",
            "boot": "启动与早期阶段日志",
            "coprocessor": "协处理器 (DSP/SCP) 日志",
            "connectivity": "连接子系统日志",
            "security": "安全与可信日志",
            "metadata": "元数据与配置",
        }
        
        for cat, infos in categories.items():
            cat_name = category_names.get(cat, cat)
            lines.append(f"## {cat_name}")
            
            for info in infos:
                relevance = ""
                if bug_types:
                    overlap = set(bug_types) & set(info.applicable_bug_types)
                    if overlap:
                        relevance = f" ⭐与当前Bug相关({', '.join(overlap)})"
                
                lines.append(f"- {info.pattern}: {info.description}{relevance}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_log_type_description(self, filename: str) -> str:
        """获取文件对应的日志类型描述"""
        info = self.identify_log_type(filename)
        if info:
            return f"[{info.category}] {info.description}"
        return "[未知类型]"


import os
