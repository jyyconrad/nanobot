# Nanobot 项目

## 项目概述
Nanobot 是一个超轻量级的个人 AI 助手，具有任务识别、规划、执行和用户响应生成等功能。项目的目标是实现一个功能完整、代码质量高、测试覆盖率良好的 AI 助手。

**项目特点**：
- **任务识别**：使用正则表达式和关键词匹配
- **任务规划**：使用复杂度分析和任务分解
- **任务执行**：使用子代理系统和工具调用
- **用户响应生成**：使用自然语言生成和模板
- **上下文管理**：使用历史消息和状态信息

## 项目版本
- **当前版本**: v0.2.0
- **发布日期**: 2026-02-08
- **开发状态**: 生产就绪

## 核心功能

### 1. Opencode 组件集成 ✅
Nanobot 现已支持完整的 Opencode 组件集成，包括：

#### 配置驱动的技能加载
- 通过 `~/.nanobot/config.json` 控制是否加载 opencode
- 支持指定要加载的 skills 列表
- 支持直接读取源文件（无需复制）
- 多优先级加载（workspace > builtin > opencode）

#### Opencode Skills
- 支持从配置加载 opencode skills
- 支持以下 skills：
  - `opencode` - Opencode 编码助手集成

#### 示例配置
```json
{
  "opencode": {
    "enabled": true,
    "skills": {
      "enabled": true,
      "source_dir": "/Users/jiangyayun/.openclaw/workspace/skills",
      "skills": ["opencode"]
    }
  }
}
```

### 2. MCP 服务器支持 ✅
Nanobot 已完整实现 MCP (Model Context Protocol) 服务器支持：
- MCP 客户端实现 (`nanobot/agent/tools/mcp.py`)
- 服务器连接管理
- 工具发现和调用
- 集成到 ToolRegistry

### 3. 命令系统 ✅
Nanobot 现已支持完整的命令系统，包括 6 个核心命令：

| 命令 | 功能 | 别名 |
|------|------|------|
| `/review` | 代码审查 | `/cr` |
| `/optimize` | 代码优化 | - |
| `/test` | 运行测试 | - |
| `/commit` | Git 提交 | - |
| `/fix` | Bug 修复 | - |
| `/debug` | 系统调试 | - |

#### 使用示例
```bash
# 直接在命令行使用
nanop agent -m "/review nanobot/agent/loop.py"

# 在聊天中使用（如果启用了通道）
/review nanobot/agent/loop.py
```

### 4. 工作流编排系统 ✅
Nanobot 已完整实现工作流编排系统，包括：
- 工作流管理器 (`agent/workflow/workflow_manager.py`)
- 任务状态跟踪
- 配置加载和保存
- MainAgent 集成

#### 使用示例
```python
from nanobot.agent.workflow.workflow_manager import WorkflowManager

# 创建工作流
workflow = WorkflowManager()
workflow.create("代码质量检查", steps=[...])

# 执行工作流
workflow.execute()
```

### 5. 多 Agent 调用 ✅
Nanobot 已完整实现多 Agent 调用系统，包括：
- Expert Agent 系统架构
- Agent 注册表
- 任务调度和协调
- 并行/串行执行支持

#### 使用示例
```python
from nanobot.agent.subagent.manager import SubagentManager

# 创建 subagent
manager = SubagentManager()

# 并行执行
task1 = manager.spawn("task1")
task2 = manager.spawn("task2")

# 串行执行
task3 = manager.spawn("task3", depends_on=[task1, task2])
```

## 项目架构

```
nanobot/
├── agent/
│   ├── loop.py              # 增强：命令路由
│   ├── main_agent.py        # MainAgent 核心
│   ├── skills.py             # 增强：opencode 支持
│   ├── subagent/            # Subagent 管理
│   ├── workflow
│   │   ├── workflow_manager.py
│   │   ├── workflow_executor.py
│   │   └── ...
│   └── tools/
│       └── mcp.py             # MCP 客户端
├── commands/                   # 新增：命令系统
│   ├── base.py
│   ├── registry.py
│   ├── review.py
│   ├── optimize.py
│   ├── test.py
│   ├── commit.py
│   ├── fix.py
│   ├── debug.py
└── config/
│   └── schema.py             # 增强：OpencodeConfig
```

## 安装和使用

### 安装
```bash
pip install nanobot
```

### 配置
创建或编辑 `~/.nanobot/config.json`：

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "your-api-key"
    }
  },
  "opencode": {
    "enabled": true,
    "skills": {
      "enabled": true,
      "source_dir": "/Users/jiangyayun/.openclaw/workspace/skills",
      "skills": ["opencode"]
    }
  }
}
```

### 启动 Gateway
```bash
# 前台运行
nanobot gateway --port 18791

# 或指定端口
nanobot gateway --port 9910
```

### 命用 Agent
```bash
# 单次查询
nanobot agent -m "你好"

# 交互模式
nanobot agent
```

## 开发

### 项目结构
```bash
nanobot/
├── agent/
│   ├── loop.py
│   ├── main_agent.py
│   ├── context.py
│   ├── task.py
│   ├── skills.py
│   ├── tools/
│   ├── workflow/
│   └── ...
├── commands/
├── config/
├── channels/
├── tests/
└── docs/
```

### 运行测试
```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_mcp.py

# 运行测试并生成覆盖率
pytest tests/ --cov=nanobot --cov-report=html
```

## 文档

- **API.md**: API 文档
- **ARCHITECTURE.md**: 架构设计
- **docs/OPENCDOE_INTEGRATION_PLAN.md**: Opencode 集成计划
- **docs/WORKFLOW_DESIGN.md**: 工作流设计
- **CHANGELOG.md**: 更新日志

## 许可证
MIT License

## 联系方式
- GitHub: https://github.com/jyyconrad/nanobot
- Issues: https://github.com/jyyconrad/nanobot/issues
