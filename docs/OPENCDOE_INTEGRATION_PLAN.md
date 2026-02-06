# Nanobot Opencode 组件整合计划

## 执行摘要

本计划将 Opencode 的关键组件整合到 Nanobot 中，重点添加代码质量、调试和版本控制工作流功能，同时保持 Nanobot 的轻量级特性。

## 一、Opencode 组件分析

### 1.1 Skills 分析

#### ✅ 适合 Nanobot 的 Skills

| Skill 名称 | 描述 | 优先级 | 理由 |
|-----------|--------|---------|------|
| `code-review` | 自动化代码审查，分析质量、安全、性能 | 🔴 高 | Nanobot 需要代码质量保证 |
| `code-refactoring` | 代码重构模式和技巧 | 🟡 中 | 改进现有代码质量 |
| `backend-dev` | 后端开发工作流 | 🟡 中 | 部分功能适合 |
| `frontend-design` | Nanobot 是后端系统，不涉及前端设计 |-|-|
| `frontend-ui-ux` | 前端 UI/UX 相关 |-|-|
| `shadcn-management` | shadcn/ui 是前端组件库 |-|-|
| `ui-ux-pro-max` | UI/UX 设计工具，前端专用 |-|-|
| `browser` | 浏览器自动化，超出范围 |-|-|
| `frontend-ui-integration` | 前端集成 |-|-|
| `frontend-ui-animator` | 前端动画 |-|-|

### 1.3 Commands 分析

#### ✅ 适合 Nanobot 的 Commands

| Command | 描述 | 优先级 | 适配工作 |
|----------|--------|---------|----------|
| `/review` | 代码审查 | 🔴 高 | 调整为 Python 代码 |
| `/optimize` | 代码优化 | 🔴 高 | 适配后端性能优化 |
| `/test` | 测试管道 | 🔴 高 | 使用 pytest 替代 pnpm |
| `/fix` | Bug 诊断和修复 | 🔴 高 | 适配 Python 调试 |
| `/commit` | Git 提交 | 🟡 中 | 直接可用 |
| `/debug` | 系统调试 | 🟡 中 | 适配 Python |
| `/brainstorm` | 头脑风暴 | 🟢 低 | 可选功能规划 |
| `/write-plan` | 编写计划 | 🟢 低 | 未来功能 |

## 二、整合策略

### 2.1 架构设计

```
nanobot/
├── agent/
│   ├── loop.py           # 增强：命令路由
│   ├── tools/
│   │   └── registry.py  # 增强：注册新工具
│   └── experts/         # 新增：专家系统
│       ├── __init__.py
│       ├── base.py
│       └── code_review.py
├── commands/            # 新增：命令系统
│   ├── __init__.py
│   ├── base.py
│   ├── review.py
│   ├── optimize.py
│   ├── test.py
│   ├── fix.py
│   ├── commit.py
│   └── debug.py
├── skills/              # 增强：opencode skills
│   ├── nanobot/          # 内置技能
│   └── opencode/         # 新增：opencode 技能
│       ├── code-review/
│       │   └── SKILL.md
│       └── code-refactoring/
│           └── SKILL.md
└── config/
    └── schema.py       # 增强：添加 commands 配置
```

### 2.2 分阶段实现

## 三、详细实现计划

### 阶段 1: 基础设施搭建（第 1 周）

#### 任务 1.1: 增强技能加载器

**文件**: `nanobot/agent/skills.py`

**目标**: 支持从 `skills/opencode/` 加载技能

```python
# 在 SkillsLoader 中添加
def __init__(self, workspace: Path, builtin_skills_dir: Path | None = None):
    self.workspace = workspace
    self.workspace_skills = workspace / "skills"
    self.builtin_skills = builtin_skills_dir or BUILTIN_SKILLS_DIR
    # 添加 opencode skills 目录
    self.opencode_skills = Path(__file__).parent.parent / "skills" / "opencode"
```

**验收标准**:
- [ ] `list_skills()` 能发现 opencode skills
- [ ] `load_skill()` 能正确加载 SKILL.md
- [ ] 保持向后兼容性

#### 任务 1.2: 复制 Opencode Skills

**源文件**:
- `/Users/jiangyayun/.config/opencode/skills/code-review/SKILL.md`
- `/Users/jiangyayun/.config/opencode/skills/code-refactoring/SKILL.md`

