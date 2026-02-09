#!/usr/bin/env python3
"""
编码任务示例

展示如何使用 Nanobot 执行编码任务。
"""

import asyncio
from nanobot.agent.enhanced_main_agent import EnhancedMainAgent


async def main():
    """主函数"""
    # 创建 MainAgent 实例
    agent = EnhancedMainAgent()

    # 示例任务：创建一个简单的 Flask 应用
    task = "创建一个简单的 Flask 应用，包含一个用户管理的 API 接口，包括获取用户列表和添加用户的功能。"

    # 处理任务
    result = await agent.process_message(task)
    print("任务执行结果：")
    print(result)

    # 等待一段时间，让任务有时间完成
    await asyncio.sleep(10)

    # 获取状态
    status = await agent.get_status()
    print("\nMainAgent 状态：")
    print(status)


if __name__ == "__main__":
    asyncio.run(main())
