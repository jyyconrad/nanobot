# Nanobot v0.2.0 - Agno 框架集成方案

> **日期**: 2026-02-09 22:35
> **状态**: 新增要求
> **目标**: 将 MainAgent 和 Subagent 改造为基于 agno 框架实现

---

## 📋 需求概述

用户要求在现有的升级计划中新增 **agno 框架集成**，将 Nanobot 的 MainAgent 和 Subagent 改造成基于 agno 框架实现。

### 核心任务

1. **研究 agno 框架** - 了解 Agent, Skills, Tools, Knowledge 的实现方式
2. **编写简单示例** - 提供 agno 框架的使用示例
3. **提示词策略设计** - 设计 2 种提示词初始化策略
4. **集成到升级计划** - 更新现有的升级方案

---

## 🔍 Agno 框架核心概念

### 1. Agent（智能体）

```python
from agno import Agent

# 创建 Agent
agent = Agent(
    name="main_agent",
    model="openai/gpt-4",
    instructions="你是一个助手",
)

# 运行 Agent
response = agent.run("用户消息")
print(response.content)
```

**核心特性**：
- `name`: Agent 名称
- `model`: 使用的 LLM 模型
- `instructions`: 系统提示词
- `tools`: 可用工具列表
- `knowledge`: 知识库
- `memory`: 记忆系统
- `hooks`: 钩子系统

### 2. Skills（技能）

Skills 在 agno 中是通过 **Toolkit** 实现的：

```python
from agno import Agent, Toolkit

# 定义工具函数
def read_file(path: str) -> str:
    """读取文件内容"""
    with open(path, "r") as f:
        return f.read()

# 创建工具包
toolkit = Toolkit(
    name="file_toolkit",
    tools=[
        Function(
            name="read_file",
            description="读取文件内容",
            func=read_file
        )
    ]
)

# 添加到 Agent
agent = Agent(
    name="main_agent",
    instructions="你是一个文件助手",
    toolkits=[toolkit]
)
```

### 3. Tools（工具）

工具通过 `Function` 定义：

```python
from agno import Function

# 定义工具
def web_search(query: str) -> str:
    """搜索网络"""
    return "搜索结果"

# 工具函数
tool = Function(
    name="web_search",
    description="搜索网络",
    func=web_search
)
```

### 4. Knowledge（知识库）

Knowledge 提供 RAG（检索增强生成）功能：

```python
from agno import Knowledge
from agno.knowledge.reader import UrlReader

# 创建知识库
knowledge = Knowledge(
    reader=UrlReader(),
    vector_store="pgvector",
)

# 添加知识源
knowledge.load(urls=["https://docs.openai.com"])

# 添加到 Agent
agent = Agent(
    name="main_agent",
    knowledge=knowledge
)
```

---

## 🎯 两种提示词初始化策略

### 策略 1: Team 协同方式（配置或参数启动）

**原理**：
- 创建一个 **Team**（团队）结构
- 每个 Team 成员负责生成提示词的某个部分
- 最终组合成完整的系统提示词

**实现**：

```python
from agno import Agent, Team

# 创建负责不同部分的 Agent
identity_agent = Agent(
    name="identity_provider",
    model="openai/gpt-4o-mini",
    instructions="你负责生成系统身份提示词",
)

soul_agent = Agent(
    name="soul_provider",
    model="openai/gpt-4o-mini",
    instructions="你负责生成系统人设提示词",
)

tools_agent = Agent(
    name="tools_provider",
    model="openai/gpt-4o-mini",
    instructions="你负责生成工具使用指导",
)

# 创建 Team
prompt_team = Team(
    agents=[identity_agent, soul_agent, tools_agent],
    instructions="协同生成完整的系统提示词",
)

# 使用 Team 生成提示词
response = prompt_team.run("生成 MainAgent 的系统提示词")

# 组合结果
full_prompt = combine_team_responses(response)
```

