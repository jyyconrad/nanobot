# Nanobot 配置迁移指南

本文档详细介绍了从 Nanobot v0.1.x 到 v0.2.x 的配置架构变更以及如何迁移现有配置。

## 1. 配置架构变更概述

v0.2.x 版本引入了新的任务管理和监控系统，配置架构发生了以下主要变更：

### 新增配置项

1. **`agents.main_agent`** - 主代理配置
2. **`agents.subagents`** - 子代理配置
3. **`monitoring`** - 监控配置
   - `monitoring.task` - 任务监控配置
   - `monitoring.cron` - Cron 任务配置

## 2. 配置文件格式

v0.2.x 支持以下配置格式：

- **JSON** (默认格式): `config.json`
- **YAML** (新增支持): `config.yaml` 或 `config.yml`

## 3. 详细变更说明

### 3.1 agents 配置块

#### v0.1.x 配置
```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.nanobot/workspace",
      "model": "anthropic/claude-opus-4-5",
      "max_tokens": 8192,
      "temperature": 0.7,
      "max_tool_iterations": 20
    }
  }
}
```

#### v0.2.x 配置
```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.nanobot/workspace",
      "model": "anthropic/claude-opus-4-5",
      "max_tokens": 8192,
      "temperature": 0.7,
      "max_tool_iterations": 20
    },
    "main_agent": {
      "name": "Main Agent",
      "description": "Main orchestration agent for handling user messages",
      "auto_create_subagents": true,
      "subagent_timeout": 3600,
      "task_monitoring_enabled": true
    },
    "subagents": {
      "default_timeout": 1800,
      "max_concurrent": 5,
      "retry_limit": 3,
      "retry_delay": 60
    }
  }
}
```

### 3.2 monitoring 配置块 (新增)

```json
{
  "monitoring": {
    "task": {
      "enabled": true,
      "check_interval": 3600,
      "max_task_duration": 86400,
      "auto_cleanup": true,
      "cleanup_delay": 3600
    },
    "cron": {
      "enabled": true,
      "config_path": "~/.nanobot/cron-job-config.json",
      "log_level": "INFO"
    }
  }
}
```

## 4. 迁移步骤

### 4.1 自动迁移 (推荐)

运行以下命令自动升级配置：

```bash
nanobot config upgrade
```

### 4.2 手动迁移

1. 备份当前配置：
   ```bash
   cp ~/.nanobot/config.json ~/.nanobot/config.json.backup
   ```

2. 更新配置结构：
   - 添加 `main_agent` 和 `subagents` 配置块
   - 添加 `monitoring` 配置块

3. 验证配置：
   ```bash
   nanobot status
   ```

## 5. 配置文件示例

### 5.1 JSON 格式

```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.nanobot/workspace",
      "model": "anthropic/claude-opus-4-5",
      "max_tokens": 8192,
      "temperature": 0.7,
      "max_tool_iterations": 20
    },
    "main_agent": {
      "name": "Main Agent",
      "description": "Main orchestration agent for handling user messages",
      "auto_create_subagents": true,
      "subagent_timeout": 3600,
      "task_monitoring_enabled": true
    },
    "subagents": {
      "default_timeout": 1800,
      "max_concurrent": 5,
      "retry_limit": 3,
      "retry_delay": 60
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_TELEGRAM_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  },
  "providers": {
    "openrouter": {
      "apiKey": "YOUR_API_KEY"
    }
  },
  "monitoring": {
    "task": {
      "enabled": true,
      "check_interval": 3600,
      "max_task_duration": 86400,
      "auto_cleanup": true,
      "cleanup_delay": 3600
    },
    "cron": {
      "enabled": true,
      "config_path": "~/.nanobot/cron-job-config.json",
      "log_level": "INFO"
    }
  },
  "tools": {
    "web": {
      "search": {
        "apiKey": "YOUR_BRAVE_API_KEY"
      }
    }
  },
  "gateway": {
    "host": "0.0.0.0",
    "port": 9910
  }
}
```

### 5.2 YAML 格式

```yaml
agents:
  defaults:
    workspace: "~/.nanobot/workspace"
    model: "anthropic/claude-opus-4-5"
    max_tokens: 8192
    temperature: 0.7
    max_tool_iterations: 20
  main_agent:
    name: "Main Agent"
    description: "Main orchestration agent for handling user messages"
    auto_create_subagents: true
    subagent_timeout: 3600
    task_monitoring_enabled: true
  subagents:
    default_timeout: 1800
    max_concurrent: 5
    retry_limit: 3
    retry_delay: 60

channels:
  telegram:
    enabled: true
    token: "YOUR_TELEGRAM_BOT_TOKEN"
    allowFrom: ["YOUR_USER_ID"]

providers:
  openrouter:
    apiKey: "YOUR_API_KEY"

monitoring:
  task:
    enabled: true
    check_interval: 3600
    max_task_duration: 86400
    auto_cleanup: true
    cleanup_delay: 3600
  cron:
    enabled: true
    config_path: "~/.nanobot/cron-job-config.json"
    log_level: "INFO"

tools:
  web:
    search:
      apiKey: "YOUR_BRAVE_API_KEY"

gateway:
  host: "0.0.0.0"
  port: 9910
```

## 6. 常见问题

### 6.1 配置文件未找到

如果 `nanobot config upgrade` 命令失败，请尝试手动执行：

```bash
nanobot onboard --force
```

### 6.2 配置验证错误

如果遇到配置验证错误，请检查：
1. 是否所有必填字段都已填写
2. 字段类型是否正确（如 `check_interval` 应为整数）
3. 是否存在语法错误

### 6.3 备份与回滚

如果升级后出现问题，可以使用备份回滚：

```bash
cp ~/.nanobot/config.json.backup ~/.nanobot/config.json
```

## 7. 后续版本升级建议

为了方便未来升级：
1. 定期备份配置文件
2. 遵循版本迁移指南
3. 使用自动升级工具
4. 测试配置变更

## 8. 获取帮助

- 查看完整文档：`nanobot help`
- 访问 GitHub 仓库：https://github.com/HKUDS/nanobot
- 加入社区支持：查看项目 README.md 中的联系方式
