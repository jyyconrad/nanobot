# Nanobot 增强架构文档

## 📋 概述

本文档描述了 Nanobot 系统的增强架构，实现了**主智能体根据任务和配置动态选择 skills 并分配给 subagent** 的功能。

---

## 🎯 核心改进目标

### 用户需求
> "mainagent 的逻辑通过智能体自主决策，自动调用工具，如获取现在配置体系中有哪些 skills，有哪些 agent 等，通过调用 subagentmanager 创建 agno 类型的 subagent。然后 subagent 通过 skill-loader 自动决定是否加载 skill 详细的信息。"

### 实现的关键点
1. ✅ MainAgent 智能决策：调用工具查询配置
2. ✅ 动态选择 skills：根据任务类型自动匹配
3. ✅ Subagent 创建时传递 skills 信息
4. ✅ Subagent 内部通过 SkillLoader 加载技能详细内容

---

## 🏗️ 架构设计

### 整体流程

```
用户消息
    ↓
EnhancedMainAgent.process_message()
    ↓
┌─────────────────────────────────────┐
│ 1. 消息分类和路由                  │
│ 2. 任务规划 (TaskPlanner)          │
│ 3. 智能技能决策 (SkillDecisionHandler) │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ SkillDecisionHandler 智能决策流程    │
├─────────────────────────────────────┤
│ 步骤 1: 调用工具查询系统配置        │
│   - get_available_skills()          │
│   - get_available_agents()          │
│                                    │
│ 步骤 2: 分析任务并选择 skills       │
│   - 使用 SkillLoader.load_skills_for_task() │
│   - 根据任务类型匹配技能             │
│                                    │
│ 步骤 3: 选择 agent 类型            │
│   - 优先选择 "agno"                │
│                                    │
│ 步骤 4: 返回决策结果                │
│   - action: "spawn_subagent"        │
│   - data: {subagent_task, subagent_config} │
└─────────────────────────────────────┘
    ↓
EnhancedMainAgent._handle_spawn_subagent_decision()
    ↓
创建 SubagentTask (包含 skills 信息)
    ↓
SubagentManager.spawn_subagent(task)
    ↓
┌─────────────────────────────────────┐
│ EnhancedAgnoSubagentManager.spawn() │
├─────────────────────────────────────┤
│ 1. 接收 skills 参数               │
│ 2. 启动后台任务                   │
│ 3. 调用 _run_subagent()          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ _run_subagent() 执行流程           │
├─────────────────────────────────────┤
│ 1. 🔥 通过 SkillLoader 加载       │
│    技能详细内容                    │
│                                    │
│ 2. 🔥 构建增强系统提示             │
│    (包含已加载的技能内容)           │
│                                    │
│ 3. 执行任务                       │
│   - 调用 LLM                     │
│   - 执行工具调用                   │
│   - 迭代直到完成                   │
└─────────────────────────────────────┘
    ↓
返回结果给用户
```

---

## 📦 核心组件详解

### 1. 配置查询工具 (`config_tools.py`)

#### `GetAvailableSkillsTool`
- **名称**: `get_available_skills`
- **功能**: 获取系统中所有可用的技能列表
- **实现**: 读取 `SkillLoader` 的技能映射配置
- **返回**: 格式化的技能列表

#### `GetSkillsForTaskTool`
- **名称**: `get_skills_for_task`
- **功能**: 根据任务类型获取推荐的技能
- **参数**: `task_type` (如: coding, debugging, security)
- **返回**: 该任务类型对应的技能列表

#### `GetAvailableAgentsTool`
- **名称**: `get_available_agents`
- **功能**: 获取支持的 agent 类型
- **返回**: agno, default 等 agent 类型及其描述

#### `GetSkillContentTool`
- **名称**: `get_skill_content`
- **功能**: 获取指定技能的详细描述
- **参数**: `skill_name`
- **返回**: 技能的详细内容

### 2. 技能决策处理器 (`skill_decision_handler.py`)

#### `SkillDecisionHandler`

**职责**: MainAgent 智能决策的核心

**关键方法**:

1. `handle_request(request)`
   - 处理技能决策请求
   - 返回创建 subagent 的决策

2. `_get_system_config()`
   - 调用工具查询系统配置
   - 获取可用 skills 和 agents

