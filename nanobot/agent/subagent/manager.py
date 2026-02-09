"""
SubagentManager - Subagent 管理类
"""

import logging
from typing import Dict, List, Optional

from nanobot.agent.subagent.agno_subagent import AgnoSubagent
from nanobot.agent.subagent.models import SubagentResult, SubagentState, SubagentTask

logger = logging.getLogger(__name__)


class SubagentManager:
    """
    Subagent 管理器

    负责：
    - Subagent 的创建和销毁
    - Subagent 状态管理
    - Subagent 任务分配
    - Subagent 通信协调
    """

    def __init__(self):
        self.subagents: Dict[str, AgnoSubagent] = {}
        self.tasks: Dict[str, SubagentTask] = {}
        self.results: Dict[str, SubagentResult] = {}
        self.states: Dict[str, SubagentState] = {}
        self._callback_map: Dict[str, callable] = {}

    def create_subagent(self, task: str) -> str:
        """
        创建一个新的 Subagent（同步接口，用于测试）

        Args:
            task: 任务描述

        Returns:
            Subagent 实例 ID
        """
        from nanobot.agent.subagent.models import SubagentTask

        # 生成简单的任务 ID
        task_id = f"test-task-{len(self.subagents) + 1}"
        subagent_task = SubagentTask(task_id=task_id, description=task)

        logger.info(f"SubagentManager 创建 Subagent: {task_id}")

        # 创建 Subagent 实例（AgnoSubagent 是数据模型，直接创建）
        subagent = AgnoSubagent(
            subagent_id=task_id,
            task_id=task_id,
            task=task,
            label=task[:30] + ("..." if len(task) > 30 else ""),
        )

        # 保存到管理状态
        self.subagents[task_id] = subagent
        self.tasks[task_id] = subagent_task
        self.states[task_id] = SubagentState(task_id=task_id, status="ASSIGNED", progress=0.0)

        return task_id

    async def spawn_subagent(self, task: SubagentTask) -> str:
        """
        生成一个新的 Subagent

        Args:
            task: Subagent 任务描述

        Returns:
            Subagent 实例 ID
        """
        logger.info(f"SubagentManager 生成 Subagent: {task.task_id}")

        # 创建 Subagent 实例
        subagent = AgnoSubagent(
            subagent_id=task.task_id,
            task_id=task.task_id,
            task=task.description,
            label=task.description[:30] + ("..." if len(task.description) > 30 else ""),
        )

        # 保存到管理状态
        self.subagents[task.task_id] = subagent
        self.tasks[task.task_id] = task
        self.states[task.task_id] = SubagentState(
            task_id=task.task_id, status="ASSIGNED", progress=0.0
        )

        # 启动 Subagent 执行
        await self._start_subagent(task.task_id)

        return task.task_id

    async def _start_subagent(self, task_id: str):
        """启动 Subagent 执行"""
        subagent = self.subagents.get(task_id)
        if not subagent:
            logger.error(f"SubagentManager 找不到 Subagent: {task_id}")
            return

        try:
            # 更新状态为运行中
            self.states[task_id].status = "RUNNING"
            self.states[task_id].progress = 0.1

            # 执行任务
            result = await subagent.execute()
            self.results[task_id] = result
            self.states[task_id] = result.state

            logger.info(f"SubagentManager Subagent 完成: {task_id}")

            # 调用回调函数
            if task_id in self._callback_map:
                await self._callback_map[task_id](result)

        except Exception as e:
            logger.error(f"SubagentManager Subagent 执行失败: {task_id} - {e}", exc_info=True)
            self.states[task_id].status = "FAILED"
            self.states[task_id].error = str(e)

    async def get_subagent_status(self, task_id: str) -> Optional[SubagentState]:
        """
        获取 Subagent 状态

        Args:
            task_id: Subagent 任务 ID

        Returns:
            Subagent 状态，或 None 表示找不到
        """
        return self.states.get(task_id)

    async def get_all_statuses(self) -> List[SubagentState]:
        """获取所有 Subagent 状态"""
        return list(self.states.values())

    async def cancel_subagent(self, task_id: str) -> bool:
        """
        取消 Subagent 执行

        Args:
            task_id: Subagent 任务 ID

        Returns:
            是否成功取消
        """
        logger.info(f"SubagentManager 取消 Subagent: {task_id}")

        subagent = self.subagents.get(task_id)
        if not subagent:
            logger.warning(f"SubagentManager 找不到要取消的 Subagent: {task_id}")
            return False

        try:
            await subagent.cancel()
            self.states[task_id].status = "CANCELLED"
            logger.info(f"SubagentManager Subagent 已取消: {task_id}")
            return True

        except Exception as e:
            logger.error(f"SubagentManager 取消 Subagent 失败: {task_id} - {e}", exc_info=True)
            return False

    async def interrupt_subagent(self, task_id: str, message: str) -> bool:
        """
        中断 Subagent 执行并发送新消息

        Args:
            task_id: Subagent 任务 ID
            message: 中断消息

        Returns:
            是否成功中断
        """
        logger.info(f"SubagentManager 中断 Subagent: {task_id}")

        subagent = self.subagents.get(task_id)
        if not subagent:
            logger.warning(f"SubagentManager 找不到要中断的 Subagent: {task_id}")
            return False

        try:
            await subagent.interrupt(message)
            logger.info(f"SubagentManager Subagent 已中断: {task_id}")
            return True

        except Exception as e:
            logger.error(f"SubagentManager 中断 Subagent 失败: {task_id} - {e}", exc_info=True)
            return False

    async def register_callback(self, task_id: str, callback: callable):
        """
        注册 Subagent 结果回调

        Args:
            task_id: Subagent 任务 ID
            callback: 回调函数
        """
        self._callback_map[task_id] = callback

    async def unregister_callback(self, task_id: str):
        """
        取消注册 Subagent 结果回调

        Args:
            task_id: Subagent 任务 ID
        """
        if task_id in self._callback_map:
            del self._callback_map[task_id]

    async def cleanup_subagent(self, task_id: str):
        """
        清理 Subagent 资源

        Args:
            task_id: Subagent 任务 ID
        """
        if task_id in self.subagents:
            del self.subagents[task_id]
        if task_id in self.tasks:
            del self.tasks[task_id]
        if task_id in self.results:
            del self.results[task_id]
        if task_id in self.states:
            del self.states[task_id]
        if task_id in self._callback_map:
            del self._callback_map[task_id]

        logger.debug(f"SubagentManager 已清理 Subagent: {task_id}")

    async def cleanup_all(self):
        """清理所有 Subagent 资源"""
        task_ids = list(self.subagents.keys())
        for task_id in task_ids:
            await self.cleanup_subagent(task_id)

        logger.debug("SubagentManager 已清理所有 Subagent 资源")

    async def get_running_tasks(self) -> List[SubagentTask]:
        """获取所有正在运行的任务"""
        running = []
        for task_id, state in self.states.items():
            if state.status in ["ASSIGNED", "RUNNING"]:
                task = self.tasks.get(task_id)
                if task:
                    running.append(task)
        return running

    async def get_completed_tasks(self) -> List[SubagentTask]:
        """获取所有已完成的任务"""
        completed = []
        for task_id, state in self.states.items():
            if state.status == "COMPLETED":
                task = self.tasks.get(task_id)
                if task:
                    completed.append(task)
        return completed

    async def get_failed_tasks(self) -> List[SubagentTask]:
        """获取所有失败的任务"""
        failed = []
        for task_id, state in self.states.items():
            if state.status == "FAILED":
                task = self.tasks.get(task_id)
                if task:
                    failed.append(task)
        return failed

    async def get_cancelled_tasks(self) -> List[SubagentTask]:
        """获取所有已取消的任务"""
        cancelled = []
        for task_id, state in self.states.items():
            if state.status == "CANCELLED":
                task = self.tasks.get(task_id)
                if task:
                    cancelled.append(task)
        return cancelled
