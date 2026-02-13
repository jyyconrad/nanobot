"""格式化模块 - 提供彩色输出和表格显示功能."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


@dataclass
class ColorTheme:
    """颜色主题配置."""

    primary: str = "cyan"
    secondary: str = "blue"
    success: str = "green"
    warning: str = "yellow"
    error: str = "red"
    info: str = "blue"
    muted: str = "dim"

    def get_style(self, key: str) -> str:
        """获取样式."""
        return getattr(self, key, "white")


# 预定义主题
DEFAULT_THEME = ColorTheme()
DARK_THEME = ColorTheme(
    primary="bright_cyan",
    secondary="bright_blue",
    success="bright_green",
    warning="bright_yellow",
    error="bright_red",
    info="bright_blue",
    muted="dim",
)


class ColorFormatter:
    """彩色格式化器."""

    def __init__(self, theme: Optional[ColorTheme] = None, console: Optional[Console] = None):
        """初始化格式化器.

        Args:
            theme: 颜色主题
            console: Rich 控制台实例
        """
        self.theme = theme or DEFAULT_THEME
        self.console = console or Console()

    def text(self, content: str, color: Optional[str] = None, bold: bool = False) -> Text:
        """创建彩色文本.

        Args:
            content: 文本内容
            color: 颜色
            bold: 是否加粗

        Returns:
            Rich Text 对象
        """
        style = color or self.theme.primary
        if bold:
            style = f"bold {style}"
        return Text(content, style=style)

    def success(self, message: str) -> Text:
        """成功消息."""
        return Text(f"✓ {message}", style=f"bold {self.theme.success}")

    def error(self, message: str) -> Text:
        """错误消息."""
        return Text(f"✗ {message}", style=f"bold {self.theme.error}")

    def warning(self, message: str) -> Text:
        """警告消息."""
        return Text(f"⚠ {message}", style=f"bold {self.theme.warning}")

    def info(self, message: str) -> Text:
        """信息消息."""
        return Text(f"ℹ {message}", style=self.theme.info)

    def muted(self, message: str) -> Text:
        """灰色文本."""
        return Text(message, style=self.theme.muted)

    def highlight(self, message: str) -> Text:
        """高亮文本."""
        return Text(message, style=f"bold {self.theme.primary}")


class TableFormatter:
    """表格格式化器."""

    def __init__(
        self,
        theme: Optional[ColorTheme] = None,
        console: Optional[Console] = None,
        box_style: box.Box = box.ROUNDED,
    ):
        """初始化表格格式化器.

        Args:
            theme: 颜色主题
            console: Rich 控制台实例
            box_style: 边框样式
        """
        self.theme = theme or DEFAULT_THEME
        self.console = console or Console()
        self.box_style = box_style

    def create_table(
        self,
        title: Optional[str] = None,
        columns: Optional[List[Dict[str, Any]]] = None,
        show_header: bool = True,
        show_lines: bool = False,
    ) -> Table:
        """创建表格.

        Args:
            title: 表格标题
            columns: 列定义列表，每项包含 name, style, justify, width 等
            show_header: 是否显示表头
            show_lines: 是否显示行间线条

        Returns:
            Rich Table 对象
        """
        table = Table(
            title=title,
            box=self.box_style,
            show_header=show_header,
            show_lines=show_lines,
            header_style=f"bold {self.theme.primary}",
            border_style=self.theme.muted,
        )

        if columns:
            for col in columns:
                table.add_column(
                    col.get("name", ""),
                    style=col.get("style"),
                    justify=col.get("justify", "left"),
                    width=col.get("width"),
                    no_wrap=col.get("no_wrap", False),
                )

        return table

    def create_key_value_table(
        self,
        data: Dict[str, Any],
        title: Optional[str] = None,
        key_style: str = "cyan",
        value_style: str = "white",
    ) -> Table:
        """创建键值对表格.

        Args:
            data: 数据字典
            title: 表格标题
            key_style: 键的样式
            value_style: 值的样式

        Returns:
            Rich Table 对象
        """
        table = Table(
            title=title,
            box=self.box_style,
            show_header=False,
            border_style=self.theme.muted,
        )
        table.add_column(style=f"bold {key_style}", justify="right", width=20)
        table.add_column(style=value_style)

        for key, value in data.items():
            # 格式化值
            if isinstance(value, float):
                value_str = f"{value:.2f}"
            elif isinstance(value, bool):
                value_str = "✓ Yes" if value else "✗ No"
            elif value is None:
                value_str = "-"
            else:
                value_str = str(value)

            table.add_row(str(key), value_str)

        return table

    def create_comparison_table(
        self,
        data: List[Dict[str, Any]],
        columns: List[str],
        title: Optional[str] = None,
        highlight_best: Optional[str] = None,
    ) -> Table:
        """创建对比表格.

        Args:
            data: 数据列表，每项是一个字典
            columns: 要显示的列名
            title: 表格标题
            highlight_best: 要高亮最佳值的列

        Returns:
            Rich Table 对象
        """
        table = Table(
            title=title,
            box=self.box_style,
            show_header=True,
            header_style=f"bold {self.theme.primary}",
            border_style=self.theme.muted,
        )

        # 添加列
        for col in columns:
            table.add_column(col, justify="center")

        # 找到最佳值
        best_value = None
        if highlight_best and data:
            values = [d.get(highlight_best) for d in data if isinstance(d.get(highlight_best), (int, float))]
            if values:
                best_value = max(values)

        # 添加行
        for row_data in data:
            row_values = []
            for col in columns:
                value = row_data.get(col, "")
                text = str(value) if value is not None else "-"

                # 高亮最佳值
                if col == highlight_best and value == best_value:
                    text = f"[bold green]{text}[/bold green]"

                row_values.append(text)

            table.add_row(*row_values)

        return table


class TreeFormatter:
    """树形结构格式化器."""

    def __init__(self, theme: Optional[ColorTheme] = None, console: Optional[Console] = None):
        """初始化树形格式化器.

        Args:
            theme: 颜色主题
            console: Rich 控制台实例
        """
        self.theme = theme or DEFAULT_THEME
        self.console = console or Console()

    def create_tree(
        self,
        label: str,
        data: Dict[str, Any],
        expanded: bool = True,
    ) -> Tree:
        """创建树形结构.

        Args:
            label: 根节点标签
            data: 树形数据
            expanded: 是否展开

        Returns:
            Rich Tree 对象
        """
        tree = Tree(
            f"[bold {self.theme.primary}]{label}[/bold {self.theme.primary}]",
            expanded=expanded,
        )
        self._add_branches(tree, data)
        return tree

    def _add_branches(self, tree: Tree, data: Any, key: Optional[str] = None) -> None:
        """递归添加分支.

        Args:
            tree: 父树节点
            data: 数据
            key: 当前键名
        """
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (dict, list)) and v:
                    branch = tree.add(f"[bold cyan]{k}:[/bold cyan]")
                    self._add_branches(branch, v, k)
                else:
                    self._add_branches(tree, v, k)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    branch = tree.add(f"[dim][{i}]:[/dim]")
                    self._add_branches(branch, item, str(i))
                else:
                    tree.add(f"[dim][{i}]:[/dim] {self._format_value(item)}")
        else:
            label = f"[cyan]{key}:[/cyan] " if key else ""
            tree.add(f"{label}{self._format_value(data)}")

    def _format_value(self, value: Any) -> str:
        """格式化值."""
        if value is None:
            return "[dim]null[/dim]"
        elif isinstance(value, bool):
            return f"[{'green' if value else 'red'}]{value}[/]"
        elif isinstance(value, (int, float)):
            return f"[yellow]{value}[/]"
        elif isinstance(value, str):
            return f'"[green]{value}[/]"'
        else:
            return str(value)


def create_status_badge(
    status: str,
    theme: Optional[ColorTheme] = None,
) -> Text:
    """创建状态徽章.

    Args:
        status: 状态字符串
        theme: 颜色主题

    Returns:
        Rich Text 对象
    """
    theme = theme or DEFAULT_THEME

    status_colors = {
        "success": theme.success,
        "completed": theme.success,
        "ok": theme.success,
        "warning": theme.warning,
        "warn": theme.warning,
        "pending": theme.warning,
        "error": theme.error,
        "failed": theme.error,
        "fail": theme.error,
        "running": theme.info,
        "active": theme.info,
        "info": theme.info,
    }

    color = status_colors.get(status.lower(), theme.muted)
    return Text(f" {status.upper()} ", style=f"bold {color}")


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小.

    Args:
        size_bytes: 字节数

    Returns:
        格式化后的字符串
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """格式化持续时间.

    Args:
        seconds: 秒数

    Returns:
        格式化后的字符串
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days}d {hours}h"


def format_timestamp(ts: Union[float, datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间戳.

    Args:
        ts: 时间戳或 datetime 对象
        fmt: 格式字符串

    Returns:
        格式化后的字符串
    """
    if isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(ts)
    elif isinstance(ts, datetime):
        dt = ts
    else:
        return str(ts)

    return dt.strftime(fmt)
