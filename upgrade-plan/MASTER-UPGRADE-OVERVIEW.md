# Nanobot v0.2.0 综合升级方案总览

> **版本**: v0.2.0
> **开始日期**: 2026-02-09
> **预计完成**: 2026-02-19
> **总工期**: 约 10 天

---

## 📋 升级概览

本次升级旨在全面提升 Nanobot 系统的能力和架构，包括提示词系统、任务管理、意图识别等多个核心模块。

### 🎌 核心升级方向

1. **提示词系统重构** - 渐进式上下文披露 + 钩子系统
2. **动态任务管理** - Task Manager + 消息路由 + Cron 系统
3. **意图识别升级** - 三层综合识别（规则 + 代码 + LLM）
4. **上下文监控** - 自动压缩 + 阈值触发

### 🎯 预期成果

- ✅ 更强大的提示词管理能力
- ✅ 灵活的任务协调和监控
- ✅ 准确的意图识别
- ✅ 高效的上下文管理
- ✅ 完善的 TDD 测试覆盖

---

## 📁 升级方案文档

### 1. 综合升级计划

**文档**: `upgrade-plan/COMPREHENSIVE-UPGRADE-PLAN.md`

**内容概要**:
- 提示词和任务管理并行开发策略
- 10 天详细开发时间表
- 验收标准和风险缓解措施

**关键要点**:
```
Week 1 (2.10 - 2.16)
├── Day 1-2: 提示词系统（创建文件）+ 任务管理（创建 TaskManager）
├── Day 3-4: 提示词系统（实现 PromptSystemV2）+ 任务管理（增强子代理）
├── Day 5-6: 提示词系统（更新 ContextBuilder）+ 任务管理（消息路由）
├── Day 7: 提示词系统（迁移内容）+ 任务管理（进度监控）
├── Day 8: 提示词系统（测试）+ 任务管理（Cron 系统）
└── Day 9-10: 集成测试 + 部署验证
```

---

### 2. 提示词系统升级

**文档**: `upgrade-plan/PROMPT-SYSTEM-UPGRADE.md`

**内容概要**:
- 渐进式上下文披露机制
- 分层加载策略（core → workspace → user → memory → decisions）
- 13 个提示词文件的详细设计

**核心架构**:
```
config/prompts/
├── core/           # 核心提示词（必需）
│   ├── identity.md
│   ├── soul.md
│   ├── tools.md
│   └── heartbeat.md
├── workspace/      # 工作区提示词
│   ├── agents.md
│   └── practices.md
├── user/           # 用户相关
│   ├── profile.md
│   └── preferences.md
├── memory/         # 记忆提示词
│   └── memory.md
├── decisions/      # 决策提示词
│   ├── task_analysis.md
│   ├── skill_selection.md
│   └── agent_selection.md
└── config.yaml     # 加载配置
```

**验收标准**:
- [ ] `config/prompts/` 目录结构完整
- [ ] PromptSystemV2 类实现完整
- [ ] MainAgent 和 Subagent 正确加载提示词
- [ ] Workspace 文件可以覆盖内置提示词
- [ ] 缓存机制工作正常
- [ ] 向后兼容旧版本 workspace 文件

---

### 3. 渐进式上下文披露分析

**文档**: `upgrade-plan/PROGRESSIVE-DISCLOSURE-ANALYSIS.md`

**内容概要**:
- OpenClaw 三层披露模式详解
- Nanobot 需要的所有提示词文件完整模板
- 配置文件设计

**三层披露模式**:
```
Layer 1 - 基础层（必需）
├── AGENTS.md - 工作区配置
├── USER.md - 用户画像
├── SOUL.md - 系统人设
└── IDENTITY.md - 系统身份

Layer 2 - 条件层（情境）
└── MEMORY.md - 仅 main session 加载

Layer 3 - 扩展层（动态）
├── Skills - Metadata（始终）+ Full Content（按需）
└── Context - 智能压缩，保留最新
```

---

### 4. 提示词系统钩子

**文档**: `upgrade-plan/PROMPT-SYSTEM-HOOKS.md`

