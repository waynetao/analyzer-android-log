# v9.0 新功能指南

## 📋 概述

v9.0 版本引入了三大核心功能：
1. **多轮 LLM 深度分析** - 突破 Token 限制，进行三轮递进式分析
2. **Workflow ID 统一产物管理** - 所有输出文件按工作流 ID 统一组织
3. **Additional Findings 额外发现标注** - 明确区分主 Bug 和额外发现

---

## 🔄 多轮 LLM 深度分析

### 工作原理

采用三轮递进式分析策略，每轮专注不同分析深度：

#### 第一轮：全景扫描 (Broad Scan)
- **Token 限制**: 8000
- **目标**: 快速建立日志全景视图
- **输出**: 关键异常点标记、时间线概览、初步分类

#### 第二轮：深度分析 (Deep Dive)
- **Token 限制**: 12000
- **目标**: 对关键异常进行深入根因分析
- **输出**: 详细根因、相关证据链、修复建议

#### 第三轮：验证优化 (Validation & Optimization)
- **Token 限制**: 8000
- **目标**: 验证分析结论，补充优化建议
- **输出**: 结论验证、优化方案、风险提示

### 使用方式

#### Feature Flag 配置
```yaml
# config/feature_flags.yaml
analysis_mode:
  type: multivariate
  options: [fast, standard, deep, multi_round]
  default: standard
```

#### CLI 使用
```bash
# 使用多轮分析模式
python scripts/cli.py full \
    --bug "描述你的Bug" \
    --log logcat.txt \
    --analysis-mode multi_round
```

#### 代码调用
```python
from harness.skills import MultiRoundAnalysisSkill
from harness.core import Orchestrator, StateManager, ContextEngine

# 初始化
state = StateManager()
context = ContextEngine()
orchestrator = Orchestrator(state, context)
multi_round_skill = MultiRoundAnalysisSkill(state, context)

# 执行多轮分析
result = multi_round_skill.execute(
    bug_description="你的 Bug 描述",
    log_content="日志内容"
)

# 访问结果
print(f"第一轮分析: {result['round1']['analysis']}")
print(f"第二轮分析: {result['round2']['root_cause']}")
print(f"第三轮验证: {result['round3']['validation']}")
```

---

## 📦 Workflow ID 统一产物管理

### 目录结构

```
outputs/
├── index/
│   └── workflow_index.json  # 工作流元数据索引
└── {workflow_id}/
    ├── logs/                # 日志文件
    ├── extracted/           # 提取结果
    ├── analysis/            # 分析结果
    ├── reports/             # 生成的报告
    └── artifacts/           # 其他产物
```

### WorkflowMetadata 数据结构

```python
@dataclass
class WorkflowMetadata:
    workflow_id: str
    created_at: datetime
    status: str  # pending, running, completed, failed
    bug_description: str
    log_path: str
    outputs: Dict[str, str]  # 各阶段输出路径
    analysis_mode: str
    additional_findings: List[Dict]
```

### 使用示例

```python
from harness.core.state import StateManager, WorkflowPaths

# 初始化 StateManager
state = StateManager()

# 创建新工作流
workflow_id = state.create_workflow(
    bug_description="Bug 描述",
    log_path="/path/to/log.txt",
    analysis_mode="multi_round"
)

# 获取工作流路径
paths = WorkflowPaths(workflow_id)
print(f"日志目录: {paths.logs_dir}")
print(f"报告目录: {paths.reports_dir}")

# 更新工作流状态
state.update_workflow_status(workflow_id, "completed")

# 添加额外发现
state.add_additional_finding(workflow_id, {
    "type": "warning",
    "description": "发现性能问题",
    "evidence": "日志片段..."
})

# 列出所有工作流
all_workflows = state.workflow_index.list_all()

# 加载特定工作流
workflow = state.workflow_index.get(workflow_id)
```

---

## 🔍 Additional Findings 额外发现标注

### 设计目标

明确区分：
- **Main Findings**: 与用户报告的 Bug 直接相关的发现
- **Additional Findings**: 日志中发现但与报告 Bug 无关的问题

### 数据结构

