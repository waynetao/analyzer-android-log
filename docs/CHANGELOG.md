# Changelog

所有重要的变更都会记录在此文件中。

格式：基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)
项目版本：遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)

---

## [9.1.0] - 2026-05-19

### 修复

- 🔧 **outputs 根目录冗余空目录清理**
  - `ensure_dirs()` 不再预创建 `reports/`、`state/`、`temp/`、`analytics/` 全局目录
  - 全局目录仅保留真正跨 workflow 共享的 4 个：`index/`、`case_library/`、`openviking_data/`、`logs/`
  - Legacy 全局常量（`OUTPUTS_REPORTS_DIR` 等）保留做兼容回退，标记为 Legacy

- 🔧 **per-workflow 产物路径全面对齐**
  - `token_stats.py` 新增 `set_workflow_dir()` 方法，Token 统计保存到 `workflows/{id}/analytics/`
  - `analytics.py` 的 `end_workflow()` 自动调用 `token_stats.set_workflow_dir()`
  - `enhanced_report_generation.py` 支持 `workflow_id` 参数，报告输出到 `workflows/{id}/reports/`
  - `llm_client.py` 使用 `WorkflowPaths.llm_interactions_dir_str` 替代手动拼接路径

- 🔧 **WorkflowPaths 新增 `llm_interactions_dir`**
  - 每个工作流独立的 LLM 交互日志目录 `workflows/{id}/llm_interactions/`
  - `ensure_dirs()` 自动创建该目录
  - 新增 `llm_interactions_dir_str` 便捷属性

- 🔧 **CLI 脚本路径信息更新**
  - `cli.py`、`harness_agent.py`、`harness_agent_advanced.py` 移除旧全局路径导入
  - 报告保存路径提示更新为 `workflows/{id}/reports/`

### 测试

- ✅ 新增 6 个测试（总计 69 个 v9 优化测试，271 个全量测试全部通过）
  - `test_llm_interactions_dir_exists` - LLM 交互日志目录创建
  - `test_ensure_dirs_no_legacy_global_dirs` - 确保不再创建 legacy 全局目录
  - `test_set_workflow_dir` - TokenStats workflow 目录切换
  - `test_set_workflow_dir_saves_to_correct_path` - TokenStats 保存到正确路径
  - `test_enhanced_report_with_workflow_id` - 增强报告 workflow_id 支持
  - `test_enhanced_report_without_workflow_id` - 增强报告无 workflow_id 回退

### 文档

- 📚 更新 `CHANGELOG.md` - v9.1.0 变更记录

---

## [9.0.0] - 2026-05-19

### 新增

- ✨ **基于 Workflow ID 的产物统一管理**
  - `WorkflowPaths` 类 - 为每个工作流创建独立的目录结构
  - `temp/` - 临时文件目录，可清理
  - `logs/` - 工作流专属日志
  - `reports/` - 生成的报告
  - `artifacts/` - 其他产物
  - `StateManager` 集成 - 自动初始化和清理

- ✨ **工作流元数据索引系统**
  - `WorkflowMetadata` dataclass - 完整的工作流元数据
  - `WorkflowIndex` 类 - 索引管理器
  - 支持注册、更新、查询、搜索、删除工作流
  - 支持按状态过滤 (running/completed/failed)
  - 支持按关键词搜索 (bug_description/bug_summary)
  - 自动清理 30 天前的旧工作流
  - `workflow_index.json` - 持久化索引文件

- ✨ **多轮深度分析功能**
  - `MultiRoundAnalysisSkill` - 全新的多轮分析技能
  - **第一轮 - 全景扫描** - 快速定位问题类型和范围
  - **第二轮 - 深度挖掘** - 深入验证假设，构建证据链
  - **第三轮 - 验证优化** - 验证结论，提供最佳修复方案
  - 支持 `analysis_mode = "multi_round"` Feature Flag
  - 报告生成集成 - 自动识别多轮分析结果并格式化展示
  - 模拟模式支持 - 无真实 LLM 时也能运行

