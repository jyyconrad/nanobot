"""
MainAgent 集成测试
"""

from unittest.mock import AsyncMock, patch

import pytest

from nanobot.agent.main_agent import MainAgent


@pytest.mark.asyncio
async def test_main_agent_integration():
    """
    测试完整的消息处理流程
    """
    # 创建 MainAgent 实例
    agent = MainAgent("test-session-1")

    # 模拟消息处理
    with patch.object(agent, "_handle_new_message", new_callable=AsyncMock) as mock_handle:
        mock_handle.return_value = "这是一个测试响应"

        # 测试处理消息
        response = await agent.process_message("测试消息")

        # 验证结果
        assert response == "这是一个测试响应"
        mock_handle.assert_called_once_with("测试消息")


@pytest.mark.asyncio
async def test_subagent_coordination():
    """
    测试子代理协调
    """
    # 创建 MainAgent 实例
    agent = MainAgent("test-session-2")

    # 模拟子代理管理器
    with patch.object(agent.subagent_manager, "spawn_subagent", new_callable=AsyncMock) as mock_spawn:
        mock_spawn.return_value = None

        with patch.object(agent, "_handle_new_message", new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = "子代理正在处理任务"

            # 测试处理需要子代理的消息
            response = await agent.process_message("执行复杂任务")

            # 验证结果
            assert "子代理" in response


@pytest.mark.asyncio
async def test_context_management():
    """
    测试上下文管理
    """
    # 创建 MainAgent 实例
    agent = MainAgent("test-session-3")

    # 直接模拟 _plan_task 方法内部的 build_context 调用
    with patch.object(agent.context_manager, "build_context", new_callable=AsyncMock) as mock_build:
        mock_build.return_value = ({"user_input": "测试消息"}, None)

        # 模拟任务规划结果
        with patch.object(type(agent.task_planner), "plan_task", new_callable=AsyncMock) as mock_plan_task:
            mock_plan_task.return_value = "计划结果"

            # 模拟决策
            with patch.object(agent, "_make_decision", new_callable=AsyncMock) as mock_decide:
                mock_decide.return_value = type('MockDecision', (), {'action': 'reply', 'message': '已处理测试消息'})()

                # 测试处理消息
                response = await agent.process_message("测试消息")

                # 验证结果
                assert "已处理" in response
                mock_build.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling():
    """
    测试错误处理
    """
    # 创建 MainAgent 实例
    agent = MainAgent("test-session-4")

    # 模拟错误
    with patch.object(agent, "_handle_new_message", new_callable=AsyncMock) as mock_handle:
        mock_handle.side_effect = Exception("测试错误")

        # 测试处理消息（应该会被适当处理）
        response = await agent.process_message("引发错误的消息")

        # 验证结果
        assert "处理消息时发生错误" in response


@pytest.mark.asyncio
async def test_task_cancellation():
    """
    测试任务取消
    """
    # 创建 MainAgent 实例
    agent = MainAgent("test-session-5")

    # 模拟任务取消
    with patch.object(agent, "_handle_task_cancellation", new_callable=AsyncMock) as mock_cancel:
        mock_cancel.return_value = "任务已取消"

        with patch.object(type(agent.task_planner.cancellation_detector), "is_cancellation",
                          new_callable=AsyncMock) as mock_is_cancel:
            mock_is_cancel.return_value = True

            # 设置当前任务以触发处理现有任务逻辑
            agent.state.current_task = "test-task"

            response = await agent.process_message("取消任务")

            assert "任务已取消" in response
            mock_cancel.assert_called_once()


@pytest.mark.asyncio
async def test_task_correction():
    """
    测试任务修正
    """
    # 创建 MainAgent 实例
    agent = MainAgent("test-session-6")

    # 模拟任务修正
    with patch.object(agent, "_handle_task_correction", new_callable=AsyncMock) as mock_correct:
        mock_correct.return_value = "任务已修正"

        with patch.object(type(agent.task_planner.correction_detector), "detect_correction",
                          new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = "修正内容"

            # 设置当前任务以触发处理现有任务逻辑
            agent.state.current_task = "test-task"

            response = await agent.process_message("修正任务")

            assert "任务已修正" in response
            mock_correct.assert_called_once()
