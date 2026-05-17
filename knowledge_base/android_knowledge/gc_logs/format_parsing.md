# GC 日志格式解析指南

## 文档信息

| 字段 | 值 |
|------|-----|
| **版本** | v1.0 |
| **适用版本** | Android 8.0+ |
| **最后更新** | 2026-05-17 |
| **状态** | Draft |
| **标签** | android, gc, art, logcat |

---

## 1. 概述

本文件详细说明 ART GC 日志的格式和解析方法。

---

## 2. GC 日志格式

### 2.1 标准日志格式

```text
I art     : <GC_TYPE> <HEAP_TYPE> <ALLOC_STATS> <TIME>

示例:
I art     : GC_CONCURRENT freed 2000K, 30% free 5000K/7100K, paused 2ms+3ms, total 50ms
I art     : GC_FOR_ALLOCATION freed 1000K, 20% free 4000K/5000K, paused 20ms
```

### 2.2 关键字段定义

| 字段 | 类型 | 含义 | 示例 |
|------|------|------|------|
| GC_TYPE | string | GC 类型 | GC_CONCURRENT |
| HEAP_TYPE | string | 堆类型 | AllocSpace |
| freed | int | 释放内存 | 2000K |
| free_percent | int | 空闲百分比 | 30% |
| used | int | 已用内存 | 5000K |
| total | int | 总内存 | 7100K |
| paused | int/int | 暂停时间 | 2ms+3ms |
| total_time | int | 总耗时 | 50ms |

### 2.3 堆类型说明

| 堆类型 | 描述 |
|--------|------|
| AllocSpace | 分配空间 |
| LargeObjectSpace | 大对象空间 |
| ImageSpace | 镜像空间 |
| ZygoteSpace | Zygote 空间 |

### 2.4 并发 GC 日志

```text
I art     : GC_CONCURRENT <phase> <stats>

Phase:
  - Before starting
  - After mark
  - After sweep

示例:
I art     : GC_CONCURRENT Before starting, 5000K allocated
I art     : GC_CONCURRENT After mark, 30% free
I art     : GC_CONCURRENT After sweep, freed 2000K
```

---

## 3. 解析方法

### 3.1 解析步骤

1. **识别 GC 类型**：查看日志开头
2. **提取内存统计**：解析 freed/free/total
3. **分析暂停时间**：查看 paused 字段
4. **判断问题**：频繁 GC? 耗时过长?

### 3.2 日志分析工具

```bash
# 过滤 GC 日志
adb logcat -s art:I | grep GC_

# 统计 GC 次数
adb logcat -s art:I | grep GC_ | wc -l

# 分析 GC 耗时
adb logcat -s art:I | grep GC_ | awk '{print $NF}'
```

### 3.3 关键指标

| 指标 | 警告阈值 | 说明 |
|------|---------|------|
| GC 频率 | > 5次/分钟 | 频繁GC |
| 单次耗时 | > 100ms | 耗时过长 |
| 空闲率 | < 10% | 内存紧张 |
| 释放量 | < 100K | 回收效率低 |

---

## 4. 示例分析

### 4.1 正常 GC

```text
I art     : GC_CONCURRENT freed 2000K, 30% free 5000K/7100K, paused 2ms+3ms, total 50ms
```
分析：正常的并发GC，暂停时间短，回收效率正常

### 4.2 频繁 GC

```text
I art     : GC_FOR_ALLOCATION freed 100K, 5% free 6900K/7300K, paused 15ms
I art     : GC_FOR_ALLOCATION freed 150K, 6% free 6850K/7300K, paused 12ms
I art     : GC_FOR_ALLOCATION freed 120K, 5% free 6880K/7300K, paused 18ms
```
分析：连续的分配失败GC，内存不足，可能有内存泄漏

### 4.3 长时间暂停

```text
I art     : GC_BEFORE_OOM freed 500K, 2% free 7200K/7350K, paused 150ms
```
分析：OOM前的最后GC，暂停时间长，内存严重不足

---

## 5. 参考资料

- Android 官方文档: [ART Logging](https://source.android.com/docs/core/runtime/art-logging)