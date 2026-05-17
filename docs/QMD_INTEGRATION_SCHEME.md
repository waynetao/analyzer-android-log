# QMD 知识库集成技术方案

## 文档信息

| 项目 | 说明 |
|------|------|
| **文档版本** | v1.0 |
| **创建日期** | 2026-05-17 |
| **适用范围** | Harness Android 日志分析 Agent |
| **技术负责人** | AI Assistant |

---

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Harness Agent System                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────────┐    │
│   │   Skills    │ ──── │   Memory    │ ──── │   QMD MCP       │    │
│   │   Layer     │      │   Manager   │      │   Server        │    │
│   │             │      │             │      │   (Docker)      │    │
│   └──────┬──────┘      └──────┬──────┘      └────────┬────────┘    │
│          │                    │                       │             │
│          │                    │                       │             │
│          ▼                    ▼                       ▼             │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────────┐    │
│   │   Policy    │      │   Context   │      │   SQLite + FTS5 │    │
│   │   Layer     │      │   Engine    │      │   + Embeddings  │    │
│   └─────────────┘      └─────────────┘      └────────┬────────┘    │
│                                                      │             │
│                                    ┌─────────────────▼─────────┐   │
│                                    │    Knowledge Base        │   │
│                                    │    (Markdown Files)      │   │
│                                    └─────────────────┬─────────┘   │
│                                                      │             │
│                    ┌─────────────────────────────────┼─────────┐   │
│                    │                                 │         │   │
│          ┌─────────▼─────────┐           ┌───────────▼───────┐ │   │
│          │  Event Log Tags   │           │   ANR/Tombstone   │ │   │
│          └───────────────────┘           └───────────────────┘ │   │
│          ┌─────────▼─────────┐           ┌───────────▼───────┐ │   │
│          │   dumpsys SOP     │           │   GC Log Format   │ │   │
│          └───────────────────┘           └───────────────────┘ │   │
│          ┌─────────▼─────────┐                                 │   │
│          │   sysprops Def    │                                 │   │
│          └───────────────────┘                                 │   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 组件职责

| 组件 | 职责 | 说明 |
|------|------|------|
| **QMD MCP Server** | 语义检索服务 | Docker 部署，提供 REST API |
| **Memory Manager** | 知识库管理 | 封装 QMD 客户端，提供统一接口 |
| **Knowledge Base** | 知识文档存储 | Git 管理的 Markdown 文件 |
| **Skills Layer** | 业务技能 | 调用 Memory Manager 获取知识 |

### 1.3 数据流

```
Agent 分析请求
    │
    ▼
┌──────────────────┐
│ 分析任务执行     │
│ (LogAnalysisSkill)│
└────────┬─────────┘
         │ 需要知识
         ▼
┌──────────────────┐
│ MemoryManager   │
│ .query("ANR格式")│
└────────┬─────────┘
         │ HTTP/REST
         ▼
┌──────────────────┐
│ QMD MCP Server  │
│ .search(query)  │
└────────┬─────────┘
         │ 检索知识库
         ▼
┌──────────────────┐
│ SQLite + FTS5   │
│ .search()       │
└────────┬─────────┘
         │ 返回结果
         ▼
┌──────────────────┐
│ 相关文档片段    │
│ (Top 3-5)      │
└────────┬─────────┘
         │ 注入上下文
         ▼
┌──────────────────┐
│ LLM 分析        │
│ (增强准确性)    │
└──────────────────┘
```

---

## 2. 目录结构设计

### 2.1 知识库目录结构

```
knowledge_base/                              # 知识库根目录
├── meta.yaml                               # 知识库元数据配置
├── config/                                 # QMD 配置目录
│   └── qmd_config.yaml                    # QMD 服务器配置
└── android_knowledge/                      # Android 知识域
    ├── _index.md                          # 知识域总览
    ├── event_log_tags/                    # Event Log Tags
    │   ├── _index.md                      # 分类总览
    │   ├── system_tags.md                 # 系统 Tags
    │   ├── app_tags.md                    # 应用 Tags
    │   └── vendor_tags.md                 # 厂商定制 Tags
    ├── anr_tombstone/                     # ANR/Tombstone
    │   ├── _index.md                      # 分类总览
    │   ├── anr_format.md                  # ANR 格式说明
    │   ├── tombstone_format.md            # Tombstone 格式
    │   └── root_cause_patterns.md         # 根因模式库
    ├── dumpsys/                           # dumpsys
    │   ├── _index.md                      # 分类总览
    │   ├── meminfo_sop.md                 # meminfo SOP
    │   ├── battery_sop.md                 # battery SOP
    │   └── activity_sop.md                # activity SOP
    ├── sysprops/                          # 系统属性
    │   ├── _index.md                      # 分类总览
    │   ├── critical_props.md              # 关键属性定义
    │   └── debug_props.md                 # 调试属性定义
    └── gc_logs/                           # GC 日志
        ├── _index.md                      # 分类总览
        ├── gc_types.md                    # GC 类型说明
        └── format_parsing.md              # 格式解析指南
```

