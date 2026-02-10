# Nanobot API 文档

## 概述

本文档描述了 Nanobot 项目的主要 API 接口，包括主代理、上下文管理、任务规划、执行决策和子代理管理等核心功能的接口定义。

## 1. MainAgent（主代理）

### 类定义

```python
class MainAgent(BaseModel):
    """
    Nanobot 的主代理类，负责协调整个系统的运行。
    """
```

### 方法

#### `__init__`

```python
def __init__(
    self,
    config: Optional[Config] = None,
    task_manager: Optional[TaskManager] = None,
    subagent_manager: Optional[SubagentManager] = None,
    context_manager: Optional[ContextManager] = None,
    decision_maker: Optional[ExecutionDecisionMaker] = None,
    hooks: Optional[MainAgentHooks] = None,
):
    """
    初始化 MainAgent 实例。

    Args:
        config: 配置对象
        task_manager: 任务管理器
        subagent_manager: 子代理管理器
        context_manager: 上下文管理器
        decision_maker: 执行决策器
        hooks: 钩子系统

    Returns:
        MainAgent 实例
    """
```

#### `process_message`

```python
async def process_message(
    self,
    message: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    message_type: str = "user",
) -> Union[str, Dict[str, Any]]:
    """
    处理用户消息并返回响应。

    Args:
        message: 用户输入的消息
        user_id: 用户 ID（可选）
        session_id: 会话 ID（可选）
        task_id: 任务 ID（可选）
        context: 上下文信息（可选）
        message_type: 消息类型（可选，默认 "user"）

    Returns:
        响应内容，可以是字符串或字典
    """
```

#### `get_status`

```python
async def get_status(self, task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    获取系统状态信息。

    Args:
        task_id: 任务 ID（可选，如果提供则获取该任务的状态）

    Returns:
        状态信息字典
    """
```

## 2. ContextManager（上下文管理）

### 类定义

```python
class ContextManager(BaseModel):
    """
    上下文管理器，负责管理任务执行过程中的上下文信息。
    """
```

### 方法

#### `__init__`

```python
def __init__(
    self,
    compressor: Optional[ContextCompressor] = None,
    expander: Optional[ContextExpander] = None,
    memory_store: Optional[EnhancedMemoryStore] = None,
    skill_loader: Optional[SkillLoader] = None,
):
    """
    初始化 ContextManager 实例。

    Args:
        compressor: 上下文压缩器
        expander: 上下文扩展器
        memory_store: 增强记忆存储
        skill_loader: 技能加载器

    Returns:
        ContextManager 实例
    """
```

#### `build_context`

```python
async def build_context(
    self,
    user_input: str,
    task_id: Optional[str] = None,
    task_type: Optional[TaskType] = None,
    memory_tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    构建上下文信息。

    Args:
        user_input: 用户输入文本
        task_id: 任务 ID（可选）
        task_type: 任务类型（可选）
        memory_tags: 记忆标签（可选）

    Returns:
        上下文信息字典
    """
```

#### `update_context`

```python
async def update_context(
    self,
    task_id: str,
    updates: Dict[str, Any],
) -> bool:
    """
    更新任务上下文。

    Args:
        task_id: 任务 ID
        updates: 要更新的上下文信息

    Returns:
        是否更新成功
    """
```

#### `get_context`

```python
async def get_context(
    self,
    task_id: str,
) -> Optional[Dict[str, Any]]:
    """
    获取任务上下文。

    Args:
        task_id: 任务 ID

    Returns:
        上下文信息字典，或 None（如果任务不存在）
    """
```

## 3. TaskPlanner（任务规划）

### 类定义

```python
class TaskPlanner(BaseModel):
    """
    任务规划器，负责分析用户输入，识别任务类型，评估复杂度，并制定执行计划。
    """
```

### 方法

#### `__init__`

```python
def __init__(
    self,
    complexity_analyzer: Optional[ComplexityAnalyzer] = None,
    task_detector: Optional[TaskDetector] = None,
    correction_detector: Optional[CorrectionDetector] = None,
    cancellation_detector: Optional[CancellationDetector] = None,
):
    """
    初始化 TaskPlanner 实例。

    Args:
        complexity_analyzer: 复杂度分析器
        task_detector: 任务检测器
        correction_detector: 修正检测器
        cancellation_detector: 取消检测器

    Returns:
        TaskPlanner 实例
    """
```

#### `plan_task`

```python
async def plan_task(
    self,
    user_input: str,
    context: Optional[Dict[str, Any]] = None,
) -> Union[TaskPlan, Dict[str, str]]:
    """
    规划任务执行计划。

    Args:
        user_input: 用户输入文本
        context: 上下文信息（可选）

    Returns:
        任务执行计划（TaskPlan）或修正/取消指令（字典）
    """
```

