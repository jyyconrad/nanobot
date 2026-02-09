"""
Git 工具 - 执行 Git 操作
"""

from typing import Any, Dict
from nanobot.agent.tools.base import Tool


class GitCloneTool(Tool):
    """克隆 Git 仓库"""

    name = "git_clone"
    description = "克隆 Git 仓库到本地目录"

    parameters = {
        "repo_url": {
            "type": "string",
            "description": "Git 仓库 URL",
            "required": True,
        },
        "target_dir": {
            "type": "string",
            "description": "目标目录（可选）",
            "required": False,
        },
        "branch": {
            "type": "string",
            "description": "分支名称（可选）",
            "required": False,
        },
    }

    async def execute(self, repo_url: str, target_dir: str = None, branch: str = None) -> str:
        """执行 Git 克隆"""
        try:
            import subprocess

            cmd = ["git", "clone"]
            if branch:
                cmd.extend(["-b", branch])

            cmd.append(repo_url)

            if target_dir:
                cmd.append(target_dir)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            return f"仓库克隆成功:\n{result.stdout}"

        except subprocess.CalledProcessError as e:
            return f"Git 克隆失败: {e.stderr}"
        except Exception as e:
            return f"Git 克隆失败: {str(e)}"


class GitCommitTool(Tool):
    """提交 Git 变更"""

    name = "git_commit"
    description = "提交当前工作区的变更"

    parameters = {
        "message": {
            "type": "string",
            "description": "提交消息",
            "required": True,
        },
        "files": {
            "type": "array",
            "items": {"type": "string"},
            "description": "要提交的文件列表（可选）",
            "required": False,
        },
    }

    async def execute(self, message: str, files: list = None) -> str:
        """执行 Git 提交"""
        try:
            import subprocess

            if files:
                add_cmd = ["git", "add"] + files
                subprocess.run(
                    add_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
            else:
                add_cmd = ["git", "add", "."]
                subprocess.run(
                    add_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                )

            commit_cmd = ["git", "commit", "-m", message]
            result = subprocess.run(
                commit_cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            return f"提交成功:\n{result.stdout}"

        except subprocess.CalledProcessError as e:
            return f"Git 提交失败: {e.stderr}"
        except Exception as e:
            return f"Git 提交失败: {str(e)}"


class GitPushTool(Tool):
    """推送到远程仓库"""

    name = "git_push"
    description = "将本地提交推送到远程仓库"

    parameters = {
        "remote": {
            "type": "string",
            "description": "远程仓库名称（默认 'origin'）",
            "required": False,
        },
        "branch": {
            "type": "string",
            "description": "分支名称（可选）",
            "required": False,
        },
    }

    async def execute(self, remote: str = "origin", branch: str = None) -> str:
        """执行 Git 推送"""
        try:
            import subprocess

            cmd = ["git", "push"]

            if remote:
                cmd.append(remote)

            if branch:
                cmd.append(branch)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            return f"推送成功:\n{result.stdout}"

        except subprocess.CalledProcessError as e:
            return f"Git 推送失败: {e.stderr}"
        except Exception as e:
            return f"Git 推送失败: {str(e)}"


class GitPullTool(Tool):
    """拉取远程变更"""

    name = "git_pull"
    description = "从远程仓库拉取变更"

    parameters = {
        "remote": {
            "type": "string",
            "description": "远程仓库名称（默认 'origin'）",
            "required": False,
        },
        "branch": {
            "type": "string",
            "description": "分支名称（可选）",
            "required": False,
        },
    }

    async def execute(self, remote: str = "origin", branch: str = None) -> str:
        """执行 Git 拉取"""
        try:
            import subprocess

            cmd = ["git", "pull"]

            if remote:
                cmd.append(remote)

            if branch:
                cmd.append(branch)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            return f"拉取成功:\n{result.stdout}"

        except subprocess.CalledProcessError as e:
            return f"Git 拉取失败: {e.stderr}"
        except Exception as e:
            return f"Git 拉取失败: {str(e)}"


class GitStatusTool(Tool):
    """获取 Git 状态"""

    name = "git_status"
    description = "获取当前工作区的状态"

    parameters = {}

    async def execute(self) -> str:
        """执行 Git 状态检查"""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "status"],
                capture_output=True,
                text=True,
                check=True,
            )

            return f"Git 状态:\n{result.stdout}"

        except subprocess.CalledProcessError as e:
            return f"Git 状态检查失败: {e.stderr}"
        except Exception as e:
            return f"Git 状态检查失败: {str(e)}"


class GitLogTool(Tool):
    """获取 Git 日志"""

    name = "git_log"
    description = "获取提交日志"

    parameters = {
        "limit": {
            "type": "integer",
            "description": "日志条数限制（可选）",
            "required": False,
        },
    }

    async def execute(self, limit: int = 10) -> str:
        """执行 Git 日志获取"""
        try:
            import subprocess

            cmd = ["git", "log", f"-{limit}"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            return f"提交日志:\n{result.stdout}"

        except subprocess.CalledProcessError as e:
            return f"Git 日志获取失败: {e.stderr}"
        except Exception as e:
            return f"Git 日志获取失败: {str(e)}"