**目标目录**: `nanobot/skills/opencode/`

**操作**:
```bash
mkdir -p nanobot/skills/opencode/code-review
cp /Users/jiangyayun/.config/opencode/skills/code-review/SKILL.md \
   nanobot/skills/opencode/code-review/

mkdir -p nanobot/skills/opencode/code-refactoring
cp /Users/jiangyayun/.config/opencode/skills/code-refactoring/SKILL.md \
   nanobot/skills/opencode/code-refactoring/
```

**验收标准**:
- [ ] 文件成功复制
- [ ] 内容保持完整
- [ ] 包含正确的 frontmatter

#### 任务 1.3: 测试技能加载

**测试文件**: `tests/test_opencode_skills.py`

```python
import pytest
from nanobot.agent.skills import SkillsLoader
from pathlib import Path

def test_opencode_skills_loading():
    loader = SkillsLoader(Path("/tmp/test_workspace"))
    skills = loader.list_skills()

    opencode_skills = [s for s in skills if s["source"] == "opencode"]
    assert len(opencode_skills) >= 2

    skill_names = [s["name"] for s in opencode_skills]
    assert "code-review" in skill_names
    assert "code-refactoring" in skill_names

def test_load_code_review_skill():
    loader = SkillsLoader(Path("/tmp/test_workspace"))
    content = loader.load_skill("code-review")
    assert content is not None
    assert "security" in content.lower()
```

**验收标准**:
- [ ] 所有测试通过
- [ ] 代码覆盖率 > 80%

### 阶段 2: 命令系统实现（第 2 周）

#### 任务 2.1: 命令基础类

**文件**: `nanobot/commands/base.py`

```python
from abc import ABC, abstractmethod
from typing import Any

class Command(ABC):
    """命令基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """命令名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """命令描述"""
        pass

    @property
    def aliases(self) -> list[str]:
        """命令别名"""
        return []

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> str:
        """执行命令"""
        pass
```

**验收标准**:
- [ ] 基类正确定义
- [ ] 类型提示完整
- [ ] 文档清晰

#### 任务 2.2: Review 命令实现

**文件**: `nanobot/commands/review.py`

```python
from .base import Command

class ReviewCommand(Command):
    """代码审查命令"""

    @property
    def name(self) -> str:
        return "review"

    @property
    def description(self) -> str:
        return "Request a code review for current changes"

    @property
    def aliases(self) -> list[str]:
        return ["code-review", "cr"]

    async def execute(self, context: dict[str, Any]) -> str:
        """执行代码审查"""
        # 加载 code-review skill
        skills_loader = context["skills"]
        skill_content = skills_loader.load_skill("code-review")

        # 获取当前文件变更
        workspace = context["workspace"]
        # 使用 git diff 获取变更

        # 使用 LLM 分析代码
        provider = context["provider"]
        messages = [
            {"role": "system", "content": skill_content},
            {"role": "user", "content": "Review this code:\n\n<code_changes>..."},
        ]

        response = await provider.chat(messages=messages, model=context.get("model"))
        return response.content
```

**验收标准**:
- [ ] 能加载 code-review skill
- [ ] 能获取 git 变更
- [ ] 能调用 LLM 进行审查
- [ ] 返回格式化的审查报告

#### 任务 2.3: Optimize 命令实现

**文件**: `nanobot/commands/optimize.py`

```python
from .base import Command

class OptimizeCommand(Command):
    """代码优化命令"""

    @property
    def name(self) -> str:
        return "optimize"

    @property
    def description(self) -> str:
        return "Analyze and optimize code for performance, security, and potential issues"

    async def execute(self, context: dict[str, Any]) -> str:
        """执行代码优化分析"""
        # 分析性能、安全、架构
        # 使用 backend-dev skill 的优化部分
        pass
```

**验收标准**:
- [ ] 分析性能问题
- [ ] 检查安全漏洞
- [ ] 提供优化建议

#### 任务 2.4: Test 命令实现

**文件**: `nanobot/commands/test.py`

