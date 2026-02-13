"""UI 组件测试模块."""

import time
import unittest
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from nanobot.ui.formatters import (
    ColorTheme,
    TableFormatter,
    TreeFormatter,
    create_status_badge,
    format_duration,
    format_file_size,
    format_timestamp,
)
from nanobot.ui.progress_manager import ProgressManager, TaskProgress
from nanobot.ui.widgets import ProgressInfo, ProgressWidget, StatusWidget


class TestTaskProgress(unittest.TestCase):
    """TaskProgress 测试类."""

    def test_init_default_values(self):
        """测试默认初始化值."""
        task = TaskProgress(id="test-1", name="Test Task")
        self.assertEqual(task.id, "test-1")
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.description, "")
        self.assertEqual(task.total, 100.0)
        self.assertEqual(task.completed, 0.0)
        self.assertEqual(task.status, "pending")
        self.assertIsNone(task.start_time)
        self.assertIsNone(task.end_time)
        self.assertEqual(task.metadata, {})

    def test_percentage_calculation(self):
        """测试百分比计算."""
        task = TaskProgress(id="test", name="Test", total=100, completed=50)
        self.assertEqual(task.percentage, 50.0)

        task.completed = 75
        self.assertEqual(task.percentage, 75.0)

        task.completed = 120
        self.assertEqual(task.percentage, 100.0)  # 应该被限制在 100%

        task.total = 0
        self.assertEqual(task.percentage, 0.0)  # 防止除以零

    def test_elapsed_time(self):
        """测试已用时间计算."""
        task = TaskProgress(id="test", name="Test")
        self.assertEqual(task.elapsed_time, 0.0)

        task.start_time = time.time() - 10  # 10 秒前开始
        self.assertAlmostEqual(task.elapsed_time, 10.0, places=1)

        task.end_time = task.start_time + 5  # 5 秒后结束
        self.assertAlmostEqual(task.elapsed_time, 5.0, places=1)

    def test_is_running(self):
        """测试运行状态检查."""
        task = TaskProgress(id="test", name="Test")

        task.status = "pending"
        self.assertFalse(task.is_running)

        task.status = "running"
        self.assertTrue(task.is_running)

        task.status = "paused"
        self.assertFalse(task.is_running)

        task.status = "completed"
        self.assertFalse(task.is_running)

        task.status = "failed"
        self.assertFalse(task.is_running)

    def test_is_completed(self):
        """测试完成状态检查."""
        task = TaskProgress(id="test", name="Test")

        task.status = "pending"
        self.assertFalse(task.is_completed)

        task.status = "running"
        self.assertFalse(task.is_completed)

        task.status = "completed"
        self.assertTrue(task.is_completed)

        task.status = "failed"
        self.assertTrue(task.is_completed)

    def test_to_dict(self):
        """测试转换为字典."""
        task = TaskProgress(
            id="test",
            name="Test Task",
            description="A test task",
            total=100,
            completed=50,
            status="running",
            metadata={"key": "value"},
        )
        task.start_time = time.time()

        result = task.to_dict()

        self.assertEqual(result["id"], "test")
        self.assertEqual(result["name"], "Test Task")
        self.assertEqual(result["description"], "A test task")
        self.assertEqual(result["total"], 100)
        self.assertEqual(result["completed"], 50)
        self.assertEqual(result["status"], "running")
        self.assertEqual(result["percentage"], 50.0)
        self.assertIn("elapsed_time", result)
        self.assertEqual(result["metadata"], {"key": "value"})