3. `_select_skills_for_task(task_description, config_info)`
   - 分析任务类型
   - 使用 `SkillLoader` 加载匹配的技能

4. `_analyze_task_type(task_description)`
   - 关键词匹配识别任务类型
   - 支持的类型: coding, debugging, testing, security, planning, writing, research, analysis

5. `_select_agent_type(task_description, config_info)`
   - 优先选择 "agno"
   - 备选 "default"

**决策结果**:
```python
DecisionResult(
    action="spawn_subagent",
    data={
        "subagent_task": "任务描述",
        "subagent_config": {
            "agent_type": "agno",
            "skills": ["coding", "debugging", "testing"],
            "task_description": "..."
        }
    }
)
```

### 3. 增强版主代理 (`enhanced_main_agent.py`)

#### `EnhancedMainAgent`

**新增组件**:
- `self.skill_loader`: SkillLoader 实例
- `self.tool_registry`: 工具注册表（包含配置查询工具）
- `self.skill_decision_handler`: 技能决策处理器

**关键方法**:

1. `__init__()`
   ```python
   # 初始化 SkillLoader
   self.skill_loader = SkillLoader()

   # 注册配置查询工具
   self.tool_registry = ToolRegistry()
   self._register_config_tools()

   # 初始化技能决策处理器
   self.skill_decision_handler = SkillDecisionHandler(
       agent_loop=None,
       tool_registry=self.tool_registry,
       skill_loader=self.skill_loader
   )
   ```

2. `_handle_chat_message(message)`
   - 任务规划
   - **智能技能决策** (调用 `skill_decision_handler`)
   - 执行决策

3. `_make_skill_decision(message)`
   - 构建决策请求
   - 调用 `SkillDecisionHandler.handle_request()`
   - 返回决策结果

4. `_handle_spawn_subagent_decision(decision)`
   - 提取 subagent 配置
   - **确保 skills 信息被传递**
   ```python
   task = SubagentTask(
       task_id=str(uuid4()),
       description=decision.data.get("subagent_task"),
       config=subagent_config,
       agent_type=subagent_config.get("agent_type"),
       skills=subagent_config.get("skills"),  # 🔥 关键
   )
   ```

### 4. 增强版 Agno Subagent (`enhanced_agno_subagent.py`)

#### `EnhancedAgnoSubagentManager`

**新增组件**:
- `self.skill_loader`: SkillLoader 实例

**关键方法**:

1. `spawn(..., skills=None, ...)`
   - 接收 `skills` 参数
   - 传递给 `_run_subagent()`

2. `_run_subagent(..., skills=None, ...)`
   - **动态加载技能详细内容**
   - **构建增强系统提示** (包含技能内容)

3. `_load_skills_content(skills)`
   ```python
   async def _load_skills_content(self, skills: List[str] | None) -> Dict[str, str]:
       skills_content = {}
       for skill_name in skills:
           content = await self.skill_loader.load_skill_content(skill_name)
           if content:
               skills_content[skill_name] = content
       return skills_content
   ```

4. `_build_enhanced_agno_prompt(task, skills_content)`
   ```python
   system_prompt = f"""
   # Enhanced Agno Subagent

   ## Your Task
   {task}

   ## Available Skills
   """

   # 🔥 将已加载的技能内容注入到系统提示
   for skill_name, content in skills_content.items():
       system_prompt += f"\n### {skill_name}\n{content}\n"

   system_prompt += """
   ## Rules
   ...

   ## What You Can Do
   ...

   ## What You Cannot Do
   ...
   """
   ```

---

## 🔧 配置文件

### `config/skill_mapping.yaml`

定义任务类型到技能的映射关系：

```yaml
task_types:
  coding:
    - coding
    - debugging
    - testing
  debugging:
    - debugging
    - coding
    - testing
  security:
    - security
    - coding
    - testing
  testing:
    - testing
    - coding
    - debugging
  planning:
    - planning
    - writing
  writing:
    - writing
    - research
  research:
    - research
    - writing
  translation:
    - writing
  analysis:
    - research
    - planning

default_skills:
  - planning
  - writing

skill_descriptions:
  coding: 编码技能 - 支持多种编程语言和代码审查
  debugging: 调试技能 - 支持错误定位和修复
  security: 安全技能 - 提供代码安全审查
  testing: 测试技能 - 支持测试生成和执行
  planning: 规划技能 - 任务分解和项目管理
  writing: 写作技能 - 内容创作和文档生成
  research: 研究技能 - 信息收集和数据分析
  translation: 翻译技能 - 多语言翻译支持
```

