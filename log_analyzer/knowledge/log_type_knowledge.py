"""
LogTypeKnowledgeBase - 日志类型领域知识库

设计理念：规则先行 + LLM 兜底
1. 确定性规则匹配已知命名模式（高置信、零成本）
2. 匹配失败或置信度低的文件，交给 LLM 识别（覆盖长尾）
3. LLM 识别结果可缓存回知识库，实现自学习

这样既保证了主流场景的性能和准确，又覆盖了长尾需求。
"""
import os
import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


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


@dataclass
class FileIdentification:
    filename: str
    file_path: str = ""
    log_type: Optional[LogTypeInfo] = None
    confidence: Confidence = Confidence.UNKNOWN
    category: str = ""
    description: str = ""
    applicable_bug_types: List[str] = field(default_factory=list)
    priority: int = 1
    identified_by: str = ""
    llm_identified: bool = False


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

LOG_EXTENSION_HEURISTICS = [
    (r"\.log$", "log_file", "日志文件（.log 扩展名）", Confidence.MEDIUM),
    (r"\.txt$", "text_file", "文本文件（.txt 扩展名）", Confidence.LOW),
    (r"^dmesg$", "kernel", "内核日志（dmesg）", Confidence.HIGH),
    (r"^kmsg", "kernel", "内核日志（kmsg）", Confidence.HIGH),
    (r"^last_kmsg", "kernel", "上次启动内核日志", Confidence.HIGH),
    (r"^console", "boot", "控制台日志", Confidence.MEDIUM),
    (r"^proc", "metadata", "进程信息", Confidence.LOW),
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
    """日志类型领域知识库 — 规则先行 + LLM 兜底

    两阶段识别流程:
    ┌──────────────────────────────────────────────────────┐
    │ 阶段1: 确定性规则匹配（零成本、高置信）                │
    │  - 已知命名模式（main_log, crash_log, adsp_log...）  │
    │  - 扩展名启发式（.log, .txt, dmesg, kmsg...）        │
    │  → 高置信: 直接使用，不走 LLM                        │
    │  → 中置信: 标记，可选走 LLM 验证                      │
    │  → 低/未知: 进入阶段2                                 │
    └──────────────────────────────────────────────────────┘
                        ↓ 未知/低置信文件
    ┌──────────────────────────────────────────────────────┐
    │ 阶段2: LLM 识别（覆盖长尾）                           │
    │  - 将未知文件清单发给 LLM                              │
    │  - LLM 返回文件类型、用途、适用 Bug 类型               │
    │  - 结果缓存到 _llm_cache，下次免调 LLM                │
    └──────────────────────────────────────────────────────┘
    """

    def __init__(self):
        self._registry = LOG_TYPE_REGISTRY
        self._bug_keywords = BUG_TYPE_KEYWORDS
        self._extension_heuristics = [
            (re.compile(p, re.IGNORECASE), cat, desc, conf)
            for p, cat, desc, conf in LOG_EXTENSION_HEURISTICS
        ]
        self._llm_cache: Dict[str, FileIdentification] = {}

    def identify_file(self, filename: str, file_path: str = "") -> FileIdentification:
        """识别单个文件的日志类型（规则优先）

        Returns:
            FileIdentification 包含置信度、类型、描述等
        """
        info = self._match_known_pattern(filename)
        if info:
            return FileIdentification(
                filename=filename,
                file_path=file_path,
                log_type=info,
                confidence=Confidence.HIGH,
                category=info.category,
                description=info.description,
                applicable_bug_types=info.applicable_bug_types,
                priority=info.priority_base,
                identified_by="rule:known_pattern",
            )

        ext_result = self._match_extension_heuristic(filename)
        if ext_result:
            cat, desc, conf = ext_result
            return FileIdentification(
                filename=filename,
                file_path=file_path,
                confidence=conf,
                category=cat,
                description=desc,
                priority=3 if conf == Confidence.MEDIUM else 2,
                identified_by="rule:extension_heuristic",
            )

        if filename in self._llm_cache:
            cached = self._llm_cache[filename]
            cached.file_path = file_path
            cached.identified_by = "llm:cached"
            return cached

        return FileIdentification(
            filename=filename,
            file_path=file_path,
            confidence=Confidence.UNKNOWN,
            identified_by="unknown",
        )

    def identify_files_batch(
        self,
        file_paths: List[str],
        extract_dir: str = ""
    ) -> Tuple[List[FileIdentification], List[FileIdentification]]:
        """批量识别文件，返回 (已识别, 需 LLM 识别)

        Args:
            file_paths: 文件路径列表
            extract_dir: 解压目录（用于生成相对路径）

        Returns:
            (identified, needs_llm) - 已识别的高/中置信文件 + 需 LLM 识别的未知文件
        """
        identified = []
        needs_llm = []

        for fp in file_paths:
            filename = os.path.basename(fp)
            result = self.identify_file(filename, fp)

            if result.confidence in (Confidence.HIGH, Confidence.MEDIUM):
                identified.append(result)
            else:
                needs_llm.append(result)

        return identified, needs_llm

    def apply_llm_results(self, llm_results: List[Dict]):
        """将 LLM 识别结果合并到知识库（缓存 + 自学习）

        Args:
            llm_results: LLM 返回的识别结果列表，每项包含:
                - filename: 文件名
                - category: 分类
                - description: 描述
                - applicable_bug_types: 适用的 Bug 类型列表
                - priority: 优先级
        """
        for item in llm_results:
            filename = item.get("filename", "")
            if not filename:
                continue

            ident = FileIdentification(
                filename=filename,
                category=item.get("category", "unknown"),
                description=item.get("description", ""),
                applicable_bug_types=item.get("applicable_bug_types", []),
                priority=item.get("priority", 3),
                confidence=Confidence.MEDIUM,
                identified_by="llm",
                llm_identified=True,
            )

            self._llm_cache[filename] = ident
            logger.debug(f"  LLM 识别缓存: {filename} → [{ident.category}] {ident.description}")

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
        """计算文件优先级分数（Bug 类型感知）"""
        ident = self.identify_file(filename)
        score = ident.priority

        if bug_types and ident.applicable_bug_types:
            for bug_type in bug_types:
                if bug_type in ident.applicable_bug_types:
                    score += 5

        return score

    def get_recommended_files(
        self,
        available_files: List[str],
        bug_types: List[str],
        max_files: int = 10
    ) -> List[str]:
        """根据 Bug 类型推荐最相关的日志文件"""
        scored = []
        for file_path in available_files:
            filename = os.path.basename(file_path) if '/' in file_path else file_path
            score = self.get_priority_for_file(filename, bug_types)
            scored.append((file_path, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [f for f, s in scored[:max_files]]

    def generate_llm_context(self, bug_types: List[str] = None) -> str:
        """生成 LLM 提示词中的日志类型参考信息"""
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
            "unknown": "未知类型",
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

    def generate_llm_identification_prompt(
        self,
        unknown_files: List[FileIdentification],
        bug_types: List[str],
        knowledge_context: str = ""
    ) -> Tuple[str, str]:
        """为未知文件生成 LLM 识别提示词

        Args:
            unknown_files: 需要识别的文件列表
            bug_types: Bug 类型
            knowledge_context: 已有的日志类型参考上下文

        Returns:
            (system_prompt, user_prompt)
        """
        file_list = []
        for f in unknown_files:
            size_str = ""
            if f.file_path and os.path.isfile(f.file_path):
                try:
                    size = os.path.getsize(f.file_path)
                    if size > 1024 * 1024:
                        size_str = f" ({size / (1024*1024):.1f}MB)"
                    elif size > 1024:
                        size_str = f" ({size / 1024:.1f}KB)"
                except OSError:
                    pass
            file_list.append(f"  - {f.filename}{size_str}")

        file_list_str = "\n".join(file_list)

        system_prompt = f"""你是一个 Android/MTK 平台的日志分析专家。
你的任务是识别未知日志文件的类型和用途。

{knowledge_context}

请对每个文件返回 JSON 格式的识别结果：
{{
  "results": [
    {{
      "filename": "文件名",
      "category": "分类（android_core/boot/coprocessor/connectivity/security/metadata/unknown）",
      "description": "该日志的用途描述",
      "applicable_bug_types": ["适用的Bug类型列表"],
      "priority": 1-10的优先级,
      "is_relevant": true/false（是否与当前Bug相关）
    }}
  ]
}}"""

        user_prompt = f"""Bug 描述涉及类型: {', '.join(bug_types)}

以下文件无法通过已知规则识别，请判断它们的类型和用途：

{file_list_str}

请识别每个文件的日志类型，判断是否与当前 Bug 相关。"""

        return system_prompt, user_prompt

    def parse_llm_identification_response(self, response: str) -> List[Dict]:
        """解析 LLM 识别结果"""
        try:
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())
            results = data.get("results", [])

            for item in results:
                if "applicable_bug_types" not in item:
                    item["applicable_bug_types"] = []
                if "priority" not in item:
                    item["priority"] = 3
                if "is_relevant" not in item:
                    item["is_relevant"] = True

            return results

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"解析 LLM 识别结果失败: {e}")
            return []

    def get_log_type_description(self, filename: str) -> str:
        """获取文件对应的日志类型描述"""
        ident = self.identify_file(filename)
        if ident.confidence != Confidence.UNKNOWN:
            return f"[{ident.category}] {ident.description}"
        return "[未知类型]"

    def get_identification_summary(self, files: List[str], bug_types: List[str] = None) -> Dict:
        """获取文件识别摘要统计"""
        high = medium = low = unknown = 0
        categories = {}

        for fp in files:
            filename = os.path.basename(fp)
            ident = self.identify_file(filename, fp)

            if ident.confidence == Confidence.HIGH:
                high += 1
            elif ident.confidence == Confidence.MEDIUM:
                medium += 1
            elif ident.confidence == Confidence.LOW:
                low += 1
            else:
                unknown += 1

            cat = ident.category or "unknown"
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total": len(files),
            "high_confidence": high,
            "medium_confidence": medium,
            "low_confidence": low,
            "unknown_needs_llm": unknown,
            "categories": categories,
        }

    def _match_known_pattern(self, filename: str) -> Optional[LogTypeInfo]:
        """匹配已知命名模式"""
        for info in self._registry:
            if info.compiled_pattern.search(filename):
                return info
        return None

    def _match_extension_heuristic(self, filename: str) -> Optional[Tuple[str, str, Confidence]]:
        """匹配扩展名启发式规则"""
        for pattern, cat, desc, conf in self._extension_heuristics:
            if pattern.search(filename):
                return cat, desc, conf
        return None
