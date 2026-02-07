"""
端到端用户工作流测试
模拟真实用户场景
"""

import pytest
from nanobot.agent.main_agent import MainAgent


def test_user_workflow_basic():
    """测试基本用户工作流程"""
    agent = MainAgent()
    
    # 用户：启动对话
    response = agent.handle_message("你好，我是用户")
    assert "你好" in response or "有什么可以帮助你的" in response
    print(f"欢迎语回复: {response}")
    
    # 用户：请求帮助
    response = agent.handle_message("帮我写一个简单的 Python 函数")
    assert "def" in response or "函数" in response
    print(f"函数生成回复: {response}")
    
    # 用户：请求解释
    response = agent.handle_message("这个函数是做什么的？")
    assert "解释" in response or "功能" in response
    print(f"解释回复: {response}")
    
    # 用户：请求修改
    response = agent.handle_message("能让它更简洁一点吗？")
    assert "修改" in response or "优化" in response
    print(f"优化回复: {response}")
    
    # 用户：结束对话
    response = agent.handle_message("谢谢，我已经学会了")
    assert "不客气" in response or "再见" in response
    print(f"结束语回复: {response}")
    
    print("基本用户工作流程测试通过")


def test_user_workflow_error_handling():
    """测试用户工作流程中的错误处理"""
    agent = MainAgent()
    
    # 用户：发送无效输入
    response = agent.handle_message("无效的输入")
    assert "理解" in response or "请重新" in response
    print(f"无效输入处理: {response}")
    
    # 用户：发送不完整的请求
    response = agent.handle_message("帮我写一个")
    assert "请提供更多" in response or "具体" in response
    print(f"不完整请求处理: {response}")
    
    print("用户工作流程错误处理测试通过")


def test_user_workflow_context_retention():
    """测试用户工作流程中的上下文保留"""
    agent = MainAgent()
    
    # 用户：发送第一个请求
    response = agent.handle_message("帮我写一个计算斐波那契数列的 Python 函数")
    assert "斐波那契" in response or "fibonacci" in response
    print(f"斐波那契函数回复: {response}")
    
    # 用户：发送相关请求，不重复上下文
    response = agent.handle_message("这个函数的时间复杂度是多少？")
    assert "时间复杂度" in response or "O(" in response
    print(f"时间复杂度回复: {response}")
    
    print("用户工作流程上下文保留测试通过")


if __name__ == "__main__":
    test_user_workflow_basic()
    test_user_workflow_error_handling()
    test_user_workflow_context_retention()
    print("所有用户工作流程验收测试通过！")
