# Nanobot 升级计划 Heartbeat 响应逻辑

当收到包含 `HEARTBEAT_UPGRADE_MONITOR_NANOBOT` 的 systemEvent 时，执行以下检查：

## 检查流程

1. **读取跟踪文件**
   ```python
   import json
   from pathlib import Path
   
   tracking_file = Path("/Users/jiangyayun/develop/code/work_code/nanobot/upgrade-plan/upgrade-tracking.json")
   with open(tracking_file) as f:
       tracking_data = json.load(f)
   ```

2. **检查子代理状态**
   ```python
   # 使用 sessions_list 查看子代理状态
   sessions_list({"activeMinutes": 5})
   ```

3. **检查计划文件**
   ```python
   required_files = [
       "upgrade-plan/v0.3.0-upgrade-plan.md",
       "upgrade-plan/v0.4.0-upgrade-plan.md",
       "upgrade-plan/comparative-analysis.md"
   ]
   ```

4. **检测状态变化**
   - 检查子代理状态是否变化（pending -> running -> completed）
   - 检查里程碑完成度是否更新
   - 检查是否有错误发生

5. **发送飞书通知**（如有重要变化）
   ```python
   message({
       "action": "send",
       "channel": "feishu",
       "to": "ou_b400e7dae9b583a4e64415293e8b5025",
       "message": "🤖 Nanobot 升级计划进度更新\n\n..."
   })
   ```

## 飞书通知格式

```
🤖 Nanobot 升级计划进度更新

⏰ 时间: 2026-02-12 23:45:00

📋 项目状态: in_progress
📌 当前版本: 0.2.1

🔄 子代理状态:
   ✅ planning: completed
   🔄 implementation: in_progress

📈 里程碑进度:
   ✅ v0.3.0: in_progress (45%)
   ⏳ v0.4.0: planning (0%)

⏱️ 监控任务: 启用
   下次运行: 2026-02-13 00:15:00

---
如需查看详细状态，请回复: 查看 nanobot 升级进度
```

## 触发通知的事件

**立即通知**：
- 规划阶段完成
- 实施阶段开始
- 里程碑完成
- 测试全部通过
- 发生错误

**每小时通知**：
- 进度更新
- 子代理状态变化

## 查看详细状态

用户回复"查看 nanobot 升级进度"时，读取并展示：
- `upgrade-plan/upgrade-tracking.json`
- `upgrade-plan/INITIAL-SETUP.md`
- 如果有计划文件，也展示
