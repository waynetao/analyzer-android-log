# Android 日志分析 Agent - Harness Engineering 规范
# 此文档是给AI Agent的核心导航地图，不是百科全书
# 版本：v8.0.0
## 1. 项目架构概览
```
android-log-analyzer/
├── scripts/                # 脚本入口
│   ├── cli.py             # 统一 CLI 入口 (v8.0+)
│   ├── harness_agent_advanced.py  # 高级 Agent 入口
│   └── ffctl.py           # Feature Flag 管理工具
├── harness/               # Harness系统核心
│   ├── core/              # 核心引擎层
│   │   ├── orchestrator.py    # Orchestrator 协调器
│   │   ├── state.py           # StateManager 状态管理 (脏标记+延迟写入)
│   │   ├── context.py         # ContextEngine 上下文引擎
│   │   ├── feature_flags.py   # Feature Flag 引擎 (v6.0+)
│   │   ├── analytics.py       # 统计分析收集器
│   │   ├── logging.py         # 统一日志系统
│   │   ├── config.py          # 配置管理
│   │   ├── paths.py           # 统一路径配置
│   │   ├── token_stats.py     # Token 统计
│   │   └── retry.py           # 重试机制
│   ├── skills/            # 技能层（可插拔）
│   │   ├── base.py            # BaseSkill 基类 + LLMBasedSkill
│   │   ├── log_extraction.py  # LogExtractionSkill
│   │   ├── log_analysis_advanced.py  # AdvancedLogAnalysisSkill
│   │   ├── llm_analysis.py    # LLMAnalysisSkill
│   │   ├── llm_enhanced.py    # LLM增强技能
│   │   ├── log_evidence_matcher.py  # LogEvidenceMatcherSkill + TimelineBuilderSkill
│   │   ├── report.py          # ReportGenerationSkill
│   │   ├── enhanced_report_generation.py  # EnhancedReportGenerationSkill (v7.0+)
│   │   ├── case_library_skill.py  # CaseLibrarySkill (v7.0+)
│   │   ├── openviking_memory_skill.py  # OpenVikingMemorySkill (v7.0+)
│   │   ├── knowledge_retrieval.py  # KnowledgeRetrievalSkill (v5.0+)
│   │   ├── bug_type_analysis_skill.py  # BugTypeAnalysisSkill (v6.0+)
│   │   ├── log_extraction_aloggrep.py  # aloggrep 技能集 (v4.0+)
│   │   ├── log_extraction_aloggrep_workflow.py  # 四阶段工作流 (v4.0+)
│   │   └── bug_type/          # Bug 类型差异化分析器
│   │       ├── crash_analyzer.py
│   │       ├── anr_analyzer.py
│   │       ├── memory_analyzer.py
│   │       └── other_analyzers.py
│   ├── policies/          # 策略层（约束和验证）
│   │   ├── base.py            # BasePolicy 基类
│   │   ├── validation.py      # ValidationPolicy
│   │   ├── quality.py         # QualityPolicy
│   │   └── format.py          # FormatPolicy
│   └── memory/            # 记忆层
│       └── qmd_memory_manager.py  # QMD 知识库管理 (v5.0+)
├── log_analyzer/          # 原始分析模块
│   ├── agent.py
│   ├── parser/
│   ├── extractor/
│   ├── llm/
│   └── bugreport/
├── config/                # 配置文件
│   ├── feature_flags.yaml     # Feature Flag 配置
│   └── report_formats.yaml    # 报告格式配置
├── knowledge_base/        # 知识库 (v5.0+)
├── case_library/          # 案例库数据 (v7.0+)
├── tests/                 # 测试目录
└── docs/                  # 文档目录
```
## 2. 核心工作流程（Harness 三层架构）
### 2.1 Core层（不可变核心）
- `Orchestrator（协调器）：`harness/core/orchestrator.py`
  - 完整工作流：`execute_workflow()`
  - 分阶段执行：`plan()` / `build()` / `verify()` / `fix()` (v8.0+)
  - 恢复执行：`resume()` (v8.0+)
  - 独立技能：`execute_skill()` (v8.0+)
  - 工作流管理：`load_workflow()` / `list_workflows()` (v8.0+)
- `StateManager（状态管理）：`harness/core/state.py`
  - 脏标记 + 延迟写入机制：`_mark_dirty()` / `flush()` / `_do_save()`
  - 加载已保存状态：`load_state()` (v8.0+)
