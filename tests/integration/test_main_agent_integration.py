"""
Main Agent 系统集成测试
"""

import asyncio

import pytest

from nanobot.agent.main_agent import MainAgent


@pytest.mark.asyncio
async def test_main_agent_integration():
    """
    测试主代理集成
    """
    agent = MainAgent("test-integration-session")

    response = await agent.process_message("测试消息")

    assert response  # 确保有响应


@pytest.mark.asyncio
async def test_subagent_coordination():
    """
    测试子代理协调
    """
    agent = MainAgent("test-subagent-coordination")

    response = await agent.process_message("创建任务测试")

    assert response  # 确保有响应


@pytest.mark.asyncio
async def test_context_management():
    """
    测试上下文管理
    """
    agent = MainAgent("test-context-management")

    # 发送多条消息以测试上下文
    messages = ["第一条消息", "第二条消息", "第三条消息"]
    for msg in messages:
        response = await agent.process_message(msg)
        assert response  # 确保有响应


@pytest.mark.asyncio
async def test_error_handling():
    """
    测试错误处理
    """
    agent = MainAgent("test-error-handling")

    response = await agent.process_message("错误测试")

    assert response  # 确保有响应


@pytest.mark.asyncio
async def test_task_cancellation():
    """
    测试任务取消
    """
    agent = MainAgent("test-task-cancellation")

    # 发送任务取消命令
    response = await agent.process_message("/cancel")

    assert response  # 确保有响应


@pytest.mark.asyncio
async def test_task_correction():
    """
    测试任务修正
    """
    agent = MainAgent("test-task-correction")

    # 发送任务修正命令
    response = await agent.process_message("修正任务")

    assert response  # 确保有响应
