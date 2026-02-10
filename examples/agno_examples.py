"""
Agno 框架使用示例

本文件包含 Agno 框架的核心功能示例，用于学习和验证 Agno 的基本用法。

示例包括：
1. Agno 基础示例（Agent 创建、配置、prompt 模板、工具集成、记忆管理、会话管理）
2. 主代理（Main Agent）示例（集成 nanobot 的 prompt_system_v2、任务分析路由、子代理调用）
3. 子代理（Sub Agent）示例（任务专注、上下文隔离、父子代理通信）
4. 实用工具示例（文件读写、代码执行、Web 搜索和抓取、Git 操作）
5. 完整工作流示例（任务接收 → 分析 → 分解 → 执行 → 汇报、错误处理、进度跟踪）
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from agno.agent import Agent
    from agno.tools.toolkit import Toolkit
    from agno.tools.function import Function
    from agno.knowledge.knowledge import Knowledge
    from agno.team.team import Team
    from nanobot.agent.prompt_system_v2 import PromptSystemV2, get_prompt_system_v2
    from nanobot.agent.main_agent import MainAgent, create_main_agent
    from nanobot.agent.subagent.agno_subagent import AgnoSubagentManager, AgnoSubagentConfig
    from nanobot.agent.tools.filesystem import ReadFileTool, WriteFileTool, ListDirTool
    from nanobot.agent.tools.shell import ExecTool
    from nanobot.agent.tools.web import WebSearchTool, WebFetchTool
    from nanobot.agent.tools.registry import ToolRegistry
    logger.info("✅ 所有模块导入成功")
except ImportError as e:
    logger.error(f"❌ 模块导入失败: {e}")
    import traceback
    logger.error(f"详细错误信息: {traceback.format_exc()}")
    sys.exit(1)


# ============================================================================
# 示例 1: Agno 基础示例 - Agent 创建和配置
# ============================================================================

def simple_agent_example():
    """创建一个简单的 Agent"""
    logger.info("\n" + "="*60)
    logger.info("示例 1: 简单 Agent 创建和配置")
    logger.info("="*60)

    try:
        # 创建 Agent
        agent = Agent(
            name="hello_agent",
            model="openai:gpt-4o-mini",
            instructions="你是一个友好的助手，用简洁的中文回答问题。",
        )

        logger.info("✅ Agent 创建成功")
        
        # 运行 Agent
        response = agent.run("你好，用一句话介绍一下你自己")
        logger.info(f"\n🤖 Agent 回复:\n{response.content}")
        return True
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
        return False


# ============================================================================
# 示例 2: Agno 基础示例 - 工具集成和使用
# ============================================================================

def get_weather(city: str) -> str:
    """获取城市天气"""
    weather_data = {
        "北京": "晴天，气温 25°C，空气质量良",
        "上海": "多云，气温 22°C，空气质量优",
        "深圳": "阴天，气温 28°C，空气质量良",
        "杭州": "小雨，气温 20°C，空气质量优",
    }
    return weather_data.get(city, f"{city} 的天气数据暂未录入")


def get_current_time() -> str:
    """获取当前时间"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def agent_with_tools_example():
    """创建带工具的 Agent"""
    logger.info("\n" + "="*60)
    logger.info("示例 2: 工具集成和使用")
    logger.info("="*60)

    try:
        # 定义工具函数
        weather_tool = Function(
            name="get_weather",
            description="查询指定城市的天气情况",
            func=get_weather
        )

        time_tool = Function(
            name="get_current_time",
            description="获取当前的日期和时间",
            func=get_current_time
        )

        # 创建 Agent
        agent = Agent(
            name="assistant_agent",
            model="openai:gpt-4o-mini",
            instructions="你是一个智能助手，可以使用工具查询天气和时间。",
            tools=[weather_tool, time_tool]
        )

        logger.info("✅ Agent 配置工具成功")
        
        # 运行 Agent
        questions = [
            "北京今天天气怎么样？",
            "现在是什么时间？",
            "上海和深圳的天气对比一下"
        ]

        for question in questions:
            logger.info(f"\n❓ 用户: {question}")
            response = agent.run(question)
            logger.info(f"🤖 Agent: {response.content}")

        return True
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
        return False


# ============================================================================
# 示例 3: Agno 基础示例 - 记忆管理
# ============================================================================

