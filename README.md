# Harness Android Log Analysis Agent

## 📋 项目概况

基于 Harness Engineering 架构的 Android 日志分析 AI Agent，支持高质量的自动化分析、证据匹配、LLM 集成、记忆系统等功能。

**当前版本**: v7.0 (Memory System)  
**最后更新**: 2026-05-17

---

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
cd /workspace

# 安装依赖
pip install -r requirements.txt

# 可选：安装 aloggrep
cargo install aloggrep
```

### 2. 运行 Agent
```bash
# 使用高级 Agent（推荐）
python scripts/harness_agent_advanced.py \
    --bug "描述你的Bug" \
    --log logcat.txt \
    --format markdown

# 使用基础 Agent
python scripts/harness_agent.py \
    --bug "描述你的Bug" \
    --log logcat.txt
```

### 3. Feature Flag 管理
```bash
# 查看所有 flags
python scripts/ffctl.py list

# 禁用某个功能
python scripts/ffctl.py set aloggrep_integration --disable

# 设置灰度发布
python scripts/ffctl.py set llm_analysis_enabled --percentage 50
```

---

## ✨ 核心功能

### 基础功能 (v1.0)
- ✅ 日志解析和提取
- ✅ Bug 自动分析
- ✅ 多格式报告生成 (Markdown/HTML/JSON)

### LLM 集成 (v2.0)
- ✅ Bug 描述智能解析
- ✅ 日志智能过滤
- ✅ 异常自动分类
- ✅ 模式匹配识别

### 证据匹配 (v3.0)
- ✅ 用户描述与日志证据匹配
- ✅ 时间轴重构
- ✅ 置信度评分系统

### aloggrep 集成 (v4.0)
- ✅ aloggrep 命令包装
- ✅ 四阶段分析工作流
- ✅ 异常检测和模式识别

### QMD 知识库 (v5.0)
- ✅ Event Log Tags 完整定义
- ✅ ANR/Tombstone 格式说明
- ✅ dumpsys SOP 文档
- ✅ GC 日志解析指南

### Feature Flag 管控 (v6.0)
- ✅ Feature Flag 核心引擎
- ✅ 环境隔离支持
- ✅ 百分比灰度发布
- ✅ 目标规则匹配
- ✅ ffctl 命令行管理

### 记忆系统 (v7.0)
- ✅ 双模记忆系统（Simple / OpenViking）
- ✅ 本地 JSON 存储（零依赖）
- ✅ 案例库技能（CRUD、搜索、统计）
- ✅ 完整测试覆盖

---

## 🏗️ 架构设计

### Harness Engineering 架构
```
┌─────────────────────────────────────────┐
│         Harness Core                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │StateMngr │ │ContextEng│ │Orchestrator│
│  └──────────┘ └──────────┘ └──────────┘ │
│  ┌──────────────────────────────────┐ │
│  │    Feature Flag Engine          │ │
│  └──────────────────────────────────┘ │
│  ┌──────────────────────────────────┐ │
│  │      Memory System              │ │
│  └──────────────────────────────────┘ │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│        Skills Layer                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │LogExtrac │ │BugAnaly │ │ReportGen││
│  └──────────┘ └──────────┘ └──────────┘│
│  ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │LLMAnaly  │ │Evidence  │ │Knowledge││
│  └──────────┘ └──────────┘ └──────────┘│
│  ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │aloggrep  │ │Timeline │ │CaseLib  ││
│  └──────────┘ └──────────┘ └──────────┘│
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│       Policies Layer                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │Validation│ │Quality   │ │Format    ││
│  └──────────┘ └──────────┘ └──────────┘│
└─────────────────────────────────────────┘
```

---

## 📁 项目结构

```
/workspace/
├── scripts/                           # 脚本和工具
│   ├── harness_agent.py              # 基础 Agent
│   ├── harness_agent_advanced.py     # 高级 Agent（推荐）
│   └── ffctl.py                      # Feature Flag 管理
├── harness/
│   ├── core/
│   │   ├── state.py                  # 状态管理
│   │   ├── context.py                # 上下文管理
│   │   ├── orchestrator.py           # 工作流编排
│   │   └── feature_flags.py          # Feature Flag 引擎
│   ├── skills/                       # 技能层
│   ├── policies/                     # 策略层
│   └── memory/                       # 记忆系统
├── log_analyzer/                     # 日志分析库
├── knowledge_base/                   # 知识文档
├── config/                           # 配置文件
├── tests/                            # 测试文件
│   ├── test_*.py                     # 单元测试和集成测试
├── docs/                             # 项目文档
│   ├── CHANGELOG.md                  # 版本变更记录
│   ├── AGENTS.md                     # 架构设计文档
│   └── ...                           # 其他文档
├── data/                             # 示例数据
├── outputs/                          # 输出目录
├── requirements.txt                  # Python 依赖
├── docker-compose.yaml               # Docker 配置
└── README.md                         # 项目说明
```

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [PROJECT_SUMMARY.md](file:///workspace/docs/PROJECT_SUMMARY.md) | 完整项目总结文档 |
| [AGENTS.md](file:///workspace/docs/AGENTS.md) | 架构设计文档 |
| [CHANGELOG.md](file:///workspace/docs/CHANGELOG.md) | 版本变更记录 |
| [MEMORY_SYSTEM_GUIDE.md](file:///workspace/docs/MEMORY_SYSTEM_GUIDE.md) | 记忆系统使用指南 |
| [HIGH_QUALITY_ANALYSIS_GUIDE.md](file:///workspace/docs/HIGH_QUALITY_ANALYSIS_GUIDE.md) | 高质量分析指南 |
| [ALOGGREP_INTEGRATION.md](file:///workspace/docs/ALOGGREP_INTEGRATION.md) | aloggrep 集成文档 |
| [QMD_INTEGRATION_SCHEME.md](file:///workspace/docs/QMD_INTEGRATION_SCHEME.md) | QMD 集成方案 |
| [QMD_IMPACT_EVALUATION.md](file:///workspace/docs/QMD_IMPACT_EVALUATION.md) | QMD 价值评估 |

---

## 🧪 测试验证

```bash
# 进入 tests 目录
cd tests