class TestProgressManager(unittest.TestCase):
    """ProgressManager 测试类."""

    def setUp(self):
        """测试前设置."""
        self.console = Console(force_terminal=True, color_system="truecolor")
        self.manager = ProgressManager(console=self.console)

    def test_init(self):
        """测试初始化."""
        self.assertIsNotNone(self.manager.console)
        self.assertEqual(self.manager.tasks, {})
        self.assertIsNone(self.manager._live)
        self.assertIsNone(self.manager._progress_bars)
        self.assertEqual(self.manager._task_id_map, {})

    def test_create_task(self):
        """测试创建任务."""
        task = self.manager.create_task(
            name="Test Task",
            description="A test task",
            total=100,
            status="pending",
            metadata={"key": "value"},
        )

        self.assertIn(task.id, self.manager.tasks)
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.description, "A test task")
        self.assertEqual(task.total, 100)
        self.assertEqual(task.status, "pending")
        self.assertEqual(task.metadata, {"key": "value"})

    def test_start_task(self):
        """测试开始任务."""
        task = self.manager.create_task(name="Test Task")
        self.assertIsNone(task.start_time)

        self.manager.start_task(task.id)
        self.assertIsNotNone(task.start_time)
        self.assertEqual(task.status, "running")

    def test_update_task(self):
        """测试更新任务."""
        task = self.manager.create_task(name="Test Task", total=100)

        self.manager.update_task(
            task.id,
            completed=50,
            status="running",
            metadata={"step": 2},
        )

        self.assertEqual(task.completed, 50)
        self.assertEqual(task.status, "running")
        self.assertEqual(task.metadata, {"step": 2})

    def test_complete_task(self):
        """测试完成任务."""
        task = self.manager.create_task(name="Test Task", total=100)
        self.manager.start_task(task.id)

        self.manager.complete_task(task.id, success=True)

        self.assertEqual(task.status, "completed")
        self.assertEqual(task.completed, task.total)
        self.assertIsNotNone(task.end_time)

    def test_complete_task_failure(self):
        """测试任务失败."""
        task = self.manager.create_task(name="Test Task", total=100)
        self.manager.start_task(task.id)

        self.manager.complete_task(task.id, success=False)

        self.assertEqual(task.status, "failed")
        self.assertIsNotNone(task.end_time)

    def test_get_task(self):
        """测试获取任务."""
        task = self.manager.create_task(name="Test Task")
        retrieved = self.manager.get_task(task.id)
        self.assertEqual(retrieved, task)

    def test_get_all_tasks(self):
        """测试获取所有任务."""
        task1 = self.manager.create_task(name="Task 1")
        task2 = self.manager.create_task(name="Task 2")

        all_tasks = self.manager.get_all_tasks()

        self.assertEqual(len(all_tasks), 2)
        self.assertIn(task1, all_tasks)
        self.assertIn(task2, all_tasks)

    def test_get_running_tasks(self):
        """测试获取运行中的任务."""
        task1 = self.manager.create_task(name="Task 1")
        task2 = self.manager.create_task(name="Task 2")

        self.manager.start_task(task1.id)

        running = self.manager.get_running_tasks()

        self.assertEqual(len(running), 1)
        self.assertEqual(running[0], task1)

    def test_remove_task(self):
        """测试移除任务."""
        task = self.manager.create_task(name="Test Task")
        self.assertIn(task.id, self.manager.tasks)

        result = self.manager.remove_task(task.id)

        self.assertTrue(result)
        self.assertNotIn(task.id, self.manager.tasks)

    def test_remove_task_not_found(self):
        """测试移除不存在的任务."""
        result = self.manager.remove_task("non-existent-id")
        self.assertFalse(result)

    def test_generate_summary_table(self):
        """测试生成汇总表格."""
        # 创建不同状态的任务
        task1 = self.manager.create_task(name="Task 1", total=100)
        task1.status = "running"
        task1.completed = 50
        task1.start_time = time.time() - 10

        task2 = self.manager.create_task(name="Task 2", total=100)
        task2.status = "completed"
        task2.completed = 100

        table = self.manager.generate_summary_table()

        self.assertIsNotNone(table)
        self.assertEqual(table.title, "Task Summary")


