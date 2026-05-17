# dumpsys meminfo SOP

## 文档信息

| 字段 | 值 |
|------|-----|
| **版本** | v1.0 |
| **适用版本** | Android 8.0+ |
| **最后更新** | 2026-05-17 |
| **状态** | Draft |
| **标签** | android, dumpsys, meminfo, memory |

---

## 1. 概述

本 SOP 描述如何使用 `dumpsys meminfo` 命令分析 Android 应用的内存使用情况。

---

## 2. 命令格式

```bash
# 基本用法
dumpsys meminfo <package_name>

# 详细输出
dumpsys meminfo <package_name> -d

# 所有进程
dumpsys meminfo

# 按 PID
dumpsys meminfo <pid>
```

### 2.1 输出格式结构

```text
Applications Memory Usage (in Kilobytes):
Uptime: <uptime> Realtime: <realtime>

** MEMINFO in pid <pid> [package_name] **
                   Pss  Private  Private  SwapPss     Heap     Heap     Heap
                 Total    Dirty    Clean    Dirty     Size    Alloc     Free
                ------   ------   ------   ------   ------   ------   ------
  Native Heap    12345      678      123      456    20000    15000     5000
  Dalvik Heap     4567      234      567        0     8000     6000     2000
         ...
        TOTAL    50000     1000      500      100    30000    25000     5000

 Objects
               Views: <count>         ViewRootImpl: <count>
         AppContexts: <count>           Activities: <count>
              Assets: <count>        AssetManagers: <count>
       Local Binders: <count>        Proxy Binders: <count>
       Parcel memory: <count>         Parcel count: <count>
    Death Recipients: <count>      OpenSSL Sockets: <count>

 SQL
         MEMORY_USED: <bytes>
  PAGECACHE_OVERFLOW: <bytes>          MALLOC_SIZE: <bytes>

 DATABASES
      pgsz     dbsz   Lookaside(b)  Dbname
         4       32              0  <dbname>
```

### 2.2 关键字段定义

| 字段 | 类型 | 含义 | 单位 |
|------|------|------|------|
| Pss Total | int | Proportional Set Size | KB |
| Private Dirty | int | 私有脏内存 | KB |
| Private Clean | int | 私有干净内存 | KB |
| SwapPss Dirty | int | 交换区脏内存 | KB |
| Heap Size | int | 堆总大小 | KB |
| Heap Alloc | int | 已分配堆内存 | KB |
| Heap Free | int | 空闲堆内存 | KB |

---

## 3. 分析方法

### 3.1 分析步骤

1. **获取内存信息**：`dumpsys meminfo <package_name> -d`
2. **检查 Pss Total**：判断整体内存占用
3. **检查 Native/Dalvik Heap**：分析堆内存使用
4. **检查 Private Dirty**：识别内存泄漏
5. **检查 Objects 计数**：查看对象数量是否异常

### 3.2 关键指标阈值

| 指标 | 警告阈值 | 严重阈值 | 说明 |
|------|---------|---------|------|
| Pss Total | > 200MB | > 500MB | 整体内存占用 |
| Native Heap | > 100MB | > 200MB | Native 堆内存 |
| Dalvik Heap | > 80MB | > 150MB | Java 堆内存 |
| Private Dirty | > 150MB | > 300MB | 私有脏内存 |

### 3.3 常见问题分析

| 问题模式 | 指标异常 | 排查方向 |
|----------|---------|----------|
| 内存泄漏 | Private Dirty 持续增长 | 检查生命周期、静态引用 |
| 堆溢出 | Heap Alloc 接近 Heap Size | 检查大对象、缓存策略 |
| Native 内存问题 | Native Heap 过大 | 检查 JNI、图片处理 |

---

## 4. 示例分析

```bash
# 分析示例应用
dumpsys meminfo com.example.app

# 输出分析
# Pss Total: 150MB - 正常
# Native Heap: 60MB - 正常
# Dalvik Heap: 40MB - 正常
# Private Dirty: 80MB - 正常
```

---

## 5. 参考资料

- Android 官方文档: [Memory Analysis](https://developer.android.com/studio/profile/memory-profiler)
- dumpsys 源码: frameworks/native/cmds/dumpsys/dumpsys.cpp