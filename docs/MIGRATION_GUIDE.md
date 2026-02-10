# Nanobot 迁移指南

## 从 v0.1.x 迁移到 v0.2.0

本指南帮助您从 Nanobot v0.1.x 版本迁移到 v0.2.0 版本。

## 主要变更

### 1. 提示词系统

**变更**: 引入了 PromptSystemV2

**影响**: 
- 旧的提示词系统仍然可用
- 建议逐步迁移到新的提示词系统

**迁移步骤**:
1. 创建 `nanobot/config/prompts/` 目录
2. 复制提示词文件到新目录
3. 更新配置文件使用新的提示词系统

### 2. Agent 架构

**变更**: 引入了基于 Agno 框架的 Agent

**影响**:
- 旧的 Agent 仍然可用
- 新的 Agent 提供更好的功能和性能

**迁移步骤**:
1. 安装 Agno 框架: `pip install agno`
2. 更新 Agent 初始化代码
3. 测试新的 Agent 功能

### 3. 配置文件

**变更**: 配置文件结构有所调整

**影响**: 需要更新配置文件

**迁移步骤**:
1. 备份现有配置
2. 根据新的配置 schema 更新配置文件
3. 验证配置是否正确

## 数据迁移

### 任务数据

任务数据存储在 `data/memory/memories.json` 中。

新版本兼容旧版本的数据格式，无需迁移。

### 会话数据

会话数据存储在 `data/sessions/` 目录中。

新版本兼容旧版本的会话数据，无需迁移。

## 回滚

如果遇到问题，可以回滚到 v0.1.x 版本：

```bash
git checkout v0.1.x
pip install -r requirements.txt
```

## 常见问题

### Q: 新版本的性能如何？

A: v0.2.0 引入了 Agno 框架，性能有显著提升。

### Q: 是否需要修改现有代码？

A: 大部分情况下不需要。新的 Agent 兼容旧版本的接口。

### Q: 如何获取帮助？

A: 如遇问题，请访问 [GitHub Issues](https://github.com/example/nanobot/issues)

## 支持

如有任何问题，请联系我们的支持团队。
