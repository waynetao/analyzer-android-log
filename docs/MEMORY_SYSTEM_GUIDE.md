# 记忆系统集成指南

## 📚 概述

我们已成功集成了一个灵活的记忆系统，支持两种模式无缝切换：

- **Simple 模式**（默认）：使用本地 JSON 存储，无外部依赖，即开即用
- **OpenViking 模式**：增强版，使用 OpenViking 上下文数据库，支持分层检索和更高级功能

两种模式共享相同的接口，通过 Feature Flag 配置即可无缝切换。

---

## 🎯 快速开始

### 1. 默认使用 Simple 模式（无需配置）

开箱即用！直接运行 Agent，会自动使用 Simple 模式：

```bash
python harness_agent_advanced.py --bug "应用崩溃" --log /path/to/log
```

### 2. 查看案例库统计

```bash
python harness_agent_advanced.py --list-cases
```

### 3. 切换模式（修改配置文件）

编辑 `config/feature_flags.yaml`：

```yaml
flags:
  memory_system_enabled:
    enabled: true    # 开启/关闭记忆系统
  memory_mode:
    default_value: simple  # 可选值：simple 或 openviking
  auto_save_cases:
    enabled: true    # 分析后自动保存案例
  similar_case_retrieval:
    enabled: true    # 分析前检索相似案例
```

---

## 📂 项目文件结构

```
/workspace/
├── config/
│   └── feature_flags.yaml          # Feature Flag 配置
├── harness/
│   └── skills/
│       ├── case_library_skill.py      # Simple 模式
│       └── openviking_memory_skill.py # OpenViking 模式（可选）
├── case_library/                      # Simple 模式数据（自动生成）
│   ├── cases/
│   ├── tags/
│   ├── index.json
│   └── metadata.json
├── openviking_data/                   # OpenViking 数据（可选）
├── openviking_config_template.json    # OpenViking 配置模板
├── test_memory_integration.py         # 集成测试
└── harness_agent_advanced.py          # 主 Agent
```

---

## 🔧 Simple 模式详解

Simple 模式使用本地 JSON 文件存储案例，优点是：
- 零依赖，无需额外配置
- 即开即用，数据透明
- 支持所有核心功能

### 使用方法

无需额外配置！功能会自动工作：
1. 分析时自动检索相似案例
2. 分析完成后自动保存案例
3. 使用标签系统组织案例

### 数据结构

```json
{
  "case_id": "case_20260517_091649_abc123",
  "created_at": "2026-05-17T09:16:49.123456",
  "updated_at": "2026-05-17T09:16:49.123456",
  "bug_description": {
    "summary": "应用启动时崩溃",
    "keywords": ["crash", "startup"]
  },
  "l0_summary": "L0 级摘要（一句话）",
  "l1_overview": {
    "crash_count": 1,
    "anr_count": 0
  },
  "analysis": {
    "bug_type": "crash",
    "root_cause": "原因分析...",
    "fix_suggestion": "修复建议...",
    "confidence": 0.9
  },
  "tags": ["crash", "startup"],
  "metadata": {
    "device": "Pixel 6",
    "android_version": "12"
  },
  "status": "active"
}
```

---

## 🚀 OpenViking 模式（高级）

OpenViking 是字节跳动开源的上下文数据库，专为 AI Agent 设计。

### 什么时候需要 OpenViking？

- 案例数量 > 1000 条
- 需要更智能的语义检索
- 需要 L0/L1/L2 分层加载（节省 Token）
- 需要多 Agent 协作
- 需要更好的可观测性

### 配置 OpenViking

1. **复制配置模板**：
   ```bash
   mkdir -p ~/.openviking
   cp /workspace/openviking_config_template.json ~/.openviking/ov.conf
   ```

2. **编辑配置文件**：
   - 填入真实的 API Key
   - 根据你的云服务商选择合适的 provider

3. **切换到 OpenViking 模式**：
   编辑 `config/feature_flags.yaml`：
   ```yaml
   memory_mode:
     default_value: openviking
   ```

### OpenViking 优势

| 特性 | Simple 模式 | OpenViking 模式 |
|------|------------|----------------|
| 安装难度 | 零配置 | 需要 API 配置 |
| 存储 | 本地 JSON | AGFS 文件系统 |
| 检索 | 关键词匹配 | 向量搜索 + 目录检索 |
| L0/L1/L2 | 基础支持 | 完整支持 |
| Token 优化 | 基础 | 显著优化 |
| 扩展性 | 有限 | 高扩展性 |

---

## 📊 Feature Flag 完整列表

| Flag | 类型 | 默认值 | 说明 |
|------|-----|--------|------|
| `memory_system_enabled` | Boolean | `true` | 记忆系统总开关 |
| `memory_mode` | Enum | `simple` | 记忆系统模式：simple/openviking |
| `auto_save_cases` | Boolean | `true` | 分析完成后自动保存案例 |
| `similar_case_retrieval` | Boolean | `true` | 分析前检索相似案例 |
| `anti_rigidity_enabled` | Boolean | `true` | 防僵化机制（待实现） |

---

## 🧪 测试

运行集成测试：

```bash
cd /workspace
python test_memory_integration.py
```

运行单元测试（Simple 模式）：
```bash
python test_case_library.py
```

---

## 💡 最佳实践

1. **开始时使用 Simple 模式**：它已覆盖所有核心功能，无需配置
2. **积累一定数据后再考虑 OpenViking**：建议 1000+ 案例后再考虑
3. **定期备份案例库**：Simple 模式的所有数据在 `/workspace/case_library/`
4. **善用标签系统**：让检索更准确
5. **使用 Feature Flag 做灰度测试**：先小范围验证 OpenViking

---

## 🛠️ 故障排查

### 问题 1: OpenViking 配置错误

**现象**: 提示配置文件未找到
**解决**: 使用 Simple 模式（不需要 OpenViking 配置）

### 问题 2: 案例未保存

**现象**: 分析结束后没有案例保存
**排查**: 检查 Feature Flag `auto_save_cases` 是否开启

### 问题 3: 相似案例检索效果不佳

**建议**: 更精确的 bug 描述和标签有助于提高检索质量

---

## 🚧 待实现功能

- [ ] 防僵化机制（Anti-rigidity）
- [ ] 案例质量评分
- [ ] 自动案例审核
- [ ] 更高级的统计分析

---

## 📞 相关文档

- [OpenViking 集成计划](./OPENVIIKING_INTEGRATION_PLAN.md)
- [Bug 类型优化](./BUG_TYPE_PROMPT_OPTIMIZATION.md)
- [日志提取精度](./LOG_EXTRACTION_PRECISION.md)

