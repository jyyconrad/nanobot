"""
Agno 框架使用示例

本文件包含 Agno 框架的核心功能示例，用于学习和验证 Agno 的基本用法。

示例包括：
1. 简单 Agent 示例
2. 带 Tools 的 Agent 示例
3. 带 Knowledge 的 Agent 示例
4. Team 协同示例
5. Hook 系统示例
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_path))

try:
    from agno import Agent, Toolkit, Function, Knowledge, Team
    print("✅ Agno 导入成功")
except ImportError as e:
    print(f"❌ Agno 导入失败: {e}")
    print("请确保已安装 agno: pip install agno")
    sys.exit(1)


# ============================================================================
# 示例 1: 简单 Agent
# ============================================================================

def simple_agent_example():
    """创建一个简单的 Agent"""
    print("\n" + "="*60)
    print("示例 1: 简单 Agent")
    print("="*60)

    # 创建 Agent
    agent = Agent(
        name="hello_agent",
        model="openai/gpt-4o-mini",
        instructions="你是一个友好的助手，用简洁的中文回答问题。",
    )

    # 运行 Agent
    try:
        response = agent.run("你好，用一句话介绍一下你自己")
        print(f"\n🤖 Agent 回复:\n{response.content}")
        return True
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        return False


# ============================================================================
# 示例 2: 带 Tools 的 Agent
# ============================================================================

def get_weather(city: str) -> str:
    """获取城市天气"""
    # 模拟天气查询
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
    print("\n" + "="*60)
    print("示例 2: 带 Tools 的 Agent")
    print("="*60)

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
        model="openai/gpt-4o-mini",
        instructions="你是一个智能助手，可以使用工具查询天气和时间。",
        tools=[weather_tool, time_tool]
    )

    # 运行 Agent
    try:
        questions = [
            "北京今天天气怎么样？",
            "现在是什么时间？",
            "上海和深圳的天气对比一下"
        ]

        for question in questions:
            print(f"\n❓ 用户: {question}")
            response = agent.run(question)
            print(f"🤖 Agent: {response.content}")

        return True
    except Exception as e:
        print(f"❌ 运行失败: {e}")
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
    print("\n" + "="*60)
    print("示例 5: 带记忆的 Agent")
    print("="*60)

    # 创建带记忆的 Agent
    agent = Agent(
        name="memory_agent",
        model="openai/gpt-4o-mini",
        instructions="你是一个有记忆的助手，记住用户的偏好和信息。",
        memory=True,  # 启用记忆
    )

    try:
        # 第一次对话
        print("\n💬 第一次对话:")
        response1 = agent.run("我叫小明，喜欢吃苹果，爱好是编程。")
        print(f"🤖 Agent: {response1.content}")

        # 第二次对话（测试记忆）
        print("\n💬 第二次对话:")
        response2 = agent.run("你还记得我的名字和爱好吗？")
        print(f"🤖 Agent: {response2.content}")

        return True
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        return False


# ============================================================================
# 主函数
# ============================================================================

def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("Agno 框架使用示例集合")
    print("="*60)

    results = {}

    # 运行所有示例
    results["simple_agent"] = simple_agent_example()
    results["agent_with_tools"] = agent_with_tools_example()
    results["team"] = team_example()
    results["template_agent"] = template_agent_example()
    results["agent_with_memory"] = agent_with_memory_example()

    # 汇总结果
    print("\n" + "="*60)
    print("示例运行结果汇总")
    print("="*60)

    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name:30} {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\n总计: {passed}/{total} 示例通过")

    return all(results.values())


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
