# Android 日志分析 AI Agent - 项目总结文档

## 📋 项目概况

**项目名称**: Harness Android Log Analysis Agent  
**版本**: v8.0 (统一 CLI + 分阶段执行)  
**最后更新**: 2026-05-18  
**架构**: Harness Engineering (Core + Skills + Policies)

---

## 🎯 功能迭代历程

### v1.0 - 基础版本 (Initial)
- ✅ 基础日志解析和提取
- ✅ Harness 核心系统 (StateManager, ContextEngine, Orchestrator)
- ✅ 基础技能：LogExtractionSkill, BugAnalysisSkill, ReportGenerationSkill

### v2.0 - LLM 集成增强 (LLM Integration)
- ✅ Bug 描述解析和关键词提取
- ✅ 日志智能过滤
- ✅ 异常分类
- ✅ 模式匹配

### v3.0 - 证据匹配和时间线 (Evidence Matching)
- ✅ 用户描述与日志证据匹配
- ✅ 时间轴重构
- ✅ 置信度评分提升

### v4.0 - aloggrep 集成 (aloggrep Integration)
- ✅ aloggrep 命令包装
- ✅ 四阶段分析工作流
- ✅ 异常检测和模式识别
- ✅ Claude Skill 集成

### v5.0 - QMD 知识库 (Knowledge Base)
- ✅ Android 知识文档库
- ✅ Event Log Tags 完整定义
- ✅ ANR/Tombstone 格式说明
- ✅ dumpsys SOP 指南
- ✅ GC 日志解析
- ✅ 系统属性定义

### v6.0 - Feature Flag 管控 (Feature Management)
- ✅ Feature Flag 核心引擎
- ✅ 环境隔离
- ✅ 灰度发布
- ✅ 目标规则
- ✅ 命令行管理工具 (ffctl)
- ✅ Bug 类型差异化分析

### v7.0 - 记忆系统 (Memory System)
- ✅ Simple 模式 - 本地 JSON 存储，零依赖
- ✅ OpenViking 模式 - 增强版，支持向量检索
- ✅ CaseLibrarySkill - 案例库 CRUD
- ✅ 索引缓存机制
- ✅ 自动案例保存和检索
- ✅ 增强报告生成

### v8.0 - 统一 CLI + 分阶段执行 (Unified CLI)
- ✅ 统一 CLI 入口 `scripts/cli.py`
- ✅ 9 个子命令：full/plan/build/verify/fix/resume/skill/status/list
- ✅ 分阶段独立执行
- ✅ 断点恢复 (resume)
- ✅ 独立技能执行 (execute_skill)
- ✅ StateManager 脏标记 + 延迟写入
- ✅ StateManager.load_state() 公开方法

---

## 📁 项目架构