**优势**：
- 灵活性高，每个部分可以独立调整
- 可以并行生成，提高速度
- 易于扩展，添加新的提示词部分

**劣势**：
- 需要多个模型调用，成本较高
- 需要设计组合逻辑

---

### 策略 2: 独立 Agent + 占位符替换

**原理**：
- 预先定义完整的提示词模板（Markdown）
- 使用占位符（如 `{{SKILLS}}`, `{{TOOLS}}`）标记动态内容
- Agent 在运行时读取模板，替换占位符

**实现**：

```python
# config/prompts/main_agent_template.md
"""
# 系统身份

你是一个 AI 智能体，名为 {{AGENT_NAME}}

# 核心能力

## 技能列表

{{SKILLS}}

## 工具列表

{{TOOLS}}

# 使用指导

{{TOOL_GUIDE}}
"""

# Agent 实现
from agno import Agent
from pathlib import Path

class MainAgent:
    def __init__(self):
        self.template_path = Path("config/prompts/main_agent_template.md")
        self.template = self._load_template()
        
    def _load_template(self) -> str:
        with open(self.template_path, "r") as f:
            return f.read()
    
    def _build_system_prompt(self, skills: list, tools: list) -> str:
        """构建系统提示词"""
        # 替换占位符
        prompt = self.template.replace("{{AGENT_NAME}}", "MainAgent")
        prompt = prompt.replace("{{SKILLS}}", "\n".join([f"- {s}" for s in skills]))
        prompt = prompt.replace("{{TOOLS}}", "\n".join([f"- {t.name}" for t in tools]))
        prompt = prompt.replace("{{TOOL_GUIDE}}", self._get_tool_guide())
        
        return prompt
    
    def _get_tool_guide(self) -> str:
        """获取工具使用指导"""
        # 从独立 Agent 加载工具指导
        guide_agent = Agent(
            name="tool_guide_provider",
            instructions="根据可用工具生成使用指导",
        )
        response = guide_agent.run(f"生成工具指导：{tools}")
        return response.content
    
    def run(self, message: str):
        """运行 Agent"""
        # 构建系统提示词
        system_prompt = self._build_system_prompt(
            skills=["coding", "testing", "debugging"],
            tools=[web_search, web_fetch]
        )
        
        # 创建运行 Agent
        agent = Agent(
            name="main_agent_runtime",
            instructions=system_prompt,
        )
        
        # 运行
        return agent.run(message)
```

**优势**：
- 模板清晰，易于维护
- 运行时动态替换，灵活性高
- 可以从文件加载，方便版本控制

**劣势**：
- 占位符设计需要提前规划
- 替换逻辑需要维护

---

## 📁 Agno 集成架构设计

### MainAgent 改造

