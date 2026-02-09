#!/usr/bin/env python3
"""
多 Subagent 示例

展示如何使用 Nanobot 执行需要多个 Subagent 的任务。
"""

import asyncio
from nanobot.agent.enhanced_main_agent import EnhancedMainAgent


async def main():
    """主函数"""
    # 创建 MainAgent 实例
    agent = EnhancedMainAgent()

    # 示例任务：创建一个完整的项目
    task = """
    创建一个完整的项目，包括：
    1. 一个简单的 Flask 应用（用户管理 API）
    2. 单元测试
    3. Dockerfile
    4. README.md 文件

    项目应该具有良好的代码结构和文档。
    """

    # 处理任务
    result = await agent.process_message(task)
    print("任务执行结果：")
    print(result)

    # 等待一段时间，让任务有时间完成
    await asyncio.sleep(15)

    # 获取状态
    status = await agent.get_status()
    print("\nMainAgent 状态：")
    print(status)


if __name__ == "__main__":
    asyncio.run(main())