### 2.2 文件命名规范

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 分类总览 | `_index.md` | `event_log_tags/_index.md` |
| 文档文件 | `{topic}_{type}.md` | `meminfo_sop.md`, `gc_types.md` |
| 配置文件 | `{name}_config.yaml` | `qmd_config.yaml` |

---

## 3. 文档模板设计

### 3.1 通用文档模板

```markdown
# 文档标题

## 文档信息

| 字段 | 值 |
|------|-----|
| **版本** | v1.0 |
| **适用版本** | Android 8.0+ |
| **最后更新** | 2026-05-17 |
| **状态** | Draft/Review/Released |
| **标签** | tag1, tag2, tag3 |

---

## 1. 概述

简明描述本文档的目的和范围。

---

## 2. 格式说明

详细说明数据格式、字段含义、解析方法。

### 2.1 格式结构

```text
[示例格式]
```

### 2.2 字段定义

| 字段 | 类型 | 含义 | 示例 |
|------|------|------|------|
| field1 | string | 说明 | example |
| field2 | int | 说明 | 123 |

---

## 3. 解析方法

说明如何解析和理解此类数据。

### 3.1 解析步骤

1. 步骤一
2. 步骤二
3. 步骤三

### 3.2 工具推荐

| 工具 | 用途 | 链接 |
|------|------|------|
| tool1 | 用途 | link |

---

## 4. 常见模式

列出常见的模式、问题、根因等。

### 4.1 问题模式

| 模式 | 描述 | 根因 |
|------|------|------|
| pattern1 | 描述 | 根因分析 |

### 4.2 示例

```text
[示例日志]
```

---

## 5. 参考资料

- [Reference 1](url)
- [Reference 2](url)
```

### 3.2 分类总览模板 (`_index.md`)

```markdown
# 知识域名称

## 概述

本知识域包含的内容概述。

## 内容清单

| 文档 | 版本 | 状态 | 描述 |
|------|------|------|------|
| doc1.md | v1.0 | Released | 描述 |
| doc2.md | v1.0 | Draft | 描述 |

## 使用场景

| 场景 | 推荐文档 |
|------|----------|
| 场景1 | doc1.md |
| 场景2 | doc2.md |

## 更新日志

| 日期 | 更新内容 | 作者 |
|------|----------|------|
| 2026-05-17 | 初始版本 | AI Assistant |
```

---

## 4. QMD 配置方案

### 4.1 QMD MCP Server 配置

```yaml
# config/qmd_config.yaml
server:
  host: 0.0.0.0
  port: 8000
  log_level: info

index:
  paths:
    - name: android_knowledge
      path: ./knowledge_base/android_knowledge
      pattern: "**/*.md"
      ignore:
        - "**/_index.md"
  
  indexing:
    enabled: true
    schedule: "0 2 * * *"  # 每天凌晨2点重新索引
    chunk_size: 512
    chunk_overlap: 64

search:
  default_mode: vsearch  # vector search
  top_k: 5
  rerank:
    enabled: true
    model: cross-encoder/ms-marco-MiniLM-L-6-v2
  hybrid:
    enabled: true
    bm25_weight: 0.3
    vector_weight: 0.7

embeddings:
  model: all-MiniLM-L6-v2
  device: cpu
  batch_size: 32

storage:
  type: sqlite
  path: ./data/qmd.db
  backup:
    enabled: true
    schedule: "0 3 * * *"
```

### 4.2 Docker Compose 配置

```yaml
version: '3.8'
services:
  qmd-server:
    image: qmd/qmd-server:latest
    container_name: qmd-server
    ports:
      - "8000:8000"
    volumes:
      - ./knowledge_base:/app/knowledge_base
      - ./config/qmd_config.yaml:/app/config/config.yaml
      - ./data:/app/data
    environment:
      - QMD_CONFIG=/app/config/config.yaml
      - QMD_LOG_LEVEL=info
    restart: unless-stopped
    networks:
      - harness-network

networks:
  harness-network:
    driver: bridge
```

---

## 5. Harness 集成方案

