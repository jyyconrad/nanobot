# Nanobot 架构设计文档

## 1. 架构概述

Nanobot 是一个轻量级的个人 AI 助手，采用模块化架构设计，具有以下核心特点：

- **轻量级**：代码量仅约 4000 行，资源消耗低
- **可扩展**：支持多种 LLM 提供商和通信渠道
- **高性能**：快速启动、低延迟、高效资源利用
- **可维护**：清晰的模块划分和代码结构

## 2. 系统架构图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Chat Apps     │────►│  Message Bus    │────►│   Agent Loop    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         ▲                      ▲                      │
         │                      │                      ▼
         │                      │               ┌─────────────────┐
         │                      │               │ Task Manager    │
         │                      │               └─────────────────┘
         │                      │                      │
         │                      │               ┌─────────────────┐
         │                      └───────────────┤  Subagents      │
         │                                      └─────────────────┘
         │                                              │
         │                                              ▼
         └────────────────────────────────────────┐ Cron Jobs       │
                                                 └─────────────────┘
```

## 3. 核心组件设计

### 3.1 任务管理框架

#### 3.1.1 TaskManager (任务管理器)

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

**关键功能**：
- 任务状态管理：跟踪任务的完整生命周期
- 子代理分配：为任务分配和管理子代理
- 进度跟踪：实时监控任务执行进度
- 任务修正：支持根据新信息修正任务
- 查询接口：提供任务状态和进度查询

#### 3.1.2 Task (任务模型)

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

### 3.2 子代理管理

#### 3.2.1 EnhancedSubagentManager (增强的子代理管理器)

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

**核心功能**：
- 子代理创建和销毁
- 任务状态同步
- 进度汇报机制
- 任务修正支持
- 资源管理

### 3.3 消息路由系统

#### 3.3.1 MessageRouter (消息路由器)

```python
class MessageRouter:
    """
    智能消息路由：
    - 分析新消息与现有任务的关联
    - 决定消息是创建新任务还是修正现有任务
    - 支持任务上下文传递
    """
```

#### 3.3.2 MessageAnalyzer (消息分析器)

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

### 3.4 执行进度监控

#### 3.4.1 ProgressTracker (进度跟踪器)

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

### 3.5 可配置定时任务系统

#### 3.5.1 Cron 任务系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Config File   │────►│ Config Loader   │────►│  Cron Service   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         ▲                      ▲                      │
         │                      │                      ▼
         │                      │               ┌─────────────────┐
         │                      │               │  Job Scheduler  │
         │                      │               └─────────────────┘
         │                      │                      │
         │                      │               ┌─────────────────┐
         │                      └───────────────┤   Job Executor  │
         │                                      └─────────────────┘
         │                                              │
         │                                              ▼
         └────────────────────────────────────────┐  Action Handler │
                                                 └─────────────────┘
```

#### 3.5.2 配置结构

```python
class CronJobConfig:
    version: str
    jobs: list[CronJob]
    globalSettings: dict

class CronJob:
    id: str
    name: str
    cronExpression: str
    action: CronAction
    enabled: bool
    description: str

class CronAction:
    type: str  # trigger_agent | monitor_status | agent_turn
    target: str | None
    method: str | None
    params: dict | None
    targets: list[dict] | None
    alertConditions: dict | None
```

#### 3.5.3 核心组件

**CronConfigLoader**：负责加载和验证定时任务配置
**CronService**：负责调度和执行定时任务
**AgentTrigger**：负责触发 Agent 方法执行
**StatusMonitor**：负责监听 Agent 状态并自动响应
**JobExecutor**：负责执行具体的任务逻辑

## 4. 配置系统设计

### 4.1 配置架构

```
┌─────────────────────────────────┐
│        Config (Root)            │
├─────────────────────────────────┤
│  ┌───────────────────────────┐  │
│  │  Agents Config            │  │
│  │  - defaults               │  │
│  │  - main_agent             │  │
│  │  - subagents              │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Channels Config          │  │
│  │  - WhatsApp               │  │
│  │  - Telegram               │  │
│  │  - Feishu                 │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Providers Config         │  │
│  │  - Anthropic              │  │
│  │  - OpenAI                 │  │
│  │  - OpenRouter             │  │
│  │  - DeepSeek               │  │
│  │  - Groq                   │  │
│  │  - Zhipu                  │  │
│  │  - vLLM                   │  │
│  │  - Gemini                 │  │
│  │  - Volcengine             │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Gateway Config           │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Tools Config             │  │
│  │  - Web Search             │  │
│  │  - Exec Shell             │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Monitoring Config        │  │
│  │  - Task Monitoring        │  │
│  │  - Cron Jobs              │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

### 4.2 配置加载机制

```python
class ConfigLoader:
    """
    配置加载器：
    - 支持 JSON 和 YAML 格式
    - 自动类型转换
    - 配置验证
    - 环境变量支持
    """
    
    def load_config(self, path: str) -> Config:
        """从文件加载配置"""
    
    def save_config(self, config: Config, path: str) -> None:
        """保存配置到文件"""
    
    def validate_config(self, config: dict) -> bool:
        """验证配置完整性和正确性"""
