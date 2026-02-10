# Nanobot 架构设计文档

## 设计理念：参考 OpenClaw 风格

### OpenClaw 核心设计原则

1. **渐进式披露**（Progressive Disclosure）
   - Metadata（name + description）始终在上下文中
   - SKILL.md 正文在技能触发时加载（<5k 词）
   - Bundled Resources 按需加载

2. **简洁优先**（Conciseness First）
   - 假设模型已经很聪明
   - 只添加模型不具备的知识
   - 质疑每段信息的必要性

3. **工具驱动**（Tool-Driven）
   - 模型通过工具调用执行操作
   - 工具有明确参数和返回值
   - 高风险工具有评估机制

4. **自主决策**（Autonomous Decision）
   - MainAgent 不问用户，自己判断
   - 通过工具获取配置信息
   - 智能选择 skills 和 agent 类型

---

## Nanobot 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                      用户输入                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    MainAgent                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. 接收和分析任务                          │   │
│  └────────────────┬─────────────────────────────┘   │
│                   │                                   │
│                   ▼                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 2. 调用工具查询配置                        │   │
│  │    - get_available_skills()                   │   │
│  │    - get_available_agents()                   │   │
│  │    - get_skills_for_task(task_type)            │   │
│  └────────────────┬─────────────────────────────┘   │
│                   │                                   │
│                   ▼                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 3. 智能决策                               │   │
│  │    - 分析任务特点                            │   │
│  │    - 选择合适的 skills                        │   │
│  │    - 选择 agent 类型（agno/default）           │   │
│  └────────────────┬─────────────────────────────┘   │
│                   │                                   │
│                   ▼                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 4. 创建 Subagent                           │   │
│  │    - 传递 skills 信息                        │   │
│  │    - 传递任务描述                            │   │
│  └────────────────┬─────────────────────────────┘   │
│                   │                                   │
│                   ▼                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 5. 监控和聚合结果                          │   │
│  └────────────────┬─────────────────────────────┘   │
└───────────────────┼───────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                Subagent（Agno 类型）                    │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 1. 接收任务和 skills 列表                  │   │
│  └────────────────┬─────────────────────────────┘   │
│                   │                                   │
│                   ▼                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 2. 调用 SkillLoader                        │   │
│  │    - load_skills_for_task(task_type)          │   │
│  │    - 动态加载技能详细内容                   │   │
│  └────────────────┬─────────────────────────────┘   │
│                   │                                   │
│                   ▼                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 3. 构建系统提示                            │   │
│  │    - 基础提示词                              │   │
│  │    + 技能详细内容                          │   │
│  │    + 任务描述                                │   │
│  └────────────────┬─────────────────────────────┘   │
│                   │                                   │
│                   ▼                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 4. 执行任务                                │   │
│  │    - 根据技能指导工作                      │   │
│  │    - 调用工具执行操作                      │   │
│  │    - (risk evaluation for high-risk ops)      │   │
│  └────────────────┬─────────────────────────────┘   │
│                   │                                   │
│                   ▼                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 5. 返回结果                                │   │
│  └────────────────┬─────────────────────────────┘   │
└───────────────────┼───────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    MainAgent                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 6. 聚合和总结结果                          │   │
│  └────────────────┬─────────────────────────────┘   │
│                   │                                   │
│                   ▼                                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 7. 返回给用户                              │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────┼───────────────────────────────────┘
                    │
                    ▼
              ┌───────────┐
              │ 用户看到    │
              │ 最终回复  │
              └───────────┘
```

---

## 组件详解

### 1. MainAgent（主智能体）

**职责**：
- 接收和分析用户任务
- 通过工具查询系统配置
- 智能选择 skills 和 agent 类型
- 创建和管理 Subagent
- 监控执行和聚合结果

**关键组件**：
```python
class EnhancedMainAgent:
    skill_loader: SkillLoader          # 技能加载器
    tool_registry: ToolRegistry       # 工具注册表
    skill_decision_handler: SkillDecisionHandler  # 技能决策处理器
    subagent_manager: SubagentManager  # Subagent 管理器
