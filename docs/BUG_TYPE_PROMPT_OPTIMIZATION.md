# Bug 类型差异化提示词和输出模板设计

## 📋 文档信息

| 项目 | 说明 |
|------|------|
| 版本 | v1.0 |
| 更新日期 | 2026-05-17 |
| 状态 | **需要实现** |

---

## 🎯 当前问题

| 问题 | 说明 |
|------|------|
| 提示词单一 | 所有 Bug 类型使用相同提示词 |
| 输出模板固定 | 统一输出"问题定位→根因分析→修复建议→预防措施" |
| 缺乏针对性 | Crash/ANR/Memory Leak 需要不同的分析维度 |
| Token 浪费 | 不相关的问题模板也占用 Token |

---

## 📊 Bug 类型分类和差异化需求

### 1. Crash 类 Bug

**特征**:
- 有明确的异常堆栈
- 通常是 Java/Native 崩溃
- 复现率可能较高

**需要重点分析**:
- 堆栈跟踪（找到第一行）
- Crash 类型（ANR/Crash/Tombstone）
- 崩溃线程（主线程/后台线程）
- 崩溃前后的状态变化

**提示词重点**:
```
1. 堆栈分析
   - 找到崩溃的"caused by"
   - 分析具体类和方法
   
2. 崩溃上下文
   - 崩溃时正在执行什么操作
   - 资源状态（内存、文件句柄）
   
3. 根因类型判断
   - 空指针
   - 数组越界
   - 内存溢出
   - 状态不一致
```

**输出模板**:
```markdown
## Crash 分析报告

### 1. 崩溃概要
- 类型: [Java Crash / Native Crash / ANR]
- 异常: [具体异常类型]
- 进程: [包名]
- 线程: [main / BackgroundThread-X]

### 2. 崩溃堆栈分析
```
[第一行堆栈 - 这里是根因]
  at com.example.Activity.method(File.java:123)
  ...
Caused by: NullPointerException
```

### 3. 根因定位
- **直接原因**: [具体说明]
- **间接原因**: [为什么会发生]

### 4. 修复方案
1. [方案1]
2. [方案2]

### 5. 预防检查
- [ ] 代码检查清单
- [ ] 测试用例建议
```

---

### 2. ANR 类 Bug

**特征**:
- 主线程被阻塞
- 超时（Input/Service/Broadcast/ContentProvider）
- 5秒超时阈值

**需要重点分析**:
- ANR 类型（输入分发/服务/广播/Provider）
- 阻塞原因（I/O/锁/计算）
- 主线程状态
- CPU 和 Binder 调用

**提示词重点**:
```
1. ANR 类型判断
   - Input dispatching timed out → UI线程阻塞
   - context bound service → Service onCreate/onStart/onBind 超时
   - broadcast timeout → BroadcastReceiver 执行超时
   
2. 主线程状态分析
   - 主线程在做什么
   - 是否在等待锁
   - 是否在执行 I/O
   
3. 阻塞点定位
   - 找到耗时操作
   - 分析锁竞争
```

**输出模板**:
```markdown
## ANR 分析报告

### 1. ANR 概要
- 类型: [Input / Service / Broadcast / Provider]
- 进程: [包名]
- 耗时: [超过X秒]

### 2. 主线程分析
- 主线程状态: [RUNNING / WAITING / BLOCKED]
- 阻塞原因: [I/O / 锁等待 / 计算密集]
- 等待的锁: [如果有]

### 3. 阻塞点定位
**耗时操作**:
- [操作1]: Xms
- [操作2]: Yms

**关键日志**:
```
[主线程堆栈]
```

### 4. 根因分析
- **直接原因**: [具体说明]
- **代码位置**: [文件:行号]

### 5. 修复方案
1. [方案1 - 将耗时操作移到后台线程]
2. [方案2 - 优化锁使用]

### 6. 预防检查
- [ ] StrictMode 检查
- [ ] 主线程 I/O 检查
```

---

### 3. Memory Leak 类 Bug

**特征**:
- OOM 崩溃
- 内存持续增长
- 可用内存持续下降

**需要重点分析**:
- Leak 类型（Java堆/ Native堆/ File Descriptor）
- Leak 大小和速率
- 内存分配峰值
- GC 日志

**提示词重点**:
```
1. 内存泄漏类型
   - Java堆泄漏: 对象未释放
   - Native堆泄漏: malloc/new 未 free/delete
   - FD泄漏: 文件/套接字未关闭
   
2. GC 分析
   - GC频率是否正常
   - GC后内存是否下降
   - Allocation Tracker 分析
   
3. 泄漏点定位
   - 找到持有大量对象的地方
   - 分析引用链
```

