#!/usr/bin/env python3
"""
Nanobot 升级计划检查脚本（供 Heartbeat 调用）

功能:
1. 读取升级计划跟踪文件
2. 检查子代理状态
3. 检测状态变化
4. 发送飞书通知（如有重要变化）

使用方法:
    python upgrade-plan/check-upgrade-status.py

返回值:
    - 0: 检查成功，无需通知
    - 1: 检查成功，已发送通知
    - 2: 检查失败
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 项目路径
PROJECT_ROOT = Path("/Users/jiangyayun/develop/code/work_code/nanobot")
TRACKING_FILE = PROJECT_ROOT / "upgrade-plan" / "upgrade-tracking.json"
NOTIFY_FILE = Path(".nanobot_upgrade_notify_pending")

# 飞书用户 ID
FEISHU_USER_ID = "ou_b400e7dae9b583a4e64415293e8b5025"


def load_tracking_data() -> Optional[Dict[str, Any]]:
    """加载跟踪数据"""
    try:
        if not TRACKING_FILE.exists():
            print(f"⚠️ 跟踪文件不存在: {TRACKING_FILE}", file=sys.stderr)
            return None
            
        with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
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
    status = upgrade_session.get('status', 'unknown')
    
    status_emoji = {
        "in_progress": "🔄",
        "completed": "✅",
        "failed": "❌",
        "paused": "⏸️"
    }.get(status, "❓")
    
    lines.append(f"📋 项目状态: {status_emoji} {status}")
    lines.append(f"📌 当前版本: {tracking_data.get('current_version', 'unknown')}")
    lines.append("")
    
    # 子代理状态
    lines.append("🔄 子代理状态:")
    for name, agent_data in tracking_data.get("subagents", {}).items():
        status = agent_data.get("status", "unknown")
        
        status_emoji = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "resumed": "🔄"
        }.get(status, "❓")
        
        lines.append(f"   {status_emoji} {name}: {status}")
    
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


def check_state_changes(tracking_data: Dict[str, Any], previous_state: Dict[str, Any]) -> bool:
    """检查状态是否变化"""
    # 检查子代理状态
    subagents = tracking_data.get("subagents", {})
    prev_subagents = previous_state.get("subagents", {})
    
    for name, agent_data in subagents.items():
        prev_data = prev_subagents.get(name, {})
        if agent_data.get("status") != prev_data.get("status"):
            return True
    
    # 检查里程碑进度
    milestones = tracking_data.get("milestones", [])
    prev_milestones = previous_state.get("milestones", [])
    
    if len(milestones) != len(prev_milestones):
        return True
    
    for milestone, prev_milestone in zip(milestones, prev_milestones):
        if milestone.get("completion", 0) != prev_milestone.get("completion", 0):
            return True
    
    return False


def load_previous_state() -> Dict[str, Any]:
    """加载上一次的状态"""
    state_file = Path(".nanobot_upgrade_previous_state")
    try:
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_current_state(state: Dict[str, Any]) -> None:
    """保存当前状态"""
    state_file = Path(".nanobot_upgrade_previous_state")
    try:
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ 无法保存状态: {e}", file=sys.stderr)


def send_feishu_notification(message: str) -> bool:
    """发送飞书通知（通过创建标记文件）"""
    try:
        notify_data = {
            "channel": "feishu",
            "to": FEISHU_USER_ID,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(NOTIFY_FILE, 'w', encoding='utf-8') as f:
            json.dump(notify_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已创建飞书通知标记: {NOTIFY_FILE}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ 创建通知标记失败: {e}", file=sys.stderr)
        return False


def main():
    """主函数"""
    # 1. 加载跟踪数据
    tracking_data = load_tracking_data()
    if not tracking_data:
        return 2
    
    # 2. 加载上一次的状态
    previous_state = load_previous_state()
    
    # 3. 检查状态是否变化
    has_changes = check_state_changes(tracking_data, previous_state)
    
    if not has_changes and previous_state:
        # 状态无变化，无需通知
        print("ℹ️ 状态无变化，无需通知", file=sys.stderr)
        return 0
    
    # 4. 格式化进度消息
    message = format_progress_message(tracking_data)
    
    # 5. 发送飞书通知
    if send_feishu_notification(message):
        # 6. 保存当前状态
        save_current_state(tracking_data)
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())
