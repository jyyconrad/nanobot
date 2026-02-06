# Nanobot 主代理与子代理协调架构规划

## 1. 架构概述

### 1.1 职责分离

**Main Agent（主代理）职责：**
- 用户消息接收和初步处理
- 任务识别、规划和分解
- 上下文和记忆管理（动态压缩、智能扩展）
- Subagent 调度和任务分配
- Subagent 执行状态监控
- 下一步动作决策
- 用户响应聚合和总结

**Subagent（子代理）职责：**
- 接收主代理分配的具体任务
- 使用指定的 skills 或加载特定的 agent 执行
- 任务执行和进度报告
- 完成后向主代理报告结果
- 不直接与用户交互

### 1.2 消息流转

```
用户 → Main Agent → [任务规划] → Subagent → [执行] → Main Agent → [决策] → 用户
                            ↓                      ↓                      ↓
                        [进度更新]          [状态报告]        [响应]
```

## 2. 核心组件

### 2.1 组件清单

| 组件 | 职责 | 关键接口 |
|------|------|----------|
| TaskPlanner | 任务分析和规划 | plan(message) → PlanningResult |
| ExecutionDecisionMaker | 执行决策 | decide(trigger, ...) → ExecutionDecision |
| ContextManager | 上下文管理 | build_context(...) → context, stats |
| EnhancedMemoryStore | 增强记忆系统 | add_memory(...), search_memory(...) |
| MainAgent | 主代理协调 | process_message(msg) → response |

### 2.2 数据结构

**PlanningResult:**
```python
{
    "action": str,           # "reply", "delegate", "multi_step", "complete"
    "task_description": str,
    "task_type": str | None,
    "subagent_type": str | None,
    "skills": list[str],
    "agent_type": str | None,
    "estimated_steps": int,
    "confidence": float,
    "reasoning": str
}
```

**ExecutionDecision:**
```python
{
    "action": str,           # "reply", "spawn_subagent", "await_result", "complete_task"
    "message": str | None,
    "subagent_task": str | None,
    "subagent_config": dict,
    "task_id": str | None
}
```

**ContextStats:**
```python
{
    "original_length": int,
    "compressed_length": int,
    "compression_ratio": float
}
```

## 3. 状态流转

### 3.1 任务状态

```
PENDING（待执行）
    ↓
PLANNED（已规划）
    ↓
ASSIGNED（已分配给 Subagent）
    ↓
RUNNING（Subagent 执行中）
    ↓
    ├─→ COMPLETED（完成）
    ├─→ FAILED（失败）
    └─→ CANCELLED（已取消）
```

### 3.2 Main Agent 决策流程

```
接收用户消息
    ↓
[任务规划]
    ├─→ SIMPLE（简单） → 直接回复
    ├─→ MODERATE（适中） → 单 Subagent
    └─→ COMPLEX（复杂） → 多步骤工作流
    ↓
[执行决策]
    ├─→ 回复用户
    ├─→ 分配新任务
    ├─→ 等待结果
    └─→ 完成任务
    ↓
[状态监控] → 循环处理
```

## 4. 关键技术要求

### 4.1 上下文管理

**动态上下文压缩：**
- 对话长时自动压缩旧消息
- 保留关键信息（任务、决定、重要结果）
- 使用 LLM 总结压缩内容

**智能上下文扩展：**
- 根据任务类型加载相关 skills
- 自动加载必要的 agent 配置
- 动态调整上下文窗口大小

**上下文组成：**
1. 基础上下文（不变）：AGENTS.md、TOOLS.md、IDENTITY.md
2. 记忆上下文（动态）：MEMORY.md、最近每日笔记、任务历史摘要
3. 技能上下文（任务相关）：根据任务类型自动加载的 skills
4. 任务上下文（当前任务）：当前任务描述、相关 Subagent 状态

### 4.2 任务规划

**规划策略：**
1. 显式技能：使用用户明确指定的技能
2. 代理类型：加载特定代理类型的技能
3. 任务类型：根据任务类型自动选择相关技能
4. 默认：加载 always skills

**技能映射：**
- coding: ["code-review", "code-refactoring"]
- debugging: ["debug", "code-review"]
- security: ["security-review", "code-review"]
- testing: ["tdd-workflow"]

### 4.3 执行决策

**决策类型：**
- reply：直接回复用户
- spawn_subagent：生成 Subagent 执行任务
- await_result：等待 Subagent 结果
- complete_task：完成任务