class TestProgressWidget(unittest.TestCase):
    """ProgressWidget 测试类."""

    def setUp(self):
        """测试前设置."""
        self.console = Console(force_terminal=True)
        self.widget = ProgressWidget(console=self.console)

    def test_init(self):
        """测试初始化."""
        self.assertIsNotNone(self.widget.console)
        self.assertTrue(self.widget.show_percentage)
        self.assertTrue(self.widget.show_time)
        self.assertTrue(self.widget.show_spinner)
        self.assertEqual(self.widget.bar_width, 40)
        self.assertIsNone(self.widget._progress)

    def test_start_stop(self):
        """测试启动和停止."""
        self.widget.start()
        self.assertIsNotNone(self.widget._progress)

        self.widget.stop()
        self.assertIsNone(self.widget._progress)

    def test_add_task(self):
        """测试添加任务."""
        self.widget.start()

        task_id = self.widget.add_task(name="Test Task", total=100)

        self.assertIsNotNone(task_id)
        self.assertIn(task_id, self.widget._task_map)

        self.widget.stop()

    def test_update_task(self):
        """测试更新任务."""
        self.widget.start()

        task_id = self.widget.add_task(name="Test Task", total=100)
        result = self.widget.update_task(task_id, completed=50)

        self.assertTrue(result)

        self.widget.stop()

    def test_remove_task(self):
        """测试移除任务."""
        self.widget.start()

        task_id = self.widget.add_task(name="Test Task", total=100)
        result = self.widget.remove_task(task_id)

        self.assertTrue(result)
        self.assertNotIn(task_id, self.widget._task_map)

        self.widget.stop()

    def test_context_manager(self):
        """测试上下文管理器."""
        with self.widget as w:
            self.assertIsNotNone(w._progress)
            task_id = w.add_task(name="Test Task")
            self.assertIsNotNone(task_id)

        self.assertIsNone(self.widget._progress)


class TestProgressInfo(unittest.TestCase):
    """ProgressInfo 测试类."""

    def test_init(self):
        """测试初始化."""
        info = ProgressInfo(name="Test")
        self.assertEqual(info.name, "Test")
        self.assertEqual(info.current, 0.0)
        self.assertEqual(info.total, 100.0)
        self.assertEqual(info.unit, "items")
        self.assertEqual(info.status, "running")
        self.assertEqual(info.description, "")
        self.assertIsNone(info.start_time)
        self.assertEqual(info.metadata, {})

    def test_percentage(self):
        """测试百分比计算."""
        info = ProgressInfo(name="Test", total=100, current=50)
        self.assertEqual(info.percentage, 50.0)

        info.current = 75
        self.assertEqual(info.percentage, 75.0)

        info.total = 0
        self.assertEqual(info.percentage, 0.0)

    def test_remaining(self):
        """测试剩余量计算."""
        info = ProgressInfo(name="Test", total=100, current=60)
        self.assertEqual(info.remaining, 40.0)

        info.current = 120
        self.assertEqual(info.remaining, 0.0)

    def test_elapsed_time(self):
        """测试已用时间计算."""
        info = ProgressInfo(name="Test")
        self.assertEqual(info.elapsed_time, 0.0)

        info.start_time = time.time() - 10
        self.assertAlmostEqual(info.elapsed_time, 10.0, places=1)

    def test_estimated_time_remaining(self):
        """测试估计剩余时间."""
        info = ProgressInfo(name="Test", total=100, current=0)
        self.assertIsNone(info.estimated_time_remaining)

        info.start_time = time.time() - 10
        info.current = 50
        # 50 items in 10 seconds = 5 items/second
        # 50 remaining = 10 seconds
        self.assertAlmostEqual(info.estimated_time_remaining, 10.0, places=1)

    def test_to_dict(self):
        """测试转换为字典."""
        info = ProgressInfo(
            name="Test",
            total=100,
            current=50,
            metadata={"key": "value"},
        )
        info.start_time = time.time() - 10

        result = info.to_dict()

        self.assertEqual(result["name"], "Test")
        self.assertEqual(result["current"], 50)
        self.assertEqual(result["total"], 100)
        self.assertEqual(result["percentage"], 50.0)
        self.assertEqual(result["metadata"], {"key": "value"})
        self.assertIn("elapsed_time", result)
        self.assertIn("estimated_time_remaining", result)


