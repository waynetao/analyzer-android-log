# 应用 Event Log Tags 定义

## 文档信息

| 字段 | 值 |
|------|-----|
| **版本** | v1.0 |
| **适用版本** | Android 8.0+ |
| **最后更新** | 2026-05-17 |
| **状态** | Draft |
| **标签** | android, logcat, event_tags, app |

---

## 1. 概述

本文件定义 Android 应用级别的 Event Log Tags，这些 Tags 由第三方应用生成。

---

## 2. 常见应用 Tags

### 2.1 通用应用 Tags

| Tag | 含义 | 常见来源 |
|-----|------|----------|
| `MainActivity` | 主 Activity | 应用入口 |
| `Application` | 应用实例 | 应用生命周期 |
| `WorkManager` | 工作管理器 | 后台任务 |
| `Firebase` | Firebase SDK | 云端服务 |
| `OkHttp` | OkHttp 库 | 网络请求 |
| `Retrofit` | Retrofit 库 | REST API |
| `Glide` | Glide 库 | 图片加载 |
| `Picasso` | Picasso 库 | 图片加载 |

### 2.2 常见第三方库 Tags

| Tag | 含义 | 严重级别 |
|-----|------|----------|
| `LeakCanary` | 内存泄漏检测 | W/E |
| `Crashlytics` | 崩溃报告 | E |
| `Timber` | 日志框架 | V/D/I/W/E |
| `RxJava` | 响应式编程 | I/W/E |
| `Room` | 数据库 | I/W/E |

### 2.3 自定义 Tags 规范

| 命名规则 | 示例 | 说明 |
|----------|------|------|
| 包名风格 | `com.example.app.MainActivity` | 完整类名 |
| 模块风格 | `MyApp:Network` | 应用名:模块名 |
| 功能风格 | `MyApp.Network` | 应用名.功能名 |

---

## 3. 使用说明

### 3.1 过滤应用日志

```bash
# 过滤特定应用的日志
adb logcat -s com.example.app:D

# 过滤网络相关日志
adb logcat -s OkHttp:D Retrofit:D

# 过滤内存泄漏检测日志
adb logcat -s LeakCanary:W
```

### 3.2 日志级别说明

| 级别 | 含义 | 用途 |
|------|------|------|
| V (Verbose) | 详细信息 | 调试信息 |
| D (Debug) | 调试信息 | 开发调试 |
| I (Info) | 一般信息 | 运行状态 |
| W (Warning) | 警告信息 | 潜在问题 |
| E (Error) | 错误信息 | 错误发生 |

---

## 4. 最佳实践

1. **Tag 命名一致性**：整个应用使用统一的命名风格
2. **级别合理使用**：生产环境避免过多 V/D 级别日志
3. **敏感信息保护**：避免在日志中记录密码、Token 等敏感信息
4. **日志分类**：按功能模块划分 Tags

---

## 5. 参考资料

- Android 官方文档: [Logging](https://developer.android.com/reference/android/util/Log)
- Timber: [GitHub](https://github.com/JakeWharton/timber)