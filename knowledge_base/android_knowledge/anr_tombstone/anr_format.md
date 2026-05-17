# ANR 日志格式说明

## 文档信息

| 字段 | 值 |
|------|-----|
| **版本** | v1.0 |
| **适用版本** | Android 8.0+ |
| **最后更新** | 2026-05-17 |
| **状态** | Draft |
| **标签** | android, anr, logcat, performance |

---

## 1. 概述

ANR（Application Not Responding）是 Android 系统检测到应用主线程阻塞超过一定时间时触发的机制。本文件详细说明 ANR 日志的格式和解析方法。

---

## 2. ANR 日志格式

### 2.1 日志位置

ANR 日志通常出现在以下位置：
- `/data/anr/traces.txt` - 完整的堆栈跟踪
- `/data/anr/anr_<timestamp>.txt` - ANR 报告文件
- logcat 输出 - 包含 ANR 摘要

### 2.2 标准格式结构

```text
ANR in <package_name> (<process_name>)
PID: <pid>
Reason: <reason>
Load: <load_average>

CPU usage from <start_time> to <end_time>:
  <process_name>: <usage>% = <user>% user + <system>% kernel / faults: <faults>
  ...

----- pid <pid> at <timestamp> -----
Cmd line: <command_line>
Build fingerprint: <fingerprint>

ABI: <abi>

"main" prio=<priority> tid=<tid> Native: <native_status>
  | group="main" sCount=<count> dsCount=<count> obj=<object> self=<self>
  | sysTid=<sys_tid> nice=<nice> cgrp=<cgroup> sched=<sched>
  | state=<state> schedstat=<schedstat>
  | utime=<utime> stime=<stime> timeout=<timeout>
  | stack=0x<stack_start>-0x<stack_end>
  | held mutexes=
  at <native_method> (Native method)
  at <java_method> (<File.java>:<line>)
  ...
```

### 2.3 关键字段定义

| 字段 | 类型 | 含义 | 示例 |
|------|------|------|------|
| package_name | string | 应用包名 | com.example.app |
| process_name | string | 进程名 | com.example.app |
| pid | int | 进程ID | 1234 |
| reason | string | ANR原因 | Input dispatching timed out |
| load_average | float | 系统负载 | 4.20 |
| timestamp | string | 时间戳 | 2026-03-04 10:23:28 |

### 2.4 常见 ANR 原因

| 原因 | 描述 | 排查方向 |
|------|------|----------|
| Input dispatching timed out | 输入事件分发超时 | 主线程阻塞 |
| Broadcast of Intent | BroadcastReceiver 执行超时 | 广播处理耗时 |
| ServiceStart | Service 启动超时 | 服务初始化耗时 |
| ContentProvider | ContentProvider 初始化超时 | Provider 耗时操作 |
| Activity launch | Activity 启动超时 | Activity onCreate 耗时 |

---

## 3. 解析方法

### 3.1 解析步骤

1. **识别 ANR 类型**：查看 `Reason` 字段
2. **定位阻塞线程**：查看堆栈跟踪中的 `main` 线程
3. **分析调用栈**：找出耗时操作的源头
4. **检查 CPU 使用**：查看 CPU 使用率是否过高
5. **检查锁状态**：查看 `held mutexes`

### 3.2 工具推荐

| 工具 | 用途 | 链接 |
|------|------|------|
| Android Studio Profiler | 性能分析 | 内置 |
| Traceview | 方法追踪 | Android SDK |
| Systrace | 系统级追踪 | Android SDK |

---

## 4. 常见模式

### 4.1 ANR 根因模式

| 模式 | 描述 | 根因 |
|------|------|------|
| 主线程网络请求 | 在 UI 线程执行网络操作 | 网络延迟 |
| 主线程数据库操作 | 在 UI 线程执行 DB 操作 | 查询耗时 |
| 死锁 | 线程间相互等待锁 | 锁顺序问题 |
| 大量计算 | 主线程执行复杂计算 | 算法效率 |
| 同步等待 | 主线程同步等待其他线程 | 线程阻塞 |

### 4.2 示例 ANR 日志

```text
ANR in com.example.app (com.example.app)
PID: 1234
Reason: Input dispatching timed out (Waiting to send non-key event because the touched window has not finished processing certain input events that were delivered to it over 500.0ms ago.)
Load: 3.50

----- pid 1234 at 2026-03-04 10:23:28 -----
"main" prio=5 tid=1 Native: 0
  ...
  at com.example.app.MainActivity.onCreate(MainActivity.java:42)
  at android.app.Activity.performCreate(Activity.java:7802)
  ...
```

---

## 5. 参考资料

- Android 官方文档: [ANR](https://developer.android.com/topic/performance/vitals/anr)
- AOSP 源码: frameworks/base/services/core/java/com/android/server/am/ActivityManagerService.java