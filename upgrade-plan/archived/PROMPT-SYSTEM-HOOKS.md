# 提示词系统钩子设计

## 📋 需求说明

在初始化阶段和触发读取系统配置提示词的场景，需要添加钩子机制：
1. 智能体完成读取配置后，自动总结所有信息
2. 输出新的完整提示词
3. 系统通过钩子构建全新完整的 MainAgent（角色系统、指令、tools、skills 概述等）

---

## 🎯 钩子类型

### 1. 配置加载钩子（Post-Load Hooks）

```python
class PostLoadHooks:
    """
    配置加载完成后的钩子
    """

    def on_config_loaded(self, config: dict) -> None:
        """
        配置文件加载完成后触发

        Args:
            config: 加载的配置字典
        """
        pass

    def on_prompts_loaded(self, prompts: dict) -> None:
        """
        提示词文件加载完成后触发

        Args:
            prompts: 加载的提示词字典
        """
        pass

    def on_layer_loaded(self, layer_name: str, content: dict) -> None:
        """
        单个提示词层加载完成后触发

        Args:
            layer_name: 层名称（core, workspace, user, memory, decisions）
            content: 该层的内容
        """
        pass
```

### 2. 提示词构建钩子（Prompt Build Hooks）

```python
class PromptBuildHooks:
    """
    提示词构建完成后的钩子
    """

    def on_prompt_built(self, agent_type: str, prompt: str) -> None:
        """
        提示词构建完成后触发

        Args:
            agent_type: Agent 类型（main_agent, sub_agent）
            prompt: 构建的完整提示词
        """
        pass

    def on_main_agent_prompt_built(self, prompt: str, sections: dict) -> None:
        """
        MainAgent 提示词构建完成后触发

        Args:
            prompt: 完整的系统提示词
            sections: 提示词各部分内容
        """
        pass

    def on_subagent_prompt_built(self, task: str, prompt: str, sections: dict) -> None:
        """
        Subagent 提示词构建完成后触发

        Args:
            task: 任务描述
            prompt: 完整的系统提示词
            sections: 提示词各部分内容
        """
        pass
```

### 3. Agent 初始化钩子（Agent Init Hooks）

```python
class AgentInitHooks:
    """
    Agent 初始化完成后的钩子
    """

    def on_agent_initialized(self, agent: "MainAgent") -> None:
        """
        Agent 初始化完成后触发

        Args:
            agent: 初始化完成的 Agent 实例
        """
        pass

    def on_agent_ready(self, agent: "MainAgent") -> None:
        """
        Agent 准备好接收消息后触发

        Args:
            agent: 准备好的 Agent 实例
        """
        pass
```

---

## 🏗️ 钩子系统架构

### 核心类：HookSystem

```python
import logging
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime

class HookSystem:
    """
    钩子管理系统

    支持多种钩子类型：
    - 配置加载钩子（on_config_loaded）
    - 提示词构建钩子（on_prompt_built）
    - Agent 初始化钩子（on_agent_initialized）
    """

    def __init__(self):
        self.hooks: Dict[str, List[Callable]] = {}
        self.logger = logging.getLogger(__name__)

    def register(self, hook_name: str, callback: Callable) -> None:
        """
        注册钩子

        Args:
            hook_name: 钩子名称
            callback: 回调函数
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []

        self.hooks[hook_name].append(callback)
        self.logger.debug(f"Hook registered: {hook_name}")

    def trigger(self, hook_name: str, **kwargs) -> None:
        """
        触发钩子

        Args:
            hook_name: 钩子名称
            **kwargs: 传递给钩子的参数
        """
        if hook_name not in self.hooks:
            self.logger.debug(f"No hooks registered for: {hook_name}")
            return

        self.logger.debug(f"Triggering hooks: {hook_name}")
        for callback in self.hooks[hook_name]:
            try:
                callback(**kwargs)
            except Exception as e:
                self.logger.error(f"Hook callback failed: {e}", exc_info=True)

    def unregister(self, hook_name: str, callback: Callable) -> None:
        """
        注销钩子

        Args:
            hook_name: 钩子名称
            callback: 要注销的回调函数
        """
        if hook_name in self.hooks:
            if callback in self.hooks[hook_name]:
                self.hooks[hook_name].remove(callback)
                self.logger.debug(f"Hook unregistered: {hook_name}")
```