```python
from .base import Command
import subprocess

class TestCommand(Command):
    """测试命令"""

    @property
    def name(self) -> str:
        return "test"

    @property
    def description(self) -> str:
        return "Run complete testing pipeline"

    async def execute(self, context: dict[str, Any]) -> str:
        """执行测试管道"""
        results = []

        # 1. 类型检查
        try:
            subprocess.run(["ruff", "check", "--select", "I"], check)
            results.append("✅ Type check passed")
        except:
            results.append("❌ Type check failed")

        # 2. Lint
        try:
            subprocess.run(["ruff", "check", "."], check)
            results.append("✅ Lint passed")
        except:
            results.append("❌ Lint failed")

        # 3. 运行测试
        try:
            subprocess.run(["pytest"], check)
            results.append("✅ Tests passed")
        except:
            results.append("❌ Tests failed")

        return "\n".join(results)
```

**验收标准**:
- [ ] 运行 ruff 类型检查
- [ ] 运行 ruff lint
- [ ] 运行 pytest
- [ ] 返回清晰的结果报告

#### 任务 2.5: Commit 命令实现

**文件**: `nanobot/commands/commit.py`

```python
from .base import Command
import subprocess

class CommitCommand(Command):
    """Git 提交命令"""

    @property
    def name(self) -> str:
        return "commit"

    @property
    def description(self) -> str:
        return "Create well-formatted git commits"

    async def execute(self, context: dict[str, Any]) -> str:
        """执行 git 提交"""
        # 1. 运行测试
        test_cmd = TestCommand()
        test_result = await test_cmd.execute(context)
        if "❌" in test_result:
            return f"Tests failed, cannot commit:\n{test_result}"

        # 2. 分析 git 状态
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True
        ).stdout

        if not status.strip():
            return "No changes to commit"

        # 3. 分析变更
        diff = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True
        ).stdout

        # 4. 生成提交消息
        # 使用 LLM 生成符合规范的提交消息

        # 5. 执行提交
        subprocess.run(["git", "commit", "-m", message])

        return f"✅ Committed: {message[:50]}..."
```

**验收标准**:
- [ ] 提交前运行测试
- [ ] 自动 stage 文件
- [ ] 生成规范的提交消息
- [ ] 成功执行提交

#### 任务 2.6: Fix 命令实现

**文件**: `nanobot/commands/fix.py`

```python
from .base import Command

class FixCommand(Command):
    """Bug 修复命令"""

    @property
    def name(self) -> str:
        return "fix"

    @property
    def description(self) -> str:
        return "Diagnose and fix bugs with systematic approach"

    async def execute(self, context: dict[str, Any]) -> str:
        """执行 bug 修复"""
        # 添加诊断日志
        # 分析根本原因
        # 实施修复
        # 验证修复
        pass
```

**验收标准**:
- [ ] 系统化诊断流程
- [ ] 假设驱动方法
- [ ] 用户确认步骤

#### 任务 2.7: 命令注册表

**文件**: `nanobot/commands/registry.py`

```python
from typing import Any
from .base import Command

class CommandRegistry:
    """命令注册表"""

    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._register_builtin_commands()

    def _register_builtin_commands(self):
        """注册内置命令"""
        from .review import ReviewCommand
        from .optimize import OptimizeCommand
        from .test import TestCommand
        from .commit import CommitCommand
        from .fix import FixCommand
        from .debug import DebugCommand

        self.register(ReviewCommand())
        self.register(OptimizeCommand())
        self.register(TestCommand())
        self.register(CommitCommand())
        self.register(FixCommand())
        self.register(DebugCommand())

    def register(self, command: Command):
        """注册命令"""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command

    def get(self, name: str) -> Command | None:
        """获取命令"""
        return self._commands.get(name)

    def parse_command(self, message: str) -> tuple[str | None, dict[str, Any]]:
        """解析命令"""
        if not message.startswith("/"):
            return None, {}

        parts = message[1:].split(maxsplit=1)
        command_name = parts[0]
        args_str = parts[1] if len(parts) > 1 else ""

        return command_name, {"raw": args_str}
```

**验收标准**:
- [ ] 所有命令成功注册
- [ ] 别名正确映射
- [ ] 能解析命令字符串

### 阶段 3: Agent Loop 集成（第 3 周）

#### 任务 3.1: 增强 Agent Loop

**文件**: `nanobot/agent/loop.py`

**修改**: 集成命令系统