class TestStatusWidget(unittest.TestCase):
    """StatusWidget 测试类."""

    def setUp(self):
        """测试前设置."""
        self.console = Console(force_terminal=True)
        self.widget = StatusWidget(console=self.console)

    def test_init(self):
        """测试初始化."""
        self.assertIsNotNone(self.widget.console)
        self.assertTrue(self.widget.show_cpu)
        self.assertTrue(self.widget.show_memory)
        self.assertFalse(self.widget.show_disk)
        self.assertTrue(self.widget.show_tasks)
        self.assertEqual(self.widget.refresh_interval, 1.0)
        self.assertEqual(self.widget._task_count, 0)
        self.assertEqual(self.widget._running_count, 0)

    def test_set_task_counts(self):
        """测试设置任务数量."""
        self.widget.set_task_counts(total=10, running=3)
        self.assertEqual(self.widget._task_count, 10)
        self.assertEqual(self.widget._running_count, 3)

    @patch("psutil.cpu_percent")
    @patch("psutil.cpu_count")
    @patch("psutil.cpu_freq")
    @patch("psutil.virtual_memory")
    def test_get_system_info(
        self,
        mock_virtual_memory,
        mock_cpu_freq,
        mock_cpu_count,
        mock_cpu_percent,
    ):
        """测试获取系统信息."""
        # 设置模拟返回值
        mock_cpu_percent.return_value = 50.0
        mock_cpu_count.return_value = 8

        class MockCpuFreq:
            current = 2400.0

        mock_cpu_freq.return_value = MockCpuFreq()

        class MockMemory:
            total = 16 * 1024**3
            available = 8 * 1024**3
            used = 8 * 1024**3
            percent = 50.0

        mock_virtual_memory.return_value = MockMemory()

        # 设置任务数量
        self.widget.set_task_counts(total=5, running=2)

        info = self.widget.get_system_info()

        self.assertIn("cpu", info)
        self.assertEqual(info["cpu"]["percent"], 50.0)
        self.assertEqual(info["cpu"]["count"], 8)

        self.assertIn("memory", info)
        self.assertEqual(info["memory"]["percent"], 50.0)

        self.assertIn("tasks", info)
        self.assertEqual(info["tasks"]["total"], 5)
        self.assertEqual(info["tasks"]["running"], 2)

    def test_make_bar(self):
        """测试创建进度条."""
        bar = self.widget._make_bar(50, 100, 20)
        self.assertEqual(len(bar), 20)
        self.assertEqual(bar, "██████████░░░░░░░░░░")

        bar = self.widget._make_bar(0, 100, 10)
        self.assertEqual(bar, "░░░░░░░░░░")

        bar = self.widget._make_bar(100, 100, 10)
        self.assertEqual(bar, "██████████")

    def test_render(self):
        """测试渲染."""
        panel = self.widget.render()
        self.assertIsInstance(panel, Panel)
        self.assertEqual(panel.title, "System Status")


class TestTableFormatter(unittest.TestCase):
    """TableFormatter 测试类."""

    def setUp(self):
        """测试前设置."""
        self.console = Console(force_terminal=True)
        self.formatter = TableFormatter(console=self.console)

    def test_init(self):
        """测试初始化."""
        self.assertIsNotNone(self.formatter.console)
        self.assertIsNotNone(self.formatter.theme)
        self.assertIsNotNone(self.formatter.box_style)

    def test_create_table(self):
        """测试创建表格."""
        columns = [
            {"name": "Name", "style": "cyan"},
            {"name": "Value", "justify": "right"},
        ]
        table = self.formatter.create_table(
            title="Test Table",
            columns=columns,
            show_header=True,
        )

        self.assertIsNotNone(table)
        self.assertEqual(table.title, "Test Table")

    def test_create_key_value_table(self):
        """测试创建键值对表格."""
        data = {
            "Name": "Test",
            "Count": 42,
            "Active": True,
            "None Value": None,
            "Float": 3.14,
        }
        table = self.formatter.create_key_value_table(data, title="KV Table")

        self.assertIsNotNone(table)
        self.assertEqual(table.title, "KV Table")

    def test_create_comparison_table(self):
        """测试创建对比表格."""
        data = [
            {"name": "Item A", "score": 85, "time": 120},
            {"name": "Item B", "score": 92, "time": 150},
            {"name": "Item C", "score": 78, "time": 100},
        ]
        table = self.formatter.create_comparison_table(
            data,
            columns=["name", "score", "time"],
            title="Comparison",
            highlight_best="score",
        )

        self.assertIsNotNone(table)
        self.assertEqual(table.title, "Comparison")


