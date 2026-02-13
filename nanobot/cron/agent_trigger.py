"""
Agent 触发器
============

触发指定 Agent 的方法执行
"""

from typing import Any, Dict, Optional

from loguru import logger

from nanobot.agent.loop import AgentLoop
from nanobot.bus.events import InboundMessage
from nanobot.bus.queue import MessageBus


class AgentTrigger:
    """
    Agent 触发器：负责触发指定 Agent 的方法执行

    支持触发 mainAgent 或任意 subagent 的方法，用于实现定时任务的执行。
    """

    def __init__(
        self, agent_loop: Optional[AgentLoop] = None, bus: Optional[MessageBus] = None
    ):
        self._agent_loop = agent_loop
        self._bus = bus

    async def trigger_agent(
        self, target: str, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        触发指定 Agent 的方法执行

        Args:
            target: 目标 Agent 名称（如 "mainAgent" 或具体的 subagent ID）
            method: 要执行的方法名称
            params: 方法参数

        Returns:
            方法执行结果

        Raises:
            ValueError: 无效的目标或方法
            Exception: 执行过程中发生的错误
        """
        if params is None:
            params = {}

        logger.info(f"Triggering agent: {target}.{method} with params: {params}")

        if target == "mainAgent":
            return await self._trigger_main_agent(method, params)
        elif target.startswith("subagent:"):
            subagent_id = target.split(":", 1)[1]
            return await self._trigger_subagent(subagent_id, method, params)
        else:
            # 尝试直接通过 subagent ID 查找
            return await self._trigger_subagent(target, method, params)

    async def _trigger_main_agent(self, method: str, params: Dict[str, Any]) -> Any:
        """
        触发 mainAgent 的方法执行

        Args:
            method: 方法名称
            params: 方法参数

        Returns:
            方法执行结果
        """
        if not self._agent_loop:
            raise ValueError("AgentLoop not available for mainAgent triggering")

        # 根据方法名称执行相应操作
        if method == "check_status":
            return await self._check_main_agent_status(params)
        elif method == "run_task":
            return await self._run_task(params)
        elif method == "get_progress":
            return await self._get_progress(params)
        elif method == "cleanup":
            return await self._cleanup_tasks(params)
        elif method == "health_check":
            return await self._health_check(params)
        else:
            raise ValueError(f"Unknown method for mainAgent: {method}")

    async def _trigger_subagent(
        self, subagent_id: str, method: str, params: Dict[str, Any]
    ) -> Any:
        """
        触发子代理的方法执行

        Args:
            subagent_id: 子代理ID
            method: 方法名称
            params: 方法参数

        Returns:
            方法执行结果
        """
        logger.warning(
            f"Subagent triggering not fully implemented yet: {subagent_id}.{method}"
        )
        # 目前只支持基本的状态检查
        if method == "check_status":
            return {
                "status": (
                    "running"
                    if subagent_id in self._agent_loop.subagents._running_tasks
                    else "stopped"
                ),
                "id": subagent_id,
            }
        else:
            raise ValueError(f"Unknown method for subagent {subagent_id}: {method}")

    async def _check_main_agent_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """检查 mainAgent 状态"""
        return {
            "status": "running",
            "tasks": {
                "active": len(
                    self._agent_loop.bus.get_task_manager().get_active_tasks()
                ),
                "completed": len(
                    self._agent_loop.bus.get_task_manager().get_completed_tasks()
                ),
                "failed": len(
                    self._agent_loop.bus.get_task_manager().get_failed_tasks()
                ),
            },
            "subagents": self._agent_loop.subagents.get_running_count(),
            "message_bus": {
                "inbound": self._agent_loop.bus.inbound_size,
                "outbound": self._agent_loop.bus.outbound_size,
            },
        }

    async def _run_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """运行任务"""
        if "task" not in params:
            raise ValueError("Task description required")

        try:
            # 创建系统消息触发任务执行
            msg = InboundMessage(
                channel="system",
                sender_id="cron",
                chat_id="system:direct",
                content=f"[Cron Task] {params['task']}",
            )

            await self._bus.publish_inbound(msg)
            return {"success": True, "message": "Task submitted"}

        except Exception as e:
            logger.error(f"Failed to run task: {e}")
            return {"success": False, "error": str(e)}

    async def _get_progress(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取任务进度"""
        task_id = params.get("task_id")

        if task_id:
            task = self._agent_loop.bus.get_task_manager().get_task(task_id)
            if task:
                return task.to_dict()
            else:
                return {"error": f"Task {task_id} not found"}

        # 获取所有任务进度
        tasks = self._agent_loop.bus.get_task_manager().get_all_tasks()
        return {"total": len(tasks), "tasks": [task.to_dict() for task in tasks]}

    async def _cleanup_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """清理任务"""
        # 清除已完成任务
        count = self._agent_loop.bus.get_task_manager().clear_completed_tasks()
        logger.info(f"Cleaned up {count} completed tasks")
        return {"success": True, "cleaned_count": count}

    async def _health_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """健康检查"""
        status = await self._check_main_agent_status(params)

        # 简单的健康评估
        is_healthy = (
            status["status"] == "running"
            and status["tasks"]["failed"] < 5
            and status["subagents"] < 20
            and status["message_bus"]["inbound"] < 100
        )

        status["health"] = "healthy" if is_healthy else "unhealthy"
        return status

    async def trigger_subagent(
        self, subagent_id: str, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        触发子代理的方法执行（别名方法）

        Args:
            subagent_id: 子代理ID
            method: 方法名称
            params: 方法参数

        Returns:
            方法执行结果
        """
        return await self._trigger_subagent(subagent_id, method, params)