```python
class AgentLoop:
    def __init__(self, ...):
        # ... 现有初始化 ...

        # 添加命令系统
        from nanobot.commands.registry import CommandRegistry
        self.commands = CommandRegistry()

    async def _process_message(self, msg: InboundMessage) -> OutboundMessage | None:
        """增强的消息处理"""
        # 检查命令
        command_name, args = self.commands.parse_command(msg.content)
        if command_name:
            return await self._handle_command(msg, command_name, args)

        # 原有处理逻辑
        return await self._original_process_message(msg)

    async def _handle_command(self, msg: InboundMessage, command_name: str, args: dict[str, Any]) -> OutboundMessage:
        """处理命令执行"""
        command = self.commands.get(command_name)
        if not command:
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"Unknown command: /{command_name}",
            )

        try:
            context = {
                "args": args,
                "workspace": self.workspace,
                "provider": self.provider,
                "model": self.model,
                "skills": self.skills,
                "session": self.sessions.get_or_create(msg.session_key),
            }

            result = await command.execute(context)

            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=result,
            )
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"Error: {str(e)}",
            )
```

**验收标准**:
- [ ] 命令正确路由
- [ ] 错误处理完善
- [ ] 上下文正确传递

#### 任务 3.2: 配置更新

**文件**: `nanobot/config/schema.py`

**添加**: 命令配置

```python
class CommandsConfig(BaseModel):
    enabled: bool = True
    prefix: str = "/"

class Config(BaseModel):
    # ... 现有字段 ...

    commands: CommandsConfig = Field(default_factory=CommandsConfig)
```

**验收标准**:
- [ ] 配置模式更新
- [ ] 向后兼容
- [ ] 默认值合理

### 阶段 4: 测试与文档（第 4 周）

#### 任务 4.1: 集成测试

**测试文件**: `tests/test_integration.py`

```python
import pytest
from nanobot.agent.loop import AgentLoop
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider

@pytest.mark.asyncio
async def test_command_execution():
    """测试命令执行"""
    bus = MessageBus()
    provider = MockLLMProvider()
    loop = AgentLoop(bus=bus, provider=provider, workspace=Path("/tmp"))

    # 发送命令消息
    msg = InboundMessage(
        channel="cli",
        sender_id="user",
        chat_id="test",
        content="/test",
    )

    response = await loop._process_message(msg)
    assert "Tests" in response.content

@pytest.mark.asyncio
async def test_review_command():
    """测试代码审查命令"""
    # 类似测试...
    pass
```

**验收标准**:
- [ ] 所有命令测试通过
- [ ] 集成测试覆盖主要流程
- [ ] 错误场景测试覆盖

#### 任务 4.2: 文档更新

**更新文件**:
- `README.md` - 添加命令使用说明
- `AGENTS.md` - 更新开发指南
- `docs/OPENCODE_INTEGRATION.md` - 新增整合文档

**内容示例**:

```markdown
## Commands

Nanobot 现在支持以下命令：

| 命令 | 描述 | 用法 |
|------|------|------|
| `/review` | 代码审查 | `/review [files]` |
| `/optimize` | 代码优化 | `/optimize [path]` |
| `/test` | 运行测试 | `/test` |
| `/fix` | 修复 bug | `/fix "error description"` |
| `/commit` | Git 提交 | `/commit [message]` |
| `/debug` | 调试 | `/debug "issue"` |

### 示例

# 代码审查
/review nanobot/agent/loop.py

# 运行测试
/test

# 提交更改
/commit
```

**验收标准**:
- [ ] README 更新
- [ ] 开发指南更新
- [ ] 整合文档完整
- [ ] 示例代码可用

#### 任务 4.3: 性能测试

**测试文件**: `tests/test_performance.py`

```python
import time

def test_command_parsing_performance():
    """测试命令解析性能"""
    registry = CommandRegistry()

    start = time.time()
    for i in range(1000):
        registry.parse_command(f"/test arg{i}")

    duration = time.time() - start
    assert duration < 0.1  # 1000 次解析在 100ms 内完成
```

**验收标准**:
- [ ] 性能基准建立
- [ ] 无明显性能退化
- [ ] 内存使用合理

## 四、优先级矩阵

