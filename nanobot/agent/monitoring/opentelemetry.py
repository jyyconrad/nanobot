"""
OpenTelemetry 分布式追踪模块
"""

import traceback
import time
from typing import Optional, Dict, Any, List
from contextvars import ContextVar

import opentelemetry.sdk.trace as trace_sdk
from opentelemetry import trace
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode
from opentelemetry.semconv.trace import SpanAttributes

from loguru import logger


class OpenTelemetryTracer:
    """OpenTelemetry 分布式追踪器"""

    def __init__(self, service_name: str = "nanobot",
                 otlp_endpoint: str = "http://localhost:4317"):
        """
        初始化 OpenTelemetry 追踪器

        Args:
            service_name: 服务名称
            otlp_endpoint: OTLP 端点地址
        """
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint
        self._tracer = None
        self._provider = None
        self._initialized = False

    def initialize(self):
        """初始化 OpenTelemetry 追踪器"""
        try:
            # 配置资源
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": "0.2.1",  # 使用项目版本
                "telemetry.sdk.name": "opentelemetry",
                "telemetry.sdk.language": "python",
                "telemetry.sdk.version": "1.17.0"
            })

            # 创建追踪提供者
            self._provider = trace_sdk.TracerProvider(resource=resource)

            # 添加 OTLP 导出器
            try:
                exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
                processor = BatchSpanProcessor(exporter)
                self._provider.add_span_processor(processor)
            except Exception as e:
                logger.warning(f"Failed to initialize OTLP exporter: {e}")

            # 设置全局追踪提供者
            trace.set_tracer_provider(self._provider)
            self._tracer = trace.get_tracer(__name__)

            self._initialized = True
            logger.info(f"OpenTelemetry initialized for service: {self.service_name}")

        except Exception as e:
            logger.error(f"OpenTelemetry initialization failed: {e}")
            logger.debug(traceback.format_exc())
            self._initialized = False

    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized

    def start_span(self, name: str, kind: int = None,
                   attributes: Dict[str, Any] = None) -> trace.Span:
        """
        开始新的跨度

        Args:
            name: 跨度名称
            kind: 跨度类型
            attributes: 附加属性

        Returns:
            Span 对象
        """
        if not self._initialized:
            # 如果未初始化，返回一个空的跨度对象以避免异常
            return _NullSpan()

        try:
            span_kind = kind or trace.SpanKind.INTERNAL
            span = self._tracer.start_span(name, kind=span_kind)

            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)

            return span

        except Exception as e:
            logger.warning(f"Failed to start span: {e}")
            return _NullSpan()

    def end_span(self, span: trace.Span, status: int = StatusCode.OK,
                description: str = None):
        """
        结束跨度

        Args:
            span: 跨度对象
            status: 状态码
            description: 状态描述
        """
        try:
            if span and not isinstance(span, _NullSpan):
                span.set_status(Status(status, description))
                span.end()
        except Exception as e:
            logger.warning(f"Failed to end span: {e}")

    def record_exception(self, span: trace.Span, exception: Exception,
                       attributes: Dict[str, Any] = None):
        """
        记录异常

        Args:
            span: 跨度对象
            exception: 异常对象
            attributes: 附加属性
        """
        try:
            if span and not isinstance(span, _NullSpan):
                span.record_exception(exception, attributes=attributes)
                span.set_status(Status(StatusCode.ERROR, str(exception)))
        except Exception as e:
            logger.warning(f"Failed to record exception: {e}")

    def trace_function(self, name: str = None,
                     attributes: Dict[str, Any] = None):
        """
        装饰器：自动追踪函数调用

        Args:
            name: 跨度名称（默认使用函数名）
            attributes: 附加属性

        Returns:
            装饰器函数
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                span_name = name or func.__name__
                span = self.start_span(span_name, attributes=attributes)

                try:
                    result = func(*args, **kwargs)
                    self.end_span(span)
                    return result
                except Exception as e:
                    self.record_exception(span, e)
                    self.end_span(span, StatusCode.ERROR, str(e))
                    raise

            return wrapper
        return decorator

    def trace_agent_execution(self, agent_id: str,
                             request_id: str = None,
                             task_id: str = None) -> trace.Span:
        """
        追踪Agent执行过程

        Args:
            agent_id: Agent ID
            request_id: 请求ID
            task_id: 任务ID

        Returns:
            跨度对象
        """
        attributes = {
            "agent.id": agent_id,
            "nanobot.version": "0.2.1"
        }

        if request_id:
            attributes["request.id"] = request_id

        if task_id:
            attributes["task.id"] = task_id

        return self.start_span("agent_execution",
                             kind=trace.SpanKind.SERVER,
                             attributes=attributes)

    def trace_llm_call(self, provider: str, model: str,
                      request_id: str = None) -> trace.Span:
        """
        追踪LLM调用

        Args:
            provider: LLM提供商
            model: 模型名称
            request_id: 请求ID

        Returns:
            跨度对象
        """
        attributes = {
            "llm.provider": provider,
            "llm.model": model,
            "nanobot.version": "0.2.1"
        }

        if request_id:
            attributes["request.id"] = request_id

        return self.start_span("llm_call",
                             kind=trace.SpanKind.CLIENT,
                             attributes=attributes)

    def trace_tool_call(self, tool_name: str,
                       request_id: str = None) -> trace.Span:
        """
        追踪工具调用

        Args:
            tool_name: 工具名称
            request_id: 请求ID

        Returns:
            跨度对象
        """
        attributes = {
            "tool.name": tool_name,
            "nanobot.version": "0.2.1"
        }

        if request_id:
            attributes["request.id"] = request_id

        return self.start_span(f"tool_{tool_name}",
                             kind=trace.SpanKind.CLIENT,
                             attributes=attributes)

    def trace_task_execution(self, task_id: str,
                           task_name: str = None) -> trace.Span:
        """
        追踪任务执行

        Args:
            task_id: 任务ID
            task_name: 任务名称

        Returns:
            跨度对象
        """
        attributes = {
            "task.id": task_id,
            "nanobot.version": "0.2.1"
        }

        if task_name:
            attributes["task.name"] = task_name

        return self.start_span(f"task_{task_id}",
                             kind=trace.SpanKind.INTERNAL,
                             attributes=attributes)

    def shutdown(self):
        """关闭追踪器"""
        try:
            if self._provider:
                self._provider.shutdown()
                self._initialized = False
                logger.info("OpenTelemetry tracer shutdown")
        except Exception as e:
            logger.warning(f"Failed to shutdown tracer: {e}")


class _NullSpan:
    """空跨度实现，用于在OpenTelemetry未初始化时避免异常"""

    def __init__(self):
        self._attributes = {}

    def set_attribute(self, key, value):
        self._attributes[key] = value

    def get_attribute(self, key):
        return self._attributes.get(key)

    def set_status(self, status, description=None):
        pass

    def end(self):
        pass

    def record_exception(self, exception, attributes=None):
        pass
