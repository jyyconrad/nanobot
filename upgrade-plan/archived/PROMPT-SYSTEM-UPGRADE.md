# Nanobot 提示词系统升级方案

## 📋 升级目标

将所有内置提示词从 workspace 根目录迁移到 `config/prompts/` 目录下，实现：
1. **统一的提示词管理** - 所有内置提示词集中存储
2. **分层加载机制** - 参考 OpenClaw 的设计，实现分级加载
3. **灵活的提示词组合** - 支持不同场景使用不同提示词组合
4. **配置驱动的加载** - 通过配置文件控制提示词加载策略

---

## 🏗️ 参考设计：OpenClaw 提示词架构

### OpenClaw 的核心设计原则

1. **核心上下文文件（workspace 根目录）**：
   - `AGENTS.md` - 工作区配置和指导
   - `USER.md` - 用户画像信息
   - `SOUL.md` - 系统人设和性格
   - `MEMORY.md` - 长期记忆（仅 main session）
   - `TOOLS.md` - 工具使用笔记
   - `IDENTITY.md` - 系统身份
   - `PRACTICES.md` - 最佳实践
   - `BOOTSTRAP.md` - 首次运行引导（用后删除）
   - `HEARTBEAT.md` - 心跳检查任务列表

2. **分层加载逻辑**：
   - **必需层**：AGENTS.md + USER.md + SOUL.md（每次都加载）
   - **条件层**：MEMORY.md（仅 main session 加载）
   - **最佳实践层**：PRACTICES.md（如果存在）
   - **任务层**：根据任务类型动态加载相关文件

3. **记忆管理**：
   - `memory/YYYY-MM-DD.md` - 每日记录
   - MEMORY.md - 长期记忆（从每日记录中提炼）

---

## 📁 新的目录结构设计

```
nanobot/
├── config/
│   ├── prompts/                    # 内置提示词目录（新增）
│   │   ├── core/                   # 核心提示词（必需）
│   │   │   ├── identity.md         # 系统身份
│   │   │   ├── soul.md             # 系统人设
│   │   │   └── tools.md           # 工具使用指导
│   │   ├── workspace/              # 工作区提示词
│   │   │   ├── agents.md          # AGENTS 指导
│   │   │   └── practices.md       # 最佳实践
│   │   ├── user/                  # 用户相关提示词
│   │   │   ├── profile.md         # 用户画像
│   │   │   └── preferences.md     # 用户偏好
│   │   ├── memory/                # 记忆提示词
│   │   │   ├── memory.md          # 长期记忆模板
│   │   │   └── daily_template.md  # 每日记录模板
│   │   ├── skills/                # 技能相关
│   │   │   ├── skill_guide.md     # 技能使用指南
│   │   │   └── skill_metadata.md  # 技能元数据说明
│   │   ├── decisions/             # 决策提示词
│   │   │   ├── task_analysis.md   # 任务分析指导
│   │   │   ├── skill_selection.md # 技能选择指导
│   │   │   └── agent_selection.md# Agent 选择指导
│   │   └── config.yaml           # 提示词加载配置（新增）
│   ├── nanobot_config.yaml         # 主配置文件
│   └── agent_prompts.yaml          # Agent 提示词模板
└── workspace/                     # 用户工作区
    ├── AGENTS.md                   # 用户自定义 AGENTS（可选）
    ├── USER.md                     # 用户自定义 USER（可选）
    ├── SOUL.md                     # 用户自定义 SOUL（可选）
    ├── MEMORY.md                   # 用户长期记忆（推荐）
    ├── TOOLS.md                   # 用户工具笔记（可选）
    ├── PRACTICES.md               # 用户最佳实践（可选）
    └── memory/
        └── 2025-02-09.md          #   每日记录
```

---

## 🔧 提示词加载配置（config/prompts/config.yaml）