```

### 4.3 配置验证

```python
class ConfigValidator:
    """
    配置验证器：
    - 验证配置完整性
    - 类型检查
    - 值范围验证
    - 逻辑一致性验证
    """
    
    def validate_agents_config(self, config: dict) -> list[str]:
        """验证代理配置"""
    
    def validate_channels_config(self, config: dict) -> list[str]:
        """验证通道配置"""
    
    def validate_providers_config(self, config: dict) -> list[str]:
        """验证提供商配置"""
    
    def validate_monitoring_config(self, config: dict) -> list[str]:
        """验证监控配置"""
```

## 5. 通信架构

### 5.1 消息流程

```
Chat App → Inbound Message → Message Router → Agent Loop → Task Manager → Subagent
                                                                          ↓
Chat App ← Outbound Message ← Message Router ← Agent Loop ← Task Manager ← Subagent
```

### 5.2 事件系统

```python
class NanobotEvent:
    """
    基础事件类型：
    - message_received
    - message_sent
    - task_created
    - task_updated
    - task_completed
    - subagent_created
    - subagent_updated
    - subagent_completed
    - cron_job_executed
    """
```

## 6. 数据存储架构

### 6.1 文件存储

- **配置文件**：`~/.nanobot/config.json` 或 `config.yaml`
- **任务状态**：`~/.nanobot/data/tasks/`
- **会话数据**：`~/.nanobot/data/sessions/`
- **记忆数据**：`~/.nanobot/data/memory/`
- **Cron 任务配置**：`~/.nanobot/cron-job-config.json`

### 6.2 数据序列化

```python
class DataSerializer:
    """
    数据序列化器：
    - JSON 序列化
    - YAML 序列化
    - 安全验证
    """
    
    def serialize(self, data: Any) -> str:
        """序列化数据"""
    
    def deserialize(self, data: str) -> Any:
        """反序列化数据"""
```

## 7. 扩展和插件系统

### 7.1 技能系统

```python
class Skill:
    """
    技能基类：
    - name: 技能名称
    - description: 技能描述
    - inputs: 输入参数定义
    - outputs: 输出结果定义
    - execute: 执行方法
    """
    
    async def execute(self, context: Context, params: dict) -> dict:
        """执行技能"""
```

### 7.2 工具系统

```python
class Tool:
    """
    工具基类：
    - name: 工具名称
    - description: 工具描述
    - parameters: 参数定义
    - run: 执行方法
    """
    
    async def run(self, **kwargs) -> Any:
        """执行工具"""
```

## 8. 性能优化设计

### 8.1 资源管理

```python
class ResourceManager:
    """
    资源管理器：
    - 内存管理
    - 线程池管理
    - 进程管理
    - 资源限制
    """
    
    def limit_memory_usage(self, limit: int) -> None:
        """限制内存使用"""
    
    def limit_cpu_usage(self, limit: int) -> None:
        """限制 CPU 使用"""
    
    def cleanup_resources(self) -> None:
        """清理资源"""
```

### 8.2 缓存系统

```python
class CacheSystem:
    """
    缓存系统：
    - LRU 缓存
    - TTL 过期
    - 内存限制
    - 持久化支持
    """
    
    def get(self, key: str) -> Any:
        """获取缓存"""
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """设置缓存"""
```

## 9. 部署架构

### 9.1 单节点部署

```
┌─────────────────────────────────────────┐
│  Nanobot Process                        │
│ ┌─────────────────────────────────────┐│
│ │  Main Agent Loop                     ││
│ │  ┌─────────────────────────────────┐││
│ │  │  Task Manager                    │││
│ │  └─────────────────────────────────┘││
│ │  ┌─────────────────────────────────┐││
│ │  │  Subagent Manager                │││
│ │  └─────────────────────────────────┘││
│ │  ┌─────────────────────────────────┐││
│ │  │  Message Router                  │││
│ │  └─────────────────────────────────┘││
│ │  ┌─────────────────────────────────┐││
│ │  │  Cron Service                    │││
│ │  └─────────────────────────────────┘││
│ └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │  Communication Channels             ││
│  │  ┌─────────────────────────────────┐││
│  │  │  WhatsApp                        │││
│  │  └─────────────────────────────────┘││
│  │  ┌─────────────────────────────────┐││
│  │  │  Telegram                        │││
│  │  └─────────────────────────────────┘││
│  │  ┌─────────────────────────────────┐││
│  │  │  Feishu                          │││
│  │  └─────────────────────────────────┘││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │  LLM Providers                      ││
│  │  ┌─────────────────────────────────┐││
│  │  │  OpenRouter                     │││
│  │  └─────────────────────────────────┘││
│  │  ┌─────────────────────────────────┐││
│  │  │  Anthropic                      │││
│  │  └─────────────────────────────────┘││
│  │  ┌─────────────────────────────────┐││
│  │  │  OpenAI                         │││
│  │  └─────────────────────────────────┘││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │  Tools & Skills                     ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### 9.2 多节点部署

