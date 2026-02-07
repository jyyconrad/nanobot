"""
命令行接口测试
"""

import subprocess

import pytest


def test_cli_help_command():
    """测试 CLI 帮助命令"""
    try:
        result = subprocess.run(
            ["python3", "-m", "nanobot", "--help"], capture_output=True, text=True, check=True
        )

        assert "Usage:" in result.stdout
        assert "nanobot" in result.stdout
        assert "Commands" in result.stdout  # 使用更宽松的匹配

        print("CLI 帮助命令测试通过")
    except Exception as e:
        pytest.fail(f"CLI 帮助命令测试失败: {e}")


def test_cli_version_command():
    """测试 CLI 版本命令"""
    try:
        result = subprocess.run(
            ["python3", "-m", "nanobot", "--version"], capture_output=True, text=True, check=True
        )

        assert "version" in result.stdout.lower() or "v" in result.stdout
        assert "." in result.stdout  # 应该包含版本号，如 1.0.0

        print("CLI 版本命令测试通过")
    except Exception as e:
        pytest.fail(f"CLI 版本命令测试失败: {e}")


def test_cli_invalid_command():
    """测试无效命令处理"""
    try:
        result = subprocess.run(
            ["python3", "-m", "nanobot", "invalid_command"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode != 0
        assert "No such command" in result.stderr or "error" in result.stderr.lower()

        print("CLI 无效命令处理测试通过")
    except Exception as e:
        pytest.fail(f"CLI 无效命令处理测试失败: {e}")


def test_cli_onboard_command():
    """测试 onboard 命令"""
    try:
        # 测试 onboard 命令帮助
        result = subprocess.run(
            ["python3", "-m", "nanobot", "onboard", "--help"],
            capture_output=True,
            text=True,
            check=True,
        )

        assert "onboard" in result.stdout
        assert "Options" in result.stdout  # 使用更宽松的匹配

        print("CLI onboard 命令帮助测试通过")
    except Exception as e:
        pytest.fail(f"CLI onboard 命令测试失败: {e}")


if __name__ == "__main__":
    test_cli_help_command()
    test_cli_version_command()
    test_cli_invalid_command()
    test_cli_onboard_command()
    print("所有 CLI 模块测试通过！")
