"""
消息通道模块测试
"""

import pytest
from nanobot.channels.base import BaseChannel
from nanobot.channels.manager import ChannelManager


def test_channel_base_class():
    """测试通道基类"""
    # 创建一个简单的通道子类
    class TestChannel(BaseChannel):
        async def send_message(self, message):
            pass
        
        async def receive_message(self):
            pass
    
    channel = TestChannel()
    assert channel is not None
    assert hasattr(channel, "send_message")
    assert hasattr(channel, "receive_message")
    
    print("通道基类测试通过")


def test_channel_manager():
    """测试通道管理器"""
    manager = ChannelManager()
    assert manager is not None
    assert hasattr(manager, "register_channel")
    assert hasattr(manager, "get_channel")
    assert hasattr(manager, "list_channels")
    
    print("通道管理器测试通过")


def test_channel_manager_register_and_get():
    """测试通道注册和获取"""
    manager = ChannelManager()
    
    # 创建测试通道类
    class TestChannel1(BaseChannel):
        async def send_message(self, message):
            pass
        
        async def receive_message(self):
            pass
    
    class TestChannel2(BaseChannel):
        async def send_message(self, message):
            pass
        
        async def receive_message(self):
            pass
    
    # 注册通道
    manager.register_channel("test1", TestChannel1())
    manager.register_channel("test2", TestChannel2())
    
    # 验证通道可以被获取
    assert manager.get_channel("test1") is not None
    assert manager.get_channel("test2") is not None
    
    # 验证通道列表
    channels = manager.list_channels()
    assert len(channels) == 2
    assert "test1" in channels
    assert "test2" in channels
    
    print("通道注册和获取测试通过")


def test_channel_manager_error_handling():
    """测试通道管理器错误处理"""
    manager = ChannelManager()
    
    # 测试获取不存在的通道
    with pytest.raises(ValueError):
        manager.get_channel("nonexistent")
    
    print("通道管理器错误处理测试通过")


if __name__ == "__main__":
    test_channel_base_class()
    test_channel_manager()
    test_channel_manager_register_and_get()
    test_channel_manager_error_handling()
    print("所有通道模块测试通过！")