```python
additional_finding = {
    "type": "warning",  # info, warning, error
    "category": "performance",  # performance, security, stability, etc.
    "description": "简短描述",
    "detailed_analysis": "详细分析",
    "evidence": "相关日志片段",
    "timestamp": "2026-05-18T10:30:00",
    "severity": "medium"  # low, medium, high
}
```

### 报告格式

生成的 Markdown 报告将包含独立章节：

```markdown
## Additional Findings

### 🔔 Warning: 性能问题

**类别**: Performance  
**严重程度**: Medium  

在日志中检测到 ANR 迹象，但与报告的 Bug 无直接关联。

**证据**:
```
05-18 10:30:00.123 E/ActivityManager: ANR in com.example.app
```

**建议**: 建议后续版本关注主线程耗时问题。
```

---

## 💰 Token 优化

### 默认值调整

| 组件 | 原限制 | 新限制 |
|------|--------|--------|
| LLM Client (单次调用) | 2000 | 4000 |
| 多轮分析 Round 1 | - | 8000 |
| 多轮分析 Round 2 | - | 12000 |
| 多轮分析 Round 3 | - | 8000 |

### 配置位置

`log_analyzer/llm/llm_client.py`:
```python
DEFAULT_MAX_TOKENS = 4000
```

---

## 🧪 测试覆盖

新增测试文件：`tests/test_workflow_enhancements.py`

运行测试：
```bash
python -m pytest tests/test_workflow_enhancements.py -v
```

测试内容：
- ✅ WorkflowMetadata 数据结构
- ✅ WorkflowIndex 索引管理
- ✅ StateManager workflow 扩展
- ✅ MultiRoundAnalysisSkill 三轮分析
- ✅ Additional Findings 管理
- ✅ 集成测试

---

## 📝 更新文件清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `harness/skills/multi_round_analysis.py` | 新增 | 多轮分析技能 |
| `harness/core/state.py` | 修改 | 添加 WorkflowMetadata, WorkflowIndex |
| `log_analyzer/llm/llm_client.py` | 修改 | Token 限制翻倍 |
| `harness/skills/llm_analysis.py` | 修改 | 集成多轮分析 |
| `harness/skills/report.py` | 修改 | 添加多轮分析报告和额外发现 |
| `config/feature_flags.yaml` | 修改 | 添加 multi_round 选项 |
| `harness/skills/__init__.py` | 修改 | 导出新技能 |
| `tests/test_workflow_enhancements.py` | 新增 | 测试用例 |
| `docs/CHANGELOG.md` | 修改 | v9.0 更新日志 |
| `README.md` | 修改 | v9.0 功能说明 |
| `docs/V9_FEATURES_GUIDE.md` | 新增 | 本文档 |

---

## 🚀 完整示例

```python
from harness.core import StateManager, ContextEngine, Orchestrator
from harness.skills import MultiRoundAnalysisSkill, ReportSkill

# 1. 初始化
state = StateManager()
context = ContextEngine()
orchestrator = Orchestrator(state, context)

# 2. 创建工作流
workflow_id = state.create_workflow(
    bug_description="App 在启动时崩溃",
    log_path="data/test_log.txt",
    analysis_mode="multi_round"
)

# 3. 执行多轮分析
multi_round_skill = MultiRoundAnalysisSkill(state, context)
analysis_result = multi_round_skill.execute(
    bug_description="App 在启动时崩溃",
    log_content=open("data/test_log.txt").read()
)

# 4. 添加额外发现
state.add_additional_finding(workflow_id, {
    "type": "warning",
    "category": "performance",
    "description": "主线程耗时过长",
    "severity": "medium"
})

# 5. 生成报告
report_skill = ReportSkill(state, context)
report = report_skill.execute(
    analysis_result=analysis_result,
    workflow_id=workflow_id,
    format="markdown"
)

# 6. 保存报告
paths = WorkflowPaths(workflow_id)
with open(paths.reports_dir / "report.md", "w") as f:
    f.write(report)

# 7. 完成工作流
state.update_workflow_status(workflow_id, "completed")
```

---

## 📚 相关文档

- [CHANGELOG.md](file:///workspace/docs/CHANGELOG.md) - 版本变更记录
- [README.md](file:///workspace/README.md) - 项目主文档
- [PROJECT_SUMMARY.md](file:///workspace/docs/PROJECT_SUMMARY.md) - 项目总结
