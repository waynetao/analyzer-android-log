# Android 日志分析 AI Agent - Harness Engineering 架构

## 🚀 概述

这是一个完全符合 **OpenAI Harness Engineering** 最佳实践的 Android 日志分析 AI Agent。它实现了完整的 **Plan-Build-Verify-Fix** 工作流，采用可插拔的三层架构，支持多种输出格式的场景化报告，并集成了 LLM 多阶段智能分析和日志证据匹配功能。

## 📋 核心特性

### 🏗️ Harness 架构

- **Core Layer**: StateManager (脏标记+延迟写入), ContextEngine, Orchestrator (分阶段API), FeatureFlags, Analytics, Logging - 不变的核心系统
- **Skills Layer**: LogExtraction, AdvancedAnalysis, LLMAnalysis, EvidenceMatching, Timeline, ReportGeneration, CaseLibrary, BugTypeAnalysis, KnowledgeRetrieval, OpenVikingMemory, EnhancedReport, AloggrepWorkflow - 可插拔的技能模块
- **Policies Layer**: Validation, Quality, Format - 约束和验证策略

### 🔄 Plan-Build-Verify-Fix 工作流

1. **Plan**: 验证输入，规划任务
2. **Build**: 执行技能链，处理数据
3. **Verify**: 应用策略检查输出
4. **Fix**: 自动修复（可扩展）

### 📊 多种报告格式

- Markdown (默认)
- HTML (响应式，带可视化)
- JSON (机器可读)

### 🎯 核心功能

- **日志证据匹配**: 置信度评分、用户现象与日志对照、场景变化追踪、事件时间线
- **记忆系统**: 案例库自动保存/检索，支持 Simple 和 OpenViking 双模
- **Bug 类型差异化**: 针对崩溃/ANR/内存/其他类型使用不同分析策略
- **Feature Flag 管控**: 条件技能注册、灰度发布、环境隔离
- **统一 CLI**: 分阶段执行、断点恢复、独立技能调用

## 📁 项目结构

```
android-log-analyzer/
├── scripts/                     # 脚本目录
│   ├── cli.py                   # 统一 CLI 入口（推荐） v8.0
│   ├── harness_agent_advanced.py # 高级版 Agent
│   └── ffctl.py                # Feature Flag 管理
├── harness/
│   ├── core/                  # 核心层
│   │   ├── context.py         # 上下文引擎
│   │   ├── state.py           # 状态管理（脏标记+延迟写入）
│   │   ├── orchestrator.py    # 协调器（分阶段API）
│   │   ├── feature_flags.py   # Feature Flag 引擎
│   │   ├── analytics.py       # 统计分析
│   │   └── logging.py         # 统一日志
│   ├── skills/                # 技能层
│   │   ├── base.py
│   │   ├── log_extraction.py
│   │   ├── log_analysis_advanced.py
│   │   ├── llm_analysis.py    # LLM智能分析
│   │   ├── llm_enhanced.py    # LLM增强
│   │   ├── log_evidence_matcher.py  # 证据匹配+时间线
│   │   ├── case_library_skill.py  # 案例库 v7.0
│   │   ├── openviking_memory_skill.py  # OpenViking v7.0
│   │   ├── knowledge_retrieval.py  # 知识检索 v5.0
│   │   ├── bug_type_analysis_skill.py  # Bug类型分析 v6.0
│   │   ├── enhanced_report_generation.py  # 增强报告 v7.0
│   │   ├── log_extraction_aloggrep_workflow.py  # aloggrep工作流 v4.0
│   │   ├── report.py          # 报告生成
│   │   └── bug_type/          # Bug类型分析器 v6.0
│   ├── policies/              # 策略层
│   │   ├── validation.py
│   │   ├── quality.py
│   │   └── format.py
│   └── memory/                # 记忆层
│       └── qmd_memory_manager.py  # QMD知识库 v5.0
├── log_analyzer/              # 原始分析模块
├── config/
│   ├── feature_flags.yaml     # Feature Flag 配置
│   └── report_formats.yaml    # 报告格式配置
├── knowledge_base/            # 知识库 v5.0
├── case_library/              # 案例库数据 v7.0
├── tests/                     # 测试目录
└── docs/                      # 文档目录
```

## 🎯 快速开始

### 安装依赖

```bash
pip install pyyaml
```

### 运行分析（推荐使用统一 CLI）

```bash
# 完整分析
python scripts/cli.py full --bug "应用崩溃" --log test_log.txt --format markdown

# 使用bug描述文件
python scripts/cli.py full --bug sample_bug.txt --log test_log.txt --format all

# 分阶段执行
python scripts/cli.py plan --bug sample_bug.txt --log test_log.txt
python scripts/cli.py build --workflow-id <ID>
python scripts/cli.py resume --workflow-id <ID>
```

