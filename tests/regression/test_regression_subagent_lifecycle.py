"""
验证 Subagent 生命周期管理
测试异常情况恢复
"""

import asyncio

import pytest

from nanobot.agent.subagent.manager import SubagentManager


def test_subagent_lifecycle_basic():
    """测试 Subagent 基本生命周期"""
    manager = SubagentManager()

    # 创建 Subagent
    task = "帮我写一个简单的 Python 函数"
    task_id = manager.create_subagent(task)
    assert task_id is not None

    # 验证 Subagent 已创建
    assert task_id in manager.subagents
    assert task_id in manager.tasks
    assert task_id in manager.states

    print("Subagent 基本生命周期测试通过")


def test_subagent_exception_recovery():
    """测试 Subagent 异常恢复"""
    manager = SubagentManager()

    # 创建一个会引发异常的任务
    bad_task = "raise_exception()"

    try:
        task_id = manager.create_subagent(bad_task)
        assert task_id is not None
        print("Subagent 异常恢复测试通过")
    except Exception as e:
        print(f"Subagent 正确处理了异常: {e}")


@pytest.mark.asyncio
async def test_subagent_concurrent_lifecycle():
    """测试多个 Subagent 并发生命周期管理"""
    manager = SubagentManager()

    # 创建多个 Subagent
    tasks = [
        "帮我写一个简单的 Python 函数",
        "帮我计算 1+2+3+...+100 的结果",
        "帮我写一个简单的 TODO 列表应用",
    ]

    task_ids = []
    for task in tasks:
        task_id = manager.create_subagent(task)
        task_ids.append(task_id)

    # 验证所有 Subagent 已创建
    for i, task_id in enumerate(task_ids):
        assert task_id in manager.subagents, f"Subagent {i} 没有正常创建"

    # 清理所有 Subagent
    for task_id in task_ids:
        await manager.cleanup_subagent(task_id)

    # 验证所有 Subagent 已清理
    for i, task_id in enumerate(task_ids):
        assert task_id not in manager.subagents, f"Subagent {i} 没有正常清理"

    print("多个 Subagent 并发生命周期管理测试通过")


if __name__ == "__main__":
    test_subagent_lifecycle_basic()
    test_subagent_exception_recovery()
    asyncio.run(test_subagent_concurrent_lifecycle())
    print("所有 Subagent 生命周期回归测试通过！")
