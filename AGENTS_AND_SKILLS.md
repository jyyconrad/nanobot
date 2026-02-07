# Nanobot 项目中的 Agent 和 Skills

## Agent 列表

### 核心 Agent

#### 1. MainAgent
- **位置**：`nanobot/agent/main_agent.py`
- **功能**：主要的 Agent 入口点，负责协调其他组件的运行
- **特点**：
  - 处理用户输入
  - 管理任务执行流程
  - 协调子代理和工具调用
  - 维护上下文和状态

### 辅助 Agent

#### 2. Planner Agent
- **位置**：`nanobot/agent/planner/`
- **功能**：负责任务规划和调度
- **子组件**：
  - `CancellationDetector`：取消检测
  - `ComplexityAnalyzer`：复杂度分析
  - `CorrectionDetector`：修正检测
  - `TaskDetector`：任务检测
  - `TaskPlanner`：任务规划器

#### 3. Decision Agent
- **位置**：`nanobot/agent/decision/`
- **功能**：负责决策和任务执行
- **子组件**：
  - `ExecutionDecisionMaker`：执行决策器
  - `CancellationHandler`：取消处理
  - `CorrectionHandler`：修正处理
  - `NewMessageHandler`：新消息处理
  - `SubagentResultHandler`：子代理结果处理

#### 4. Subagent Manager
- **位置**：`nanobot/agent/subagent/`
- **功能**：负责管理子代理的生命周期
- **子组件**：
  - `SubagentManager`：子代理管理器
  - `AgnoSubagent`：基于 Agno 的子代理
  - `InterruptHandler`：中断处理
  - `RiskEvaluator`：风险评估
  - `SubagentHooks`：子代理钩子

#### 5. Context Manager
- **位置**：`nanobot/agent/context_manager.py`
- **功能**：负责管理上下文和状态
- **子组件**：
  - `ContextBuilder`：上下文构建
  - `ContextCompressor`：上下文压缩
  - `ContextExpander`：上下文扩展
  - `ContextManager`：上下文管理器

#### 6. Memory Agent
- **位置**：`nanobot/agent/memory/`
- **功能**：负责管理记忆和历史记录
- **子组件**：
  - `EnhancedMemoryStore`：增强的记忆存储
  - `MemoryStore`：内存存储
  - `SessionManager`：会话管理

#### 7. Skill Loader
- **位置**：`nanobot/agent/skill_loader.py`
- **功能**：负责加载和管理技能
- **特点**：
  - 动态加载技能
  - 技能验证和依赖检查
  - 技能分类和管理

## Skills 列表

### 内置技能

#### 1. GitHub 技能
- **位置**：`nanobot/skills/github/`
- **功能**：与 GitHub API 交互的技能
- **特点**：
  - 查看仓库信息
  - 创建和管理问题
  - 查看和管理拉取请求
  - 查看和管理提交

#### 2. Skill Creator 技能
- **位置**：`nanobot/skills/skill-creator/`
- **功能**：用于创建新技能的技能
- **特点**：
  - 生成技能模板
  - 自动创建技能结构
  - 技能验证和测试

#### 3. Summarize 技能
- **位置**：`nanobot/skills/summarize/`
- **功能**：用于总结文本内容的技能
- **特点**：
  - 文本摘要生成
  - 内容提取和分析
  - 关键词提取

#### 4. Tmux 技能
- **位置**：`nanobot/skills/tmux/`
- **功能**：与 Tmux 终端多路复用器交互的技能
- **特点**：
  - 管理 Tmux 会话
  - 创建和管理窗口
  - 执行 Tmux 命令

#### 5. Weather 技能
- **位置**：`nanobot/skills/weather/`
- **功能**：获取天气信息的技能
- **特点**：
  - 获取当前天气信息
  - 天气预报查询
  - 天气警报和通知

## 技能加载和管理

### 技能加载器
- **位置**：`nanobot/agent/skill_loader.py`
- **功能**：负责加载和管理技能
- **特点**：
  - 动态加载技能
  - 技能验证和依赖检查
  - 技能分类和管理

### 技能格式
- **每个技能都有一个 SKILL.md 文件**：包含技能的详细信息和配置
- **技能结构**：
  - `SKILL.md`：技能描述和配置
  - `scripts/`：技能的脚本文件
  - `tests/`：技能的测试文件

## 总结

Nanobot 项目包含多个核心 Agent 和技能，这些组件协同工作，提供了一个功能完整的 AI 助手。核心 Agent 负责协调任务执行流程，而技能提供了与外部系统交互的能力。

项目的技能系统是可扩展的，允许用户添加新的技能来满足特定需求。每个技能都有自己的配置和测试文件，确保技能的可维护性和可扩展性。
