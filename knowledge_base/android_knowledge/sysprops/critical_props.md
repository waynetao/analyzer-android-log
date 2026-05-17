# 系统关键属性定义

## 文档信息

| 字段 | 值 |
|------|-----|
| **版本** | v1.0 |
| **适用版本** | Android 8.0+ |
| **最后更新** | 2026-05-17 |
| **状态** | Draft |
| **标签** | android, sysprops, system, properties |

---

## 1. 概述

本文件定义 Android 系统的关键属性，这些属性对问题分析和环境确认非常重要。

---

## 2. 属性定义

### 2.1 设备信息属性

| 属性名 | 类型 | 含义 | 示例 |
|--------|------|------|------|
| ro.product.model | string | 设备型号 | Pixel 5 |
| ro.product.brand | string | 品牌 | google |
| ro.product.name | string | 产品名称 | redfin |
| ro.build.version.sdk | int | SDK 版本 | 33 |
| ro.build.version.release | string | Android 版本 | 13 |
| ro.build.fingerprint | string | 构建指纹 | google/... |

### 2.2 硬件信息属性

| 属性名 | 类型 | 含义 | 示例 |
|--------|------|------|------|
| ro.hardware | string | 硬件名称 | qcom |
| ro.board.platform | string | 平台 | sdsm845 |
| ro.cpu.abilist | string | ABI 列表 | arm64-v8a,armeabi-v7a |
| persist.sys.usb.config | string | USB 配置 | adb |

### 2.3 系统状态属性

| 属性名 | 类型 | 含义 | 示例 |
|--------|------|------|------|
| sys.boot_completed | int | 启动完成标志 | 1 |
| sys.usb.state | string | USB 状态 | connected |
| persist.sys.timezone | string | 时区 | Asia/Shanghai |

### 2.4 内存相关属性

| 属性名 | 类型 | 含义 | 示例 |
|--------|------|------|------|
| dalvik.vm.heapsize | string | 堆大小 | 512m |
| dalvik.vm.heapgrowthlimit | string | 堆增长限制 | 256m |
| dalvik.vm.stack-trace-file | string | 堆栈文件 | /data/anr/traces.txt |

---

## 3. 使用说明

### 3.1 获取属性

```bash
# 获取单个属性
getprop ro.build.version.sdk

# 获取所有属性
getprop

# 过滤属性
getprop | grep heap
```

### 3.2 设置属性（需要 root）

```bash
# 设置属性
setprop persist.sys.debug.memory 1

# 持久化属性
setprop persist.sys.usb.config adb
```

---

## 4. 常见问题

| 属性异常 | 可能原因 | 影响 |
|----------|---------|------|
| ro.build.version.sdk 不匹配 | ROM 篡改 | 兼容性问题 |
| sys.boot_completed=0 | 启动未完成 | 服务不可用 |
| dalvik.vm.heapsize 过小 | 配置错误 | OOM 问题 |

---

## 5. 参考资料

- Android 官方文档: [Properties](https://source.android.com/docs/core/system/init/properties)