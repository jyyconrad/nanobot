"""
验证配置加载向后兼容
测试旧格式配置仍能正常加载
"""

import pytest
import os
import tempfile
import yaml
from nanobot.config.schema import Config


def test_old_config_format_compatibility():
    """测试旧格式配置加载兼容性"""
    # 创建旧格式的配置文件
    old_config = {
        "agent": {
            "name": "Nanobot",
            "version": "1.0.0",
            "max_history": 100
        },
        "llm": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.7
        },
        "database": {
            "type": "sqlite",
            "path": "data/nanobot.db"
        }
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(old_config, f)
        
        # 尝试加载旧格式配置
        try:
            config = Config.load(config_path)
            assert config.agent.name == "Nanobot"
            assert config.agent.version == "1.0.0"
            assert config.llm.model == "gpt-3.5-turbo"
            assert config.database.type == "sqlite"
            print("旧格式配置加载成功")
        except Exception as e:
            pytest.fail(f"旧格式配置加载失败: {e}")


def test_config_default_values():
    """测试配置默认值"""
    # 创建一个不完整的配置文件
    minimal_config = {
        "agent": {
            "name": "TestBot"
        }
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(minimal_config, f)
        
        config = Config.load(config_path)
        
        # 验证必填字段存在
        assert config.agent.name == "TestBot"
        
        # 验证默认值是否正确设置
        assert hasattr(config, "llm")
        assert hasattr(config, "database")
        assert hasattr(config, "server")
        
        print("配置默认值测试通过")


def test_config_migration():
    """测试配置自动迁移功能"""
    # 创建需要迁移的配置文件
    legacy_config = {
        "bot": {
            "name": "LegacyBot",
            "max_memory": 50
        },
        "ai": {
            "engine": "gpt-4",
            "temp": 0.5
        },
        "db": {
            "driver": "mysql",
            "url": "mysql://user:pass@localhost/db"
        }
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(legacy_config, f)
        
        # 加载需要迁移的配置
        try:
            config = Config.load(config_path)
            
            # 验证配置是否正确迁移
            assert config.agent.name == "LegacyBot"
            assert config.llm.model == "gpt-4"
            assert config.database.type == "mysql"
            
            print("配置迁移测试通过")
        except Exception as e:
            pytest.fail(f"配置迁移失败: {e}")


if __name__ == "__main__":
    test_old_config_format_compatibility()
    test_config_default_values()
    test_config_migration()
    print("所有配置加载回归测试通过！")