def agent_with_memory_example():
    """创建带记忆的 Agent"""
    logger.info("\n" + "="*60)
    logger.info("示例 3: 记忆管理")
    logger.info("="*60)

    try:
        # 创建 Agent（Agno 框架中的记忆管理方式不同，这里演示基本的会话记忆）
        agent = Agent(
            name="memory_agent",
            model="openai:gpt-4o-mini",
            instructions="你是一个有记忆的助手，记住用户的偏好和信息。",
        )

        # 第一次对话
        logger.info("\n💬 第一次对话:")
        response1 = agent.run("我叫小明，喜欢吃苹果，爱好是编程。")
        logger.info(f"🤖 Agent: {response1.content}")

        # 第二次对话（测试记忆）
        logger.info("\n💬 第二次对话:")
        response2 = agent.run("你还记得我的名字和爱好吗？")
        logger.info(f"🤖 Agent: {response2.content}")

        return True
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False


# ============================================================================
# 示例 4: 主代理（Main Agent）示例 - 集成 prompt_system_v2
# ============================================================================

def main_agent_with_prompt_system_v2_example():
    """创建集成 prompt_system_v2 的主代理"""
    logger.info("\n" + "="*60)
    logger.info("示例 4: 主代理集成 prompt_system_v2")
    logger.info("="*60)

    try:
        # 初始化提示词系统 V2
        prompt_system = get_prompt_system_v2()
        
        # 配置主代理
        main_agent = create_main_agent(
            session_id="test_session_123",
            prompt_system_v2=prompt_system
        )

        logger.info("✅ 主代理创建成功")
        
        # 获取系统提示词
        system_prompt = prompt_system.build_main_agent_prompt()
        logger.info(f"\n📝 系统提示词预览:\n{system_prompt[:200]}...")

        return True
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False


# ============================================================================
# 示例 5: 子代理（Sub Agent）示例 - Agno 子代理创建
# ============================================================================

def agno_subagent_basic_example():
    """创建 Agno 子代理"""
    logger.info("\n" + "="*60)
    logger.info("示例 5: Agno 子代理创建和配置")
    logger.info("="*60)

    try:
        from nanobot.providers.base import LLMProvider
        from nanobot.providers.litellm_provider import LiteLLMProvider

        # 初始化 LLM 提供者
        provider = LiteLLMProvider()
        
        # 初始化 Agno 子代理管理器
        config = AgnoSubagentConfig(
            max_iterations=10,
            timeout=300,
            model="gpt-4o-mini"
        )
        
        manager = AgnoSubagentManager(
            provider=provider,
            workspace=Path.cwd(),
            bus=None,
            config=config
        )

        logger.info("✅ Agno 子代理管理器创建成功")
        
        return True
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False


# ============================================================================
# 示例 6: 实用工具示例 - 文件操作
# ============================================================================

def file_operations_example():
    """演示文件读写工具的使用"""
    logger.info("\n" + "="*60)
    logger.info("示例 6: 文件操作工具")
    logger.info("="*60)

    try:
        # 创建工具注册表
        tools = ToolRegistry()
        tools.register(ReadFileTool())
        tools.register(WriteFileTool())
        tools.register(ListDirTool())

        logger.info("✅ 文件操作工具注册成功")
        
        # 创建测试文件
        test_file = "test_agno.txt"
        test_content = "这是 Agno 框架的文件操作测试内容"
        
        # 写入文件
        write_result = tools.execute("write_file", {"file_path": test_file, "content": test_content})
        logger.info(f"📝 文件写入结果: {write_result}")
        
        # 读取文件
        read_result = tools.execute("read_file", {"file_path": test_file})
        logger.info(f"📖 文件内容:\n{read_result}")
        
        # 删除测试文件
        import os
        if os.path.exists(test_file):
            os.remove(test_file)

        return True
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False


# ============================================================================
# 示例 7: 实用工具示例 - 代码执行
# ============================================================================

def code_execution_example():
    """演示代码执行工具的使用"""
    logger.info("\n" + "="*60)
    logger.info("示例 7: 代码执行工具")
    logger.info("="*60)

    try:
        # 创建工具
        exec_tool = ExecTool(
            working_dir=str(Path.cwd()),
            timeout=30,
            restrict_to_workspace=True
        )

        logger.info("✅ 代码执行工具初始化成功")
        
        # 执行简单命令
        result = exec_tool.execute({"command": "echo 'Hello from Agno!'"})
        logger.info(f"🚀 命令执行结果:\n{result}")

        return True
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False


