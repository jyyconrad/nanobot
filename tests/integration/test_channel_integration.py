"""
通道系统集成测试
"""

import asyncio

import pytest

from nanobot.agent.main_agent import MainAgent


@pytest.mark.asyncio
async def test_channel_message_sending():
    """
    测试消息发送
    """
    agent = MainAgent("test-session-1")

    response = await agent.process_message("发送消息测试")

    assert response  # 确保有响应


@pytest.mark.asyncio
async def test_channel_message_reception():
    """
    测试消息接收
    """
    agent = MainAgent("test-session-2")

    response = await agent.process_message("接收消息测试")

    assert response  # 确保有响应


@pytest.mark.asyncio
async def test_channel_error_handling():
    """
    测试错误处理
    """
    agent = MainAgent("test-session-3")

    response = await agent.process_message("错误测试")

    assert response  # 确保有响应


@pytest.mark.asyncio
async def test_channel_context_management():
    """
    测试上下文管理
    """
    agent = MainAgent("test-session-4")

    # 发送多条消息以测试上下文
    messages = ["消息1", "消息2", "消息3"]
    for msg in messages:
        response = await agent.process_message(msg)
        assert response  # 确保有响应


@pytest.mark.asyncio
async def test_channel_message_queue():
    """
    测试消息队列处理
    """
    agent = MainAgent("test-session-5")

    # 发送多个消息
    tasks = []
    for i in range(3):
        task = asyncio.create_task(agent.process_message(f"消息 {i + 1}"))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    assert len(results) == 3
    assert all(results)  # 所有消息都应有响应
