# 工具安装指南

## 概述

本项目使用一些可选工具来提供增强功能。虽然这些工具不是必须的，但安装它们可以解锁更强大的分析能力。

---

## 必装工具

### 1. Python 3.8+

这是项目的核心运行环境。

**官网**：https://www.python.org/

**安装**：
```bash
# 检查是否已安装
python --version
# 或
python3 --version
```

### 2. Git

用于版本控制和代码拉取。

**官网**：https://git-scm.com/

---

## 可选但推荐的工具

### 1. aloggrep ⭐ 强烈推荐

**aloggrep** 是一个强大的 Android 日志分析命令行工具，可以大幅提升日志分析的效率和准确性。

**官网/源码**：https://github.com/rossettaylm/loggrep

#### 安装方式

##### 方式一：通过 Cargo 安装（推荐）

先安装 Rust/Cargo：
- **Rust 官网**：https://www.rust-lang.org/tools/install

然后安装 aloggrep：
```bash
cargo install aloggrep
```

##### 方式二：从源码编译

```bash
git clone https://github.com/rossettaylm/loggrep
cd loggrep
cargo install --path .
```

##### 方式三：预编译二进制文件（如果有的话）

查看 GitHub Releases 页面下载预编译版本。

#### 验证安装

```bash
aloggrep --version
# 或
alg --version
```

#### 主要功能

- **多格式支持**：自动识别 logcat (threadtime/brief)、xlog、华为 hilog 格式
- **智能过滤**：按级别/标签/消息/PID/TID 过滤，支持布尔表达式
- **分析能力**：summary 统计、时间直方图（带异常检测）、崩溃提取、去重归并
- **多输出格式**：JSON/CSV 结构化输出，便于程序处理

#### 常用命令示例

```bash
# 全局概览
alg -f app.log --summary
alg -f app.log --histogram 1m  # 带异常检测的时间分布

# 过滤
alg -f app.log --level E  # 错误级别
alg -f app.log --tag OkHttp
alg -f app.log -e 'msg ~ timeout and level >= W'  # 布尔表达式

# 崩溃分析
alg -f app.log --crashes

# 输出控制
alg -f app.log --format json --fields t,l,T,m --limit 100
```

---

### 2. OpenViking ⭐ 可选但推荐

**OpenViking** 是一个分层记忆系统，用于更高效的案例存储和检索。

**官网文档**：https://www.volcengine.com/docs/82379/2288685?lang=zh

**安装方式**：
```bash
pip install openviking
```

**项目配置**：
在 Feature Flag 中启用 OpenViking 模式（`config/feature_flags.yaml`）：
```yaml
memory_mode:
  default_value: openviking
```

**模型配置（可选）**：
OpenViking 支持两种模型配置，在 `.env` 文件中添加：

```bash
# 嵌入模型配置（用于语义搜索）
OPENVIKING_EMBEDDING_BACKEND=volcengine
OPENVIKING_EMBEDDING_API_KEY=<ARK_API_KEY>
OPENVIKING_EMBEDDING_MODEL=doubao-embedding-vision
OPENVIKING_EMBEDDING_API_BASE=https://ark.cn-beijing.volces.com/api/coding/v3

# VLM 模型配置（用于多模态处理）
OPENVIKING_VLM_BACKEND=volcengine
OPENVIKING_VLM_API_KEY=<ARK_API_KEY>
OPENVIKING_VLM_MODEL=doubao-seed-2.0-pro
OPENVIKING_VLM_API_BASE=https://ark.cn-beijing.volces.com/api/coding/v3
OPENVIKING_VLM_TEMPERATURE=0.1
```

**功能说明**：
- 分层存储（L0/L1/L2），优化检索效率
- 自动语义相似度匹配
- 支持标签和类型分类
- 支持多模态嵌入（文本+图像）

---

### 3. QMD Server ⭐ 可选但推荐

**QMD (Knowledge Base)** 是一个知识库服务器，用于存储和检索 Android 开发相关的知识。

**安装方式**（Docker 部署）：
```bash
# QMD 是独立项目，需要单独部署
# 请参考 QMD 项目文档进行 Docker 部署
```

**配置**：
在 `.env` 文件中添加：
```bash
QMD_SERVER_URL=http://localhost:8000
```

**功能说明**：
- 提供 Android 开发知识库（ANR、崩溃、日志格式等）
- 支持语义检索和知识增强
- 通过 REST API 访问

---

