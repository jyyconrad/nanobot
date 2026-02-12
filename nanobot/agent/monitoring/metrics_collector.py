"""
性能指标收集模块
"""

import time
import psutil
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict


@dataclass
class LLMCallMetrics:
    """LLM调用指标"""
    provider: str
    model: str
    call_count: int = 0
    total_latency: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    success_count: int = 0
    error_count: int = 0

    def record_call(self, latency: float, prompt_tokens: int,
                   completion_tokens: int, cost: float = 0.0, success: bool = True):
        """记录LLM调用"""
        self.call_count += 1
        self.total_latency += latency
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.cost += cost
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

    def get_avg_latency(self) -> float:
        """获取平均延迟"""
        return self.total_latency / self.call_count if self.call_count > 0 else 0.0

    def get_token_throughput(self) -> float:
        """获取token吞吐量（token/秒）"""
        return self.total_tokens / self.total_latency if self.total_latency > 0 else 0.0

    def get_success_rate(self) -> float:
        """获取成功率"""
        return self.success_count / self.call_count if self.call_count > 0 else 0.0


@dataclass
class ToolUseMetrics:
    """工具使用指标"""
    tool_name: str
    call_count: int = 0
    total_execution_time: float = 0.0
    success_count: int = 0
    error_count: int = 0
    input_size: int = 0
    output_size: int = 0

    def record_use(self, execution_time: float, success: bool = True,
                   input_size: int = 0, output_size: int = 0):
        """记录工具使用"""
        self.call_count += 1
        self.total_execution_time += execution_time
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        self.input_size += input_size
        self.output_size += output_size

    def get_avg_execution_time(self) -> float:
        """获取平均执行时间"""
        return self.total_execution_time / self.call_count if self.call_count > 0 else 0.0

    def get_success_rate(self) -> float:
        """获取成功率"""
        return self.success_count / self.call_count if self.call_count > 0 else 0.0


@dataclass
class ContextMetrics:
    """上下文使用指标"""
    total_tokens: int = 0
    compression_count: int = 0
    compression_ratio_sum: float = 0.0
    hit_count: int = 0
    miss_count: int = 0
    cache_size: int = 0

    def record_compression(self, original_tokens: int, compressed_tokens: int):
        """记录上下文压缩"""
        self.compression_count += 1
        ratio = compressed_tokens / original_tokens if original_tokens > 0 else 0
        self.compression_ratio_sum += ratio

    def record_cache_access(self, hit: bool):
        """记录缓存访问"""
        if hit:
            self.hit_count += 1
        else:
            self.miss_count += 1

    def get_avg_compression_ratio(self) -> float:
        """获取平均压缩率"""
        return self.compression_ratio_sum / self.compression_count if self.compression_count > 0 else 0.0

    def get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0


class MetricsCollector:
    """性能指标收集器"""

    def __init__(self):
        self._llm_metrics: Dict[str, LLMCallMetrics] = defaultdict(lambda: LLMCallMetrics("", ""))
        self._tool_metrics: Dict[str, ToolUseMetrics] = defaultdict(lambda: ToolUseMetrics(""))
        self._context_metrics = ContextMetrics()
        self._system_metrics = {
            "cpu": {"usage": 0.0, "count": 0, "avg": 0.0},
            "memory": {"usage": 0.0, "count": 0, "avg": 0.0},
            "disk": {"usage": 0.0, "count": 0, "avg": 0.0}
        }
        self._start_time = time.time()

    def record_llm_call(self, provider: str, model: str, latency: float,
                      prompt_tokens: int, completion_tokens: int,
                      cost: float = 0.0, success: bool = True):
        """记录LLM调用"""
        key = f"{provider}:{model}"
        if key not in self._llm_metrics:
            self._llm_metrics[key] = LLMCallMetrics(provider, model)

        self._llm_metrics[key].record_call(
            latency=latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            success=success
        )

    def record_tool_use(self, tool_name: str, execution_time: float,
                      success: bool = True, input_size: int = 0,
                      output_size: int = 0):
        """记录工具使用"""
        if tool_name not in self._tool_metrics:
            self._tool_metrics[tool_name] = ToolUseMetrics(tool_name)

        self._tool_metrics[tool_name].record_use(
            execution_time=execution_time,
            success=success,
            input_size=input_size,
            output_size=output_size
        )

    def record_context_compression(self, original_tokens: int, compressed_tokens: int):
        """记录上下文压缩"""
        self._context_metrics.record_compression(original_tokens, compressed_tokens)

    def record_context_cache_access(self, hit: bool):
        """记录上下文缓存访问"""
        self._context_metrics.record_cache_access(hit)

    def record_token_count(self, tokens: int):
        """记录上下文token数量"""
        self._context_metrics.total_tokens += tokens

    def update_system_metrics(self):
        """更新系统资源指标"""
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        # 更新CPU指标
        self._system_metrics["cpu"]["usage"] = cpu_usage
        self._system_metrics["cpu"]["count"] += 1
        self._system_metrics["cpu"]["avg"] = (
            (self._system_metrics["cpu"]["avg"] * (self._system_metrics["cpu"]["count"] - 1) + cpu_usage) /
            self._system_metrics["cpu"]["count"]
        )

        # 更新内存指标
        self._system_metrics["memory"]["usage"] = memory_usage
        self._system_metrics["memory"]["count"] += 1
        self._system_metrics["memory"]["avg"] = (
            (self._system_metrics["memory"]["avg"] * (self._system_metrics["memory"]["count"] - 1) + memory_usage) /
            self._system_metrics["memory"]["count"]
        )

        # 更新磁盘指标
        self._system_metrics["disk"]["usage"] = disk_usage
        self._system_metrics["disk"]["count"] += 1
        self._system_metrics["disk"]["avg"] = (
            (self._system_metrics["disk"]["avg"] * (self._system_metrics["disk"]["count"] - 1) + disk_usage) /
            self._system_metrics["disk"]["count"]
        )

    def get_llm_metrics(self) -> Dict[str, LLMCallMetrics]:
        """获取LLM调用指标"""
        return dict(self._llm_metrics)

    def get_tool_metrics(self) -> Dict[str, ToolUseMetrics]:
        """获取工具使用指标"""
        return dict(self._tool_metrics)

    def get_context_metrics(self) -> ContextMetrics:
        """获取上下文指标"""
        return self._context_metrics

    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统资源指标"""
        return self._system_metrics.copy()

    def get_summary(self) -> Dict[str, Any]:
        """获取完整指标摘要"""
        self.update_system_metrics()  # 确保获取最新指标

        return {
            "llm_calls": dict(self._llm_metrics),
            "tool_usage": dict(self._tool_metrics),
            "context": self._context_metrics,
            "system": self._system_metrics,
            "uptime": time.time() - self._start_time
        }

    def reset(self):
        """重置所有指标"""
        self._llm_metrics.clear()
        self._tool_metrics.clear()
        self._context_metrics = ContextMetrics()
        self._system_metrics = {
            "cpu": {"usage": 0.0, "count": 0, "avg": 0.0},
            "memory": {"usage": 0.0, "count": 0, "avg": 0.0},
            "disk": {"usage": 0.0, "count": 0, "avg": 0.0}
        }
        self._start_time = time.time()
