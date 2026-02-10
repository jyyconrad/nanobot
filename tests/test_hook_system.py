"""
HookSystem 测试用例
测试钩子系统的核心功能
"""

from nanobot.agent.hooks.hook_system import HookSystem


def test_hook_registration():
    """测试钩子注册和触发"""
    hooks = HookSystem()
    called = False

    def test_callback():
        nonlocal called
        called = True

    hooks.register("test_hook", test_callback)
    hooks.trigger("test_hook")
    assert called is True


def test_multiple_hooks():
    """测试多个钩子注册和触发"""
    hooks = HookSystem()
    call_count = 0

    def callback1():
        nonlocal call_count
        call_count += 1

    def callback2():
        nonlocal call_count
        call_count += 1

    hooks.register("test_hook", callback1)
    hooks.register("test_hook", callback2)
    hooks.trigger("test_hook")
    assert call_count == 2


def test_hook_unregistration():
    """测试钩子注销功能"""
    hooks = HookSystem()
    called = False

    def test_callback():
        nonlocal called
        called = True

    hooks.register("test_hook", test_callback)
    hooks.unregister("test_hook", test_callback)
    hooks.trigger("test_hook")
    assert called is False


def test_hook_with_arguments():
    """测试带参数的钩子触发"""
    hooks = HookSystem()
    received_args = None

    def test_callback(*args, **kwargs):
        nonlocal received_args
        received_args = (args, kwargs)

    hooks.register("test_hook", test_callback)
    hooks.trigger("test_hook", param1="value1", param2=42)
    assert received_args is not None
    assert len(received_args[0]) == 0
    assert received_args[1]["param1"] == "value1"
    assert received_args[1]["param2"] == 42


def test_get_hooks():
    """测试获取钩子列表"""
    hooks = HookSystem()

    def callback1():
        pass

    def callback2():
        pass

    hooks.register("test_hook", callback1)
    hooks.register("test_hook", callback2)

    registered_hooks = hooks.get_hooks("test_hook")
    assert len(registered_hooks) == 2
    assert callback1 in registered_hooks
    assert callback2 in registered_hooks


def test_nonexistent_hook():
    """测试触发不存在的钩子"""
    hooks = HookSystem()
    # 触发不存在的钩子应该不抛出异常
    hooks.trigger("nonexistent_hook")
    assert True  # 如果没有抛出异常，测试通过


def test_error_handling_in_hooks():
    """测试钩子回调中的错误处理"""
    hooks = HookSystem()

    def error_callback():
        raise Exception("Hook callback error")

    hooks.register("test_hook", error_callback)

    # 触发包含错误的钩子应该不会中断程序
    try:
        hooks.trigger("test_hook")
        assert True  # 如果没有抛出异常，测试通过
    except Exception as e:
        assert False, f"钩子触发时抛出了异常: {e}"


def test_all_defined_hook_types():
    """测试所有预定义的钩子类型都可正常工作"""
    hooks = HookSystem()
    tested_hooks = []

    def test_callback(hook_name):
        def callback():
            tested_hooks.append(hook_name)

        return callback

    # 测试所有预定义的钩子类型
    predefined_hooks = [
        "on_config_loaded",
        "on_prompts_loaded",
        "on_layer_loaded",
        "on_main_agent_prompt_built",
        "on_subagent_prompt_built",
        "on_prompt_ready",
        "on_agent_initialized",
        "on_agent_ready",
    ]

    for hook_name in predefined_hooks:
        hooks.register(hook_name, test_callback(hook_name))
        hooks.trigger(hook_name)

    # 验证所有钩子都被触发
    for hook_name in predefined_hooks:
        assert hook_name in tested_hooks, f"钩子 {hook_name} 未被正确触发"
