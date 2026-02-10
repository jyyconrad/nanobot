# Nanobot v0.2.0 综合升级方案总览（已更新）

> **版本**: v0.2.0
> **开始日期**: 2026-02-09
> **预计完成**: 2026-02-23
> **总工期**: 约 14 天（新增 Agno 集成）

---

## 📋 升级概览

本次升级旨在全面提升 Nanobot 系统的能力和架构，包括 **Agno 框架集成**、提示词系统、任务管理、意图识别等多个核心模块。

### 🎌 核心升级方向

1. **🆕 Agno 框架集成** - 基于 agno 的 MainAgent 和 Subagent 架构
2. **提示词系统重构** - 渐进式上下文披露 + 钩子系统
3. **动态任务管理** - Task Manager + 消息路由 + Cron 系统
4. **意图识别升级** - 三层综合识别（规则 + 代码 + LLM）
5. **上下文监控** - 自动压缩 + 阈值触发

### 🎯 预期成果

- ✅ 基于 agno 的现代化架构
- ✅ 两种提示词初始化策略
- ✅ 更强大的提示词管理能力
- ✅ 灵活的任务协调和监控
- ✅ 准确的意图识别
- ✅ 高效的上下文管理
- ✅ 完善的 TDD 测试覆盖

---

## 🆕 Agno 框架集成详解

### 架构设计

**参考文档**: `upgrade-plan/nanobot-agno-upgrade-plan-v2.md`（已存在于 workspace/memory）

**核心设计**:
- 基于 agno 的 Agent、Toolkit、Knowledge、Team 框架
- 统一的文件化提示词管理（参考 OpenClaw）
- MainAgent 和 SubAgent 统一架构
- 两种提示词初始化策略

### 目录结构

```
nanobot-agno/
├── config/
│   ├── prompts/                 # 所有内置提示词文件
│   │   ├── agents.md           # 工作区配置和智能体行为准则
│   │   ├── soul.md             # 核心身份和行为哲学
│   │   ├── user.md             # 用户信息和偏好
│   │   ├── tools.md            # 工具配置信息
│   │   ├── identity.md         # 基本身份信息
│   │   ├── heartbeat.md        # 心跳检查和定期任务
│   │   └── memory.md           # 长时记忆配置
│   ├── model_config.py          # 模型配置
│   └── system_config.py         # 系统配置
├── tools/                       # 工具集合
│   ├── framework/              # 框架级工具
│   ├── project/                # 项目级工具
│   └── user/                   # 用户级工具
├── skills/                      # 技能集合
│   ├── base/                   # 基础技能
│   └── specialized/            # 专业技能
├── context/                     # 上下文管理
│   ├── memory/                 # 用户记忆（每日文件）
│   │   ├── YYYY-MM-DD.md
│   │   └── heartbeat-state.json
│   └── session/                # 会话状态
├── agents/                      # Agent 实现
│   ├── agno_main_agent.py     # 基于 agno 的 MainAgent
│   └── agno_subagent.py      # 基于 agno 的 SubAgent
├── examples/                    # agno 使用示例
│   └── agno_examples.py       # Agno 框架使用示例
└── main.py                      # MainAgent 入口
```

### 两种提示词初始化策略

#### 策略 1: Team 协同方式

**特点**：
- 创建多个 Agent，每个负责生成提示词的某部分
- 使用 Team 统一协调
- 适合复杂提示词组合

**示例代码**：
```python
from agno import Agent, Team

# 创建负责不同部分的 Agent
identity_agent = Agent(
    name="identity_provider",
    instructions="你负责生成系统身份提示词"
)

soul_agent = Agent(
    name="soul_provider",
    instructions="你负责生成系统人设提示词"
)

# 创建 Team
prompt_team = Team(
    agents=[identity_agent, soul_agent],
    instructions="协同生成完整的系统提示词"
)

# 使用 Team 生成提示词
response = prompt_team.run("生成 MainAgent 的系统提示词")
```

#### 策略 2: 模板 + 占位符替换

