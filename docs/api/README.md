# API 文档

Nanobot API 文档中心。

---

## 📚 文档列表

- [API](API.md) - 核心 API 文档

---

## 🔌 核心 API

### MainAgent

```python
from nanobot.agents.agno_main_agent import AgnoMainAgent

agent = AgnoMainAgent(config=...)
response = agent.process("用户消息")
```

### SubAgent

```python
from nanobot.agents.agno_subagent import AgnoSubAgent

subagent = AgnoSubAgent(config=...)
response = subagent.process("任务描述")
```

### PromptSystem

```python
from nanobot.agent.prompt_system_v2 import PromptSystemV2

system = PromptSystemV2()
prompt = system.build_main_agent_prompt()
```

---

## 🛠️ 工具 API

### ToolRegistry

工具注册和调用

```python
from nanobot.agent.tools.registry import ToolRegistry

registry = ToolRegistry()
registry.register("tool_name", tool_function)
result = registry.execute("tool_name", args)
```

---

## 📡 通道 API

### Channel

通信渠道接口

```python
from nanobot.channels.base import BaseChannel

class MyChannel(BaseChannel):
    def send(self, message):
        # 实现发送逻辑
        pass
```

---

**注意**: 详细 API 文档待补充，目前请参考源码注释。