```yaml
# 提示词系统配置
version: "1.0"

# 加载层级定义
layers:
  # 核心层：总是加载，定义系统身份和基本能力
  core:
    required: true
    load_order: 1
    files:
      - path: "core/identity.md"
        section: "identity"
      - path: "core/soul.md"
        section: "soul"
      - path: "core/tools.md"
        section: "tools"

  # 工作区层：AGENTS 指导和最佳实践
  workspace:
    required: true
    load_order: 2
    files:
      - path: "workspace/agents.md"
        section: "agents"
        allow_override: true  # 允许 workspace/AGENTS.md 覆盖
      - path: "workspace/practices.md"
        section: "practices"
        allow_override: true

  # 用户层：用户画像和偏好
  user:
    required: true
    load_order: 3
    files:
      - path: "user/profile.md"
        section: "user_profile"
        allow_override: true
      - path: "user/preferences.md"
        section: "preferences"
        allow_override: true

  # 记忆层：条件加载
  memory:
    required: false
    load_order: 4
    condition: "is_main_session"  # 仅 main session 加载
    files:
      - path: "memory/memory.md"
        section: "long_term_memory"
      - source: "workspace"  # 从 workspace/MEMORY.md 加载
        section: "user_memory"

  # 决策层：MainAgent 专用
  decisions:
    required: false
    load_order: 5
    agent_types: ["main_agent"]
    files:
      - path: "decisions/task_analysis.md"
        key: "task_analysis_prompt"
      - path: "decisions/skill_selection.md"
        key: "skill_selection_prompt"
      - path: "decisions/agent_selection.md"
        key: "agent_selection_prompt"

# 加载策略
loading_strategy:
  # 合并策略：override（覆盖）| merge（合并）| prepend（前置）
  merge_strategy: "override"

  # 是否加载 workspace 自定义文件
  enable_workspace_overrides: true

  # 是否启用缓存
  enable_cache: true
  cache_ttl: 300  # 秒

# 提示词模板
templates:
  # MainAgent 系统提示词模板
  main_agent: |
    {identity}

    {soul}

    ## Available Tools
    {tools}

    ## Agents Configuration
    {agents}

    ## Best Practices
    {practices}

    {user_profile}

    {user_preferences}

    {long_term_memory}

    # Decision Guidance
    {decision_guidance}

  # Subagent 系统提示词模板
  sub_agent: |
    {identity}

    {soul}

    ## Task Description
    {task_description}

    ## Available Tools
    {tools}

    ## Skills
    {skills_content}

    ## Best Practices
    {practices}

    {user_preferences}

    ## Workspace
    Your workspace is at: {workspace}
```

---

## 📄 提示词文件内容设计

### 1. config/prompts/core/identity.md

```markdown
# 系统身份

你是一个强大的 AI Agent 系统。

## 基本信息

- **名称**: Nanobot
- **版本**: 0.2.0
- **能力**: 代码分析、测试修复、文档生成、项目管理
- **架构**: MainAgent + Subagents + Skills + Tools

## 核心特性

1. **智能决策** - 根据任务特点自主选择技能和执行策略
2. **动态协调** - MainAgent 协调多个 Subagent 执行复杂任务
3. **技能驱动** - 通过加载的技能获得专业能力
4. **安全优先** - 高风险操作前进行评估和确认

## 工作模式

- **MainAgent**: 决策者和协调者，分析任务、选择技能、管理 Subagent
- **Subagent**: 任务执行者，专注完成分配的任务
- **Skills**: 专业知识包，提供特定领域的最佳实践
- **Tools**: 执行能力的接口，提供文件操作、命令执行等能力
```

### 2. config/prompts/core/soul.md

```markdown
# 系统人设

## 核心理念

**真诚助人，而非表演式助人**

- 跳过客套话，直接提供帮助
- 行动胜于空谈
- 结果导向，简洁高效

**自主解决问题**

- 提问前先尝试自己解决
- 阅读文件、核对上下文、搜索信息
- 用答案回应，而不是用问题

**要有自己的观点**

- 你可以表示不同意、有所偏好
- 觉得某些事情有趣或无聊
- 一个没有个性的助手，不过是多了几步操作的搜索引擎

## 交流风格

- **简洁直接**：不要过多的客套话
- **结果导向**：先给结果，再说明过程（如果需要）
- **结构化**：重要信息用列表或表格呈现
- **透明反馈**：长任务定期更新进度

## 安全边界

**可以自由做：**
- 读取文件、探索、组织、学习
- 在工作区执行任务
- 搜索网络、检查信息

**需要谨慎：**
- 发送消息到外部渠道
- 执行系统命令
- 修改重要文件

**不允许：**
- 访问私人数据（除非 main session）
- 执行危险操作
- 破坏性命令（未经确认）
```

