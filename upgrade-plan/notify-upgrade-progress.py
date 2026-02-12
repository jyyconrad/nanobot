"""
Nanobot 升级计划通知脚本

功能:
1. 读取升级计划跟踪文件
2. 检查子代理状态
3. 发送进度通知到飞书

使用方法:
    python upgrade-plan/notify-upgrade-progress.py
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 默认配置
DEFAULT_TRACKING_FILE = "upgrade-plan/upgrade-tracking.json"
DEFAULT_FEISHU_USER = "ou_b400e7dae9b583a4e64415293e8b5025"  # 江神的用户 ID


def load_tracking_data(tracking_file: str) -> Optional[Dict[str, Any]]:
    """加载跟踪数据"""
    try:
        with open(tracking_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 无法加载跟踪数据: {e}", file=sys.stderr)
        return None


def format_progress_message(tracking_data: Dict[str, Any]) -> str:
    """格式化进度消息"""
    lines = []
    
    # 标题
    lines.append("🤖 Nanobot 升级计划进度更新")
    lines.append("")
    lines.append(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # 项目状态
    upgrade_session = tracking_data.get("upgrade_session", {})
    lines.append(f"📋 项目状态: {upgrade_session.get('status', 'unknown')}")
    lines.append(f"📌 当前版本: {tracking_data.get('current_version', 'unknown')}")
    lines.append("")
    
    # 子代理状态
    lines.append("🔄 子代理状态:")
    for name, agent_data in tracking_data.get("subagents", {}).items():
        status = agent_data.get("status", "unknown")
        start_time = agent_data.get("start_time", "")
        
        if status == "running":
            lines.append(f"   ✅ {name}: {status}")
            if start_time:
                lines.append(f"      开始时间: {start_time}")
        elif status == "completed":
            lines.append(f"   ✅ {name}: {status}")
        elif status == "pending":
            lines.append(f"   ⏳ {name}: {status}")
        else:
            lines.append(f"   ❓ {name}: {status}")
    
    lines.append("")
    
    # 里程碑进度
    lines.append("📈 里程碑进度:")
    for milestone in tracking_data.get("milestones", []):
        version = milestone.get("version", "unknown")
        status = milestone.get("status", "unknown")
        completion = milestone.get("completion", 0)
        
        status_emoji = {
            "pending": "⏳",
            "planning": "📝",
            "in_progress": "🔄",
            "completed": "✅",
            "failed": "❌"
        }.get(status, "❓")
        
        lines.append(f"   {status_emoji} {version}: {status} ({completion}%)")
    
    lines.append("")
    
    # Cron Job 状态
    cron_job = tracking_data.get("cron_job", {})
    lines.append(f"⏱️ 监控任务: {'启用' if cron_job.get('enabled') else '禁用'}")
    if cron_job.get("next_run_at"):
        next_run = datetime.fromtimestamp(cron_job["next_run_at"] / 1000)
        lines.append(f"   下次运行: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    lines.append("")
    lines.append("---")
    lines.append("如需查看详细状态，请回复: 查看 nanobot 升级进度")
    
    return "\n".join(lines)


def send_feishu_notification(message: str, user_id: str) -> bool:
    """发送飞书通知"""
    try:
        # 尝试使用 OpenClaw 的 message 工具
        # 这里我们通过创建一个临时 Python 文件来调用 OpenClaw 的 API
        
        # 方法 1: 通过 subprocess 调用 openclaw 命令
        # 注意：这里需要用户手动执行，或者我们需要有其他方式
        
        # 方法 2: 创建一个标记文件，让主会话检测到并发送
        notify_file = Path(".nanobot_upgrade_notify_pending")
        notify_file.write_text(json.dumps({
            "message": message,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        print(f"✅ 已创建飞书通知标记文件: {notify_file}", file=sys.stderr)
        print(f"消息内容:\n{message}", file=sys.stderr)
        return True
        
    except Exception as e:
        print(f"❌ 发送飞书通知失败: {e}", file=sys.stderr)
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nanobot 升级计划通知")
    parser.add_argument(
        "--tracking-file",
        default=DEFAULT_TRACKING_FILE,
        help="跟踪文件路径"
    )
    parser.add_argument(
        "--feishu-user",
        default=DEFAULT_FEISHU_USER,
        help="飞书用户 ID"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印消息，不发送通知"
    )
    
    args = parser.parse_args()
    
    # 加载跟踪数据
    tracking_data = load_tracking_data(args.tracking_file)
    if not tracking_data:
        return 1
    
    # 格式化进度消息
    message = format_progress_message(tracking_data)
    
    # 发送通知
    if args.dry_run:
        print(message)
        return 0
    else:
        success = send_feishu_notification(message, args.feishu_user)
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