### 使用高级版 Agent（兼容旧方式）

```bash
python scripts/harness_agent_advanced.py --bug sample_bug.txt --log test_log.txt --format all
```

### 统一 CLI（v8.0 新增，推荐）

```bash
# 完整分析
python scripts/cli.py full --bug sample_bug.txt --log test_log.txt --format markdown

# 分阶段执行
python scripts/cli.py plan --bug sample_bug.txt --log test_log.txt
python scripts/cli.py build --workflow-id <ID>
python scripts/cli.py verify --workflow-id <ID>

# 从断点恢复
python scripts/cli.py resume --workflow-id <ID>

# 单独执行技能
python scripts/cli.py skill --list
python scripts/cli.py skill --name log_extraction --log test_log.txt

# 工作流状态管理
python scripts/cli.py list
python scripts/cli.py status --workflow-id <ID>
```

### 测试日志证据匹配功能

```bash
# 运行证据匹配测试
python test_evidence_matching.py
```

## 📖 Harness Engineering 原则

### 1️⃣ 上下文工程 (Context Engineering)

- **地图而非百科全书**: AGENTS.md 作为导航
- **按需加载**: 相关信息仅在需要时获取
- **熵治理**: 限制状态大小，防止信息过载

### 2️⃣ 架构约束 (Architectural Constraints)

- **分层架构**: Core → Skills → Policies，单向依赖
- **可插拔**: 技能和策略可以独立替换
- **机械执行**: 约束通过代码强制实施

### 3️⃣ 自验证循环 (Self-Validation Loop)

- **Plan-Build-Verify-Fix**: 每个阶段都有检查
- **Policy-driven**: 验证由策略模块执行
- **可追踪**: 状态持久化，支持审计

## 🎓 扩展开发

### 添加新技能

```python
from harness.skills.base import BaseSkill, SkillResult

class MyNewSkill(BaseSkill):
    @property
    def name(self):
        return "my_new_skill"
    
    def execute(self, inputs):
        # 实现你的逻辑
        return SkillResult(True, {"data": "..."}, "成功")
```

### 添加新策略

```python
from harness.policies.base import BasePolicy, ValidationResult

class MyPolicy(BasePolicy):
    @property
    def name(self):
        return "my_policy"
    
    def validate_output(self, outputs):
        return ValidationResult(True, "通过")
```

## 📊 示例输出

### 高级版执行过程 (包含证据匹配)

```
============================================================
Android 日志分析 AI Agent - 高级版 (Harness Engineering)
============================================================
✅ 技能已注册: log_extraction
✅ 技能已注册: advanced_log_analysis
✅ 技能已注册: llm_analysis
✅ 技能已注册: log_evidence_matcher
✅ 技能已注册: timeline_builder
✅ 技能已注册: report_generation
📋 策略已加载: validation
📋 策略已加载: quality
📋 策略已加载: format

📝 解析bug描述...

🚀 启动Harness工作流...

🚀 开始执行工作流: bug_analysis_advanced
   工作流ID: bug_analysis_20260516_205300_ca1b4529

📋 === 阶段 1/4: PLAN (规划) ===
   ✓ 输入验证完成

🔨 === 阶段 2/4: BUILD (构建) ===

   执行技能: log_extraction
   ✓ 技能 log_extraction 执行完成: 成功提取并解析 59 条日志

   执行技能: advanced_log_analysis
   ✓ 技能 advanced_log_analysis 执行完成: 高级分析完成: 提取了 5 条关键日志

   执行技能: llm_analysis
   ✓ 技能 llm_analysis 执行完成: LLM分析完成

   执行技能: log_evidence_matcher
   ✓ 技能 log_evidence_matcher 执行完成: 日志证据匹配完成，置信度 92%

   执行技能: timeline_builder
   ✓ 技能 timeline_builder 执行完成: 时间线构建完成

   执行技能: report_generation
   ✓ 技能 report_generation 执行完成: 成功生成报告: ...

🔍 === 阶段 3/4: VERIFY (验证) ===
   ✅ validation: 输出验证通过
   ✅ quality: 发现 25 个问题，建议优先修复
   ✅ format: 格式验证通过

✅ 工作流执行成功!
```

## 📝 参考资料

- OpenAI Harness Engineering 官方博客
- Anthropic Effective Harnesses for Long-Running Agents
- Martin Fowler on AI Engineering Practices

## 📄 许可证

MIT License