#### `is_complex_task`

```python
async def is_complex_task(self, user_input: str) -> bool:
    """
    判断任务是否复杂。

    Args:
        user_input: 用户输入文本

    Returns:
        是否为复杂任务
    """
```

#### `get_task_type`

```python
async def get_task_type(self, user_input: str) -> TaskType:
    """
    获取任务类型。

    Args:
        user_input: 用户输入文本

    Returns:
        任务类型（TaskType）
    """
```

## 4. ExecutionDecisionMaker（执行决策）

### 类定义

```python
class ExecutionDecisionMaker(BaseModel):
    """
    执行决策器，负责根据用户输入和系统状态做出执行决策。
    """
```

### 方法

#### `__init__`

```python
def __init__(self, decision_handlers: Optional[Dict[str, Any]] = None):
    """
    初始化 ExecutionDecisionMaker 实例。

    Args:
        decision_handlers: 决策处理器（可选）

    Returns:
        ExecutionDecisionMaker 实例
    """
```

#### `make_decision`

```python
async def make_decision(
    self,
    request: Dict[str, Any],
    task: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> DecisionResult:
    """
    做出执行决策。

    Args:
        request: 决策请求
        task: 任务信息（可选）
        context: 上下文信息（可选）

    Returns:
        决策结果（DecisionResult）
    """
```

#### `register_handler`

```python
def register_handler(self, request_type: str, handler: Any):
    """
    注册决策处理器。

    Args:
        request_type: 请求类型
        handler: 处理器实例

    Returns:
        None
    """
```

## 5. SubagentManager（子代理管理）

### 类定义

```python
class SubagentManager(BaseModel):
    """
    子代理管理器，负责管理子代理的创建、执行和监控。
    """
```

### 方法

#### `__init__`

```python
def __init__(
    self,
    hook_system: Optional[SubagentHooks] = None,
    interrupt_handler: Optional[InterruptHandler] = None,
    risk_evaluator: Optional[RiskEvaluator] = None,
):
    """
    初始化 SubagentManager 实例。

    Args:
        hook_system: 钩子系统
        interrupt_handler: 中断处理器
        risk_evaluator: 风险评估器

    Returns:
        SubagentManager 实例
    """
```

#### `spawn_subagent`

```python
async def spawn_subagent(
    self,
    task: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
) -> Optional[str]:
    """
    生成新的子代理来执行任务。

    Args:
        task: 任务信息
        context: 上下文信息（可选）
        timeout: 超时时间（可选）

    Returns:
        子代理 ID（可选，失败时返回 None）
    """
```

#### `cancel_subagent`

```python
async def cancel_subagent(
    self,
    subagent_id: str,
    reason: Optional[str] = None,
) -> bool:
    """
    取消子代理的执行。

    Args:
        subagent_id: 子代理 ID
        reason: 取消原因（可选）

    Returns:
        是否取消成功
    """
```

#### `get_subagent_status`

```python
async def get_subagent_status(
    self,
    subagent_id: str,
) -> Optional[Dict[str, Any]]:
    """
    获取子代理的状态。

    Args:
        subagent_id: 子代理 ID

    Returns:
        子代理状态信息（可选，不存在时返回 None）
    """
```

#### `get_running_tasks`

```python
async def get_running_tasks(self) -> List[Dict[str, Any]]:
    """
    获取所有正在运行的任务。

    Returns:
        正在运行的任务列表
    """
```

## 6. 数据模型

### TaskPlan（任务计划）

```python
class TaskPlan(BaseModel):
    """
    任务执行计划数据模型。
    """
    task_type: TaskType
    priority: TaskPriority
    complexity: float
    steps: List[str]
    estimated_time: int
    requires_approval: bool
```

### TaskType（任务类型）

```python
class TaskType(str, Enum):
    """
    任务类型枚举。
    """
    CODE_GENERATION = "code_generation"
    TEXT_SUMMARIZATION = "text_summarization"
    DATA_ANALYSIS = "data_analysis"
    WEB_SEARCH = "web_search"
    FILE_OPERATION = "file_operation"
    SYSTEM_COMMAND = "system_command"
    OTHER = "other"
```

### TaskPriority（任务优先级）

