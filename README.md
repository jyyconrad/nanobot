# Nanobot - 轻量级 AI Agent 框架

> **版本**: v0.4.4
> **Python**: >=3.11
> **许可证**: MIT

---

## 🎯 项目概述

Nanobot 是一个轻量级的个人 AI 助手框架，专注于代码质量提升、测试修复、文档生成和项目管理。

### 核心特性

- **多渠道支持**: Telegram、飞书、WhatsApp、Matrix、CLI
- **任务识别与规划**: 自动识别用户意图，分解复杂任务
- **多 Agent 协作**: 基于 Agno 框架的 Subagent 系统
- **上下文管理**: 智能上下文压缩和记忆系统
- **工具集成**: MCP (Model Context Protocol) 服务器支持
- **技能系统**: 可扩展的技能加载机制
- **安全防护**: 路径遍历防护、API 密钥热加载
- **心跳机制**: 虚拟工具调用决策，静默心跳降低 API 成本

---

## 📦 安装

```bash
pip install nanobot-ai
```

### 开发模式安装

```bash
git clone https://github.com/jyyconrad/nanobot.git
cd nanobot
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 可选依赖

```bash
# 飞书渠道
pip install nanobot-ai[feishu]

# Matrix 渠道
pip install nanobot-ai[matrix]
```

---

## ⚡ 快速开始

### 1. 配置

创建 `~/.nanobot/config.json`:

```json
{
  "providers": {
    "openai": {
      "apiKey": "your-api-key",
      "model": "gpt-4"
    }
  }
}
```

### 2. 启动 Gateway

```bash
nanobot gateway --port 18791
```

### 3. 使用 Agent

```bash
# 单次查询
nanobot agent -m "帮我检查这段代码质量"

# 交互模式
nanobot agent
```

---

## 🏗️ 项目结构

```
nanobot/
├── nanobot/              # 核心代码
│   ├── agents/           # Agno Agent 实现
│   ├── agent/            # 旧架构 Agent（兼容）
│   ├── bus/              # 消息总线
│   ├── channels/         # 通信渠道
│   ├── config/           # 配置管理
│   ├── commands/         # 命令系统
│   ├── providers/        # LLM Provider
│   └── utils/            # 工具函数
├── tests/                # 测试
├── docs/                 # 文档中心
├── upgrade-plan/         # 升级计划
└── reports/              # 报告归档
```

---

## 📚 文档

- [文档中心](docs/README.md) - 完整技术文档
- [架构总览](docs/architecture/overview.md) - 系统架构设计
- [升级计划](upgrade-plan/MASTER-UPGRADE-OVERVIEW.md) - v0.2.0 升级方案
- [部署指南](docs/deployment/DEPLOYMENT.md) - 部署和运维

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_prompt_system_v2.py -v

# 生成覆盖率报告
pytest tests/ --cov=nanobot --cov-report=html
```

---

## 🚀 开发

### 分支策略

- `main`: 主分支，生产代码
- `dev/*`: 开发分支
- `feat/*`: 新功能
- `fix/*`: Bug 修复

### 提交规范

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
test: 添加测试
refactor: 重构代码
```

---

## 📊 当前状态

### v0.2.0 升级进度

| 阶段 | 状态 | 完成度 |
|------|------|--------|
| Phase 0: Agno 框架集成 | ✅ 已完成 | 100% |
| Phase 1: 方案确认和准备 | ✅ 已完成 | 100% |
| Phase 2: 提示词系统 | ⚠️ 部分完成 | 60% |
| Phase 3-6: 任务管理系统 | ⏸ 未开始 | 0% |

详见: [升级计划](upgrade-plan/MASTER-UPGRADE-OVERVIEW.md)

---

## 🤝 贡献

欢迎贡献！请查看[贡献指南](docs/development/CONTRIBUTING.md)。

---

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🔗 链接

- [GitHub 仓库](https://github.com/jyyconrad/nanobot)
- [Issue Tracker](https://github.com/jyyconrad/nanobot/issues)
- [更新日志](CHANGELOG.md)

---

**最后更新**: 2026-02-10
