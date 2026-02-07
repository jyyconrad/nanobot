"""
配置系统集成测试
"""

import os
from unittest.mock import patch

import pytest

from nanobot.config.schema import Config


@pytest.mark.asyncio
async def test_config_loading():
    """
    测试配置加载
    """
    # 测试默认配置加载
    config = Config()
    assert config is not None
    assert isinstance(config, Config)
    assert hasattr(config, "agents")
    assert hasattr(config, "channels")
    assert hasattr(config, "providers")
    assert hasattr(config, "gateway")
    assert hasattr(config, "tools")


@pytest.mark.asyncio
async def test_config_validation():
    """
    测试配置验证
    """
    # 测试配置验证
    config = Config()
    assert config.agents.defaults.model == "anthropic/claude-opus-4-5"
    assert config.agents.defaults.max_tokens == 8192
    assert config.gateway.port == 9910
    assert config.tools.exec.timeout == 60


@pytest.mark.asyncio
async def test_config_validation_error():
    """
    测试配置验证错误
    """
    with pytest.raises(Exception):
        # 尝试创建无效配置
        Config(agents="invalid")


@pytest.mark.asyncio
async def test_multi_source_config():
    """
    测试多配置源
    """
    # 测试环境变量配置
    with patch.dict(os.environ, {"NANOBOT_PROVIDERS__OPENAI__API_KEY": "env-test-key"}):
        config = Config()
        assert config.providers.openai.api_key == "env-test-key"


@pytest.mark.asyncio
async def test_config_override():
    """
    测试配置覆盖
    """
    # 测试不同配置源的覆盖
    with patch.dict(os.environ, {"NANOBOT_PROVIDERS__OPENAI__API_KEY": "env-key"}):
        config = Config()
        assert config.providers.openai.api_key == "env-key"


@pytest.mark.asyncio
async def test_config_defaults():
    """
    测试配置默认值
    """
    config = Config()

    # 验证默认值
    assert config.agents.defaults.max_tokens == 8192
    assert config.agents.defaults.temperature == 0.7
    assert config.gateway.port == 9910
    assert config.tools.exec.timeout == 60
    assert config.monitoring.task.max_task_duration == 86400
