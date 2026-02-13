"""
MessageBus 测试

测试 MessageBus 的核心功能，包括：
- 发布/订阅
- 子任务结果汇报
- 状态同步
- 消息重试
"""

import asyncio
from datetime import datetime

import pytest

from nanobot.agent.message_bus import MemoryBackend, MessageBus, RedisBackend
from nanobot.agent.message_schemas import (
    ControlMessage,
    MessageType,
    StatusUpdateMessage,
    TaskResultMessage,
)


@pytest.fixture
async def message_bus():
    """创建测试用的 MessageBus"""
    bus = MessageBus(backend_type="memory")
    await bus.initialize()
    yield bus
    await bus.shutdown()


@pytest.mark.asyncio
async def test_publish_subscribe(message_bus):
    """测试发布订阅功能"""
    received_messages = []

    async def callback(message):
        received_messages.append(message)

    # 订阅主题
    sub_id = await message_bus.subscribe("test.topic", callback)

    # 发布消息
    await message_bus.publish("test.topic", {"test": "data"})

    # 等待消息处理
    await asyncio.sleep(0.1)

    # 验证
    assert len(received_messages) == 1
    assert received_messages[0]["test"] == "data"

    # 取消订阅
    await message_bus.unsubscribe(sub_id)


@pytest.mark.asyncio
async def test_task_result_reporting(message_bus):
    """测试任务结果汇报"""
    # 模拟父代理接收结果
    received_results = []

    async def parent_callback(message):
        if message.get("message_type") == MessageType.TASK_RESULT:
            received_results.append(message)

    # 父代理订阅结果主题
    await message_bus.subscribe("agent.parent_agent.results", parent_callback)

    # 子代理汇报结果
    await message_bus.report_task_result(
        task_id="task_001",
        subagent_id="subagent_001",
        parent_agent_id="parent_agent",
        status="completed",
        result={"output": "任务完成"},
        logs=["开始执行", "执行中...", "完成"],
        execution_time=10.5,
    )

    # 等待消息处理
    await asyncio.sleep(0.1)

    # 验证
    assert len(received_results) == 1
    assert received_results[0]["task_id"] == "task_001"
    assert received_results[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_status_sync(message_bus):
    """测试状态同步"""
    status_updates = []

    async def status_callback(message):
        status_updates.append(message)

    # 订阅状态主题
    await message_bus.subscribe("agent.agent_001.status", status_callback)

    # 发送状态更新
    await message_bus.update_status(
        agent_id="agent_001",
        status="running",
        progress=0.5,
        current_task="处理数据",
        metadata={"cpu": "45%", "memory": "60%"},
    )

    # 等待处理
    await asyncio.sleep(0.1)

    # 验证
    assert len(status_updates) == 1
    assert status_updates[0]["status"] == "running"
    assert status_updates[0]["progress"] == 0.5


@pytest.mark.asyncio
async def test_control_command(message_bus):
    """测试控制命令"""
    control_commands = []

    async def control_callback(message):
        control_commands.append(message)

    # 订阅控制主题
    await message_bus.subscribe("agent.agent_002.control", control_callback)

    # 发送控制命令
    await message_bus.send_control_command(
        command="pause",
        target_agent_id="agent_002",
        source_agent_id="main_agent",
        parameters={"reason": "资源紧张"},
    )

    # 等待处理
    await asyncio.sleep(0.1)

    # 验证
    assert len(control_commands) == 1
    assert control_commands[0]["command"] == "pause"
    assert control_commands[0]["target_agent_id"] == "agent_002"


@pytest.mark.asyncio
async def test_message_retry():
    """测试消息重试机制"""
    bus = MessageBus(backend_type="memory")
    await bus.initialize()

    try:
        # 模拟发布失败后的重试
        attempt_count = 0

        class FailingBackend(MemoryBackend):
            async def publish(self, topic, message):
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count < 3:
                    raise Exception("模拟失败")
                return await super().publish(topic, message)

        bus._backend = FailingBackend()

        # 使用重试发布
        success = await bus.publish_with_retry(
            "test.topic", {"test": "data"}, max_retries=3
        )

        assert success is True
        assert attempt_count == 3  # 前两次失败，第三次成功

    finally:
        await bus.shutdown()


@pytest.mark.asyncio
async def test_multiple_subscribers(message_bus):
    """测试多个订阅者"""
    received_messages_1 = []
    received_messages_2 = []

    async def callback1(message):
        received_messages_1.append(message)

    async def callback2(message):
        received_messages_2.append(message)

    # 两个订阅者订阅同一主题
    sub_id1 = await message_bus.subscribe("test.multi", callback1)
    sub_id2 = await message_bus.subscribe("test.multi", callback2)

    # 发布消息
    await message_bus.publish("test.multi", {"data": "test"})

    # 等待处理
    await asyncio.sleep(0.1)

    # 验证两个订阅者都收到消息
    assert len(received_messages_1) == 1
    assert len(received_messages_2) == 1
    assert received_messages_1[0]["data"] == "test"
    assert received_messages_2[0]["data"] == "test"

    # 取消订阅
    await message_bus.unsubscribe(sub_id1)
    await message_bus.unsubscribe(sub_id2)


@pytest.mark.asyncio
async def test_request_response(message_bus):
    """测试请求-响应模式"""

    # 订阅请求主题并发送响应
    async def request_handler(message):
        if message.get("_request_id"):
            # 发送响应
            response_topic = message.get("_response_topic")
            if response_topic:
                await message_bus.publish(
                    response_topic,
                    {
                        "status": "success",
                        "data": "响应数据",
                        "_request_id": message["_request_id"],
                    },
                )

    await message_bus.subscribe("test.requests", request_handler)

    # 发送请求
    response = await message_bus.request(
        "test.requests", {"action": "test"}, timeout=5.0
    )

    # 验证响应
    assert response is not None
    assert response["status"] == "success"
    assert response["data"] == "响应数据"


@pytest.mark.skipif(True, reason="需要Redis服务器")
@pytest.mark.asyncio
async def test_redis_backend():
    """测试Redis后端（需要Redis服务器）"""
    try:
        bus = MessageBus(
            backend_type="redis", backend_config={"redis_url": "redis://localhost:6379"}
        )
        await bus.initialize()

        received_messages = []

        async def callback(message):
            received_messages.append(message)

        # 订阅
        sub_id = await bus.subscribe("test.redis", callback)

        # 发布
        await bus.publish("test.redis", {"test": "redis"})

        # 等待
        await asyncio.sleep(0.5)

        # 验证
        assert len(received_messages) == 1
        assert received_messages[0]["test"] == "redis"

        # 清理
        await bus.unsubscribe(sub_id)
        await bus.shutdown()

    except Exception as e:
        pytest.skip(f"Redis测试跳过: {e}")