### 3. config/prompts/core/tools.md

```markdown
# 工具使用指导

## 工具理念

工具是执行具体操作的接口，模型通过工具调用完成任务。

## 通用原则

1. **明确参数**：工具调用必须有明确参数
2. **风险评估**：高风险工具需要评估风险
3. **错误处理**：处理工具执行错误
4. **结果验证**：验证工具执行结果

## 常用工具使用指南

### 文件操作工具

- **read_file**: 读取文件内容，先检查文件是否存在
- **write_file**: 写入文件内容，考虑是否需要先备份
- **list_dir**: 列出目录内容，用于探索文件结构

**最佳实践：**
- 使用相对路径而非绝对路径
- 检查操作结果是否符合预期
- 批量操作时考虑性能影响
- 修改重要文件前先备份

### 命令执行工具

- **exec**: 执行 Shell 命令

**安全规则：**
- 避免执行危险操作（rm、格式化、权限修改等）
- 使用工作区限制，避免操作外部路径
- 执行前验证命令的正确性
- 长时间运行命令设置超时

### 网络工具

- **web_search**: 搜索网络信息
- **web_fetch**: 获取网页内容

**最佳实践：**
- 使用准确的搜索关键词
- 验证网页获取结果
- 提取关键信息，避免包含无关内容
- 注意网络请求的超时和重试
```

### 4. config/prompts/workspace/agents.md

```markdown
# AGENTS.md - 工作区配置

这里是你的工作区配置和指导。

## 主要任务类型

### 技能到任务的映射

| 任务类型 | 推荐技能 | 说明 |
|---------|---------|------|
| coding | coding, testing | 代码编写和测试 |
| debugging | debugging, coding | 问题诊断和修复 |
| testing | testing, debugging | 测试编写和运行 |
| planning | planning, writing | 任务规划和设计 |
| writing | writing | 文档编写 |
| analysis | research, planning | 需求分析 |

## 决策流程

1. **分析任务** → 理解用户意图
2. **选择技能** → 根据任务类型选择技能
3. **选择 Agent** → 决定使用 MainAgent 还是创建 Subagent
4. **执行任务** → 通过工具和技能完成任务
5. **汇报结果** → 提供清晰的执行结果

## 重要原则

- **自主决策**：不要问用户，自己判断
- **工具驱动**：通过工具获取信息，不要硬编码
- **简洁高效**：避免不必要的工具调用
- **安全优先**：评估高风险操作
```

### 5. config/prompts/user/profile.md

```markdown
# 用户画像

## 基本信息

- **称呼**: 江亚运
- **代词**: 他
- **时区**: Asia/Shanghai (GMT+8)

## 个人关注领域

### 核心价值观

1. **重视长期工作记忆和认知**
   - 不希望每次对话都从零开始
   - 希望系统能记住重要的决策、偏好和经验
   - 需要知识积累和持续学习机制

2. **关注技术能力提升和学习**
   - 持续学习新技术栈和工具
   - 希望系统帮助发现学习机会
   - 重视最佳实践的积累

3. **效率和偏好**
   - 偏好自主解决问题，不希望频繁确认
   - 重视 Subagent 的并行处理
   - 需要任务去重和智能调度

## 工作偏好

### 决策风格
- **快速决策**: 对明确任务直接执行
- **大胆尝试**: 对可回滚的操作敢于尝试
- **风险意识**: 对不可逆操作会先建议

### 沟通偏好
- **简洁直接**: 不要过多客套话
- **结果导向**: 先给结果，再说明过程
- **结构化**: 重要信息用列表呈现
- **进度可见**: 长任务定期更新进度
```

### 6. config/prompts/decisions/task_analysis.md

