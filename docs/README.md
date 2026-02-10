# Nanobot 文档中心

欢迎来到 Nanobot 文档中心。本文档提供 Nanobot 项目的完整技术文档。

## 📚 文档导航

### 🏗️ [架构文档](./architecture/)
了解 Nanobot 的整体架构设计。

- **[架构总览](./architecture/overview.md)** - 系统架构概览（C4 Model Level 1）
- **[组件详情](./architecture/components/)** - 核心组件详细设计
  - [MainAgent](./architecture/components/main-agent.md) - 主代理
  - [Subagent](./architecture/components/subagent.md) - 子代理系统
  - [Task Planner](./architecture/components/task-planner.md) - 任务规划器
  - [Decision Maker](./architecture/components/decision-maker.md) - 决策系统
  - [Context Manager](./architecture/components/context-manager.md) - 上下文管理
  - [Message Router](./architecture/components/message-router.md) - 消息路由
  - [Workflow Manager](./architecture/components/workflow-manager.md) - 工作流管理
  - [Skill System](./architecture/components/skill-system.md) - 技能系统
- **[数据模型](./architecture/data-model.md)** - 数据模型和ERD图 ⭐
- **[数据流](./architecture/data-flow.md)** - 数据流图
- **[架构决策](./architecture/decisions/)** - 架构决策记录(ADR)

### 🔌 [API 文档](./api/)
了解如何使用 Nanobot 的 API。

- **[核心 API](./api/core-api.md)** - MainAgent 等核心接口
- **[工具 API](./api/tools-api.md)** - 工具系统接口
- **[渠道 API](./api/channels-api.md)** - 通信渠道接口

### 🚀 [部署运维](./deployment/)
部署和运维 Nanobot。

- **[部署指南](./deployment/DEPLOYMENT.md)** - 安装和配置
- **[运维手册](./deployment/OPERATIONS.md)** - 监控和日志
- **[故障排查](./deployment/TROUBLESHOOTING.md)** - 常见问题

### 💻 [开发指南](./development/)
参与 Nanobot 开发。

- **[贡献指南](./development/CONTRIBUTING.md)** - 如何贡献代码
- **[测试指南](./development/testing.md)** - 测试策略和方法

### 🤖 [AI 能力](./ai-file-system/)
AI 能力文档（保留）。

- [系统概述](./ai-file-system/01-system-overview.md)
- [需求分析](./ai-file-system/02-requirements.md)
- [架构设计](./ai-file-system/03-architecture.md)
- [数据模型](./ai-file-system/04-data-model.md)
- [API 设计](./ai-file-system/05-api-design.md)
- [AI 能力](./ai-file-system/06-ai-capabilities.md)

### 📦 [归档文档](./archive/)
历史文档（已过时）。

- [归档说明](./archive/README.md)

---

## 🎯 快速开始

1. **了解系统**: 阅读[架构总览](./architecture/overview.md)
2. **查看数据模型**: 查看[数据模型文档](./architecture/data-model.md) ⭐
3. **部署系统**: 参考[部署指南](./deployment/DEPLOYMENT.md)
4. **参与开发**: 查看[贡献指南](./development/CONTRIBUTING.md)

---

## 📝 文档维护

本文档遵循以下原则：

- **单一事实来源**: 每个主题只在一份文档中详细描述
- **代码即文档**: 文档与代码同步更新
- **渐进式披露**: 从概览到细节的层次结构
- **可操作性**: 提供具体的代码示例和命令

---

**最后更新**: 2026-02-10  
**文档版本**: v1.0.0  
**维护者**: Nanobot Team
