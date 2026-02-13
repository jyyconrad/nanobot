"""UI 组件模块 - 提供进度和状态显示组件."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import psutil
from rich import box
from rich.console import Console, ConsoleOptions, RenderResult
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text


@dataclass
class ProgressInfo:
    """进度信息数据类."""

    name: str
    current: float = 0.0
    total: float = 100.0
    unit: str = "items"
    status: str = "running"  # running, paused, completed, failed
    description: str = ""
    start_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def percentage(self) -> float:
        """计算完成百分比."""
        if self.total <= 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100)

    @property
    def remaining(self) -> float:
        """计算剩余工作量."""
        return max(0.0, self.total - self.current)

    @property
    def elapsed_time(self) -> float:
        """计算已用时间(秒)."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    @property
    def estimated_time_remaining(self) -> Optional[float]:
        """估算剩余时间(秒)."""
        if self.current <= 0 or self.start_time is None:
            return None
        rate = self.current / self.elapsed_time
        if rate <= 0:
            return None
        return self.remaining / rate

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "name": self.name,
            "current": self.current,
            "total": self.total,
            "unit": self.unit,
            "status": self.status,
            "percentage": self.percentage,
            "description": self.description,
            "elapsed_time": self.elapsed_time,
            "estimated_time_remaining": self.estimated_time_remaining,
            "metadata": self.metadata,
        }


class ProgressWidget:
    """进度显示组件."""

    def __init__(
        self,
        console: Optional[Console] = None,
        show_percentage: bool = True,
        show_time: bool = True,
        show_spinner: bool = True,
        bar_width: int = 40,
    ):
        """初始化进度组件.

        Args:
            console: Rich 控制台实例
            show_percentage: 是否显示百分比
            show_time: 是否显示时间
            show_spinner: 是否显示旋转器
            bar_width: 进度条宽度
        """
        self.console = console or Console()
        self.show_percentage = show_percentage
        self.show_time = show_time
        self.show_spinner = show_spinner
        self.bar_width = bar_width

        self._progress: Optional[Progress] = None
        self._task_map: Dict[str, TaskID] = {}

    def _create_progress(self) -> Progress:
        """创建进度条对象."""
        columns: List[Any] = []

        if self.show_spinner:
            columns.append(SpinnerColumn("dots"))

        columns.append(TextColumn("[bold blue]{task.description}"))
        columns.append(BarColumn(bar_width=self.bar_width))

        if self.show_percentage:
            columns.append(TaskProgressColumn())

        if self.show_time:
            columns.append(TimeElapsedColumn())
            columns.append(TimeRemainingColumn())

        return Progress(*columns, console=self.console)

    def start(self) -> None:
        """启动进度显示."""
        if self._progress is None:
            self._progress = self._create_progress()
            self._progress.start()

    def stop(self) -> None:
        """停止进度显示."""
        if self._progress is not None:
            self._progress.stop()
            self._progress = None
            self._task_map.clear()

    def add_task(
        self,
        name: str,
        total: float = 100.0,
        completed: float = 0.0,
        visible: bool = True,
    ) -> str:
        """添加任务.

        Args:
            name: 任务名称
            total: 总工作量
            completed: 已完成工作量
            visible: 是否可见

        Returns:
            任务 ID
        """
        import uuid

        task_id = str(uuid.uuid4())

        if self._progress is not None:
            rich_task_id = self._progress.add_task(
                description=name,
                total=total,
                completed=completed,
                visible=visible,
            )
            self._task_map[task_id] = rich_task_id

        return task_id

    def update_task(
        self,
        task_id: str,
        completed: Optional[float] = None,
        total: Optional[float] = None,
        name: Optional[str] = None,
        visible: Optional[bool] = None,
    ) -> bool:
        """更新任务进度.

        Args:
            task_id: 任务 ID
            completed: 已完成工作量
            total: 总工作量
            name: 任务名称
            visible: 是否可见

        Returns:
            是否更新成功
        """
        if self._progress is None or task_id not in self._task_map:
            return False

        rich_task_id = self._task_map[task_id]

        kwargs: Dict[str, Any] = {}
        if completed is not None:
            kwargs["completed"] = completed
        if total is not None:
            kwargs["total"] = total
        if name is not None:
            kwargs["description"] = name
        if visible is not None:
            kwargs["visible"] = visible

        self._progress.update(rich_task_id, **kwargs)
        return True

    def remove_task(self, task_id: str) -> bool:
        """移除任务.

        Args:
            task_id: 任务 ID

        Returns:
            是否移除成功
        """
        if self._progress is None or task_id not in self._task_map:
            return False

        rich_task_id = self._task_map[task_id]
        self._progress.remove_task(rich_task_id)
        del self._task_map[task_id]
        return True

    def __enter__(self) -> ProgressWidget:
        """上下文管理器入口."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口."""
        self.stop()


