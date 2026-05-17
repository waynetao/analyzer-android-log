# 调试属性定义

## 文档信息

| 字段 | 值 |
|------|-----|
| **版本** | v1.0 |
| **适用版本** | Android 8.0+ |
| **最后更新** | 2026-05-17 |
| **状态** | Draft |
| **标签** | android, sysprops, debug, properties |

---

## 1. 概述

本文件定义 Android 系统的调试属性，用于开启各种调试功能。

---

## 2. 调试属性定义

### 2.1 日志调试属性

| 属性名 | 类型 | 含义 | 默认值 |
|--------|------|------|--------|
| debug.atrace.tags.enableflags | int | atrace 标签 | 0 |
| debug.log.tag.<tag> | string | 特定 Tag 级别 | null |
| persist.log.tag.<tag> | string | 持久化 Tag 级别 | null |
| debug.log.level | string | 全局日志级别 | null |

### 2.2 内存调试属性

| 属性名 | 类型 | 含义 | 默认值 |
|--------|------|------|--------|
| debug.meminfo.app_procs | string | meminfo 过滤 | null |
| debug.memory.max_usage_threshold | int | 内存阈值(%) | 90 |
| persist.sys.debug.memory | int | 内存调试模式 | 0 |

### 2.3 性能调试属性

| 属性名 | 类型 | 含义 | 默认值 |
|--------|------|------|--------|
| debug.sf.showfps | int | 显示帧率 | 0 |
| debug.perf.trace.enable | int | 性能追踪 | 0 |
| debug.perf.prof_cpu | int | CPU 采样 | 0 |

### 2.4 ANR 调试属性

| 属性名 | 类型 | 含义 | 默认值 |
|--------|------|------|--------|
| debug.anrshowdialog | int | 显示 ANR 对话框 | 1 |
| debug.sf.hw | int | 硬件加速 | 1 |
| persist.sys.anrdebug | int | ANR 调试模式 | 0 |

### 2.5 网络调试属性

| 属性名 | 类型 | 含义 | 默认值 |
|--------|------|------|--------|
| persist.sys.debug.network | int | 网络调试 | 0 |
| net.dns1 | string | DNS 服务器1 | - |
| net.dns2 | string | DNS 服务器2 | - |

---

## 3. 使用说明

### 3.1 开启调试属性

```bash
# 开启帧率显示
setprop debug.sf.showfps 1

# 设置特定 Tag 级别
setprop debug.log.tag.MyApp VERBOSE

# 开启内存调试
setprop persist.sys.debug.memory 1
```

### 3.2 常用调试命令

```bash
# 查看所有调试属性
getprop | grep debug

# 查看日志级别设置
getprop | grep log.tag

# 重置所有调试属性
setprop persist.sys.debug.memory 0
```

---

## 4. 参考资料

- Android 官方文档: [Debugging](https://source.android.com/docs/core/debug)