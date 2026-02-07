"""
任务管理器
============

任务管理和协调中心：
- 跟踪所有运行中的子代理任务
- 管理任务状态和进度
- 处理任务修正和重新执行
- 提供任务查询接口
"""

from typing import Dict, List, Optional

from nanobot.agent.task import Task, TaskStatus


class TaskManager:
    """
    任务管理器：负责任务的创建、查询、更新和管理

    这是一个单例模式的任务管理中心，跟踪所有任务的状态和生命周期。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tasks: Dict[str, Task] = {}
        return cls._instance

    def create_task(self, task: Task) -> str:
        """
        创建新任务

        Args:
            task: 任务对象

        Returns:
            任务ID
        """
        self._tasks[task.id] = task
        return task.id

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务对象

        Args:
            task_id: 任务ID

        Returns:
            任务对象，如果不存在则返回None
        """
        return self._tasks.get(task_id)

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """
        根据状态获取任务列表

        Args:
            status: 任务状态

        Returns:
            符合条件的任务列表
        """
        return [task for task in self._tasks.values() if task.status == status]

    def get_active_tasks(self) -> List[Task]:
        """
        获取所有活跃任务（待执行、执行中、暂停）

        Returns:
            活跃任务列表
        """
        active_statuses = [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.PAUSED]
        return [task for task in self._tasks.values() if task.status in active_statuses]

    def get_completed_tasks(self) -> List[Task]:
        """
        获取已完成任务

        Returns:
            已完成任务列表
        """
        return self.get_tasks_by_status(TaskStatus.COMPLETED)

    def get_failed_tasks(self) -> List[Task]:
        """
        获取失败任务

        Returns:
            失败任务列表
        """
        return self.get_tasks_by_status(TaskStatus.FAILED)

    def update_task(self, task_id: str, updates: Dict) -> Optional[Task]:
        """
        更新任务信息

        Args:
            task_id: 任务ID
            updates: 更新字段字典

        Returns:
            更新后的任务对象，如果任务不存在则返回None
        """
        task = self.get_task(task_id)
        if task:
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
        return task

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def get_all_tasks(self) -> List[Task]:
        """
        获取所有任务

        Returns:
            所有任务列表
        """
        return list(self._tasks.values())

    def get_task_count(self) -> int:
        """
        获取任务总数

        Returns:
            任务总数
        """
        return len(self._tasks)

    def get_task_count_by_status(self, status: TaskStatus) -> int:
        """
        获取指定状态的任务数量

        Args:
            status: 任务状态

        Returns:
            任务数量
        """
        return len(self.get_tasks_by_status(status))

    def clear_completed_tasks(self) -> int:
        """
        清除已完成的任务

        Returns:
            清除的任务数量
        """
        completed_tasks = self.get_completed_tasks()
        for task in completed_tasks:
            del self._tasks[task.id]
        return len(completed_tasks)

    def clear_all_tasks(self) -> int:
        """
        清除所有任务

        Returns:
            清除的任务数量
        """
        count = len(self._tasks)
        self._tasks.clear()
        return count

    def find_tasks_by_session(self, session_key: str) -> List[Task]:
        """
        根据会话密钥查找任务

        Args:
            session_key: 会话密钥

        Returns:
            符合条件的任务列表
        """
        return [task for task in self._tasks.values() if task.session_key == session_key]

    def find_tasks_by_channel(self, channel: str, chat_id: str) -> List[Task]:
        """
        根据渠道和聊天ID查找任务

        Args:
            channel: 消息渠道
            chat_id: 聊天ID

        Returns:
            符合条件的任务列表
        """
        return [
            task
            for task in self._tasks.values()
            if task.channel == channel and task.chat_id == chat_id
        ]

    def find_tasks_by_subagent(self, subagent_id: str) -> List[Task]:
        """
        根据子代理ID查找任务

        Args:
            subagent_id: 子代理ID

        Returns:
            符合条件的任务列表
        """
        return [task for task in self._tasks.values() if task.subagent_id == subagent_id]
