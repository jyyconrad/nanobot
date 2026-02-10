# Nanobot Opencode 集成使用指南

## 概述

Nanobot v0.2.0 已成功集成 Opencode 组件支持，包括：
- 配置驱动的技能加载
- MCP 服务器支持
- 命令系统（6 个核心命令）
- 工作流编排系统
- 多 Agent 编排和协调

---

## 配置 Opencode 集成

### 基础配置

在 `~/.nanobot/config.json` 中添加以下配置：

```json
{
  "opencode": {
    "enabled": true,
    "skills": {
      "enabled": true,
      "source_dir": "/path/to/opencode/skills",
      "skills": ["skill1", "skill2", "skill3"]
    },
    "commands": {
      "enabled": true,
      "source_dir": "/path/to/opencode/commands",
      "commands": ["review", "test", "commit"]
    },
    "agents": {
      "enabled": true,
      "source_dir": "/path/to/opencode/agents",
      "agents": ["code-reviewer", "frontend-developer"]
    }
  }
}
```

### 配置选项

| 配置项 | 说明 | 默认值 |
|---------|------|---------|
| `enabled` | 是否启用 Opencode 集成 | false |
| `source_dir` | Opencode 源目录路径 | `~/.config/opencode/xxx` |
| `skills` | 要加载的 skills 列表 | `[]` (全部) |
| `commands` | 要注册的命令列表 | `[]` (全部) |
| `agents` | 要注册的 agents 列表 | `[]` (全部) |

---

## 命令系统

### 可用命令

启动 gateway 后，可以通过以下命令与 Nanobot 交互：

| 命令 | 功能 | 别名 |
|------|------|------|
| `/review` | 代码审查 | `/cr` |
| `/test` | 运行测试 | |
| `/commit` | Git 提交 | |
| `/fix` | Bug 修复 | |
| `/optimize` | 代码优化 | |
| `/debug` | 系统调试 | |

### 命令示例

#### 代码审查
```
/review nanobot/agent/loop.py
```

#### 运行测试
```
/test
```

#### 提交代码
```
/commit "fix: 修复用户认证bug"
```

---

## MCP 服务器支持

### MCP 客户端

Nanobot 内置了 MCP (Model Context Protocol) 客户端，可以连接到 MCP 服务器并使用其提供的工具。

### 配置 MCP 服务器

在 `~/.nanobot/config.json` 中添加 MCP 服务器配置：

```json
{
  "opencode": {
    "mcp_servers": {
      "filesystem": {
        "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"],
        "env": {}
      },
      "brave-search": {
        "command": ["npx", "-y", "@modelcontextprotocol/server-brave-search"],
        "env": {
          "BRAVE_API_KEY": "your-api-key"
        }
      }
    }
  }
}
```

### 使用 MCP 工具

MCP 工具会自动集成到 Nanobot 的工具注册表中，可以在聊天中直接使用：

```
请使用 MCP 文件系统工具读取 /path/to/file.txt
```

---

## 工作流编排系统

### 创建工作流

使用 `workflow create` 命令创建新工作流：

```
/workflow create "代码质量检查工作流"
```

### 工作流执行

工作流会自动编排多个任务的执行顺序，支持：
- 串行执行
- 并行执行
- 任务依赖管理
- 失败重试

### 工作流状态管理

- 查看工作流状态
- 暂停/继续工作流
- 取消工作流

---

## 多 Agent 调用

### Expert Agents

Nanobot 支持多个 Expert Agents，每个 Agent 专注于特定领域：

| Agent | 领域 | 描述 |
|-------|------|------|
| `code-reviewer` | 代码审查 | 专注于代码质量和安全 |
| `frontend-developer` | 前端开发 | 专注于前端框架和 UI |
| `backend-developer` | 后端开发 | 专注于 API 和服务端 |

### Agent 调度

Nanobot 可以智能调度多个 Agent 处理复杂任务：

- **串行调度**：Agent 依次执行任务
- **并行调度**：多个 Agent 同时处理独立任务
- **依赖管理**：确保 Agent 间的任务依赖关系正确

### Agent 协作

使用 Subagent API 创建和管理 Agent：

```
spawn 一个 subagent 来处理代码审查任务
```

---

## 开发指南

### 添加自定义 Skill

1. 在 Opencode skills 目录创建新的 Skill
2. 编写 SKILL.md 文件
3. 在配置中添加 Skill 名称

### 添加自定义命令

1. 在 `nanobot/commands/` 目录创建新的命令文件
2. 继承 Command 基类
3. 在命令注册表中注册

### 添加自定义 Expert Agent

1. 在 `nanobot/agent/experts/` 目录创建新的 Agent
2. 继承 ExpertAgent 基类
3. 在 Agent 注册表中注册

---

## 测试和验证

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 查看覆盖率
coverage report

# 运行特定测试
pytest tests/test_opencode_integration.py
```

### 检查配置

```bash
# 查看配置
nanobot status

# 验证 Opencode 集成状态
cat ~/.nanobot/config.json | grep opencode
```

---

## 故障排除

### Skill 加载失败

1. 检查 source_dir 路径是否正确
2. 确认 Skill 文件名正确
3. 检查 SKILL.md 格式是否正确

### 命令不工作

1. 确认命令已在注册表中注册
2. 检查命令别名配置
3. 查看 Agent Loop 日志

### MCP 连接失败

1. 检查 MCP 服务器是否运行
2. 确认配置中的 command 和 env
3. 查看网络连接

---

## 性能优化

### 启动优化

- 使用 `--model` 指定合适的模型
- 调整 `max_tool_iterations` 控制工具调用次数
- 启用 Skill 缓存减少重复加载

### 内存优化

- 使用上下文压缩减少内存占用
- 定期清理旧会话数据
- 限制并发 Agent 数量

---

## 更新日志

### v0.2.0 (2026-02-08)

- ✅ 完成 Opencode 集成计划的基础设施搭建
- ✅ 实现配置驱动的技能加载
- ✅ 添加 6 个核心命令
- ✅ 实现 MCP 服务器支持
- ✅ 实现工作流编排系统
- ✅ 实现多 Agent 编排和协调
- ✅ 编写完整测试用例（398 个测试全部通过）

### 后续计划

- 完善文档和示例
- 添加更多 Opencode skills
- 优化性能和内存使用
- 增强错误处理和日志

---

## 联系方式

- **GitHub**: https://github.com/jiangyayun/nanobot
- **Issues**: https://github.com/jiangyayun/nanobot/issues
- **文档**: docs/ 目录

---

感谢使用 Nanobot！

如有问题或建议，欢迎通过 GitHub Issues 反馈。