# ============================================================================
# 示例 8: Team 协同示例
# ============================================================================

def team_collaboration_example():
    """使用 Team 协同"""
    logger.info("\n" + "="*60)
    logger.info("示例 8: Team 协同")
    logger.info("="*60)

    try:
        # 创建协同的 Agents
        writer_agent = Agent(
            name="writer",
            model="openai:gpt-4o-mini",
            instructions="你擅长写作，负责生成文章内容。"
        )

        editor_agent = Agent(
            name="editor",
            model="openai:gpt-4o-mini",
            instructions="你擅长编辑，负责优化文章的语言和结构。"
        )

        # 创建 Team
        team = Team(
            agents=[writer_agent, editor_agent],
            instructions="协同完成写作任务：writer 负责初稿，editor 负责润色。",
            model="openai:gpt-4o-mini"
        )

        logger.info("✅ Team 创建成功")
        
        # 运行 Team
        response = team.run("写一段 100 字左右的介绍，说明 AI 助手如何帮助程序员提高效率。")
        logger.info(f"\n🤖 Team 协同结果:\n{response.content}")

        return True
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False


# ============================================================================
# 示例 3: Team 协同
# ============================================================================

def team_example():
    """使用 Team 协同"""
    print("\n" + "="*60)
    print("示例 3: Team 协同")
    print("="*60)

    # 创建协同的 Agents
    writer_agent = Agent(
        name="writer",
        model="openai/gpt-4o-mini",
        instructions="你擅长写作，负责生成文章内容。"
    )

    editor_agent = Agent(
        name="editor",
        model="openai/gpt-4o-mini",
        instructions="你擅长编辑，负责优化文章的语言和结构。"
    )

    # 创建 Team
    team = Team(
        agents=[writer_agent, editor_agent],
        instructions="协同完成写作任务：writer 负责初稿，editor 负责润色。",
        model="openai/gpt-4o-mini"
    )

    # 运行 Team
    try:
        response = team.run("写一段 100 字左右的介绍，说明 AI 助手如何帮助程序员提高效率。")
        print(f"\n🤖 Team 协同结果:\n{response.content}")
        return True
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        return False


# ============================================================================
# 示例 4: 模板提示词策略
# ============================================================================

class TemplateAgent:
    """使用模板 + 占位符的 Agent"""

    def __init__(self, name: str, model: str = "openai/gpt-4o-mini"):
        self.name = name
        self.model = model
        self.template = self._load_template()
        self.agent = self._create_agent()

    def _load_template(self) -> str:
        """加载提示词模板"""
        template = """# 系统身份

你是一个 AI 智能体，名为 {{AGENT_NAME}}

# 核心能力

## 技能列表
{{SKILLS}}

## 工具列表
{{TOOLS}}

# 使用指导

{{TOOL_GUIDE}}
"""
        return template

    def _build_system_prompt(self, skills: list, tools: list) -> str:
        """构建系统提示词"""
        prompt = self.template.replace("{{AGENT_NAME}}", self.name)
        prompt = prompt.replace("{{SKILLS}}", "\n".join([f"- {s}" for s in skills]))
        prompt = prompt.replace("{{TOOLS}}", "\n".join([f"- {t.name}" for t in tools]))

        # 简单的工具指导
        tool_guide = "使用工具时，确保输入参数格式正确，并根据工具返回结果生成回答。"
        prompt = prompt.replace("{{TOOL_GUIDE}}", tool_guide)

        return prompt

    def _create_agent(self) -> Agent:
        """创建 Agent"""
        skills = ["对话", "信息查询", "任务执行"]
        tools = []

        system_prompt = self._build_system_prompt(skills, tools)

        agent = Agent(
            name=self.name,
            model=self.model,
            instructions=system_prompt
        )

        return agent

    def run(self, message: str) -> str:
        """运行 Agent"""
        response = self.agent.run(message)
        return response.content