---

## 🚀 使用示例

### 示例 1: 编码任务

**用户输入**:
```
编写一个 Python 函数，实现快速排序算法
```

**执行流程**:
1. MainAgent 接收消息
2. 调用 `get_available_skills()` → 获取技能列表
3. 调用 `get_available_agents()` → 获取 agent 类型
4. 分析任务类型 → 识别为 "coding"
5. `SkillLoader.load_skills_for_task("coding")` → 返回 `["coding", "debugging", "testing"]`
6. 选择 agent 类型 → "agno"
7. 创建 SubagentTask (包含 skills)
8. AgnoSubagent 执行：
   - 加载技能内容
   - 构建系统提示（包含 coding, debugging, testing 技能说明）
   - 执行任务

**生成的系统提示**:
```
# Enhanced Agno Subagent

## Your Task
编写一个 Python 函数，实现快速排序算法

## Available Skills

### coding
编码技能 - 支持多种编程语言和代码审查

### debugging
调试技能 - 支持错误定位和修复

### testing
测试技能 - 支持测试生成和执行

## Rules
...

## What You Can Do
...
```

### 示例 2: 调试任务

**用户输入**:
```
帮我调试这段代码，它总是报错
```

**执行流程**:
1. 分析任务类型 → 识别为 "debugging"
2. `SkillLoader.load_skills_for_task("debugging")` → 返回 `["debugging", "coding", "testing"]`
3. 创建 SubagentTask
4. AgnoSubagent 执行（加载相应的技能内容）

### 示例 3: 安全审计

**用户输入**:
```
对这个项目进行安全审计
```

**执行流程**:
1. 分析任务类型 → 识别为 "security"
2. `SkillLoader.load_skills_for_task("security")` → 返回 `["security", "coding", "testing"]`
3. 创建 SubagentTask
4. AgnoSubagent 执行（加载相应的技能内容）

---

## 🔍 技术细节

### 任务类型识别

`_analyze_task_type()` 方法使用关键词匹配：

```python
task_keywords = {
    "coding": ["代码", "函数", "class", "python", "javascript", ...],
    "debugging": ["bug", "错误", "调试", "修复", "debug", ...],
    "testing": ["测试", "test", "单元测试", "测试用例", ...],
    "security": ["安全", "漏洞", "安全审计", ...],
    "planning": ["规划", "计划", "设计", "架构", ...],
    "writing": ["文档", "写作", "write", "document", ...],
    "research": ["研究", "调研", "分析", "research", ...],
    "analysis": ["分析", "数据", "报告", "analysis", ...],
}
```

### Skills 加载优先级

`SkillLoader.load_skills_for_task()` 的加载策略：

1. **显式技能优先**: 用户明确指定的技能（如果存在）
2. **任务类型映射**: 根据 `skill_mapping.yaml` 自动匹配
3. **默认技能**: 总是加载 `default_skills`

```python
# 1. 显式技能
if explicit_skills:
    skills.extend(explicit_skills)

# 2. 任务类型映射
if task_type in self.skill_mapping:
    skills.extend(self.skill_mapping[task_type])

# 3. 默认技能
skills.extend(self.default_skills)

# 去重
unique_skills = list(dict.fromkeys(skills))
```

### 工具注册

`EnhancedMainAgent` 启动时自动注册配置查询工具：

```python
def _register_config_tools(self):
    self.tool_registry.register(GetAvailableSkillsTool())
    self.tool_registry.register(GetSkillsForTaskTool())
    self.tool_registry.register(GetAvailableAgentsTool())
    self.tool_registry.register(GetSkillContentTool())
```

这些工具可以被 MainAgent 的决策逻辑调用，也可以被 LLM 通过 Function Calling 调用。

---

## 📊 与原架构的对比