**内容概要**:
- 三种钩子类型（配置加载、提示词构建、Agent 初始化）
- HookSystem 核心类设计
- 8 个钩子接口定义

**钩子类型**:
| 钩子名称 | 触发时机 |
|---------|---------|
| on_config_loaded | 配置文件加载完成 |
| on_prompts_loaded | 所有提示词加载完成 |
| on_layer_loaded | 单个提示词层加载完成 |
| on_main_agent_prompt_built | MainAgent 提示词构建完成 |
| on_subagent_prompt_built | Subagent 提示词构建完成 |
| on_prompt_ready | 任意提示词构建完成 |
| on_agent_initialized | Agent 初始化完成 |
| on_agent_ready | Agent 准备好接收消息 |

**核心类**:
```python
class HookSystem:
    def register(hook_name: str, callback: Callable)
    def trigger(hook_name: str, **kwargs)
    def unregister(hook_name: str, callback: Callable)
```

**验收标准**:
- [ ] HookSystem 类实现
- [ ] 8 个钩子接口正常工作
- [ ] 默认钩子自动注册
- [ ] 支持自定义钩子
- [ ] 钩子异常不影响主流程

---

### 5. 上下文监控钩子

**文档**: `upgrade-plan/CONTEXT-MONITOR-HOOKS.md`

**内容概要**:
- 上下文监控器设计
- 60% 阈值自动触发压缩
- 两个核心钩子（压缩前/压缩后）

**核心功能**:
```python
class ContextMonitor:
    def __init__(
        context_compressor,
        max_tokens: int = 128000,
        threshold_percent: float = 0.6,  # 60% 阈值
        hooks: Optional[HookSystem] = None
    ):
    
    def check_and_compress(messages) -> List[Dict]:
        """检查并压缩上下文"""
        current_tokens = self._count_tokens(messages)
        
        if current_tokens >= self.threshold:
            # 触发压缩前钩子
            self.hooks.trigger("before_context_compression", ...)
            
            # 执行压缩
            compressed = self._compress_messages(messages)
            
            # 触发压缩后钩子
            self.hooks.trigger("after_context_compression", ...)
            
            return compressed
        
        return messages
```

