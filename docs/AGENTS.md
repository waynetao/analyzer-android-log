# Android 日志分析 Agent - Harness Engineering 规范
# 此文档是给AI Agent的核心导航地图，不是百科全书
# 版本：v2.0.0
## 1. 项目架构概览
```
/workspace/
├── docs/                    # 架构规范文档
├── harness/                # Harness系统核心
│   ├── core/            # 核心引擎层
│   ├── skills/          # 技能层（可插拔）
│   ├── policies/       # 策略层（约束和验证）
│   └── workflows/    # 工作流定义
├── config/              # 配置文件
└── outputs/           # 输出目录
```
## 2. 核心工作流程（Harness 三层架构
### 2.1 Core层（不可变核心
- `Orchestrator（协调器）：`harness/core/orchestrator.py`
- `StateManager（状态管理）：`harness/core/state.py`
- `ContextEngine（上下文引擎）：`harness/core/context.py`

### 2.2 Skills层（可插拔技能）
- `LogExtractionSkill（日志提取）：`harness/skills/log_extraction.py`
- `AdvancedLogAnalysisSkill（高级日志分析）：`harness/skills/log_analysis_advanced.py`
- `LLMAnalysisSkill（LLM智能分析）：`harness/skills/llm_analysis.py`
- `LogEvidenceMatcherSkill（日志证据匹配）：`harness/skills/log_evidence_matcher.py` (新!)
- `TimelineBuilderSkill（时间线构建）：`harness/skills/log_evidence_matcher.py` (新!)
- `ReportGenerationSkill（报告生成）：`harness/skills/report.py`

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
## 4. 约束规则（架构约束）

## 4.1 模块化原则
- 每一层只能依赖左边层（Skills → 核心
- Skills通过接口通信
- Skills必须有统一的Skill接口
- 4.2 命名约定

## 4.2 命名约定
- 技能类：XXXSkill（后缀Skill
- 策略类：XXXPolicy
- 工作流：workflow_xxx
- 配置文件：*.yaml
- 接口定义：

## 4.3 验证检查点清单
1. 输入验证
2. 日志解析验证
3. 分析结果验证
4. 报告格式验证
5. 输出验证

## 5. 场景化分析报告配置
参见：`/config/report_formats.yaml`
支持格式：
- Markdown (default)
- HTML
- JSON
- PDF (via HTML)
## 6. 默认输出目录
- bug分析输出：`/outputs/bug_analysis/`
- 报告输出：`/outputs/reports/`
- 中间状态：`/outputs/state/`
## 7. 工作流程（可插拔工作流定义
工作流位于：`/harness/workflows/`
- `bug_analysis.yaml - 标准问题分析流程
- `bug_analysis_advanced.yaml - 高级分析流程（含证据匹配
- `scenario_qa.yaml - 场景化问答流程
- `deep_dive.yaml - 深度分析流程

## 8. 版本历史
- v2.0.0 - 新增日志证据匹配和时间线构建功能
- v1.0.0 - 初始Harness Engineering架构实现