```python
from agno import Agent, Toolkit, Knowledge
from typing import List, Dict, Optional

class MainAgent:
    """基于 agno 的 MainAgent"""
    
    def __init__(
        self,
        name: str = "main_agent",
        model: str = "openai/gpt-4",
        prompt_strategy: str = "template",  # "team" or "template"
        config: Optional[Dict] = None
    ):
        self.name = name
        self.model = model
        self.prompt_strategy = prompt_strategy
        self.config = config or {}
        
        # 初始化组件
        self._init_toolkits()
        self._init_knowledge()
        self._init_hooks()
        
        # 创建 agno Agent
        self.agent = self._create_agent()
    
    def _init_toolkits(self):
        """初始化工具包"""
        # 文件工具
        self.file_toolkit = Toolkit(
            name="file_toolkit",
            tools=[
                Function(name="read_file", description="读取文件", func=self._read_file),
                Function(name="write_file", description="写入文件", func=self._write_file),
            ]
        )
        
        # 搜索工具
        self.search_toolkit = Toolkit(
            name="search_toolkit",
            tools=[
                Function(name="web_search", description="搜索网络", func=self._web_search),
                Function(name="web_fetch", description="获取网页内容", func=self._web_fetch),
            ]
        )
    
    def _init_knowledge(self):
        """初始化知识库"""
        # 工作区上下文
        self.workspace_knowledge = Knowledge(
            reader=DirectoryReader(),
            vector_store="pgvector",
        )
        self.workspace_knowledge.load(paths=["/workspace"])
    
    def _create_agent(self) -> Agent:
        """创建 agno Agent"""
        # 构建系统提示词
        instructions = self._build_system_prompt()
        
        # 创建 Agent
        agent = Agent(
            name=self.name,
            model=self.model,
            instructions=instructions,
            toolkits=[self.file_toolkit, self.search_toolkit],
            knowledge=self.workspace_knowledge,
        )
        
        return agent
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词（根据策略）"""
        if self.prompt_strategy == "team":
            return self._build_prompt_with_team()
        elif self.prompt_strategy == "template":
            return self._build_prompt_with_template()
        else:
            raise ValueError(f"Unknown prompt strategy: {self.prompt_strategy}")
    
    def _build_prompt_with_team(self) -> str:
        """策略 1: 使用 Team 协同生成"""
        # 创建 Team 成员
        identity_agent = Agent(name="identity", instructions="生成身份")
        soul_agent = Agent(name="soul", instructions="生成人设")
        tools_agent = Agent(name="tools", instructions="生成工具指导")
        
        # 创建 Team
        team = Team(
            agents=[identity_agent, soul_agent, tools_agent],
            instructions="协同生成完整提示词"
        )
        
        # 运行 Team
        response = team.run("生成 MainAgent 提示词")
        return response.content
    
    def _build_prompt_with_template(self) -> str:
        """策略 2: 使用模板 + 占位符"""
        # 加载模板
        template_path = Path("config/prompts/main_agent_template.md")
        with open(template_path, "r") as f:
            template = f.read()
        
        # 替换占位符
        prompt = template.replace("{{AGENT_NAME}}", self.name)
        prompt = prompt.replace("{{SKILLS}}", "\n".join(["coding", "testing", "debugging"]))
        # ... 其他替换
        
        return prompt
    
    def run(self, message: str) -> str:
        """运行 Agent"""
        response = self.agent.run(message)
        return response.content
```

### SubAgent 改造

```python
from agno import Agent, Toolkit

class SubAgent:
    """基于 agno 的 SubAgent"""
    
    def __init__(
        self,
        name: str,
        task_description: str,
        skills: List[str],
        parent_agent: Optional[MainAgent] = None,
    ):
        self.name = name
        self.task_description = task_description
        self.skills = skills
        self.parent_agent = parent_agent
        
        # 创建 Agent
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """创建 agno Agent"""
        # 构建系统提示词
        instructions = self._build_subagent_prompt()
        
        # 创建工具包（从 parent 继承）
        toolkits = []
        if self.parent_agent:
            toolkits = self.parent_agent.agent.toolkits
        
        # 创建 Agent
        agent = Agent(
            name=self.name,
            model=self.parent_agent.model if self.parent_agent else "openai/gpt-4",
            instructions=instructions,
            toolkits=toolkits,
        )
        
        return agent
    
    def _build_subagent_prompt(self) -> str:
        """构建 SubAgent 提示词"""
        template = """
        # 任务描述
        
        {{TASK_DESCRIPTION}}
        
        # 可用技能
        
        {{SKILLS}}
        """
        
        prompt = template.replace("{{TASK_DESCRIPTION}}", self.task_description)
        prompt = prompt.replace("{{SKILLS}}", "\n".join([f"- {s}" for s in self.skills]))
        
        return prompt
    
    def run(self, message: str) -> str:
        """运行 Agent"""
        response = self.agent.run(message)
        return response.content
```

---

## 📝 实现步骤

### Phase 1: 研究 Agno 框架（1 天）

