# 部署指南

## 1. 环境准备

### 1.1 系统要求

- Python 3.11+
- pip 或 uv（推荐使用 uv）
- Docker（可选，用于容器化部署）

### 1.2 依赖安装

```bash
# 使用 uv 安装（推荐）
uv pip install nanobot-ai

# 或使用 pip 安装
pip install nanobot-ai
```

## 2. 配置文件更新

### 2.1 检查现有配置

```bash
ls -la ~/.nanobot/
```

### 2.2 更新配置文件

**编辑 `~/.nanobot/config.json` 以启用新功能：**

```json
{
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5"
    },
    "task_manager": {
      "enabled": true,
      "max_concurrent_tasks": 10,
      "task_timeout": 3600
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    },
    "whatsapp": {
      "enabled": false
    },
    "feishu": {
      "enabled": false
    }
  },
  "cron": {
    "enabled": true,
    "store_path": "~/.nanobot/cron_store.json"
  }
}
```

## 3. 部署步骤

### 3.1 方式一：从源代码部署

#### 3.1.1 克隆代码

```bash
cd /Users/jiangyayun/develop/code/work_code/nanobot
git pull origin main
```

#### 3.1.2 安装依赖

```bash
uv venv
uv pip install -e .
```

#### 3.1.3 初始化配置

```bash
uv run nanobot onboard
```

#### 3.1.4 加载 Cron Job 配置

**使用提供的配置文件：**

```bash
cp upgrade-plan/cron-job-config.json ~/.nanobot/
```

#### 3.1.5 启动服务

```bash
uv run nanobot gateway
```

### 3.2 方式二：使用 Docker 部署

#### 3.2.1 构建 Docker 镜像

```bash
cd /Users/jiangyayun/develop/code/work_code/nanobot
docker build -t nanobot:v0.2.0 .
```

#### 3.2.2 初始化配置

```bash
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot:v0.2.0 onboard
```

#### 3.2.3 加载 Cron Job 配置

```bash
cp upgrade-plan/cron-job-config.json ~/.nanobot/
```

#### 3.2.4 启动容器

```bash
docker run -d \
  --name nanobot \
  -v ~/.nanobot:/root/.nanobot \
  -p 18790:18790 \
  nanobot:v0.2.0 gateway
```

## 4. 验证部署

### 4.1 检查服务状态

```bash
nanobot status
```

**预期输出示例：**

```
nanobot v0.2.0 - Ultra-Lightweight Personal AI Assistant

Agent Status:
  - Running: True
  - Model: anthropic/claude-opus-4-5
  - Workspace: ~/.nanobot/workspace
  - Active Tasks: 0

Channels:
  - telegram: Enabled, Connected
  - whatsapp: Disabled
  - feishu: Disabled

Cron Jobs:
  - task-progress-monitor: Enabled, Next run at 2024-02-06 16:00:00

System Status:
  - Python: 3.11.6
  - OS: Darwin 24.5.0
  - Memory: 456 MB used
```

### 4.2 手动触发监控任务

```bash
nanobot cron run task-progress-monitor
```

**预期输出：**

```
Running job task-progress-monitor...
Job completed successfully.
Result: Task execution status check completed. No issues found.
```

### 4.3 测试任务执行

**发送测试消息：**
```bash
nanobot agent -m "帮我搜索最近一周关于人工智能的新闻"
```

**预期响应：**
```
Subagent [搜索最近一周关于人工智能的新闻] started (id: abc123). I'll notify you when it completes.
```

## 5. 数据迁移

### 5.1 检查现有任务数据

```bash
ls -la ~/.nanobot/
```

### 5.2 执行数据迁移

**如果您有现有的任务数据，需要执行迁移：**

```bash
nanobot migrate tasks
```

## 6. 监控和维护

### 6.1 查看日志

