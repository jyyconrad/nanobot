# Nanobot 系统综合升级计划

> **版本**: v0.2.0
> **开始日期**: 2025-02-09
> **预计完成**: 2025-02-16
> **总工时**: 约 10 天

---

## 📋 升级概览

本次升级包含两个主要部分：

1. **提示词系统重构** - 将内置提示词迁移到 `config/prompts/` 并实现分层加载
2. **动态任务管理与监控** - 完整的任务管理框架、消息路由、定时巡检

两个部分可以**并行开发**，相互独立，最后一起集成测试。

---

## 🎯 一、提示词系统重构

### 1.1 升级目标

- 所有内置提示词存储在 `config/prompts/` 目录
- 分层加载机制：core → workspace → user → memory → decisions
- 支持 workspace 文件覆盖内置提示词
- 配置驱动的加载策略（`config/prompts/config.yaml`）

### 1.2 新目录结构

```
nanobot/
├── config/
│   ├── prompts/                    # 内置提示词目录
│   │   ├── core/                   # 核心提示词（必需）
│   │   │   ├── identity.md         # 系统身份
│   │   │   ├── soul.md             # 系统人设
│   │   │   └── tools.md           # 工具使用指导
│   │   ├── workspace/              # 工作区提示词
│   │   │   ├── agents.md          # AGENTS 指导
│   │   │   └── practices.md       # 最佳实践
│   │   ├── user/                  # 用户相关提示词
│   │   │   ├── profile.md         # 用户画像
│   │   │   └── preferences.md     # 用户偏好
│   │   ├── memory/                # 记忆提示词
│   │   │   └── memory.md          # 长期记忆模板
│   │   ├── decisions/             # 决策提示词
│   │   │   ├── task_analysis.md   # 任务分析指导
│   │   │   ├── skill_selection.md # 技能选择指导
│   │   │   └── agent_selection.md# Agent 选择指导
│   │   └── config.yaml           # 提示词加载配置
│   └── nanobot_config.yaml         # 主配置文件
└── workspace/                     # 用户工作区（保持不变）
    ├── AGENTS.md                   # 用户自定义（可选，覆盖内置）
    ├── USER.md                     # 用户自定义（可选）
    ├── SOUL.md                     # 用户自定义（可选）
    ├── MEMORY.md                   # 用户长期记忆（推荐）
    └── memory/                     # 每日记录
```

### 1.3 实现步骤（6 天）

| 阶段 | 任务 | 预计时间 | 优先级 |
|------|------|---------|--------|
| 1.1 | 创建提示词目录结构和所有文件 | 1天 | P0 |
| 1.2 | 实现 PromptSystemV2 类 | 2天 | P0 |
| 1.3 | 更新 ContextBuilder 使用新系统 | 1天 | P0 |
| 1.4 | 迁移现有内容到新系统 | 1天 | P1 |
| 1.5 | 测试和验证 | 1天 | P0 |
| 1.6 | 集成到定时任务巡检 | 0.5天 | P1 |

**详细说明：** 见 `upgrade-plan/PROMPT-SYSTEM-UPGRADE.md`

---

## 🚀 二、动态任务管理与监控

### 2.1 升级目标

1. **动态子代理创建** - ChatApps 接收消息后，mainAgent 分析并动态创建 subagent
2. **双向通信** - subagent 完成后返回结果给 mainAgent
3. **任务修正机制** - 新消息影响已有任务时，让 subagent 修正或重新工作
4. **定时监控任务** - 每小时获取执行进度和状态，及时修正计划
5. **可配置 Cron 系统** - 配置文件驱动的定时任务

### 2.2.1 新架构组件

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Chat Apps   │────►│ Message Bus  │────►│  Agent Loop  │
└──────────────┘     └──────────────┘     └──────────────┘
         ▲                     ▲                   │
         │         Message Router               ▼
         │              (新增)            ┌──────────────┐
         │                                 │ Task Manager │
         │                                 └──────────────┘
         │                     │                   │
         │                     │            ┌──────────────┐
         │                     └────────────┤ Subagents    │
         │                                  └──────────────┘
         │                                          │
         │                                          ▼
         └──────────────────────────────────────┐ Cron Jobs    │
                                                └──────────────┘
