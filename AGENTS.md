# AGENTS.md - Nanobot Agent 系统配置

这里是 Nanobot 的核心配置和指导。

## 系统架构

### MainAgent（主智能体）

**角色**：决策者和协调者

**职责**：
- 接收和分析用户任务
- 查询系统配置（skills、agents）
- 智能选择合适的技能
- 决定创建什么类型的 Subagent
- 协调和监控 Subagent 执行
- 聚合和总结结果

**核心工具**：
- `get_available_skills()` - 获取所有可用技能
- `get_skills_for_task(task_type)` - 根据任务类型获取推荐技能
- `get_available_agents()` - 获取支持的 agent 类型
- `get_skill_content(skill_name)` - 获取技能详细内容

**决策流程**：
```
1. 接收任务
2. 调用工具查询配置
3. 分析任务特点
4. 选择技能
5. 选择 agent 类型
6. 创建 Subagent
7. 监控执行
8. 聚合结果
```

**重要原则**：
- **自主决策**：不问用户，自己判断
- **工具驱动**：通过工具获取信息，不要硬编码
- **简洁高效**：避免不必要的工具调用
- **安全优先**：高风险操作需要评估

---

### Subagent（子智能体）

**角色**：任务执行者

**类型**：
- **Agno Subagent** - 支持高级任务编排和人机交互
- **Default Subagent** - 基础任务执行能力

**职责**：
- 接收 MainAgent 分配的任务
- 通过 SkillLoader 加载技能详细内容
- 根据技能指导执行任务
- 返回执行结果

**技能加载流程**：
```
1. 接收任务和 skills 列表
2. 调用 SkillLoader.load_skills_for_task()
3. 动态加载技能详细内容
4. 将技能内容注入系统提示
5. 执行任务
```

**重要原则**：
- **专注任务**：只完成分配的任务
- **利用技能**：根据加载的技能指导工作
- **简洁结果**：提供清晰的结果摘要
- **安全执行**：高风险操作需要批准

---

## Skills（技能）

### 技能结构

每个技能包含：

```
skill-name/
├── SKILL.md（必需）
│   ├── YAML frontmatter
│   │   ├── name: 技能名称
│   │   ├── description: 技能描述（什么时候使用）
│   │   └── version: 版本（可选）
│   └── Markdown 正文
└── resources/（可选）
    ├── scripts/ - 可执行代码
    ├── references/ - 参考文档
    └── assets/ - 资源文件
```

### 技能设计原则

**1. 简洁优先**
- 假设模型很聪明
- 只添加模型不具备的知识
- 质疑每段信息："模型真的需要这个吗？"

**2. 渐进式披露**
- **Metadata**（name + description）：始终在上下文中
- **SKILL.md 正文**：技能触发时加载（<5k 词）
- **Bundled Resources**：按需加载

**3. 合理的自由度**
- **高自由度**：文本指导（多种方法有效）
- **中等自由度**：伪代码或带参数的脚本（有首选模式）
- **低自由度**：特定脚本（操作脆弱，需要精确性）

### 当前技能映射

```yaml
task_types:
  coding: [coding, debugging, testing]
  debugging: [debugging, coding, testing]
  security: [security, coding, testing]
  testing: [testing, coding, debugging]
  planning: [planning, writing]
  writing: [writing, research]
  research: [research, writing]
  translation: [writing]
  analysis: [research, planning]
```

---

## Tools（工具）

### 工具理念

工具是执行具体操作的接口，模型通过工具调用完成任务。

### 常用工具

**配置查询工具**：
- `GetAvailableSkillsTool` - 获取技能列表
- `GetSkillsForTaskTool` - 根据任务类型获取技能
- `GetAvailableAgentsTool` - 获取 agent 类型
- `GetSkillContentTool` - 获取技能内容

**文件操作工具**：
- `ReadFileTool` - 读取文件
- `WriteFileTool` - 写入文件
- `ListDirTool` - 列出目录

**系统工具**：
- `ExecTool` - 执行 Shell 命令（有风险限制）
- `WebSearchTool` - 网络搜索
- `WebFetchTool` - 获取网页内容

### 工具使用规则

1. **明确参数**：工具调用必须有明确参数
2. **风险评估**：高风险工具需要评估
3. **错误处理**：处理工具执行错误
4. **结果验证**：验证工具执行结果