### 5.1 MemoryManager 实现

```python
# harness/memory/qmd_memory_manager.py
from typing import List, Dict, Any, Optional
import requests
import json

class QMDMemoryManager:
    """QMD 知识库管理器"""
    
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url
        self.session = requests.Session()
    
    def search(self, 
               query: str, 
               top_k: int = 5, 
               collection: str = "android_knowledge") -> List[Dict[str, Any]]:
        """
        检索知识库
        
        Args:
            query: 检索查询
            top_k: 返回结果数量
            collection: 知识集合名称
        
        Returns:
            检索结果列表，包含文档片段和相关性评分
        """
        try:
            response = self.session.post(
                f"{self.server_url}/api/search",
                json={
                    "query": query,
                    "top_k": top_k,
                    "collection": collection
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Fallback: 返回空列表，不影响主流程
            return []
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取完整文档内容"""
        try:
            response = self.session.get(
                f"{self.server_url}/api/documents/{document_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
    
    def get_collections(self) -> List[str]:
        """获取所有知识集合"""
        try:
            response = self.session.get(
                f"{self.server_url}/api/collections",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return []
    
    def query_by_type(self, 
                      doc_type: str, 
                      query: str = "",
                      top_k: int = 5) -> List[Dict[str, Any]]:
        """
        按文档类型检索
        
        Args:
            doc_type: 文档类型 (event_tags, anr, dumpsys, gc, sysprops)
            query: 可选的查询词
            top_k: 返回数量
        
        Returns:
            检索结果
        """
        type_mapping = {
            "event_tags": "event_log_tags",
            "anr": "anr_tombstone",
            "dumpsys": "dumpsys",
            "gc": "gc_logs",
            "sysprops": "sysprops"
        }
        
        collection = type_mapping.get(doc_type, "android_knowledge")
        return self.search(query, top_k, collection)
```

### 5.2 KnowledgeRetrievalSkill

```python
# harness/skills/knowledge_retrieval.py
from typing import Dict, Any
from .base import BaseSkill, SkillResult

class KnowledgeRetrievalSkill(BaseSkill):
    """知识检索技能 - 从 QMD 知识库检索相关知识"""
    
    @property
    def name(self) -> str:
        return "knowledge_retrieval"
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """
        执行知识检索
        
        Args:
            inputs: 包含以下字段
                - query: 检索查询词
                - doc_type: 文档类型 (可选)
                - top_k: 返回数量 (可选，默认5)
        
        Returns:
            检索结果
        """
        valid, msg = self._validate_inputs(inputs, ["query"])
        if not valid:
            return SkillResult(False, {}, msg)
        
        from harness.memory.qmd_memory_manager import QMDMemoryManager
        
        try:
            manager = QMDMemoryManager()
            
            doc_type = inputs.get("doc_type", "")
            top_k = inputs.get("top_k", 5)
            
            if doc_type:
                results = manager.query_by_type(doc_type, inputs["query"], top_k)
            else:
                results = manager.search(inputs["query"], top_k)
            
            return SkillResult(
                success=True,
                data={
                    "results": results,
                    "query": inputs["query"],
                    "doc_type": doc_type,
                    "count": len(results)
                },
                message=f"检索到 {len(results)} 条相关知识"
            )
        
        except Exception as e:
            return SkillResult(
                success=False,
                data={},
                message=f"知识检索失败: {str(e)}"
            )
```

### 5.3 Agent 集成

```python
# 在 harness_agent_advanced.py 中注册新技能

class AdvancedHarnessAgent(HarnessAgent):
    def __init__(self):
        super().__init__()
        self._register_skills()
    
    def _register_skills(self):
        # 原有技能
        self.orchestrator.register_skill(LogExtractionSkill())
        self.orchestrator.register_skill(BugAnalysisSkill())
        self.orchestrator.register_skill(ReportGenerationSkill())
        
        # LLM 技能
        self.orchestrator.register_skill(LLMAnalysisSkill())
        self.orchestrator.register_skill(AdvancedLogAnalysisSkill())
        
        # 证据匹配技能
        self.orchestrator.register_skill(LogEvidenceMatcherSkill())
        self.orchestrator.register_skill(TimelineBuilderSkill())
        
        # aloggrep 技能
        self.orchestrator.register_skill(AloggrepWorkflowSkill())
        
        # 知识检索技能（新增）
        self.orchestrator.register_skill(KnowledgeRetrievalSkill())
```

---

## 6. API 契约