```

**决策流程**：
```
1. 分析任务
   ↓
2. 调用工具：
   - get_available_skills()
   - get_available_agents()
   ↓
3. 任务类型识别
   ↓
4. 调用 get_skills_for_task(task_type)
   ↓
5. 选择 agent 类型（agno）
   ↓
6. 创建 Subagent，传递 skills
```

**工具调用**：
- `get_available_skills()` - 获取所有可用技能列表
- `get_skills_for_task(task_type)` - 根据任务类型获取推荐技能
- `get_available_agents()` - 获取支持的 agent 类型
- `get_skill_content(skill_name)` - 获取技能详细内容

---

### 2. SkillLoader（技能加载器）

**职责**：
- 从配置文件加载技能映射
- 根据任务类型智能匹配技能
- 动态加载技能详细内容

**加载策略**：
1. **显式技能优先**：用户明确指定的技能
2. **任务类型映射**：根据任务类型自动匹配技能
3. **默认技能**：加载 always skills

**关键方法**：
```python
class SkillLoader:
    async def load_skills_for_task(
        self, task_type: str, explicit_skills: List[str] = None
    ) -> List[str]:
        # 1. 显式技能优先
        # 2. 任务类型映射
        # 3. 默认技能
        # 去重并返回

    async def load_skill_content(self, skill_name: str) -> Optional[str]:
        # 加载技能的 SKILL.md 文件
        # 返回技能详细内容
```

**配置文件**：
```yaml
# config/skill_mapping.yaml
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

default_skills:
  - planning
  - writing
```

---

### 3. Skills（技能）

**技能结构**（OpenClaw 风格）：
```
skill-name/
├── SKILL.md（必需）
│   ├── YAML frontmatter
│   │   ├── name: 技能名称
│   │   - description: 技能描述（什么时候使用）
│   │   └── version: 版本（可选）
│   └── Markdown 正文（技能指导）
└── resources/（可选）
    ├── scripts/ - 可执行代码
    ├── references/ - 参考文档
    └── assets/ - 资源文件
```

**渐进式披露**：
1. **Metadata**（name + description）：
   - 始终在上下文中（~100 词）
   - 用于技能匹配和选择

2. **SKILL.md 正文**：
   - 技能触发时加载（<5k 词）
   - 包含技能使用指导

3. **Bundled Resources**：
   - 按需加载
   - scripts 可以执行，不占用上下文

**示例技能**：
- `coding` - 编码技能
- `debugging` - 调试技能
- `testing` - 测试技能
- `security` - 安全技能
- `planning` - 规划技能
- `writing` - 写作技能
- `research` - 研究技能

---

### 4. Tools（工具）

**工具理念**：
- 工具是模型执行操作的接口
- 有明确的参数和返回值
- 高风险工具有评估机制

**配置查询工具**：
```python
class GetAvailableSkillsTool(Tool):
    name = "get_available_skills"
    description = "获取所有可用的技能列表"
    async def execute(self) -> str:
        # 返回技能列表

class GetSkillsForTaskTool(Tool):
    name = "get_skills_for_task"
    description = "根据任务类型获取推荐的技能列表"
    parameters = {"task_type": {...}}
    async def execute(self, task_type: str) -> str:
        # 返回任务类型对应的技能

class GetAvailableAgentsTool(Tool):
    name = "get_available_agents"
    description = "获取系统支持的 agent 类型"
    async def execute(self) -> str:
        # 返回 agent 类型列表

class GetSkillContentTool(Tool):
    name = "get_skill_content"
    description = "获取技能的详细内容"
    parameters = {"skill_name": {...}}
    async def execute(self, skill_name: str) -> str:
        # 返回技能详细内容
```

**文件操作工具**：
- `ReadFileTool` - 读取文件
- `WriteFileTool` - 写入文件
- `ListDirTool` - 列出目录

**系统工具**：
- `ExecTool` - 执行 Shell 命令（有风险限制）
- `WebSearchTool` - 网络搜索
- `WebFetchTool` - 获取网页内容

---

### 5. Subagent（子智能体）

**类型**：
- **Agno Subagent** - 支持高级任务编排和人机交互
- **Default Subagent** - 基础任务执行能力

**职责**：
- 接收 MainAgent 分配的任务和 skills 列表
- 通过 SkillLoader 动态加载技能详细内容
- 根据技能指导执行任务
- 返回执行结果

**执行流程**：
```
1. 接收任务和 skills 列表
   ↓