# 全面功能验证
python test_full_validation.py

# Feature Flag 测试
python test_feature_flags_advanced.py

# 案例库测试
python test_case_library_advanced.py

# 核心集成测试
python test_core_integration.py

# 记忆系统集成测试
python test_integration_memory_system.py

# aloggrep 集成测试
python test_aloggrep_deep_integration.py

# 回归测试
python test_regression_v2.py

# 或者在项目根目录运行所有测试
python -m pytest tests/ -v
```

---

## 🎯 Feature Flags

### 预置 Flags
```yaml
llm_analysis_enabled:
  描述: 是否启用 LLM 分析功能
  类型: boolean
  默认: true

aloggrep_integration:
  描述: 是否启用 aloggrep 集成
  类型: boolean
  默认: true

knowledge_base_enabled:
  描述: 是否启用 QMD 知识库检索
  类型: boolean
  默认: true

evidence_matching_enabled:
  描述: 是否启用日志证据匹配
  类型: boolean
  默认: true

analysis_mode:
  描述: 分析模式
  类型: multivariate
  选项: fast / standard / deep
  默认: standard

memory_system_enabled:
  描述: 是否启用记忆系统
  类型: boolean
  默认: true
```

---

## 📊 版本迭代历程

| 版本 | 日期 | 主要功能 |
|------|------|---------|
| 7.0.0 | 2026-05-17 | 记忆系统集成 |
| 6.0.0 | 2026-05-17 | Feature Flag 管控 |
| 5.0.0 | 2026-05-17 | QMD 知识库集成 |
| 4.0.0 | 2026-05-17 | aloggrep 深度集成 |
| 3.0.0 | 2026-05-17 | 证据匹配和时间线 |
| 2.0.0 | 2026-05-17 | LLM 集成增强 |
| 1.0.0 | 2026-05-16 | 初始版本 |

---

## 💡 下一步规划

- [ ] 完善知识库内容
- [ ] 集成实际 QMD 服务
- [ ] 性能优化和监控
- [ ] 持续迭代新特性（通过 Feature Flag）
- [ ] 优化案例库功能

---

## 📝 许可证

基于 Harness Engineering 架构构建。

---

## 🙏 致谢

感谢 Harness Engineering 架构思想和 aloggrep 项目的启发！
