"""
AgnoSubAgent - 基于 agno 框架的 SubAgent 实现

这是一个基于 agno 框架的 SubAgent 实现，提供以下功能：
- 集成 PromptSystemV2 - 动态提示词加载
- 继承 MainAgent 的工具包 - 文件系统、Web 搜索、Shell 等
- 支持任务管理 - 任务分配和进度汇报
- 父 Agent 通信 - 与 MainAgent 的消息传递
- 独立会话 - 每个 SubAgent 有独立的会话状态
- 钩子系统 - 前置/后置钩子
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Awaitable, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

# 导入现有组件
try:
    from agno import Agent, Function, Knowledge, Toolkit

    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    Agent = None
    Knowledge = None
    Toolkit = None
    Function = None

try:
    from nanobot.agent.prompt_system import PromptSystemV2, get_prompt_system_v2

    PROMPT_SYSTEM_V2_AVAILABLE = True
except ImportError:
    PROMPT_SYSTEM_V2_AVAILABLE = False
    PromptSystemV2 = None
    get_prompt_system_v2 = None

try:
    from nanobot.config.schema import NanobotConfig

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    NanobotConfig = None


class AgnoSubAgentConfig(BaseModel):
    """AgnoSubAgent 配置模型"""

    agent_id: str = Field(..., description="Agent 唯一标识")
    task_description: str = Field(..., description="任务描述")
    parent_agent_id: Optional[str] = Field(default=None, description="父 Agent ID")
    model: str = Field(default="openai/gpt-4o-mini", description="LLM 模型")
    workspace: Optional[Path] = Field(default=None, description="工作目录")
    max_iterations: int = Field(default=10, description="最大迭代次数")
    timeout: int = Field(default=240, description="超时时间（秒）")
    enable_memory: bool = Field(default=True, description="是否启用记忆系统")
    enable_knowledge: bool = Field(default=False, description="是否启用知识库")


class AgnoSubAgent:
    """
    基于 agno 框架的 SubAgent 实现

    这个类提供了一个基于 agno 框架的高层 Agent 抽象，集成了：
    - PromptSystemV2：用于动态提示词管理
    - 继承工具包系统：从 MainAgent 继承文件系统、Web 搜索、Shell 等工具
    - 任务管理：任务分配和进度汇报
    - 父 Agent 通信：与 MainAgent 的消息传递
    - 独立会话：每个 SubAgent 有独立的会话状态
    """

    def __init__(self, config: Optional[AgnoSubAgentConfig] = None, **kwargs):
        """
        初始化 AgnoSubAgent

        Args:
            config: AgnoSubAgentConfig 配置对象
            **kwargs: 配置参数（优先级高于 config）
        """
        if not AGNO_AVAILABLE:
            raise ImportError("agno 框架未安装。请先安装: pip install agno")

        # 合并配置
        if config is None:
            raise ValueError("必须提供配置对象")

        self.config = config.model_copy(update=kwargs)

        # 设置工作目录
        self.workspace = self.config.workspace or Path.cwd()

        # 初始化组件
        self.prompt_system = self._init_prompt_system()
        self.toolkits = self._create_toolkits()
        self.knowledge = (
            self._create_knowledge() if self.config.enable_knowledge else None
        )

        # 创建 agno Agent
        self.agent = self._create_agent()

        logger.info(f"AgnoSubAgent 初始化完成: {self.config.agent_id}")
        logger.debug(f"任务描述: {self.config.task_description}")
        if self.config.parent_agent_id:
            logger.debug(f"父 Agent: {self.config.parent_agent_id}")

    def _init_prompt_system(self) -> Optional[PromptSystemV2]:
        """初始化提示词系统"""
        if not PROMPT_SYSTEM_V2_AVAILABLE:
            logger.warning("PromptSystemV2 不可用，将使用默认提示词")
            return None

        try:
            return get_prompt_system_v2()
        except Exception as e:
            logger.warning(f"初始化 PromptSystemV2 失败: {e}")
            return None

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        if self.prompt_system is None:
            return self._get_default_prompt()

        try:
            return self.prompt_system.build_subagent_prompt(
                task=self.config.task_description, agent_id=self.config.agent_id
            )
        except Exception as e:
            logger.warning(f"获取 SubAgent 提示词失败: {e}，使用默认提示词")
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        prompt = f"""# SubAgent 系统提示词

