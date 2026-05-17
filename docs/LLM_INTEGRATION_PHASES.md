# 🤖 LLM集成阶段分析

## 📊 当前LLM引入的阶段

### ✅ 阶段1：高级日志分析后，LLM深度分析

**文件位置**：[`harness/skills/llm_analysis.py`](file:///workspace/harness/skills/llm_analysis.py)

**流程**：
```
日志提取 → 高级分析 → [LLM分析] → 报告生成
```

**具体功能**：
- 接收用户bug描述
- 接收关键日志证据
- 接收设备状态信息
- 生成高质量分析报告

**提示词特点**（第76-127行）：
1. 要求引用具体日志证据
2. 要求根因分析
3. 要求具体修复建议
4. 要求预防措施

---

### ✅ 阶段2：日志证据匹配 (新增!)

**文件位置**：[`harness/skills/log_evidence_matcher.py`](file:///workspace/harness/skills/log_evidence_matcher.py)

**流程**：
```
日志提取 → 高级分析 → [证据匹配] → [时间线构建] → 报告生成
```

**具体功能**：
- 对照用户描述的现象和实际日志
- 提供置信度评分
- 构建场景变化追踪
- 生成"我们在日志中看到了什么"和"发生了什么"

**特性**：
1. 支持模拟模式（无需API）
2. 支持真实LLM调用
3. 输出结构化数据供报告使用

---

## 🔄 完整工作流

### 当前6步分析流程（高级版）

| 步骤 | 阶段 | 说明 | 文件 |
|-----|-----|-----|-----|
| 1️⃣ | **日志提取** | 解析日志文件 | [`log_extraction.py`](file:///workspace/harness/skills/log_extraction.py) |
| 2️⃣ | **高级分析** | 提取关键日志、设备状态 | [`log_analysis_advanced.py`](file:///workspace/harness/skills/log_analysis_advanced.py) |
| 3️⃣ | **LLM分析** | 智能深度分析 ⭐ | [`llm_analysis.py`](file:///workspace/harness/skills/llm_analysis.py) |
| 4️⃣ | **证据匹配** | 对照用户现象和日志 ⭐ (新!) | [`log_evidence_matcher.py`](file:///workspace/harness/skills/log_evidence_matcher.py) |
| 5️⃣ | **时间线构建** | 重构事件顺序 ⭐ (新!) | [`log_evidence_matcher.py`](file:///workspace/harness/skills/log_evidence_matcher.py) |
| 6️⃣ | **报告生成** | 多格式输出 | [`report.py`](file:///workspace/harness/skills/report.py) |

---

## 🎯 证据匹配技能的输入输出

### 输入数据结构

```python
{
    "bug_description": {
        "raw_text": "用户的bug描述",
        "summary": "问题摘要",
        "keywords": ["crash"]
    },
    "critical_logs": [...],  # 关键日志证据
    "device_state": {...}    # 设备状态
}
```

### 输出数据结构

```python
{
    "confidence_score": 0.92,  # 置信度评分
    "timeline_match": [        # 用户现象与日志对照
        {
            "user_description": "应用打开主页面时崩溃",
            "log_evidence": "找到了对应时间的崩溃日志",
            "matched": True,
            "confidence": 0.95,
            "log_entries": [...]
        }
    ],
    "scene_changes": [         # 场景变化
        {
            "time_point": "11:25:30",
            "scene": "应用启动",
            "log_summary": "ActivityManager: Start proc com.example.app"
        }
    ],
    "what_we_saw_in_logs": [...],  # 我们在日志中看到了什么
    "what_happened": [...],        # 发生了什么
    "confidence_explanation": "..." # 置信度说明
}
```

---

## 💡 LLM提示词工程

### 提示词结构（阶段1：llm_analysis.py，第76-127行）

1. **系统角色**：资深Android技术支持专家
2. **任务要求**：所有结论必须有日志证据支撑
3. **上下文信息**：
   - 用户问题描述
   - 日志分析摘要
   - 关键日志证据（前5条）
   - 设备状态信息
4. **输出要求**：
   - 问题定位（有日志证据）
   - 根因分析
   - 修复建议（可操作）
   - 预防措施

### 提示词结构（阶段2：log_evidence_matcher.py，待实现）

1. **系统角色**：日志证据鉴定专家
2. **任务要求**：对照用户描述和日志
3. **输出要求**：
   - 置信度评分
   - 证据匹配对照
   - 场景变化追踪
   - 事件时间线

---

## 📊 时间线构建技能

**文件位置**：[`harness/skills/log_evidence_matcher.py`](file:///workspace/harness/skills/log_evidence_matcher.py)

**功能**：
- 从日志中提取事件序列
- 自动识别事件类型（应用启动、崩溃、ANR、内存等）
- 按重要性排序
- 生成结构化时间线数据

**输出结构**：
```python
{
    "total_events": 50,
    "critical_events": [...],  # 关键事件
    "high_important_events": [...],
    "full_timeline": [...]
}
```

---

## 🚀 可以扩展的LLM阶段

### 未来可能引入LLM的环节

| 阶段 | 功能说明 | 优先级 |
|-----|---------|-------|
| **Bug描述解析** | 自动提取包名、时间点、复现步骤 | 🟡 中 |
| **日志过滤** | 智能筛选相关日志 | 🟢 高 |
| **异常分类** | 自动识别异常类型和严重程度 | 🟡 中 |
| **报告摘要** | 自动生成不同版本的报告 | 🟢 高 |
| **修复验证** | 分析修复后的日志是否解决问题 | 🟡 中 |
| **场景对话** | 回答用户针对分析的追问 | 🟢 高 |

---

## 🔧 当前实现细节

### LLM技能集成位置

在[`harness_agent_advanced.py`](file:///workspace/harness_agent_advanced.py)中注册所有技能：

```python
# 注册技能
self.orchestrator.register_skill(LogExtractionSkill())
self.orchestrator.register_skill(AdvancedLogAnalysisSkill())
self.orchestrator.register_skill(self.llm_skill)
self.orchestrator.register_skill(LogEvidenceMatcherSkill(...))  # 新!
self.orchestrator.register_skill(TimelineBuilderSkill())  # 新!
self.orchestrator.register_skill(ReportGenerationSkill())
```

### 报告中的证据匹配内容

在[`report.py`](file:///workspace/harness/skills/report.py)中，证据匹配结果作为独立章节展示：
- Markdown中的`## 🎯 日志证据匹配`
- 置信度展示、用户现象与日志对照、场景变化等
- 新增`## 📊 事件时间线`章节
- HTML中的可视化区域
- JSON中的完整结构化数据

---

## ✨ 总结

### 当前LLM使用情况
- ✅ **2个阶段**引入LLM/智能分析
- ✅ **阶段1**：高级分析后的LLM深度分析
- ✅ **阶段2**：日志证据匹配和时间线构建 (新!)
- ✅ **有证据支撑**：所有LLM分析都基于关键日志
- ✅ **高质量输出**：要求具体修复建议和预防措施
- ✅ **多格式集成**：所有分析结果集成到所有报告格式

### 设计优势
- 🔒 **LLM独立阶段**：不影响基础分析流程
- 🛡️ **降级方案**：提供mock模式，无API也可工作
- 📦 **模块化设计**：容易替换和升级
- 🎯 **证据匹配**：大幅提升报告置信度和可信度

---

## 📄 测试脚本

- [`test_advanced_agent.py`](file:///workspace/test_advanced_agent.py) - 测试完整高级分析流程
- [`test_evidence_matching.py`](file:///workspace/test_evidence_matching.py) - 专门测试证据匹配功能 (新!)
