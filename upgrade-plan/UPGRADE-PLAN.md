# 升级计划：动态子代理协调与执行监控

## 1. 升级目标

### 1.1 核心需求

1. **动态子代理创建**：ChatApps 接收消息后，mainAgent 分析并动态创建 subagent 处理消息
2. **双向通信**：subagent 完成后返回结果和过程信息给 mainAgent，mainAgent 决策下一步
3. **任务修正机制**：如果收到多条消息，新消息会影响已有 subagent 时，让 subagent 根据新消息修正或重新工作
4. **定时监控任务**：创建一个 Cron Job 每小时获取一次计划的执行进度和状态，如果存在问题及时修正计划和更新执行动作

## 2. 架构设计

### 2.1 新架构图

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Chat Apps   │────►│ Message Bus  │────►│  Agent Loop  │
└──────────────┘     └──────────────┘     └──────────────┘
         ▲                     ▲                   │
         │                     │                   ▼
         │                     │            ┌──────────────┐
         │                     │            │ Task Manager │
         │                     │            └──────────────┘
         │                     │                   │
         │                     │            ┌──────────────┐
         │                     └────────────┤ Subagents    │
         │                                  └──────────────┘
         │                                          │
         │                                          ▼
         └──────────────────────────────────────┐ Cron Job    │
                                                └──────────────┘
```

### 2.2 关键组件设计

#### 2.2.1 Task Manager (任务管理器)

```python
class TaskManager:
    """
    任务管理和协调中心：
    - 跟踪所有运行中的子代理任务
    - 管理任务状态和进度
    - 处理任务修正和重新执行
    - 提供任务查询接口
    """
```

#### 2.2.2 Enhanced Subagent Manager (增强的子代理管理器)

```python
class EnhancedSubagentManager(SubagentManager):
    """
    增强的子代理管理：
    - 支持任务状态跟踪
    - 提供任务修正接口
    - 实时进度汇报
    - 子代理生命周期管理
    """
```

#### 2.2.3 Message Routing System (消息路由系统)

```python
class MessageRouter:
    """
    智能消息路由：
    - 分析新消息与现有任务的关联
    - 决定消息是创建新任务还是修正现有任务
    - 支持任务上下文传递
    """
```

## 3. 实现步骤

### 3.1 阶段一：任务管理框架 (1-2 天)

#### 3.1.1 创建任务管理模块

```
nanobot/
├── agent/
│   ├── task_manager.py          # 任务管理器
│   ├── task.py                  # 任务数据模型
│   └── subagent.py              # 增强的子代理管理器
```

**任务模型 (agent/task.py)**：
```python
class Task:
    id: str
    type: str
    status: TaskStatus  # pending/running/complete/failed
    original_message: str
    current_task: str
    progress: float
    subagent_id: str
    session_key: str
    channel: str
    chat_id: str
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    result: str | None
    history: list[str]
```

#### 3.1.2 增强子代理管理器

**修改 nanobot/agent/subagent.py**：
- 添加任务状态跟踪
- 支持任务修正接口
- 实时进度汇报机制
- 子代理与任务的关联

### 3.2 阶段二：消息路由与分析 (2-3 天)

#### 3.2.1 创建消息分析器

**创建 nanobot/bus/message_analyzer.py**：
```python
class MessageAnalyzer:
    """
    分析消息与任务的关联：
    - 语义相似度分析
    - 任务相关性识别
    - 决定创建新任务还是修正现有任务
    """
    
    def analyze_message(self, message: InboundMessage, active_tasks: list[Task]) -> AnalysisResult:
        """
        AnalysisResult:
        - action: create_task | update_task | cancel_task
        - target_task_id: str | None
        - confidence: float
        """
```

#### 3.2.2 修改消息总线

**修改 nanobot/bus/queue.py 和 nanobot/agent/loop.py**：
- 集成消息分析器
- 实现智能消息路由
- 处理任务修正逻辑

### 3.3 阶段三：执行进度监控 (2 天)

#### 3.3.1 创建进度监控模块

**创建 nanobot/monitor/progress_tracker.py**：
```python
class ProgressTracker:
    """
    任务进度跟踪：
    - 监控子代理执行状态
    - 收集过程信息
    - 提供进度查询接口
    """
    
    def get_task_progress(self, task_id: str) -> dict:
        """返回任务进度详情"""
    
    def get_all_progress(self) -> list[dict]:
        """返回所有任务进度"""
```

#### 3.3.2 子代理进度汇报

**修改 nanobot/agent/subagent.py**：
- 在子代理执行过程中定期汇报进度
- 记录关键步骤和中间结果
- 支持进度更新机制

### 3.4 阶段四：可配置定时任务系统 (2-3 天)

#### 3.4.1 创建配置驱动的 Cron 系统

**创建 nanobot/cron/config_loader.py**：
```python
class CronConfigLoader:
    """
    从配置文件加载和管理定时任务
    """
    def load_config(self, path: str) -> dict
    def validate_config(self, config: dict) -> bool
    def create_jobs(self, config: dict) -> list[CronJob]
```

**创建 nanobot/cron/agent_trigger.py**：
```python
class AgentTrigger:
    """
    触发指定 Agent 的方法执行
    """
    async def trigger_agent(self, target: str, method: str, params: dict) -> Any
    async def trigger_subagent(self, subagent_id: str, method: str, params: dict) -> Any
