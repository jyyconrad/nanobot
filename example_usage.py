#!/usr/bin/env python3
"""
Nanobot 新功能使用示例

演示如何使用升级后的 MainAgent 和 Subagent 功能
"""

import asyncio
import logging

from nanobot.agent.enhanced_main_agent import EnhancedMainAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def example_task_analysis():
    """示例：任务分析和技能选择"""
    logger.info("=== 示例：任务分析和技能选择 ===")
    
    main_agent = EnhancedMainAgent()
    
    # 测试不同类型的任务
    test_messages = [
        "修复 Python 代码中的 bug",
        "编写文档",
        "进行安全审计",
        "分析数据",
        "测试功能"
    ]
    
    for message in test_messages:
        logger.info(f"\n测试消息: {message}")
        decision = await main_agent._make_skill_decision(message)
        logger.info(f"决策结果: {decision.action}")
        if decision.success and decision.action == "spawn_subagent":
            subagent_config = decision.data.get("subagent_config", {})
            logger.info(f"所选技能: {subagent_config.get('skills', [])}")
            logger.info(f"代理类型: {subagent_config.get('agent_type')}")


async def example_end_to_end():
    """示例：端到端流程"""
    logger.info("\n=== 示例：端到端流程 ===")
    
    main_agent = EnhancedMainAgent()
    
    # 测试一个简单的任务
    test_message = "编写一个 Python 函数来计算斐波那契数列"
    logger.info(f"测试消息: {test_message}")
    
    response = await main_agent.process_message(test_message)
    logger.info(f"响应: {response}")


async def example_tool_query():
    """示例：工具查询配置"""
    logger.info("\n=== 示例：工具查询配置 ===")
    
    main_agent = EnhancedMainAgent()
    
    # 获取工具注册表
    tool_registry = main_agent.get_tool_registry()
    
    # 查询可用技能
    if tool_registry.has("get_available_skills"):
        result = await tool_registry.execute("get_available_skills", {})
        logger.info(f"可用技能: {result}")
    
    # 查询可用代理类型
    if tool_registry.has("get_available_agents"):
        result = await tool_registry.execute("get_available_agents", {})
        logger.info(f"可用代理类型: {result}")


async def main():
    """主函数"""
    await example_task_analysis()
    await example_tool_query()
    await example_end_to_end()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"示例运行出错: {e}")
        import traceback
        traceback.print_exc()
