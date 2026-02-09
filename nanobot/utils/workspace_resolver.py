"""
Workspace 解析工具 - 确保 workspace 路径正确且一致

解决软链接、相对路径等问题
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def resolve_workspace(workspace: str | Path) -> Path:
    """
    解析并规范化 workspace 路径

    Args:
        workspace: workspace 路径（可能是相对路径、~、软链接）

    Returns:
        解析后的绝对路径
    """
    logger.debug(f"解析 workspace: {workspace}")

    # 转换为 Path
    path = Path(workspace).expanduser()

    # 解析软链接
    try:
        resolved = path.resolve()
        logger.debug(f"解析后路径: {resolved}")

        # 检查是否是符号链接
        if path.is_symlink():
            logger.warning(f"⚠️  workspace 是软链接: {path} -> {resolved}")
            logger.warning("建议删除软链接，使用真实目录")

        return resolved
    except Exception as e:
        logger.error(f"解析 workspace 失败: {e}")
        return path


def validate_workspace(workspace: Path) -> dict:
    """
    验证 workspace 配置

    Args:
        workspace: workspace 路径

    Returns:
        验证结果字典
    """
    issues = []
    warnings = []

    # 检查 1: 是否是绝对路径
    if not workspace.is_absolute():
        warnings.append("workspace 不是绝对路径，将使用 expanduser()")

    # 检查 2: 是否是软链接
    if workspace.is_symlink():
        issues.append("workspace 是软链接，可能导致路径混乱")
        issues.append(f"软链接目标: {workspace.resolve()}")

    # 检查 3: 目录是否存在
    if not workspace.exists():
        issues.append("workspace 目录不存在")
    elif not workspace.is_dir():
        issues.append("workspace 不是目录")

    # 检查 4: 是否可写
    if workspace.exists() and not workspace.is_dir():
        pass  # 不是目录，跳过
    elif workspace.exists() and workspace.is_dir():
        if not os.access(workspace, os.W_OK):
            issues.append("workspace 不可写")

    # 检查 5: 是否在项目目录内
    project_root = Path(__file__).parent.parent.parent
    if workspace.resolve().is_relative_to(project_root):
        warnings.append("workspace 在项目目录内，可能导致混淆")
        warnings.append(f"项目根: {project_root}")
        warnings.append(f"workspace: {workspace.resolve()}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "workspace": str(workspace.resolve()),
    }


def get_workspace_info(workspace: str | Path) -> dict:
    """
    获取 workspace 详细信息

    Args:
        workspace: workspace 路径

    Returns:
        workspace 信息字典
    """
    path = Path(workspace).expanduser()
    resolved = path.resolve()

    return {
        "original": str(workspace),
        "expanded": str(path),
        "resolved": str(resolved),
        "is_symlink": path.is_symlink(),
        "is_absolute": resolved.is_absolute(),
        "exists": resolved.exists(),
        "is_dir": resolved.is_dir() if resolved.exists() else False,
        "is_project_dir": Path(__file__).parent.parent.parent in resolved.parents,
    }


def diagnose_workspace_config(config_workspace: str) -> dict:
    """
    诊断 workspace 配置

    Args:
        config_workspace: 配置文件中的 workspace

    Returns:
        诊断结果
    """
    print("=" * 80)
    print("🔍 Workspace 配置诊断")
    print("=" * 80)
    print()

    # 1. 显示配置中的值
    print("📋 配置中的 workspace:")
    print(f"  原始值: {config_workspace}")
    print()

    # 2. 解析路径
    info = get_workspace_info(config_workspace)
    print("📊 路径解析:")
    print(f"  展开后: {info['expanded']}")
    print(f"  解析后: {info['resolved']}")
    print(f"  是软链接: {'是' if info['is_symlink'] else '否'}")
    print(f"  是绝对路径: {'是' if info['is_absolute'] else '否'}")
    print(f"  存在: {'是' if info['exists'] else '否'}")
    print(f"  是目录: {'是' if info['is_dir'] else '否'}")
    print(f"  在项目内: {'是' if info['is_project_dir'] else '否'}")
    print()

    # 3. 验证配置
    validation = validate_workspace(config_workspace)
    print("🔍 验证结果:")

    if validation["valid"]:
        print("  ✅ workspace 配置有效")
    else:
        print("  ❌ 发现问题:")
        for issue in validation["issues"]:
            print(f"     - {issue}")

    if validation["warnings"]:
        print("  ⚠️  警告:")
        for warning in validation["warnings"]:
            print(f"     - {warning}")
    print()

    # 4. 建议修复方案
    if not validation["valid"]:
        print("🛠️  建议修复方案:")
        print()

        if "软链接" in " ".join(validation["issues"]):
            print("  1. 删除软链接，创建真实目录:")
            print(f"     rm ~/.nanobot/workspace")
            print(f"     mkdir -p ~/.nanobot/workspace")
            print(f"     cp -r ~/.nanobot/workspace.backup/* ~/.nanobot/workspace/")

        if "在项目目录内" in " ".join(validation["warnings"]):
            print("  2. 使用独立的 workspace 目录:")
            print(f"     修改 config.json 中的 workspace 为:")
            print(f'     "workspace": "/Users/jiangyayun/.nanobot/workspace"')

    print()
    print("=" * 80)

    return {
        "info": info,
        "validation": validation,
    }


if __name__ == "__main__":
    import os
    import sys

    if len(sys.argv) > 1:
        config_workspace = sys.argv[1]
    else:
        # 默认测试
        config_workspace = "~/.nanobot/workspace"

    result = diagnose_workspace_config(config_workspace)
