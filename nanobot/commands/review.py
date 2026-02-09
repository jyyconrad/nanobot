"""Code review command implementation."""

from typing import Any

from .base import Command


class ReviewCommand(Command):
    """代码审查命令"""

    @property
    def name(self) -> str:
        return "review"

    @property
    def description(self) -> str:
        return "Request a code review for current changes"

    @property
    def aliases(self) -> list[str]:
        return ["code-review", "cr"]

    async def execute(self, context: dict[str, Any]) -> str:
        """执行代码审查"""
        # 加载 code-review skill
        skills_loader = context["skills"]
        skill_content = skills_loader.load_skill("code-review")

        if not skill_content:
            return "❌ Code review skill not available"

        # 获取当前文件变更
        # 使用 git diff 获取变更

        # 使用 LLM 分析代码
        provider = context["provider"]
        messages = [
            {"role": "system", "content": skill_content},
            {"role": "user", "content": "Review this code:\n\n<code_changes>..."},
        ]

        response = await provider.chat(messages=messages, model=context.get("model"))
        return response.content
