# Changelog

所有重要的变更都会记录在此文件中。

格式：基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)
项目版本：遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)

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
| 8.0.0 | 2026-05-18 | 统一 CLI 入口 + 分阶段执行 + 断点恢复 |
| 7.0.0 | 2026-05-17 | 记忆系统（Simple/OpenViking）双模集成 |
| 6.0.0 | 2026-05-17 | Feature Flag 管控系统 |
| 5.0.0 | 2026-05-17 | QMD 知识库集成 |
| 4.0.0 | 2026-05-17 | aloggrep 深度集成 |
| 3.0.0 | 2026-05-17 | 证据匹配和时间线 |
| 2.0.0 | 2026-05-17 | LLM 集成增强 |
| 1.0.0 | 2026-05-16 | 初始版本 |