class StatusWidget:
    """系统状态显示组件."""

    def __init__(
        self,
        console: Optional[Console] = None,
        show_cpu: bool = True,
        show_memory: bool = True,
        show_disk: bool = False,
        show_tasks: bool = True,
        refresh_interval: float = 1.0,
    ):
        """初始化状态组件.

        Args:
            console: Rich 控制台实例
            show_cpu: 是否显示 CPU 信息
            show_memory: 是否显示内存信息
            show_disk: 是否显示磁盘信息
            show_tasks: 是否显示任务数
            refresh_interval: 刷新间隔(秒)
        """
        self.console = console or Console()
        self.show_cpu = show_cpu
        self.show_memory = show_memory
        self.show_disk = show_disk
        self.show_tasks = show_tasks
        self.refresh_interval = refresh_interval

        self._task_count = 0
        self._running_count = 0

    def set_task_counts(self, total: int, running: int) -> None:
        """设置任务数量.

        Args:
            total: 总任务数
            running: 运行中的任务数
        """
        self._task_count = total
        self._running_count = running

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息.

        Returns:
            系统信息字典
        """
        info: Dict[str, Any] = {}

        if self.show_cpu:
            info["cpu"] = {
                "percent": psutil.cpu_percent(interval=None),
                "count": psutil.cpu_count(),
                "freq": psutil.cpu_freq(),
            }

        if self.show_memory:
            mem = psutil.virtual_memory()
            info["memory"] = {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "percent": mem.percent,
                "unit": "GB",
            }

        if self.show_disk:
            disk = psutil.disk_usage("/")
            info["disk"] = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100,
                "unit": "GB",
            }

        if self.show_tasks:
            info["tasks"] = {
                "total": self._task_count,
                "running": self._running_count,
            }

        return info

    def render(self) -> Panel:
        """渲染状态面板.

        Returns:
            Rich Panel 对象
        """
        info = self.get_system_info()

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="bold cyan", width=12)
        table.add_column("Value", style="white")

        if "cpu" in info:
            cpu = info["cpu"]
            bar = self._make_bar(cpu["percent"], 100, 20)
            table.add_row("CPU", f"{bar} {cpu['percent']:.1f}%")

        if "memory" in info:
            mem = info["memory"]
            used_gb = mem["used"] / (1024**3)
            total_gb = mem["total"] / (1024**3)
            bar = self._make_bar(mem["percent"], 100, 20)
            table.add_row(
                "Memory",
                f"{bar} {mem['percent']:.1f}% ({used_gb:.1f}/{total_gb:.1f} GB)",
            )

        if "disk" in info:
            disk = info["disk"]
            used_gb = disk["used"] / (1024**3)
            total_gb = disk["total"] / (1024**3)
            bar = self._make_bar(disk["percent"], 100, 20)
            table.add_row(
                "Disk",
                f"{bar} {disk['percent']:.1f}% ({used_gb:.1f}/{total_gb:.1f} GB)",
            )

        if "tasks" in info:
            tasks = info["tasks"]
            table.add_row(
                "Tasks",
                f"Running: {tasks['running']}, Total: {tasks['total']}",
            )

        return Panel(table, title="System Status", border_style="green", padding=(1, 2))

    def _make_bar(self, value: float, max_value: float, width: int) -> str:
        """创建进度条字符串.

        Args:
            value: 当前值
            max_value: 最大值
            width: 进度条宽度

        Returns:
            进度条字符串
        """
        if max_value <= 0:
            return "█" * width
        filled = int((value / max_value) * width)
        return "█" * filled + "░" * (width - filled)

    def __rich__(self) -> Panel:
        """Rich 渲染支持."""
        return self.render()

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich 控制台渲染支持."""
        yield self.render()
