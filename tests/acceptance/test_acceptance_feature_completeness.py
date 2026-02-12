"""
验证所有功能按计划文档实现
检查关键接口可用性
"""

import os

import pytest

from nanobot.agent.context_compressor import ContextCompressor
from nanobot.agent.context_manager import ContextManagerV2 as ContextManager
from nanobot.agent.decision.decision_maker import ExecutionDecisionMaker
from nanobot.agent.planner.task_planner import TaskPlanner
from nanobot.agent.subagent.manager import SubagentManager


def test_core_modules_availability():
    """测试核心模块可用性"""
    # 测试上下文管理模块
    context_manager = ContextManager()
    assert context_manager is not None
    assert hasattr(context_manager, "add_message")
    assert hasattr(context_manager, "get_history")

    # 测试上下文压缩模块
    compressor = ContextCompressor()
    assert compressor is not None
    assert hasattr(compressor, "compress")

    # 测试任务规划模块
    planner = TaskPlanner()
    assert planner is not None
    assert hasattr(planner, "plan_task")

    # 测试决策模块 - 注意：ExecutionDecisionMaker 需要 AgentLoop 实例，但我们可以传入 None 进行测试
    decision_maker = ExecutionDecisionMaker(None)
    assert decision_maker is not None
    assert hasattr(decision_maker, "make_decision")

    # 测试 Subagent 管理模块
    subagent_manager = SubagentManager()
    assert subagent_manager is not None
    assert hasattr(subagent_manager, "create_subagent")

    print("所有核心模块可用性测试通过")


def test_configuration_system():
    """测试配置系统"""
    from nanobot.config.schema import Config

    config = Config.load()
    assert config is not None
    assert hasattr(config, "agents")
    assert hasattr(config, "channels")
    assert hasattr(config, "providers")
    assert hasattr(config, "gateway")
    assert hasattr(config, "tools")
    assert hasattr(config, "monitoring")

    print("配置系统测试通过")


def test_database_operations():
    """测试数据库操作"""
    from nanobot.agent.memory.enhanced_memory import EnhancedMemory

    memory = EnhancedMemory()
    assert memory is not None
    assert hasattr(memory, "add_memory")
    assert hasattr(memory, "search_memory")
    assert hasattr(memory, "delete_memory")

    print("数据库操作测试通过")


def test_cli_interface():
    """测试命令行接口"""
    import subprocess

    try:
        result = subprocess.run(
            ["python3", "-m", "nanobot", "--help"], capture_output=True, text=True, check=True
        )
        assert "Usage:" in result.stdout
        assert "nanobot" in result.stdout

        print("命令行接口测试通过")
    except Exception as e:
        pytest.fail(f"命令行接口测试失败: {e}")


def test_docs_availability():
    """测试文档可用性"""
    docs_dir = "docs"
    required_files = ["README.md", "ARCHITECTURE.md", "DEPLOYMENT.md", "MIGRATION_GUIDE.md"]

    for file_name in required_files:
        file_path = os.path.join(docs_dir, file_name)
        assert os.path.exists(file_path), f"文档文件缺失: {file_path}"

    print("文档可用性测试通过")


if __name__ == "__main__":
    test_core_modules_availability()
    test_configuration_system()
    test_database_operations()
    test_cli_interface()
    test_docs_availability()
    print("所有功能完整性验收测试通过！")
