# 日志提取精准度 - MTK Log 处理策略

## 📋 文档信息

| 项目 | 说明 |
|------|------|
| 版本 | v1.0 |
| 更新日期 | 2026-05-17 |
| 相关文档 | [TOKEN_COST_ANALYSIS.md](file:///workspace/TOKEN_COST_ANALYSIS.md) |

---

## 🎯 问题分析

### MTK Log 特点

| 特性 | 说明 | 挑战 |
|------|------|------|
| **文件大** | 100MB - 3GB+ | 完整读取耗时巨大 |
| **日志多** | 100万 - 1500万行 | 99% 内容与当前 Bug 无关 |
| **格式杂** | logcat + kernel + modem + event | 需要统一处理 |
| **时间长** | 覆盖数小时到数天 | 需要精准定位时间窗口 |

### 核心目标

```
目标: 从 100-1500万 行原始日志中
      提取出 500-5000行 与 Bug 直接相关的内容
      压缩比: 99.5% - 99.95%
```

---

## 🏗️ 整体处理流程

### 阶段 0: 预处理 (无 LLM)

```
原始 MTK Log
    ↓
[ 解压和扫描 ] 识别文件结构、定位关键文件
    ↓
[ 初始过滤 ] 进程筛选 + 时间范围裁剪 + 级别过滤
    ↓
初步候选日志 (5-10万行, 压缩比 90-95%)
```

### 阶段 1: 智能提取 (有 LLM/规则)

```
初步候选日志
    ↓
[ 关键事件识别 ] Bug发生前后的关键时间点
    ↓
[ 上下文扩展 ] 关键事件前后 N 行
    ↓
[ 特征匹配 ] 用户 Bug 描述关键词匹配
    ↓
筛选日志 (5000-50000行, 压缩比 99-99.5%)
```

### 阶段 2: 精准聚焦 (有 LLM)

```
筛选日志
    ↓
[ 证据匹配 ] 用户描述与日志匹配度评分
    ↓
[ 异常提取 ] Crash/ANR/Exception 提取
    ↓
[ 状态变化 ] 设备状态变更日志
    ↓
最终相关日志 (500-5000行, 压缩比 99.5-99.95%)
```

---

## 📝 最终提取的日志内容

### 1. Bug 核心发生日志

#### 1.1 Crash 相关

```
✅ Android Runtime Fatal Exception
  - FATAL EXCEPTION: main/...
  - Process: com.example.app
  - java.lang.NullPointerException/...
  - Stack trace (完整堆栈)

✅ Native Crash (tombstone)
  - signal 11 (SIGSEGV)
  - backtrace
  - register dump
  - memory map
  - fault addr
```

#### 1.2 ANR 相关

```
✅ ANR 触发点
  - am_anr: [time,pid,package,reason]
  - Reason: Input dispatching timed out
  - Reason: executing service ...

✅ ANR 发生前的主线程状态
  - main thread state
  - pending messages
  - binder transactions
  - last known activity
```

### 2. 用户描述匹配的事件

```
✅ 用户提到的关键字匹配
  - 按 Bug 描述中的关键词
  - 例如: "启动 crash" → 搜索 launch + crash
  - 例如: "滑动卡顿" → 搜索 Choreographer + draw

✅ 用户描述的场景
  - WiFi 断连 → 搜索 wpa_supplicant + disconnect
  - 蓝牙无法连接 → 搜索 Bluetooth + connect
  - 相机打不开 → 搜索 CameraService + open
```

### 3. 设备状态日志

```
✅ 系统服务日志
  - ActivityManager: am_on_resume_called
  - WindowManager: Displayed
  - PackageManager: install/uninstall
  - PowerManager: PARTIAL_WAKE_LOCK

✅ 资源使用
  - meminfo (dumpsys 中的关键部分)
  - procstats (内存状态)
  - battery info
  - thermal throttling

✅ 网络状态
  - ConnectivityManager: CONNECTIVITY_CHANGE
  - NetworkStats: data usage
  - WiFi scan results
```

### 4. 时间轴关键日志

```
✅ Bug 发生前 (T-5min 到 T)
  - App start/stop
  - Service bind/unbind
  - Broadcast received
  - Async task started

✅ Bug 发生时刻 (T)
  - 核心崩溃/ANR/异常
  - 相关进程状态

✅ Bug 发生后 (T 到 T+1min)
  - App restart
  - System recovery
  - Error reporting
```

### 5. 关键异常模式

```
✅ Java 异常
  - Exception in thread
  - Caused by:
  - Suppressed exceptions

✅ 系统错误
  - E/AndroidRuntime
  - E/SystemServer
  - E/StrictMode
  - E/Parcel
  - E/DatabaseUtils

✅ Kernel 异常
  - <3>[  123.456]
  - oom_killer
  - BUG:
  - WARNING:
```

### 6. aloggrep 增强提取

```
✅ aloggrep summary 输出
  - top errors
  - top warnings
  - crash count
  - ANR count

✅ aloggrep crash 输出
  - structured crash JSON
  - process info
  - timestamp
  - error type

✅ aloggrep histogram (异常检测)
  - log volume spikes
  - error rate peaks
  - unexpected pattern changes
```

---

## 🔍 日志提取策略详解

### 策略 1: 时间窗口裁剪

```python
# 从用户描述中提取
bug_time = "2026-05-17 14:32:15"  # 如果用户说了
  ↓
# 时间窗口设置
before = 5 * 60    # Bug 前 5 分钟
after = 1 * 60     # Bug 后 1 分钟
  ↓
# 提取范围
[bug_time - before, bug_time + after]
```

**压缩效果**: 从数小时/天的日志 → 6分钟的日志

---

### 策略 2: 进程筛选

```python
# 相关进程
target_packages = [
  "com.example.app",           # 用户问题 App
  "system_server",             # 系统服务
  "surfaceflinger",            # 渲染
  "mediaserver",               # 多媒体
]

# 提取策略
只保留 PID/UID 属于上述进程的日志
```

**压缩效果**: 从所有进程 → 只看问题相关进程

---

### 策略 3: 级别过滤

```python
# 按重要性分层提取
level_categories = {
  "critical": ["F", "E"],          # 致命/错误 (必须看)
  "warning":  ["W"],               # 警告 (辅助看)
  "info":     ["I", "D", "V"],     # 信息/调试 (很少看)
}

# 最终只保留:
critical + warning
  + 关键 info (与问题直接相关)
```

**压缩效果**: 从所有级别 → ~20% 的重要日志

---

### 策略 4: 事件标签聚焦 (QMD 知识库)

```python
# Event Tag 优先级分类
high_priority_tags = [
  "am_anr",          # ANR 发生
  "am_crash",        # App 崩溃
  "am_low_memory",   # 内存紧张
  "am_proc_died",    # 进程死亡
  "am_proc_start",   # 进程启动
  "wm_draw",         # 窗口绘制
  "am_on_paused",    # 页面暂停
  "am_on_resumed",   # 页面恢复
  # ... (完整定义在 QMD 知识库)
]

# 提取
只保留高优先级 Event Log Tags
```

**压缩效果**: 从所有 Events → ~10% 的关键 Events

---

### 策略 5: 堆栈和上下文

```python
# 发现一个异常
发现: FATAL EXCEPTION
  ↓
# 扩展提取
前 50 行: 异常触发前的相关操作
后 100 行: 异常后果和系统反应
堆栈跟踪: 完整保留 (这是根因关键)
```

**提取比**: 异常点 → 带上下文的完整信息

---

## 📊 各阶段压缩效果示例

### 示例: 一个中型 MTK Log 处理过程

| 阶段 | 日志行数 | 压缩比 | 说明 |
|------|---------|--------|------|
| **原始 MTK Log** | 5,000,000 行 | 0% | 完整日志 |
| **时间窗口** | 300,000 行 | 94% | T-5min 到 T+1min |
| **进程筛选** | 80,000 行 | 98.4% | 只保留目标进程 |
| **级别过滤** | 20,000 行 | 99.6% | 只留 F/E/W + 相关 I |
| **关键词匹配** | 5,000 行 | 99.9% | 与用户描述相关 |
| **证据匹配** | 1,500 行 | 99.97% | 最相关的内容 |
| **最终报告** | ~300-500行 | 99.99% | 总结分析后的关键 |

---

## 🎯 最终交付给 LLM 的内容

### 内容结构

```
┌─────────────────────────────────────────────────┐
│  1. 用户 Bug 描述                               │
│     - 问题描述                                  │
│     - 复现步骤                                  │
│     - 设备信息                                  │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│  2. 提取的关键日志 (1000-2000行)               │
│     ├─ Bug 发生核心日志                        │
│     │  ├─ Crash/ANR (100-300行)              │
│     │  └─ Stack trace (完整)                  │
│     │                                          │
│     ├─ 时间线日志 (500-800行)                  │
│     │  ├─ T-5min: App start/setup             │
│     │  ├─ T: 发生问题                          │
│     │  └─ T+1min: 后果                          │
│     │                                          │
│     ├─ 设备状态 (200-400行)                    │
│     │  ├─ 内存使用                             │
│     │  ├─ 系统服务                             │
│     │  └─ 关键事件                             │
│     │                                          │
│     └─ aloggrep 分析输出                       │
│        ├─ summary                              │
│        ├─ crash report                         │
│        └─ histogram (异常检测)                 │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│  3. 知识背景 (来自 QMD)                         │
│     - Event Log Tags 说明                      │
│     - ANR 类型说明                              │
│     - dumpsys 解读指南                          │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│  4. 分析指令                                    │
│     - 分析目标                                  │
│     - 输出格式                                  │
└─────────────────────────────────────────────────┘
```

---

## 🛡️ 保证精准度的机制

### 机制 1: 多层验证

```
提取 → 验证 1: 是否包含核心问题 → 验证 2: 时间是否匹配 → 验证 3: 是否有关键堆栈
  ↓
如失败: 放宽过滤条件，重新提取
```

### 机制 2: 证据匹配评分

```
每条日志 → 与用户 Bug 描述匹配 → 0-100 分
  ↓
只保留 > 50 分的内容
```

### 机制 3: Feature Flag 控制

```yaml
evidence_matching_enabled: true  # 启用证据匹配
knowledge_base_enabled: true     # 启用知识库
analysis_mode: deep              # 深度模式，确保不遗漏
```

### 机制 4: 人工审核的可能性

```
LLM 分析结果
  ↓
同时显示提取的关键日志
  ↓
用户可以检查日志是否完整
  ↓
如果不足，可以调整参数重新分析
```

---

## 📚 相关文档

| 文档 | 路径 |
|------|------|
| Token 消耗分析 | [TOKEN_COST_ANALYSIS.md](file:///workspace/TOKEN_COST_ANALYSIS.md) |
| QMD 知识库集成 | [QMD_INTEGRATION_SCHEME.md](file:///workspace/QMD_INTEGRATION_SCHEME.md) |
| Feature Flag 文档 | [README.md](file:///workspace/README.md) |