**输出模板**:
```markdown
## Memory Leak 分析报告

### 1. 内存问题概要
- 类型: [Java Heap / Native Heap / FD]
- 泄漏大小: [X MB]
- 泄漏速率: [X MB/hour]

### 2. 内存使用分析
- 当前使用: [X MB]
- 可用内存: [X MB]
- 峰值内存: [X MB]

### 3. GC 日志分析
- GC频率: [正常/异常]
- GC后内存: [是否正常下降]
- Allocation Tracker: [主要分配者]

### 4. 泄漏点定位
**可疑对象**:
- [对象类型1]: [X个实例, Y MB]
- [对象类型2]: [X个实例, Y MB]

**引用链**:
```
[GC Root] → [引用1] → ... → [泄漏对象]
```

### 5. 根因分析
- **直接原因**: [具体说明]
- **常见场景**: [Activity/Fragment/Callback未释放]

### 6. 修复方案
1. [方案1 - 使用WeakReference]
2. [方案2 - onDestroy中清理资源]
3. [方案3 - 使用 LeakCanary 检测]

### 7. 预防检查
- [ ] 内存监控
- [ ] LeakCanary 集成
```

---

### 4. 性能问题类 Bug

**特征**:
- 卡顿/掉帧
- 启动慢
- 响应慢

**需要重点分析**:
- 帧率分析（Choreographer）
- 启动时间拆解
- CPU/GPU 使用
- I/O 操作

**提示词重点**:
```
1. 性能指标
   - 帧率: [平均/最低]
   - 掉帧数: [总掉帧/严重掉帧]
   - 耗时操作: [X ms]
   
2. 瓶颈分析
   - UI线程耗时
   - 渲染耗时
   - I/O等待
   
3. 优化建议
   - 减少布局层级
   - 异步加载
   - 缓存策略
```

**输出模板**:
```markdown
## 性能问题分析报告

### 1. 性能概要
- 问题类型: [卡顿 / 启动慢 / 响应慢]
- 影响范围: [影响用户数]
- 严重程度: [P0/P1/P2]

### 2. 性能指标
| 指标 | 测量值 | 标准值 | 状态 |
|------|--------|--------|------|
| 帧率 | X fps | 60 fps | ❌ |
| 启动时间 | X ms | <1000ms | ❌ |
| 响应时间 | X ms | <100ms | ⚠️ |

### 3. 瓶颈分析
**主要耗时**:
1. [操作1]: X ms
2. [操作2]: Y ms

**调用栈**:
```
[关键堆栈]
```

### 4. 根因分析
- **直接原因**: [具体说明]
- **影响路径**: [从哪到哪]

### 5. 优化方案
1. [方案1 - 具体优化]
2. [方案2 - 具体优化]

### 6. 预期效果
- 帧率: [X fps → Y fps]
- 启动时间: [X ms → Y ms]
```

---

### 5. 网络问题类 Bug

**特征**:
- 请求超时
- 连接失败
- 数据异常

**需要重点分析**:
- 网络类型（WiFi/Mobile）
- 请求/响应详情
- 错误码
- 重试逻辑

**提示词重点**:
```
1. 网络错误类型
   - 超时: connect/read/write timeout
   - 连接失败: connection refused/reset
   - 协议错误: HTTP 4xx/5xx
   
2. 请求分析
   - URL 和参数
   - 请求头
   - 请求体大小
   
3. 响应分析
   - 状态码
   - 响应时间
   - 错误信息
```

**输出模板**:
```markdown
## 网络问题分析报告

### 1. 问题概要
- 错误类型: [超时 / 连接失败 / 数据错误]
- 影响接口: [API路径]
- 错误码: [HTTP Xxx / 自定义码]

### 2. 请求详情
- URL: [完整URL]
- Method: [GET/POST]
- Headers: [关键Header]
- Body: [请求体大小]

### 3. 响应详情
- 状态码: [HTTP xxx]
- 响应时间: [X ms]
- 错误信息: [服务端返回的错误]

### 4. 日志分析
```
[相关网络日志]
```

### 5. 根因分析
- **直接原因**: [具体说明]
- **可能场景**: [服务端问题 / 网络问题 / 客户端问题]

### 6. 修复方案
1. [方案1]
2. [方案2]

### 7. 预防措施
- [ ] 重试机制
- [ ] 降级策略
- [ ] 监控告警
```

---