## Agent 身份
你是一个专业的 AI 助手，你的唯一标识是：{self.config.agent_id}

## 核心任务
{self.config.task_description}

## 工作说明
你需要：
1. 专注于完成分配的任务
2. 如果遇到困难，及时向父 Agent 汇报
3. 保持与主任务的一致性
4. 使用提供的工具完成任务

## 工具使用
请根据任务需要使用工具，确保输入参数格式正确。
"""

        if self.config.parent_agent_id:
            prompt += (
                f"\n## 父 Agent 信息\n你的父 Agent 是：{self.config.parent_agent_id}"
            )

        return prompt

    def _create_toolkits(self) -> List[Toolkit]:
        """创建工具包列表（继承 MainAgent 的工具）"""
        toolkits = []

        # 文件系统工具包
        file_toolkit = self._create_filesystem_toolkit()
        if file_toolkit:
            toolkits.append(file_toolkit)

        # Web 工具包
        web_toolkit = self._create_web_toolkit()
        if web_toolkit:
            toolkits.append(web_toolkit)

        # Shell 工具包
        shell_toolkit = self._create_shell_toolkit()
        if shell_toolkit:
            toolkits.append(shell_toolkit)

        logger.info(f"创建了 {len(toolkits)} 个工具包")
        return toolkits

    def _create_filesystem_toolkit(self) -> Optional[Toolkit]:
        """创建文件系统工具包"""
        try:
            tools = []

            # read_file
            def read_file(path: str) -> str:
                """读取文件内容"""
                file_path = self.workspace / path
                if not file_path.exists():
                    return f"文件不存在: {path}"
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()

            tools.append(
                Function(name="read_file", description="读取文件内容", func=read_file)
            )

            # write_file
            def write_file(path: str, content: str) -> str:
                """写入文件内容"""
                file_path = self.workspace / path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"成功写入文件: {path}"

            tools.append(
                Function(name="write_file", description="写入文件内容", func=write_file)
            )

            # list_directory
            def list_directory(path: str = ".") -> str:
                """列出目录内容"""
                dir_path = self.workspace / path
                if not dir_path.exists():
                    return f"目录不存在: {path}"
                items = [item.name for item in dir_path.iterdir()]
                return "\n".join(items)

            tools.append(
                Function(
                    name="list_directory",
                    description="列出目录内容",
                    func=list_directory,
                )
            )

            # create_directory
            def create_directory(path: str) -> str:
                """创建目录"""
                dir_path = self.workspace / path
                dir_path.mkdir(parents=True, exist_ok=True)
                return f"成功创建目录: {path}"

            tools.append(
                Function(
                    name="create_directory",
                    description="创建目录",
                    func=create_directory,
                )
            )

            return Toolkit(
                name="filesystem", description="文件系统操作工具包", tools=tools
            )
        except Exception as e:
            logger.error(f"创建文件系统工具包失败: {e}")
            return None

    def _create_web_toolkit(self) -> Optional[Toolkit]:
        """创建 Web 工具包"""
        try:
            from nanobot.agent.tools.web import WebFetchTool, WebSearchTool

            tools = []

            # web_search - use real WebSearchTool
            search_tool = WebSearchTool()

            def web_search(query: str, count: int = 5) -> str:
                """搜索网络"""
                try:
                    import asyncio

                    # Run the async search tool
                    result = asyncio.run(search_tool.execute(query=query, count=count))
                    return result
                except Exception as e:
                    logger.error(f"Web search failed: {e}")
                    return f"搜索失败: {e}"

            tools.append(
                Function(
                    name="web_search",
                    description="搜索网络，使用 Brave Search API。需要 BRAVE_API_KEY 环境变量。",
                    func=web_search,
                )
            )

            # web_fetch - use real WebFetchTool
            fetch_tool = WebFetchTool()

            def web_fetch(url: str, extract_mode: str = "markdown") -> str:
                """获取网页内容"""
                try:
                    import asyncio

                    # Run the async fetch tool
                    result = asyncio.run(
                        fetch_tool.execute(url=url, extract_mode=extract_mode)
                    )
                    return result
                except Exception as e:
                    logger.error(f"Web fetch failed: {e}")
                    return f"获取网页失败: {e}"

            tools.append(
                Function(
                    name="web_fetch",
                    description="获取网页内容，转换为 markdown 或纯文本。",
                    func=web_fetch,
                )
            )

            return Toolkit(
                name="web",
                description="网络搜索和获取工具包（使用 Brave Search API）",
                tools=tools,
            )
        except Exception as e:
            logger.error(f"创建 Web 工具包失败: {e}")
            return None

    def _create_shell_toolkit(self) -> Optional[Toolkit]:
        """创建 Shell 工具包"""
        try:
            tools = []

            # execute_command
            def execute_command(command: str) -> str:
                """执行 Shell 命令"""
                import subprocess

                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        cwd=self.workspace,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode == 0:
                        return result.stdout or "命令执行成功"
                    else:
                        return f"命令执行失败: {result.stderr}"
                except subprocess.TimeoutExpired:
                    return "命令执行超时"
                except Exception as e:
                    return f"执行命令失败: {e}"

            tools.append(
                Function(
                    name="execute_command",
                    description="执行 Shell 命令",
                    func=execute_command,
                )
            )

            return Toolkit(
                name="shell", description="Shell 命令执行工具包", tools=tools
            )
        except Exception as e:
            logger.error(f"创建 Shell 工具包失败: {e}")
            return None

    def _create_knowledge(self) -> Optional[Knowledge]:
        """创建知识库（目前不实现）"""
        # TODO: 实现知识库集成
        return None

    def _create_agent(self) -> Agent:
        """创建 agno Agent"""
        system_prompt = self._get_system_prompt()

        agent = Agent(
            name=self.config.agent_id,
            model=self.config.model,
            instructions=system_prompt,
            toolkits=self.toolkits,
            knowledge=self.knowledge,
            memory=self.config.enable_memory,
        )

        logger.info(f"创建 agno Agent: {self.config.agent_id}")
        return agent

    def run(self, user_message: str) -> str:
        """
        同步运行 Agent

        Args:
            user_message: 用户消息

        Returns:
            Agent 的响应内容
        """
        logger.info(f"运行 SubAgent: {self.config.agent_id}")

        try:
            response = self.agent.run(user_message)
            result = response.content if hasattr(response, "content") else str(response)

            logger.info(f"SubAgent 响应: {result[:100]}...")
            return result
        except Exception as e:
            logger.error(f"运行 SubAgent 失败: {e}")
            raise

    async def run_async(self, user_message: str) -> str:
        """
        异步运行 Agent

        Args:
            user_message: 用户消息

        Returns:
            Agent 的响应内容
        """
        logger.info(f"异步运行 SubAgent: {self.config.agent_id}")

        try:
            response = await self.agent.arun(user_message)
            result = response.content if hasattr(response, "content") else str(response)

            logger.info(f"SubAgent 响应: {result[:100]}...")
            return result
        except Exception as e:
            logger.error(f"运行 SubAgent 失败: {e}")
            raise

    def reset(self) -> None:
        """重置 Agent 状态"""
        logger.info(f"重置 SubAgent: {self.config.agent_id}")
        # 重新创建 agent 以清除状态
        self.agent = self._create_agent()

    def get_config(self) -> AgnoSubAgentConfig:
        """获取配置"""
        return self.config

    def get_status(self) -> Dict[str, Any]:
        """获取 Agent 状态"""
        return {
            "agent_id": self.config.agent_id,
            "task_description": self.config.task_description,
            "parent_agent_id": self.config.parent_agent_id,
            "model": self.config.model,
            "workspace": str(self.workspace),
            "toolkits_count": len(self.toolkits),
            "knowledge_enabled": self.knowledge is not None,
            "prompt_system_enabled": self.prompt_system is not None,
            "memory_enabled": self.config.enable_memory,
            "max_iterations": self.config.max_iterations,
            "timeout": self.config.timeout,
        }

    def update_task_description(self, new_task_description: str) -> None:
        """
        更新任务描述

        Args:
            new_task_description: 新的任务描述
        """
        self.config.task_description = new_task_description
        # 重新创建 agent 以应用新的任务描述
        self.agent = self._create_agent()
        logger.info(f"SubAgent 任务描述已更新: {self.config.agent_id}")

    def send_message_to_parent(self, message: str) -> None:
        """
        向父 Agent 发送消息

        Args:
            message: 要发送的消息
        """
        if self.config.parent_agent_id:
            logger.info(f"发送消息到父 Agent {self.config.parent_agent_id}: {message}")
            # TODO: 实现实际的父 Agent 通信
        else:
            logger.warning("SubAgent 没有设置父 Agent，消息无法发送")

    def get_task_progress(self) -> Dict[str, Any]:
        """获取任务进度"""
        return {
            "agent_id": self.config.agent_id,
            "task_description": self.config.task_description,
            "status": "running",
            "progress": 0,
            "timestamp": asyncio.get_event_loop().time(),
        }


def create_agno_subagent(
    agent_id: str,
    task_description: str,
    parent_agent_id: Optional[str] = None,
    model: str = "openai/gpt-4o-mini",
    workspace: Optional[Path] = None,
    **kwargs,
) -> AgnoSubAgent:
    """
    创建 AgnoSubAgent 的便捷函数

    Args:
        agent_id: Agent 唯一标识
        task_description: 任务描述
        parent_agent_id: 父 Agent ID
        model: LLM 模型
        workspace: 工作目录
        **kwargs: 其他配置参数

    Returns:
        AgnoSubAgent 实例
    """
    config = AgnoSubAgentConfig(
        agent_id=agent_id,
        task_description=task_description,
        parent_agent_id=parent_agent_id,
        model=model,
        workspace=workspace,
        **kwargs,
    )
    return AgnoSubAgent(config=config)


# 兼容性：提供一个与现有 SubAgent 相似的接口
class SubAgent(AgnoSubAgent):
    """
    SubAgent 兼容层

    这个类保持与现有 SubAgent 的兼容性，内部使用 AgnoSubAgent 实现。
    """

    def __init__(
        self,
        name: str,
        task: str,
        parent_agent: Optional[Any] = None,
        model: str = "openai/gpt-4o-mini",
        workspace: Optional[Path] = None,
        **kwargs,
    ):
        """
        初始化 SubAgent（兼容性接口）

        Args:
            name: Agent 名称（兼容参数）
            task: 任务描述
            parent_agent: 父 Agent 实例（兼容参数）
            model: LLM 模型
            workspace: 工作目录
            **kwargs: 其他配置参数
        """
        parent_agent_id = None
        if parent_agent:
            # 尝试从父 Agent 实例中获取 ID
            if hasattr(parent_agent, "config") and hasattr(
                parent_agent.config, "agent_id"
            ):
                parent_agent_id = parent_agent.config.agent_id
            elif hasattr(parent_agent, "name"):
                parent_agent_id = parent_agent.name

        config = AgnoSubAgentConfig(
            agent_id=name,
            task_description=task,
            parent_agent_id=parent_agent_id,
            model=model,
            workspace=workspace,
            **kwargs,
        )
        super().__init__(config=config)


__all__ = [
    "AgnoSubAgent",
    "AgnoSubAgentConfig",
    "create_agno_subagent",
    "SubAgent",  # 兼容性导出
]