---

## 🔧 集成到 PromptSystemV2

### 修改后的 PromptSystemV2 类

```python
class PromptSystemV2:
    """
    新版提示词系统，支持钩子
    """

    def __init__(self, config_path: Path, workspace: Path):
        self.config = self._load_config(config_path)
        self.workspace = workspace
        self.prompts_dir = config_path.parent
        self._cache = {}

        # 钩子系统
        self.hooks = HookSystem()

        # 注册默认钩子
        self._register_default_hooks()

    def _register_default_hooks(self):
        """注册默认钩子"""
        # 配置加载完成后，总结配置
        self.hooks.register("on_config_loaded", self._on_config_loaded)

        # 提示词层加载完成后，记录加载进度
        self.hooks.register("on_layer_loaded", self._on_layer_loaded)

        # MainAgent 提示词构建完成后，输出完整提示词
        self.hooks.register(
            "on_main_agent_prompt_built",
            self._on_main_agent_prompt_built
        )

        # Subagent 提示词构建完成后，记录构建信息
        self.hooks.register(
            "on_subagent_prompt_built",
            self._on_subagent_prompt_built
        )

    # ==================== 默认钩子实现 ====================

    def _on_config_loaded(self, config: dict):
        """
        配置加载完成后的默认处理

        Args:
            config: 加载的配置
        """
        self.logger.info(f"Prompt system config loaded: version={config.get('version')}")

        # 记录配置摘要
        layers = list(config.get("layers", {}).keys())
        self.logger.info(f"Configured layers: {', '.join(layers)}")

        # 检查配置完整性
        required_layers = ["core", "workspace", "user"]
        for layer in required_layers:
            if layer not in config.get("layers", {}):
                self.logger.warning(f"Missing required layer: {layer}")

    def _on_layer_loaded(self, layer_name: str, content: dict):
        """
        提示词层加载完成后的默认处理



 Args:
            layer_name: 层名称
            content: 层内容
        """
        sections = list(content.keys())
        self.logger.debug(f"Layer loaded: {layer_name} (sections: {', '.join(sections)})")

    def _on_main_agent_prompt_built(self, prompt: str, sections: dict):
        """
        MainAgent 提示词构建完成后的默认处理

        Args:
            prompt: 完整的系统提示词
            sections: 提示词各部分
        """
        self.logger.info(f"MainAgent prompt built (length: {len(prompt)} chars)")

        # 生成提示词摘要
        summary = self._generate_prompt_summary(sections)

        # 记录到日志
        self.logger.info(f"Prompt summary:\n{summary}")

        # 保存提示词到文件（用于调试）
        self._save_prompt_to_file("main_agent", prompt)

        # 触发自定义钩子（让外部可以自定义处理）
        self.hooks.trigger("on_prompt_ready", agent_type="main_agent", prompt=prompt, sections=sections)

    def _on_subagent_prompt_built(self, task: str, prompt: str, sections: dict):
        """
        Subagent 提示词构建完成后的默认处理

        Args:
            task: 任务描述
            prompt: 完整的系统提示词
            sections: 提示词各部分
        """
        self.logger.info(f"Subagent prompt built for task: {task[:50]}... (length: {len(prompt)} chars)")

        # 保存提示词到文件（用于调试）
        self._save_prompt_to_file("subagent", prompt, task=task)

    # ==================== 辅助方法 ====================

    def _generate_prompt_summary(self, sections: dict) -> str:
        """
        生成提示词摘要

        Args:
            sections: 提示词各部分

        Returns:
            摘要字符串
        """
        summary_lines = []

        for section_name, section_content in sections.items():
            if section_content:
                char_count = len(str(section_content))
                summary_lines.append(f"  - {section_name}: {char_count} chars")
            else:
                summary_linesCharCount(f"  - {section_name}: (empty)")

        return "\n".join(summary_lines)

    def _save_prompt_to_file(self, agent_type: str, prompt: str, task: str | None = None):
        """
        保存提示词到文件（用于调试）

        Args:
            agent_type: Agent 类型
            prompt: 提示词内容
            task: 任务描述（仅 Subagent）
        """
        try:
            import os

            # 创建调试目录
            debug_dir = self.workspace / "debug" / "prompts"
            debug_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if task:
                safe_task = task[:30].replace("/", "_").replace(" ", "_")
                filename = f"{agent_type}_{timestamp}_{safe_task}.md"
            else:
                filename = f"{agent_type}_{timestamp}.md"

            # 写入文件
            filepath = debug_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# System Prompt - {agent_type}\n\n")
                if task:
                    f.write(f"## Task\n\n{task}\n\n")
                f.write(f"## Generated at\n\n{datetime.now().isoformat()}\n\n")
                f.write("---\n\n")
                f.write(prompt)

            self.logger.debug(f"Prompt saved to: {filepath}")

        except Exception as e:
            self.logger.warning(f"Failed to save prompt to file: {e}")
```

