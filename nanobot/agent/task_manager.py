"""
TaskManager - 任务管理模块

该模块提供了任务的创建、查询、更新、删除和状态跟踪功能，
支持任务持久化存储和加载。
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from uuid import uuid4


# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


@dataclass
class Task:
    """
    任务数据模型

    表示一个任务的完整信息，包括标识符、标题、描述、状态、优先级、时间戳等。

    Attributes:
        task_id: 任务唯一标识符
        title: 任务标题
        description: 任务描述
        status: 任务状态 (pending, running, completed, failed)
        priority: 任务优先级 (1-5)
        created_at: 任务创建时间
        updated_at: 任务最后更新时间
        completed_at: 任务完成时间 (可选)
        result: 任务执行结果 (可选)
        error: 任务执行错误信息 (可选)
    """
    title: str
    description: str
    task_id: str = field(default_factory=lambda: str(uuid4()))
    status: str = "pending"
    priority: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        """初始化后验证任务属性"""
        self._validate_status()
        self._validate_priority()

    def _validate_status(self):
        """验证任务状态是否合法"""
        valid_statuses = ["pending", "running", "completed", "failed"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {valid_statuses}")

    def _validate_priority(self):
        """验证任务优先级是否合法"""
        if not (1 <= self.priority <= 5):
            raise ValueError(f"Priority must be between 1 and 5, got {self.priority}")

    def to_dict(self) -> Dict[str, Any]:
        """
        将任务对象转换为字典

        Returns:
            包含任务所有属性的字典
        """
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """
        从字典创建任务对象

        Args:
            data: 包含任务属性的字典

        Returns:
            任务对象
        """
        return cls(
            task_id=data["task_id"],
            title=data["title"],
            description=data["description"],
            status=data["status"],
            priority=data["priority"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            result=data.get("result"),
            error=data.get("error")
        )


class TaskManager:
    """
    任务管理器

    负责任务的创建、查询、更新、删除和持久化管理。
    """

    def __init__(self, storage_file: str = "tasks.json"):
        """
        初始化任务管理器

        Args:
            storage_file: 任务存储文件路径，默认为 tasks.json
        """
        self.storage_file = storage_file
        self.tasks: Dict[str, Task] = {}
        self._load_tasks()
        logger.info(f"TaskManager initialized with {len(self.tasks)} tasks loaded from {storage_file}")

    def _load_tasks(self):
        """从存储文件加载任务"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    tasks_data = json.load(f)
                    self.tasks = {
                        task_data["task_id"]: Task.from_dict(task_data)
                        for task_data in tasks_data
                    }
                logger.info(f"Successfully loaded {len(self.tasks)} tasks from {self.storage_file}")
            except Exception as e:
                logger.error(f"Failed to load tasks from {self.storage_file}: {e}")
                self.tasks = {}
        else:
            logger.info(f"Storage file {self.storage_file} does not exist. Starting with empty task list.")

    def _save_tasks(self):
        """保存任务到存储文件"""
        try:
            tasks_data = [task.to_dict() for task in self.tasks.values()]
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2, default=str)
            logger.debug(f"Successfully saved {len(self.tasks)} tasks to {self.storage_file}")
        except Exception as e:
            logger.error(f"Failed to save tasks to {self.storage_file}: {e}")

    def create_task(
        self,
        title: str,
        description: str,
        priority: int = 3,
        status: str = "pending"
    ) -> Task:
        """
        创建新任务

        Args:
            title: 任务标题
            description: 任务描述
            priority: 任务优先级 (1-5)，默认为 3
            status: 任务状态，默认为 pending

        Returns:
            创建的任务对象

        Raises:
            ValueError: 当状态或优先级不合法时
        """
        task = Task(
            title=title,
            description=description,
            priority=priority,
            status=status
        )
        self.tasks[task.task_id] = task
        self._save_tasks()
        logger.info(f"Task created: {task.task_id} - {task.title}")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        根据任务ID获取任务

        Args:
            task_id: 任务唯一标识符

        Returns:
            任务对象，或 None 表示未找到
        """
        task = self.tasks.get(task_id)
        if task:
            logger.debug(f"Task retrieved: {task_id} - {task.title}")
        else:
            logger.warning(f"Task not found: {task_id}")
        return task

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[Task]:
        """
        更新任务信息

        Args:
            task_id: 任务唯一标识符
            title: 新的任务标题 (可选)
            description: 新的任务描述 (可选)
            status: 新的任务状态 (可选)
            priority: 新的任务优先级 (可选)
            result: 任务执行结果 (可选)
            error: 任务执行错误信息 (可选)

        Returns:
            更新后的任务对象，或 None 表示未找到

        Raises:
            ValueError: 当状态或优先级不合法时
        """
        task = self.get_task(task_id)
        if not task:
            return None

        # 保存原始更新时间以便比较
        original_updated_at = task.updated_at

        if title:
            task.title = title
        if description:
            task.description = description
        if status:
            valid_statuses = ["pending", "running", "completed", "failed"]
            if status not in valid_statuses:
                raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
            # 状态转换逻辑
            if task.status == "pending" and status not in ["running", "completed", "failed"]:
                raise ValueError("Pending task can only transition to running, completed, or failed")
            if task.status == "running" and status not in ["completed", "failed"]:
                raise ValueError("Running task can only transition to completed or failed")
            if task.status == "completed" and status != "completed":
                raise ValueError("Completed task cannot be updated to other statuses")
            if task.status == "failed" and status != "failed":
                raise ValueError("Failed task cannot be updated to other statuses")

            task.status = status
            # 记录完成时间
            if status in ["completed", "failed"] and not task.completed_at:
                task.completed_at = datetime.now()
            elif status not in ["completed", "failed"] and task.completed_at:
                task.completed_at = None

        if priority:
            if not (1 <= priority <= 5):
                raise ValueError(f"Priority must be between 1 and 5, got {priority}")
            task.priority = priority

        if result:
            task.result = result

        if error:
            task.error = error

        # 确保更新时间比原始时间晚
        import time
        while task.updated_at <= original_updated_at:
            task.updated_at = datetime.now()
            time.sleep(0.001)

        self._save_tasks()
        logger.info(f"Task updated: {task_id} - {task.title} (status: {task.status})")
        return task

    def list_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Task]:
        """
        列出任务 (支持筛选)

        Args:
            status: 状态筛选条件 (可选)
            priority: 优先级筛选条件 (可选)
            start_date: 开始日期筛选条件 (可选)
            end_date: 结束日期筛选条件 (可选)

        Returns:
            符合条件的任务列表
        """
        filtered_tasks = list(self.tasks.values())

        if status:
            filtered_tasks = [task for task in filtered_tasks if task.status == status]

        if priority:
            filtered_tasks = [task for task in filtered_tasks if task.priority == priority]

        if start_date:
            filtered_tasks = [task for task in filtered_tasks if task.created_at >= start_date]

        if end_date:
            filtered_tasks = [task for task in filtered_tasks if task.created_at <= end_date]

        # 按创建时间降序排序
        filtered_tasks.sort(key=lambda x: x.created_at, reverse=True)

        logger.debug(f"Returning {len(filtered_tasks)} tasks after filtering")
        return filtered_tasks

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务唯一标识符

        Returns:
            删除成功返回 True，否则返回 False
        """
        if task_id in self.tasks:
            task_title = self.tasks[task_id].title
            del self.tasks[task_id]
            self._save_tasks()
            logger.info(f"Task deleted: {task_id} - {task_title}")
            return True
        else:
            logger.warning(f"Attempted to delete non-existent task: {task_id}")
            return False

    def get_task_count(self, status: Optional[str] = None) -> int:
        """
        获取任务数量

        Args:
            status: 状态筛选条件 (可选)

        Returns:
            任务数量
        """
        if status:
            return len([task for task in self.tasks.values() if task.status == status])
        return len(self.tasks)

    def clear_all_tasks(self) -> int:
        """
        清除所有任务

        Returns:
            清除的任务数量
        """
        count = len(self.tasks)
        self.tasks.clear()
        self._save_tasks()
        logger.info(f"All tasks cleared: {count} tasks deleted")
        return count