### 整体架构图
```
┌─────────────────────────────────────────────────────────────────┐
│                     Harness Engineering                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Harness Core                           │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐          │  │
│  │  │StateManager│ │ContextEng. │ │Orchestrator│          │  │
│  │  │(脏标记+延迟)│ │            │ │(分阶段API) │          │  │
│  │  └────────────┘ └────────────┘ └────────────┘          │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐          │  │
│  │  │FeatureFlag │ │ Analytics  │ │  Logging   │          │  │
│  │  │  Engine    │ │ Collector  │ │  Manager   │          │  │
│  │  └────────────┘ └────────────┘ └────────────┘          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Skills Layer                            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                           │  │
│  │  v1.0 - 基础技能:          v2.0 - LLM增强:             │  │
│  │  ┌────────────┐            ┌─────────────────┐        │  │
│  │  │LogExtraction│            │LLMAnalysisSkill │        │  │
│  │  │BugAnalysis │            │LLMEnhancedSkill │        │  │
│  │  │ReportGen.  │            └─────────────────┘        │  │
│  │  └────────────┘                                        │  │
│  │                                                           │  │
│  │  v3.0 - 证据匹配:          v4.0 - aloggrep:           │  │
│  │  ┌─────────────────┐      ┌─────────────────┐          │  │
│  │  │LogEvidenceMatcher│      │AloggrepWorkflow │          │  │
│  │  │TimelineBuilder  │      └─────────────────┘          │  │
│  │  └─────────────────┘                                    │  │
│  │                                                           │  │
│  │  v5.0 - 知识库:            v6.0 - 特性管控:           │  │
│  │  ┌─────────────────┐      ┌─────────────────┐          │  │
│  │  │KnowledgeRetrieval│      │BugTypeAnalysis  │          │  │
│  │  │ (QMD集成)       │      │(Flag驱动)       │          │  │
│  │  └─────────────────┘      └─────────────────┘          │  │
│  │                                                           │  │
│  │  v7.0 - 记忆系统:          v8.0 - 统一CLI:            │  │
│  │  ┌─────────────────┐      ┌─────────────────┐          │  │
│  │  │CaseLibrarySkill │      │ scripts/cli.py  │          │  │
│  │  │OpenVikingMemory │      │ 分阶段/恢复/技能 │          │  │
│  │  │EnhancedReport   │      └─────────────────┘          │  │
│  │  └─────────────────┘                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      Policies Layer                        │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │  │
│  │  │Validation│ │Quality   │ │Format    │                  │  │
│  │  └──────────┘ └──────────┘ └──────────┘                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   External Dependencies                   │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                  │  │
│  │  │  LLM API │ │  aloggrep│ │  QMD KB  │                  │  │
│  │  └──────────┘ └──────────┘ └──────────┘                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 核心文件结构

```
android-log-analyzer/
├── scripts/
│   ├── cli.py                          # 统一 CLI 入口 (v8.0+，推荐)
│   ├── harness_agent_advanced.py       # 高级 Agent 入口
│   └── ffctl.py                        # Feature Flag 管理工具
├── harness/
│   ├── core/
│   │   ├── state.py                    # StateManager (状态管理，脏标记+延迟写入)
│   │   ├── context.py                  # ContextEngine (上下文管理)
│   │   ├── orchestrator.py             # Orchestrator (工作流编排，分阶段API)
│   │   ├── feature_flags.py            # Feature Flag 引擎 (v6.0+)
│   │   ├── analytics.py                # 统计分析收集器
│   │   ├── logging.py                  # 统一日志系统
│   │   ├── config.py                   # 配置管理
│   │   ├── paths.py                    # 统一路径配置
│   │   ├── token_stats.py              # Token 统计
│   │   └── retry.py                    # 重试机制
│   ├── skills/
│   │   ├── base.py                     # BaseSkill + LLMBasedSkill (基类)
│   │   ├── log_extraction.py           # LogExtractionSkill (v1.0)
│   │   ├── log_analysis_advanced.py    # AdvancedLogAnalysisSkill (v3.0)
│   │   ├── llm_analysis.py             # LLMAnalysisSkill (v2.0)
│   │   ├── llm_enhanced.py             # LLM增强技能 (v2.0)
│   │   ├── log_evidence_matcher.py     # 证据匹配 + 时间线技能 (v3.0)
│   │   ├── report.py                   # ReportGenerationSkill (v1.0)
│   │   ├── enhanced_report_generation.py # 增强报告生成 (v7.0)
│   │   ├── case_library_skill.py       # 案例库技能 (v7.0)
│   │   ├── openviking_memory_skill.py  # OpenViking记忆技能 (v7.0)
│   │   ├── knowledge_retrieval.py      # 知识检索技能 (v5.0)
│   │   ├── bug_type_analysis_skill.py  # Bug类型分析技能 (v6.0)
│   │   ├── log_extraction_aloggrep.py  # aloggrep技能集 (v4.0)
│   │   ├── log_extraction_aloggrep_workflow.py # 四阶段工作流 (v4.0)
│   │   └── bug_type/                   # Bug类型差异化分析器 (v6.0)
│   │       ├── crash_analyzer.py
│   │       ├── anr_analyzer.py
│   │       ├── memory_analyzer.py
│   │       └── other_analyzers.py
│   ├── policies/
│   │   ├── base.py                     # 策略基类
│   │   ├── validation.py               # 验证策略
│   │   ├── quality.py                  # 质量策略
│   │   └── format.py                   # 格式策略
│   └── memory/
│       └── qmd_memory_manager.py       # QMD 知识库管理 (v5.0)
│
├── log_analyzer/
│   ├── agent.py
│   ├── parser/
│   ├── extractor/
│   ├── llm/
│   └── bugreport/
│
├── knowledge_base/                     # Android 知识库 (v5.0)
│   ├── android_knowledge/
│   └── config/
│
├── case_library/                       # 案例库数据 (v7.0，自动生成)
│
├── config/
│   ├── feature_flags.yaml              # Feature Flag 配置 (v6.0)
│   └── report_formats.yaml             # 报告格式配置
│
├── tests/                              # 测试目录
├── docs/                               # 文档目录
└── data/                               # 数据文件
```

---

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装依赖
pip install -r requirements.txt

# 可选：安装 aloggrep
cargo install aloggrep
```

### 2. 使用统一 CLI（v8.0+，推荐）
```bash
# 完整分析
python scripts/cli.py full --bug bug_description.txt --log log_file.txt --format markdown

# 分阶段执行
python scripts/cli.py plan --bug bug_description.txt --log log_file.txt
python scripts/cli.py build --workflow-id <ID>
python scripts/cli.py verify --workflow-id <ID>

# 从断点恢复
python scripts/cli.py resume --workflow-id <ID>

# 单独执行技能
python scripts/cli.py skill --list
python scripts/cli.py skill --name log_extraction --log log_file.txt

# 工作流管理
python scripts/cli.py list
python scripts/cli.py status --workflow-id <ID>
```

