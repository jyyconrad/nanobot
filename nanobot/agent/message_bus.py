"""
MessageBus - 增强型消息总线

支持内存和Redis两种后端，提供子代理通信、状态同步、结果汇报功能。
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Set, Awaitable
from datetime import datetime

from nanobot.agent.message_schemas import (
    MessageType,
    TaskResultMessage,
    StatusUpdateMessage,
    ControlMessage,
    HeartbeatMessage,
    ErrorMessage,
    LogMessage,
    RequestMessage,
    ResponseMessage,
    parse_message,
)

logger = logging.getLogger(__name__)


class MessageBackend(ABC):
    """消息后端抽象基类"""

    @abstractmethod
    async def publish(self, topic: str, message: dict) -> bool:
        """发布消息到主题"""
        pass

    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        callback: Callable[[dict], Awaitable[None]]
    ) -> str:
        """订阅主题，返回订阅ID"""
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        pass

    @abstractmethod
    async def request(
        self,
        topic: str,
        message: dict,
        timeout: float = 30.0
    ) -> Optional[dict]:
        """发送请求并等待响应"""
        pass

    @abstractmethod
    async def close(self):
        """关闭后端连接"""
        pass


class MemoryBackend(MessageBackend):
    """内存消息后端"""

    def __init__(self):
        self._topics: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, Dict[str, Callable]] = {}
        self._response_handlers: Dict[str, asyncio.Queue] = {}
        self._running = True
        self._lock = asyncio.Lock()

    async def publish(self, topic: str, message: dict) -> bool:
        """发布消息到主题"""
        try:
            async with self._lock:
                # 获取或创建主题队列
                if topic not in self._topics:
                    self._topics[topic] = asyncio.Queue()

                queue = self._topics[topic]

            # 将消息放入队列
            await queue.put(message)

            # 通知订阅者
            await self._notify_subscribers(topic, message)

            return True

        except Exception as e:
            logger.error(f"发布消息失败: {e}")
            return False

    async def _notify_subscribers(self, topic: str, message: dict):
        """通知所有订阅者"""
        async with self._lock:
            subscribers = self._subscribers.get(topic, {}).copy()

        # 异步调用所有订阅者回调
        tasks = []
        for sub_id, callback in subscribers.items():
            task = asyncio.create_task(self._safe_callback(callback, message, sub_id))
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_callback(
        self,
        callback: Callable,
        message: dict,
        sub_id: str
    ):
        """安全地调用回调"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(message)
            else:
                callback(message)
        except Exception as e:
            logger.error(f"订阅者回调失败 [{sub_id}]: {e}")

    async def subscribe(
        self,
        topic: str,
        callback: Callable[[dict], Awaitable[None]]
    ) -> str:
        """订阅主题"""
        sub_id = f"{topic}:{uuid.uuid4().hex[:8]}"

        async with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = {}

            self._subscribers[topic][sub_id] = callback

        logger.debug(f"已订阅主题: {topic}, ID: {sub_id}")
        return sub_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        try:
            # 解析主题和ID
            parts = subscription_id.split(":")
            if len(parts) != 2:
                logger.error(f"无效的订阅ID格式: {subscription_id}")
                return False

            topic = parts[0]

            async with self._lock:
                if topic in self._subscribers:
                    if subscription_id in self._subscribers[topic]:
                        del self._subscribers[topic][subscription_id]
                        logger.debug(f"已取消订阅: {subscription_id}")
                        return True

            logger.warning(f"未找到订阅: {subscription_id}")
            return False

        except Exception as e:
            logger.error(f"取消订阅失败: {e}")
            return False

    async def request(
        self,
        topic: str,
        message: dict,
        timeout: float = 30.0
    ) -> Optional[dict]:
        """发送请求并等待响应"""
        # 生成请求ID
        request_id = f"req:{uuid.uuid4().hex}"
        message["_request_id"] = request_id

        # 创建响应队列
        response_queue = asyncio.Queue()

        async with self._lock:
            self._response_handlers[request_id] = response_queue

        try:
            # 发送请求
            await self.publish(topic, message)

            # 等待响应
            try:
                response = await asyncio.wait_for(
                    response_queue.get(),
                    timeout=timeout
                )
                return response
            except asyncio.TimeoutError:
                logger.warning(f"请求超时: {request_id}")
                return None

        finally:
            # 清理
            async with self._lock:
                if request_id in self._response_handlers:
                    del self._response_handlers[request_id]

    async def send_response(self, request_id: str, response: dict):
        """发送响应"""
        async with self._lock:
            if request_id in self._response_handlers:
                queue = self._response_handlers[request_id]
                await queue.put(response)

    async def close(self):
        """关闭后端"""
        self._running = False

        # 清理队列
        for queue in self._topics.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

        self._topics.clear()
        self._subscribers.clear()
        self._response_handlers.clear()


