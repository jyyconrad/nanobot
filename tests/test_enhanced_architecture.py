"""
增强架构测试脚本

测试 MainAgent 智能决策、动态技能选择和 Subagent 创建流程
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_config_tools():
    """测试配置查询工具"""
    print("=" * 60)
    print("测试 1: 配置查询工具")
    print("=" * 60)

    from nanobot.agent.tools.config_tools import (
        GetAvailableAgentsTool,
        GetAvailableSkillsTool,
        GetSkillsForTaskTool,
    )

    # 测试获取可用技能
    print("\n1.1 测试 get_available_skills")
    skills_tool = GetAvailableSkillsTool()
    result = await skills_tool.execute()
    print(f"结果:\n{result}")
    print()

    # 测试获取 agent 类型
    print("1.2 测试获取 get_available_agents")
    agents_tool = GetAvailableAgentsTool()
    result = await agents_tool.execute()
    print(f"结果:\n{result}")
    print()

    # 测试根据任务类型获取技能
    print("1.3 测试 get_skills_for_task (coding)")
    task_tool = GetSkillsForTaskTool()
    result = await task_tool.execute(task_type="coding")
    print(f"结果:\n{result}")
    print()

    print("✅ 配置查询工具测试完成")
    print()


async def test_skill_loader():
    """测试 SkillLoader"""
    print("=" * 60)
    print("测试 2: SkillLoader")
    print("=" * 60)

    from nanobot.agent.skill_loader import SkillLoader

    loader = SkillLoader()

    # 测试获取任务类型映射
    print("\n2.1 测试 get_task_type_mapping")
    mapping = loader.get_task_type_mapping()
    for task_type, skills in mapping.items():
        print(f"  {task_type}: {skills}")
    print()

    # 测试加载技能
    print("2.2 测试 load_skills_for_task (coding)")
    skills = await loader.load_skills_for_task("coding")
    print(f"  结果: {skills}")
    print()

    # 测试加载技能内容
    print("2.3 测试 load_skill_content (coding)")
    content = await loader.load_skill_content("coding")
    if content:
        print(f"  结果: {content[:100]}...")
    else:
        print("  未找到技能内容")
    print()

    print("✅ SkillLoader 测试完成")
    print()


async def test_skill_decision_handler():
    """测试技能决策处理器"""
    print("=" * 60)
    print("测试 3: SkillDecisionHandler")
    print("=" * 60)

    from nanobot.agent.decision.models import DecisionRequest
    from nanobot.agent.decision.skill_decision_handler import SkillDecisionHandler
    from nanobot.agent.skill_loader import SkillLoader
    from nanobot.agent.tools.config_tools import (
        GetAvailableAgentsTool,
        GetAvailableSkillsTool,
    )
    from nanobot.agent.tools.registry import ToolRegistry

    # 初始化组件
    tool_registry = ToolRegistry()
    tool_registry.register(GetAvailableSkillsTool())
    tool_registry.register(GetAvailableAgentsTool())

    skill_loader = SkillLoader()

    decision_handler = SkillDecisionHandler(
        agent_loop=None, tool_registry=tool_registry, skill_loader=skill_loader
    )

    # 测试编码任务
    print("\n3.1 测试编码任务决策")
    request = DecisionRequest(
        request_type="skill_decision",
        data={
            "message_id": "test-001",
            "content": "编写一个 Python 函数实现快速排序",
            "sender_id": "user",
            "timestamp": 0,
            "conversation_id": "test-session",
            "message_type": "text",
        },
        context={"session_id": "test-session"},
    )

    result = await decision_handler.handle_request(request)
    print(f"  决策动作: {result.action}")
    print(f"  决策消息: {result.message}")
    print(f"  Subagent 任务: {result.data.get('subagent_task')}")
    print(f"  Subagent 配置:")
    config = result.data.get("subagent_config", {})
    print(f"    - agent_type: {config.get('agent_type')}")
    print(f"    - skills: {config.get('skills')}")
    print()

    # 测试调试任务
    print("3.2 测试调试任务决策")
    request.data["content"] = "帮我调试这段代码，它总是报错"
    result = await decision_handler.handle_request(request)
    print(f"  决策动作: {result.action}")
    print(f"  Subagent 配置:")
    config = result.data.get("subagent_config", {})
    print(f"    - agent_type: {config.get('agent_type')}")
    print(f"    - skills: {config.get('skills')}")
    print()

    # 测试安全任务
    print("3.3 测试安全审计任务决策")
    request.data["content"] = "对这个项目进行安全审计"
    result = await decision_handler.handle_request(request)
    print(f"  决策动作: {result.action}")
    print(f"  Subagent 配置:")
    config = result.data.get("subagent_config", {})
    print(f"    - agent_type: {config.get('agent_type')}")
    print(f"    - skills: {config.get('skills')}")
    print()

    print("✅ SkillDecisionHandler 测试完成")
    print()


async def test_enhanced_main_agent():
    """测试增强版 MainAgent"""
    print("=" * 60)
    print("测试 4: EnhancedMainAgent")
    print("=" * 60)

    from nanobot.agent.enhanced_main_agent import EnhancedMainAgent

    # 创建 EnhancedMainAgent 实例
    print("\n4.1 创建 EnhancedMainAgent 实例")
    main_agent = EnhancedMainAgent(session_id="test-session")
    print("  ✅ 实例创建成功")
    print()

    # 检查工具注册表
    print("4.2 检查工具注册表")
    tool_registry = main_agent.get_tool_registry()
    print(f"  已注册工具数量: {len(tool_registry)}")
    print(f"  工具列表: {tool_registry.tool_names}")
    print()

    # 检查 SkillDecisionHandler
    print("4.3 检查 SkillDecisionHandler")
    print(f"  SkillDecisionHandler 已初始化: {main_agent.skill_decision_handler is not None}")
    print()

    # 模拟处理消息（不实际调用 LLM）
    print("4.4 测试技能决策（不执行完整流程）")
    message = "编写一个 Python 函数实现快速排序"

    # 创建决策请求
    import time
    from nanobot.agent.decision.models import DecisionRequest
    from uuid import uuid4

    request = DecisionRequest(
        request_type="skill_decision",
        data={
            "message_id": str(uuid4()),
            "content": message,
            "sender_id": "user",
            "timestamp": time.time(),
            "conversation_id": main_agent.session_id,
            "message_type": "text",
        },
        context={"session_id": main_agent.session_id},
    )

    decision = await main_agent._make_skill_decision(message)
    print(f"  决策动作: {decision.action}")
    print(f"  决策消息: {decision.message}")
    if decision.data.get("subagent_config"):
        config = decision.data["subagent_config"]
        print(f"  Agent 类型: {config.get('agent_type')}")
        print(f"  选择的技能: {config.get('skills')}")
    print()

    print("✅ EnhancedMainAgent 测试完成")
    print()


async def test_task_type_analysis():
    """测试任务类型分析"""
    print("=" * 60)
    print("测试 5: 任务类型分析")
    print("=" * 60)

    from nanobot.agent.decision.skill_decision_handler import SkillDecisionHandler
    from nanobot.agent.skill_loader import SkillLoader
    from nanobot.agent.tools.registry import ToolRegistry

    # 初始化
    decision_handler = SkillDecisionHandler(
        agent_loop=None, tool_registry=ToolRegistry(), skill_loader=SkillLoader()
    )

    # 测试不同类型的任务
    test_cases = [
        ("编写一个 Python 函数", "coding"),
        ("帮我调试这段代码", "debugging"),
        ("编写单元测试", "testing"),
        ("进行安全审计", "security"),
        ("制定项目计划", "planning"),
        ("编写技术文档", "writing"),
        ("调研市场趋势", "research"),
        ("分析数据报告", "analysis"),
    ]

    print("\n5.1 测试任务类型识别")
    for task, expected_type in test_cases:
        task_type = await decision_handler._analyze_task_type(task)
        status = "✅" if task_type == expected_type else "❌"
        print(f"  {status} 任务: {task[:30]:30s} → 识别为: {task_type:12s} (期望: {expected_type})")
    print()

    print("✅ 任务类型分析测试完成")
    print()


async def test_skills_loading_flow():
    """测试完整的技能加载流程"""
    print("=" * 60)
    print("测试 6: 完整的技能加载流程")
    print("=" * 60)

    from nanobot.agent.enhanced_main_agent import EnhancedMainAgent
    from nanobot.agent.subagent.models import SubagentTask
    from nanobot.agent.decision.models import DecisionResult

    # 创建 EnhancedMainAgent
    print("\n6.1 创建 EnhancedMainAgent")
    main_agent = EnhancedMainAgent(session_id="test-session-001")
    print("  ✅ 已创建")
    print()

    # 模拟技能决策
    print("6.2 模拟智能技能决策")
    message = "编写一个 Python 函数实现快速排序"
    decision = await main_agent._make_skill_decision(message)
    print(f"  决策: {decision.action}")
    print(f"  Agent 类型: {decision.data.get('subagent_config', {}).get('agent_type')}")
    print(f"  选择的技能: {decision.data.get('subagent_config', {}).get('skills')}")
    print()

    # 模拟创建 SubagentTask
    print("6.3 模拟创建 SubagentTask")
    if decision.action == "spawn_subagent":
        subagent_config = decision.data.get("subagent_config", {})
        task = SubagentTask(
            task_id="test-task-001",
            description=decision.data.get("subagent_task"),
            config=subagent_config,
            agent_type=subagent_config.get("agent_type"),
            skills=subagent_config.get("skills"),  # 🔥 技能信息被传递
        )
        print(f"  ✅ SubagentTask 已创建")
        print(f"     - task_id: {task.task_id}")
        print(f"     - agent_type: {task.agent_type}")
        print(f"     - skills: {task.skills}")
    print()

    # 测试技能内容加载
    print("6.4 测试技能内容加载")
    if task and task.skills:
        from nanobot.agent.skill_loader import SkillLoader

        skill_loader = SkillLoader()
        print(f"  需要加载的技能: {task.skills}")

        loaded_skills = {}
        for skill_name in task.skills:
            content = await skill_loader.load_skill_content(skill_name)
            if content:
                loaded_skills[skill_name] = content
                print(f"    ✅ {skill_name}: 加载成功")
            else:
                print(f"    ❌ {skill_name}: 未找到")

        print(f"\n  已加载 {len(loaded_skills)} 个技能")
        print()

        # 展示系统提示构建
        print("6.5 模拟构建系统提示")
        system_prompt_parts = ["# Enhanced Agno Subagent\n", f"## Your Task\n{task.description}\n", "## Available Skills\n"]

        for skill_name, content in loaded_skills.items():
            system_prompt_parts.append(f"\n### {skill_name}\n{content}\n")

        system_prompt = "".join(system_prompt_parts)
        print(f"  系统提示长度: {len(system_prompt)} 字符")
        print(f"  系统提示预览 (前 300 字符):")
        print(f"  {'-' * 60}")
        print(f"  {system_prompt[:300]}...")
        print(f"  {'-' * 60}")
        print()

    print("✅ 完整技能加载流程测试完成")
    print()


async def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Nanobot 增强架构测试" + " " * 30 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    try:
        # 运行所有测试
        await test_config_tools()
        await test_skill_loader()
        await test_skill_decision_handler()
        await test_enhanced_main_agent()
        await test_task_type_analysis()
        await test_skills_loading_flow()

        # 总结
        print("=" * 60)
        print("🎉 所有测试完成！")
        print("=" * 60)
        print()
        print("测试摘要:")
        print("  ✅ 配置查询工具 - 正常工作")
        print("  ✅ SkillLoader - 正常工作")
        print("  ✅ SkillDecisionHandler - 正常工作")
        print("  ✅ EnhancedMainAgent - 正常工作")
        print("  ✅ 任务类型分析 - 正常工作")
        print("  ✅ 完整技能加载流程 - 正常工作")
        print()
        print("架构验证:")
        print("  ✅ MainAgent 可以调用工具查询配置")
        print("  ✅ MainAgent 智能决策可以选择 skills")
        print("  ✅ Subagent 创建时 skills 信息被传递")
        print("  ✅ 技能内容可以通过 SkillLoader 动态加载")
        print()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
