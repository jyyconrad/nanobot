"""
验证消息处理逻辑一致
测试边界情况
"""

import pytest

from nanobot.agent.context_manager import ContextManager
from nanobot.agent.decision.new_message_handler import NewMessageHandler


def test_message_handling_basic():
    """测试基本消息处理逻辑"""
    handler = NewMessageHandler()
    context_manager = ContextManager()

    # 测试简单消息
    simple_message = "你好，我是用户"
    response = handler.handle(simple_message, context_manager)
    assert response is not None
    assert len(response) > 0
    print(f"简单消息处理成功: {response}")

    # 测试包含指令的消息
    command_message = "帮我写一个 Python 函数"
    response = handler.handle(command_message, context_manager)
    assert response is not None
    assert len(response) > 0
    print(f"指令消息处理成功: {response}")


def test_message_handling_edge_cases():
    """测试边界情况的消息处理"""
    handler = NewMessageHandler()
    context_manager = ContextManager()

    # 测试空消息
    empty_message = ""
    with pytest.raises(Exception):
        handler.handle(empty_message, context_manager)

    # 测试非常长的消息
    long_message = "a" * 10000
    response = handler.handle(long_message, context_manager)
    assert response is not None
    assert len(response) > 0
    print("长消息处理成功")

    # 测试包含特殊字符的消息
    special_char_message = "Hello\nWorld\t!@#$%^&*()"
    response = handler.handle(special_char_message, context_manager)
    assert response is not None
    assert len(response) > 0
    print("特殊字符消息处理成功")


def test_message_history_handling():
    """测试消息历史处理"""
    handler = NewMessageHandler()
    context_manager = ContextManager()

    # 发送多条消息
    messages = ["你好", "帮我写一个简单的 Python 函数", "如何使用这个函数？", "能再优化一下吗？"]

    for msg in messages:
        response = handler.handle(msg, context_manager)
        assert response is not None
        assert len(response) > 0

    # 验证历史记录是否正确存储
    history = context_manager.get_history()
    assert len(history) == len(messages) * 2  # 每个用户消息对应一个助手回复
    print("消息历史处理成功")


if __name__ == "__main__":
    test_message_handling_basic()
    test_message_handling_edge_cases()
    test_message_history_handling()
    print("所有消息处理回归测试通过！")
