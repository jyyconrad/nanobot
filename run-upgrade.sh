#!/bin/bash
# 运行 Nanobot v0.3.0 升级任务
cd /Users/jiangyayun/develop/code/work_code/nanobot

echo "=== 启动 Nanobot v0.3.0 升级计划 ==="

# 使用 openclaw 技能调用 multi-coding-agent
openclaw agent --local <<EOF
使用 multi-coding-agent 实施 Nanobot v0.3.0 升级计划
项目路径: /Users/jiangyayun/develop/code/work_code/nanobot
升级计划: /Users/jiangyayun/develop/code/work_code/nanobot/upgrade-plan/v0.3.0-upgrade-plan.md

实施原则:
1. 按阶段顺序执行：准备 → 持续工作机制 → 记忆系统 → 技能系统 → 文件管理 → 集成测试 → 收尾
2. 每个阶段完成后进行 E2E 验证
3. 验证通过后更新进度到 upgrade-tracking.json
4. 如有错误，立即停止并报告

请开始执行升级计划。
EOF