class RedisBackend(MessageBackend):
    """Redis消息后端"""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis = None
        self._pubsub = None
        self._subscriptions: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def connect(self):
        """连接到Redis"""
        try:
            import redis.asyncio as aioredis

            self._redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True
            )
            self._pubsub = self._redis.pubsub()

            logger.info(f"已连接到Redis: {self.redis_url}")

        except ImportError:
            raise RuntimeError("redis-py未安装，请运行: pip install redis")
        except Exception as e:
            raise RuntimeError(f"连接Redis失败: {e}")

    async def publish(self, topic: str, message: dict) -> bool:
        """发布消息到主题"""
        try:
            if not self._redis:
                raise RuntimeError("Redis未连接")

            # 序列化消息
            message_json = json.dumps(message, default=str)

            # 发布到Redis频道
            await self._redis.publish(topic, message_json)

            return True

        except Exception as e:
            logger.error(f"Redis发布失败: {e}")
            return False

    async def subscribe(
        self,
        topic: str,
        callback: Callable[[dict], Awaitable[None]]
    ) -> str:
        """订阅主题"""
        try:
            if not self._pubsub:
                raise RuntimeError("Redis pubsub未初始化")

            # 生成订阅ID
            sub_id = f"{topic}:{uuid.uuid4().hex[:8]}"

            # 订阅Redis频道
            await self._pubsub.subscribe(topic)

            # 存储回调
            async with self._lock:
                self._subscriptions[sub_id] = {
                    "topic": topic,
                    "callback": callback
                }

            # 启动消息监听
            asyncio.create_task(self._listen_for_messages())

            logger.debug(f"已订阅Redis主题: {topic}, ID: {sub_id}")
            return sub_id

        except Exception as e:
            logger.error(f"Redis订阅失败: {e}")
            raise

    async def _listen_for_messages(self):
        """监听Redis消息"""
        try:
            if not self._pubsub:
                return

            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data = message["data"]

                    try:
                        # 解析消息
                        message_dict = json.loads(data)

                        # 找到对应的回调
                        async with self._lock:
                            matching_subs = [
                                sub_info for sub_id, sub_info in self._subscriptions.items()
                                if sub_info["topic"] == channel
                            ]

                        # 调用所有匹配的回调
                        for sub_info in matching_subs:
                            callback = sub_info["callback"]
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(message_dict)
                                else:
                                    callback(message_dict)
                            except Exception as e:
                                logger.error(f"回调执行失败: {e}")

                    except json.JSONDecodeError:
                        logger.error(f"消息JSON解析失败: {data}")

        except Exception as e:
            logger.error(f"Redis消息监听失败: {e}")

    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        try:
            async with self._lock:
                if subscription_id not in self._subscriptions:
                    logger.warning(f"未找到订阅: {subscription_id}")
                    return False

                sub_info = self._subscriptions[subscription_id]
                topic = sub_info["topic"]

                # 从存储中移除
                del self._subscriptions[subscription_id]

            # 检查是否还有其他订阅使用此主题
            async with self._lock:
                other_subs = [
                    s for s in self._subscriptions.values()
                    if s["topic"] == topic
                ]

            # 如果没有其他订阅，取消订阅Redis频道
            if not other_subs and self._pubsub:
                await self._pubsub.unsubscribe(topic)

            logger.debug(f"已取消订阅: {subscription_id}")
            return True

        except Exception as e:
            logger.error(f"取消订阅失败: {e}")
            return False

    async def request(
        self,
        topic: str,
        message: dict,
        timeout: float = 30.0
    ) -> Optional[dict]:
        """发送请求并等待响应"""
        # Redis实现使用临时响应主题
        request_id = f"req:{uuid.uuid4().hex}"
        response_topic = f"{topic}:response:{request_id}"

        message["_request_id"] = request_id
        message["_response_topic"] = response_topic

        # 创建响应等待队列
        response_queue = asyncio.Queue()

        # 订阅响应主题
        sub_id = await self.subscribe(response_topic, response_queue.put)

        try:
            # 发送请求
            await self.publish(topic, message)

            # 等待响应
            try:
                response = await asyncio.wait_for(
                    response_queue.get(),
                    timeout=timeout
                )
                return response
            except asyncio.TimeoutError:
                logger.warning(f"请求超时: {request_id}")
                return None
        finally:
            # 取消订阅
            await self.unsubscribe(sub_id)

    async def close(self):
        """关闭后端连接"""
        try:
            # 取消所有订阅
            if self._pubsub:
                await self._pubsub.unsubscribe()
                await self._pubsub.close()

            # 关闭Redis连接
            if self._redis:
                await self._redis.close()

            self._subscriptions.clear()
            logger.info("Redis后端已关闭")

        except Exception as e:
            logger.error(f"关闭Redis后端失败: {e}")


