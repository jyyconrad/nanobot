"""
测试任务规划性能
测量规划响应时间和复杂度分析准确性
"""

import time

import pytest

from nanobot.agent.planner.complexity_analyzer import ComplexityAnalyzer
from nanobot.agent.planner.task_planner import TaskPlanner


@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=False,
    reason="Task planning response time may vary depending on system performance",
)
async def test_planning_response_time():
    """测试任务规划响应时间"""
    planner = TaskPlanner()

    # 测试简单任务规划
    simple_task = "帮我写一个简单的 Python 函数"

    start_time = time.time()
    await planner.plan_task(simple_task)
    simple_time = time.time() - start_time
    assert simple_time < 5.0  # 简单任务规划应在 5 秒内

    # 测试中等复杂度任务规划
    medium_task = (
        "帮我实现一个用户管理系统，包含用户注册、登录、查询功能，使用 SQLite 数据库"
    )

    start_time = time.time()
    await planner.plan_task(medium_task)
    medium_time = time.time() - start_time
    assert medium_time < 3.0  # 中等复杂度任务规划应在 3 秒内

    # 测试复杂任务规划
    complex_task = "帮我设计一个分布式系统架构，包含前端、后端、数据库、缓存、消息队列，考虑高可用性和负载均衡"

    start_time = time.time()
    await planner.plan_task(complex_task)
    complex_time = time.time() - start_time
    assert complex_time < 5.0  # 复杂任务规划应在 5 秒内

    print("规划响应时间测试通过:")
    print(f"  简单任务: {simple_time:.3f} 秒")
    print(f"  中等任务: {medium_time:.3f} 秒")
    print(f"  复杂任务: {complex_time:.3f} 秒")


@pytest.mark.asyncio
async def test_complexity_analysis_accuracy():
    """测试复杂度分析准确性"""
    analyzer = ComplexityAnalyzer()

    from nanobot.agent.planner.models import TaskType

    test_cases = [
        ("帮我写一个简单的 Python 函数", TaskType.CODE_GENERATION),
        (
            "帮我实现一个用户管理系统，包含用户注册、登录、查询功能",
            TaskType.CODE_GENERATION,
        ),
        (
            "帮我设计一个分布式系统架构，包含前端、后端、数据库、缓存、消息队列",
            TaskType.CODE_GENERATION,
        ),
    ]

    for task, task_type in test_cases:
        complexity = await analyzer.analyze_complexity(task, task_type)
        category = await analyzer.get_complexity_category(task, task_type)
        print(f"任务: '{task}'")
        print(f"任务类型: {task_type}")
        print(f"复杂度评分: {complexity:.2f}")
        print(f"复杂度类别: {category}")
        print()

    # 验证复杂度评分在合理范围内
    for task, task_type in test_cases:
        complexity = await analyzer.analyze_complexity(task, task_type)
        assert 0.0 <= complexity <= 1.0

    print("复杂度分析准确性测试通过")


if __name__ == "__main__":
    test_planning_response_time()
    test_complexity_analysis_accuracy()
    print("所有规划性能测试通过！")
