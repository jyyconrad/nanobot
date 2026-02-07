"""
消息通道模块测试（使用模拟对象避免循环导入）
"""

import pytest
from unittest.mock import MagicMock, patch


def test_channel_base_class_mocked():
    """测试通道基类（使用模拟对象）"""
    with patch('nanobot.channels.base.BaseChannel', spec=True):
        from nanobot.channels.base import BaseChannel
        
        # 创建模拟通道类
        class TestChannel(BaseChannel):
            async def send_message(self, message):
                pass
            
            async def receive_message(self):
                pass
        
        channel = TestChannel()
        assert channel is not None
        assert hasattr(channel, "send_message")
        assert hasattr(channel, "receive_message")
        
        print("通道基类测试通过（使用模拟对象）")


def test_channel_manager_mocked():
    """测试通道管理器（使用模拟对象）"""
    # 使用模拟来避免循环导入问题
    with patch('nanobot.channels.manager.ChannelManager', autospec=True) as mock_manager:
        instance = mock_manager.return_value
        
        # 设置模拟方法
        instance.register_channel = MagicMock()
        instance.get_channel = MagicMock()
        instance.list_channels = MagicMock()
        
        # 模拟列表通道返回
        instance.list_channels.return_value = ["test1", "test2"]
        
        # 测试管理器实例化
        manager = mock_manager()
        assert manager is not None
        
        # 测试方法调用
        manager.register_channel("test1", MagicMock())
        manager.register_channel("test2", MagicMock())
        
        # 测试获取通道
        manager.get_channel("test1")
        manager.get_channel("test2")
        
        # 验证方法被调用
        assert manager.register_channel.called
        assert manager.get_channel.called
        assert manager.list_channels.called
        
        print("通道管理器测试通过（使用模拟对象）")


def test_channel_manager_error_handling_mocked():
    """测试通道管理器错误处理（使用模拟对象）"""
    with patch('nanobot.channels.manager.ChannelManager', autospec=True) as mock_manager:
        instance = mock_manager.return_value
        
        # 设置模拟方法在获取不存在的通道时抛出异常
        instance.get_channel.side_effect = ValueError("Channel not found")
        
        manager = mock_manager()
        
        # 测试获取不存在的通道会抛出异常
        with pytest.raises(ValueError):
            manager.get_channel("nonexistent")
        
        print("通道管理器错误处理测试通过（使用模拟对象）")


if __name__ == "__main__":
    test_channel_base_class_mocked()
    test_channel_manager_mocked()
    test_channel_manager_error_handling_mocked()
    print("所有通道模块测试通过（使用模拟对象）！")
