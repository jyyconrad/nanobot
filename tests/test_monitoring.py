"""
监控系统测试
"""

import time

import pytest

from nanobot.agent.monitoring.debugger import Debugger
from nanobot.agent.monitoring.health_checker import (
    HealthChecker,
    create_default_health_checker,
)
from nanobot.agent.monitoring.logger import StructuredLogger
from nanobot.agent.monitoring.metrics_collector import (
    ContextMetrics,
    LLMCallMetrics,
    MetricsCollector,
    ToolUseMetrics,
)
from nanobot.agent.monitoring.state_tracker import (
    AgentState,
    StateTracker,
    TaskProgress,
)


class TestStateTracker:
    """Agent状态跟踪器测试"""

    def test_initialization(self):
        """测试初始化"""
        tracker = StateTracker("agent_001")
        assert tracker.agent_id == "agent_001"
        assert tracker.get_state() == AgentState.INITIALIZING

    def test_state_transitions(self):
        """测试状态转换"""
        tracker = StateTracker("agent_001")
        tracker.set_state(AgentState.RUNNING)
        assert tracker.get_state() == AgentState.RUNNING

        tracker.set_state(AgentState.COMPLETED)
        assert tracker.get_state() == AgentState.COMPLETED

        states = [s["state"] for s in tracker.get_state_history()]
        assert len(states) >= 2

    def test_task_progress_creation_and_update(self):
        """测试任务进度创建和更新"""
        tracker = StateTracker("agent_001")
        progress = tracker.create_task_progress("task_001", "Test Task", 10)

        assert isinstance(progress, TaskProgress)
        assert progress.task_id == "task_001"
        assert progress.task_name == "Test Task"
        assert progress.total_steps == 10

        # 更新进度
        progress.update(percentage=25, current_step=2, status=AgentState.RUNNING)
        assert progress.percentage == 25.0
        assert progress.current_step == 2
        assert progress.status == AgentState.RUNNING

    def test_task_throughput(self):
        """测试任务吞吐量计算"""
        tracker = StateTracker("agent_001")
        progress = tracker.create_task_progress("task_001", "Test Task", 10)
        time.sleep(0.1)  # 等待一段时间以确保时间差
        progress.update(current_step=1)

        throughput = progress.get_throughput()
        assert throughput > 0

    def test_alive_check(self):
        """测试存活检查"""
        tracker = StateTracker("agent_001")
        assert tracker.is_alive() is True

    def test_uptime(self):
        """测试运行时间计算"""
        tracker = StateTracker("agent_001")
        time.sleep(0.1)
        assert tracker.get_uptime() >= 0.1


class TestMetricsCollector:
    """性能指标收集器测试"""

    def test_initialization(self):
        """测试初始化"""
        collector = MetricsCollector()
        assert isinstance(collector, MetricsCollector)

    def test_llm_call_recording(self):
        """测试LLM调用记录"""
        collector = MetricsCollector()
        collector.record_llm_call(
            provider="openai",
            model="gpt-3.5-turbo",
            latency=1.2,
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.002,
        )

        llm_metrics = collector.get_llm_metrics()
        assert "openai:gpt-3.5-turbo" in llm_metrics
        assert llm_metrics["openai:gpt-3.5-turbo"].call_count == 1
        assert llm_metrics["openai:gpt-3.5-turbo"].total_latency == 1.2

    def test_tool_use_recording(self):
        """测试工具使用记录"""
        collector = MetricsCollector()
        collector.record_tool_use(
            tool_name="file_operations", execution_time=0.5, success=True
        )

        tool_metrics = collector.get_tool_metrics()
        assert "file_operations" in tool_metrics
        assert tool_metrics["file_operations"].call_count == 1
        assert tool_metrics["file_operations"].total_execution_time == 0.5

    def test_context_compression_recording(self):
        """测试上下文压缩记录"""
        collector = MetricsCollector()
        collector.record_context_compression(1000, 500)
        collector.record_context_compression(800, 400)

        assert collector.get_context_metrics().compression_count == 2
        assert collector.get_context_metrics().get_avg_compression_ratio() == 0.5

    def test_context_cache_recording(self):
        """测试上下文缓存记录"""
        collector = MetricsCollector()
        collector.record_context_cache_access(True)
        collector.record_context_cache_access(True)
        collector.record_context_cache_access(False)

        assert collector.get_context_metrics().hit_count == 2
        assert collector.get_context_metrics().miss_count == 1
        assert collector.get_context_metrics().get_cache_hit_rate() == 2 / 3

    def test_system_metrics(self):
        """测试系统指标收集"""
        collector = MetricsCollector()
        collector.update_system_metrics()

        system_metrics = collector.get_system_metrics()
        assert "cpu" in system_metrics
        assert "memory" in system_metrics
        assert "disk" in system_metrics

        # 检查是否有有效的系统指标值
        assert isinstance(system_metrics["cpu"]["usage"], float)
        assert system_metrics["cpu"]["usage"] >= 0
        assert system_metrics["cpu"]["usage"] <= 100

    def test_summary_generation(self):
        """测试指标摘要生成"""
        collector = MetricsCollector()
        summary = collector.get_summary()

        assert "llm_calls" in summary
        assert "tool_usage" in summary
        assert "context" in summary
        assert "system" in summary


