# dumpsys battery SOP

## 文档信息

| 字段 | 值 |
|------|-----|
| **版本** | v1.0 |
| **适用版本** | Android 8.0+ |
| **最后更新** | 2026-05-17 |
| **状态** | Draft |
| **标签** | android, dumpsys, battery, power |

---

## 1. 概述

本 SOP 描述如何使用 `dumpsys battery` 和 `dumpsys batterystats` 命令分析 Android 设备的电池使用情况。

---

## 2. 命令格式

```bash
# 电池状态
dumpsys battery

# 电池统计
dumpsys batterystats

# 指定应用统计
dumpsys batterystats <package_name>

# 重置统计
dumpsys batterystats --reset

# 生成报告
dumpsys batterystats > /sdcard/battery_report.txt
```

### 2.1 dumpsys battery 输出格式

```text
Current Battery Service state:
  AC powered: false
  USB powered: true
  Wireless powered: false
  Max charging current: 500000
  Max charging voltage: 5000000
  Charge counter: 4500000
  status: 2
  health: 2
  present: true
  level: 85
  scale: 100
  voltage: 4200
  temperature: 300
  technology: Li-ion
```

### 2.2 dumpsys batterystats 输出格式

```text
Battery History (60% used, 49KB used of 80KB, 115 entries)
...
Aggregate power use:
  Capacity: 4500 mAh
  Total drain: 1200 mAh (26.67%)
  
  Per-app drain:
    com.example.app: 200 mAh (16.67%)
    com.android.systemui: 150 mAh (12.5%)
    ...
  
  Wake locks:
    com.example.app: 30 minutes
    ...
```

### 2.3 关键字段定义

| 字段 | 类型 | 含义 | 单位 |
|------|------|------|------|
| level | int | 电池电量百分比 | % |
| scale | int | 电量刻度 | % |
| voltage | int | 电池电压 | mV |
| temperature | int | 电池温度 | 0.1°C |
| status | int | 状态码 | - |
| health | int | 健康状态码 | - |

### 2.4 状态码说明

| status | 含义 | health | 含义 |
|--------|------|--------|------|
| 1 | Unknown | 1 | Unknown |
| 2 | Charging | 2 | Good |
| 3 | Discharging | 3 | Overheat |
| 4 | Not charging | 4 | Dead |
| 5 | Full | 5 | Over voltage |

---

## 3. 分析方法

### 3.1 分析步骤

1. **检查电池状态**：`dumpsys battery`
2. **获取统计信息**：`dumpsys batterystats <package_name>`
3. **分析耗电应用**：查看 Per-app drain
4. **检查唤醒锁**：查看 Wake locks
5. **检查网络唤醒**：查看 Mobile radio active

### 3.2 关键指标

| 指标 | 警告阈值 | 说明 |
|------|---------|------|
| 应用耗电占比 | > 30% | 单个应用耗电过高 |
| 唤醒锁时长 | > 1小时/天 | 唤醒锁使用过多 |
| 移动网络活跃 | > 2小时/天 | 网络唤醒频繁 |
| 屏幕开启 | > 4小时/天 | 屏幕耗电过多 |

### 3.3 常见问题分析

| 问题模式 | 指标异常 | 排查方向 |
|----------|---------|----------|
| 待机耗电快 | 待机时应用耗电高 | 检查后台服务、定时任务 |
| 唤醒锁过多 | Wake locks 时间长 | 检查 WakeLock 使用 |
| 网络耗电高 | Mobile radio 活跃时间长 | 检查网络请求频率 |

---

## 4. 参考资料

- Android 官方文档: [Battery](https://developer.android.com/training/monitoring-device-state/battery-monitoring)