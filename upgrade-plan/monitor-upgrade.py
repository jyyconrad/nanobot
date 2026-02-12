"""
Nanobot 升级计划监控脚本

功能:
1. 定期检查升级计划状态
2. 如果任务因意外停止，自动恢复
3. 发送进度通知
4. 验证任务完成状态
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from nanobot.agent.message_bus import MessageBus
from nanobot.agent.message_schemas import MessageType, MessagePriority


class UpgradeMonitor:
    """升级计划监控器"""

    def __init__(self, tracking_file: str):
        self.tracking_file = tracking_file
        self.tracking_data: Dict[str, Any] = {}
        self.message_bus = MessageBus(backend="memory")

    def load_tracking_data(self) -> bool:
        """加载跟踪数据"""
        try:
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                self.tracking_data = json.load(f)
            return True
        except Exception as e:
            print(f"❌ 无法加载跟踪数据: {e}")
            return False

    def save_tracking_data(self) -> bool:
        """保存跟踪数据"""
        try:
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(self.tracking_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ 无法保存跟踪数据: {e}")
            return False

    def check_subagent_status(self, agent_name: str) -> str:
        """检查子代理状态"""
        try:
            import subprocess
            result = subprocess.run(
                ["openclaw", "sessions", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout

            # 检查子代理是否在运行
            if agent_name in output:
                return "running"
            else:
                return "stopped"
        except Exception as e:
            print(f"⚠️ 无法检查子代理状态: {e}")
            return "unknown"

    def check_plan_files(self) -> bool:
        """检查升级计划文件是否存在"""
        required_files = [
            "upgrade-plan/v0.3.0-upgrade-plan.md",
            "upgrade-plan/v0.4.0-upgrade-plan.md",
            "upgrade-plan/comparative-analysis.md"
        ]

        project_root = Path(self.tracking_file).parent.parent
        missing_files = []

        for file in required_files:
            if not (project_root / file).exists():
                missing_files.append(file)

        if missing_files:
            print(f"❌ 缺失计划文件: {', '.join(missing_files)}")
            return False

        return True

    def resume_planning(self) -> bool:
        """恢复规划任务"""
        print("🔄 尝试恢复规划任务...")

        try:
            # TODO: 这里应该调用 sessions_spawn 恢复任务
            # 暂时只记录日志
            self.tracking_data["subagents"]["planning"]["status"] = "resumed"
            self.tracking_data["subagents"]["planning"]["resume_time"] = datetime.now().isoformat()
            self.save_tracking_data()

            print("✅ 规划任务已标记为恢复")
            return True
        except Exception as e:
            print(f"❌ 恢复规划任务失败: {e}")
            return False

    def check_progress(self) -> Dict[str, Any]:
        """检查升级进度"""
        progress = {
            "total_completion": 0,
            "milestones": [],
            "subagents": {}
        }

        # 检查子代理状态
        for name, agent_data in self.tracking_data.get("subagents", {}).items():
            status = self.check_subagent_status(name)
            progress["subagents"][name] = {
                "current_status": agent_data.get("status"),
                "runtime_status": status,
                "session_key": agent_data.get("session_key")
            }

        # 检查里程碑
        for milestone in self.tracking_data.get("milestones", []):
            progress["milestones"].append({
                "version": milestone.get("version"),
                "status": milestone.get("status"),
                "completion": milestone.get("completeness", 0)
            })

        # 计算总完成度
        if self.tracking_data.get("milestones"):
            total = sum(m.get("completeness", 0) for m in self.tracking_data.get("milestones", []))
            progress["total_completion"] = total / len(self.tracking_data["milestones"])

        return progress

    def send_notification(self, message: str, priority: MessagePriority = MessagePriority.NORMAL):
        """发送通知"""
        try:
            # 发送到飞书
            # TODO: 实现飞书消息发送
            print(f"📢 通知: {message}")

        except Exception as e:
            print(f"⚠️ 发送通知失败: {e}")

    def run_check(self) -> bool:
        """执行检查一次"""
        print(f"\n{'='*60}")
        print(f"📊 Nanobot 升级计划监控检查")
        print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        # 1. 加载跟踪数据
        if not self.load_tracking_data():
            return False

        # 2. 检查项目状态
        project_status = self.tracking_data.get("upgrade_session", {}).get("status")
        print(f"📋 项目状态: {project_status}")

        if project_status == "completed":
            print("✅ 升级计划已完成，无需继续监控")
            return True

        # 3. 检查规划任务
        planning_status = self.tracking_data.get("subagents", {}).get("planning", {}).get("status")
        print(f"📝 规划任务状态: {planning_status}")

        if planning_status == "running":
            runtime_status = self.check_subagent_status("planning")
            print(f"   运行时状态: {runtime_status}")

            if runtime_status == "stopped":
                print("⚠️ 规划任务意外停止，尝试恢复...")
                self.resume_planning()

        elif planning_status == "completed":
            # 检查计划文件
            if self.check_plan_files():
                print("✅ 规划完成，计划文件齐全")
            else:
                print("❌ 规划完成但缺少计划文件")
                return False

        # 4. 检查进度
        progress = self.check_progress()
        print(f"\n📈 总完成度: {progress['total_completion']:.1f}%")

        for milestone in progress['milestones']:
            print(f"   - {milestone['version']}: {milestone['status']} ({milestone['completion']}%)")

        # 5. 发送通知（如有重要更新）
        if planning_status == "completed" and not self.tracking_data.get("notified_planning"):
            self.send_notification("规划阶段已完成，准备开始实施", MessagePriority.HIGH)
            self.tracking_data["notified_planning"] = True
            self.save_tracking_data()

        # 6. 返回结果
        print(f"\n{'='*60}\n")
        return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Nanobot 升级计划监控")
    parser.add_argument(
        "--tracking-file",
        default="upgrade-plan/upgrade-tracking.json",
        help="跟踪文件路径"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="只执行一次检查"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=1800,
        help="检查间隔（秒），默认 30 分钟"
    )

    args = parser.parse_args()

    monitor = UpgradeMonitor(args.tracking_file)

    if args.once:
        # 只执行一次
        success = monitor.run_check()
        sys.exit(0 if success else 1)
    else:
        # 持续监控
        import time
        print(f"🔄 开始持续监控，检查间隔: {args.interval} 秒\n")

        while True:
            try:
                monitor.run_check()
                time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n\n⏹️ 监控已停止")
                break
            except Exception as e:
                print(f"\n❌ 监控过程中发生错误: {e}")
                time.sleep(60)  # 错误后等待 1 分钟再重试


if __name__ == "__main__":
    main()