- ✨ **额外发现功能**
  - `LogEvidenceMatcherSkill` 增强 - 支持区分匹配结果和额外发现
  - 报告生成增强 - 单独展示额外发现章节
  - 橙色警告样式 - 明确区分与主问题的关系
  - 描述文案 - 清楚说明这是与用户描述可能不相关的发现

### 增强

- 🚀 **Token 限制翻倍**
  - LLM 默认 max_tokens 从 2000 → 4000
  - 多轮分析各轮: 第一轮 8000, 第二轮 12000, 第三轮 8000
  - 为 Claude、Gemini 等大模型预留足够空间进行详细分析

- 🚀 **CLI 增强**
  - `list` 命令支持 `--detailed` 显示详细工作流信息
  - `search` 命令 - 按关键词搜索工作流
  - `info` 命令 - 查看单个工作流的完整详情

- 🚀 **StateManager 增强**
  - `initialize_workflow()` 新增参数: bug_description, bug_summary, log_path, output_format, analysis_mode
  - `workflow_index` 属性 - 访问工作流索引
  - `workflow_paths` 属性 - 访问当前工作流的路径管理
  - `cleanup_workflow()` - 清理当前工作流的临时文件
  - `transition_stage()` 自动更新工作流索引状态

- 🚀 **LLMAnalysisSkill 增强**
  - 识别 `analysis_mode` 参数
  - 自动调用 `MultiRoundAnalysisSkill` 进行多轮分析
  - 保持向后兼容 - standard/deep 模式仍使用原有单轮分析

### 修复

- 🔧 **修复重复方法** - 移除 StateManager 中重复的 load_state() 定义

### 测试

- ✅ `test_workflow_enhancements.py` - 新功能完整测试套件
  - `TestWorkflowMetadata` - 元数据创建测试
  - `TestWorkflowIndex` - 索引管理器完整测试
  - `TestWorkflowPaths` - 路径管理器测试
  - `TestStateManagerEnhanced` - 增强的状态管理测试
  - `TestMultiRoundAnalysis` - 多轮分析测试
  - `TestAdditionalFindings` - 额外发现功能测试
  - `TestReportWithAdditionalFindings` - 报告集成测试
- ✅ 所有现有测试通过 (test_state.py, test_health_check.py)
- ✅ 完整的模拟模式支持 - 不需要真实 LLM 即可测试

### 文档

- 📚 更新 `CHANGELOG.md` - 完整的变更记录
- 📚 更新 `README.md` - 新功能介绍
- 📚 `tests/test_workflow_enhancements.py` 包含完整的使用示例

---

## [8.0.0] - 2026-05-18

### 新增

- ✨ **统一 CLI 入口** - `scripts/cli.py`
  - 9 个子命令：`full` `plan` `build` `verify` `fix` `resume` `skill` `status` `list`
  - 所有命令复用 `UnifiedAgent`，统一初始化和日志
  - argparse subparser 模式，每命令独立 handler 函数
  - 完整的帮助信息和示例

- ✨ **Pipeline 分阶段执行**
  - Orchestrator 暴露公开方法：`plan()` `build()` `verify()` `fix()`
  - 从保存的状态恢复执行：`load_workflow()` `resume()`
  - 独立技能执行：`execute_skill(skill_name, inputs)`
  - 工作流列表：`list_workflows()` `get_current_state()`

- ✨ **Orchestrator API 扩展**
  - `load_workflow(workflow_id)` - 从 JSON 文件加载状态
  - `plan/build/verify/fix()` - 分阶段独立执行
  - `resume()` - 从当前检查点恢复并继续到完成
  - `execute_skill()` - 单独执行任意注册技能
  - `list_workflows()` - 列出所有已保存的工作流

- ✨ **StateManager 封装增强**
  - 新增 `load_state(workflow_id)` 公开方法，消除后门访问
  - 保持现有 `initialize_workflow` / `update_context` / `update_output` 等接口

### 重构