class TestStructuredLogger:
    """结构化日志记录器测试"""

    def test_logger_initialization(self):
        """测试日志器初始化"""
        logger = StructuredLogger("test_logger")
        assert isinstance(logger, StructuredLogger)

    def test_basic_log_levels(self):
        """测试基本日志级别"""
        logger = StructuredLogger("test_logger")
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

    def test_context_logging(self):
        """测试上下文日志记录"""
        logger = StructuredLogger("test_logger")
        logger.log_with_context(
            "INFO",
            "Request processed",
            request_id="req_001",
            task_id="task_001",
            session_id="session_001",
        )

    def test_log_paths(self):
        """测试日志路径"""
        logger = StructuredLogger("test_logger")
        assert logger.get_log_path().exists()


class TestHealthChecker:
    """健康检查器测试"""

    def test_initialization(self):
        """测试初始化"""
        state_tracker = StateTracker("agent_001")
        checker = HealthChecker(state_tracker)
        assert isinstance(checker, HealthChecker)

    def test_default_checker_creation(self):
        """测试默认健康检查器创建"""
        state_tracker = StateTracker("agent_001")
        checker = create_default_health_checker(state_tracker)
        assert isinstance(checker, HealthChecker)

        # 应该至少有3个健康检查
        status = checker.get_health_status()
        assert status["check_count"] >= 3
        assert isinstance(status["healthy"], bool)

    def test_health_check_execution(self):
        """测试健康检查执行"""
        state_tracker = StateTracker("agent_001")
        checker = create_default_health_checker(state_tracker)
        state_tracker.heartbeat()  # 更新心跳

        # 运行所有健康检查
        results = checker.run_all_checks()
        assert len(results) > 0

        # 检查至少包含基本的健康信息
        for result in results:
            assert hasattr(result, "check_name")
            assert hasattr(result, "is_healthy")
            assert hasattr(result, "message")

    def test_auto_recovery_registration(self):
        """测试自动恢复注册"""
        state_tracker = StateTracker("agent_001")
        checker = HealthChecker(state_tracker)

        recovered = False

        def recovery_action():
            nonlocal recovered
            recovered = True

        checker.register_check(
            "custom_check", lambda: (False, "Test failure", {}), recovery_action
        )

        assert not recovered
        checker.auto_recover()
        assert recovered


class TestDebugger:
    """调试器测试"""

    def test_initialization(self):
        """测试初始化"""
        debugger = Debugger()
        assert isinstance(debugger, Debugger)

    def test_debug_mode_control(self):
        """测试调试模式控制"""
        debugger = Debugger()
        assert not debugger.is_enabled()

        debugger.enable()
        assert debugger.is_enabled()

        debugger.disable()
        assert not debugger.is_enabled()

    def test_breakpoint_management(self):
        """测试断点管理"""
        debugger = Debugger()
        debugger.set_breakpoint("test_function")
        assert "test_function" in debugger.get_breakpoints()

        debugger.clear_breakpoint("test_function")
        assert "test_function" not in debugger.get_breakpoints()

        debugger.set_breakpoint("test_function")
        debugger.set_breakpoint("another_function")
        assert len(debugger.get_breakpoints()) == 2

        debugger.clear_all_breakpoints()
        assert len(debugger.get_breakpoints()) == 0

    def test_trace_recording(self):
        """测试跟踪记录"""
        debugger = Debugger()
        debugger.enable()

        debugger.trace(
            "Starting processing",
            location="process_request",
            request_id="req_001",
            task_id="task_001",
        )

        trace_stack = debugger.get_trace_stack()
        assert len(trace_stack) > 0

        debugger.clear_trace_stack()
        assert len(debugger.get_trace_stack()) == 0

    def test_request_response_tracking(self):
        """测试请求/响应追踪"""
        debugger = Debugger()
        debugger.enable()

        debugger.record_request(
            "req_001", "GET", "/api/v1/test", {"User-Agent": "Test"}, {"data": "test"}
        )

        time.sleep(0.1)
        debugger.record_response(
            "req_001", 200, {"Content-Type": "application/json"}, {"result": "success"}
        )

        trace = debugger.get_request_response_trace("req_001")
        assert trace is not None
        assert trace["request"]["method"] == "GET"
        assert trace["response"]["status_code"] == 200
        assert "latency" in trace


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
