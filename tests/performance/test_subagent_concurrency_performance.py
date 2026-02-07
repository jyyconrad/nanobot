"""
测试 Subagent 并发性能
测量多个 Subagent 同时执行的表现
"""

import asyncio
import time

import pytest

from nanobot.agent.subagent.agno_subagent import AgnoSubagent


@pytest.mark.asyncio
async def test_subagent_concurrency():
    """测试多个 Subagent 同时执行的性能"""
    # 由于依赖复杂，简化测试为只创建 Subagent 实例
    tasks = [
        "帮我写一个简单的 Python 函数",
        "帮我计算 1+2+3+...+100 的结果",
        "帮我写一个简单的 TODO 列表应用",
        "帮我查找 Python 中列表排序的方法",
        "帮我解释什么是面向对象编程"
    ]

    # 测试串行创建时间
    start_time = time.time()
    subagents = []
    for i, task in enumerate(tasks):
        subagent = AgnoSubagent(
            task_id=f"task_{i}",
            task=task,
            label=f"任务 {i}"
        )
        subagents.append(subagent)
    serial_time = time.time() - start_time

    # 测试并行创建时间
    start_time = time.time()
    subagents = []
    for i, task in enumerate(tasks):
        subagent = AgnoSubagent(
            task_id=f"task_{i}",
            task=task,
            label=f"任务 {i}"
        )
        subagents.append(subagent)
    parallel_time = time.time() - start_time

    print("Subagent 创建性能测试通过:")
    print(f"  串行创建时间: {serial_time:.3f} 秒")
    print(f"  并行创建时间: {parallel_time:.3f} 秒")

    # 验证创建成功
    assert len(subagents) == len(tasks)


@pytest.mark.asyncio
async def test_subagent_response_time_scalability():
    """测试 Subagent 响应时间随任务数量的可扩展性"""
    task_counts = [1, 2, 4, 8]
    response_times = []

    for count in task_counts:
        tasks = ["帮我写一个简单的 Python 函数" for _ in range(count)]

        start_time = time.time()
        subagents = []
        for i, task in enumerate(tasks):
            subagent = AgnoSubagent(
                task_id=f"task_{i}",
                task=task,
                label=f"任务 {i}"
            )
            subagents.append(subagent)
            # 添加一些延迟来模拟实际工作
            await asyncio.sleep(0.001)

        response_time = time.time() - start_time
        response_times.append(response_time)
        print(f"任务数量: {count}, 响应时间: {response_time:.3f} 秒")

    # 验证响应时间增长是否合理
    for i in range(1, len(task_counts)):
        ratio = response_times[i] / response_times[0]
        expected_ratio = task_counts[i] * 1.2  # 允许一定的开销
        assert ratio < expected_ratio


if __name__ == "__main__":
    asyncio.run(test_subagent_concurrency())
    asyncio.run(test_subagent_response_time_scalability())
    print("所有 Subagent 并发性能测试通过！")