**决策触发器：**
- new_message：新用户消息
- subagent_result：Subagent 结果
- task_correction：任务修正
- task_cancellation：任务取消

## 5. 实施阶段和任务清单

**关键要点：**
- 所有代码需遵循 nanobot 代码规范（类型提示、异步、错误处理）
- 新增模块必须有配套单元测试，覆盖率 ≥ 80%
- 使用 Pydantic 定义数据模型，确保类型安全
- 所有接口需要明确的文档字符串

### 5.1 阶段一：上下文管理增强

**关键要点：**
- 实现智能的上下文压缩和扩展策略
- 支持技能动态加载机制
- 增强记忆系统的标签和搜索能力

#### 5.1.1 创建 ContextManager 类

**产物：**
- 代码：`nanobot/agent/context_manager.py`
  - 类：`ContextManager`
  - 接口：
    - `async build_context(session_id: str, task_type: str | None = None) -> tuple[str, ContextStats]`
    - `async compress_context(messages: list[dict]) -> tuple[list[dict], ContextStats]`
    - `async expand_context(context: str, skills: list[str]) -> str`
- 测试：`tests/test_context_manager.py`
  - 单元测试覆盖率 ≥ 85%
  - 测试场景：压缩、扩展、边界条件、错误处理
- 文档：API 文档、使用示例

#### 5.1.2 实现动态上下文压缩

**产物：**
- 代码：`nanobot/agent/context_compressor.py`
  - 类：`ContextCompressor`
  - 接口：
    - `async compress(messages: list[dict], max_tokens: int) -> tuple[list[dict], ContextStats]`
    - `async summarize_messages(messages: list[dict]) -> str`
- 测试：`tests/test_context_compressor.py`
  - 测试覆盖率 ≥ 80%
  - 测试场景：长对话压缩、关键信息保留、总结质量验证

#### 5.1.3 实现智能上下文扩展

**产物：**
- 代码：`nanobot/agent/context_expander.py`
  - 类：`ContextExpander`
  - 接口：
    - `async expand(base_context: str, task_type: str) -> str`
    - `async load_skills(skill_names: list[str]) -> list[str]`
- 测试：`tests/test_context_expander.py`
  - 测试覆盖率 ≥ 80%

#### 5.1.4 实现技能智能加载

**产物：**
- 代码：`nanobot/agent/skill_loader.py`
  - 类：`SkillLoader`
  - 接口：
    - `async load_skills_for_task(task_type: str, explicit_skills: list[str] | None) -> list[str]`
    - `get_task_type_mapping() -> dict[str, list[str]]`
- 配置：`nanobot/config/skill_mapping.yaml`
  - 定义任务类型到技能的映射关系
- 测试：`tests/test_skill_loader.py`

#### 5.1.5 创建 EnhancedMemoryStore 类

**产物：**
- 代码：`nanobot/agent/memory/enhanced_memory.py`
  - 类：`EnhancedMemoryStore`
  - 接口：
    - `async add_memory(content: str, tags: list[str], task_id: str | None) -> str`
    - `async search_memory(query: str, tags: list[str] | None) -> list[Memory]`
    - `async get_task_memories(task_id: str) -> list[Memory]`
- 数据模型：`nanobot/agent/memory/models.py`
  - `Memory`（标签、内容、时间戳、任务关联）
- 测试：`tests/test_enhanced_memory.py`
  - 测试覆盖率 ≥ 85%

### 5.2 阶段二：任务规划系统

**关键要点：**
- 实现基于 LLM 的任务复杂度分析和规划
- 支持任务修正和取消检测
- 清晰的规划结果数据结构

#### 5.2.1 创建 TaskPlanner 类

**产物：**
- 代码：`nanobot/agent/planner/task_planner.py`
  - 类：`TaskPlanner`
  - 接口：
    - `async plan(message: str, history: list[dict]) -> PlanningResult`
- 数据模型：`nanobot/agent/planner/models.py`
  - `PlanningResult`
  - `TaskComplexity`
- 测试：`tests/test_task_planner.py`
  - 测试覆盖率 ≥ 80%

#### 5.2.2 实现任务复杂度分析

**产物：**
- 代码：`nanobot/agent/planner/complexity_analyzer.py`
  - 类：`ComplexityAnalyzer`
  - 接口：
    - `async analyze(message: str, context: str) -> TaskComplexity`
- 测试：`tests/test_complexity_analyzer.py`

#### 5.2.3 实现任务类型检测

**产物：**
- 代码：`nanobot/agent/planner/task_detector.py`
  - 类：`TaskDetector`
  - 接口：
    - `async detect(message: str) -> str`
