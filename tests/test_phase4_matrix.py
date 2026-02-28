"""Phase 4 Matrix 渠道集成测试用例"""

import pytest
from unittest.mock import MagicMock


def test_matrix_config_default_values():
    """测试 Matrix 配置默认值"""
    from nanobot.config.schema import MatrixConfig

    config = MatrixConfig()
    assert config.enabled is False
    assert config.homeserver == "https://matrix.org"
    assert config.access_token == ""
    assert config.user_id == ""
    assert config.device_id == ""
    assert config.e2ee_enabled is True
    assert config.sync_stop_grace_seconds == 2
    assert config.max_media_bytes == 20 * 1024 * 1024
    assert config.allow_from == []
    assert config.group_policy == "open"
    assert config.group_allow_from == []
    assert config.allow_room_mentions is False


def test_matrix_config_custom_values():
    """测试 Matrix 配置自定义值"""
    from nanobot.config.schema import MatrixConfig

    config = MatrixConfig(
        enabled=True,
        homeserver="https://matrix.example.com",
        access_token="test_token",
        user_id="@bot:matrix.example.com",
        device_id="test_device",
        e2ee_enabled=False,
        sync_stop_grace_seconds=5,
        max_media_bytes=10 * 1024 * 1024,
        allow_from=["@user1:matrix.org", "@user2:matrix.org"],
        group_policy="mention",
        group_allow_from=["!room1:matrix.org"],
        allow_room_mentions=True,
    )
    assert config.enabled is True
    assert config.homeserver == "https://matrix.example.com"
    assert config.access_token == "test_token"
    assert config.user_id == "@bot:matrix.example.com"
    assert config.device_id == "test_device"
    assert config.e2ee_enabled is False
    assert config.sync_stop_grace_seconds == 5
    assert config.max_media_bytes == 10 * 1024 * 1024
    assert config.allow_from == ["@user1:matrix.org", "@user2:matrix.org"]
    assert config.group_policy == "mention"
    assert config.group_allow_from == ["!room1:matrix.org"]
    assert config.allow_room_mentions is True


def test_channel_manager_includes_matrix():
    """测试 ChannelManager 包含 Matrix 渠道（需要 matrix SDK）"""
    pytest.importorskip("nio")
    pytest.importorskip("nh3")
    pytest.importorskip("mistune")

    from nanobot.config.schema import Config
    from nanobot.channels.manager import ChannelManager

    config_dict = {
        "channels": {
            "tui": {"enabled": False},
            "matrix": {"enabled": True, "homeserver": "https://matrix.org"},
        }
    }
    config = Config(**config_dict)
    bus = MagicMock()
    manager = ChannelManager(config, bus)
    assert "matrix" in manager.channels
