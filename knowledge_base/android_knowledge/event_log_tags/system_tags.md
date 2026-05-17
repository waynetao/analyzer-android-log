# 系统 Event Log Tags 定义

## 文档信息

| 字段 | 值 |
|------|-----|
| **版本** | v1.0 |
| **适用版本** | Android 8.0+ |
| **最后更新** | 2026-05-17 |
| **状态** | Draft |
| **标签** | android, logcat, event_tags, system |

---

## 1. 概述

本文件定义 Android 系统级别的 Event Log Tags，这些 Tags 由 Android 框架和系统服务生成。

---

## 2. Tags 定义

### 2.1 系统核心 Tags

| Tag | 来源 | 含义 | 严重级别 |
|-----|------|------|----------|
| `AndroidRuntime` | Android Runtime | 运行时异常和崩溃 | E/W |
| `ActivityManager` | Activity 管理器 | Activity 生命周期事件 | I/D |
| `PackageManager` | 包管理器 | 应用安装/卸载事件 | I/D |
| `WindowManager` | 窗口管理器 | 窗口状态变化 | I/D |
| `InputDispatcher` | 输入分发器 | 输入事件处理 | I/W |

### 2.2 服务相关 Tags

| Tag | 来源 | 含义 | 严重级别 |
|-----|------|------|----------|
| `ConnectivityService` | 网络连接服务 | 网络状态变化 | I/D |
| `WifiService` | WiFi 服务 | WiFi 连接事件 | I/D |
| `PowerManagerService` | 电源管理服务 | 电源状态变化 | I/W |
| `BatteryService` | 电池服务 | 电池状态变化 | I/D |

### 2.3 性能相关 Tags

| Tag | 来源 | 含义 | 严重级别 |
|-----|------|------|----------|
| `chatty` | 系统守护进程 | 频繁日志抑制提示 | I |
| `am_hprof` | ActivityManager | HPROF 内存快照 | I |
| `StrictMode` | 严格模式 | 性能警告 | W/E |
| `Watchdog` | 系统看门狗 | 服务超时检测 | E |

### 2.4 安全相关 Tags

| Tag | 来源 | 含义 | 严重级别 |
|-----|------|------|----------|
| `Security` | 安全框架 | 安全事件 | E/W |
| `SELinux` | SELinux 子系统 | 权限检查 | E/W |
| `keystore` | 密钥库服务 | 密钥操作 | I/E |

---

## 3. 使用说明

### 3.1 过滤系统 Tags

```bash
# 过滤所有系统级别日志
adb logcat -s AndroidRuntime:E ActivityManager:I

# 过滤严重级别为 Error 的系统日志
adb logcat *:E | grep -E "(AndroidRuntime|Watchdog|Security)"
```

### 3.2 常见问题

| 问题模式 | 相关 Tag | 排查方向 |
|----------|----------|----------|
| 应用崩溃 | AndroidRuntime | 检查堆栈跟踪 |
| ANR | ActivityManager | 检查 ANR 日志 |
| 网络问题 | ConnectivityService | 检查网络状态 |
| 电池耗电 | BatteryService | 检查耗电应用 |

---

## 4. 参考资料

- Android 官方文档: [EventLog Tags](https://source.android.com/docs/core/system/event-log)
- AOSP 源码: frameworks/base/core/java/android/util/EventLog.java