### 3. 使用高级 Agent（兼容旧方式）
```bash
python scripts/harness_agent_advanced.py \
    --bug bug_description.txt \
    --log log_file.txt \
    --format markdown
```

### 4. Feature Flag 管理
```bash
python scripts/ffctl.py list
python scripts/ffctl.py set aloggrep_integration --disable
python scripts/ffctl.py set llm_analysis_enabled --percentage 50
```

---

## 🔧 功能验证

### 运行测试
```bash
# 运行全部测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_state.py -v
pytest tests/test_orchestrator.py -v
pytest tests/test_cli.py -v
pytest tests/test_case_library.py -v
```

### 功能清单

| 迭代 | 功能 | 状态 |
|------|------|------|
| v1.0 | 基础日志解析 | ✅ |
| v1.0 | Harness Core 系统 | ✅ |
| v2.0 | LLM 分析集成 | ✅ |
| v3.0 | 证据匹配和时间线 | ✅ |
| v4.0 | aloggrep 集成 | ✅ |
| v5.0 | QMD 知识库 | ✅ |
| v6.0 | Feature Flag 管控 | ✅ |
| v6.0 | Bug 类型差异化分析 | ✅ |
| v7.0 | 记忆系统 (Simple/OpenViking) | ✅ |
| v7.0 | 增强报告生成 | ✅ |
| v8.0 | 统一 CLI 入口 | ✅ |
| v8.0 | 分阶段执行 + 断点恢复 | ✅ |
| v8.0 | StateManager 脏标记+延迟写入 | ✅ |

---

## 📊 版本更新记录

### v8.0 (2026-05-18) - 统一 CLI + 分阶段执行
- **新增**: 统一 CLI 入口 `scripts/cli.py`
- **新增**: 9 个子命令（full/plan/build/verify/fix/resume/skill/status/list）
- **新增**: Orchestrator 分阶段 API（plan/build/verify/fix/resume/execute_skill）
- **新增**: StateManager.load_state() 公开方法
- **优化**: StateManager 脏标记 + 延迟写入，减少磁盘 I/O
- **优化**: CaseLibrarySkill 索引缓存，避免重复加载
- **优化**: print() → logger 统一日志系统
- **优化**: 宽泛 except Exception → 具体异常类型

### v7.0 (2026-05-17) - 记忆系统
- **新增**: CaseLibrarySkill（Simple 模式）
- **新增**: OpenVikingMemorySkill（OpenViking 模式）
- **新增**: 增强报告生成
- **新增**: Feature Flag 完全控制记忆系统

### v6.0 (2026-05-17) - Feature Flag 管控
- **新增**: Feature Flag 核心引擎
- **新增**: Bug 类型差异化分析
- **新增**: ffctl 管理工具

### v5.0 (2026-05-17) - QMD 知识库集成
- **新增**: Android 知识文档库
- **新增**: KnowledgeRetrievalSkill

### v4.0 (2026-05-17) - aloggrep 深度集成
- **新增**: aloggrep 命令包装
- **新增**: 四阶段分析工作流

### v3.0 (2026-05-17) - 证据匹配和时间线
- **新增**: LogEvidenceMatcherSkill
- **新增**: TimelineBuilderSkill

### v2.0 (2026-05-17) - LLM 集成增强
- **新增**: BugDescriptionParserSkill
- **新增**: LLMAnalysisSkill

### v1.0 (2026-05-16) - 基础版本
- **新增**: Harness Core 系统
- **新增**: 基础技能集合

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| [AGENTS.md](AGENTS.md) | 核心架构导航 |
| [CHANGELOG.md](CHANGELOG.md) | 变更记录 |
| [README_HARNESS.md](README_HARNESS.md) | Harness 架构说明 |
| [MEMORY_SYSTEM_GUIDE.md](MEMORY_SYSTEM_GUIDE.md) | 记忆系统指南 |
| [ALOGGREP_INTEGRATION.md](ALOGGREP_INTEGRATION.md) | aloggrep 集成文档 |
| [QMD_INTEGRATION_SCHEME.md](QMD_INTEGRATION_SCHEME.md) | QMD 集成方案 |
| [LLM_INTEGRATION_PHASES.md](LLM_INTEGRATION_PHASES.md) | LLM 集成阶段 |

---

## 🎯 下一步规划

- [ ] 防僵化机制（Anti-rigidity）
- [ ] 案例质量评分
- [ ] 集成实际的 QMD 服务
- [ ] 性能优化和监控
- [ ] 持续迭代新特性（通过 Feature Flag）

---

## 📝 致谢

感谢 Harness Engineering 架构思想和 aloggrep 项目的启发！
