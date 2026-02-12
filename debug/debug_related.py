import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nanobot.agent.planner.correction_detector import CorrectionDetector


async def debug_related():
    detector = CorrectionDetector()
    user_input = "修改代码"
    last_task = {"description": "编写Python函数"}

    print("用户输入:", user_input)
    print("上一个任务:", last_task)

    is_related = await detector._is_related_to_last_task(user_input, last_task)
    print("是否相关:", is_related)

    # 检查关键词匹配
    description = last_task["description"].lower()
    input_text = user_input.lower()
    common_words = ["代码", "文件", "数据", "分析", "搜索", "任务", "函数", "配置"]
    matching_words = []

    for word in common_words:
        if word in description and word in input_text:
            matching_words.append(word)

    print("匹配的关键词:", matching_words)


if __name__ == "__main__":
    import asyncio

    asyncio.run(debug_related())
