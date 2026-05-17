# OpenViking 集成实施计划

## 📋 文档信息

| 项目 | 说明 |
|------|------|
| 版本 | v1.0 |
| 更新日期 | 2026-05-17 |
| 状态 | 规划中 |
| 相关文档 | [BUG_TYPE_PROMPT_OPTIMIZATION.md](file:///workspace/BUG_TYPE_PROMPT_OPTIMIZATION.md) |

---

## 🎯 目标

通过 Feature Flag 控制两种记忆模式：
1. **MVP 模式** (`memory_mode=simple`): 轻量级 JSON 案例库，无需额外依赖
2. **OpenViking 模式** (`memory_mode=openviking`): 完整 OpenViking 集成，支持高级检索

---

## 🏗️ Feature Flag 设计

### 新增 Flags

```yaml
# config/feature_flags.yaml

flags:
  # 记忆系统总开关
  memory_system_enabled:
    name: memory_system_enabled
    description: 是否启用记忆系统
    flag_type: boolean
    enabled: true
    environments: [dev, prod]
    
  # 记忆模式选择
  memory_mode:
    name: memory_mode
    description: 记忆系统模式：simple(轻量MVP) | openviking(完整集成)
    flag_type: multivariate
    default_value: simple
    enabled: true
    environments: [dev, prod]
    variants:
      simple:
        description: 轻量级MVP模式，使用JSON文件存储
        value: simple
      openviking:
        description: OpenViking完整集成模式
        value: openviking
    percentage_rollout: 10  # 10%流量先测试openviking

  # 案例自动写入
  auto_save_cases:
    name: auto_save_cases
    description: 分析完成后自动保存案例到记忆库
    flag_type: boolean
    enabled: true
    environments: [dev, prod]
    
  # 相似案例检索
  similar_case_retrieval:
    name: similar_case_retrieval
    description: 分析前检索相似历史案例
    flag_type: boolean
    enabled: true
    environments: [dev, prod]
    
  # 防僵化机制
  anti_rigidity_enabled:
    name: anti_rigidity_enabled
    description: 启用防僵化机制（差异对比、失效标记等）
    flag_type: boolean
    enabled: true
    environments: [dev, prod]
```

---

## 📁 阶段 1: MVP 模式实现 (memory_mode=simple)

### 1.1 目录结构

```
/workspace/
├── case_library/
│   ├── index.json                    # 案例索引
│   ├── cases/
│   │   ├── 2026/
│   │   │   ├── 05/
│   │   │   │   ├── case_20260517_001.json
│   │   │   │   ├── case_20260517_002.json
│   │   │   │   └── ...
│   │   │   └── ...
│   │   └── ...
│   └── tags/
│       ├── crash.json
│       ├── anr.json
│       ├── memory_leak.json
│       └── ...
```

### 1.2 案例数据模型

```json
{
  "case_id": "case_20260517_001",
  "created_at": "2026-05-17T14:30:00Z",
  "updated_at": "2026-05-17T14:30:00Z",
  
  "bug_description": {
    "summary": "应用启动时崩溃",
    "keywords": ["crash", "startup", "NullPointerException"]
  },
  
  "l0_summary": {
    "text": "用户在启动APP时遇到java.lang.NullPointerException崩溃，发生在MainActivity.onCreate()",
    "tokens": 89,
    "generated_by": "aloggrep"
  },
  
  "l1_overview": {
    "crash_count": 1,
    "anr_count": 0,
    "exception_types": ["NullPointerException"],
    "affected_process": "com.example.app",
    "key_logs": [
      "FATAL EXCEPTION: main",
      "java.lang.NullPointerException: Attempt to invoke...",
      "MainActivity.onCreate():36"
    ],
    "tokens": 1850,
    "generated_by": "aloggrep"
  },
  
  "l2_full": {
    "extracted_logs": "...",
    "tokens": 45000
  },
  
  "analysis": {
    "bug_type": "crash",
    "root_cause": "View 未正确初始化",
    "fix_suggestion": "在 onCreate 中添加空值检查",
    "confidence": 0.95
  },
  
  "tags": ["crash", "startup", "NullPointerException", "android-12"],
  
  "metadata": {
    "device": "Pixel 6",
    "android_version": "12",
    "analyzer_version": "1.0.0"
  },
  
  "status": "active",
  "validation_count": 0,
  "success_count": 0,
  "failure_count": 0
}
```

### 1.3 MVP Skill 实现

```python
# harness/skills/case_library_skill.py

class CaseLibrarySkill(BaseSkill):
    """
    轻量级案例库 Skill (MVP)
    使用本地 JSON 文件存储，无需外部依赖
    """
    
    @property
    def name(self) -> str:
        return "case_library"
    
    def __init__(self):
        self.feature_sdk = FeatureSDK()
        self.library_path = Path("/workspace/case_library")
        self._ensure_directory_structure()
    
    def _ensure_directory_structure(self):
        """确保目录结构存在"""
        (self.library_path / "cases").mkdir(parents=True, exist_ok=True)
        (self.library_path / "tags").mkdir(parents=True, exist_ok=True)
        (self.library_path / "index.json").touch(exist_ok=True)
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """
        根据模式执行不同操作：
        - save_case: 保存新案例
        - search_similar: 搜索相似案例
        - get_by_tag: 按标签获取案例
        """
        action = inputs.get("action", "search_similar")
        
        if action == "save_case":
            return self._save_case(inputs)
        elif action == "search_similar":
            return self._search_similar(inputs)
        elif action == "get_by_tag":
            return self._get_by_tag(inputs)
        else:
            return SkillResult(False, {}, f"Unknown action: {action}")
    
    def _save_case(self, inputs: Dict) -> SkillResult:
        """保存案例"""
        case_id = self._generate_case_id()
        case_data = {
            "case_id": case_id,
            "created_at": datetime.now().isoformat(),
            "l0_summary": inputs.get("l0_summary"),
            "l1_overview": inputs.get("l1_overview"),
            "analysis": inputs.get("analysis"),
            "tags": inputs.get("tags", []),
            "status": "active"
        }
        
        # 保存案例文件
        case_path = self.library_path / "cases" / case_id
        with open(case_path, "w") as f:
            json.dump(case_data, f, indent=2, ensure_ascii=False)
        
        # 更新索引和标签
        self._update_index(case_data)
        self._update_tags(case_data)
        
        return SkillResult(True, {"case_id": case_id}, "案例已保存")
    
    def _search_similar(self, inputs: Dict) -> SkillResult:
        """搜索相似案例"""
        query = inputs.get("query", "")
        bug_type = inputs.get("bug_type")
        top_k = inputs.get("top_k", 3)
        
        # 简单关键词匹配
        results = self._simple_search(query, bug_type, top_k)
        
        return SkillResult(True, {
            "results": results,
            "mode": "simple"
        }, f"找到 {len(results)} 个相似案例")
    
    def _simple_search(self, query: str, bug_type: str, top_k: int) -> List[Dict]:
        """
        简单搜索算法 (MVP阶段)
        后续可升级为向量检索
        """
        index = self._load_index()
        scores = []
        
        query_keywords = set(query.lower().split())
        
        for case_id, case_meta in index.items():
            score = 0
            
            # Bug 类型匹配
            if bug_type and case_meta.get("bug_type") == bug_type:
                score += 5
            
            # 标签匹配
            case_tags = set(case_meta.get("tags", []))
            overlap = query_keywords & case_tags
            score += len(overlap) * 2
            
            # 关键词匹配
            case_keywords = set(case_meta.get("keywords", []))
            overlap = query_keywords & case_keywords
            score += len(overlap)
            
            if score > 0:
                scores.append((score, case_id))
        
        # 返回 top_k 个结果
        scores.sort(reverse=True)
        top_results = []
        
        for _, case_id in scores[:top_k]:
            case_path = self.library_path / "cases" / case_id
            if case_path.exists():
                with open(case_path) as f:
                    top_results.append(json.load(f))
        
        return top_results
```

---

## 📁 阶段 2: OpenViking 模式实现 (memory_mode=openviking)

### 2.1 OpenViking 环境准备

```bash
# 1. 安装 OpenViking
pip install openviking

# 2. 初始化配置
openviking-server init

# 3. 启动服务 (后台)
openviking-server start -d

# 4. 验证服务
openviking-server doctor
```

### 2.2 OpenViking Skill 实现

```python
# harness/skills/openviking_memory_skill.py

class OpenVikingMemorySkill(BaseSkill):
    """
    OpenViking 记忆 Skill
    提供完整的上下文数据库能力
    """
    
    @property
    def name(self) -> str:
        return "openviking_memory"
    
    def __init__(self):
        self.feature_sdk = FeatureSDK()
        self.viking_client = self._init_viking_client()
    
    def _init_viking_client(self):
        """初始化 OpenViking 客户端"""
        try:
            import openviking
            client = openviking.Client()
            return client
        except ImportError:
            logger.warning("OpenViking 未安装，OpenViking 模式不可用")
            return None
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """执行记忆操作"""
        if not self.viking_client:
            return SkillResult(False, {}, "OpenViking 客户端未初始化")
        
        action = inputs.get("action", "retrieve")
        
        if action == "store":
            return self._store_memory(inputs)
        elif action == "retrieve":
            return self._retrieve_memory(inputs)
        elif action == "analyze_session":
            return self._analyze_session(inputs)
    
    def _store_memory(self, inputs: Dict) -> SkillResult:
        """存储案例到 OpenViking"""
        
        # 构建 viking:// URI 结构
        uri = self._build_case_uri(inputs)
        
        # L0 摘要 (约100 tokens)
        l0_content = f"""
Bug摘要: {inputs.get('bug_summary')}
类型: {inputs.get('bug_type')}
关键词: {', '.join(inputs.get('tags', []))}
"""
        
        # L1 概览 (约2000 tokens)
        l1_content = f"""
# Bug 案例概览

## 基本信息
- Bug类型: {inputs.get('bug_type')}
- 影响进程: {inputs.get('affected_process')}
- 设备: {inputs.get('device')}
- Android版本: {inputs.get('android_version')}

## 关键日志
{inputs.get('key_logs', [])}

## 分析结论
- 根因: {inputs.get('root_cause')}
- 修复建议: {inputs.get('fix_suggestion')}
- 置信度: {inputs.get('confidence')}

## 标签
{', '.join(inputs.get('tags', []))}
"""
        
        # 存储到 OpenViking (分层)
        self.viking_client.write(uri, content=l0_content, level="L0")
        self.viking_client.write(uri, content=l1_content, level="L1")
        
        if inputs.get("include_l2"):
            self.viking_client.write(uri, content=inputs.get("l2_full"), level="L2")
        
        return SkillResult(True, {"uri": uri}, "案例已存储到 OpenViking")
    
    def _retrieve_memory(self, inputs: Dict) -> SkillResult:
        """从 OpenViking 检索案例"""
        
        query = inputs.get("query")
        level = inputs.get("level", "L1")  # L0 | L1 | L2
        
        # 使用目录递归检索
        results = self.viking_client.find(
            query=query,
            path="viking://agent/case_library/",
            level=level,
            max_results=inputs.get("top_k", 3)
        )
        
        return SkillResult(True, {
            "results": results,
            "level": level,
            "mode": "openviking"
        }, f"检索到 {len(results)} 个案例")
    
    def _analyze_session(self, inputs: Dict) -> SkillResult:
        """分析当前会话，更新记忆"""
        
        # 1. 压缩会话内容
        session_summary = self.viking_client.abstract(
            inputs.get("conversation")
        )
        
        # 2. 提取关键信息
        key_findings = self.viking_client.extract(
            session_summary,
            keys=["root_cause", "fix_suggestion", "new_questions"]
        )
        
        # 3. 更新长期记忆
        if key_findings:
            self.viking_client.commit(
                session_id=inputs.get("session_id"),
                summary=session_summary,
                key_findings=key_findings
            )
        
        return SkillResult(True, {
            "summary": session_summary,
            "findings": key_findings
        }, "会话已分析并更新记忆")
    
    def _build_case_uri(self, inputs: Dict) -> str:
        """构建 viking:// URI"""
        bug_type = inputs.get("bug_type", "unknown")
        case_id = inputs.get("case_id", uuid.uuid4().hex[:8])
        date = datetime.now().strftime("%Y/%m")
        
        return f"viking://agent/case_library/{bug_type}/{date}/{case_id}"
```

---

## 🔄 防僵化机制实现

### 3.1 核心逻辑

```python
# harness/skills/anti_rigidity_skill.py

class AntiRigiditySkill(BaseSkill):
    """
    防僵化 Skill
    确保 Agent 不会机械套用历史结论
    """
    
    @property
    def name(self) -> str:
        return "anti_rigidity"
    
    def execute(self, inputs: Dict[str, Any]) -> SkillResult:
        """
        执行防僵化检查
        """
        similar_cases = inputs.get("similar_cases", [])
        current_analysis = inputs.get("current_analysis", {})
        
        # 1. 强制差异对比
        differences = self._find_differences(similar_cases, current_analysis)
        
        # 2. 要求证据验证
        evidence_validation = self._validate_evidence(current_analysis)
        
        # 3. 检测未解释项
        unexplained = self._find_unexplained(current_analysis)
        
        # 4. 检查历史结论有效性
        outdated = self._check_outdated_cases(similar_cases)
        
        result = {
            "differences": differences,
            "evidence_validation": evidence_validation,
            "unexplained": unexplained,
            "outdated_cases": outdated,
            "rigidity_score": self._calculate_rigidity_score(
                differences, evidence_validation, unexplained
            )
        }
        
        # 如果僵化风险高，给出警告
        if result["rigidity_score"] > 0.7:
            result["warning"] = "检测到可能的僵化风险，请重新审视差异"
        
        return SkillResult(True, result, "防僵化检查完成")
    
    def _find_differences(self, cases: List[Dict], current: Dict) -> List[str]:
        """
        找出当前分析与历史案例的差异
        """
        differences = []
        
        for case in cases:
            # 设备差异
            if case.get("device") != current.get("device"):
                differences.append(f"设备不同: {case.get('device')} vs {current.get('device')}")
            
            # Android 版本差异
            if case.get("android_version") != current.get("android_version"):
                differences.append(f"Android版本不同: {case.get('android_version')} vs {current.get('android_version')}")
            
            # 日志模式差异 (使用 aloggrep histogram)
            if case.get("log_histogram") != current.get("log_histogram"):
                differences.append("日志分布模式存在差异，可能需要新分析")
        
        return differences
    
    def _validate_evidence(self, analysis: Dict) -> Dict:
        """
        验证分析是否有足够的日志证据支撑
        """
        evidence_count = len(analysis.get("cited_logs", []))
        has_stack_trace = bool(analysis.get("stack_trace"))
        has_timeline = bool(analysis.get("timeline"))
        
        return {
            "evidence_count": evidence_count,
            "has_stack_trace": has_stack_trace,
            "has_timeline": has_timeline,
            "is_evidence_sufficient": evidence_count >= 3 and has_stack_trace
        }
    
    def _find_unexplained(self, analysis: Dict) -> List[str]:
        """
        找出分析中未解释的异常或线索
        """
        unexplained = []
        
        # 检测 histogram 中的异常峰值
        histogram = analysis.get("log_histogram", {})
        for tag, count in histogram.items():
            if count > histogram.get("avg", 0) * 3:
                unexplained.append(f"日志量异常: {tag} 出现 {count} 次，超出平均值3倍")
        
        return unexplained
    
    def _check_outdated_cases(self, cases: List[Dict]) -> List[Dict]:
        """
        检查历史案例是否过时
        """
        outdated = []
        current_date = datetime.now()
        threshold = timedelta(days=180)  # 180天前的案例标记为过时
        
        for case in cases:
            case_date = datetime.fromisoformat(case.get("created_at"))
            if current_date - case_date > threshold:
                outdated.append({
                    "case_id": case.get("case_id"),
                    "age_days": (current_date - case_date).days,
                    "reason": "案例超过6个月，可能不适用于当前系统版本"
                })
        
        return outdated
    
    def _calculate_rigidity_score(self, differences: List, validation: Dict, unexplained: List) -> float:
        """
        计算僵化风险分数 (0-1)
        越高表示越可能存在机械套用
        """
        score = 0.0
        
        # 差异多但未提及 -> 高风险
        if len(differences) > 3 and not validation.get("is_evidence_sufficient"):
            score += 0.4
        
        # 未解释项多 -> 中风险
        if len(unexplained) > 2:
            score += 0.3
        
        # 证据不足 -> 中风险
        if not validation.get("is_evidence_sufficient"):
            score += 0.3
        
        return min(score, 1.0)
```

---

## 🔧 Agent 集成

### 4.1 技能注册 (harness_agent_advanced.py)

```python
def _register_skills(self):
    """根据 Feature Flag 注册可插拔技能"""
    
    # ... 现有代码 ...
    
    # 记忆系统 (根据模式选择)
    if self.feature_sdk.is_enabled("memory_system_enabled"):
        
        memory_mode = self.feature_sdk.get_variant("memory_mode")
        
        if memory_mode == "simple":
            # MVP 模式
            self.orchestrator.register_skill(CaseLibrarySkill())
            print("  ✅ CaseLibrarySkill (简单模式)")
            
        elif memory_mode == "openviking":
            # OpenViking 模式
            self.orchestrator.register_skill(OpenVikingMemorySkill())
            print("  ✅ OpenVikingMemorySkill (完整模式)")
        
        # 防僵化机制
        if self.feature_sdk.is_enabled("anti_rigidity_enabled"):
            self.orchestrator.register_skill(AntiRigiditySkill())
            print("  ✅ AntiRigiditySkill (已启用)")
```

### 4.2 工作流集成

```python
# 分析工作流中的使用

class AnalysisWorkflow:
    """
    增强的分析工作流
    """
    
    def execute(self, inputs):
        # 1. 日志预处理 (aloggrep)
        log_data = self._preprocess_logs(inputs)
        
        # 2. L0/L1 摘要生成
        l0_summary = aloggrep.summary(log_data)
        l1_overview = aloggrep.crashes(log_data)
        
        # 3. 知识检索 (QMD)
        knowledge = self._query_knowledge(inputs)
        
        # 4. 相似案例检索 (根据模式)
        if memory_system_enabled:
            if similar_case_retrieval:
                similar_cases = self._retrieve_similar_cases(
                    query=inputs.get("bug_description"),
                    bug_type=inputs.get("bug_type")
                )
                
                # 5. 防僵化检查
                if anti_rigidity_enabled:
                    anti_rigidity_check = self._check_anti_rigidity(
                        similar_cases,
                        current_analysis
                    )
        
        # 6. LLM 分析
        analysis = self._llm_analyze(
            l0=l0_summary,
            l1=l1_overview,
            knowledge=knowledge,
            similar_cases=similar_cases if similar_case_retrieval else None,
            anti_rigidity=anti_rigidity_check if anti_rigidity_enabled else None
        )
        
        # 7. 保存案例
        if auto_save_cases:
            self._save_case(
                l0=l0_summary,
                l1=l1_overview,
                analysis=analysis
            )
        
        return analysis
```

---

## 📊 实施路线图

### Phase 1: MVP 验证 (Week 1-2)
- [ ] 实现 CaseLibrarySkill
- [ ] 实现基础 L0/L1 生成 (aloggrep 集成)
- [ ] 实现简单相似案例检索
- [ ] Feature Flag 配置
- [ ] 单元测试

### Phase 2: OpenViking 准备 (Week 3-4)
- [ ] 学习 OpenViking API
- [ ] 本地部署 OpenViking 服务
- [ ] 设计 viking:// URI 结构
- [ ] 实现 OpenViking 客户端

### Phase 3: OpenViking 集成 (Week 5-6)
- [ ] 实现 OpenVikingMemorySkill
- [ ] 并行查询测试
- [ ] 性能对比
- [ ] 灰度发布

### Phase 4: 防僵化机制 (Week 7-8)
- [ ] 实现 AntiRigiditySkill
- [ ] aloggrep histogram 集成
- [ ] 失效标记机制
- [ ] 用户反馈收集

### Phase 5: 优化与闭环 (Week 9-10)
- [ ] 案例质量评估
- [ ] 检索算法优化
- [ ] 自动化案例审核
- [ ] 完整文档

---

## 🎯 验收标准

### MVP 阶段
- [ ] 能够保存和检索案例
- [ ] Token 消耗降低 30%+
- [ ] 相似案例检索准确率 > 70%

### OpenViking 阶段
- [ ] 分层加载正常工作
- [ ] Token 消耗降低 70%+
- [ ] 检索延迟 < 500ms

### 防僵化阶段
- [ ] 差异对比强制执行
- [ ] 过时案例自动标记
- [ ] Agent 不机械套用历史结论

---

## 📚 参考资料

- [OpenViking GitHub](https://github.com/volcengine/OpenViking)
- [OpenViking 文档](https://openviking.ai/)
- [aloggrep 命令参考](file:///workspace/.claude/skills/loggrep-analyzer/references/commands.md)

