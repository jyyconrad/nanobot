import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nanobot.agent.planner.task_planner import TaskPlanner


async def debug_plan_correction():
    planner = TaskPlanner()
    user_input = "修改代码中的错误"
    context = {"last_task": {"description": "编写Python函数"}}

    print("用户输入:", user_input)
    print("上下文:", context)

    # 检查是否是取消指令
    is_cancellation = await planner.cancellation_detector.is_cancellation(user_input)
    print("是取消指令:", is_cancellation)

    if is_cancellation:
        reason = await planner.cancellation_detector.get_reason(user_input)
        print("取消原因:", reason)

    # 检查是否是修正指令
    correction = await planner.correction_detector.detect_correction(user_input, context)
    print("是修正指令:", correction)

if __name__ == "__main__":
    import asyncio
    asyncio.run(debug_plan_correction())