2. 调用 SkillLoader.load_skills_for_task()
   ↓
3. 动态加载技能详细内容
   ↓
4. 构建系统提示：
   - 基础提示词
   + 技能详细内容
   + 任务描述
   ↓
5. 执行任务：
   - 根据技能指导工作
   - 调用工具执行操作
   - 高风险操作需要批准
   ↓
6. 返回结果
```

**关键组件**：
```python
class EnhancedAgnoSubagentManager:
    skill_loader: SkillLoader          # 技能加载器
    provider: LLMProvider              # LLM 提供商
    tool_registry: ToolRegistry         # 工具注册表

    async def _load_skills_content(self, skills: List[str]) -> Dict[str, str]:
        # 动态加载技能详细内容
        # 返回技能名称到内容的映射

    def _build_enhanced_agno_prompt(self, task: str, skills_content: Dict[str, str]) -> str:
        # 构建增强的系统提示
        # 包含技能详细内容
```

---

### 6. SkillDecisionHandler（技能决策处理器）

**职责**：
- 协调 MainAgent 的智能决策
- 调用工具查询配置
- 分析任务并选择 skills
- 决定创建什么类型的 Subagent

**决策流程**：
```python
class SkillDecisionHandler:
    async def handle_request(self, request: DecisionRequest) -> DecisionResult:
        # 1. 获取系统配置
        config_info = await self._get_system_config()

        # 2. 分析任务并选择 skills
        selected_skills = await self._select_skills_for_task(
            task_description, config_info
        )

        # 3. 选择 agent 类型
        agent_type = await self._select_agent_type(
            task_description, config_info
        )

        # 4. 返回决策结果
        return DecisionResult(
            action="spawn_subagent",
            data={
                "subagent_task": task_description,
                "subagent_config": {
                    "agent_type": agent_type,
                    "skills": selected_skills,
                }
            }
        )
```

---

## 配置文件

### 1. agent_prompts.yaml

定义 MainAgent 和 Subagent 的系统提示词。

**结构**：
```yaml
main_agent:
  system_prompt: |
    # 你是 Nanobot MainAgent
    ...

sub_agent:
  system_prompt_template: |
    # 你是 Nanobot Subagent
    任务：{task_description}
    技能：{skills_content}
    ...

agno_subagent:
  system_prompt_template: |
    # 你是 Agno-based Subagent
    ...

decision_guidance:
  task_analysis_prompt: |
    分析以下任务...
  skill_selection_prompt: |
    为以下任务选择最合适的技能...
```

### 2. skill_mapping.yaml

定义任务类型到技能的映射。

**结构**：
```yaml
task_types:
  coding: [coding, debugging, testing]
  debugging: [debugging, coding, testing]
  ...

default_skills:
  - planning
  - writing