```

**创建 nanobot/cron/status_monitor.py**：
```python
class AgentStatusMonitor:
    """
    监听 Agent 状态并根据条件触发响应
    """
    async def monitor_agent(self, agent: str, checks: list[str]) -> dict
    async def check_conditions(self, status: dict, conditions: dict) -> list[Alert]
    async def handle_alert(self, alert: Alert) -> None
```

#### 3.4.2 扩展 Cron 服务

**修改 nanobot/cron/types.py**'：
```python
class CronAction:
    type: str  # trigger_agent | monitor_status | agent_turn
    target: str | None
    method: str | None
    params: dict | None
    targets: list[dict] | None  # for monitor_status
    alertConditions: dict | None

class CronJobConfig:
    version: str
    jobs: list[CronJob]
    globalSettings: dict
```

**修改 nanobot/cron/service.py**：
- 支持从配置文件加载任务
- 实现配置重载功能
- 支持 trigger_agent 和 monitor_status 动作类型

#### 3.4.3 创建增强配置文件

**创建 upgrade-plan/cron-job-config-enhanced.json**（v2.0）：
- `trigger_agent` 类型：触发 mainAgent 或其他 Agent 方法执行
- `monitor_status` 类型：监听 Agent 状态并自动响应
- 预设任务：任务进度监控、每日健康检查、Agent 状态监听、任务清理
- 支持全局设置：通知渠道、执行超时、并发限制

详见：`upgrade-plan/ENHANCED-CRON.md`

## 4. 代码变更清单

### 4.1 新增文件

| 文件路径 | 功能描述 |
|---------|---------|
| nanobot/agent/task.py | 任务数据模型 |
| nanobot/agent/task_manager.py | 任务管理器 |
| nanobot/bus/message_analyzer.py | 消息分析器 |
| nanobot/monitor/progress_tracker.py | 进度跟踪器 |
| nanobot/cron/monitor.py | 任务监控器 |
| upgrade-plan/cron-job-config.json | Cron 任务配置 |
| upgrade-plan/test-scenarios.md | 测试场景 |
| upgrade-plan/deployment-guide.md | 部署指南 |

### 4.2 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| nanobot/agent/subagent.py | 增强子代理管理，支持任务状态和修正 |
| nanobot/agent/loop.py | 集成任务管理和消息分析 |
| nanobot/bus/events.py | 新增任务相关事件类型 |
| nanobot/bus/queue.py | 优化消息路由 |
| nanobot/cron/types.py | 新增任务监控类型和增强配置支持 |
| nanobot/cron/service.py | 支持新任务类型执行和配置驱动 |
| nanobot/cron/config_loader.py | 配置文件加载和验证 |
| nanobot/cron/agent_trigger.py | Agent 触发器 |
| nanobot/cron/status_monitor.py | Agent 状态监听器 |

## 5. 测试计划

### 5.1 单元测试

```
tests/
├── test_task_manager.py          # 任务管理测试
├── test_message_analyzer.py      # 消息分析测试
├── test_subagent_enhanced.py     # 增强子代理测试
└── test_task_monitor.py          # 任务监控测试
```

### 5.2 集成测试

**场景测试**：
1. 基本任务执行流程
2. 任务修正场景
3. 多任务并发执行
4. 监控任务触发和执行
5. 任务失败自动修复

### 5.3 性能测试

- 子代理创建和销毁时间
- 消息分析响应时间
- 任务监控开销
- 系统资源消耗

## 6. 部署和验证

### 6.1 部署步骤

1. 更新代码到最新版本
2. 运行数据库迁移（如需要）
3. 加载新的 Cron 任务配置
4. 重启 nanobot 服务
5. 验证任务监控功能

### 6.2 验证方法

```bash
# 检查 Cron 任务是否加载
nanobot cron list

# 手动触发监控任务
nanobot cron run <monitor-job-id>

# 查看任务状态
nanobot status --tasks
```

## 7. 风险评估和注意事项

### 7.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 消息分析精度 | 任务关联错误导致修正失败 | 使用更强大的语义相似度模型，提供手动修正选项 |
| 子代理资源消耗 | 大量子代理导致系统过载 | 实现子代理资源限制和自动伸缩 |
| 任务状态一致性 | 子代理状态与任务管理器不同步 | 使用心跳机制定期同步状态 |

### 7.2 业务风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 用户体验 | 任务修正可能导致混淆 | 清晰的任务状态展示和进度更新 |
| 任务失败 | 重要任务失败未及时通知 | 增强错误通知机制，支持任务重试 |

### 7.3 注意事项

1. **数据迁移**：现有的任务状态可能需要迁移到新的任务管理系统
2. **API 兼容性**：确保与现有工具和技能的兼容性
3. **性能监控**：部署后需要密切监控系统资源使用情况
4. **回滚方案**：准备回滚到旧版本的方案，如需要

## 8. 版本规划

### 8.1 v0.2.0 - 基础任务管理

- 任务管理框架
- 增强子代理管理
- 基本消息路由

### 8.2 v0.2.1 - 消息分析和任务修正

- 消息分析器
- 任务修正机制
- 进度跟踪

### 8.3 v0.2.2 - 可配置定时任务系统

- 配置文件驱动的 Cron 系统
- Agent 触发器（支持 mainAgent 和任意 subagent）
- Agent 状态监听器和自动响应
- 预设任务：进度监控、健康检查、状态监听、任务清理

### 8.4 v0.2.3 - 性能优化和测试

- 性能优化
- 全面测试
- 部署验证