- 测试：`tests/test_task_detector.py`

#### 5.2.4 实现任务修正检测

**产物：**
- 代码：`nanobot/agent/planner/correction_detector.py`
  - 类：`CorrectionDetector`
  - 接口：
    - `async is_correction(new_message: str, current_task: str) -> bool`
- 测试：`tests/test_correction_detector.py`

#### 5.2.5 实现任务取消检测

**产物：**
- 代码：`nanobot/agent/planner/cancellation_detector.py`
  - 类：`CancellationDetector`
  - 接口：
    - `async is_cancellation(message: str) -> bool`
- 测试：`tests/test_cancellation_detector.py`

### 5.3 阶段三：执行决策系统

**关键要点：**
- 实现灵活的执行决策逻辑
- 支持多种触发器和决策类型
- 与 Subagent 协调工作

#### 5.3.1 创建 ExecutionDecisionMaker 类

**产物：**
- 代码：`nanobot/agent/decision/decision_maker.py`
  - 类：`ExecutionDecisionMaker`
  - 接口：
    - `async decide(trigger: DecisionTrigger, **kwargs) -> ExecutionDecision`
- 数据模型：`nanobot/agent/decision/models.py`
  - `ExecutionDecision`
  - `DecisionTrigger`
- 测试：`tests/test_decision_maker.py`
  - 测试覆盖率 ≥ 80%

#### 5.3.2 实现新消息决策

**产物：**
- 代码：`nanobot/agent/decision/new_message_handler.py`
  - 类：`NewMessageHandler`
  - 接口：
    - `async handle(message: str, planning_result: PlanningResult) -> ExecutionDecision`
- 测试：`tests/test_new_message_handler.py`

#### 5.3.3 实现 Subagent 结果决策

**产物：**
- 代码：`nanobot/agent/decision/subagent_result_handler.py`
  - 类：`SubagentResultHandler`
  - 接口：
    - `async handle(result: SubagentResult) -> ExecutionDecision`
- 测试：`tests/test_subagent_result_handler.py`

#### 5.3.4 实现任务修正决策

**产物：**
- 代码：`nanobot/agent/decision/correction_handler.py`
  - 类：`CorrectionHandler`
  - 接口：
    - `async handle(correction: str, current_task: Task) -> ExecutionDecision`
- 测试：`tests/test_correction_handler.py`

#### 5.3.5 实现任务取消决策

**产物：**
- 代码：`nanobot/agent/decision/cancellation_handler.py`
  - 类：`CancellationHandler`
  - 接口：
    - `async handle(task_id: str) -> ExecutionDecision`
- 测试：`tests/test_cancellation_handler.py`

### 5.4 阶段四：基于 Agno 的 Subagent 实现

**关键要点：**
- 使用最新版本的 Agno 框架
- 实现 Human-in-loop 机制（高风险评估、消息中断）
- Subagent 会话 Hooks 支持

#### 5.4.1 Subagent 基础架构

**产物：**
- 代码：`nanobot/agent/subagent/agno_subagent.py`
  - 类：`AgnoSubagent`
  - 接口：
    - `async execute(task: SubagentTask) -> SubagentResult`
    - `async interrupt(new_message: str) -> bool`
    - `async cancel() -> bool`
- 数据模型：`nanobot/agent/subagent/models.py`
  - `SubagentTask`
  - `SubagentResult`
  - `SubagentState`
- 测试：`tests/test_agno_subagent.py`
  - 测试覆盖率 ≥ 80%

#### 5.4.2 Human-in-loop：高风险操作评估

**产物：**
- 代码：`nanobot/agent/subagent/risk_evaluator.py`
  - 类：`RiskEvaluator`
  - 接口：
    - `async evaluate_risk(action: str) -> RiskLevel`
    - `async request_user_confirmation(action: str) -> bool`
- 集成：通过 ChatChannel 发送确认请求
- 测试：`tests/test_risk_evaluator.py`
  - 测试场景：高风险检测、用户确认流程、超时处理

#### 5.4.3 Human-in-loop：消息中断机制

**产物：**
- 代码：`nanobot/agent/subagent/interrupt_handler.py`
  - 类：`InterruptHandler`
  - 接口：
    - `async handle_new_message(message: str, agent_state: SubagentState) -> InterruptAction`
- 数据模型：
  - `RiskLevel`（none, low, medium, high, critical）
  - `InterruptAction`（continue, modify, cancel）
