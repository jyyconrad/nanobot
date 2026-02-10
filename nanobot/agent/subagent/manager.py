"""
SubagentManager - Subagent 管理类
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta

from nanobot.agent.subagent.agno_subagent import AgnoSubagent
from nanobot.agent.subagent.models import SubagentResult, SubagentState, SubagentTask
from nanobot.agent.task_manager import TaskManager
from nanobot.agent.task import Task, TaskStatus

logger = logging.getLogger(__name__)


class SubagentManager:
    """
    Subagent 管理器

    负责：
    - Subagent 的创建和销毁
    - Subagent 状态管理
    - Subagent 任务分配
    - Subagent 通信协调
    - 任务跟踪和进度汇报
    - 任务修正和重试机制
    - 与 TaskManager 集成
    """

    def __init__(self):
        self.subagents: Dict[str, AgnoSubagent] = {}
        self.tasks: Dict[str, SubagentTask] = {}
        self.results: Dict[str, SubagentResult] = {}
        self.states: Dict[str, SubagentState] = {}
        self._callback_map: Dict[str, callable] = {}
        # 任务修正请求存储
        self.correction_requests: Dict[str, Dict[str, Any]] = {}
        # 任务重试次数记录
        self.retry_counts: Dict[str, int] = {}
        # 任务创建时间和完成时间
        self.task_timestamps: Dict[str, Dict[str, datetime]] = {}
        # 集成 TaskManager
        self.task_manager = TaskManager()

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
        self.states[task_id] = SubagentState(
            task_id=task_id,
            status="ASSIGNED",
            progress=0.0,
            started_at=datetime.now()
        )
        
        # 记录任务时间戳
        self.task_timestamps[task_id] = {
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None
        }
        
        # 集成 TaskManager
        # 我们需要确保 TaskManager 使用与我们相同的 task_id
        import uuid
        from nanobot.agent.task_manager import Task
        
        # 创建任务时使用我们自己的 task_id
        task_obj = Task(
            title=task[:50] + ("..." if len(task) > 50 else ""),
            description=task,
            task_id=task_id,
            priority=1,
            status="pending"
        )
        self.task_manager.tasks[task_id] = task_obj
        self.task_manager._save_tasks()

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
            task_id=task.task_id,
            status="ASSIGNED",
            progress=0.0,
            started_at=datetime.now()
        )
        
        # 记录任务时间戳
        self.task_timestamps[task.task_id] = {
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None
        }
        
        # 集成 TaskManager
        from nanobot.agent.task_manager import Task
        
        task_obj = Task(
            title=task.description[:50] + ("..." if len(task.description) > 50 else ""),
            description=task.description,
            task_id=task.task_id,
            priority=task.priority,
            status="pending"
        )
        self.task_manager.tasks[task.task_id] = task_obj
        self.task_manager._save_tasks()

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
            # 更新启动时间
            start_time = datetime.now()
            self.task_timestamps[task_id]["started_at"] = start_time
            self.states[task_id].started_at = start_time
            
            # 更新状态为运行中
            self.states[task_id].status = "RUNNING"
            self.states[task_id].progress = 0.1
            
            # 同步到 TaskManager
            self.task_manager.update_task(
                task_id,
                status="running"
            )

            # 执行任务
            result = await subagent.execute()
            self.results[task_id] = result
            self.states[task_id] = result.state
            
            # 更新完成时间
            end_time = datetime.now()
            self.task_timestamps[task_id]["completed_at"] = end_time
            self.states[task_id].completed_at = end_time
            
            # 同步到 TaskManager
            task_status = "completed" if result.success else "failed"
            self.task_manager.update_task(
                task_id,
                status=task_status,
                result={"output": result.output} if result.success else None,
                error=result.error if not result.success else None
            )

            logger.info(f"SubagentManager Subagent 完成: {task_id}")

            # 调用回调函数
            if task_id in self._callback_map:
                await self._callback_map[task_id](result)

        except Exception as e:
            logger.error(f"SubagentManager Subagent 执行失败: {task_id} - {e}", exc_info=True)
            self.states[task_id].status = "FAILED"
            self.states[task_id].error = str(e)
            self.states[task_id].completed_at = datetime.now()
            
            # 同步到 TaskManager
            self.task_manager.update_task(
                task_id,
                status="failed",
                error=str(e)
            )

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

    async def report_progress(self, task_id: str, progress: float, current_step: str = "", estimated_time_remaining: Optional[timedelta] = None):
        """
        报告子代理任务进度

        Args:
            task_id: Subagent 任务 ID
            progress: 完成百分比 (0-100)
            current_step: 当前执行步骤描述
            estimated_time_remaining: 预计剩余时间

        Raises:
            ValueError: 如果任务不存在或进度值无效
        """
        if task_id not in self.states:
            raise ValueError(f"任务 {task_id} 不存在")
            
        if not (0.0 <= progress <= 100.0):
            raise ValueError("进度值必须在 0-100 范围内")
            
        # 更新状态
        self.states[task_id].progress = progress / 100.0  # 转换为 0-1 范围
        if current_step:
            self.states[task_id].current_step = current_step
            
        # 同步到 TaskManager
        self.task_manager.update_task(
            task_id,
            status="running"
        )
        
        logger.debug(f"SubagentManager 任务进度更新: {task_id} - {progress}%, 当前步骤: {current_step}")

    async def get_progress(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务进度信息

        Args:
            task_id: Subagent 任务 ID

        Returns:
            进度信息字典，包含:
            - progress: 完成百分比 (0-100)
            - current_step: 当前执行步骤
            - estimated_time_remaining: 预计剩余时间
            - status: 任务状态
            - started_at: 开始时间
            - completed_at: 完成时间
            - execution_time: 已执行时间

        Raises:
            ValueError: 如果任务不存在
        """
        if task_id not in self.states:
            raise ValueError(f"任务 {task_id} 不存在")
            
        state = self.states[task_id]
        timestamps = self.task_timestamps.get(task_id, {})
        
        # 计算执行时间和预计剩余时间
        execution_time = None
        estimated_time_remaining = None
        if timestamps.get("started_at"):
            execution_time = datetime.now() - timestamps["started_at"]
            if state.progress > 0:
                total_estimated_time = execution_time / state.progress
                estimated_time_remaining = total_estimated_time - execution_time
                
        return {
            "progress": state.progress * 100,  # 转换为百分比
            "current_step": state.current_step,
            "estimated_time_remaining": estimated_time_remaining,
            "status": state.status,
            "started_at": timestamps.get("started_at"),
            "completed_at": state.completed_at,
            "execution_time": execution_time
        }

    async def request_correction(self, task_id: str, issue: str, details: str = "") -> str:
        """
        请求任务修正

        Args:
            task_id: Subagent 任务 ID
            issue: 问题描述
            details: 详细信息

        Returns:
            修正请求 ID

        Raises:
            ValueError: 如果任务不存在
        """
        if task_id not in self.states:
            raise ValueError(f"任务 {task_id} 不存在")
            
        correction_id = f"correction-{task_id}-{len(self.correction_requests.get(task_id, [])) + 1}"
        
        if task_id not in self.correction_requests:
            self.correction_requests[task_id] = []
            
        self.correction_requests[task_id].append({
            "correction_id": correction_id,
            "issue": issue,
            "details": details,
            "requested_at": datetime.now(),
            "status": "pending"
        })
        
        logger.warning(f"SubagentManager 任务修正请求: {task_id} - {correction_id}: {issue}")
        
        return correction_id

    async def provide_correction(self, task_id: str, correction_id: str, guidance: str) -> bool:
        """
        提供任务修正指导

        Args:
            task_id: Subagent 任务 ID
            correction_id: 修正请求 ID
            guidance: 修正指导内容

        Returns:
            是否成功提供修正

        Raises:
            ValueError: 如果任务不存在
        """
        if task_id not in self.correction_requests:
            raise ValueError(f"任务 {task_id} 不存在修正请求")
            
        for request in self.correction_requests[task_id]:
            if request["correction_id"] == correction_id:
                request["guidance"] = guidance
                request["provided_at"] = datetime.now()
                request["status"] = "provided"
                logger.info(f"SubagentManager 修正指导已提供: {task_id} - {correction_id}")
                return True
                
        raise ValueError(f"修正请求 {correction_id} 不存在")

    async def retry_task(self, task_id: str, new_task: Optional[SubagentTask] = None) -> str:
        """
        重试任务

        Args:
            task_id: 原任务 ID
            new_task: 新任务描述（可选，如不提供则使用原任务）

        Returns:
            新任务 ID

        Raises:
            ValueError: 如果任务不存在
        """
        if task_id not in self.tasks:
            raise ValueError(f"任务 {task_id} 不存在")
            
        # 增加重试计数
        self.retry_counts[task_id] = self.retry_counts.get(task_id, 0) + 1
        
        # 使用原任务或新任务
        if new_task is None:
            original_task = self.tasks[task_id]
            new_task = SubagentTask(
                task_id=f"{task_id}-retry-{self.retry_counts[task_id]}",
                description=original_task.description,
                config=original_task.config,
                agent_type=original_task.agent_type,
                skills=original_task.skills,
                priority=original_task.priority,
                deadline=original_task.deadline
            )
            
        logger.info(f"SubagentManager 任务重试: {task_id} -> {new_task.task_id}")
        
        # 生成新的 Subagent
        return await self.spawn_subagent(new_task)

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

    async def get_correction_requests(self, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取任务修正请求

        Args:
            task_id: 任务 ID（可选，如不提供则返回所有）

        Returns:
            修正请求列表
        """
        if task_id:
            return self.correction_requests.get(task_id, [])
        else:
            all_requests = []
            for task_requests in self.correction_requests.values():
                all_requests.extend(task_requests)
            return all_requests

    async def get_retry_count(self, task_id: str) -> int:
        """
        获取任务重试次数

        Args:
            task_id: 任务 ID

        Returns:
            重试次数

        Raises:
            ValueError: 如果任务不存在
        """
        if task_id not in self.tasks:
            raise ValueError(f"任务 {task_id} 不存在")
            
        return self.retry_counts.get(task_id, 0)

    async def get_task_timeline(self, task_id: str) -> Dict[str, Optional[datetime]]:
        """
        获取任务时间线

        Args:
            task_id: 任务 ID

        Returns:
            时间线字典，包含创建时间、开始时间和完成时间

        Raises:
            ValueError: 如果任务不存在
        """
        if task_id not in self.task_timestamps:
            raise ValueError(f"任务 {task_id} 不存在")
            
        return self.task_timestamps[task_id]

    async def get_task_result(self, task_id: str) -> Optional[SubagentResult]:
        """
        获取任务结果

        Args:
            task_id: 任务 ID

        Returns:
            任务结果，或 None 表示未完成
        """
        return self.results.get(task_id)

    async def sync_with_task_manager(self) -> None:
        """
        同步任务状态到 TaskManager

        确保 SubagentManager 和 TaskManager 的任务状态一致
        """
        for task_id, state in self.states.items():
            # 获取或创建任务
            task = self.task_manager.get_task(task_id)
            if task is None:
                subagent_task = self.tasks.get(task_id)
                if subagent_task:
                    from nanobot.agent.task_manager import Task
                    task_obj = Task(
                        title=subagent_task.description[:50] + ("..." if len(subagent_task.description) > 50 else ""),
                        description=subagent_task.description,
                        task_id=task_id,
                        priority=subagent_task.priority,
                        status="pending"
                    )
                    self.task_manager.tasks[task_id] = task_obj
                    self.task_manager._save_tasks()
            
            # 同步状态
            if task:
                task_status = {
                    "ASSIGNED": "pending",
                    "RUNNING": "running",
                    "COMPLETED": "completed",
                    "FAILED": "failed",
                    "CANCELLED": "cancelled",
                    "PENDING": "pending"
                }.get(state.status, "pending")
                
                # 避免 TaskManager 的状态转换限制
                try:
                    self.task_manager.update_task(
                        task_id,
                        status=task_status
                    )
                except ValueError as e:
                    logger.warning(f"无法同步任务状态 {task_id}: {e}")

        logger.debug("SubagentManager 已同步任务状态到 TaskManager")

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
        if task_id in self.correction_requests:
            del self.correction_requests[task_id]
        if task_id in self.retry_counts:
            del self.retry_counts[task_id]
        if task_id in self.task_timestamps:
            del self.task_timestamps[task_id]
        # 同时从 TaskManager 中删除
        self.task_manager.delete_task(task_id)

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