**钩子列表**:
| 钩子名称 | 参数 | 用途 |
|---------|------|------|
(压缩前 | current_tokens, max_tokens, threshold | 记录日志、分析模式 |
(压缩后 | original_count, compressed_count, compression_ratio | 记录统计、发送通知 |

**验收标准**:
- [ ] ContextMonitor 类实现
- [ ] Token 计数准确
- [ ] 60% 阈值正确触发
- [ ] 集成 ContextCompressorV2
- [ ] 钩子正常工作
- [ ] 统计信息准确

---

### 6. 意图识别系统升级

**文档**: `upgrade-plan/INTENT-RECOGNITION-UPGRADE.md`

**内容概要**:
- 三层综合识别架构
- 固定规则、代码逻辑、大模型识别
- HybridIntentRecognizer 统一接口

**三层架构**:
```
用户输入
    ↓
Layer 1: 固定规则（优先级 1）
├── 精确匹配
├── 正则表达式
└── 命令关键词
    ↓ 匹配成功 → 直接返回
    ↓ 匹配失败
Layer 2: 代码逻辑（优先级 2）
├── 状态检查
├── 上下文分析
└── 多条件组合
    ↓ 匹配成功 → 直接返回
    ↓ 匹配失败
Layer 3: 大模型（优先级 3）
├── 意图分类
├── 实体提取
└── 多意图识别
    ↓
返回识别结果
```

**核心组件**:
| 识别器 | 速度 | 准确率 | 适用场景 |
|--------|------|--------|---------|
| RuleBasedRecognizer | 极快 | 100% | 明确命令 |
| CodeBasedRecognizer | 快 | 90% | 状态检查 |
| LLMRecognizer | 慢 | 85% | 语义理解 |

**验收标准**:
- [ ] 三层识别器实现
- [ ] 优先级机制正确
- [ ] 固定规则匹配准确
- [ ] 代码逻辑上下文感知
- [ ] 大模型识别语义准确
- [ ] 集成到 Gateway
- [ ] 性能和准确率达标

---

## 🚀 开发策略和流程

### 📌 基本原则

1. **TDD 驱动开发** - 先写测试，再写实现
2. **Code Agent + Opencode** - 使用专业的编码工具
3. **方案先行确认** - 每个 subagent 任务先完善方案并与 claw 核对
4. **并行独立推进** - 提示词系统和任务管理可并行开发

### 🔄 Subagent 方案确认流程

**Step 1: 方案完善（在独立 Session 中）**
```
1. 开启新的 isolated session
2. 载入必要信息（设计文档、现有代码）
3. 使用 skill-review 分析方案
4. 与 claw 交互讨论细节
5. 完善方案并保存到文件
6. 关闭 session
```

**Step 2: 用户确认**
```
1. 向用户展示完善后的方案
2. 说明实现要点和风险
3. 等待用户确认或修改
4. 确认后进入开发阶段
```

**Step 3: 开发实现（使用 Code Agent）**
```
1. 使用 opencode 启动编码会话
2. 按照 TDD 流程开发：
   a. 编写测试用例
   b. 运行测试（失败）
   c. 编写实现代码
   d. 运行测试（通过）
   e. 重构优化
3. 提交代码
4. 生成覆盖率报告
```

---

## 📅 分阶段实施计划

### Phase 1: 方案确认和准备（Day 1）

**任务清单**:
- [ ] 使用 subagent 完善提示词系统方案
- [ ] 使用 subagent 完善任务管理方案
- [ ] 使用 subagent 完善意图识别方案
- [ ] 与用户确认所有方案
- [ ] 创建开发分支

**Subagent 任务 1: 完善提示词系统方案**
```python
{
    "task": "分析并完善提示词系统升级方案",
    "context": {
        "documents": [
            "upgrade-plan/PROMPT-SYSTEM-UPGRADE.md",
            "upgrade-plan/PROGRESSIVE-DISCLOSURE-ANALYSIS.md",
            "upgrade-plan/PROMPT-SYSTEM-HOOKS.md"
        ],
        "existing_code": [
            "nanobot/agent/prompt_builder.py",
            "nanobot/agent/context.py"
        ]
    },
    "deliverables": [
        "prompts-plan-refined.md",
        "implementation-checklist.md"
    ]
}
```

**Subagent 任务 2: 完善任务管理方案**
```python
{
    "task": "分析并完善任务管理系统升级方案",
    "context": {
        "documents": [
            "upgrade-plan/UPGRADE-PLAN.md",
            "upgrade-plan/ENHANCED-CRON.md"
        ],
        "existing_code": [
            "nanobot/agent/task_manager.py",
            "nanobot/agent/task.py"
        ]
    },
    "deliverables": [
        "task-management-plan-refined.md",
        "implementation-checklist.md"
    ]
}
```

**Subagent 任务 3: 完善意图识别方案**
```python
{
    "task": "分析并完善意图识别系统升级方案",
    "context": {
        "documents": [
            "upgrade-plan/INTENT-RECOGNITION-UPGRADE.md"
        ],
        "existing_code": [
            "nanobot/gateway.py",
            "nanobot/agent/decision"
        ]
    },
    "deliverables": [
        "intent-recognition-plan-refined.md",
        "implementation-checklist.md"
    ]
}
```

---

### Phase 2: 提示词系统开发（Day 2-5）

#### Day 2: 创建提示词文件结构

**任务清单**:
- [ ] 创建 `config/prompts/` 目录结构
- [ ] 创建所有核心提示词文件（13 个）
- [ ] 编写文件结构验证测试

**使用 Opencode**:
```bash
# 启动 opencode 编码会话
opencode --model glm-4.7 --project nanobot

# TDD 流程：
# 1. 编写测试
tests/test_prompt_system_structure.py
  ├── test_core_prompts_exist()
  ├── test_workspace_prompts_exist()
  ├── test_user_prompts_exist()
  └── test_config_file_valid()

# 2. 创建文件
config/prompts/core/identity.md
config/prompts/core/soul.md
config/prompts/core/tools.md
...

# 3. 运行测试
pytest tests/test_prompt_system_structure.py -v

# 4. 修复问题并重测
```

#### Day 3-4: 实现 PromptSystemV2 类

**任务清单**:
- [ ] 实现 HookSystem 类
- [ ] 实现 PromptSystemV2 核心功能
- [ ] 实现分层加载逻辑
- [ ] 实现覆盖机制
- [ ] 编写单元测试

**TDD 流程**:
```python
# tests/test_prompt_system_v2.py

class TestPromptSystemV2:
    def test_init(self):
        """测试初始化"""
        system = PromptSystemV2(config_path, workspace)
        assert system.config is not None
        assert system.hooks is not None
    
    def test_load_config(self):
        """测试配置加载"""
        system = PromptSystemV2(config_path, workspace)
        assert "layers" in system.config
        assert "templates" in system.config
    
    def test_build_main_agent_prompt(self):
        """测试 MainAgent 提示词构建"""
        prompt = system.build_main_agent_prompt(context, tools, skills)
        assert "identity" in prompt
        assert "soul" in prompt
        assert len(prompt) < 10000  # 检查长度
    
    def test_build_subagent_prompt(self):
        """测试 Subagent 提示词构建"""
        prompt = system.build_subagent_prompt(task, workspace, skills)
        assert "task_description" in prompt
        assert "workspace" in prompt
    
    def test_layer_override(self):
        """测试覆盖机制"""
        # 实现 workspace 文件覆盖测试
```

#### Day 5: 集成到 ContextBuilder

**任务清单**:
- [ ] 修改 ContextBuilder 使用 PromptSystemV2
- [ ] 更新 MainAgent 初始化流程
- [ ] 编写集成测试
- [ ] 测试向后兼容

---

### Phase 3: 任务管理系统开发（Day 2-6）

**并行开发，与提示词系统独立**

#### Day 2: 创建 TaskManager

**任务清单**:
- [ ] 实现 Task 数据模型
- [ ] 实现 TaskManager 核心功能
- [ ] 实现任务状态跟踪
- [ ] 编写单元测试

**TDD 流程**:
```python
# tests/test_task_manager.py

class TestTaskManager:
    def test_create_task(self):
        """测试创建任务"""
        task = await task_manager.create_task(message, channel)
        assert task.id is not None
        assert task.status == "pending"
    
    def test_update_task_status(self):
        """测试更新任务状态"""
        task = await task_manager.update_status(task_id, "running")
        assert task.status == "running"
    
    def test_get_running_tasks(self):
        """测试获取运行中任务"""
        tasks = await task_manager.get_running_tasks()
        assert all(t.status == "running" for t in tasks)
```

#### Day 3-4: 增强子代理管理

**任务清单**:
- [ ] 修改 SubagentManager 支持任务跟踪
- [ ] 实现进度汇报机制
- [ ] 实现任务修正接口
- [ ] 编写集成测试

#### Day 5-6: 消息路由和 Cron 系统

**任务清单**:
- [ ] 实现 MessageAnalyzer
- [ ] 实现 MessageRouter
- [ ] 实现可配置 Cron 系统
- [ ] 编写端到端测试

---

### Phase 4: 上下文监控开发（Day 6-7）

#### Day 6: 实现 ContextMonitor

**任务清单**:
- [ ] 实现 ContextMonitor 类
- [ ] 实现 token 计数
- [ ] 实现阈值检查
- [ ] 编写单元测试

**TDD 流程**:
```python
# tests/test_context_monitor.py

class TestContextMonitor:
    def test_init(self):
        """测试初始化"""
        monitor = ContextMonitor(compressor, max_tokens=128000, threshold=0.6)
        assert monitor.threshold == 76800  # 128000 * 0.6
    
    def test_no_compression_under_threshold(self):
        """测试阈值下不压缩"""
        messages = create_small_messages()  # 50000 tokens
        result = monitor.check_and_compress(messages)
        assert len(result) == len(messages)  # 不变
    
    def test_compression_above_threshold(self):
        """测试阈值上压缩"""
        messages = create_large_messages()  # 80000 tokens
        result = monitor.check_and_compress(messages)
        assert len(result) < len(messages)  # 压缩了
    
    def test_hook_triggering(self):
        """测试钩子触发"""
        hooks_triggered = []
        
        def hook(**kwargs):
            hooks_triggered.append(kwargs["hook_name"])
        
        monitor.hooks.register("after_context_compression", hook)
        monitor.check_and_compress(large_messages)
        
        assert "after_context_compression" in hooks_triggered
```

#### Day 7: 集成到 Agent Loop

**任务清单**:
- [ ] 修改 AgentLoop 集成 ContextMonitor
- [ ] 在 process_message 中自动检查
- [ ] 编写集成测试
- [ ] 测试多模态消息

---

### Phase 5: 意图识别开发（Day 7-9）

#### Day 7: 实现三层识别器

**任务清单**:
- [ ] 实现 RuleBasedRecognizer
- [ ] 实现 CodeBasedRecognizer
- [ ] 实现 LLMRecognizer
- [ ] 编写单元测试

**TDD 流程**:
```python
# tests/test_intent_recognizers.py

class TestRuleBasedRecognizer:
    def test_exact_match(self):
        """测试精确匹配"""
        intent = await recognizer.recognize("/status")
        assert intent.type == IntentType.STATUS
        assert intent.confidence == 1.0
    
    def test_no_match(self):
        """测试不匹配"""
        intent = await recognizer.recognize("随便说点什么")
        assert intent is None

class TestLLMRecognizer:
    def test_semantic_recognition(self):
        """测试语义识别"""
        intent = await recognizer.recognize(
            "这个代码看起来有点乱，能帮我优化一下吗？"
        )
        assert intent.type in [IntentType.CODE_REFACTORING, IntentType.CODE_ANALYSIS]
        assert intent.confidence > 0.7
```

#### Day 8: 实现综合识别器

**任务清单**:
- [ ] 实现 HybridIntentRecognizer
- [ ] 实现优先级机制
- [ ] 实现降级策略
- [ ] 编写集成测试

#### Day 9: 集成到 Gateway

**任务清单**:
- [ ] 修改 Gateway 使用 HybridIntentRecognizer
- [ ] 实现意图到方法的映射
- [ ] 编写端到端测试
- [ ] 测试性能

---

### Phase 6: 集成测试和验证（Day 10）

**任务清单**:
- [ ] 运行完整测试套件
- [ ] 生成测试覆盖率报告
- [ ] 性能测试（响应时间、资源占用）
- [ ] 集成测试（端到端场景）
- [ ] 验收检查
- [ ] 文档更新

**测试场景**:
```python
# tests/test_integration.py

class TestFullWorkflow:
    async def test_main_agent_initialization(self):
        """测试 MainAgent 初始化"""
        agent = MainAgent(config)
        assert agent.prompt_system is not None
        assert agent.intent_recognizer is not None
    
    async def test_message_processing_flow(self):
        """测试完整消息处理流程"""
        # 用户输入 → 意图识别 → MainAgent 处理 → 返回结果
        response = await gateway.handle_message("分析这个项目")
        assert "analysis" in response.lower()
    
    async def test_context_compression(self):
        """测试上下文压缩"""
        # 发送大量消息，触发压缩
        for i in range(100):
            await gateway.handle_message(f"Message {i}")
        
        # 验证上下文被压缩
        stats = agent.context_monitor.get_stats()
        assert stats["compressions_triggered"] > 0
    
    async def test_task_creation_and_execution(self):
        """测试任务创建和执行"""
        # 发送复杂任务，应创建 Subagent
        response = await gateway.handle_message("重构整个项目的代码")
        
        # 验证任务被创建
        tasks = await agent.task_manager.get_all_tasks()
        assert len(tasks) > 0
```

---

## ✅ 验收标准

### 系统功能

- [ ] 提示词系统正常工作
  - [ ] 所有提示词文件正确加载
  - [ ] MainAgent 和 Subagent 提示词正确
  - [ ] Workspace 文件可以覆盖内置文件
  - [ ] 缓存机制正常

- [ ] 任务管理系统正常工作
  - [ ] TaskManager 创建和跟踪任务
  - [ ] 子代理管理器增强正常
  - [ ] 消息路由准确
  - [ ] Cron 任务按计划执行

- [ ] 意图识别系统正常工作
  - [ ] 固定规则匹配准确
  - [ ] 代码逻辑上下文感知
  - [ ] 大模型语义识别准确
  - [ ] 三层优先级正确

- [ ] 上下文监控正常工作
  - [ ] 60% 阈值触发压缩
  - [ ] 钩子正常触发
  - [ ] 统计信息准确
  - [ ] 多模态消息支持

### 测试质量

- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过
- [ ] 端到端测试通过
- [ ] 性能测试达标
- [ ] 无 P0/P1 级别 bug

### 文档质量

- [ ] API 文档完整
- [ ] 配置说明清晰
- [ ] 升级指南完善
- [ ] 示例代码正确

---

## 🛠️ 风险和缓解措施

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 提示词系统影响性能 | 中等 | 中 | 使用缓存，限制加载频率 |
| 任务管理器状态不一致 | 高 | 低 | 使用锁和事务，定期同步 |
| 意图识别准确率不足 | 中等 | 中 | 提供手动修正选项，持续优化 |
| 上下文压缩丢失重要信息 | 高 | 低 | 保留最近消息，提供压缩预览 |
| 并行开发接口不一致 | 中等等 | 中 | 频繁同步，明确接口契约 |

---

## 📚 相关资源

### 设计文档

1. `upgrade-plan/COMPREHENSIVE-UPGRADE-PLAN.md` - 综合升级计划
2. `upgrade-plan/PROMPT-SYSTEM-UPGRADE.md` - 提示词系统升级
3. `upgrade-plan/PROGRESSIVE-DISCLOSURE-ANALYSIS.md` - 渐进式上下文披露分析
4. `upgrade-plan/PROMPT-SYSTEM-HOOKS.md` - 提示词系统钩子
5. `upgrade-plan/CONTEXT-MONITOR-HOOKS.md` - 上下文监控钩子
6. `upgrade-plan/INTENT-RECOGNITION-UPGRADE.md` - 意图识别系统升级
7. `upgrade-plan/UPGRADE-PLAN.md` - 任务管理系统方案
8. `upgrade-plan/ENHANCED-CRON.md` - 增强版 Cron 系统

### 配置文件

1. `upgrade-plan/cron-job-config-enhanced.json` - Cron 任务配置

### 参考系统

1. OpenClaw 提示词架构
2. Agno 框架设计
3. Claude Code 编码工具

---

## 🎯 下一步行动

### 立即开始

1. ✅ **方案确认** - 使用 subagent 完善三个核心方案
2. ⏳ **用户确认** - 向用户展示完善后的方案，等待确认
3. ⏳ **分支创建** - 创建 `upgrade/v0.2.0` 分支
4. ⏳ **开始开发** - 按照 Phase 2-6 逐步实施

### 开发顺序

```
Phase 1 (Day 1): 方案确认和准备
    ↓
Phase 2 (Day 2-5): 提示词系统开发
  ├─ 创建文件结构
  ├─ 实现 PromptSystemV2
  └─ 集成到 ContextBuilder
    ↓
Phase 3 (Day 2-6): 任务管理系统开发（并行）
  ├─ 创建 TaskManager
  ├─ 增强子代理
  └─ 消息路由和 Cron
    ↓
Phase 4 (Day 6-7): 上下文监控开发
  ├─ 实现 ContextMonitor
  └─ 集成到 Agent Loop
    ↓
Phase 5 (Day 7-9): 意图识别开发
  ├─ 实现三层识别器
  ├─ 实现综合识别器
  └─ 集成到 Gateway
    ↓
Phase 6 (Day 10): 集成测试和验证
    ↓
发布 v0.2.0
```

---

## 📞 需要用户确认

在开始开发之前，请确认：

1. **升级方向** - 本次升级的 4 个核心方向是否符合预期？
2. **开发策略** - 使用 TDD + Code Agent + Opencode 是否认可？
3. **时间安排** - 10 天工期是否合理？
4. **并行开发** - 提示词系统和任务管理并行推进是否可行？
5. **风险接受** - 列出的风险和缓解措施是否充分？

**请回复确认或提出修改意见，确认后我们将立即启动 Phase 1。**
