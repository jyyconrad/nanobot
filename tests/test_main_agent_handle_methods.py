"""
MainAgent 处理方法的单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from nanobot.agent.main_agent import MainAgent


@pytest.mark.asyncio
async def test_handle_chat_message_with_llm_response():
    """测试处理聊天消息的方法"""
    # 创建 MainAgent 实例
    agent = MainAgent(session_id="test-session")
    
    # 模拟 context_manager.get_history() 方法返回空历史
    agent.context_manager.get_history = Mock(return_value=[])
    
    # 模拟 LiteLLMProvider 的 chat 方法
    with patch("nanobot.providers.litellm_provider.LiteLLMProvider") as mock_provider_cls:
        mock_provider = Mock()
        mock_response = Mock()
        mock_response.has_tool_calls = False
        mock_response.content = "这是一个测试回复"
        mock_provider.chat = AsyncMock(return_value=mock_response)
        mock_provider_cls.return_value = mock_provider
        
        # 调用测试方法
        response = await agent._handle_chat_message("你好，这是测试消息")
        
        # 验证返回值
        assert isinstance(response, str)
        assert len(response) > 0
        assert "测试回复" in response


@pytest.mark.asyncio
async def test_handle_chat_message_with_tool_calls():
    """测试处理包含工具调用的聊天消息"""
    # 创建 MainAgent 实例
    agent = MainAgent(session_id="test-session")
    
    # 模拟 context_manager.get_history() 方法返回空历史
    agent.context_manager.get_history = Mock(return_value=[])
    
    # 模拟工具调用响应
    with patch("nanobot.providers.litellm_provider.LiteLLMProvider") as mock_provider_cls:
        mock_provider = Mock()
        mock_response = Mock()
        mock_response.has_tool_calls = True
        mock_response.tool_calls = [
            Mock(name="read_file", arguments={"path": "/test.txt"})
        ]
        mock_provider.chat = AsyncMock(return_value=mock_response)
        mock_provider_cls.return_value = mock_provider
        
        # 模拟 _handle_tool_calls 方法
        agent._handle_tool_calls = AsyncMock(return_value="工具调用完成")
        
        # 调用测试方法
        response = await agent._handle_chat_message("读取测试文件")
        
        # 验证返回值
        assert isinstance(response, str)
        assert "工具调用完成" in response


@pytest.mark.asyncio
async def test_handle_tool_calls():
    """测试处理工具调用的方法"""
    # 创建 MainAgent 实例
    agent = MainAgent(session_id="test-session")
    
    # 模拟 agent_loop 和工具
    mock_tool = Mock()
    mock_tool.execute = AsyncMock(return_value="测试内容")
    
    mock_tools = Mock()
    mock_tools.get = Mock(return_value=mock_tool)
    
    agent.agent_loop = Mock()
    agent.agent_loop.tools = mock_tools
    
    # 模拟包含工具调用的响应
    mock_response = Mock()
    mock_response.has_tool_calls = True
    mock_response.tool_calls = [
        Mock(name="read_file", arguments={"path": "/test.txt"})
    ]
    
    # 模拟再次调用 LLM 的响应（无工具调用）
    with patch("nanobot.providers.litellm_provider.LiteLLMProvider") as mock_provider_cls:
        mock_provider = Mock()
        final_response = Mock()
        final_response.has_tool_calls = False
        final_response.content = "工具调用完成，已读取测试文件"
        mock_provider.chat = AsyncMock(return_value=final_response)
        mock_provider_cls.return_value = mock_provider
        
        # 调用测试方法
        result = await agent._handle_tool_calls(mock_response, [])
        
        # 验证返回值
        assert isinstance(result, str)
        assert len(result) > 0


@pytest.mark.asyncio
async def test_get_status():
    """测试获取代理状态的方法"""
    # 创建 MainAgent 实例
    agent = MainAgent(session_id="test-session")
    
    # 设置一些状态
    agent.state.current_task = "测试任务"
    agent.state.subagent_tasks = {"task1": "任务1"}
    agent.state.subagent_results = {"task1": "结果1"}
    agent.state.is_processing = False
    agent.state.context_stats = {"length": 100}
    agent.state.subagent_states = {
        "task1": Mock(status="RUNNING")
    }
    
    # 调用测试方法
    status = await agent.get_status()
    
    # 验证返回值
    assert isinstance(status, dict)
    assert "session_id" in status
    assert "current_task" in status
    assert "subagent_tasks" in status
    assert "subagent_count" in status
    assert "subagent_results" in status
    assert "is_processing" in status
    assert "context_stats" in status
    assert "running_count" in status
    
    assert status["session_id"] == "test-session"
    assert status["current_task"] == "测试任务"
    assert len(status["subagent_tasks"]) == 1
    assert status["subagent_count"] == 1
    assert len(status["subagent_results"]) == 1
    assert status["is_processing"] == False
    assert status["running_count"] == 1


@pytest.mark.asyncio
async def test_cleanup_task():
    """测试清理任务的方法"""
    # 创建 MainAgent 实例
    agent = MainAgent(session_id="test-session")
    
    # 设置一些状态
    agent.state.current_task = "测试任务"
    agent.state.subagent_tasks = {"task1": "任务1"}
    agent.state.subagent_results = {"task1": "结果1"}
    agent.state.subagent_states = {"task1": "状态1"}
    
    # 调用测试方法
    await agent._cleanup_task()
    
    # 验证状态已被清理
    assert agent.state.current_task is None
    assert len(agent.state.subagent_tasks) == 0
    assert len(agent.state.subagent_results) == 0
    assert len(agent.state.subagent_states) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