- 测试：`tests/test_interrupt_handler.py`

#### 5.4.4 Subagent 会话 Hooks

**产物：**
- 代码：`nanobot/agent/subagent/hooks.py`
  - 类：`SubagentHooks`
  - 接口：
    - `on_task_start(task_id: str, description: str)`
    - `on_progress(task_id: str, progress: float)`
    - `on_human_interaction(task_id: str, interaction: HumanInteraction)`
    - `on_complete(task_id: str, result: SubagentResult)`
- 数据模型：
  - `HumanInteraction`
  - `HookEvent`
- 测试：`tests/test_subagent_hooks.py`

### 5.5 阶段五：主代理集成

**关键要点：**
- 创建 MainAgent 核心类
- 集成所有子系统（上下文、规划、决策、Subagent）
- MainAgent 会话 Hooks 支持
- 与现有 AgentLoop 集成（关注流转状态、数据结构、核心业务逻辑、关键实体）

#### 5.5.1 创建 MainAgent 类

**产物：**
- 代码：`nanobot/agent/main_agent.py`
  - 类：`MainAgent`
  - 接口：
    - `async process_message(message: str, session_id: str) -> str`
    - `async _handle_new_message(message: str) -> str`
    - `async _handle_subagent_result(result: SubagentResult) -> str`
    - `async _aggregate_responses() -> str`
- 测试：`tests/test_main_agent.py`
  - 测试覆盖率 ≥ 80%
  - 测试场景：完整消息处理流程、Subagent 协调、错误处理

#### 5.5.2 集成 ContextManager

**产物：**
- 集成代码：在 `MainAgent` 中注入和使用 `ContextManager`
- 测试：验证上下文构建和压缩功能
- 文档：集成模式说明

#### 5.5.3 集成 TaskPlanner

**产物：**
- 集成代码：在 `MainAgent` 中使用 `TaskPlanner`
- 测试：验证任务规划流程
- 文档：规划策略文档

#### 5.5.4 集成 ExecutionDecisionMaker

**产物：**
- 集成代码：在 `MainAgent` 中使用 `ExecutionDecisionMaker`
- 测试：验证决策流程
- 文档：决策逻辑说明

#### 5.5.5 集成 SubagentManager

**产物：**
- 代码：`nanobot/agent/subagent/manager.py`
  - 类：`SubagentManager`
  - 接口：
    - `async spawn_subagent(task: SubagentTask) -> str`
    - `async get_subagent_status(agent_id: str) -> SubagentState`
    - `async cancel_subagent(agent_id: str) -> bool`
- 集成代码：在 `MainAgent` 中使用 `SubagentManager`
- 测试：`tests/test_subagent_manager.py`
  - 测试覆盖率 ≥ 80%

#### 5.5.6 MainAgent 会话 Hooks

**产物：**
- 代码：`nanobot/agent/hooks.py`
  - 类：`MainAgentHooks`
  - 接口：
    - `on_message_receive(message: str, session_id: str) -> HookResult`
    - `before_planning(message: str) -> HookResult`
    - `after_planning(result: PlanningResult) -> None`
    - `before_decision(trigger: DecisionTrigger) -> HookResult`
    - `after_decision(decision: ExecutionDecision) -> None`
    - `on_subagent_spawn(agent_id: str, task: SubagentTask) -> None`
    - `on_response_send(response: str, session_id: str) -> None`
- 数据模型：
  - `HookResult`（allow, block, modify）
- 测试：`tests/test_main_agent_hooks.py`

#### 5.5.7 集成到现有 AgentLoop

**关键关注点：**
- 流转状态：PENDING → PLANNED → ASSIGNED → RUNNING → COMPLETED/FAILED/CANCELLED
- 数据结构：`Task`、`SubagentResult`、`MainAgentState`
- 核心业务逻辑：消息处理流程、Subagent 协调、响应聚合
- 关键实体：MainAgent、SubagentManager、TaskPlanner、ExecutionDecisionMaker

**产物：**
- 代码：修改 `nanobot/agent/agent_loop.py`
  - 集成 `MainAgent`
  - 适配消息流转逻辑
- 测试：`tests/test_agent_loop_integration.py`
  - 集成测试覆盖率 ≥ 75%
- 文档：集成迁移指南

### 5.6 阶段六：配置和文档

**关键要点：**
- 更新配置架构支持新功能
- 完善文档和示例
- 提供清晰的迁移指南

#### 5.6.1 更新配置架构