```python
class TaskPriority(str, Enum):
    """
    任务优先级枚举。
    """
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

### DecisionResult（决策结果）

```python
class DecisionResult(BaseModel):
    """
    决策结果数据模型。
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None
    requires_approval: bool = False
```

## 7. Workflow Manager（工作流管理）

### 类定义

```python
class WorkflowManager:
    """
    工作流管理器，负责管理工作流的创建、状态跟踪和任务管理。
    """
```

### 方法

#### `__init__`

```python
def __init__(self, workspace: Path = Path("workspace")):
    """
    初始化 WorkflowManager 实例。

    Args:
        workspace: 工作区路径（可选，默认 "workspace"）

    Returns:
        WorkflowManager 实例
    """
```

#### `create_workflow`

```python
def create_workflow(self, name: str, steps: List[WorkflowStep]) -> str:
    """
    创建一个新的工作流。

    Args:
        name: 工作流名称
        steps: 工作流步骤列表

    Returns:
        工作流 ID
    """
```

#### `get_workflow_state`

```python
def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
    """
    获取工作流的当前状态。

    Args:
        workflow_id: 工作流 ID

    Returns:
        工作流状态（WorkflowState）或 None（如果工作流不存在）
    """
```

#### `create_task`

```python
def create_task(self, workflow_id: str, task_id: str, description: str) -> str:
    """
    在指定工作流中创建一个新任务。

    Args:
        workflow_id: 工作流 ID
        task_id: 任务 ID
        description: 任务描述

    Returns:
        任务 ID
    """
```

#### `get_task_status`

```python
def get_task_status(self, task_id: str) -> Optional[TaskState]:
    """
    获取任务的当前状态。

    Args:
        task_id: 任务 ID

    Returns:
        任务状态（TaskState）或 None（如果任务不存在）
    """
```

#### `pause_workflow`

```python
def pause_workflow(self, workflow_id: str) -> None:
    """
    暂停工作流。

    Args:
        workflow_id: 工作流 ID

    Raises:
        ValueError: 工作流不存在
    """
```

#### `resume_workflow`

```python
def resume_workflow(self, workflow_id: str) -> None:
    """
    恢复暂停的工作流。

    Args:
        workflow_id: 工作流 ID

    Raises:
        ValueError: 工作流不存在
    """
```

#### `complete_workflow`

```python
def complete_workflow(self, workflow_id: str) -> None:
    """
    完成工作流。

    Args:
        workflow_id: 工作流 ID

    Raises:
        ValueError: 工作流不存在
    """
```

#### `cancel_workflow`

```python
def cancel_workflow(self, workflow_id: str) -> None:
    """
    取消工作流。

    Args:
        workflow_id: 工作流 ID

    Raises:
        ValueError: 工作流不存在
    """
```

#### `update_task_status`

```python
def update_task_status(self, task_id: str, status: TaskState) -> None:
    """
    更新任务状态。

    Args:
        task_id: 任务 ID
        status: 新状态

    Raises:
        ValueError: 任务不存在
    """
```

#### `get_workflow_tasks`

```python
def get_workflow_tasks(self, workflow_id: str) -> List[str]:
    """
    获取工作流中的所有任务。

    Args:
        workflow_id: 工作流 ID

    Returns:
        任务 ID 列表

    Raises:
        ValueError: 工作流不存在
    """
```

#### `list_workflows`

```python
def list_workflows(self) -> List[Dict]:
    """
    列出所有工作流。

    Returns:
        工作流信息列表
    """
```

#### `handle_task_message`

```python
def handle_task_message(self, category: MessageCategory, message: str) -> str:
    """
    处理任务相关消息。

    Args:
        category: 消息类别
        message: 消息内容

    Returns:
        响应内容
    """
```

## 8. Message Router（消息路由器）

### 类定义

```python
class MessageRouter:
    """
    消息路由器，负责将消息分类并路由到相应的处理器。
    """
```

### 方法

#### `__init__`

```python
def __init__(self, llm_provider=None):
    """
    初始化 MessageRouter 实例。

    Args:
        llm_provider: LLM 提供者（可选）

    Returns:
        MessageRouter 实例
    """
```

#### `get_category`

```python
def get_category(self, message: str) -> MessageCategory:
    """
    对消息进行分类。

    Args:
        message: 要分类的消息

    Returns:
        消息类别（MessageCategory）
    """
```

#### `route`

```python
async def route(self, message: str, context: Dict) -> MessageCategory:
    """
    路由消息到相应类别（异步版本）。

    Args:
        message: 要路由的消息
        context: 分类的额外上下文

    Returns:
        消息类别（MessageCategory）
    """
```

#### `get_category_hint`

```python
async def get_category_hint(self, message: str) -> str:
    """
    获取消息分类的提示。

    Args:
        message: 要分析的消息

    Returns:
        分类提示字符串
    """
```

## 9. 数据模型（新增）

### MessageCategory（消息类别）

```python
class MessageCategory(Enum):
    """
    消息分类枚举。
    """
    CHAT = "chat"          # 普通对话
    INQUIRY = "inquiry"    # 询问类消息
    TASK_CREATE = "task_create"      # 创建任务
    TASK_STATUS = "task_status"     # 查询任务状态
    TASK_CANCEL = "task_cancel"      # 取消任务
    TASK_COMPLETE = "task_complete"  # 完成任务
    TASK_LIST = "task_list"         # 列出任务
    CONTROL = "control"              # 控制命令
    HELP = "help"                    # 帮助命令
    UNKNOWN = "unknown"
```

### TaskState（任务状态）

```python
class TaskState(Enum):
    """
    任务状态枚举。
    """
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    PAUSED = "paused"       # 已暂停
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    FAILED = "failed"        # 失败
```

### WorkflowStep（工作流步骤）

```python
class WorkflowStep:
    """
    工作流步骤数据模型。
    """
    step_id: str
    name: str
    description: str
    dependencies: List[str]
    status: TaskState
    start_time: Optional[float]
    end_time: Optional[float]
    output: Any
    error: Optional[str]
```

### WorkflowState（工作流状态）

```python
class WorkflowState(Enum):
    """
    工作流状态枚举。
    """
    PLANNING = "planning"       # 规划中
    ACTIVE = "active"         # 进行中
    PAUSED = "paused"         # 已暂停
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
```

## 10. 使用示例

### 基本使用

```python
import asyncio
from nanobot.agent.main_agent import MainAgent
from nanobot.config import Config

async def main():
    # 加载配置
    config = Config()
    
    # 创建主代理
    agent = MainAgent(config=config)
    
    # 处理用户消息
    response = await agent.process_message("计算两个数的和")
    print("响应:", response)
    
    # 获取系统状态
    status = await agent.get_status()
    print("系统状态:", status)

if __name__ == "__main__":
    asyncio.run(main())
```

### 任务规划示例

```python
import asyncio
from nanobot.agent.planner.task_planner import TaskPlanner

async def main():
    # 创建任务规划器
    planner = TaskPlanner()
    
    # 规划任务
    user_input = "实现一个图像识别系统"
    plan = await planner.plan_task(user_input)
    print("任务类型:", plan.task_type)
    print("优先级:", plan.priority)
    print("复杂度:", plan.complexity)
    print("执行步骤:", plan.steps)
    print("预计时间:", plan.estimated_time)

if __name__ == "__main__":
    asyncio.run(main())
```

### 上下文管理示例

```python
import asyncio
from nanobot.agent.context_manager import ContextManager

async def main():
    # 创建上下文管理器
    manager = ContextManager()
    
    # 构建任务上下文
    user_input = "编写Python函数"
    context = await manager.build_context(user_input, task_type="code_generation")
    print("任务上下文:", context)
    
    # 更新上下文
    task_id = "test-task-1"
    await manager.update_context(task_id, {"status": "running"})
    
    # 获取上下文
    retrieved_context = await manager.get_context(task_id)
    print("获取的上下文:", retrieved_context)

if __name__ == "__main__":
    asyncio.run(main())
```

## 8. 异常处理

Nanobot API 可能会抛出以下异常：

### 通用异常

```python
class NanobotException(Exception):
    """
    Nanobot 的基类异常。
    """
    pass

class ConfigurationError(NanobotException):
    """
    配置错误。
    """
    pass

class TaskNotFoundError(NanobotException):
    """
    任务未找到错误。
    """
    pass

class SubagentError(NanobotException):
    """
    子代理错误。
    """
    pass
```

### 异常处理示例

```python
import asyncio
from nanobot.agent.main_agent import MainAgent
from nanobot.exceptions import NanobotException, TaskNotFoundError

async def main():
    try:
        agent = MainAgent()
        response = await agent.process_message("执行任务")
        print("响应:", response)
    except TaskNotFoundError as e:
        print("任务未找到:", e)
    except NanobotException as e:
        print("Nanobot 错误:", e)
    except Exception as e:
        print("其他错误:", e)

if __name__ == "__main__":
    asyncio.run(main())
```

## 9. 配置选项

### 基本配置

```python
from nanobot.config import Config

# 加载默认配置
config = Config()

# 或者从文件加载
config = Config.from_file("config.yaml")

# 或者直接设置配置
config = Config(
    api_keys={"openai": "your-api-key"},
    max_context_tokens=8192,
    subagent_timeout=300,
)
```

### 高级配置

```python
config = Config(
    # API 密钥配置
    api_keys={
        "openai": "sk-xxxx",
        "anthropic": "sk-ant-xxxx",
    },
    
    # 上下文管理配置
    context_manager={
        "compression": {
            "strategy": "summarization",
            "max_tokens": 4096,
        },
        "expansion": {
            "max_skills": 10,
        },
    },
    
    # 任务规划配置
    task_planner={
        "complexity_threshold": 0.6,
        "timeout": 60,
    },
    
    # 子代理配置
    subagent_manager={
        "timeout": 300,
        "max_concurrent": 5,
    },
)
```