```markdown
# 任务分析指导

## 分析步骤

1. **理解用户意图** - 用户想要完成什么？
2. **识别任务类型** - coding、debugging、testing、planning 等
3. **评估复杂度** - 简单任务（<30秒）还是复杂任务（需要 Subagent）
4. **检查依赖** - 需要哪些技能、工具、上下文？
5. **决策执行策略** - MainAgent 直接执行还是创建 Subagent？

## 复杂度评估

**简单任务特征：**
- 单步查询或操作
- 耗时预计 < 30 秒
- 结果可以直接返回

**复杂任务特征：**
- 多步骤或需要迭代
- 耗时预计 > 30 秒
- 需要并行处理
- 需要专门的知识领域

## 决策示例

**任务**: "检查这个项目的代码质量问题"
- 意图: 代码质量分析
- 类型: coding + analysis
- 复杂度: 复杂（需要多文件分析）
- 执行策略: 创建 Subagent，加载 coding 和 analysis 技能

**任务**: "当前目录有什么文件？"
- 意图: 列出目录内容
- 类型: 信息查询
- 复杂度: 简单
- 执行策略: MainAgent 直接调用 list_dir
```

---

## 🔄 实现步骤

### 阶段一：创建新的提示词目录结构（1天）

1. 创建 `config/prompts/` 目录及其子目录
2. 创建核心提示词文件（identity.md, soul.md, tools.md）
3. 创建工作区提示词文件（agents.md, practices.md）
4. 创建用户提示词文件（profile.md, preferences.md）
5. 创建决策提示词文件（task_analysis.md, skill_selection.md, agent_selection.md）
6. 创建提示词配置文件（config.yaml）

### 阶段二：实现新的提示词加载器（2天）

1. 创建 `nanobot/agent/prompt_system_v2.py`
2. 实现 `PromptSystemV2` 类
3. 实现分层加载逻辑
4. 实现覆盖机制（workspace 文件覆盖内置文件）
5. 实现缓存机制
6. 实现 MainAgent 和 Subagent 的提示词构建方法

### 阶段三：更新现有代码以使用新系统（1天）

1. 修改 `nanobot/agent/context.py`
2. 更新 `ContextBuilder` 以使用新的提示词系统
3. 更新 `nanobot/agent/prompt_builder.py`
4. 确保向后兼容（如果 workspace 有旧文件）

### 阶段四：迁移现有内容（1天）

1. 检查 workspace 根目录的现有文件
2. 将 AGENTS.md、USER.md、SOUL.md 的内容整合到新系统
3. 保留 workspace 版本作为用户自定义版本（覆盖用）
4. 创建迁移脚本

### 阶段五：测试和验证（1天）

1. 测试 MainAgent 提示词加载
2. 测试 Subagent 提示词加载
3. 测试覆盖机制
4. 测试缓存机制
5. 验证所有功能正常工作

---

## 📝 代码实现：新提示词系统

### PromptSystemV2 类设计

```python
class PromptSystemV2:
    """
    新版提示词系统

    特性：
    - 分层加载：core → workspace → user → memory → decisions
    - 覆盖机制：workspace 文件可以覆盖内置提示词
    - 缓存机制：减少重复加载
    - 配置驱动：通过 config.yaml 控制加载策略
    """

    def __init__(self, config_path: Path, workspace: Path):
        self.config = self._load_config(config_path)
        self.workspace = workspace
        self.prompts_dir = config_path.parent
        self._cache = {}

    def build_main_agent_prompt(
        self,
        context: dict,
        available_tools: ToolRegistry,
        skills: list[str] | None = None,
        memory_content: str | None = None
    ) -> str:
        """
        构建 MainAgent 系统提示词
        """
        # 按层级加载提示词
        sections = {}

        for layer_name, layer_config in self.config["layers"].items():
            if not self._should_load_layer(layer_config, context):
                continue

            for file_config in layer_config["files"]:
                content = self._load_prompt_file(file_config, context)
                if content:
                    sections[file_config.get("section", layer_name)] = content

        # 添加工具描述
        sections["tools"] = self._format_tools(available_tools)

        # 添加技能（如果有）
        if skills:
            sections["skills"] = self._load_skills(skills)

        # 添加记忆（如果有）
        if memory_content:
            sections["long_term_memory"] = memory_content

        # 使用模板构建最终提示词
        template = self.config["templates"]["main_agent"]
        return template.format(**sections)

    def build_subagent_prompt(
        self,
        task_description: str,
        workspace: Path,
        skills: list[str] | None = None,
        available_tools: ToolRegistry | None = None
    ) -> str:
        """
        构建 Subagent 系统提示词
        """
        sections = {}

        # 加载核心层和用户层
        for layer_name in ["core", "user"]:
            layer_config = self.config["layers"][layer_name]
            for file_config in layer_config["files"]:
                content = self._load_prompt_file(file_config, {})
                if content:
                    sections[file_config.get("section", layer_name)] = content

        sections["task_description"] = task_description
        sections["workspace"] = str(workspace)

        # 添加工具描述（如果有）
        if available_tools:
            sections["tools"] = self._format_tools(available_tools)

        # 添加技能（如果有）
        if skills:
            sections["skills"] = self._load_skills(skills)

        # 使用模板构建最终提示词
        template = self.config["templates"]["sub_agent"]
        return template.format(**sections)

    def get_decision_prompt(self, prompt_type: str, **kwargs) -> str:
        """
        获取决策提示词
        """
        decisions_layer = self.config["layers"]["decisions"]
        for file_config in decisions_layer["files"]:
            if file_config.get("key") == prompt_type:
                return self._load_prompt_file(file_config, {})

        return ""
```