- `ContextEngine（上下文引擎）：`harness/core/context.py`
- `Feature Flag 引擎：`harness/core/feature_flags.py` (v6.0+)
- `统一日志系统：`harness/core/logging.py`
- `统计分析：`harness/core/analytics.py`

### 2.2 Skills层（可插拔技能）
- `LogExtractionSkill（日志提取）：`harness/skills/log_extraction.py`
- `AdvancedLogAnalysisSkill（高级日志分析）：`harness/skills/log_analysis_advanced.py`
- `LLMAnalysisSkill（LLM智能分析）：`harness/skills/llm_analysis.py`
- `LogEvidenceMatcherSkill（日志证据匹配）：`harness/skills/log_evidence_matcher.py`
- `TimelineBuilderSkill（时间线构建）：`harness/skills/log_evidence_matcher.py`
- `ReportGenerationSkill（报告生成）：`harness/skills/report.py`
- `CaseLibrarySkill（案例库）：`harness/skills/case_library_skill.py` (v7.0+)
- `BugTypeAnalysisSkill（Bug类型分析）：`harness/skills/bug_type_analysis_skill.py` (v6.0+)
- `KnowledgeRetrievalSkill（知识检索）：`harness/skills/knowledge_retrieval.py` (v5.0+)
- `OpenVikingMemorySkill（OpenViking记忆）：`harness/skills/openviking_memory_skill.py` (v7.0+)
- `EnhancedReportGenerationSkill（增强报告）：`harness/skills/enhanced_report_generation.py` (v7.0+)
- `AloggrepWorkflowSkill（aloggrep工作流）：`harness/skills/log_extraction_aloggrep_workflow.py` (v4.0+)

### 2.3 Policies层（策略和约束）
- `ValidationPolicy（验证策略）：`harness/policies/validation.py`
- `QualityPolicy（质量策略）：`harness/policies/quality.py`
- `FormatPolicy（格式策略）：`harness/policies/format.py`

## 3. 强制自验证循环
所有执行Plan-Build-Verify-Fix工作流：
1. PLAN：明确任务和检查清单
2. BUILD：执行任务
3. VERIFY：对照验证点检查
4. FIX：修复失败的验证

支持分阶段独立执行和断点恢复（v8.0+）：
```bash
python scripts/cli.py plan --bug bug.txt --log test.log
python scripts/cli.py build --workflow-id <ID>
python scripts/cli.py verify --workflow-id <ID>
python scripts/cli.py resume --workflow-id <ID>
```

## 4. 约束规则（架构约束）

### 4.1 模块化原则
- 每一层只能依赖左边层（Skills → Core）
- Skills通过接口通信
- Skills必须有统一的Skill接口

### 4.2 命名约定
- 技能类：XXXSkill（后缀Skill）
- 策略类：XXXPolicy
- 工作流：workflow_xxx
- 配置文件：*.yaml

### 4.3 验证检查点清单
1. 输入验证
2. 日志解析验证
3. 分析结果验证
4. 报告格式验证
5. 输出验证

## 5. 场景化分析报告配置
参见：`config/report_formats.yaml`
支持格式：
- Markdown (default)
- HTML
- JSON
- PDF (via HTML)

## 6. 默认输出目录
- bug分析输出：`outputs/bug_analysis/`
- 报告输出：`outputs/reports/`
- 中间状态：`outputs/state/`

## 7. Feature Flag 控制 (v6.0+)
参见：`config/feature_flags.yaml`
核心 Flags：
- `aloggrep_integration` - aloggrep 集成开关
- `llm_analysis_enabled` - LLM 分析开关
- `evidence_matching_enabled` - 证据匹配开关
- `knowledge_base_enabled` - 知识库检索开关
- `bug_type_optimization_enabled` - Bug类型差异化开关
- `memory_system_enabled` - 记忆系统总开关
- `memory_mode` - 记忆模式：simple/openviking
- `auto_save_cases` - 自动保存案例
- `similar_case_retrieval` - 相似案例检索
- `analysis_mode` - 分析模式：fast/standard/deep

## 8. 版本历史
- v8.0.0 - 统一 CLI 入口 + 分阶段执行 + 断点恢复
- v7.0.0 - 记忆系统（Simple/OpenViking 双模）
- v6.0.0 - Feature Flag 管控系统
- v5.0.0 - QMD 知识库集成
- v4.0.0 - aloggrep 深度集成
- v3.0.0 - 证据匹配和时间线
- v2.0.0 - LLM 集成增强
- v1.0.0 - 初始 Harness Engineering 架构实现