**特点**：
- 预先定义完整的提示词模板
- 使用占位符（`{{SKILLS}}`, `{{TOOLS}}`）标记动态内容
- Agent 运行时读取模板，替换占位符

**示例代码**：
```python
# config/prompts/main_agent_template.md
"""
# 系统身份
你是一个 AI 智能体，名为 {{AGENT_NAME}}

# 核心能力
## 技能列表
{{SKILLS}}

## 工具列表
{{TOOLS}}
"""

# Agent 实现
class MainAgent:
    def _build_system_prompt(self, skills: list, tools: list) -> str:
        """构建系统提示词"""
        # 加载模板
        with open("config/prompts/main_agent_template.md", "r") as f:
            template = f.read()
        
        # 替换占位符
        prompt = template.replace("{{AGENT_NAME}}", "MainAgent")
        prompt = prompt.replace("{{SKILLS}}", "\n".join(skills))
        prompt = prompt.replace("{{TOOLS}}", "\n".join([t.name for t in tools]))
        
        return prompt
```

### 集成阶段

| 阶段 | 天数 | 任务 |
|------|------|------|
| Agno 研究 | 1 | 研究 agno 框架，编写示例 |
| 设计方案 | 0.5 | 设计提示词策略，更新方案文档 |
| MainAgent 改造 | 1 | 创建 `agno_main_agent.py` |
| SubAgent 改造 | 1 | 创建 `agno_subagent.py` |
| 集成测试 | 1 | 端到端测试，向后兼容测试 |

---

## 📁 升级方案文档

### 🆕 Agno 相关文档

1. **Agno 集成方案**
   - **文档**: `memory/nanobot-agno-upgrade-plan-v2.md`（workspace/memory）
   - **内容**: 完整的 Agno 框架集成方案，包括架构设计、目录结构、提示词加载逻辑

2. **Agno 集成计划**
   - **文档**: `upgrade-plan/AGNO-INTEGRATION-PLAN.md`
   - **内容**: Agno 框架研究、两种提示词策略、实现步骤

### 原有升级文档

3. **综合升级计划**
   - **文档**: `upgrade-plan/COMPREHENSIVE-UPGRADE-PLAN.md`
   - **内容**: 提示词和任务管理并行开发策略，14 天详细开发时间表

4. **提示词系统升级**
   - **文档**: `upgrade-plan/PROMPT-SYSTEM-UPGRADE.md`
   - **内容**: 渐进式上下文披露机制，13 个提示词文件的详细设计

5. **渐进式上下文披露分析**
   - **文档**: `upgrade-plan/PROGRESSIVE-DISCLOSURE-ANALYSIS.md`
   - **内容**: OpenClaw 三层披露模式详解，Nanobot 需要的所有提示词文件模板

6. **提示词系统钩子**
   - **文档**: `upgrade-plan/PROMPT-SYSTEM-HOOKS.md`
   - **内容**: 三种钩子类型，HookSystem 核心类设计

7. **上下文监控钩子**
   - **文档**: `upgrade-plan/CONTEXT-MONITOR-HOOKS.md`
   - **内容**: 上下文监控器设计，60% 阈值自动触发压缩

8. **意图识别系统升级**
   - **文档**: `upgrade-plan/INTENT-RECOGNITION-UPGRADE.md`
   - **内容**: 三层综合识别架构，固定规则、代码逻辑、大模型识别

---

## 🚀 开发策略和流程

### 📌 基本原则

1. **Agno 优先** - 所有开发基于 agno 框架
2. **TDD 驱动开发** - 先写测试，再写实现
3. **Code Agent + Opencode** - 使用专业的编码工具
4. **方案先行确认** - 每个 subagent 任务先完善方案并与 claw 核对
5. **并行独立推进** - Agno 研究、提示词系统和任务管理可并行开发

### 🔄 Agno 研究流程

**Step 1: 研究 agno 框架**
```
1. 查看 agno 核心结构
   - agno.agent (Agent, AgentSession, Message, Toolkit)
   - agno.knowledge (Knowledge)
   - agno.tools (Function)

2. 编写 agno 示例
   - examples/agno_examples.py
   - 简单 Agent 示例
   - 带 Tools 的 Agent 示例
   - Team 协同示例

3. 测试基础功能
   - Agent 创建和运行
   - Toolkit 集成
   - Knowledge 加载
```

