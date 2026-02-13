"""进度管理模块 - 管理多任务进度显示."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text


@dataclass
class TaskProgress:
    """单个任务的进度信息."""

    id: str
    name: str
    description: str = ""
    total: float = 100.0
    completed: float = 0.0
    status: str = "pending"  # pending, running, paused, completed, failed
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def percentage(self) -> float:
        """计算完成百分比."""
        if self.total <= 0:
            return 0.0
        return min(100.0, (self.completed / self.total) * 100)

    @property
    def elapsed_time(self) -> float:
        """计算已用时间(秒)."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def is_running(self) -> bool:
        """检查任务是否正在运行."""
        return self.status == "running"

    @property
    def is_completed(self) -> bool:
        """检查任务是否已完成."""
        return self.status in ("completed", "failed")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "total": self.total,
            "completed": self.completed,
            "status": self.status,
            "percentage": self.percentage,
            "elapsed_time": self.elapsed_time,
            "metadata": self.metadata,
        }


class ProgressManager:
    """进度管理器 - 管理多个任务的进度显示."""

    def __init__(self, console: Optional[Console] = None):
        """初始化进度管理器.

        Args:
            console: Rich 控制台实例，如果为 None 则创建新实例
        """
        self.console = console or Console()
        self.tasks: Dict[str, TaskProgress] = {}
        self._live: Optional[Live] = None
        self._progress_bars: Optional[Progress] = None
        self._task_id_map: Dict[str, int] = {}  # 映射 task.id 到 Rich progress task_id

    def create_task(
        self,
        name: str,
        description: str = "",
        total: float = 100.0,
        status: str = "pending",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskProgress:
        """创建新任务.

        Args:
            name: 任务名称
            description: 任务描述
            total: 总工作量
            status: 初始状态
            metadata: 额外元数据

        Returns:
            创建的任务进度对象
        """
        task_id = str(uuid4())
        task = TaskProgress(
            id=task_id,
            name=name,
            description=description,
            total=total,
            status=status,
            metadata=metadata or {},
        )
        self.tasks[task_id] = task

        # 如果进度条已启动，添加新任务到显示
        if self._progress_bars is not None:
            rich_task_id = self._progress_bars.add_task(
                description=f"[cyan]{name}[/cyan]",
                total=total,
                completed=0,
            )
            self._task_id_map[task_id] = rich_task_id

        return task

    def start_task(self, task_id: str) -> TaskProgress:
        """开始任务.

        Args:
            task_id: 任务 ID

        Returns:
            任务进度对象

        Raises:
            KeyError: 如果任务不存在
        """
        task = self.tasks[task_id]
        task.status = "running"
        task.start_time = time.time()
        return task

    def update_task(
        self,
        task_id: str,
        completed: Optional[float] = None,
        total: Optional[float] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskProgress:
        """更新任务进度.

        Args:
            task_id: 任务 ID
            completed: 已完成工作量
            total: 总工作量
            status: 状态
            metadata: 额外元数据

        Returns:
            任务进度对象

        Raises:
            KeyError: 如果任务不存在
        """
        task = self.tasks[task_id]

        if completed is not None:
            task.completed = completed
        if total is not None:
            task.total = total
        if status is not None:
            task.status = status
        if metadata is not None:
            task.metadata.update(metadata)

        # 更新进度条显示
        if self._progress_bars is not None and task_id in self._task_id_map:
            rich_task_id = self._task_id_map[task_id]
            self._progress_bars.update(
                rich_task_id,
                completed=task.completed,
                total=task.total,
            )

        return task

    def complete_task(self, task_id: str, success: bool = True) -> TaskProgress:
        """完成任务.

        Args:
            task_id: 任务 ID
            success: 是否成功完成

        Returns:
            任务进度对象
        """
        task = self.tasks[task_id]
        task.status = "completed" if success else "failed"
        task.end_time = time.time()
        task.completed = task.total

        # 更新进度条
        if self._progress_bars is not None and task_id in self._task_id_map:
            rich_task_id = self._task_id_map[task_id]
            self._progress_bars.update(
                rich_task_id,
                completed=task.total,
                total=task.total,
            )

        return task

    def get_task(self, task_id: str) -> TaskProgress:
        """获取任务.

        Args:
            task_id: 任务 ID

        Returns:
            任务进度对象
        """
        return self.tasks[task_id]

    def get_all_tasks(self) -> List[TaskProgress]:
        """获取所有任务.

        Returns:
            任务列表
        """
        return list(self.tasks.values())

    def get_running_tasks(self) -> List[TaskProgress]:
        """获取正在运行的任务.

        Returns:
            正在运行的任务列表
        """
        return [t for t in self.tasks.values() if t.is_running]

    def remove_task(self, task_id: str) -> bool:
        """移除任务.

        Args:
            task_id: 任务 ID

        Returns:
            是否成功移除
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            if task_id in self._task_id_map:
                del self._task_id_map[task_id]
            return True
        return False

    def start_display(self) -> Live:
        """启动实时显示.

        Returns:
            Live 显示对象
        """
        if self._live is not None:
            return self._live

        # 创建进度条
        self._progress_bars = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            " ",
            TimeElapsedColumn(),
            " ",
            TimeRemainingColumn(),
            console=self.console,
        )

        # 将现有任务添加到进度条
        for task_id, task in self.tasks.items():
            rich_task_id = self._progress_bars.add_task(
                description=f"[cyan]{task.name}[/cyan]",
                total=task.total,
                completed=task.completed,
            )
            self._task_id_map[task_id] = rich_task_id

        # 创建布局
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
        )
        layout["main"].split_row(
            Layout(name="progress", ratio=2),
            Layout(name="status", ratio=1),
        )

        # 设置面板
        layout["header"].update(
            Panel(
                Text("Nanobot Progress Manager", style="bold cyan", justify="center"),
                border_style="cyan",
            )
        )
        layout["progress"].update(
            Panel(self._progress_bars, title="Tasks", border_style="blue")
        )
        layout["status"].update(
            Panel(Text("Loading..."), title="System Status", border_style="green")
        )

        # 启动实时显示
        self._live = Live(layout, console=self.console, refresh_per_second=4)
        self._live.start()

        return self._live

    def stop_display(self) -> None:
        """停止实时显示."""
        if self._live is not None:
            self._live.stop()
            self._live = None
            self._progress_bars = None
            self._task_id_map.clear()

    def __enter__(self) -> ProgressManager:
        """上下文管理器入口."""
        self.start_display()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口."""
        self.stop_display()

    def generate_summary_table(self) -> Table:
        """生成任务汇总表格.

        Returns:
            Rich Table 对象
        """
        table = Table(
            title="Task Summary",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Task", style="cyan", width=20)
        table.add_column("Status", style="bold", width=12)
        table.add_column("Progress", width=15)
        table.add_column("Time", justify="right", width=10)

        for task in self.tasks.values():
            status_style = {
                "pending": "dim",
                "running": "blue",
                "paused": "yellow",
                "completed": "green",
                "failed": "red",
            }.get(task.status, "white")

            progress_bar = "█" * int(task.percentage / 10) + "░" * (10 - int(task.percentage / 10))
            progress_text = f"{progress_bar} {task.percentage:.1f}%"

            table.add_row(
                task.name,
                f"[{status_style}]{task.status}[/{status_style}]",
                progress_text,
                f"{task.elapsed_time:.1f}s",
            )

        return table
