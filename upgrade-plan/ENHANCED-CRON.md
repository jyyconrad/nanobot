# 增强版 Cron 任务配置方案

## 更新需求

原计划中的定时监控任务升级为**可配置化的定时任务系统**，支持：
- 根据配置文件自动创建定时任务
- 触发 mainAgent 或其他 Agent 的执行
- 监听 Agent 状态并自动响应

## 配置文件结构

配置文件：`upgrade-plan/cron-job-config-enhanced.json`

### 核心字段说明

#### Job 基本配置
```json
{
  "id": "task-progress-monitor",      // 任务唯一标识
  "name": "Task Progress Monitor",    // 任务名称
  "enabled": true,                    // 是否启用
  "schedule": {                      // 调度配置
    "kind": "cron",                   // 调度类型：cron | at | every
    "expr": "0 * * * *",              // Cron 表达式
    "tz": "Asia/Shanghai"             // 时区
  }
}
```

#### Action 类型

**1. 触发 Agent 执行**
```json
"action": {
  "type": "trigger_agent",
  "target": "mainAgent",             // 目标 Agent：mainAgent | subagent:<id>
  "method": "monitor_tasks",         // 要调用的方法
  "params": {                        // 方法参数
    "check_all_tasks": true,
    "auto_fix": true,
    "report_issues": true
  }
}
```

**2. 监听 Agent 状态**
```json
"action": {
  "type": "monitor_status",
  "targets": [                        // 监听目标列表
    {
      "agent": "mainAgent",          // 监听 mainAgent
      "check": ["running", "responsive", "memory_usage"]
    },
    {
      "agent": "all_subagents",      // 监听所有子代理
      "check": ["running", "timeout_check", "resource_usage"]
    }
  ],
  "alertConditions": {               // 告警条件
    "agent_not_responsive": {
      "threshold": "5m",             // 超过 5 分钟无响应
      "action": "restart"            // 执行重启操作
    },
    "memory_usage_high": {
      "threshold": "80%",            // 内存使用超过 80%
      "action": "notify"             // 发送通知
    },
    "subagent_timeout": {
      "threshold": "30m",            // 子代理超时 30 分钟
      "action": "terminate_and_notify"  // 终止并通知
    }
  }
}
```

#### 错误处理
```json
"onError": {
  "retry": 3,                        // 失败后重试 3 次
  "retryInterval": "5m",             // 重试间隔 5 分钟
  "notify": true                     // 失败后发送通知
}
```

## 预设任务配置

### 1. 任务进度监控（每小时）
- 监听 mainAgent 的 `monitor_tasks` 方法
- 检查所有任务执行状态
- 自动修正问题任务
- 汇报执行结果

### 2. 每日系统健康检查（每天 9:00）
- 触发 mainAgent 的 `health_check` 方法
- 检查系统状态、资源使用、子代理状态
- 生成健康报告

### 3. Agent 状态监听（每 30 秒）
- 监听 mainAgent 和所有子代理的状态
- 检查响应性、内存使用、超时情况
- 根据预设条件自动重启/通知

### 4. 清理已完成任务（每天 2:00）
- 触发 mainAgent 的 `cleanup_tasks` 方法
- 清理 7 天前的已完成任务
- 可选归档功能

## 全局设置

```json
"globalSettings": {
  "notification": {
    "enabled": true,
    "channel": "cli",                 // 通知渠道：cli | feishu | telegram
    "onFailure": true,
    "onSuccess": false
  },
  "execution": {
    "timeout": "10m",                 // 单次任务超时时间
    "maxConcurrent": 5,               // 最大并发任务数
    "priority": "normal"              // 优先级：low | normal | high
  }
}
```

## 实现要点

### 1. 配置文件加载器
```python
class CronConfigLoader:
    """
    从配置文件加载和管理定时任务
    """
    def load_config(self, path: str) -> dict
    def validate_config(self, config: dict) -> bool
    def create_jobs(self, config: dict) -> list[CronJob]
```

### 2. Agent 触发器
```python
class AgentTrigger:
    """
    触发指定 Agent 的方法执行
    """
    async def trigger_agent(self, target: str, method: str, params: dict) -> Any
    async def trigger_subagent(self, subagent_id: str, method: str, params: dict) -> Any
```

### 3. 状态监听器
```python
class AgentStatusMonitor:
    """
    监听 Agent 状态并根据条件触发响应
    """
    async def monitor_agent(self, agent: str, checks: list[str]) -> dict
    async def check_conditions(self, status: dict, conditions: dict) -> list[Alert]
    async def handle_alert(self, alert: Alert) -> None
```

### 4. 响应执行器
```python
class ActionExecutor:
    """
    执行告警响应动作
    """
    async def restart_agent(self, agent: str) -> bool
    async def notify(self, message: str) -> None
    async def terminate_agent(self, agent: str) -> bool
```

## 使用示例

### 添加新的定时任务
编辑 `cron-job-config-enhanced.json`，添加：
```json
{
  "id": "custom-task",
  "name": "My Custom Task",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "*/15 * * * *",
    "tz": "Asia/Shanghai"
  },
  "action": {
    "type": "trigger_agent",
    "target": "mainAgent",
    "method": "my_custom_method",
    "params": {
      "param1": "value1"
    }
  }
}
```

### 手动触发任务
```bash
nanobot cron run task-progress-monitor
```

### 列出所有任务
```bash
nanobot cron list
```

### 启 reload 配置
```bash
nanobot cron reload
```

## 优势与其他方案对比

| 特性 | 原方案 | 增强方案 |
|------|--------|----------|
| 配置方式 | 硬编码 | 配置文件驱动 |
| 灵活性 | 固定任务 | 动态添加/修改 |
| 目标支持 | 仅 mainAgent | 任意 Agent |
| 监控能力 | 简单轮询 | 状态监听+自动响应 |
| 错误处理 | 无 | 重试+通知 |
| 扩展性 | 低 | 高 |

## 安全注意事项

1. **配置验证**：加载配置时必须进行严格验证
2. **方法白名单**：只允许调用安全的 Agent 方法
3. **资源限制**：限制并发任务数和单次任务时长
4. **权限控制**：触发 Agent 前检查权限
5. **敏感信息**：配置文件不应包含敏感信息

## 向后兼容

- 保留原有的 `cron-job-config.json` 作为向后兼容版本
- 新配置文件标记为 `version: "2.0"`
- 支持从 v1.0 自动迁移到 v2.0