**Step 2: 设计提示词策略**
```
1. 完善 Team 策略设计
2. 完善模板策略设计
3. 编写策略对比文档
4. 创建提示词模板文件
```

---

## 📅 分阶段实施计划

### Phase 0: Ag（框架研究和集成（新增）（Day 1-4）

#### Day 1: 研究 Agno 框架

**任务清单**:
- [x] ✅ 已完成：查看 agno 核心结构
- [ ] 编写 agno Agent 礵例
- [ ] 编写 agno Skills/Tools 示例
- [ ] 编写 agno Knowledge 示例
- [ ] 测试基础功能

**使用文件**:
- `examples/agno_examples.py` - Agno 框架使用示例（需创建）

#### Day 2: 设计提示词策略

**任务清单**:
- [ ] 完善 Team 策略设计
- [ ] 完善模板策略设计
- [ ] 编写策略对比文档
- [ ] 创建提示词模板文件

**使用文件**:
- `config/prompts/main_agent_template.md` - 提示词模板（需创建）
- `config/prompts/subagent_template.md` - SubAgent 模板（需创建）

#### Day 3: 改造 MainAgent

**任务清单**:
- [ ] 创建 `nanobot/agents/agno_main_agent.py`
- [ ] 实现提示词构建逻辑
- [ ] 集成工具包
- [ ] 集成知识库
- [ ] 编写测试

#### Day 4: 改造 SubAgent

**任务清单**:
- [ ] 创建 `nanobot/agents/agno_subagent.py`
- [ ] 实现继承逻辑
- [ ] 实现任务分发

- [ ] 编写测试

---

### Phase 1: 方案确认和准备（Day 5）

**任务清单**:
- [ ] 使用 subagent 完善提示词系统方案
- [ ] 使用 subagent 完善任务管理方案
- [ ] 使用 subagent 完善意图识别方案
- [ ] 与用户确认所有方案
- [ ] 创建开发分支

---

### Phase 2: 提示词系统开发（Day 6-9）

#### Day 6: 创建提示词文件结构

**任务清单**:
- [ ] 创建 `config/prompts/` 目录结构
- [ ] 创建所有核心提示词文件（13 个）
- [ ] 编写文件结构验证测试

#### Day 7-8: 实现 PromptSystemV2 类

**任务清单**:
- [ ] 实现 HookSystem 类
- [ ] 实现 PromptSystemV2 核心功能
- [ ] 实现分层加载逻辑
- [ ] 实现覆盖机制
- [ ] 编写单元测试

#### Day 9: 集成到 Agno MainAgent

**任务清单**:
- [ ] 修改 AgnoMainAgent 使用 PromptSystemV2
- [ ] 更新初始化流程
- [ ] 编写集成测试
- [ ] 测试向后兼容

---

### Phase 3: 任务管理系统开发（Day 6-10）

**并行开发，与提示词系统独立**

#### Day 6: 创建 TaskManager

**任务清单**:
- [ ] 实现 Task 数据模型
- [ ] 实现 TaskManager 核心功能
- [ ] 实现任务状态跟踪
- [ ] 编写单元测试

#### Day 7-8: 增强子代理管理

**任务清单**:
- [ ] 修改 SubagentManager 支持任务跟踪
- [ ] 实现进度汇报机制
- [ ] 实现任务修正接口
- [ ] 编写集成测试

#### Day 9-10: 消息路由和 Cron 系统

**任务清单**:
- [ ] 实现 MessageAnalyzer
- [ ] 实现 MessageRouter
- [ ] 实现可配置 Cron 系统
- [ ] 编写端到端测试

---

### Phase 4: 上下文监控开发（Day 11-12）

#### Day 11: 实现 ContextMonitor

**任务清单**:
- [ ] 实现 ContextMonitor 类
- [ ] 实现 token 计数
- [ ] 实现阈值检查
- [ ] 编写单元测试