- [x] ✅ 已完成：查看 agno 核心结构
- [ ] 编写 agno Agent 示例
- [ ] 编写 agno Skills/Tools 示例
- [ ] 编写 agno Knowledge 示例
- [ ] 测试基础功能

### Phase 2: 设计提示词策略（0.5 天）

- [ ] 完善 Team 策略设计
- [ ] 完善模板策略设计
- [ ] 编写策略对比文档
- [ ] 创建提示词模板文件

### Phase 3: 改造 MainAgent（1 天）

- [ ] 创建 `nanobot/agent/agno_main_agent.py`
- [ ] 实现提示词构建逻辑
- [ ] 集成工具包
- [ ] 集成知识库
- [ ] 编写测试

### Phase 4: 改造 SubAgent（1 天）

- [ ] 创建 `nanobot/agent/agno_subagent.py`
- [ ] 实现继承逻辑
- [ ] 实现任务分发
- [ ] 编写测试

### Phase 5: 集成测试（1 天）

- [ ] 端到端测试
- [ ] 性能对比测试
- [ ] 向后兼容测试
- [ ] 文档更新

---

## 🎯 下一行动

### 1. 编写 Agno 示例

创建文件 `examples/agno_examples.py`：

```python
"""
Agno 框架使用示例
"""

from agno import Agent, Toolkit, Function, Knowledge, Team

# 示例 1: 简单 Agent
def simple_agent_example():
    """创建一个简单的 Agent"""
    agent = Agent(
        name="hello_agent",
        model="openai/gpt-4o-mini",
        instructions="你是一个友好的助手",
    )
    
    response = agent.run("你好，介绍一下你自己")
    print(response.content)

# 示例 2: 带 Tools 的 Agent
def agent_with_tools_example():
    """创建带工具的 Agent"""
    
    def get_weather(city: str) -> str:
        """获取天气"""
        return f"{city} 的天气：晴天，25°C"
    
    tool = Function(
        name="get_weather",
        description="获取天气信息",
        func=get_weather
    )
    
    agent = Agent(
        name="weather_agent",
        instructions="你可以查询天气",
        tools=[tool]
    )
    
    response = agent.run("北京今天天气怎么样？")
    print(response.content)

# 示例 3: Team 协同
def team_example():
    """使用 Team 协同"""
    
    agent1 = Agent(name="writer", instructions="你负责写作")
    agent2 = Agent(name="editor", instructions="你负责编辑")
    
    team = Team(agents=[agent1, agent2])
    
    response = team.run("写一篇文章关于 AI")
    print(response.content)

if __name__ == "__main__":
    print("=== 示例 1: 简单 Agent ===")
    simple_agent_example()
    
    print("\n=== 示例 2: 带 Tools 的 Agent ===")
    agent_with_tools_example()
    
    print("\n=== 示例 3: Team 协同 ===")
    team_example()
```

### 2. 创建提示词模板

创建文件 `config/prompts/main_agent_template.md`：

```markdown
# 系统身份

你是一个 AI 智能体，名为 {{AGENT_NAME}}

# 核心能力

## 技能列表

{{SKILLS}}

## 工具列表

{{TOOLS}}

# 使用指导

{{TOOL_GUIDE}}
```

---

## 📊 更新现有升级计划

需要更新以下文件：

1. ✅ `upgrade-plan/MASTER-UPGRADE-OVERVIEW.md` - 添加 Agno 集成阶段
2. ✅ `upgrade-plan/AGNO-INTEGRATION-PLAN.md` - 本文档（新创建）
3. ✅ `upgrade-plan/CURRENT-STATUS.md` - 更新开发状态

---

**建议**：
- 在现有计划中插入 **Phase 0: Agno 框架研究和集成**（2 天）
- 后续阶段都基于 agno 框架实现

---

**准备就绪，等待确认！** 🚀

> 下一步：创建 `examples/agno_examples.py` 和提示词模板文件