**产物：**
- 代码：`nanobot/config/schema.py`
  - 新增 `MainAgentConfig`
  - 新增 `ContextConfig`
  - 新增 `SubagentConfig`
- 代码：`nanobot/config/loader.py`
  - 支持新配置加载
- 示例配置：`config/examples/main_agent_config.yaml`
- 测试：`tests/test_config.py`

#### 5.6.2 更新 README.md

**产物：**
- 文档：`README.md`
  - 新增 Main Agent 功能介绍
  - 新增 Human-in-loop 说明
  - 新增使用示例文档

#### 5.6.3 创建迁移指南

**产物：**
- 文档：`docs/MIGRATION_GUIDE.md`
  - 从旧架构迁移步骤
  - 配置迁移指南
  - 常见问题解答

#### 5.6.4 创建架构文档

**产物：**
- 文档：`docs/ARCHITECTURE.md`
  - 系统架构图
  - 组件交互流程
  - 数据流转图
  - 接口说明

#### 5.6.5 创建 API 文档

**产物：**
- 文档：`docs/API.md`
  - 所有公共接口详细说明
  - 参数、返回值、异常说明

### 5.7 阶段七：测试和验证

**关键要点：**
- 单元测试覆盖率 ≥ 80%
- 集成测试覆盖核心流程
- 性能测试和回归测试

#### 5.7.1 单元测试

**产物：**
- 测试：`tests/test_*.py`
  - 所有模块单元测试
  - 测试覆盖率 ≥ 80%
- 文档：测试报告

#### 5.7.2 集成测试

**产物：**
- 测试：`tests/integration/`
  - MainAgent 完整流程测试
  - Subagent 协调测试
  - Human-in-loop 集成测试
- 测试覆盖率 ≥ 75%

#### 5.7.3 性能测试

**产物：**
- 测试：`tests/performance/`
  - 上下文压缩性能
  - 规划和决策响应时间
  - Subagent 并发性能
- 文档：性能基准报告

#### 5.7.4 回归测试

**产物：**
- 测试：`tests/regression/`
  - 确保新功能不破坏现有功能
- 文档：回归测试报告

#### 5.7.5 用户验收测试

**产物：**
- 测试：`tests/acceptance/`
  - 端到端场景测试
  - 真实用例验证
- 文档：验收测试报告

### 5.8 阶段八：部署和发布

**关键要点：**
- 将代码发布到本地 Python 环境
- 提供启动脚本和配置示例
- 文档化部署步骤

#### 5.8.1 发布到本地环境

**产物：**
- 命令：`pip install -e .`
- 验证：安装后功能可用性测试
- 文档：`docs/DEPLOYMENT.md`

#### 5.8.2 创建启动脚本

**产物：**
- 代码：`scripts/start_nanobot.sh`
  - 环境检查（Python 版本、依赖）
  - 配置加载
  - 启动主程序
  - 错误处理和日志输出
- 代码：`scripts/start_dev.sh`
  - 开发模式启动脚本
  - 热重载支持
- 文档：`scripts/README.md`（启动脚本使用说明）

## 6. 验收标准

### 6.1 阶段一：上下文管理增强验收

**功能验收：**
- [ ] `ContextManager` 能正确构建、压缩、扩展上下文
- [ ] 上下文压缩保留关键信息（任务、决定、重要结果）
- [ ] 技能加载器能根据任务类型正确加载技能
- [ ] `EnhancedMemoryStore` 支持标签和任务关联

**质量验收：**
- [ ] 单元测试覆盖率 ≥ 85%
- [ ] 所有测试通过
- [ ] `ruff check .` 无错误
- [ ] `ruff format .` 无警告

**文档验收：**
- [ ] API 文档完整
- [ ] 使用示例可用

### 6.2 阶段二：任务规划系统验收

**功能验收：**
- [ ] `TaskPlanner` 能正确分析任务复杂度
- [ ] 任务类型检测准确率 > 80%
- [ ] 任务修正和取消检测准确

**质量验收：**
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 所有测试通过
- [ ] Lint 无错误

**文档验收：**
- [ ] 规划策略文档
- [ ] 数据模型文档

### 6.3 阶段三：执行决策系统验收

**功能验收：**
- [ ] `ExecutionDecisionMaker` 能正确处理各种触发器
- [ ] 决策逻辑符合预期
- [ ] Subagent 结果处理正确

**质量验收：**
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 所有测试通过
- [ ] Lint 无错误

### 6.4 阶段四：基于 Agno 的 Subagent 验收