```
┌─────────────────────────────────────────────────────────────────┐
│  Cluster Management                                            │
│ ┌───────────────────────────────────────────────────────────┐  │
│ │  Load Balancer                                             │  │
│ └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────┬───────────────────────────┐    │
│  │  Node 1                   │  Node 2                   │    │
│  │ ┌───────────────────────┐ │ ┌───────────────────────┐ │    │
│  │ │  Main Agent Loop      │ │ │  Main Agent Loop      │ │    │
│  │ └───────────────────────┘ │ └───────────────────────┘ │    │
│  │ ┌───────────────────────┐ │ ┌───────────────────────┐ │    │
│  │ │  Subagent Pool        │ │ │  Subagent Pool        │ │    │
│  │ └───────────────────────┘ │ └───────────────────────┘ │    │
│  │ ┌───────────────────────┐ │ ┌───────────────────────┐ │    │
│  │ │  Task Manager         │ │ │  Task Manager         │ │    │
│  │ └───────────────────────┘ │ └───────────────────────┘ │    │
│  └───────────────────────────┴───────────────────────────┘    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Shared Storage                                           │  │
│  │ ┌───────────────────────┐ ┌───────────────────────┐      │  │
│  │ │  Task Database        │ │  Session Storage      │      │  │
│  │ └───────────────────────┘ └───────────────────────┘      │  │
│  │ ┌───────────────────────┐ ┌───────────────────────┐      │  │
│  │ │  Memory Store         │ │  Config Cache         │      │  │
│  │ └───────────────────────┘ └───────────────────────┘      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 10. 安全架构

### 10.1 访问控制

```python
class AccessControl:
    """
    访问控制：
    - 白名单机制
    - 用户认证
    - 权限验证
    - 会话管理
    """
    
    def is_allowed(self, user_id: str, channel: str) -> bool:
        """验证用户是否允许访问"""
    
    def validate_session(self, session_id: str) -> bool:
        """验证会话有效性"""
```

### 10.2 数据安全

```python
class DataSecurity:
    """
    数据安全：
    - 加密存储
    - 安全传输
    - 数据备份
    - 审计日志
    """
    
    def encrypt_data(self, data: str, key: str) -> str:
        """加密数据"""
    
    def decrypt_data(self, encrypted_data: str, key: str) -> str:
        """解密数据"""
```

## 11. 监控和日志系统

### 11.1 日志系统

```python
class Logger:
    """
    日志系统：
    - 多级别日志
    - 文件日志
    - 控制台日志
    - 远程日志
    """
    
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
    
    def error(self, message: str, **kwargs) -> None:
        """记录错误日志"""
```

### 11.2 监控指标

```python
class MetricsCollector:
    """
    指标收集器：
    - 系统资源使用
    - 任务执行时间
    - 错误率
    - 用户活跃度
    """
    
    def collect_system_metrics(self) -> dict:
        """收集系统指标"""
    
    def collect_task_metrics(self) -> dict:
        """收集任务指标"""
```

## 12. 未来架构展望

### 12.1 架构演进方向

1. **微服务架构**：将组件拆分为独立的微服务
2. **容器化部署**：使用 Docker 和 Kubernetes
3. **分布式计算**：支持任务在多节点之间分配
4. **事件驱动架构**：使用消息队列和事件总线
5. **机器学习优化**：基于使用模式优化性能
6. **多语言支持**：支持 Python 以外的语言

### 12.2 技术栈规划

- **通信**：gRPC、WebSocket、MQTT
- **存储**：PostgreSQL、Redis、MongoDB
- **消息队列**：RabbitMQ、Kafka
- **监控**：Prometheus、Grafana
- **部署**：Docker、Kubernetes
- **CI/CD**：GitHub Actions、GitLab CI
