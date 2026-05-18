# Android 日志分析 AI Agent - 快速开始指南

## 前置准备

### 安装必要工具

在开始之前，请先阅读 [工具安装指南](./INSTALL_TOOLS.md)，其中包含：
- Python 安装
- Git 安装
- **aloggrep 安装**（强烈推荐，可以大幅提升分析效果）

### 验证环境

```bash
# 检查 Python
python --version

# 检查 aloggrep（如果安装了）
aloggrep --version

# 运行健康检查
python tests/test_health_check.py
```

---

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

#### 基础配置

创建 `.env` 文件在项目根目录，配置 LLM：
```
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

#### 场景定制（高级功能）

你可以为不同的分析场景配置不同的模型！支持的场景：
- `analysis`: LLM 高级分析（复杂推理）
- `bug_parser`: Bug 描述解析
- `log_filter`: 智能日志过滤
- `exception_classifier`: 异常分类
- `evidence_matcher`: 日志证据匹配

示例配置（在 `.env` 中添加）：
```
# 分析场景用更强大的模型
LLM_ANALYSIS_API_KEY=your_api_key
LLM_ANALYSIS_MODEL=gpt-4o
LLM_ANALYSIS_MAX_TOKENS=4000

# Bug 解析用更快更便宜的模型
LLM_BUG_PARSER_MODEL=gpt-4o-mini
LLM_BUG_PARSER_TEMPERATURE=0.3
```

更多预定义模型配置请参考 [.env.example](./.env.example)

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
