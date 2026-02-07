"""
通道系统集成测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from nanobot.agent.main_agent import MainAgent


@pytest.mark.asyncio
async def test_channel_message_sending():
    """
    测试消息发送
    """
    agent = MainAgent("test-session-1")
    
    with patch.object(agent, "_handle_new_message", new_callable=AsyncMock) as mock_handle:
        mock_handle.return_value = "响应内容"
        
        response = await agent.process_message("发送消息测试")
        
        assert "响应内容" in response


@pytest.mark.asyncio
async def test_channel_message_reception():
    """
    测试消息接收
    """
    agent = MainAgent("test-session-2")
    
    with patch.object(agent, "_handle_new_message", new_callable=AsyncMock) as mock_handle:
        mock_handle.return_value = "已处理"
        
        response = await agent.process_message("接收消息测试")
        
        assert response == "已处理"
        mock_handle.assert_called_once_with("接收消息测试")


@pytest.mark.asyncio
async def test_channel_error_handling():
    """
    测试消息发送错误处理
    """
    agent = MainAgent("test-session-3")
    
    # 模拟处理消息时出现错误
    with patch.object(agent, "_handle_new_message", new_callable=AsyncMock) as mock_handle:
        mock_handle.side_effect = Exception("处理失败")
        
        response = await agent.process_message("触发错误测试")
        
        assert "处理消息时发生错误" in response


@pytest.mark.asyncio
async def test_channel_context_management():
    """
    测试上下文管理
    """
    agent = MainAgent("test-session-4")
    
    # 直接模拟 _plan_task 方法内部的 build_context 调用
    with patch.object(agent.context_manager, "build_context", new_callable=AsyncMock) as mock_build:
        mock_build.return_value = ({"user_input": "测试消息"}, None)
        
        # 模拟任务规划结果
        with patch.object(type(agent.task_planner), "plan_task", new_callable=AsyncMock) as mock_plan_task:
            mock_plan_task.return_value = "计划结果"
            
            # 模拟决策
            with patch.object(agent, "_make_decision", new_callable=AsyncMock) as mock_decide:
                mock_decide.return_value = type('MockDecision', (), {'action': 'reply', 'message': '已处理'})()
                
                await agent.process_message("测试消息")
                
                mock_build.assert_called_once()


@pytest.mark.asyncio
async def test_channel_message_queue():
    """
    测试消息队列处理
    """
    agent = MainAgent("test-session-5")
    
    with patch.object(agent, "_handle_new_message", new_callable=AsyncMock) as mock_process:
        mock_process.return_value = "已处理"
        
        # 发送多个消息
        tasks = []
        for i in range(3):
            task = asyncio.create_task(agent.process_message(f"消息 {i+1}"))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        assert all("已处理" in result for result in results)
        assert mock_process.call_count == 3
