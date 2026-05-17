# GC 类型说明

## 文档信息

| 字段 | 值 |
|------|-----|
| **版本** | v1.0 |
| **适用版本** | Android 8.0+ |
| **最后更新** | 2026-05-17 |
| **状态** | Draft |
| **标签** | android, gc, art, memory |

---

## 1. 概述

本文件说明 Android ART 虚拟机支持的各种 GC 类型及其特点。

---

## 2. GC 类型定义

### 2.1 GC 类型列表

| GC 类型 | 名称 | 描述 | 暂停时间 | 适用场景 |
|---------|------|------|----------|----------|
| GC_CONCURRENT | Concurrent GC | 并发回收，不阻塞主线程 | 短 | 日常回收 |
| GC_FOR_ALLOCATION | Allocation GC | 分配失败触发的同步 GC | 中等 | 内存紧张 |
| GC_BEFORE_OOM | OOM 前 GC | OOM 前的最后尝试 | 长 | OOM 前 |
| GC_EXPLICIT | Explicit GC | 显式调用 System.gc() | 中等 | 手动触发 |
| GC_TRIM_MEMORY | Trim GC | 内存整理 | 短 | 低内存时 |
| GC_WHEN_IDLE | Idle GC | 空闲时执行 | 中等 | 空闲状态 |

### 2.2 GC 模式说明

| 模式 | 描述 | 特点 |
|------|------|------|
| Partial GC | 只回收部分代 | 快速 |
| Full GC | 回收所有代 | 较慢 |
| Mark-Sweep | 标记-清除 | 不移动对象 |
| Mark-Compact | 标记-压缩 | 移动对象，整理内存 |

---

## 3. GC 触发条件

### 3.1 自动触发

| 条件 | 触发类型 | 说明 |
|------|---------|------|
| 分配失败 | GC_FOR_ALLOCATION | 堆内存不足 |
| 堆达到阈值 | GC_CONCURRENT | 后台并发回收 |
| 低内存通知 | GC_TRIM_MEMORY | 系统通知低内存 |
| 空闲状态 | GC_WHEN_IDLE | CPU 空闲时 |

### 3.2 手动触发

| 方式 | 类型 | 说明 |
|------|------|------|
| System.gc() | GC_EXPLICIT | 应用显式调用 |
| Runtime.getRuntime().gc() | GC_EXPLICIT | 同 System.gc() |

---

## 4. GC 性能影响

### 4.1 暂停时间参考

| GC 类型 | 典型暂停时间 | 影响 |
|---------|-------------|------|
| GC_CONCURRENT | < 5ms | 几乎无感知 |
| GC_FOR_ALLOCATION | 10-50ms | 可能卡顿 |
| GC_BEFORE_OOM | 50-200ms | 明显卡顿 |
| GC_EXPLICIT | 10-100ms | 取决于堆大小 |

### 4.2 常见问题

| 问题 | 表现 | 原因 |
|------|------|------|
| GC 频繁 | 每秒多次 GC | 内存泄漏或分配过快 |
| GC 耗时过长 | 单次 GC > 100ms | 堆过大或碎片严重 |
| OOM | GC 后仍无法分配 | 内存泄漏或堆不足 |

---

## 5. 参考资料

- Android 官方文档: [ART GC](https://source.android.com/docs/core/runtime/gc)
- ART 源码: art/runtime/gc/collector/