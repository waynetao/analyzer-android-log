# Android 日志分析知识库

## 概述

本知识库包含 Android 日志分析所需的核心知识文档，用于支持 AI Agent 进行准确、高质量的日志分析。

## 知识域清单

| 知识域 | 文档数量 | 状态 | 描述 |
|--------|---------|------|------|
| Event Log Tags | 4 | Active | Android 系统 Event Log Tags 定义 |
| ANR/Tombstone | 4 | Active | ANR 和 Tombstone 日志格式与分析 |
| dumpsys | 4 | Active | dumpsys 关键服务 SOP |
| 系统属性 | 3 | Active | Android 系统属性定义 |
| GC 日志 | 3 | Active | ART GC 日志格式解析 |

## 快速导航

### 问题诊断

| 问题类型 | 推荐文档 |
|----------|----------|
| 应用崩溃 | anr_tombstone/anr_format.md, anr_tombstone/tombstone_format.md |
| 内存问题 | dumpsys/meminfo_sop.md, gc_logs/format_parsing.md |
| 电池问题 | dumpsys/battery_sop.md |
| 系统属性 | sysprops/critical_props.md |

### 日志类型

| 日志类型 | 推荐文档 |
|----------|----------|
| Logcat Tags | event_log_tags/system_tags.md, event_log_tags/app_tags.md |
| ANR | anr_tombstone/anr_format.md |
| Native Crash | anr_tombstone/tombstone_format.md |
| GC | gc_logs/format_parsing.md |

## 使用说明

### 检索方式

```bash
# 通过 QMD 查询
qmd search "ANR 格式"

# 通过 Agent 技能
from harness.skills.knowledge_retrieval import KnowledgeRetrievalSkill

skill = KnowledgeRetrievalSkill()
result = skill.execute({
    "query": "ANR 格式",
    "doc_type": "anr",
    "top_k": 3
})
```

## 更新日志

| 日期 | 更新内容 | 作者 |
|------|----------|------|
| 2026-05-17 | 初始版本创建 | AI Assistant |
| 2026-05-17 | 创建所有知识域 demo 模板 | AI Assistant |

## 版本信息

| 字段 | 值 |
|------|-----|
| 版本 | v1.0.0 |
| 创建日期 | 2026-05-17 |
| 文档总数 | 18 |
| 适用 Android 版本 | 8.0+ |