---

## 🚀 集成到定时任务巡检

### 在 `upgrade-plan/cron-job-config-enhanced.json` 添加新任务

```json
{
  "id": "prompt-system-health-check",
  "name": "Prompt System Health Check",
  "enabled": true,
  "schedule": {
    "kind": "cron",
    "expr": "0 6 * * *",
    "tz": "Asia/Shanghai"
  },
  "description": "每天早上 6:00 检查提示词系统健康状态",
  "action": {
    "type": "trigger_agent",
    "target": "mainAgent",
    "method": "check_prompt_system",
    "params": {
      "check_integrity": true,
      "check_overrides": true,
      "check_cache": true,
      "report_issues": true
    }
  },
  "onError": {
    "retry": 2,
    "retryInterval": "5m",
    "notify": true
  }
}
```

### 在 MainAgent 添加检查方法

```python
async def check_prompt_system(
    self,
    check_integrity: bool = True,
    check_overrides: bool = True,
    check_cache: bool = True,
    report_issues: bool = True
) -> dict:
    """
    检查提示词系统健康状态

    Returns:
        检查结果字典
    """
    results = {
        "status": "healthy",
        "issues": [],
        "timestamp": datetime.now().isoformat()
    }

    # 检查提示词文件完整性
    if check_integrity:
        integrity = await self._check_prompt_integrity()
        if integrity["issues"]:
            results["issues"].extend(integrity["issues"])
            results["status"] = "warning"

    # 检查覆盖配置
    if check_overrides:
        overrides = await self._check_workspace_overrides()
    else:
        overrides = {}

    # 检查缓存状态
    if check_cache:
        cache = await self._check_prompt_cache()
    else:
        cache = {}

    results["checks"] = {
        "integrity": integrity,
        "overrides": overrides,
        "cache": cache
    }

    # 汇报问题
    if report_issues and results["issues"]:
        await self._report_prompt_issues(results["issues"])

    return results
```

---

## 📊 升级计划总结

| 阶段 | 任务 | 预计时间 | 优先级 |
|------|------|---------|--------|
| 阶段一 | 创建提示词目录结构和文件 | 1天 | P0 |
| 阶段二：实现新的提示词加载器 | 2天 | P0 |
| 阶段三 | 更新现有代码使用新系统 | 1天 | P0 |
| 阶段四 | 迁移现有内容 | 1天 | P1 |
| 阶段五 | 测试和验证 | 1天 | P0 |
| 阶段六 | 集成到定时任务巡检 | 0.5天 | P1 |

**总计：** 6.5 天

---

## ⚠️ 风险和注意事项

1. **向后兼容性** - 确保旧版本的 workspace 文件仍然可用
2. **性能影响** - 分层加载不应显著增加启动时间
3. **配置迁移** - 提供迁移脚本帮助用户升级
4. **测试覆盖** - 所有场景都需要测试（main_agent, sub_agent, 多种任务类型）

---

## ✅ 验收标准

1. ✅ 新的提示词目录结构完整
2. ✅ MainAgent 和 Subagent 正确加载提示词
3. ✅ Workspace 文件可以覆盖内置提示词
4. ✅ 缓存机制工作正常
5. ✅ 定时任务可以检查提示词系统健康状态
6. ✅ 所有现有功能正常工作
7. ✅ 向后兼容旧版本 workspace 文件