### 4. Rust/Cargo（仅用于安装 aloggrep）

如果选择通过 Cargo 安装 aloggrep，则需要安装 Rust。

**官网**：https://www.rust-lang.org/tools/install

**Windows 安装**：
下载并运行 `rustup-init.exe`

**Linux/Mac 安装**：
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

---

## 依赖包安装

### 安装 Python 依赖

在项目根目录运行：

```bash
pip install -r requirements.txt
```

### 主要依赖

| 包名 | 用途 | 必须/可选 |
|-----|------|---------|
| python-dotenv | 加载环境变量 | ✅ 必须 |
| PyYAML | 解析 YAML 配置 | ✅ 必须 |
| openai | LLM 集成（可选） | ⚙️ 可选 |

---

## 完整安装流程（推荐）

### Windows 用户

1. 安装 Python 3.8+
   - 访问 https://www.python.org/downloads/
   - 下载并安装，**务必勾选 "Add Python to PATH"**

2. 安装 Git
   - 访问 https://git-scm.com/download/win
   - 下载并安装

3. 安装 Rust（用于 aloggrep）
   - 访问 https://www.rust-lang.org/tools/install
   - 下载并运行 `rustup-init.exe`

4. 安装 aloggrep
   ```powershell
   cargo install aloggrep
   ```

5. 克隆项目并安装依赖
   ```powershell
   git clone https://github.com/waynetao/android-log-analyzer.git
   cd android-log-analyzer
   pip install -r requirements.txt
   ```

### Linux/Mac 用户

```bash
# 1. 安装 Python 3.8+ (如果未安装)
# Ubuntu/Debian
sudo apt-get install python3 python3-pip

# Mac (使用 Homebrew)
brew install python3

# 2. 安装 Git (如果未安装)
# Ubuntu/Debian
sudo apt-get install git

# Mac
brew install git

# 3. 安装 Rust 和 aloggrep
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
cargo install aloggrep

# 4. 克隆项目并安装依赖
git clone https://github.com/waynetao/android-log-analyzer.git
cd android-log-analyzer
pip install -r requirements.txt
```

---

## 验证安装

### 检查所有工具

```bash
# Python
python --version

# Git
git --version

# aloggrep (如果安装了)
aloggrep --version

# 运行健康检查测试
cd android-log-analyzer
python tests/test_health_check.py
```

---

## 可选：LLM 配置

如果你想使用 AI 增强的分析功能，需要配置 LLM。

复制 `.env.example` 为 `.env`：
```bash
cp .env.example .env
```

然后编辑 `.env` 文件，填入你的配置。

### 支持的模型提供商

已预配置以下常见模型，只需取消注释即可使用：

| 提供商 | 模型示例 | Base URL |
|-------|---------|---------|
| **OpenAI** | gpt-4o, gpt-4o-mini | https://api.openai.com/v1 |
| **智谱 AI** | glm-4, glm-4-flash | https://open.bigmodel.cn/api/paas/v4 |
| **通义千问** | qwen-plus, qwen-turbo | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| **文心一言** | ernie-4.0, ernie-3.5 | https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop |
| **火山引擎** | doubao-pro-32k | https://ark.cn-beijing.volces.com/api/v3 |
| **腾讯混元** | hunyuan-lite | https://hunyuan.tencentcloudapi.com |

### 配置示例

#### 使用 OpenAI
```
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

#### 使用智谱 AI
```
LLM_API_KEY=your_zhipu_key
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash
```

**OpenAI 官网**：https://openai.com/
**智谱 AI 官网**：https://open.bigmodel.cn/
**通义千问官网**：https://dashscope.console.aliyun.com/

---

## 常见问题

### Q: 不安装 aloggrep 可以用吗？
A: 可以！aloggrep 是可选的。不安装它只会缺少一些高级功能，基础分析功能完全可用。

### Q: Cargo 安装很慢怎么办？
A: 可以配置国内镜像源，或者尝试下载预编译版本（如果有的话）。

### Q: aloggrep 支持 Windows 吗？
A: 支持！Rust 是跨平台的，aloggrep 可以在 Windows/Linux/Mac 上运行。

### Q: 如何卸载 aloggrep？
A: `cargo uninstall aloggrep`

---

## 更多文档

- [快速开始指南](./QUICKSTART.md)
- [aloggrep 深度集成](./docs/ALOGGREP_INTEGRATION.md)
- [aloggrep 命令参考](./.claude/skills/loggrep-analyzer/references/commands.md)