class TestTreeFormatter(unittest.TestCase):
    """TreeFormatter 测试类."""

    def setUp(self):
        """测试前设置."""
        self.console = Console(force_terminal=True)
        self.formatter = TreeFormatter(console=self.console)

    def test_create_tree(self):
        """测试创建树形结构."""
        data = {
            "level1": {
                "level2a": {
                    "level3": "value1",
                },
                "level2b": "value2",
            },
            "simple": "value3",
        }
        tree = self.formatter.create_tree("Root", data)

        self.assertIsNotNone(tree)

    def test_format_value(self):
        """测试格式化值."""
        self.assertEqual(
            self.formatter._format_value(None),
            "[dim]null[/dim]",
        )
        self.assertEqual(
            self.formatter._format_value(True),
            "[green]True[/]",
        )
        self.assertEqual(
            self.formatter._format_value(False),
            "[red]False[/]",
        )
        self.assertEqual(
            self.formatter._format_value(42),
            "[yellow]42[/]",
        )
        self.assertEqual(
            self.formatter._format_value(3.14),
            "[yellow]3.14[/]",
        )
        self.assertEqual(
            self.formatter._format_value("hello"),
            '"[green]hello[/]"',
        )


class TestFormatters(unittest.TestCase):
    """格式化函数测试类."""

    def test_create_status_badge(self):
        """测试创建状态徽章."""
        # 测试各种状态
        badge = create_status_badge("success")
        self.assertIsInstance(badge, Text)

        badge = create_status_badge("error")
        self.assertIsInstance(badge, Text)

        badge = create_status_badge("warning")
        self.assertIsInstance(badge, Text)

        badge = create_status_badge("info")
        self.assertIsInstance(badge, Text)

        badge = create_status_badge("unknown")
        self.assertIsInstance(badge, Text)

    def test_format_file_size(self):
        """测试格式化文件大小."""
        self.assertEqual(format_file_size(500), "500.00 B")
        self.assertEqual(format_file_size(1024), "1.00 KB")
        self.assertEqual(format_file_size(1024 * 1024), "1.00 MB")
        self.assertEqual(format_file_size(1024**3), "1.00 GB")
        self.assertEqual(format_file_size(1024**4), "1.00 TB")

    def test_format_duration(self):
        """测试格式化持续时间."""
        self.assertEqual(format_duration(45), "45.0s")
        self.assertEqual(format_duration(90), "1m 30s")
        self.assertEqual(format_duration(3600), "1h 0m")
        self.assertEqual(format_duration(3661), "1h 1m")
        self.assertEqual(format_duration(86400), "1d 0h")
        self.assertEqual(format_duration(90061), "1d 1h")

    def test_format_timestamp(self):
        """测试格式化时间戳."""
        import time
        from datetime import datetime

        # 测试 float 时间戳
        ts = time.time()
        result = format_timestamp(ts)
        self.assertIsInstance(result, str)

        # 测试 datetime 对象
        dt = datetime.now()
        result = format_timestamp(dt)
        self.assertIsInstance(result, str)

        # 测试自定义格式
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = format_timestamp(dt, "%Y-%m-%d")
        self.assertEqual(result, "2024-01-15")


class TestColorTheme(unittest.TestCase):
    """ColorTheme 测试类."""

    def test_default_theme(self):
        """测试默认主题."""
        theme = ColorTheme()
        self.assertEqual(theme.primary, "cyan")
        self.assertEqual(theme.success, "green")
        self.assertEqual(theme.error, "red")
        self.assertEqual(theme.warning, "yellow")

    def test_custom_theme(self):
        """测试自定义主题."""
        theme = ColorTheme(primary="blue", success="bright_green")
        self.assertEqual(theme.primary, "blue")
        self.assertEqual(theme.success, "bright_green")
        self.assertEqual(theme.error, "red")  # 默认值

    def test_get_style(self):
        """测试获取样式."""
        theme = ColorTheme()
        self.assertEqual(theme.get_style("primary"), "cyan")
        self.assertEqual(theme.get_style("success"), "green")
        self.assertEqual(theme.get_style("nonexistent"), "white")


if __name__ == "__main__":
    unittest.main()