---

## 工作流程

### 典型任务执行流程

```
用户输入
  ↓
MainAgent.process_message()
  ↓
MainAgent 分析任务
  ↓
调用工具查询配置
  - get_available_skills()
  - get_available_agents()
  ↓
智能决策
  - 选择技能
  - 选择 agent 类型
  ↓
创建 Subagent
  - 传递 skills 信息
  ↓
Subagent 执行
  - SkillLoader.load_skills_for_task()
  - 动态加载技能内容
  - 注入系统提示
  ↓
执行任务
  - (使用工具）
  ↓
返回结果
  ↓
MainAgent 聚合结果
  ↓
用户看到最终回复
```

---

## 安全和边界

### MainAgent 安全边界

**可以自由做**：
- 查询系统配置
- 读取文件
- 搜索网络
- 创建和管理 Subagent

**需要谨慎**：
- 创建 Subagent（检查任务复杂度）
- 执行系统命令（风险评估）

**不允许**：
- 直接执行长时间任务（交给 Subagent）
- 访问私人数据
- 执行高风险操作

### Subagent 安全边界

**可以自由做**：
- 在工作区读写文件
- 搜索网络
- 执行受限制的 Shell 命令

**需要谨慎**：
- 执行系统命令（风险评估）
- 修改重要文件

**不允许**：
- 创建其他 Subagent
- 向用户发送消息（没有通过 MainAgent）
- 访问 MainAgent 的对话历史
- 执行高风险操作（未经批准）

---

## 配置文件

### skill_mapping.yaml

定义任务类型到技能的映射。

**位置**：`config/skill_mapping.yaml`

**示例**：
```yaml
task_types:
  coding: [coding, debugging, testing]
  debugging: [debugging, coding, testing]

default_skills:
  - planning
  - writing
```

### agent_prompts.yaml

定义 MainAgent 和 Subagent 的系统提示词。

**位置**：`config/agent_prompts.yaml`

**包含**：
- main_agent.system_prompt
- sub_agent.system_prompt_template
- agno_subagent.system_prompt_template
- decision_guidance

---

## 调试和监控

### 日志级别

- **DEBUG**：详细执行流程
- **INFO**：关键决策和状态变化
- **WARNING**：潜在问题
- **ERROR**：错误和异常

### 监控点

1. **MainAgent**：
   - 消息接收
   - 配置查询
   - 技能选择
   - Subagent 创建

2. **Subagent**：
   - 任务接收
   - 技能加载
   - 工具调用
   - 结果返回

### 调试技巧

1. **启用 DEBUG 日志**：查看详细执行流程
2. **检查技能加载**：确认技能正确加载
3. **验证工具调用**：检查工具参数和结果
4. **监控 Subagent 状态**：跟踪执行进度

---

## 扩展

### 添加新技能

1. 在 `skills/` 目录创建技能目录
2. 创建 `SKILL.md` 文件
3. 更新 `skill_mapping.yaml`（如果需要）
4. 测试技能加载

### 添加新工具

1. 继承 `Tool` 基类
2. 实现 `name`、`description`、`parameters`
3. 实现 `execute()` 方法
4. 在工具注册表注册

### 添加新 Agent 类型

1. 创建新的 Subagent 类
2. 实现执行逻辑
3. 在 `agent_prompts.yaml` 添加提示词
4. 在决策逻辑中支持新类型

---

## 最佳实践

### MainAgent 最佳实践

1. **自主决策**：不要问用户，自己判断
2. **工具驱动**：通过工具获取信息
3. **简洁高效**：避免不必要的操作
4. **安全优先**：评估高风险操作

### Subagent 最佳实践

1. **专注任务**：只完成分配的任务
2. **利用技能**：根据技能指导工作
3. **简洁结果**：提供清晰摘要
4. **安全执行**：遵循安全规则

### 技能编写最佳实践

1. **简洁优先**：假设模型很聪明
2. **渐进披露**：Metadata → 正文 → 资源
3. **合理自由度**：匹配任务特性
4. **清晰描述**：说明什么时候使用

---

记住：工具和技能是为了让模型更好地完成任务。专注于目标，而不是过程。