```

### 2.2 实现步骤（7 天）

| 阶段 | 任务 | 预计时间 | 优先级 |
|------|------|---------|--------|
| 2.1 | 创建任务管理器（TaskManager + Task） | 1天 | P0 |
| 2.2 | 增强子代理管理器（任务状态跟踪） | 1天 | P0 |
| 2.3 | 实现消息分析器和路由系统 | 2天 | P0 |
| 2.4 | 创建进度监控模块 | 1天 | P0 |
| 2.5 | 实现可配置 Cron 系统 | 2天 | P0 |
| 2.6 | 集成所有组件到 Agent Loop | 1天 | P0 |

**详细说明：** 见 `upgrade-plan/UPGRADE-PLAN.md` 和 `upgrade-plan/ENHANCED-CRON.md`

---

## 🔗 三、定时任务巡检集成

### 3.1 Cron 任务配置

更新 `upgrade-plan/cron-job-config-enhanced.json`，添加提示词系统巡检任务：

```json
{
  "version": "2.0",
  "globalSettings": {
    "notification": {
      "enabled": true,
      "channel": "feishu",
      "onFailure": true,
      "onSuccess": false
    },
    "execution": {
      "timeout": "10m",
      "maxConcurrent": 5,
      "priority": "normal"
    }
  },
  "jobs": [
    {
      "id": "task-progress-monitor",
      "name": "任务进度监控",
      "enabled": true,
      "schedule": {
        "kind": "cron",
        "expr": "0 * * * *",
        "tz": "Asia/Shanghai"
      },
      "description": "每小时检查所有任务的执行进度和状态",
      "action": {
        "type": "trigger_agent",
        "target": "mainAgent",
        "method": "monitor_tasks",
        "params": {
          "check_all_tasks": true,
          "auto_fix": true,
          "report_issues": true
        }
      }
    },
    {
      "id": "prompt-system-health-check",
      "name": "提示词系统健康检查",
      "enabled": true,
      "schedule": {
        "kind": "cron",
        "expr": "0 6 * * *",
        "tz": "Asia/Shanghai"
      },
      "description": "每天早上 6:00 检查提示词系统健康状态",
      "action": {
        "type": "trigger_agent",
        "target": "mainAgent",
        "method": "check_prompt_system",
        "params": {
          "check_integrity": true,
          "check_overrides": true,
          "check_cache": true,
          "report_issues": true
        }
      }
    },
    {
      "id": "daily-system-health-check",
      "name": "每日系统健康检查",
      "enabled": true,
      "schedule": {
        "kind": "cron",
        "expr": "0 9 * * *",
        "tz": "Asia/Shanghai"
      },
      "description": "每天早上 9:00 检查系统状态、资源使用、子代理状态",
      "action": {
        "type": "trigger_agent",
        "target": "mainAgent",
        "method": "health_check",
        "params": {
          "check_system": true,
          "check_resources": true,
          "check_subagents": true,
          "generate_report": true
        }
      }
    },
    {
      "id": "agent-status-monitor",
      "name": "Agent 状态监听",
      "enabled": true,
      "schedule": {
        "kind": "cron",
        "expr": "*/30 * * * *",
        "tz": "Asia/Shanghai"
      },
      "description": "每 30 秒监听 mainAgent 和子代理的状态",
      "action": {
        "type": "monitor_status",
        "targets": [
          {
            "agent": "mainAgent",
            "check": ["running", "responsive", "memory_usage"]
          },
          {
            "agent": "all_subagents",
            "check": ["running", "timeout_check", "resource_usage"]
          }
        ],
        "alertConditions": {
          "agent_not_responsive": {
            "threshold": "5m",
            "action": "restart"
          },
          "memory_usage_high": {
            "threshold": "80%",
            "action": "notify"
          },
          "subagent_timeout": {
            "threshold": "30m",
            "action": "terminate_and_notify"
          }
        }
      }
    },
    {
      "id": "cleanup-completed-tasks",
      "name": "清理已完成任务",
      "enabled": true,
      "schedule": {
        "kind": "cron",
        "expr": "0 2 * * *",
        "tz": "Asia/Shanghai"
      },
      "description": "每天凌晨 2:00 清理 7 天前的已完成任务",
      "action": {
        "type": "trigger_agent",
        "target": "mainAgent",
        "method": "cleanup_tasks",
        "params": {
          "days_to_keep": 7,
          "archive": false
        }
      }
    }
  ]
}
```

### 3.2 MainAgent 巡检方法

#### 3.2.1 监控任务进度

```python
async def monitor_tasks(
    self,
    check_all_tasks: bool = True,
    auto_fix: bool = True,
    report_issues: bool = True
) -> dict:
    """
    监控所有任务的执行进度和状态

    Args:
        check_all_tasks: 是否检查所有任务
        auto_fix: 是否自动修复问题
        report_issues: 是否汇报问题

    Returns:
        监控结果
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "tasks_checked": 0,
        "issues_found": [],
        "auto_fixes_applied": []
    }

    if not check_all_tasks:
        return results

    # 获取所有任务
    tasks = await self.task_manager.get_all_tasks()
    results["tasks_checked"] = len(tasks)

    for task in tasks:
        # 检查任务状态
        if task.status == "running":
            # 检查超时
            if self._is_task_timeout(task):
                issue = {
                    "task_id": task.id,
                    "issue": "timeout",
                    "running_time": (datetime.now() - task.created_at).total_seconds()
                }
                results["issues_found"].append(issue)

                # 自动修复
                if auto_fix:
                    fix = await self._auto_fix_timeout_task(task)
                    results["auto_fixes_applied"].append(fix)

        # 检查任务进度停滞
        elif task.status == "running" and task.progress > 0:
            if self._is_task_stalled(task):
                issue = {
                    "task_id": task.id,
                    "issue": "stalled",
                    "progress": task.progress,
                    "last_updated": task.updated_at.isoformat()
                }
                results["issues_found"].append(issue)

    # 汇报问题
    if report_issues and results["issues_found"]:
        await self._report_monitoring_results(results)

    return results
```

#### 3.2.2 检查提示词系统健康状态

```python
async def check_prompt_system(
    self,
    check_integrity: bool = True,
    check_overrides: bool = True,
    check_cache: bool = True,
    report_issues: bool = True
) -> dict:
    """
    检查提示词系统健康状态

    Args:
        check_integrity: 检查文件完整性
        check_overrides: 检查覆盖配置
        check_cache: 检查缓存状态
        report_issues: 汇报问题

    Returns:
        检查结果
    """
    results = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "issues": []
    }

    # 检查提示词文件完整性
    if check_integrity:
        integrity = await self._check_prompt_integrity()
        results["checks"]["integrity"] = integrity

        if integrity["issues"]:
            results["issues"].extend(integrity["issues"])
            results["status"] = "warning"

    # 检查覆盖配置
    if check_overrides:
        overrides = await self._check_workspace_overrides()
        results["checks"]["overrides"] = overrides

    # 检查缓存状态
    if check_cache:
        cache = await self._check_prompt_cache()
        results["checks"]["cache"] = cache

    # 汇报问题
    if report_issues and results["issues"]:
        await self._report_prompt_issues(results["issues"])

    return results
```

#### 3.2.3 系统健康检查

```python
async def health_check(
    self,
    check_system: bool = True,
    check_resources: bool = True,
    check_subagents: bool = True,
    generate_report: bool = True
) -> dict:
    """
    每日系统健康检查

    Args:
        check_system: 检查系统状态
        check_resources: 检查资源使用
        check_subagents: 检查子代理状态
        generate_report: 生成报告

    Returns:
        健康检查结果
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "checks": {}
    }

    # 检查系统状态
    if check_system:
        system_check = {
            "uptime": self._get_uptime(),
            "version": self._get_version(),
            "config_valid": self._validate_config()
        }
        results["checks"]["system"] = system_check

    # 检查资源使用
    if check_resources:
        resources_check = {
            "cpu_usage": self._get_cpu_usage(),
            "memory_usage": self._get_memory_usage(),
            "disk_usage": self._get_disk_usage()
        }
        results["checks"]["resources"] = resources_check

    # 检查子代理状态
    if check_subagents:
        subagents_check = {
            "total": len(self.subagent_manager.active_subagents),
            "running": len([s for s in self.subagent_manager.active_subagents if s.status == "running"]),
            "failed": len([s for s in self.subagent_manager.active_subagents if s.status == "failed"])
        }
        results["checks"]["subagents"] = subagents_check

    # 生成报告
    if generate_report:
        report = self._generate_health_report(results)
        await self._save_health_report(report)

    return results
