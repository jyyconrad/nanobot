#!/usr/bin/env python3
"""
验证 Nanobot 升级后的新功能

任务要求：
1. 验证 MainAgent 智能决策
   - 测试 MainAgent 能否通过工具查询配置
   - 测试 MainAgent 能否智能选择 skills
   - 测试 MainAgent 能否自主决策不询问用户

2. 验证 Subagent 技能加载
   - 测试 Subagent 能否接收 skills 列表
   - 测试 Subagent 能否动态加载技能内容
   - 测试技能内容是否被注入到系统提示

3. 端到端测试
   - 完整流程测试：用户输入 → MainAgent → Subagent → 结果
   - 验证整个协作流程

4. 性能测试
   - 测试响应时间是否满足要求
   - 测试技能加载是否高效
"""

import asyncio
import logging
import time
from uuid import uuid4

from nanobot.agent.enhanced_main_agent import EnhancedMainAgent
from nanobot.agent.skill_loader import SkillLoader
from nanobot.agent.tools.config_tools import GetAvailableSkillsTool, GetSkillsForTaskTool, GetSkillContentTool
from nanobot.agent.tools.registry import ToolRegistry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_main_agent_intelligent_decision():
    """测试 MainAgent 智能决策"""
    logger.info("=== 测试 MainAgent 智能决策 ===")

    # 创建增强版主智能体
    main_agent = EnhancedMainAgent(session_id=str(uuid4()))

    # 1. 测试通过工具查询配置
    logger.info("1. 测试通过工具查询配置")
    tool_registry = main_agent.get_tool_registry()

    if tool_registry.has("get_available_skills"):
        result = await tool_registry.execute("get_available_skills", {})
        logger.info(f"   可用技能: {result}")
    else:
        logger.error("   未找到 get_available_skills 工具")
        return False

    if tool_registry.has("get_available_agents"):
        result = await tool_registry.execute("get_available_agents", {})
        logger.info(f"   可用代理类型: {result}")
    else:
        logger.error("   未找到 get_available_agents 工具")
        return False

    # 2. 测试智能选择 skills
    logger.info("2. 测试智能选择 skills")
    test_message = "修复 Python 代码中的 bug"
    decision = await main_agent._make_skill_decision(test_message)
    logger.info(f"   决策结果: {decision}")

    if decision.success and decision.action == "spawn_subagent":
        subagent_config = decision.data.get("subagent_config", {})
        selected_skills = subagent_config.get("skills", [])
        logger.info(f"   智能选择的技能: {selected_skills}")
    else:
        logger.error("   决策失败")
        return False

    # 3. 测试自主决策不询问用户
    logger.info("3. 测试自主决策不询问用户")
    if decision.success and decision.action in ["spawn_subagent", "reply"]:
        logger.info("   MainAgent 可以自主决策")
    else:
        logger.error("   MainAgent 无法自主决策")
        return False

    logger.info("✅ MainAgent 智能决策测试通过")
    return True


async def test_subagent_skill_loading():
    """测试 Subagent 技能加载"""
    logger.info("=== 测试 Subagent 技能加载 ===")

    # 1. 测试技能加载器加载技能
    logger.info("1. 测试技能加载器加载技能")
    skill_loader = SkillLoader()
    task_type = "debugging"
    skills = await skill_loader.load_skills_for_task(task_type)
    logger.info(f"   任务类型 '{task_type}' 对应的技能: {skills}")

    # 2. 测试技能内容加载
    logger.info("2. 测试技能内容加载")
    all_loaded = True
    for skill in skills:
        content = await skill_loader.load_skill_content(skill)
        if content:
            logger.info(f"   技能 '{skill}' 内容加载成功: {content}")
        else:
            logger.warning(f"   技能 '{skill}' 内容未找到")
            all_loaded = False

    # 3. 测试技能验证
    logger.info("3. 测试技能验证")
    valid_skills = await skill_loader.validate_skills(skills)
    logger.info(f"   有效技能: {valid_skills}")

    if all_loaded and len(valid_skills) > 0:
        logger.info("✅ Subagent 技能加载测试通过")
        return True
    else:
        logger.error("❌ Subagent 技能加载测试失败")
        return False


async def test_end_to_end_flow():
    """测试端到端流程"""
    logger.info("=== 测试端到端流程 ===")

    main_agent = EnhancedMainAgent(session_id=str(uuid4()))

    # 测试一个简单的任务
    test_message = "编写一个 Python 函数来计算斐波那契数列"

    logger.info(f"测试消息: {test_message}")

    start_time = time.time()
    response = await main_agent.process_message(test_message)
    end_time = time.time()

    logger.info(f"响应时间: {end_time - start_time:.2f} 秒")
    logger.info(f"响应内容: {response}")

    if "正在执行任务" in response or "已处理" in response:
        logger.info("✅ 端到端流程测试通过")
        return True
    else:
        logger.error("❌ 端到端流程测试失败")
        return False


async def test_performance():
    """测试性能"""
    logger.info("=== 测试性能 ===")

    # 1. 技能加载时间测试
    logger.info("1. 测试技能加载时间")
    start_time = time.time()
    skill_loader = SkillLoader()
    for i in range(10):
        await skill_loader.load_skills_for_task("coding")
    end_time = time.time()
    avg_time = (end_time - start_time) / 10
    logger.info(f"   技能加载平均时间: {avg_time:.3f} 秒")

    # 2. 任务类型分析时间测试
    logger.info("2. 测试任务类型分析时间")
    main_agent = EnhancedMainAgent(session_id=str(uuid4()))
    test_messages = [
        "修复 Python 代码中的 bug",
        "编写文档",
        "进行安全审计",
        "分析数据",
        "测试功能"
    ]
    total_time = 0
    for msg in test_messages:
        start = time.time()
        decision = await main_agent._make_skill_decision(msg)
        total_time += time.time() - start
        logger.debug(f"   消息 '{msg}' 分析时间: {time.time() - start:.3f} 秒")

    avg_analysis_time = total_time / len(test_messages)
    logger.info(f"   任务类型分析平均时间: {avg_analysis_time:.3f} 秒")

    if avg_time < 0.1 and avg_analysis_time < 0.5:
        logger.info("✅ 性能测试通过")
        return True
    else:
        logger.warning("⚠️ 性能测试警告：响应时间可能不符合要求")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("开始验证 Nanobot 升级后的新功能")

    results = {}

    # 运行各项测试
    results["main_agent_intelligent_decision"] = await test_main_agent_intelligent_decision()
    results["subagent_skill_loading"] = await test_subagent_skill_loading()
    results["end_to_end_flow"] = await test_end_to_end_flow()
    results["performance"] = await test_performance()

    # 统计结果
    passed = sum(1 for result in results.values() if result)
    failed = len(results) - passed

    logger.info(f"\n=== 测试结果总结 ===")
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {failed}")

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")

    if failed == 0:
        logger.info("\n🎉 所有功能验证通过！")
    else:
        logger.error(f"\n⚠️ 有 {failed} 项功能验证失败！")

    return failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        if not success:
            exit(1)
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        exit(1)