| 功能 | 原架构 | 增强架构 |
|------|--------|----------|
| MainAgent 决策 | 简单的决策逻辑 | 智能决策，调用工具查询配置 |
| Skills 信息 | 存在 SkillLoader 但未被集成 | 完全集成到决策流程 |
| Subagent 创建 | 不传递 skills 信息 | 传递 skills 列表 |
| Subagent 执行 | 固定系统提示 | 动态加载技能内容到系统提示 |
| 配置查询 | 无专用工具 | 提供 4 个配置查询工具 |
| 任务类型识别 | 基础规划器 | 增强的关键词匹配 |

---

## 🎓 设计模式

### 1. Strategy Pattern（策略模式）
- `SkillDecisionHandler`: 根据任务类型选择不同的技能策略
- `TaskPlanner`: 根据任务复杂度选择不同的执行策略

### 2. Dependency Injection（依赖注入）
- `SkillDecisionHandler` 注入 `ToolRegistry` 和 `SkillLoader`
- `EnhancedMainAgent` 注入各个组件

### 3. Template Method（模板方法）
- `_run_subagent()` 定义执行框架，`_load_skills_content()` 等由子类实现

### 4. Registry Pattern（注册表模式）
- `ToolRegistry`: 动态注册和管理工具
- `SkillLoader`: 管理技能映射配置

---

## 🔮 未来扩展

### 可能的改进方向

1. **更智能的任务类型识别**
   - 使用 LLM 进行语义分析
   - 支持多任务类型（组合任务）

2. **技能动态评分**
   - 根据历史执行效果调整技能权重
   - 用户反馈驱动的技能推荐

3. **多 agent 协作**
   - 支持 subagent 之间通信
   - 分治策略处理复杂任务

4. **技能依赖管理**
   - 支持技能之间的依赖关系
   - 自动解析和加载依赖技能

5. **性能监控**
   - 记录每个技能的使用频率和效果
   - 优化技能加载策略

---

## 📝 文件清单

### 新增文件
- `nanobot/agent/tools/config_tools.py` - 配置查询工具
- `nanobot/agent/decision/skill_decision_handler.py` - 技能决策处理器
- `nanobot/agent/enhanced_main_agent.py` - 增强版主代理
- `nanobot/agent/subagent/enhanced_agno_subagent.py` - 增强版 Agno Subagent
- `docs/enhanced_architecture.md` - 本文档

### 修改文件（建议）
- `nanobot/agent/main_agent.py` - 可选：合并 `EnhancedMainAgent` 的改进
- `nanobot/agent/subagent/agno_subagent.py` - 可选：合并增强功能

### 配置文件
- `nanobot/config/skill_mapping.yaml` - 技能映射配置（已存在）

---

## ✅ 验证检查

### 功能验证清单

- [ ] MainAgent 可以调用 `get_available_skills()` 工具
- [ ] MainAgent 可以调用 `get_available_agents()` 工具
- [ ] `SkillDecisionHandler` 正确分析任务类型
- [ ] `SkillDecisionHandler` 正确选择 skills
- [ ] Subagent 创建时 skills 信息被传递
- [ ] AgnoSubagent 接收到 skills 参数
- [ ] AgnoSubagent 通过 SkillLoader 加载技能内容
- [ ] 技能内容被正确注入到系统提示
- [ ] 任务执行时可以访问技能信息

### 测试建议

1. **单元测试**
   - 测试 `SkillDecisionHandler` 的决策逻辑
   - 测试 `SkillLoader` 的技能加载
   - 测试配置查询工具的执行

2. **集成测试**
   - 测试 MainAgent 到 Subagent 的完整流程
   - 测试不同任务类型的技能选择

3. **端到端测试**
   - 发送编码任务，验证选择的 skills
   - 发送调试任务，验证技能加载
   - 检查生成的系统提示内容

---

## 🎉 总结

本次增强架构实现了**主智能体根据任务和配置动态选择 skills 并分配给 subagent**的核心需求：

✅ **智能决策**: MainAgent 通过工具调用查询配置
✅ **动态技能选择**: 根据任务类型自动匹配技能
✅ **技能信息传递**: Subagent 创建时接收 skills 列表
✅ **技能内容加载**: Subagent 内部通过 SkillLoader 加载详细内容
✅ **配置透明化**: 提供配置查询工具
✅ **可扩展性**: 模块化设计，易于扩展

这个架构为 Nanobot 系统提供了强大的自适应能力，能够根据任务需求智能地配置和执行。
