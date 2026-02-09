#!/usr/bin/env python3
"""
调试任务示例

展示如何使用 Nanobot 执行调试任务。
"""

import asyncio
from nanobot.agent.enhanced_main_agent import EnhancedMainAgent


async def main():
    """主函数"""
    # 创建 MainAgent 实例
    agent = EnhancedMainAgent()

    # 示例任务：调试一个 Python 函数
    task = """
    我有一个计算阶乘的 Python 函数，但是它有 bug，无法正确计算阶乘。请帮我找出并修复它。

    函数代码：
    def factorial(n):
        result = 0
        for i in range(1, n+1):
            result *= i
        return result

    问题：
    当调用 factorial(5) 时，返回 0，而不是预期的 120。
    """

    # 处理任务
    result = await agent.process_message(task)
    print("任务执行结果：")
    print(result)

    # 等待一段时间，让任务有时间完成
    await asyncio.sleep(5)

    # 获取状态
    status = await agent.get_status()
    print("\nMainAgent 状态：")
    print(status)


if __name__ == "__main__":
    asyncio.run(main())
