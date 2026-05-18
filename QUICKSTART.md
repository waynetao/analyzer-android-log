# Android 日志分析 AI Agent - 快速开始指南

## 问题分析

从你的运行结果来看，主要有以下几个问题：

### 1. 日志路径问题
```
⚠️ 技能 log_extraction: 日志提取失败: [Errno 2] No such file or directory: 'D:\\02_project_my\\06_agent\\android-log-analyzer-main\\bug'
```
**原因**：你的 `bug` 目录不存在或者没有有效的日志文件

### 2. aloggrep 不可用
```
⚠️ 技能 aloggrep_analysis: aloggrep is not available
```
**原因**：aloggrep 是 Android 系统工具，可选功能。这是正常的。

### 3. 其他技能缺少参数
这是因为日志提取失败后，后续技能缺少必要输入。

---

## 正确使用方式

### 方式一：使用示例数据（推荐先尝试这个）

```bash
# 在项目根目录下运行
cd E:\01_workspace\02_studyAgent\android-log-analyzer-main

# 1. 使用示例数据测试
python scripts/harness_agent_advanced.py --bug "example/bug/sample_bug.txt" --log "example/bug"
```

### 方式二：使用真实数据

1. **准备你的数据**：
   - 创建一个目录（比如 `my_bug`）
   - 在该目录中放置至少一个日志文件（.log 或 .txt）
   - 准备一个 bug 描述文件（文本文件）

2. **运行分析**：
```bash
python scripts/harness_agent_advanced.py --bug "my_bug/bug_description.txt" --log "my_bug"
```

### 方式三：使用单个日志文件

```bash
python scripts/harness_agent_advanced.py --bug "my_bug.txt" --log "test_log.txt"
```

---

## 预期的输出结构

运行成功后，你会看到：

```
✅ 工作流执行成功!
报告保存在: outputs/reports/
```

输出会在 `outputs/reports/` 目录下，包含：
- Markdown 格式报告
- HTML 格式报告
- JSON 格式报告

---

## 其他说明

### 1. 配置 .env 文件（可选）

创建 `.env` 文件在项目根目录，配置 LLM：
```
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

### 2. 如果没有 LLM

代码会自动使用模拟模式，仍然会生成有价值的分析报告（基于规则）。

### 3. aloggrep 功能

这是一个可选的 Android 系统工具，用于高级日志分析。如果没有安装也没关系，基础功能不受影响。

---

## 示例数据说明

`example/bug/` 目录已准备好，包含：
- `sample_bug.txt` - 示例 Bug 描述
- `test_log.txt` - 示例日志文件

你可以先运行这个测试，确认环境配置正确！
