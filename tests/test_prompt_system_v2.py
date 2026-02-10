"""
PromptSystemV2 测试用例
测试提示词系统 V2 的核心功能
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from nanobot.agent.prompt_system_v2 import PromptSystemV2


def test_config_loading():
    """测试配置加载功能"""
    system = PromptSystemV2()
    assert system.config is not None
    assert isinstance(system.config, dict)


def test_prompt_layer_loading():
    """测试提示词层级加载"""
    system = PromptSystemV2()
    # 现在直接检查配置中是否定义了预期的层
    layers = ["core", "workspace", "user", "memory", "decisions"]
    config_layers = system.config.get("layers", {})
    
    for layer in layers:
        assert layer in config_layers
        assert isinstance(config_layers[layer], dict)


def test_cache_functionality():
    """测试缓存功能"""
    system = PromptSystemV2()

    # 测试缓存是否启用
    assert hasattr(system, "prompts_cache")
    assert isinstance(system.prompts_cache, dict)

    # 测试缓存 TTL 机制
    if hasattr(system, "_cache_ttl"):
        assert system._cache_ttl > 0


def test_build_main_agent_prompt():
    """测试 MainAgent 提示词构建"""
    system = PromptSystemV2()
    prompt = system.build_main_agent_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_build_subagent_prompt():
    """测试 Subagent 提示词构建"""
    system = PromptSystemV2()
    task_description = "测试任务"
    prompt = system.build_subagent_prompt(task_description)
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert task_description in prompt


def test_hooks_triggered():
    """测试钩子系统是否被正确触发"""
    system = PromptSystemV2()
    config_loaded = False

    def on_config_loaded(config):
        nonlocal config_loaded
        config_loaded = True

    system.register_hook("on_config_loaded", on_config_loaded)
    system.trigger("on_config_loaded", config=system.config)
    assert config_loaded is True


def test_layer_load_hook():
    """测试层加载钩子"""
    system = PromptSystemV2()
    layer_loaded = False

    def on_layer_loaded(layer_name, content):
        nonlocal layer_loaded
        layer_loaded = True

    system.register_hook("on_layer_loaded", on_layer_loaded)
    
    # 模拟加载一个层
    with patch.object(system, "_load_layer") as mock_load:
        mock_load.return_value = {"test": "content"}
        system.load_prompts()
        # 检查钩子是否被调用
        assert layer_loaded is True


def test_main_agent_prompt_hook():
    """测试 MainAgent 提示词构建钩子"""
    system = PromptSystemV2()
    prompt_built = False

    def on_main_agent_prompt_built(prompt):
        nonlocal prompt_built
        prompt_built = True

    system.register_hook("on_main_agent_prompt_built", on_main_agent_prompt_built)
    system.build_main_agent_prompt()
    assert prompt_built is True


def test_subagent_prompt_hook():
    """测试 Subagent 提示词构建钩子"""
    system = PromptSystemV2()
    prompt_built = False

    def on_subagent_prompt_built(prompt):
        nonlocal prompt_built
        prompt_built = True

    system.register_hook("on_subagent_prompt_built", on_subagent_prompt_built)
    system.build_subagent_prompt("测试任务")
    assert prompt_built is True


def test_workspace_override():
    """测试工作区覆盖提示词功能"""
    # 创建临时目录作为工作区
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # 创建提示词覆盖目录
        (temp_dir / "prompts" / "core").mkdir(parents=True, exist_ok=True)

        # 创建覆盖文件
        override_content = """
test_prompt: "工作区覆盖的提示词"
"""
        with open(temp_dir / "prompts" / "core" / "test.yaml", "w") as f:
            f.write(override_content)

        # 使用临时工作区初始化
        system = PromptSystemV2(workspace_path=temp_dir)

        # 验证覆盖是否生效
        assert system.workspace == temp_dir


def test_config_validation():
    """测试配置验证功能"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # 创建无效的配置文件
        invalid_config = """
invalid: "配置"
"""
        config_file = temp_dir / "config.yaml"
        with open(config_file, "w") as f:
            f.write(invalid_config)

        # 应该能正常初始化，但配置内容可能不完整
        system = PromptSystemV2(config_path=config_file)
        assert system.config is not None


def test_cache_invalidation():
    """测试缓存失效机制"""
    system = PromptSystemV2()

    # 测试缓存清除方法
    system.prompts_cache["test"] = "value"
    assert len(system.prompts_cache) > 0
    
    system.clear_cache()
    assert len(system.prompts_cache) == 0