#### Day 12: 集成到 Agent Loop

**任务清单**:
- [ ] 修改 AgentLoop 集成 ContextMonitor
- [ ] 在 process_message 中自动检查
- [ ] 编写集成测试
- [ ] 测试多模态消息

---

### Phase 5: 意图识别开发（Day 13）

#### Day 13: 实

现三层识别器

**任务清单**:
- [ ] 实现 RuleBasedRecognizer
- [ ] 实现 CodeBasedRecognizer
- [ ] 实现 LLMRecognizer
- [ ] 编写单元测试

#### Day 13: 实现综合识别器

**任务清单**:
- [ ] 实现 HybridIntentRecognizer
- [ ] 实现优先级机制
- [ ] 实现降级策略
- [ ] 编写集成测试

#### Day 13: 集成到 Gateway

**任务清单**:
- [ ] 修改 Gateway 使用 HybridIntentRecognizer
- [ ] 实现意图到方法的映射
- [ ] 编写端到端测试
- [ ] 测试性能

---

### Phase 6: 集成测试和验证（Day 14）

**任务清单**:
- [ ] 运行完整测试套件
- [ ] 生成测试覆盖率报告
- [ ] 性能测试（响应时间、资源占用）
- [ ] 集成测试（端到端场景）
- [ ] 验收检查
- [ ] 文档更新

---

## ✅ 验收标准

### 🆕 Agno 集成功能

- [ ] Agno 框架集成成功
  - [ ] MainAgent 基于 agno.Agent 实现
  - [ ] SubAgent 基于 agno.Agent 实现
  - [ ] Toolkit 集成正确
  - [ ] Knowledge 集成正确
  - [ ] Team 协同可选功能正常

- [ ] 提示词初始化策略工作正常
  - [ ] Team 策略正确生成提示词
  - [ ] 模板策略正确替换占位符
  - [ ] 策略可通过配置切换

- [ ] 文件化提示词管理
  - [ ] 所有提示词文件正确加载
  - [ ] 提示词更新自动检测
  - [ ] 版本控制正常
  - [ ] 热更新功能正常

### 系统功能

- [ ] 提示词系统正常工作
  - [ ] 所有提示词文件正确加载
  - [ ] MainAgent 和 Subagent 提示词正确
  - [ ] Workspace 文件可以覆盖内置文件
  - [ ] 缓存机制正常

- [ ] 任务管理系统正常工作
  - [ ] TaskManager 创建和跟踪任务
  - [ ] 子代理管理器增强正常
  - [ ] 消息路由准确
  - [ ] Cron 任务按计划执行

- [ ] 意图识别系统正常工作
  - [ ] 固定规则匹配准确
  - [ ] 代码逻辑上下文感知
  - [ ] 大模型语义识别准确
  - [ ] 三层优先级正确

- [ ] 上下文监控正常工作
  - [ ] 60% 阈值触发压缩
  - [ ] 钩子正常触发
  - [ ] 统计信息准确
  - [ ] 多模态消息支持

### 测试质量

- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过
- [ ] 端到端测试通过
- [ ] 性能测试达标
- [ ] 无 P0/P1 级别 bug

### 文档质量

- [ ] API 文档完整
- [ ] 配置说明清晰
- [ ] 升级指南完善
- [ ] 示例代码正确

---

## 🛠️ 风险和缓解措施

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| Agno 框架不兼容 | 高 | 低 | 提前测试，准备降级方案 |
| 提示词系统影响性能 | 中等 | 中 | 使用缓存，限制加载频率 |
| 任务管理器状态不一致 | 高 | 低 | 使用锁和事务，定期同步 |
| 意图识别准确率不足 | 中等 | 中 | 提供手动修正选项，持续优化 |
| 上下文压缩丢失重要信息 | 高 | 低 | 保留最近消息，提供压缩预览 |
| 并行开发接口不一致 | 中等 | 中 | 频繁同步，明确接口契约 |

---

## 📚 相关资源

### Agno 相关资源

