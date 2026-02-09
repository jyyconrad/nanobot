#!/usr/bin/env python3
"""
简单任务示例

展示如何使用 Nanobot 执行一个简单的任务。
"""

import asyncio
from nanobot.agent.enhanced_main_agent import EnhancedMainAgent


async def main():
    """主函数"""
    # 创建 MainAgent 实例
    agent = EnhancedMainAgent()

    # 示例任务：写一个简单的 Python 函数
    task = "写一个计算阶乘的 Python 函数，并保存到 factorial.py 文件中"

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