def template_agent_example():
    """使用模板策略的 Agent"""
    print("\n" + "="*60)
    print("示例 4: 模板提示词策略")
    print("="*60)

    try:
        agent = TemplateAgent(name="TemplateAgent")
        print("\n✅ 模板 Agent 创建成功")
        print("\n📝 系统提示词预览:")
        print("-" * 40)
        print(agent.agent.instructions[:200] + "...")
        print("-" * 40)

        response = agent.run("你叫什么名字？你的技能有哪些？")
        print(f"\n🤖 Agent 回复:\n{response.content}")

        return True
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        return False


# ============================================================================
# 示例 5: 带记忆的 Agent
# ============================================================================

def agent_with_memory_example():
    """创建带记忆的 Agent"""
    logger.info("\n" + "="*60)
    logger.info("示例 3: 记忆管理")
    logger.info("="*60)

    try:
        # 创建 Agent（Agno 框架中的记忆管理方式不同，这里演示基本的会话记忆）
        agent = Agent(
            name="memory_agent",
            model="openai:gpt-4o-mini",
            instructions="你是一个有记忆的助手，记住用户的偏好和信息。",
        )

        # 第一次对话
        logger.info("\n💬 第一次对话:")
        response1 = agent.run("我叫小明，喜欢吃苹果，爱好是编程。")
        logger.info(f"🤖 Agent: {response1.content}")

        # 第二次对话（测试记忆）
        logger.info("\n💬 第二次对话:")
        response2 = agent.run("你还记得我的名字和爱好吗？")
        logger.info(f"🤖 Agent: {response2.content}")

        return True
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False
        return False


# ============================================================================
# 示例 9: 完整工作流示例 - 任务执行和监控
# ============================================================================

def complete_workflow_example():
    """演示完整工作流：任务接收 → 分析 → 分解 → 执行 → 汇报"""
    logger.info("\n" + "="*60)
    logger.info("示例 9: 完整工作流示例")
    logger.info("="*60)

    try:
        # 创建主代理
        main_agent = create_main_agent(session_id="workflow_test_session")
        
        logger.info("✅ 工作流初始化成功")
        
        # 模拟任务执行
        logger.info("\n📋 任务：创建一个简单的 Python 脚本")
        
        # 创建测试脚本
        test_script_content = """#!/usr/bin/env python3
\"\"\"简单的 Python 脚本示例\"\"\"

def hello_agno():
    return "Hello from Agno!"

if __name__ == "__main__":
    print(hello_agno())
"""
        
        test_script_path = "hello_agno.py"
        
        # 写入文件
        write_tool = WriteFileTool()
        write_tool.execute({"file_path": test_script_path, "content": test_script_content})
        
        logger.info("✅ 脚本创建成功")
        
        # 执行脚本
        exec_tool = ExecTool(working_dir=str(Path.cwd()), timeout=30)
        result = exec_tool.execute({"command": f"python {test_script_path}"})
        
        logger.info(f"🚀 脚本执行结果:\n{result}")
        
        # 删除测试文件
        import os
        if os.path.exists(test_script_path):
            os.remove(test_script_path)
        
        logger.info("✅ 工作流完成")
        
        return True
    except Exception as e:
        logger.error(f"❌ 运行失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False


# ============================================================================
# 主函数
# ============================================================================

def main():
    """运行所有示例"""
    logger.info("\n" + "="*60)
    logger.info("Agno 框架使用示例集合")
    logger.info("="*60)

    results = {}

    # 运行所有示例
    results["simple_agent"] = simple_agent_example()
    results["agent_with_tools"] = agent_with_tools_example()
    results["agent_with_memory"] = agent_with_memory_example()
    results["main_agent_prompt_system_v2"] = main_agent_with_prompt_system_v2_example()
    results["agno_subagent_basic"] = agno_subagent_basic_example()
    results["file_operations"] = file_operations_example()
    results["code_execution"] = code_execution_example()
    results["team_collaboration"] = team_collaboration_example()
    results["complete_workflow"] = complete_workflow_example()

    # 汇总结果
    logger.info("\n" + "="*60)
    logger.info("示例运行结果汇总")
    logger.info("="*60)

    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"{name:35} {status}")

    total = len(results)
    passed = sum(results.values())

    logger.info(f"\n总计: {passed}/{total} 示例通过")

    return all(results.values())


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\n⏹️ 用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ 发生错误: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        sys.exit(1)