class MessageBus:
    """
    增强型消息总线
    支持内存和Redis两种后端
    提供子代理通信、状态同步、结果汇报功能
    """

    def __init__(
        self,
        backend_type: str = "memory",
        backend_config: Optional[dict] = None,
        enable_ack: bool = True,
        retry_policy: Optional[dict] = None
    ):
        self.backend_type = backend_type
        self.backend_config = backend_config or {}
        self.enable_ack = enable_ack
        self.retry_policy = retry_policy or {
            "max_retries": 3,
            "backoff_factor": 2,
            "max_delay": 60
        }

        self._backend: Optional[MessageBackend] = None
        self._pending_acks: Dict[str, asyncio.Future] = {}
        self._running = False
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化消息总线"""
        if self.backend_type == "memory":
            self._backend = MemoryBackend()
        elif self.backend_type == "redis":
            self._backend = RedisBackend(**self.backend_config)
            await self._backend.connect()
        else:
            raise ValueError(f"未知的后端类型: {self.backend_type}")

        self._running = True
        logger.info(f"消息总线已初始化，后端: {self.backend_type}")

    async def shutdown(self):
        """关闭消息总线"""
        self._running = False

        # 清理挂起的确认
        for future in self._pending_acks.values():
            if not future.done():
                future.cancel()

        self._pending_acks.clear()

        # 关闭后端
        if self._backend:
            await self._backend.close()
            self._backend = None

        logger.info("消息总线已关闭")

    # ===== 子代理通信功能 =====

    async def report_task_result(
        self,
        task_id: str,
        subagent_id: str,
        parent_agent_id: str,
        status: str,
        result: dict,
        logs: List[str],
        execution_time: float
    ) -> bool:
        """汇报子任务结果"""
        message = TaskResultMessage(
            task_id=task_id,
            subagent_id=subagent_id,
            parent_agent_id=parent_agent_id,
            status=status,
            result=result,
            logs=logs,
            execution_time=execution_time
        )

        topic = f"agent.{parent_agent_id}.results"

        if self.enable_ack:
            return await self.publish_with_ack(topic, message.model_dump())
        else:
            return await self.publish(topic, message.model_dump())

    async def update_status(
        self,
        agent_id: str,
        status: str,
        progress: float,
        current_task: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """更新代理状态"""
        message = StatusUpdateMessage(
            agent_id=agent_id,
            status=status,
            progress=progress,
            current_task=current_task,
            metadata=metadata or {}
        )

        topic = f"agent.{agent_id}.status"

        if self.enable_ack:
            return await self.publish_with_ack(topic, message.model_dump())
        else:
            return await self.publish(topic, message.model_dump())

    async def send_control_command(
        self,
        command: str,
        target_agent_id: str,
        source_agent_id: str,
        parameters: Optional[dict] = None
    ) -> bool:
        """发送控制命令"""
        message = ControlMessage(
            command=command,
            target_agent_id=target_agent_id,
            source_agent_id=source_agent_id,
            parameters=parameters or {}
        )

        topic = f"agent.{target_agent_id}.control"

        if self.enable_ack:
            return await self.publish_with_ack(topic, message.model_dump())
        else:
            return await self.publish(topic, message.model_dump())

    # ===== 基础消息操作 =====

    async def publish(self, topic: str, message: dict) -> bool:
        """发布消息到主题"""
        if not self._backend:
            raise RuntimeError("消息总线未初始化")

        try:
            return await self._backend.publish(topic, message)
        except Exception as e:
            logger.error(f"发布消息失败: {e}")
            return False

    async def subscribe(
        self,
        topic: str,
        callback: Callable[[dict], Awaitable[None]]
    ) -> str:
        """订阅主题"""
        if not self._backend:
            raise RuntimeError("消息总线未初始化")

        try:
            subscription_id = await self._backend.subscribe(topic, callback)
            logger.info(f"已订阅主题: {topic}, ID: {subscription_id}")
            return subscription_id
        except Exception as e:
            logger.error(f"订阅失败: {e}")
            raise

    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        if not self._backend:
            raise RuntimeError("消息总线未初始化")

        try:
            return await self._backend.unsubscribe(subscription_id)
        except Exception as e:
            logger.error(f"取消订阅失败: {e}")
            return False

    async def request(
        self,
        topic: str,
        message: dict,
        timeout: float = 30.0
    ) -> Optional[dict]:
        """发送请求并等待响应"""
        if not self._backend:
            raise RuntimeError("消息总线未初始化")

        try:
            return await self._backend.request(topic, message, timeout)
        except Exception as e:
            logger.error(f"请求失败: {e}")
            return None

    # ===== 可靠传输功能 =====

    async def publish_with_ack(
        self,
        topic: str,
        message: dict,
        timeout: float = 30.0
    ) -> bool:
        """发布消息并等待确认"""
        message_id = str(uuid.uuid4())
        message["_message_id"] = message_id
        message["_requires_ack"] = True

        # 创建等待Future
        future = asyncio.get_event_loop().create_future()

        async with self._lock:
            self._pending_acks[message_id] = future

        try:
            # 发布消息
            success = await self.publish(topic, message)
            if not success:
                return False

            # 等待确认
            await asyncio.wait_for(future, timeout=timeout)
            return True

        except asyncio.TimeoutError:
            logger.warning(f"消息确认超时: {message_id}")
            return False
        except Exception as e:
            logger.error(f"发布消息失败: {e}")
            return False
        finally:
            # 清理
            async with self._lock:
                if message_id in self._pending_acks:
                    del self._pending_acks[message_id]

    async def handle_ack(self, message_id: str):
        """处理消息确认"""
        async with self._lock:
            if message_id in self._pending_acks:
                future = self._pending_acks[message_id]
                if not future.done():
                    future.set_result(True)

    async def publish_with_retry(
        self,
        topic: str,
        message: dict,
        max_retries: int = 3
    ) -> bool:
        """带重试的消息发布"""
        for attempt in range(max_retries):
            try:
                success = await self.publish(topic, message)
                if success:
                    return True

                # 重试
                if attempt < max_retries - 1:
                    delay = self.retry_policy["backoff_factor"] ** attempt
                    delay = min(delay, self.retry_policy["max_delay"])
                    logger.warning(f"消息发布失败，{delay}秒后重试...")
                    await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"发布消息异常: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)

        logger.error(f"消息发布失败，已重试{max_retries}次")
        return False
