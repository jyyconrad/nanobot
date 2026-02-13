"""
进度跟踪器
============

任务进度跟踪：
- 监控子代理执行状态
- 收集过程信息
- 提供进度查询接口
"""

from datetime import datetime
from typing import Dict, List, Optional

from loguru import logger

from nanobot.agent.task import Task, TaskStatus
from nanobot.agent.task_manager import TaskManager


class ProgressTracker:
    """
    任务进度跟踪器：监控任务执行进度和状态

    主要功能：
    - 实时监控任务进度
    - 收集任务执行过程信息
    - 提供进度查询接口
    - 生成进度报告
    """

    def __init__(self, task_manager: Optional[TaskManager] = None):
        self._task_manager = task_manager or TaskManager()
        self._progress_history: Dict[str, List[Dict]] = {}

    def track_progress(self, task_id: str, progress: float, message: str = ""):
        """
        跟踪任务进度

        Args:
            task_id: 任务ID
            progress: 进度值（0-100）
            message: 进度消息
        """
        if task_id not in self._progress_history:
            self._progress_history[task_id] = []

        self._progress_history[task_id].append(
            {
                "timestamp": datetime.now().isoformat(),
                "progress": progress,
                "message": message,
            }
        )

        logger.debug(f"Task {task_id} progress: {progress:.1f}% - {message}")

    def get_task_progress(self, task_id: str) -> Dict:
        """
        获取任务进度详情

        Args:
            task_id: 任务ID

        Returns:
            包含任务信息和进度历史的字典
        """
        task = self._task_manager.get_task(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}

        history = self._progress_history.get(task_id, [])

        return {
            "task": task.to_dict(),
            "progress_history": history,
            "current_progress": task.progress,
            "status": task.status.value,
            "time_elapsed": self._calculate_time_elapsed(task),
            "estimated_completion": self._estimate_completion(task, history),
        }

    def get_all_progress(self) -> List[Dict]:
        """
        获取所有任务进度

        Returns:
            所有任务的进度信息列表
        """
        all_tasks = self._task_manager.get_all_tasks()
        progress_list = []

        for task in all_tasks:
            progress_list.append(self.get_task_progress(task.id))

        return progress_list

    def get_active_progress(self) -> List[Dict]:
        """
        获取活跃任务进度

        Returns:
            活跃任务的进度信息列表
        """
        active_tasks = self._task_manager.get_active_tasks()
        progress_list = []

        for task in active_tasks:
            progress_list.append(self.get_task_progress(task.id))

        return progress_list

    def get_completion_stats(self) -> Dict:
        """
        获取任务完成统计

        Returns:
            任务完成统计信息
        """
        all_tasks = self._task_manager.get_all_tasks()
        completed = 0
        failed = 0
        running = 0
        pending = 0

        for task in all_tasks:
            if task.status == TaskStatus.COMPLETED:
                completed += 1
            elif task.status == TaskStatus.FAILED:
                failed += 1
            elif task.status == TaskStatus.RUNNING:
                running += 1
            elif task.status == TaskStatus.PENDING:
                pending += 1

        return {
            "total": len(all_tasks),
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "completion_rate": completed / len(all_tasks) if all_tasks else 0,
        }

    def get_progress_summary(self) -> Dict:
        """
        获取进度总结

        Returns:
            进度总结信息
        """
        stats = self.get_completion_stats()
        active_progress = self.get_active_progress()

        avg_progress = 0.0
        if active_progress:
            avg_progress = sum(
                task["current_progress"] for task in active_progress
            ) / len(active_progress)

        return {
            "stats": stats,
            "active_tasks": len(active_progress),
            "average_progress": avg_progress,
            "last_updated": datetime.now().isoformat(),
        }

    def _calculate_time_elapsed(self, task: Task) -> str:
        """
        计算任务执行时间

        Args:
            task: 任务对象

        Returns:
            格式化的时间字符串
        """
        end_time = task.completed_at or datetime.now()
        elapsed = end_time - task.created_at

        hours, remainder = divmod(elapsed.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"

    def _estimate_completion(self, task: Task, history: List[Dict]) -> Optional[str]:
        """
        估算任务完成时间

        Args:
            task: 任务对象
            history: 进度历史

        Returns:
            估算的完成时间字符串，或None
        """
        if task.status == TaskStatus.COMPLETED or task.status == TaskStatus.FAILED:
            return None

        if len(history) < 2:
            return None

        # 计算平均进度速率
        times = []
        progress_values = []

        for entry in history:
            times.append(datetime.fromisoformat(entry["timestamp"]))
            progress_values.append(entry["progress"])

        # 计算速率（%/秒）
        total_time = (times[-1] - times[0]).total_seconds()
        total_progress = progress_values[-1] - progress_values[0]

        if total_progress <= 0:
            return None

        rate = total_progress / total_time

        remaining_progress = 100 - progress_values[-1]
        remaining_time = remaining_progress / rate

        if remaining_time <= 0:
            return None

        completion_time = times[-1] + datetime.timedelta(seconds=remaining_time)

        return completion_time.strftime("%H:%M:%S")

    def clear_history(self, task_id: Optional[str] = None):
        """
        清除进度历史

        Args:
            task_id: 可选的任务ID，如未提供则清除所有历史
        """
        if task_id:
            if task_id in self._progress_history:
                del self._progress_history[task_id]
                logger.debug(f"Cleared progress history for task {task_id}")
        else:
            self._progress_history.clear()
            logger.debug("Cleared all progress history")

    def export_report(self) -> Dict:
        """
        导出详细进度报告

        Returns:
            包含完整报告的字典
        """
        report = {
            "summary": self.get_progress_summary(),
            "tasks": self.get_all_progress(),
            "generated_at": datetime.now().isoformat(),
        }

        return report

    def get_tasks_by_progress_range(
        self, min_progress: float, max_progress: float
    ) -> List[Dict]:
        """
        获取指定进度范围内的任务

        Args:
            min_progress: 最小进度
            max_progress: 最大进度

        Returns:
            符合条件的任务列表
        """
        all_progress = self.get_all_progress()

        return [
            task
            for task in all_progress
            if min_progress <= task["current_progress"] <= max_progress
        ]

    def get_stalled_tasks(self, time_threshold: int = 300) -> List[Dict]:
        """
        找出可能已停滞的任务

        Args:
            time_threshold: 停滞时间阈值（秒）

        Returns:
            可能已停滞的任务列表
        """
        now = datetime.now()
        stalled = []

        for task_info in self.get_active_progress():
            task = task_info["task"]
            updated_at = datetime.fromisoformat(task["updated_at"])

            # 检查是否在指定时间内没有更新
            if (now - updated_at).total_seconds() > time_threshold:
                stalled.append(task_info)

        return stalled