### 6. 功耗问题类 Bug

**特征**:
- 电池消耗快
- 后台耗电异常
- WakeLock 未释放

**需要重点分析**:
- WakeLock 使用
- 后台服务
- GPS/网络使用
- 传感器使用

**提示词重点**:
```
1. 耗电原因分析
   - WakeLock 持有时长
   - 后台网络请求
   - GPS 使用
   - Alarm 频率
   
2. Battery Stats 分析
   - 各组件耗电
   - 应用耗电排名
```

**输出模板**:
```markdown
## 功耗问题分析报告

### 1. 问题概要
- 问题类型: [后台耗电 / 待机耗电 / 发热]
- 耗电程度: [轻度 / 中度 / 严重]

### 2. Battery Stats 分析
**主要耗电组件**:
| 组件 | 耗电量 | 时长 |
|------|--------|------|
| WiFi | X mAh | Y min |
| GPS | X mAh | Y min |
| CPU | X mAh | Y min |

### 3. WakeLock 分析
- 持有者: [类名]
- 持有时长: [X ms]
- 是否正确释放: [是/否]

### 4. 后台活动分析
**可疑活动**:
- [服务1]: [时长]
- [广播接收器]: [频率]

### 5. 根因分析
- **直接原因**: [具体说明]
- **影响程度**: [X%电池消耗]

### 6. 修复方案
1. [方案1 - 优化WakeLock]
2. [方案2 - 减少后台活动]

### 7. 预防措施
- [ ] Battery Historian 集成
- [ ] 耗电监控
```

---

## 🏗️ 技术实现方案

### 方案 1: Skill 分类（推荐）

创建专门的 Bug 类型分析 Skill：

```
harness/skills/bug_type/
├── __init__.py
├── base_analyzer.py          # 基类
├── crash_analyzer.py         # Crash 分析器
├── anr_analyzer.py           # ANR 分析器
├── memory_analyzer.py        # Memory Leak 分析器
├── performance_analyzer.py   # 性能分析器
└── network_analyzer.py       # 网络分析器
```

### 方案 2: 提示词模板管理器

```python
class PromptTemplateManager:
    """提示词模板管理器"""
    
    TEMPLATES = {
        "crash": {
            "system_prompt": "你是Crash分析专家...",
            "user_prompt": CRASH_TEMPLATE,
            "output_format": "structured_json"
        },
        "anr": {
            "system_prompt": "你是ANR分析专家...",
            "user_prompt": ANR_TEMPLATE,
            "output_format": "structured_json"
        },
        # ...
    }
    
    def get_template(self, bug_type: str) -> Dict:
        return self.TEMPLATES.get(bug_type, self.TEMPLATES["general"])
```

### 方案 3: Feature Flag 控制

```yaml
bug_type_optimization:
  name: "bug_type_optimization"
  description: "启用不同Bug类型的差异化提示词"
  enabled: true  # 默认开启
```

---

## 📊 预期收益

| 维度 | 改善 | 说明 |
|------|------|------|
| 分析准确率 | +15-25% | 针对性提示词让 LLM 更聚焦 |
| Token 消耗 | -20-30% | 只发送相关问题模板 |
| 分析深度 | +30% | 不同类型有不同的分析维度 |
| 用户满意度 | +20% | 报告更专业、更实用 |

---

## 🚀 实施计划

### Phase 1: 基础框架 (1天)
- [ ] 创建 PromptTemplateManager
- [ ] 设计各 Bug 类型提示词模板
- [ ] 实现模板选择逻辑

### Phase 2: 实现分析器 (2天)
- [ ] 实现 CrashAnalyzer
- [ ] 实现 ANRAnalyzer
- [ ] 实现 MemoryAnalyzer

### Phase 3: 完善和测试 (2天)
- [ ] 实现 PerformanceAnalyzer
- [ ] 实现 NetworkAnalyzer
- [ ] 端到端测试

### Phase 4: 上线和监控 (1天)
- [ ] 集成到 Agent
- [ ] 添加 Feature Flag
- [ ] 监控效果

---

## 📝 总结

| 项目 | 当前状态 | 目标 |
|------|---------|------|
| Bug 类型识别 | ✅ 有简单判断 | 完善识别逻辑 |
| 差异化提示词 | ❌ 缺失 | 实现 6 种类型 |
| 输出模板 | ❌ 统一模板 | 6 种专用模板 |
| Token 优化 | ❌ 无优化 | 预计节省 20-30% |

这是一个值得优化的方向，可以显著提升分析质量和效率！