1. **Agno 框架文档**
   - 位置: `/Users/jiangyayun/develop/code/work_code/incubate_project/.venv/lib/python3.12/site-packages/agno`
   - 核心模块: `agno.agent`, `agno.knowledge`, `agno.tools`

2. **Agno 集成方案**
   - `memory/nanobot-agno-upgrade-plan-v2.md` - 完整集成方案
   - `upgrade-plan/AGNO-INTEGRATION-PLAN.md` - 实施计划

3. **Agno 示例代码**
   - `examples/agno_examples.py` - 使用示例（需创建）

### 设计文档

4. **综合升级计划**
   - `upgrade-plan/COMPREHENSIVE-UPGRADE-PLAN.md`

5. **提示词系统升级**
   - `upgrade-plan/PROMPT-SYSTEM-UPGRADE.md`
   - `upgrade-plan/PROGRESSIVE-DISCLOSURE-ANALYSIS.md`
   - `upgrade-plan/PROMPT-SYSTEM-HOOKS.md`

6. **上下文监控钩子**
   - `upgrade-plan/CONTEXT-MONITOR-HOOKS.md`

7. **意图识别系统升级**
   - `upgrade-plan/INTENT-RECOGNITION-UPGRADE.md`

8. **任务管理系统方案**
   - `upgrade-plan/UPGRADE-PLAN.md`
   - `upgrade-plan/ENHANCED-CRON.md`

### 配置文件

9. **Cron 任务配置**
   - `upgrade-plan/cron-job-config-enhanced.json` - Cron 任务配置（已更新）

### 参考系统

10. **参考系统**
    - OpenClaw 提示词架构
    - Agno 框架设计
    - Claude Code 编码工具

---

## 🎯 下一步行动

### 立即开始

1. ✅ **Agno 框架研究** - 研究已完成核心结构分析
2. ⏳ **编写 Agno 示例** - 创建 `examples/agno_examples.py`
3. ⏳ **设计提示词策略** - 完善两种策略设计
4. ⏳ **方案确认** - 与用户确认所有方案
5. ⏳ **分支创建** - 创建 `upgrade/v0.2.0` 分支
6. ⏳ **开始开发** - 按照 Phase 0-6 逐步实施

### 开发顺序

```
Phase 0 (Day 1-4): Agno 框架研究和集成
  ├─ 研究 Agno 框架
  ├─ 设计提示词策略
  ├─ 改造 MainAgent
  └─ 改造 SubAgent
    ↓
Phase 1 (Day 5): 方案确认和准备
    ↓
Phase 2 (Day 6-9): 提示词系统开发
  ├─ 创建文件结构
  ├─ 实现 PromptSystemV2
  └─ 集成到 Agno MainAgent
    ↓
Phase 3 (Day 6-10): 任务管理系统开发（并行）
  ├─ 创建 TaskManager
  ├─ 增强子代理
  └─ 消息路由和 Cron
    ↓
Phase 4 (Day 11-12): 上下文监控开发
  ├─ 实现 ContextMonitor
  └─ 集成到 Agent Loop
    ↓
Phase 5 (Day 13): 意图识别开发
  ├─ 实现三层识别器
  ├─ 实现综合识别器
  └─ 集成到 Gateway
    ↓
Phase 6 (Day 14): 集成测试和验证
    ↓
发布 v0.2.0
```

---

## 📞 需要用户确认

在开始开发之前，请确认：

1. **🆕 Agno 框架集成** - 是否确认使用 agno 框架作为基础？
2. **🆕 提示词策略** - 两种提示词初始化策略是否都需实现？
3. **🆕 总工期调整** - 14 天工期（从 10 天延长）是否可接受？
4. **升级方向** - 本次升级的 5 个核心方向是否符合预期？
5. **开发策略** - 使用 TDD + Code Agent + Opencode 是否认可？
6. **并行开发** - Agno 研究、提示词系统和任务管理并行推进是否可行？
7. **风险接受** - 列出的风险和缓解措施是否充分？

**请回复确认或提出修改意见，确认后我们将立即启动 Phase 0。**