| 任务 | 优先级 | 依赖 | 预计时间 | 风险 |
|------|---------|-------|----------|------|
| 技能加载器增强 | P0 | 无 | 1 天 | 低 |
| 复制 Opencode Skills | P0 | 无 | 0.5 天 | 低 |
| 命令基础类 | P0 | 无 | 0.5 天 | 低 |
| Test 命令 | P0 | 命令基础类 | 1 天 | 中 |
| Review 命令 | P0 | 命令基础类 | 2 天 | 中 |
| Commit 命令 | P0 | Test 命令 | 1.5 天 | 中 |
| Optimize 命令 | P1 | Review 命令 | 2 天 | 中 |
| Fix 命令 | P1 | Review 命令 | 3 天 | 高 |
| Agent Loop 集成 | P0 | 所有命令 | 2 天 | 中 |
| 配置更新 | P0 | Agent Loop 集成 | 0.5 天 | 低 |
| 集成测试 | P0 | Agent Loop 集成 | 2 天 | 中 |
| 文档更新 | P1 | 集成测试 | 1 天 | 低 |
| 性能测试 | P2 | 所有组件 | 1 天 | 低 |

## 五、风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|-------|---------|
| 命令冲突 | 高 | 中 | 提供命令列表，明确的命名空间 |
| 性能退化 | 高 | 低 | 性能基准测试，懒加载 |
| 向后兼容性破坏 | 高 | 中 | 保持现有接口，渐进迁移 |
| LLM 上下文溢出 | 中 | 中 | 分段处理，上下文管理 |
| 测试不完整 | 中 | 中 | TDD 方法，持续集成 |

## 六、成功指标

### 功能指标
- [ ] 6 个命令成功实现
- [ ] 2 个 Opencode skills 成功加载
- [ ] 命令系统完全集成到 Agent Loop

### 质量指标
- [ ] 代码覆盖率 > 80%
- [ ] 所有 ruff 检查通过
- [ ] 所有类型检查通过
- [ ] 无已知 bug

### 性能指标
- [ ] 启动时间 < 2 秒
- [ ] 命令解析 < 1ms
- [ ] 内存开销 < 50MB

### 用户体验指标
- [ ] 命令响应时间 < 3 秒
- [ ] 错误消息清晰
- [ ] 帮助文档完整

## 七、实施时间表

### 第 1 周：基础设施
- Day 1-2: 技能加载器增强 + 复制 Opencode Skills
- Day 3: 命令基础类 + Test 命令
- Day 4: Review 命令
- Day 5: 测试和验证

### 第 2 周：核心命令
- Day 1-2: Commit 命令
- Day 3-4: Optimize 命令
- Day 5: 集成测试

### 第 3 周：高级功能
- Day 1-3: Fix 命令
- Day 4: Agent Loop �集成
- Day 5: 配置更新

### 第 4 周：完善和测试
- Day 1-2: 集成测试
- Day 3: 文档更新
- Day 4: 性能测试
- Day 5: 最终验证

## 八、验收清单

### 功能验收
- [ ] `/review` 命令工作正常
- [ ] `/optimize` 命令工作正常
- [ ] `/test` 命令工作正常
- [ ] `/fix` 命令工作正常
- [ ] `/commit` 命令工作正常
- [ ] `/debug` 命令工作正常
- [ ] Opencode skills 可用
- [ ] 命令别名工作

### 质量验收
- [ ] 所有测试通过
- [ ] 代码覆盖率达标
- [ ] Lint 无错误
- [ ] 类型检查通过
- [ ] 文档完整

### 性能验收
- [ ] 启动时间达标
- [ ] 命令响应快
- [ ] 内存使用合理
- [ ] 无明显性能退化

## 九、后续优化

### 短期（下个版本）
- [ ] 添加更多 Opencode skills
- [ ] 实现专家系统（从 agent 演进）
- [ ] 添加 MCP 服务器集成
- [ ] 支持自定义命令

### 长期（未来版本）
- [ ] 完整的专家代理系统
- [ ] 工作流编排
- [ ] 跨项目记忆
- [ ] 自我改进能力

## 十、资源

### 参考文档
- `docs/OPENCODE_DESIGN.md` - 整合设计文档
- `AGENTS.md` - 开发指南
- `/Users/jiangyayun/.config/opencode/` - Opencode 源文件

### 外部资源
- [Opencode Skills](.config/opencode/skills/)
- [Opencode Commands](.config/opencode/commands/)
- [Pytest 文档](https://docs.pytest.org/)
- [Ruff 文档](https://docs.astral.sh/ruff/)

---

**计划状态**: 准备就绪
**预计完成时间**: 4 周
**负责人**: AI Assistant
**最后更新**: 2026-02-07