**功能验收：**
- [ ] `AgnoSubagent` 能正确执行任务
- [ ] 高风险评估准确率 > 85%
- [ ] 人工确认机制工作正常
- [ ] 消息中断机制响应及时
- [ ] Subagent Hooks 在正确时机触发

**质量验收：**
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试通过
- [ ] Lint 无错误

**文档验收：**
- [ ] Agno 集成文档
- [ ] Human-in-loop 使用指南

### 6.5 阶段五：：主代理集成验收

**功能验收：**
- [ ] `MainAgent` 能正确处理完整消息流程
- [ ] 上下文、规划、决策、Subagent 协调工作正常
- [ ] MainAgent Hooks 在正确时机触发
- [ ] 与现有 AgentLoop 集成成功

**质量验收：**
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试覆盖率 ≥ 75%
- [ ] 所有测试通过
- [ ] Lint 无错误

**文档验收：**
- [ ] 集成迁移指南
- [ ] 架构文档

### 6.6 阶段六：配置和文档验收

**功能验收：**
- [ ] 配置架构正确加载
- [ ] 示例配置可用
- [ ] 文档完整准确

**质量验收：**
- [ ] 配置测试通过
- [ ] 文档示例可执行

### 6.7 阶段七：测试和验证验收

**功能验收：**
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 所有性能测试通过基准

**质量验收：**
- [ ] 总体测试覆盖率 ≥ 80%
- [ ] 关键模块覆盖率 ≥ 85%
- [ ] 无性能退化
- [ ] Lint 无错误

### 6.8 阶段八：部署和发布验收

**功能验收：**
- [ ] 代码成功安装到本地环境
- [ ] 启动脚本正确执行
- [ ] 启动后功能可用

**质量验收：**
- [ ] 安装测试通过
- [ ] 启动脚本测试通过
- [ ] 部署文档完整

### 6.9 总体验收标准

**功能验收：**
- [ ] 主代理能正确处理各种消息类型
- [ ] 任务规划准确率 > 80%
- [ ] 上下文压缩有效率 > 30%
- [ ] Subagent 调度成功率 > 90%
- [ ] 执行决策准确率 > 85%
- [ ] Human-in-loop 机制正常工作

**质量验收：**
- [ ] 所有新模块有测试
- [ ] 测试覆盖率达标（总体 ≥ 80%，关键模块 ≥ 85%）
- [ ] `ruff check .` 无错误
- [ ] `ruff format .` 无警告
- [ ] 类型检查结果通过

**文档验收：**
- [ ] 配置文档更新
- [ ] README 更新
- [ ] 迁移指南完整
- [ ] 架构文档完整
- [ ] API 文档完整
- [ ] 部署文档完整
- [ ] 示例代码可用

**性能验收：**
- [ ] 上下文构建高效（< 500ms）
- [ ] 规划快速准确（< 1s）
- [ ] 决策响应及时（< 500ms）
- [ ] 无明显性能退化
- [ ] 性能基准测试通过

## 7. 关键技术决策

### 7.1 框架选择

**Agno 框架：**
- 原因：轻量、支持多 LLM、良好的 Agent 编排能力、活跃的社区支持
- 版本：使用最新稳定版本
- 文档参考：实现时需查阅 Agno 官方文档，梳理最佳实践后再进行开发

### 7.2 Human-in-loop 实现策略

**高风险方案：**
1. 使用 LLM 评估 Subagent 计划执行的每个操作
2. 如果检测到高风险操作（删除、配置修改、部署等），通过 ChatChannel 通知用户
3. 用户确认后继续执行，或取消操作

**消息中断方案：**
1. 用户发送新消息到 MainAgent
2. MainAgent 判断消息对当前执行任务或 Subagent 的影响
3. 如果需要中断，通知 Subagent 接收新消息并调整执行动作
4. Subagent 根据新消息决定是否继续、修改或取消当前任务

### 7.3 数据存储

**记忆存储：**
- 使用文件系统存储（保持与现有架构一致）
- 支持 JSON 序列化
- 标签索引通过内存缓存加速查询

**任务状态存储：**
- 使用内存存储（会话级别）
- 持久化选项：可选的文件系统备份

### 7.4 性能优化

**上下文压缩：**
- 使用缓存避免重复压缩
- 批量压缩提高效率
- 设置压缩阈值避免不必要的压缩

**Subagent 协调：**
- 异步执行避免阻塞
- 任务队列管理并发
- 超时和重试机制

---

**规划状态**: 已完善
**最后更新**: 2026-02-07
**版本**: 2.0
