# Nanobot 项目

## 项目概述
Nanobot 是一个超轻量级的个人 AI 助手，具有任务识别、规划、执行和用户响应生成等功能。项目的目标是实现一个功能完整、代码质量高、测试覆盖率良好的 AI 助手。

## 项目特点
- **任务识别**：使用正则表达式和关键词匹配
- **任务规划**：使用复杂度分析和任务分解
- **任务执行**：使用子代理系统和工具调用
- **用户响应生成**：使用自然语言生成和模板
- **上下文管理**：使用历史消息和状态信息

## 项目架构

### 核心组件
- **MainAgent**：主要的 Agent 入口点
- **Planner Agent**：任务规划和调度
- **Decision Agent**：决策和任务执行
- **Subagent Manager**：子代理生命周期管理
- **Context Manager**：上下文和状态管理
- **Memory Agent**：记忆和历史记录管理
- **Skill Loader**：技能加载和管理

### 内置技能
- **GitHub 技能**：与 GitHub API 交互
- **Skill Creator 技能**：用于创建新技能
- **Summarize 技能**：文本摘要生成
- **Tmux 技能**：与 Tmux 终端多路复用器交互
- **Weather 技能**：天气信息获取

## 安装和使用

### 安装方法
```bash
pip install nanobot
```

### 使用方法
```bash
nanobot --help
```

## 项目文档

### 主要文档
- **项目完成报告**：`PROJECT_COMPLETED.md`
- **任务完成总结**：`TASK_FINISHED.md`
- **文档更新记录**：`CHANGELOG.md`
- **工具使用说明**：`TOOLS.md`
- **实施过程记录**：`IMPLEMENTATION_LOG.md`
- **心跳检查**：`HEARTBEAT.md`
- **发布说明**：`RELEASE_NOTES.md`

### 项目架构和设计
- **项目架构**：`ARCHITECTURE.md`
- **任务流程**：`WORKFLOW.md`
- **实施计划**：`IMPLEMENTATION_PLAN.md`
- **实施总结**：`IMPLEMENTATION_SUMMARY.md`

### 开发和维护
- **开发指南**：`DEVELOPMENT_GUIDE.md`
- **测试覆盖**：`TEST_COVERAGE.md`
- **代码质量**：`CODE_QUALITY.md`
- **性能优化**：`PERFORMANCE_OPTIMIZATION.md`

## 贡献者
- **jyyconrad**：项目实施和维护

## 许可证
- **MIT License**：项目使用 MIT 许可证

## 联系方式
- **GitHub 仓库**：https://github.com/jyyconrad/nanobot
- **问题反馈**：https://github.com/jyyconrad/nanobot/issues
