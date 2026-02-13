"""
SubagentManager 增强功能测试
=============================

测试任务跟踪、进度汇报和任务修正功能。
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from nanobot.agent.subagent.manager import SubagentManager
from nanobot.agent.subagent.models import SubagentState, SubagentStatus, SubagentTask
from nanobot.agent.task import TaskStatus
from nanobot.agent.task_manager import TaskManager


class TestSubagentManagerEnhanced:
    """测试 SubagentManager 增强功能"""

    @pytest.fixture
    async def manager(self):
        """创建 SubagentManager 实例"""
        return SubagentManager()

    @pytest.mark.asyncio
    async def test_task_tracking(self, manager: SubagentManager):
        """测试任务跟踪功能"""
        # 创建任务
        task_id = manager.create_subagent("测试任务")

        # 验证任务创建
        assert task_id in manager.tasks
        assert task_id in manager.states
        assert task_id in manager.task_timestamps
        assert manager.task_timestamps[task_id]["created_at"] is not None
        assert manager.task_timestamps[task_id]["started_at"] is None
        assert manager.task_timestamps[task_id]["completed_at"] is None

        # 验证状态
        state = manager.states[task_id]
        assert state.status == SubagentStatus.ASSIGNED
        assert state.progress == 0.0
        assert state.started_at is not None
        assert state.completed_at is None

        # 验证与 TaskManager 集成
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        assert task is not None
        assert task.task_id == task_id
        assert task.status == "pending"

    @pytest.mark.asyncio
    async def test_progress_reporting(self, manager: SubagentManager):
        """测试进度汇报功能"""
        # 创建任务
        task_id = manager.create_subagent("进度测试任务")

        # 报告进度
        await manager.report_progress(
            task_id,
            progress=30,
            current_step="数据采集",
            estimated_time_remaining=timedelta(minutes=10),
        )

        # 验证进度更新
        state = manager.states[task_id]
        assert state.progress == 0.3  # 内部存储为 0-1 范围
        assert state.current_step == "数据采集"

        # 验证通过 get_progress() 获取
        progress_info = await manager.get_progress(task_id)
        assert progress_info["progress"] == 30
        assert progress_info["current_step"] == "数据采集"
        # 第一次报告进度时，由于还没有执行时间，所以 estimated_time_remaining 可能是 None
        if progress_info["estimated_time_remaining"]:
            assert isinstance(progress_info["estimated_time_remaining"], timedelta)

        # 验证 TaskManager 同步
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        assert task is not None
        assert task.status == "running"

    @pytest.mark.asyncio
    async def test_correction_requests(self, manager: SubagentManager):
        """测试任务修正请求"""
        # 创建任务
        task_id = manager.create_subagent("需要修正的任务")

        # 请求修正
        correction_id = await manager.request_correction(
            task_id, issue="输出格式不正确", details="应该返回 JSON 格式而不是纯文本"
        )

        # 验证修正请求创建
        correction_requests = await manager.get_correction_requests(task_id)
        assert len(correction_requests) == 1
        assert correction_requests[0]["correction_id"] == correction_id
        assert correction_requests[0]["issue"] == "输出格式不正确"
        assert correction_requests[0]["status"] == "pending"

        # 提供修正指导
        await manager.provide_correction(
            task_id, correction_id, guidance="请使用 json.dumps() 格式化输出结果"
        )

        # 验证修正指导已提供
        correction_requests = await manager.get_correction_requests(task_id)
        assert correction_requests[0]["status"] == "provided"
        assert (
            correction_requests[0]["guidance"] == "请使用 json.dumps() 格式化输出结果"
        )
        assert correction_requests[0]["provided_at"] is not None

    @pytest.mark.asyncio
    async def test_task_retry(self, manager: SubagentManager):
        """测试任务重试功能"""
        # 创建原任务
        original_task_id = manager.create_subagent("原始任务")

        # 第一次重试
        retry1_task_id = await manager.retry_task(original_task_id)

        # 验证重试计数
        retry_count = await manager.get_retry_count(original_task_id)
        assert retry_count == 1

        # 验证新任务创建
        assert retry1_task_id in manager.tasks
        assert retry1_task_id != original_task_id
        assert "retry-1" in retry1_task_id

        # 第二次重试
        retry2_task_id = await manager.retry_task(original_task_id)
        retry_count = await manager.get_retry_count(original_task_id)
        assert retry_count == 2
        assert "retry-2" in retry2_task_id

    @pytest.mark.asyncio
    async def test_task_timeline(self, manager: SubagentManager):
        """测试任务时间线"""
        # 创建任务
        task_id = manager.create_subagent("时间线测试任务")

        # 获取时间线
        timeline = await manager.get_task_timeline(task_id)
        assert isinstance(timeline["created_at"], datetime)
        assert timeline["started_at"] is None
        assert timeline["completed_at"] is None

    @pytest.mark.asyncio
    async def test_sync_with_task_manager(self, manager: SubagentManager):
        """测试与 TaskManager 同步"""
        # 创建任务
        task_id = manager.create_subagent("同步测试任务")

        # 更新状态
        await manager.report_progress(task_id, 50, "处理中")

        # 手动同步
        await manager.sync_with_task_manager()

        # 验证同步结果
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        assert task is not None

    @pytest.mark.asyncio
    async def test_cleanup_task(self, manager: SubagentManager):
        """测试任务清理"""
        # 创建任务
        task_id = manager.create_subagent("清理测试任务")

        # 验证任务存在
        assert task_id in manager.tasks

        # 清理任务
        await manager.cleanup_subagent(task_id)

        # 验证任务已删除
        assert task_id not in manager.tasks
        assert task_id not in manager.states
        assert task_id not in manager.task_timestamps

        # 验证 TaskManager 中的任务也已删除
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        assert task is None

    @pytest.mark.asyncio
    async def test_get_completed_tasks(self, manager: SubagentManager):
        """测试获取已完成任务"""
        # 创建任务
        task_id1 = manager.create_subagent("任务1")
        task_id2 = manager.create_subagent("任务2")

        # 标记任务1为完成
        manager.states[task_id1].status = SubagentStatus.COMPLETED
        manager.states[task_id1].completed_at = datetime.now()

        # 获取已完成任务
        completed_tasks = await manager.get_completed_tasks()
        assert len(completed_tasks) == 1
        assert completed_tasks[0].task_id == task_id1

    @pytest.mark.asyncio
    async def test_error_handling_invalid_progress(self, manager: SubagentManager):
        """测试无效进度值的错误处理"""
        # 创建任务
        task_id = manager.create_subagent("错误处理测试任务")

        # 测试无效进度值
        with pytest.raises(ValueError):
            await manager.report_progress(task_id, -10)

        with pytest.raises(ValueError):
            await manager.report_progress(task_id, 110)

    @pytest.mark.asyncio
    async def test_error_handling_nonexistent_task(self, manager: SubagentManager):
        """测试对不存在任务的错误处理"""
        non_existent_task_id = "nonexistent-task"

        with pytest.raises(ValueError):
            await manager.report_progress(non_existent_task_id, 50)

        with pytest.raises(ValueError):
            await manager.get_progress(non_existent_task_id)

        with pytest.raises(ValueError):
            await manager.request_correction(non_existent_task_id, "问题")

        with pytest.raises(ValueError):
            await manager.retry_task(non_existent_task_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
