"""
Docker 工具 - 执行 Docker 操作
"""

from typing import Any, Dict

from nanobot.agent.tools.base import Tool


class DockerBuildTool(Tool):
    """构建 Docker 镜像"""

    name = "docker_build"
    description = "构建 Docker 镜像"

    parameters = {
        "context": {
            "type": "string",
            "description": "构建上下文路径",
            "required": True,
        },
        "tag": {
            "type": "string",
            "description": "镜像标签",
            "required": True,
        },
        "dockerfile": {
            "type": "string",
            "description": "Dockerfile 路径（可选）",
            "required": False,
        },
        "build_args": {
            "type": "object",
            "description": "构建参数（可选）",
            "required": False,
        },
    }

    async def execute(
        self, context: str, tag: str, dockerfile: str = None, build_args: dict = None
    ) -> str:
        """执行 Docker 镜像构建"""
        try:
            import subprocess

            cmd = ["docker", "build"]

            if dockerfile:
                cmd.extend(["-f", dockerfile])

            if build_args:
                for key, value in build_args.items():
                    cmd.extend([f"--build-arg", f"{key}={value}"])

            cmd.extend(["-t", tag, context])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            return f"Docker 镜像构建成功:\n{result.stdout}"

        except subprocess.CalledProcessError as e:
            return f"Docker 构建失败: {e.stderr}"
        except Exception as e:
            return f"Docker 构建失败: {str(e)}"


class DockerRunTool(Tool):
    """运行 Docker 容器"""

    name = "docker_run"
    description = "运行 Docker 容器"

    parameters = {
        "image": {
            "type": "string",
            "description": "镜像名称或 ID",
            "required": True,
        },
        "name": {
            "type": "string",
            "description": "容器名称（可选）",
            "required": False,
        },
        "ports": {
            "type": "array",
            "items": {"type": "string"},
            "description": "端口映射（可选，格式 '主机端口:容器端口'）",
            "required": False,
        },
        "volumes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "卷挂载（可选，格式 '主机路径:容器路径'）",
            "required": False,
        },
        "environment": {
            "type": "object",
            "description": "环境变量（可选）",
            "required": False,
        },
        "command": {
            "type": "string",
            "description": "命令（可选）",
            "required": False,
        },
    }

    async def execute(
        self,
        image: str,
        name: str = None,
        ports: list = None,
        volumes: list = None,
        environment: dict = None,
        command: str = None,
    ) -> str:
        """执行 Docker 容器运行"""
        try:
            import subprocess

            cmd = ["docker", "run", "-d"]

            if name:
                cmd.extend(["--name", name])

            if ports:
                for port in ports:
                    cmd.extend(["-p", port])

            if volumes:
                for volume in volumes:
                    cmd.extend(["-v", volume])

            if environment:
                for key, value in environment.items():
                    cmd.extend(["-e", f"{key}={value}"])

            cmd.append(image)

            if command:
                cmd.extend(["sh", "-c", command])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            container_id = result.stdout.strip()
            return f"Docker 容器运行成功: {container_id}"

        except subprocess.CalledProcessError as e:
            return f"Docker 容器运行失败: {e.stderr}"
        except Exception as e:
            return f"Docker 容器运行失败: {str(e)}"


class DockerComposeTool(Tool):
    """使用 Docker Compose"""

    name = "docker_compose"
    description = "使用 Docker Compose 执行操作"

    parameters = {
        "command": {
            "type": "string",
            "description": "Compose 命令（如 up、down、build）",
            "required": True,
        },
        "compose_file": {
            "type": "string",
            "description": "Compose 文件路径（可选）",
            "required": False,
        },
        "detach": {
            "type": "boolean",
            "description": "是否在后台运行（可选，默认 False）",
            "required": False,
        },
    }

    async def execute(
        self, command: str, compose_file: str = None, detach: bool = False
    ) -> str:
        """执行 Docker Compose 命令"""
        try:
            import subprocess

            cmd = ["docker", "compose"]

            if compose_file:
                cmd.extend(["-f", compose_file])

            cmd.append(command.lower())

            if detach and command.lower() == "up":
                cmd.append("-d")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            return f"Docker Compose 命令成功:\n{result.stdout}"

        except subprocess.CalledProcessError as e:
            return f"Docker Compose 命令失败: {e.stderr}"
        except Exception as e:
            return f"Docker Compose 命令失败: {str(e)}"


class DockerPsTool(Tool):
    """列出运行中的容器"""

    name = "docker_ps"
    description = "列出运行中的 Docker 容器"

    parameters = {
        "all": {
            "type": "boolean",
            "description": "是否显示所有容器（包括停止的）",
            "required": False,
        },
    }

    async def execute(self, all: bool = False) -> str:
        """执行 Docker 容器列表命令"""
        try:
            import subprocess

            cmd = ["docker", "ps"]

            if all:
                cmd.append("-a")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            return f"运行中的容器:\n{result.stdout}"

        except subprocess.CalledProcessError as e:
            return f"Docker 容器列表获取失败: {e.stderr}"
        except Exception as e:
            return f"Docker 容器列表获取失败: {str(e)}"


class DockerStopTool(Tool):
    """停止 Docker 容器"""

    name = "docker_stop"
    description = "停止 Docker 容器"

    parameters = {
        "container": {
            "type": "string",
            "description": "容器名称或 ID",
            "required": True,
        },
    }

    async def execute(self, container: str) -> str:
        """执行 Docker 容器停止"""
        try:
            import subprocess

            result = subprocess.run(
                ["docker", "stop", container],
                capture_output=True,
                text=True,
                check=True,
            )

            return f"Docker 容器停止成功: {result.stdout}"

        except subprocess.CalledProcessError as e:
            return f"Docker 容器停止失败: {e.stderr}"
        except Exception as e:
            return f"Docker 容器停止失败: {str(e)}"


class DockerRemoveTool(Tool):
    """删除 Docker 容器或镜像"""

    name = "docker_remove"
    description = "删除 Docker 容器或镜像"

    parameters = {
        "target": {
            "type": "string",
            "description": "容器名称/ID 或镜像名称/ID",
            "required": True,
        },
        "type": {
            "type": "string",
            "description": "目标类型：'container' 或 'image'",
            "required": True,
        },
        "force": {
            "type": "boolean",
            "description": "是否强制删除",
            "required": False,
        },
    }

    async def execute(
        self, target: str, type: str = "container", force: bool = False
    ) -> str:
        """执行 Docker 删除操作"""
        try:
            import subprocess

            cmd = ["docker", "rm" if type == "container" else "rmi"]

            if force:
                cmd.append("-f")

            cmd.append(target)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            return f"Docker {type} 删除成功: {result.stdout}"

        except subprocess.CalledProcessError as e:
            return f"Docker 删除失败: {e.stderr}"
        except Exception as e:
            return f"Docker 删除失败: {str(e)}"
