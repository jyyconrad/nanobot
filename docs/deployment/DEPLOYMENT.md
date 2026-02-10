# Nanobot 部署文档

## 概述

本文档详细介绍了如何部署和运行 Nanobot - 一个智能的 AI 助手系统。

## 系统要求

### 硬件要求
- **CPU**: 2 核或以上
- **内存**: 4 GB 或以上
- **存储**: 至少 10 GB 可用空间

### 软件要求
- **操作系统**: Linux / macOS / Windows
- **Python**: 3.10 或更高版本
- **pip**: 最新版本

## 部署步骤

### 1. 安装 Python 依赖

#### 1.1 创建和激活虚拟环境

```bash
# 在项目根目录创建虚拟环境
python -m venv temp_venv

# 激活虚拟环境
# macOS/Linux
source temp_venv/bin/activate

# Windows (PowerShell)
.\temp_venv\Scripts\Activate.ps1

# Windows (CMD)
.\temp_venv\Scripts\activate.bat
```

#### 1.2 安装 Nanobot 包

```bash
# 安装 Nanobot（开发模式）
pip install -e .[dev]

# 或者只安装生产依赖
pip install -e .
```

### 2. 配置文件

#### 2.1 创建配置目录

```bash
mkdir -p config
```

#### 2.2 配置文件说明

项目需要以下配置文件：

1. **nanobot_config.yaml** - 主配置文件
2. **secrets.yaml** - 敏感信息配置文件

示例配置文件可在 `config/` 目录下找到（以 `.example` 结尾的文件）。

#### 2.3 生成配置文件

```bash
# 复制示例配置文件
cp config/nanobot_config.yaml.example config/nanobot_config.yaml
cp config/secrets.yaml.example config/secrets.yaml
```

#### 2.4 配置参数说明

**nanobot_config.yaml** 关键配置项：

```yaml
# 机器人基本信息
bot:
  name: "Nanobot"
  version: "0.1.3"
  description: "智能的 AI 助手系统"

# LLM 配置
llm:
  provider: "openai"
  model: "gpt-4o"
  temperature: 0.7

# 插件配置
plugins:
  - name: "web_search"
    enabled: true

  - name: "file_manager"
    enabled: true
```

**secrets.yaml** 关键配置项：

```yaml
# OpenAI API 密钥
openai_api_key: "your-api-key-here"

# Telegram 配置
telegram:
  token: "your-telegram-bot-token"
  allowed_users:
    - "user1"
    - "user2"
```

### 3. 启动 Nanobot

#### 3.1 使用启动脚本（推荐）

```bash
# 生产模式
chmod +x scripts/start_nanobot.sh
./scripts/start_nanobot.sh

# 开发模式（启用调试和热重载）
chmod +x scripts/start_dev.sh
./scripts/start_dev.sh
```

#### 3.2 直接启动

```bash
# 生产模式
nanobot run

# 开发模式
nanobot run --dev
```

#### 3.3 命令行参数

```bash
nanobot run [OPTIONS]

选项：
  --config PATH          配置文件路径 (默认: config/nanobot_config.yaml)
  --secrets PATH         密钥文件路径 (默认: config/secrets.yaml)
  --data-dir PATH        数据存储目录 (默认: data/)
  --dev                  开发模式
  --debug                启用调试日志
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                         日志级别
  --help                 显示帮助信息
```

## 验证安装

### 1. 检查 Nanobot 版本

```bash
nanobot --version
```

### 2. 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_bot.py

# 运行测试并生成覆盖率报告
pytest --cov=nanobot tests/
```

### 3. 访问 API（如果启用）

如果在配置中启用了 API 服务器，可以通过以下方式访问：

```bash
# 检查服务器是否运行
curl http://localhost:8000/health

# 获取版本信息
curl http://localhost:8000/version
```

## 常见问题

### 1. 端口被占用

```bash
# 查找占用端口的进程
lsof -ti :8000

# 杀死进程
kill -9 <PID>
```

### 2. 依赖包安装失败

```bash
# 更新 pip 和 wheel
pip install --upgrade pip wheel

# 清理并重新安装依赖
pip cache purge
pip install -e .[dev]
```

### 3. 配置文件问题

```bash
# 检查配置文件语法
python -c "import yaml; print(yaml.safe_load(open('config/nanobot_config.yaml')))"

# 检查密钥文件
python -c "import yaml; print(yaml.safe_load(open('config/secrets.yaml')))"
```

### 4. 日志查看

```bash
# 查看系统日志
tail -f logs/nanobot.log