```

---

## 实施路线图

### Phase 1：核心架构（当前阶段）

**目标**：建立基本的 MainAgent、Subagent、SkillLoader 协作

**任务**：
- ✅ 创建 `config_tools.py` - 配置查询工具
- ✅ 创建 `skill_decision_handler.py` - 技能决策处理器
- ✅ 创建 `enhanced_main_agent.py` - 增强版 MainAgent
- ✅ 创建 `enhanced_agno_subagent.py` - 增强版 Agno Subagent
- ✅ 创建 `agent_prompts.yaml` - 提示词配置
- ✅ 创建 AGENTS.md - 系统指导文档
- ✅ 创建示例技能（coding, debugging）

**验证**：
- MainAgent 可以通过工具查询配置
- MainAgent 可以智能选择 skills
- Subagent 可以动态加载技能内容
- 技能内容被注入到系统提示

### Phase 2：技能系统完善

**目标**：建立完整的技能生态系统

**任务**：
- 创建更多技能（testing, security, planning, writing, research）
- 完善 SkillLoader 的内容加载逻辑
- 支持技能的 scripts/、references/、assets/ 资源
- 实现技能的动态发现和注册

**验证**：
- 技能可以正确加载和解析
- 技能内容按需加载
- 技能匹配逻辑准确

### Phase 3：工具系统增强

**目标**：提供丰富的工具支持

**任务**：
- 扩展工具库（Git, Docker, Cloud, Database 等）
- 实现工具的风险评估机制
- 支持工具的异步执行
- 完善工具的错误处理

**验证**：
- 工具可以正确注册和调用
- 高风险工具有评估
- 工具错误被正确处理

### Phase 4：Subagent 管理完善

**目标**：提供强大的 Subagent 管理能力

**任务**：
- 支持 Subagent 的生命周期管理
- 实现 Subagent 的中断和恢复
- 支持 Subagent 的进度跟踪
- 实现 Subagent 的资源清理

**验证**：
- Subagent 可以正确创建和销毁
- Subagent 可以被中断和恢复
- Subagent 进度可以被跟踪

### Phase 5：测试和文档

**目标**：确保系统稳定性和可维护性

**任务**：
- 编写单元测试和集成测试
- 创建用户文档
- 创建开发者文档
- 性能优化和调优

**验证**：
- 测试覆盖率 > 80%
- 文档完整清晰
- 性能满足要求

---

## 设计决策记录

### 为什么使用工具驱动？

**决策**：MainAgent 通过工具调用查询配置，而不是直接访问配置

**理由**：
1. **一致性**：所有信息获取都通过工具
2. **可扩展性**：容易添加新的查询工具
3. **可测试性**：工具可以被 mock 和测试
4. **透明性**：模型可以看到信息来源

### 为什么使用渐进式披露？

**决策**：技能分三层加载（Metadata → 正文 → 资源）

**理由**：
1. **上下文效率**：只加载必要的信息
2. **灵活性**：可以根据任务动态加载
3. **可维护性**：技能内容可以独立更新

### 为什么 MainAgent 自主决策？

**决策**：MainAgent 不问用户"要使用什么技能"

**理由**：
1. **效率**：减少交互次数
2. **用户体验**：更流畅的交互
3. **智能性**：展现智能体的自主能力
4. **可预测性**：相同输入产生相同输出

### 为什么技能内容注入系统提示？

**决策**：Subagent 将技能内容注入到系统提示中

**理由**：
1. **上下文统一**：技能内容和任务在同一个提示中
2. **自然引导**：模型自然地使用技能
3. **灵活性**：可以根据任务动态调整提示

---

## 参考资料

### OpenClaw 参考文档

- **Skill Creator**：`/skills/skill-creator/SKILL.md`
- **GitHub Skill**：`/skills/github/SKILL.md`
- **AGENTS.md**：工作空间的 AGENTS.md
- **项目文档**：`/docs/` 目录

### 设计原则

1. **Conciseness**：简洁优先，假设模型很聪明
2. **Progressive Disclosure**：渐进式披露，按需加载
3. **Tool-Driven**：工具驱动，明确接口
4. **Autonomous Decision**：自主决策，减少询问
5. **Safety First**：安全优先，风险评估

---

## 总结

Nanobot 的架构设计参考了 OpenClaw 的优秀实践，包括：

1. **渐进式披露**的技能系统
2. **简洁优先**的内容组织
3. **工具驱动**的执行模型
4. **自主决策**的智能体行为

核心改进包括：

1. **MainAgent** 智能决策：通过工具查询配置，自主选择 skills
2. **SkillLoader** 动态加载：根据任务类型智能匹配技能
3. **Subagent** 技能注入：动态加载技能内容并注入系统提示
4. **工具系统** 配置查询：提供丰富的查询工具

通过这个架构，Nanobot 可以：
- 自主地理解和完成复杂任务
- 动态地选择和应用合适的技能
- 高效地利用上下文窗口
- 保持代码的可维护性和可扩展性

记住：工具和技能是为了让模型更好地完成任务。专注于目标，而不是过程。
