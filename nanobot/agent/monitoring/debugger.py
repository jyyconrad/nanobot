"""
调试和诊断模块
"""

import traceback
import json
import time
from typing import Optional, Dict, Any, List

from loguru import logger


class Debugger:
    """调试和诊断器"""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self._breakpoints = set()
        self._trace_stack = []
        self._request_tracker = {}
        self._response_tracker = {}

    def enable(self):
        """启用调试模式"""
        self.enabled = True
        logger.debug("Debug mode enabled")

    def disable(self):
        """禁用调试模式"""
        self.enabled = False
        self.clear_trace_stack()
        logger.debug("Debug mode disabled")

    def is_enabled(self) -> bool:
        """检查是否启用调试模式"""
        return self.enabled

    def set_breakpoint(self, location: str):
        """
        设置断点

        Args:
            location: 断点位置（如 "file:line" 或函数名）
        """
        self._breakpoints.add(location)
        logger.debug(f"Breakpoint set at: {location}")

    def clear_breakpoint(self, location: str):
        """
        清除断点

        Args:
            location: 断点位置
        """
        self._breakpoints.discard(location)
        logger.debug(f"Breakpoint cleared at: {location}")

    def clear_all_breakpoints(self):
        """清除所有断点"""
        self._breakpoints.clear()
        logger.debug("All breakpoints cleared")

    def get_breakpoints(self) -> List[str]:
        """获取所有断点"""
        return list(self._breakpoints)

    def check_breakpoint(self, location: str) -> bool:
        """
        检查是否在断点位置

        Args:
            location: 位置字符串

        Returns:
            是否在断点位置
        """
        return location in self._breakpoints

    def trace(self, message: str, location: str = None,
             request_id: str = None, task_id: str = None,
             **kwargs):
        """
        记录跟踪信息

        Args:
            message: 跟踪信息
            location: 代码位置
            request_id: 请求ID
            task_id: 任务ID
            **kwargs: 附加信息
        """
        if not self.enabled:
            return

        entry = {
            "timestamp": time.time(),
            "message": message,
            "location": location,
            "request_id": request_id,
            "task_id": task_id,
            **kwargs
        }

        self._trace_stack.append(entry)
        logger.debug(json.dumps(entry, ensure_ascii=False))

    def clear_trace_stack(self):
        """清除跟踪堆栈"""
        self._trace_stack.clear()

    def get_trace_stack(self) -> List[Dict[str, Any]]:
        """获取跟踪堆栈"""
        return self._trace_stack.copy()

    def record_request(self, request_id: str, method: str,
                     url: str, headers: Dict[str, str],
                     body: Any, timestamp: float = None):
        """
        记录请求信息

        Args:
            request_id: 请求ID
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            body: 请求体
            timestamp: 时间戳
        """
        self._request_tracker[request_id] = {
            "timestamp": timestamp or time.time(),
            "method": method,
            "url": url,
            "headers": headers,
            "body": body
        }

    def record_response(self, request_id: str, status_code: int,
                      headers: Dict[str, str], body: Any,
                      timestamp: float = None):
        """
        记录响应信息

        Args:
            request_id: 请求ID
            status_code: 状态码
            headers: 响应头
            body: 响应体
            timestamp: 时间戳
        """
        self._response_tracker[request_id] = {
            "timestamp": timestamp or time.time(),
            "status_code": status_code,
            "headers": headers,
            "body": body
        }

    def get_request_response_trace(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        获取请求/响应追踪

        Args:
            request_id: 请求ID

        Returns:
            包含请求和响应信息的字典，或者None
        """
        if request_id not in self._request_tracker:
            return None

        result = {"request": self._request_tracker[request_id]}

        if request_id in self._response_tracker:
            result["response"] = self._response_tracker[request_id]
            result["latency"] = (
                result["response"]["timestamp"] - result["request"]["timestamp"]
            )

        return result

    def get_all_request_tracker(self) -> Dict[str, Any]:
        """获取所有请求追踪"""
        return self._request_tracker.copy()

    def get_all_response_tracker(self) -> Dict[str, Any]:
        """获取所有响应追踪"""
        return self._response_tracker.copy()

    def clear_request_tracker(self):
        """清除请求追踪"""
        self._request_tracker.clear()

    def clear_response_tracker(self):
        """清除响应追踪"""
        self._response_tracker.clear()

    def clear_all_tracking(self):
        """清除所有追踪信息"""
        self.clear_trace_stack()
        self.clear_request_tracker()
        self.clear_response_tracker()

    def get_exception_info(self, exc: Exception) -> Dict[str, Any]:
        """
        获取异常信息

        Args:
            exc: 异常对象

        Returns:
            包含异常详情的字典
        """
        return {
            "type": type(exc).__name__,
            "message": str(exc),
            "stack_trace": traceback.format_exc(),
            "traceback_list": traceback.format_stack()
        }

    def log_exception(self, exc: Exception, request_id: str = None,
                     task_id: str = None, **kwargs):
        """
        记录异常信息

        Args:
            exc: 异常对象
            request_id: 请求ID
            task_id: 任务ID
            **kwargs: 附加信息
        """
        info = self.get_exception_info(exc)
        info.update({
            "request_id": request_id,
            "task_id": task_id,
            **kwargs
        })

        logger.error(json.dumps(info, ensure_ascii=False))
        return info

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.enabled:
            return {"error": "Debug mode not enabled"}

        request_count = len(self._request_tracker)
        response_count = len(self._response_tracker)
        completed_requests = []

        for request_id in self._request_tracker:
            if request_id in self._response_tracker:
                latency = (self._response_tracker[request_id]["timestamp"] -
                          self._request_tracker[request_id]["timestamp"])
                completed_requests.append(latency)

        return {
            "debug_mode": self.enabled,
            "breakpoints": self.get_breakpoints(),
            "trace_count": len(self._trace_stack),
            "requests": {
                "total": request_count,
                "responded": response_count,
                "pending": request_count - response_count
            },
            "response_times": {
                "count": len(completed_requests),
                "avg": sum(completed_requests) / len(completed_requests) if completed_requests else 0,
                "min": min(completed_requests) if completed_requests else 0,
                "max": max(completed_requests) if completed_requests else 0
            }
        }