---

## 🎯 使用示例

### 示例 1：在 MainAgent 初始化时输出提示词摘要

```python
def print_prompt_summary(**kwargs):
    """打印提示词摘要"""
    agent_type = kwargs.get("agent_type")
    sections = kwargs.get("sections", {})

    print(f"\n{'='*60}")
    print(f"{agent_type.upper()} PROMPT SUMMARY")
    print(f"{'='*60}")

    for section_name, section_content in sections.items():
        if section_content:
            print(f"\n✓ {section_name}: {len(str(section_content))} chars")
        else:
            print(f"\n✗ {section_name}: (empty)")

    print(f"\n{'='*60}\n")

# 注册钩子
prompt_system.hooks.register("on_prompt_ready", print_prompt_summary)
```

### 示例 2：在提示词构建后保存到数据库

```python
async def save_prompt_to_db(**kwargs):
    """保存提示词到数据库"""
    agent_type = kwargs.get("agent_type")
    prompt = kwargs.get("prompt")
    sections = kwargs.get("sections", {})

    # 保存到数据库
    await db.insert({
        "agent_type": agent_type,
        "prompt": prompt,
        "sections": sections,
        "created_at": datetime.now()
    })

    print(f"Prompt saved to database: {agent_type}")

# 注册钩子
prompt_system.hooks.register("on_prompt_ready", save_prompt_to_db)
```

### 示例 3：在配置加载后验证配置

```python
def validate_config(**kwargs):
    """验证配置"""
    config = kwargs.get("config", {})

    # 验证必需字段
    required_fields = ["version", "layers", "templates"]
    missing_fields = [f for f in required_fields if f not in config]

    if missing_fields:
        raise ValueError(f"Missing required config fields: {missing_fields}")

    # 验证 layers
    required_layers = ["core", "workspace", "user"]
    missing_layers = [l for l in required_layers if l not in config.get("layers", {})]

    if missing_layers:
        print(f"Warning: Missing layers: {missing_layers}")

    print(f"Config validated: version={config['version']}")

# 注册钩子
prompt_system.hooks.register("on_config_loaded", validate_config)
```

---

## 📊 钩子触发流程

### MainAgent 初始化流程

