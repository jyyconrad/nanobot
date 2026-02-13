"""
TaskManager 单元测试

测试任务管理器的核心功能，包括：
- CRUD 操作
- 任务状态转换
- 持久化功能
"""

import json
import os
import unittest
from datetime import datetime, timedelta

from nanobot.agent.task_manager import Task, TaskManager


class TestTaskManager(unittest.TestCase):
    """测试 TaskManager 类"""

    def setUp(self):
        """测试前准备：创建临时存储文件的任务管理器"""
        self.test_file = "test_tasks.json"
        self.manager = TaskManager(storage_file=self.test_file)
        self.manager.clear_all_tasks()

    def tearDown(self):
        """测试后清理：删除临时存储文件"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_create_task(self):
        """测试创建任务"""
        task = self.manager.create_task(
            title="测试任务", description="这是一个测试任务", priority=2
        )

        self.assertIsInstance(task, Task)
        self.assertEqual(task.title, "测试任务")
        self.assertEqual(task.description, "这是一个测试任务")
        self.assertEqual(task.priority, 2)
        self.assertEqual(task.status, "pending")
        self.assertIsNotNone(task.task_id)
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)
        self.assertIsNone(task.completed_at)
        self.assertIsNone(task.result)
        self.assertIsNone(task.error)

    def test_get_task(self):
        """测试获取任务"""
        task = self.manager.create_task(
            title="测试任务", description="这是一个测试任务"
        )

        retrieved_task = self.manager.get_task(task.task_id)
        self.assertIsNotNone(retrieved_task)
        self.assertEqual(retrieved_task.task_id, task.task_id)
        self.assertEqual(retrieved_task.title, task.title)

        # 测试获取不存在的任务
        non_existent_task = self.manager.get_task("non-existent-task-id")
        self.assertIsNone(non_existent_task)

    def test_update_task(self):
        """测试更新任务"""
        task = self.manager.create_task(
            title="原始任务", description="原始描述", priority=3
        )

        # 增加时间间隔以确保 updated_at 不同
        import time

        time.sleep(0.01)

        updated_task = self.manager.update_task(
            task_id=task.task_id,
            title="更新后的任务",
            description="更新后的描述",
            priority=4,
            status="running",
        )

        self.assertIsNotNone(updated_task)
        self.assertEqual(updated_task.title, "更新后的任务")
        self.assertEqual(updated_task.description, "更新后的描述")
        self.assertEqual(updated_task.priority, 4)
        self.assertEqual(updated_task.status, "running")
        # 比较时间差，确保更新后的时间晚于创建时间
        self.assertGreater(updated_task.updated_at, task.created_at)

    def test_task_status_transition(self):
        """测试任务状态转换"""
        task = self.manager.create_task(
            title="状态转换测试任务", description="测试任务状态转换"
        )

        # pending → running
        task = self.manager.update_task(task.task_id, status="running")
        self.assertEqual(task.status, "running")
        self.assertIsNone(task.completed_at)

        # running → completed
        task = self.manager.update_task(
            task.task_id, status="completed", result={"success": True}
        )
        self.assertEqual(task.status, "completed")
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.result, {"success": True})

        # 测试已完成任务不能再更新状态
        with self.assertRaises(ValueError):
            self.manager.update_task(task.task_id, status="running")

    def test_task_status_transition_with_error(self):
        """测试任务失败状态转换"""
        task = self.manager.create_task(
            title="失败状态测试任务", description="测试任务失败状态"
        )

        # pending → running
        task = self.manager.update_task(task.task_id, status="running")
        self.assertEqual(task.status, "running")

        # running → failed
        task = self.manager.update_task(
            task.task_id, status="failed", error="执行过程中发生错误"
        )
        self.assertEqual(task.status, "failed")
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.error, "执行过程中发生错误")

    def test_list_tasks(self):
        """测试列出任务"""
        # 创建多个任务
        task1 = self.manager.create_task(
            title="任务1", description="描述1", priority=1, status="pending"
        )
        task2 = self.manager.create_task(
            title="任务2", description="描述2", priority=3, status="running"
        )
        task3 = self.manager.create_task(
            title="任务3", description="描述3", priority=5, status="completed"
        )

        # 测试列出所有任务
        all_tasks = self.manager.list_tasks()
        self.assertEqual(len(all_tasks), 3)

        # 测试按状态筛选
        pending_tasks = self.manager.list_tasks(status="pending")
        self.assertEqual(len(pending_tasks), 1)
        self.assertEqual(pending_tasks[0].task_id, task1.task_id)

        running_tasks = self.manager.list_tasks(status="running")
        self.assertEqual(len(running_tasks), 1)
        self.assertEqual(running_tasks[0].task_id, task2.task_id)

        completed_tasks = self.manager.list_tasks(status="completed")
        self.assertEqual(len(completed_tasks), 1)
        self.assertEqual(completed_tasks[0].task_id, task3.task_id)

        # 测试按优先级筛选
        high_priority_tasks = self.manager.list_tasks(priority=5)
        self.assertEqual(len(high_priority_tasks), 1)
        self.assertEqual(high_priority_tasks[0].task_id, task3.task_id)

    def test_delete_task(self):
        """测试删除任务"""
        task = self.manager.create_task(
            title="待删除任务", description="这是一个要删除的任务"
        )

        self.assertEqual(self.manager.get_task_count(), 1)

        deleted = self.manager.delete_task(task.task_id)
        self.assertTrue(deleted)
        self.assertEqual(self.manager.get_task_count(), 0)
        self.assertIsNone(self.manager.get_task(task.task_id))

        # 测试删除不存在的任务
        not_deleted = self.manager.delete_task("non-existent-task-id")
        self.assertFalse(not_deleted)

    def test_persistence(self):
        """测试任务持久化"""
        # 创建任务
        task = self.manager.create_task(
            title="持久化测试任务", description="测试任务持久化功能", priority=4
        )

        # 创建新的任务管理器实例，加载相同的存储文件
        new_manager = TaskManager(storage_file=self.test_file)
        loaded_task = new_manager.get_task(task.task_id)

        self.assertIsNotNone(loaded_task)
        self.assertEqual(loaded_task.task_id, task.task_id)
        self.assertEqual(loaded_task.title, task.title)
        self.assertEqual(loaded_task.description, task.description)
        self.assertEqual(loaded_task.priority, task.priority)
        self.assertEqual(loaded_task.status, task.status)

    def test_task_count(self):
        """测试任务计数"""
        self.assertEqual(self.manager.get_task_count(), 0)

        self.manager.create_task(title="任务1", description="描述1")
        self.assertEqual(self.manager.get_task_count(), 1)

        self.manager.create_task(title="任务2", description="描述2")
        self.assertEqual(self.manager.get_task_count(), 2)

        # 按状态计数
        self.assertEqual(self.manager.get_task_count(status="pending"), 2)

    def test_clear_all_tasks(self):
        """测试清除所有任务"""
        self.manager.create_task(title="任务1", description="描述1")
        self.manager.create_task(title="任务2", description="描述2")
        self.manager.create_task(title="任务3", description="描述3")

        count = self.manager.clear_all_tasks()
        self.assertEqual(count, 3)
        self.assertEqual(self.manager.get_task_count(), 0)

    def test_invalid_status(self):
        """测试无效状态"""
        with self.assertRaises(ValueError):
            self.manager.create_task(
                title="无效状态任务",
                description="测试无效状态",
                status="invalid_status",
            )

    def test_invalid_priority(self):
        """测试无效优先级"""
        with self.assertRaises(ValueError):
            self.manager.create_task(
                title="无效优先级任务", description="测试无效优先级", priority=6
            )

        with self.assertRaises(ValueError):
            self.manager.create_task(
                title="无效优先级任务", description="测试无效优先级", priority=0
            )


if __name__ == "__main__":
    unittest.main()