```bash
# 实时查看日志
tail -f ~/.nanobot/nanobot.log

# 查看特定日期的日志
grep "2024-02-06" ~/.nanobot/nanobot.log
```

### 6.2 检查任务状态

```bash
nanobot status --tasks
```

### 6.3 管理 Cron Jobs

```bash
# 列出所有任务
nanobot cron list

# 添加新任务
nanobot cron add --name "my-task" --message "Check status" --cron "0 * * * *"

# 删除任务
nanobot cron remove <job-id>
```

## 7. 回滚方案

### 7.1 停止当前服务

```bash
# 对于 Docker 部署
docker stop nanobot
docker rm nanobot

# 对于直接部署
pkill -f "nanobot gateway"
```

### 7.2 恢复旧版本

```bash
# 切换到旧版本
cd /Users/jiangyayun/develop/code/work_code/nanobot
git checkout v0.1.3.post4

# 重新安装依赖
uv pip install -e .

# 重启服务
uv run nanobot gateway
```

### 7.3 数据恢复

**如果需要恢复旧版本数据：**

```bash
cp ~/.nanobot/config.json.backup ~/.nanobot/config.json
cp ~/.nanobot/cron_store.json.backup ~/.nanobot/cron_store.json
```

## 8. 常见问题

### 8.1 服务启动失败

**问题**：服务无法启动，出现以下错误：
```
Error: Failed to initialize task manager
```

**解决方法**：
```bash
# 检查配置文件
cat ~/.nanobot/config.json

# 确保任务管理器配置正确
uv run nanobot config validate
```

### 8.2 Cron 任务不执行

**问题**：监控任务没有按计划执行。

**解决方法**：
```bash
# 检查 Cron 服务状态
nanobot status

# 检查任务配置
nanobot cron list

# 检查日志
grep "Cron" ~/.nanobot/nanobot.log
```

### 8.3 子代理任务失败

**问题**：子代理任务失败，出现以下错误：
```
Error: Subagent failed to execute task
```

**解决方法**：
```bash
# 检查子代理日志
grep "Subagent" ~/.nanobot/nanobot.log

# 检查网络连接
curl -I https://api.openrouter.ai

# 检查 API 密钥
cat ~/.nanobot/config.json | grep "apiKey"
```

### 8.4 任务状态更新不及时

**问题**：任务状态在用户界面上更新不及时。

**解决方法**：
```bash
# 检查任务管理器状态
nanobot status --tasks

# 检查网络连接
nanobot network check

# 重启服务
pkill -f "nanobot gateway"
uv run nanobot gateway
```

## 9. 性能优化建议

### 9.1 资源限制

```bash
# 设置最大并发任务数
nanobot config set agents.task_manager.max_concurrent_tasks 5

# 设置任务超时时间
nanobot config set agents.task_manager.task_timeout 1800
```

### 9.2 缓存优化

```bash
# 启用任务结果缓存
nanobot config set agents.cache.enabled true

# 设置缓存大小（MB）
nanobot config set agents.cache.max_size 500
```

### 9.3 日志优化

```bash
# 调整日志级别
nanobot config set logging.level info

# 设置日志滚动大小（MB）
nanobot config set logging.max_size 100
```

## 10. 安全注意事项

### 10.1 API 密钥保护

```bash
# 限制配置文件权限
chmod 600 ~/.nanobot/config.json

# 使用环境变量替代硬编码
export OPENROUTER_API_KEY="sk-or-v1-xxx"
```

### 10.2 网络安全

```bash
# 使用 HTTPS 代理
nanobot config set network.proxy_url "https://proxy.example.com:8080"

# 设置网络超时（秒）
nanobot config set network.timeout 30
```

### 10.3 权限控制

```bash
# 限制允许访问的用户（Telegram）
nanobot config set channels.telegram.allowFrom '["123456789"]'

# 限制允许访问的用户（WhatsApp）
nanobot config set channels.whatsapp.allowFrom '["+1234567890"]'
```
