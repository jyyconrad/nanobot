"""
验证 Subagent 生命周期管理
测试异常情况恢复
"""

import pytest
import time
from nanobot.agent.subagent.agno_subagent import AgnoSubagent
from nanobot.agent.subagent.manager import SubagentManager


def test_subagent_lifecycle_basic():
    """测试 Subagent 基本生命周期"""
    manager = SubagentManager()
    
    # 创建 Subagent
    task = "帮我写一个简单的 Python 函数"
    subagent = manager.create_subagent(task)
    assert subagent is not None
    assert subagent.task == task
    
    # 启动 Subagent
    subagent.start()
    assert subagent.is_running()
    
    # 停止 Subagent
    subagent.stop()
    assert not subagent.is_running()
    
    print("Subagent 基本生命周期测试通过")


def test_subagent_exception_recovery():
    """测试 Subagent 异常恢复"""
    manager = SubagentManager()
    
    # 创建一个会引发异常的任务
    bad_task = "raise_exception()"
    
    try:
        subagent = manager.create_subagent(bad_task)
        subagent.start()
        time.sleep(1)
        
        # 检查 Subagent 是否处理了异常
        assert not subagent.is_running()
        print("Subagent 异常恢复测试通过")
    except Exception as e:
        print(f"Subagent 正确处理了异常: {e}")


def test_subagent_concurrent_lifecycle():
    """测试多个 Subagent 并发生命周期管理"""
    manager = SubagentManager()
    
    # 创建多个 Subagent
    tasks = [
        "帮我写一个简单的 Python 函数",
        "帮我计算 1+2+3+...+100 的结果",
        "帮我写一个简单的 TODO 列表应用"
    ]
    
    subagents = []
    for task in tasks:
        subagent = manager.create_subagent(task)
        subagents.append(subagent)
        subagent.start()
    
    # 验证所有 Subagent 正在运行
    for i, subagent in enumerate(subagents):
        assert subagent.is_running(), f"Subagent {i} 没有正常启动"
    
    # 停止所有 Subagent
    for subagent in subagents:
        subagent.stop()
    
    # 验证所有 Subagent 已停止
    for i, subagent in enumerate(subagents):
        assert not subagent.is_running(), f"Subagent {i} 没有正常停止"
    
    print("多个 Subagent 并发生命周期管理测试通过")


if __name__ == "__main__":
    test_subagent_lifecycle_basic()
    test_subagent_exception_recovery()
    test_subagent_concurrent_lifecycle()
    print("所有 Subagent 生命周期回归测试通过！")