```
1. 加载配置文件
   ↓
   trigger("on_config_loaded", config)
   ↓
2. 按层级加载提示词
   ├─ core/
   │  ├─ identity.md
   │  ├─ soul.md
   │  └─ tools.md
   │  → trigger("on_layer_loaded", "core", {...})
   ├─ workspace/
   │  └─ ...
   │  → trigger("on_layer_loaded", "workspace", {...})
   ├─ user/
   │  └─ ...
   │  → trigger("on_layer_loaded", "user", {...})
   └─ ...
   ↓
   trigger("on_prompts_loaded", prompts)
   ↓
3. 构建 MainAgent 系统提示词
   ↓
   trigger("on_main_agent_prompt_built", prompt, sections)
   ↓
   trigger("on_prompt_ready", agent_type="main_agent", ...)
   ↓
4. 初始化 MainAgent
   ↓
   trigger("on_agent_initialized", agent)
   ↓
5. Agent 准备好
   ↓
   trigger("on_agent_ready", agent)
```

---

## ✅ 钩子清单

| 钩子名称 | 触发时机 | 参数 | 用途 |
|---------|---------|------|------|
| on_config_loaded | 配置文件加载完成 | config | 验证配置、记录日志 |
| on_prompts_loaded | 所有提示词加载完成 | prompts | 验证提示词、预处理 |
| on_layer_loaded | 单个提示词层加载完成 | layer_name, content | 记录加载进度 |
| on_main_agent_prompt_built | MainAgent 提示词构建完成 | prompt, sections | 输出提示词摘要、保存调试文件 |
| on_subagent_prompt_built | Subagent 提示词构建完成 | task, prompt, sections | 记录构建信息、保存调试文件 |
| on_prompt_ready | 任意提示词构建完成（通用） | agent_type, prompt, sections | 自定义处理 |
| on_agent_initialized | Agent 初始化完成 | agent | 设置 Agent 属性、注册工具 |
| on_agent_ready | Agent 准备好接收消息 | agent | 启动监听、发送就绪通知 |

---

## 🎨 最佳实践

### 1. 钩子命名规范

```python
# 好的命名
def on_config_loaded(config): ...
def on_main_agent_prompt_built(prompt, sections): ...

# 不好的命名
def handle_config(cfg): ...
def build_prompt_done(p, s): ...
```

### 2. 钩子异常处理

```python
def safe_hook(**kwargs):
    """安全的钩子实现"""
    try:
        # 执行钩子逻辑
        pass
    except Exception as e:
        # 记录错误，但不中断流程
        logging.error(f"Hook failed: {e}", exc_info=True)
```

### 3. 钩子性能优化

```python
# 对于耗时操作，使用异步
async def async_hook(**kwargs):
    """异步钩子"""
    await some_async_operation()

# 或者使用后台线程
import threading

def background_hook(**kwargs):
    """后台钩子"""
    def _run():
        # 耗时操作
        pass
    threading.Thread(target=_run, daemon=True).start()
```

### 4. 钩子条件执行

```python
def conditional_hook(**kwargs):
    """条件钩子"""
    if kwargs.get("agent_type") == "main_agent":
        # 只对 MainAgent 执行
        pass
```

---

## 🔍 调试支持

### 启用钩子日志

```python
import logging

# 设置日志级别为 DEBUG
logging.basicConfig(level=logging.DEBUG)

# 钩子系统会输出详细的调试信息
# - 钩子注册
# - 钩子触发
# - 钩子执行时间
# - 钩子异常
```

### 查看已注册的钩子

```python
def list_hooks(hook_system: HookSystem):
    """列出所有已注册的钩子"""
    print("Registered hooks:")
    for hook_name, callbacks in hook_system.hooks.items():
        print(f"  - {hook_name}: {len(callbacks)} callback(s)")
```

---

## 📝 总结

钩子系统提供了灵活的扩展机制，允许在关键阶段插入自定义逻辑：

✅ **配置加载阶段** - 验证配置、记录日志
✅ **提示词加载阶段** - 验证提示词、预处理
✅ **提示词构建阶段** - 输出摘要、保存调试文件
✅ **Agent 初始化阶段** - 设置属性、注册工具
✅ **Agent 就绪阶段** - 启动监听、发送通知

通过钩子，可以轻松实现：
- 提示词摘要输出
- 调试信息保存
- 配置验证
- 性能监控
- 自定义扩展