- 🔥 **CLI 代码结构优化**
  - `main()` 从 90 行 if-elif 链重构为 handler 函数字典
  - 每命令添加独立 subparser 函数（`_add_*_subparser`）
  - 每命令添加独立 handler 函数（`_handle_*`）
  - 清理冗余参数：build/verify/fix/resume 只保留 `--workflow-id`
  - `plan` 命令新增 `--format` 参数，与 `full` 接口一致

- 🔥 **Orchestrator 封装优化**
  - 移除 `_load_state()` 私有方法（职责迁移到 StateManager）
  - 移除 `json` 导入（不再自行加载 JSON）
  - `load_workflow()` 委托给 `StateManager.load_state()`

### 测试

- ✅ 所有 139 个测试通过
- ✅ 139 passed, 62 warnings（仅 pytest return-not-none 警告）

---

## [7.0.0] - 2026-05-17

### 新增
- ✨ **记忆系统（Memory System）** - 双模记忆系统
  - **Simple 模式** - 本地 JSON 存储，零依赖，即开即用
    - CaseLibrarySkill 实现
    - L0/L1/L2 层级摘要支持
    - 标签系统和相似案例搜索
    - 统计功能
  - **OpenViking 模式** - 增强版（可选）
    - OpenVikingMemorySkill 实现
    - 自动降级机制
    - OpenViking 配置模板
  - **Feature Flag 完全控制**
    - memory_system_enabled - 总开关
    - memory_mode - simple/openviking 切换
    - auto_save_cases - 自动保存
    - similar_case_retrieval - 相似案例搜索
    - anti_rigidity_enabled - 防僵化（待实现）

### 增强
- 🚀 **harness_agent_advanced.py 深度集成**
  - 记忆系统自动初始化
  - 分析前自动搜索相似案例
  - 分析后自动保存案例
  - --list-cases 命令行选项
  - --memory-mode 强制模式选择
  - 完整的 Feature Flag 集成和状态显示

- 🚀 **增强 CaseLibrarySkill**
  - 完整的 CRUD 操作
  - 完善的错误处理和边界情况
  - 数据持久化保证
  - 统计和元数据管理

### 测试
- ✅ test_case_library_advanced.py - CaseLibrarySkill 完整测试套件
- ✅ test_feature_flags_advanced.py - Feature Flag 引擎完整测试
- ✅ test_core_integration.py - 核心组件综合测试
- ✅ test_memory_integration.py - 记忆系统集成测试（与 test_memory_system.py 重复）
- ✅ 所有测试覆盖率 > 90%，全面通过

### 文档
- 📚 MEMORY_SYSTEM_GUIDE.md - 记忆系统完整使用指南
- 📚 OPENVIIKING_INTEGRATION_PLAN.md - OpenViking 集成方案
- 📚 openviking_config_template.json - OpenViking 配置模板

---

## [6.0.0] - 2026-05-17

### 新增
- ✨ **Feature Flag 管控系统** - 完整的特性开关机制
  - Feature Flag Engine 核心引擎
  - Feature SDK 简化接入
  - ffctl.py 命令行管理工具
  - config/feature_flags.yaml 配置文件
  - 支持 Boolean/Multivariate/Dynamic Config 类型
  - 支持环境隔离
  - 支持百分比灰度发布
  - 支持目标规则匹配

### 变更
- 🔧 更新 `harness_agent_advanced.py` 集成 Feature Flag
  - 添加条件技能注册
  - 支持分析模式选择 (fast/standard/deep)
  - 启动时显示 Feature Flag 状态

### 文档
- 📚 新增 `PROJECT_SUMMARY.md` 项目总结文档
- 📚 新增 `test_full_validation.py` 全面功能验证
- 📚 更新所有相关文档

### 测试
- ✅ test_feature_flags.py - Feature Flag 测试
- ✅ test_full_validation.py - 全面功能验证

---

## [5.0.0] - 2026-05-17

### 新增
- ✨ **QMD 知识库集成**
  - knowledge_base/ 目录结构
  - Event Log Tags 完整定义
  - ANR/Tombstone 格式说明
  - dumpsys 关键服务 SOP 文档
  - 系统属性关键项定义
  - GC 日志格式说明
  - QMDMemoryManager 知识库管理
  - KnowledgeRetrievalSkill 知识检索技能