# 查看错误日志
grep -i "ERROR" logs/nanobot.log
```

## 部署架构

### 单节点部署

```
┌─────────────────────────────────────────────────────────┐
│                  服务器节点                              │
│ ┌──────────────────────┐  ┌──────────────────────┐      │
│ │    Nanobot 主进程     │  │    后台任务调度器      │      │
│ │  - 消息处理引擎      │  │  - 定时任务执行器      │      │
│ │  - 插件管理系统      │  │  - 缓存管理          │      │
│ │  - API 服务器        │  │  - 资源监控          │      │
│ └──────────────────────┘  └──────────────────────┘      │
│                          ┌──────────────────────┐      │
│                          │    数据存储            │      │
│                          │  - SQLite 数据库      │      │
│                          │  - 本地文件存储        │      │
│                          └──────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

### 多节点部署（高级）

```
┌─────────────────────────────────────────────────────────┐
│                  负载均衡器                              │
└─────────────────┬─────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼───────┐  ┌───────▼───────┐
│   应用服务器1   │  │   应用服务器2   │
│ ┌───────────┐ │  │ ┌───────────┐ │
│ │ Nanobot  │ │  │ │ Nanobot  │ │
│ └───────────┘ │  │ └───────────┘ │
└───────────────┘  └───────────────┘
        │                   │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │    共享数据存储     │
        │ ┌───────────────┐ │
        │ │  Redis 缓存    │ │
        │ └───────────────┘ │
        │ ┌───────────────┐ │
        │ │ PostgreSQL DB  │ │
        │ └───────────────┘ │
        └───────────────────┘
```

## 性能优化

### 1. 内存优化

```yaml
# 在 nanobot_config.yaml 中
performance:
  cache_size: 1000
  max_memory_usage: "4GB"
  gc_threshold: 0.8
```

### 2. 并发优化

```yaml
# 在 nanobot_config.yaml 中
concurrency:
  max_workers: 4
  task_queue_size: 1000
  timeout: 300
```

### 3. 日志优化

```yaml
# 在 nanobot_config.yaml 中
logging:
  level: "INFO"
  file_rotation: "500MB"
  file_retention: 30
  compression: "gzip"
```

## 安全建议

### 1. 密钥管理

- 不要将 `secrets.yaml` 提交到版本控制系统
- 使用环境变量替代硬编码的密钥
- 定期轮换 API 密钥

### 2. 访问控制

```yaml
# 在 secrets.yaml 中
telegram:
  allowed_users:
    - "user1"
    - "user2"

api:
  enabled: true
  cors_allowed_origins:
    - "http://localhost:3000"
  rate_limiting:
    enabled: true
    requests_per_minute: 60
```

### 3. 网络安全

- 使用 HTTPS 协议
- 配置防火墙规则
- 定期更新依赖包

## 备份与恢复

### 1. 数据备份

```bash
# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

# 备份数据文件
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/

# 备份整个项目
tar -czf nanobot_backup_$(date +%Y%m%d).tar.gz --exclude='temp_venv' --exclude='*.pyc' .
```

### 2. 数据恢复

```bash
# 恢复配置文件
tar -xzf config_backup_20231225.tar.gz

# 恢复数据文件
tar -xzf data_backup_20231225.tar.gz
```

## 版本升级

### 1. 备份数据

```bash
# 按照上面的备份步骤执行
```

### 2. 更新代码

```bash
git pull origin main
```

### 3. 重新安装依赖

```bash
pip install -e .[dev]
```

### 4. 重启服务

```bash
./scripts/start_nanobot.sh
```

## 监控与维护

### 1. 系统监控

```bash
# 查看进程状态
ps aux | grep nanobot

# 查看系统资源使用情况
top -p $(pgrep -f "nanobot")
```

### 2. 日志分析

```bash
# 查看最近 100 行日志
tail -n 100 logs/nanobot.log

# 查看错误日志统计
grep -i "ERROR" logs/nanobot.log | awk '{print $2}' | sort | uniq -c | sort -rn
```

### 3. 自动化监控

```bash
# 使用 cron 定时检查服务状态
0 * * * * /path/to/nanobot/scripts/check_health.sh
```

## 故障排除

### 1. 服务无法启动

```bash
# 检查端口占用
lsof -ti :8000

# 检查配置文件
python -c "import yaml; print(yaml.safe_load(open('config/nanobot_config.yaml')))"

# 检查日志
tail -n 50 logs/nanobot.log
```

### 2. 插件无法加载

```bash
# 检查插件目录结构
ls -la nanobot/plugins/

# 检查插件配置
grep -A 10 "plugins" config/nanobot_config.yaml

# 检查插件导入错误
grep -i "import" logs/nanobot.log
```

### 3. LLM 响应失败

```bash
# 检查 API 密钥
grep "api_key" config/secrets.yaml

# 检查网络连接
curl -I https://api.openai.com/

# 检查 API 响应
curl -X GET https://api.openai.com/v1/models -H "Authorization: Bearer $(grep "openai_api_key" config/secrets.yaml | awk '{print $2}')"
```

---

## 许可证

本文档和 Nanobot 项目遵循 MIT 许可证。
