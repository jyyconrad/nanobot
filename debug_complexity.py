import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nanobot.agent.planner.complexity_analyzer import ComplexityAnalyzer
from nanobot.agent.planner.models import TaskType


async def debug_complexity():
    analyzer = ComplexityAnalyzer()
    user_input = "计算两个数的和"
    task_type = TaskType.CODE_GENERATION

    print("用户输入:", user_input)
    print("任务类型:", task_type)

    complexity = await analyzer.analyze_complexity(user_input, task_type)
    print("复杂度:", complexity)

    category = await analyzer.get_complexity_category(user_input, task_type)
    print("复杂度类别:", category)


if __name__ == "__main__":
    import asyncio

    asyncio.run(debug_complexity())