### 6.1 QMD Server API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/search` | POST | 检索知识库 |
| `/api/documents/{id}` | GET | 获取文档详情 |
| `/api/collections` | GET | 获取集合列表 |
| `/api/index` | POST | 手动触发索引 |
| `/api/health` | GET | 健康检查 |

#### `/api/search` 请求体

```json
{
  "query": "ANR 格式",
  "top_k": 5,
  "collection": "android_knowledge",
  "mode": "vsearch"
}
```

#### `/api/search` 响应体

```json
{
  "results": [
    {
      "id": "doc1",
      "title": "ANR 格式说明",
      "path": "anr_tombstone/anr_format.md",
      "content": "ANR (Application Not Responding)...",
      "score": 0.92,
      "metadata": {
        "version": "v1.0",
        "tags": ["anr", "format"]
      }
    }
  ],
  "total": 15,
  "query": "ANR 格式"
}
```

### 6.2 MemoryManager API

| 方法 | 参数 | 返回值 | 描述 |
|------|------|--------|------|
| `search()` | query, top_k, collection | List[Dict] | 通用检索 |
| `get_document()` | document_id | Optional[Dict] | 获取完整文档 |
| `get_collections()` | - | List[str] | 获取集合列表 |
| `query_by_type()` | doc_type, query, top_k | List[Dict] | 按类型检索 |

### 6.3 KnowledgeRetrievalSkill 输入输出

#### 输入

```python
{
    "query": "ANR 格式",          # 必填: 检索查询词
    "doc_type": "anr",            # 可选: 文档类型过滤
    "top_k": 5                    # 可选: 返回数量，默认5
}
```

#### 输出

```python
{
    "results": [...],             # 检索结果列表
    "query": "ANR 格式",          # 原始查询
    "doc_type": "anr",            # 使用的文档类型
    "count": 3                    # 结果数量
}
```

---

## 7. 部署与运行

### 7.1 启动 QMD Server

```bash
# 方式1: Docker Compose
cd /workspace
docker-compose up -d

# 方式2: 手动启动（开发模式）
python -m qmd.server --config config/qmd_config.yaml
```

### 7.2 健康检查

```bash
curl http://localhost:8000/api/health
# 预期响应: {"status": "healthy"}
```

### 7.3 测试检索

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "ANR 格式", "top_k": 3}'
```

---

## 8. 安全与监控

### 8.1 安全措施

| 措施 | 说明 |
|------|------|
| **网络隔离** | Docker 网络隔离，仅允许内部访问 |
| **API 认证** | 可选的 API Key 认证 |
| **输入验证** | 对查询参数进行安全过滤 |
| **日志审计** | 记录所有检索请求 |

### 8.2 监控指标

| 指标 | 说明 |
|------|------|
| `qmd_search_requests` | 检索请求数 |
| `qmd_search_latency` | 检索延迟(ms) |
| `qmd_index_size` | 索引大小 |
| `qmd_documents_count` | 文档数量 |

---

## 9. 回滚与降级

### 9.1 降级策略

```python
class QMDMemoryManager:
    def search(self, query, top_k=5, collection="android_knowledge"):
        try:
            # 正常检索
            response = self.session.post(...)
            return response.json()
        except requests.exceptions.RequestException:
            # 降级: 返回空列表
            # Agent 将使用内置知识或跳过知识增强
            return []
```

### 9.2 回滚方案

| 场景 | 回滚方案 |
|------|----------|
| QMD Server 故障 | Agent 使用内置知识，不影响主流程 |
| 索引损坏 | 从备份恢复 `qmd.db` |
| 文档错误 | 回滚 Git 提交，重新索引 |

---

## 附录

### A. 文档类型枚举

| 类型标识 | 目录 | 描述 |
|---------|------|------|
| `event_tags` | event_log_tags/ | Event Log Tags |
| `anr` | anr_tombstone/ | ANR/Tombstone |
| `dumpsys` | dumpsys/ | dumpsys SOP |
| `gc` | gc_logs/ | GC 日志 |
| `sysprops` | sysprops/ | 系统属性 |

### B. 状态枚举

| 状态 | 含义 |
|------|------|
| `Draft` | 草稿，正在编写 |
| `Review` | 审核中 |
| `Released` | 已发布，可使用 |
| `Deprecated` | 已废弃 |

### C. 标签规范

| 标签 | 含义 |
|------|------|
| `android` | Android 相关 |
| `logcat` | Logcat 相关 |
| `anr` | ANR 相关 |
| `memory` | 内存相关 |
| `battery` | 电池相关 |

---

**文档版本**: v1.0  
**最后更新**: 2026-05-17