### 文档
- 📚 QMD_INTEGRATION_SCHEME.md - 集成方案
- 📚 QMD_IMPACT_EVALUATION.md - 价值评估
- 📚 test_qmd_integration.py - 集成测试

---

## [4.0.0] - 2026-05-17

### 新增
- ✨ **aloggrep 深度集成**
  - ALogGrep 基础包装器
  - ALogGrepEnhanced 增强版
  - LogExtractionWithAloggrepSkill
  - ALogGrepAnalysisSkill
  - ALogGrepFilterSkill
  - AloggrepWorkflowSkill - 四阶段工作流
  - AloggrepQuickAnalysisSkill
  - Claude Skill 集成 (.claude/skills/)
  - docker-compose.yaml 部署配置

### 文档
- 📚 ALOGGREP_INTEGRATION.md - aloggrep 集成文档
- 📚 test_aloggrep_deep_integration.py - 深度集成测试
- 📚 test_aloggrep_integration.py - 基础集成测试

---

## [3.0.0] - 2026-05-17

### 新增
- ✨ **证据匹配和时间线系统**
  - LogEvidenceMatcherSkill - 日志证据匹配
  - TimelineBuilderSkill - 时间轴重构
  - 置信度评分系统
  - 场景变化识别
  - 事件时间序列重建

### 增强
- 🚀 报告生成 - 增强证据展示

### 文档
- 📚 REVIEW_REPORT.md - Code Review 报告
- 📚 test_evidence_matching.py - 证据匹配测试

---

## [2.0.0] - 2026-05-17

### 新增
- ✨ **LLM 集成增强**
  - BugDescriptionParserSkill - Bug 描述解析
  - LogFilterSkill - 智能日志过滤
  - ExceptionClassifierSkill - 异常分类
  - PromptMatcherSkill - 模式匹配
  - LLMAnalysisSkill - 完整的 LLM 分析

### 增强
- 🚀 多阶段 LLM 集成，提升分析质量

### 文档
- 📚 LLM_INTEGRATION_PHASES.md - LLM 集成阶段说明
- 📚 HIGH_QUALITY_ANALYSIS_GUIDE.md - 高质量分析指南

---

## [1.0.0] - 2026-05-16

### 新增
- ✨ **Harness Engineering 核心系统**
  - StateManager - 状态管理
  - ContextEngine - 上下文管理
  - Orchestrator - 工作流编排

- ✨ **基础技能层**
  - LogExtractionSkill - 日志提取
  - BugAnalysisSkill - Bug 分析
  - ReportGenerationSkill - 报告生成 (Markdown/HTML/JSON)

- ✨ **策略层**
  - ValidationPolicy - 验证策略
  - QualityPolicy - 质量策略
  - FormatPolicy - 格式策略

### 文档
- 📚 README.md - 项目说明
- 📚 AGENTS.md - 架构文档
- 📚 README_HARNESS.md - Harness 介绍

---

## 版本历史摘要

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| 9.1.0 | 2026-05-19 | outputs 目录清理 + per-workflow 产物路径对齐 |
| 9.0.0 | 2026-05-19 | 多轮分析 + 工作流索引 + 产物管理 |
| 8.0.0 | 2026-05-18 | 统一 CLI 入口 + 分阶段执行 + 断点恢复 |
| 7.0.0 | 2026-05-17 | 记忆系统（Simple/OpenViking）双模集成 |
| 6.0.0 | 2026-05-17 | Feature Flag 管控系统 |
| 5.0.0 | 2026-05-17 | QMD 知识库集成 |
| 4.0.0 | 2026-05-17 | aloggrep 深度集成 |
| 3.0.0 | 2026-05-17 | 证据匹配和时间线 |
| 2.0.0 | 2026-05-17 | LLM 集成增强 |
| 1.0.0 | 2026-05-16 | 初始版本 |