```

#### 3.2.4 清理已完成任务

```python
async def cleanup_tasks(
    self,
    days_to_keep: int = 7,
    archive: bool = False
) -> dict:
    """
    清理已完成任务

    Args:
        days_to_keep: 保留天数
        archive: 是否归档

    Returns:
        清理结果
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "tasks_before": 0,
        "tasks_deleted": 0,
        "tasks_archived": 0
    }

    # 获取所有任务
    all_tasks = await self.task_manager.get_all_tasks()
    results["tasks_before"] = len(all_tasks)

    # 筛选需要清理的任务
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    tasks_to_cleanup = [
        task for task in all_tasks
        if task.status in ["complete", "failed"] and task.completed_at
        and task.completed_at < cutoff_date
    ]

    # 清理任务
    for task in tasks_to_cleanup:
        if archive:
            await self._archive_task(task)
            results["tasks_archived"] += 1
        else:
            await self.task_manager.delete_task(task.id)
            results["tasks_deleted"] += 1

    return results
```

---

## 📅 四、开发时间表

### 并行开发策略

由于提示词系统重构和任务管理相对独立，可以**并行开发**：

```
Week 1 (2.10 - 2.16)
├── Day 1-2: 提示词系统（创建文件）+ 任务管理（创建 TaskManager）
├── Day 3-4: 提示词系统（实现 PromptSystemV2）+ 任务管理（增强子代理）
├── Day 5-6: 提示词系统（更新 ContextBuilder）+ 任务管理（消息路由）
├── Day 7: 提示词系统（迁移内容）+ 任务管理（进度监控）
├── Day 8: 提示词系统（测试）+ 任务管理（Cron 系统）
└── Day 9-10: 集成测试 + 定时任务巡检 + 部署验证
```

### 详细日程

| 日期 | 提示词系统 | 任务管理 | 协作 |
|------|-----------|---------|------|
| 2.10 | 创建目录和文件 | 创建 TaskManager + Task | 同步接口设计 |
| 2.11 | 实现 PromptSystemV2（上） | 增强 SubagentManager | 定期同步 |
| 2.12 | 实现 PromptSystemV2（下） | 实现 MessageRouter | 定期同步 |
| 2.13 | 更新 ContextBuilder | 实现进度监控模块 | 集成讨论 |
| 2.14 | 迁移现有内容 | 实现 Cron 系统 | 接口对接 |
| 2.15 | 测试和验证 | 集成所有组件 | 联合测试 |
| 2.16 | 集成测试 + 部署 | 集成测试 + 部署 | 最终验收 |

---

## ✅ 五、验收标准

### 5.1 提示词系统

- [ ] `config/prompts/` 目录结构完整
- [ ] 所有提示词文件存在且格式正确
- [ ] PromptSystemV2 类实现完整
- [ ] MainAgent 正确加载提示词
- [ ] Subagent 正确加载提示词
- [ ] Workspace 文件可以覆盖内置提示词
- [ ] 缓存机制工作正常
- [ ] 定时任务可以检查提示词系统健康状态
- [ ] 向后兼容旧版本 workspace 文件

### 5.2 任务管理系统

- [ ] TaskManager 正常工作
- [ ] 任务状态跟踪准确
- [ ] 消息路由正确
- [ ] 任务修正机制工作
- [ ] 进度监控实时准确
- [ ] Cron 系统配置驱动
- [ ] 所有定时任务正常执行
- [ ] 健康检查功能完整

### 5.3 集成测试

- [ ] 完整流程测试（用户消息 → MainAgent → Subagent → 结果）
- [ ] 并发任务测试
- [ ] 超时和恢复测试
- [ ] 定时任务测试
- [ ] 性能测试（响应时间、资源占用）
- [ ] 向后兼容测试

---

## ⚠️ 六、风险和缓解措施

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 提示词系统影响性能 | 中等 | 中 | 使用缓存，限制加载频率 |
| 任务管理器状态不一致 | 高 | 低 | 使用锁和事务，定期同步 |
| 消息分析精度不足 | 中等 | 中 | 提供手动修正选项，持续优化 |
| Cron 任务执行失败 | 高 | 低 | 实现重试机制，错误通知 |
| 向后兼容性破坏 | 高 | 低 | 充分测试，提供迁移脚本 |
| 并行开发接口不一致 | 中等 | 中 | 频繁同步，明确接口契约 |

---

## 📚 七、相关文档

- `upgrade-plan/PROMPT-SYSTEM-UPGRADE.md` - 提示词系统详细升级方案
- `upgrade-plan/UPGRADE-PLAN.md` - 任务管理系统升级方案
- `upgrade-plan/ENHANCED-CRON.md` - 增强版 Cron 系统设计
- `upgrade-plan/cron-job-config-enhanced.json` - Cron 任务配置示例
- `upgrade-plan/test-scenarios.md` - 测试场景
- `upgrade-plan/deployment-guide.md` - 部署指南

---

## 🚀 八、下一步行动

1. ✅ 创建综合升级计划（本文件）
2. ⏳ 开始并行开发（提示词系统 + 任务管理）
3. ⏳ 定期同步进度和接口设计
4. ⏳ 集成测试和部署验证
5. ⏳ 文档更新和培训

---

**准备开始升级吗？我们可以从两个系统并行开发开始。**
