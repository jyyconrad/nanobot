# Nanobot 升级方案 - MainAgent 智能决策与技能系统

## 📋 项目信息

**项目名称**：Nanobot MainAgent 智能决策与技能系统升级
**创建时间**：2026-02-08
**参考架构**：OpenClaw
**目标版本**：Nanobot v2.0

---

## 🎯 升级目标

### 核心目标

1. **MainAgent 智能决策**
   - MainAgent 能够自主决策，不询问用户
   - 通过工具调用查询系统配置（skills、agents）
   - 根据任务特点智能选择合适的 skills
   - 动态决定创建什么类型的 subagent

2. **Subagent 技能加载**
   - Subagent 接收 skills 列表
   - 通过 SkillLoader 动态加载技能详细内容
   - 将技能内容注入到系统提示词中
   - 根据技能指导执行任务

3. **技能系统完善**
   - 参照 OpenClaw 的技能设计风格
   - 支持渐进式披露（Metadata → 正文 → 资源）
   - 简洁优先，假设模型很聪明
   - 丰富的示例技能库

4. **工具系统增强**
   - 提供配置查询工具
   - 支持高风险操作的风险评估
   - 完善的错误处理

---

## 📐 架构设计参考

### OpenClaw 核心设计原则

1. **渐进式披露**（Progressive Disclosure）
   - Metadata（name + description）始终在上下文中
   - SKILL.md 正文在技能触发时加载（<5k 词）
   - Bundled Resources 按需加载

2. **简洁优先**（Conciseness First）
   - 假设模型已经很聪明
   - 只添加模型不具备的知识
   - 质疑每段信息的必要性

3. **工具驱动**（Tool-Driven）
   - 模型通过工具调用执行操作
   - 工具有明确参数和返回值
   - 高风险工具有评估机制

4. **自主决策**（Autonomous Decision）
   - MainAgent 不问用户，自己判断
   - 通过工具获取配置信息
   - 智能选择 skills 和 agent 类型

### 期望的工作流程

```
用户输入
  ↓
MainAgent.process_message()
  ↓
MainAgent 分析任务
  ↓
调用工具查询配置
  - get_available_skills()
  - get_available_agents()
  ↓
智能决策
  - 选择技能 (SkillDecisionHandler)
  - 选择 agent 类型 (agno)
  ↓
创建 Subagent (SubagentManager.spawn())
  - 传递 skills 信息
  ↓
Subagent 执行
  - SkillLoader.load_skills_for_task()
  - 动态加载技能内容
  - 注入系统提示 (_build_enhanced_agno_prompt)
  ↓
执行任务 (使用工具)
  ↓
返回结果
  ↓
MainAgent 聚合结果
  ↓
用户看到最终回复
```

---

## 📝 实施计划

### Phase 1：核心架构搭建

**目标**：建立基本的 MainAgent、Subagent、SkillLoader 协作

#### 任务 1.1：创建配置查询工具

**文件**：`nanobot/agent/tools/config_tools.py`

**功能**：
- `GetAvailableSkillsTool` - 获取所有可用技能列表
- `GetSkillsForTaskTool` - 根据任务类型获取推荐技能
- `GetAvailableAgentsTool` - 获取支持的 agent 类型
- `GetSkillContentTool` - 获取技能详细内容

**实现要点**：
- 继承 `Tool` 基类
- 定义 `name`、`description`、`parameters`
- 实现 `execute()` 异步方法
- 返回格式化的字符串结果

**验证**：
- [ ] 工具可以被注册和调用
- [ ] 返回正确的技能列表
- [ ] 支持正确的参数验证

#### 任务：创建技能决策处理器

**文件**：`nanobot/agent/decision/skill_decision_handler.py`

**功能**：
- `_get_system_config()` - 获取系统配置信息
- `_select_skills_for_task()` - 为任务选择合适的技能
- `_analyze_task_type()` - 分析任务类型
- `_select_agent_type()` - 选择 agent 类型

**实现要点**：
- 集成 `ToolRegistry` 和 `SkillLoader`
- 调用配置查询工具获取信息
- 根据任务关键词匹配任务类型
- 使用 SkillLoader 加载对应技能

**验证**：
- [ ] 可以调用工具查询配置
- [ ] 任务类型识别准确
- [ ] 技能选择合理
- [ ] 返回正确的决策结果

#### 任务：创建增强版 MainAgent

**文件**：`nanobot/agent/enhanced_main_agent.py`

**功能**：
- 初始化时创建 `SkillLoader` 和 `ToolRegistry`
- 注册配置查询工具
- 使用 `SkillDecisionHandler` 进行智能决策
- 创建 Subagent 时传递 skills 信息

**实现要点**：
- 集成 `SkillLoader` 和 `SkillDecisionHandler`
- 修改 `_handle_spawn_subagent_decision` 传递 skills
- 保持与原 `MainAgent` 的兼容性
- 添加详细的日志记录

**验证**：
- [ ] 初始化时正确加载组件
- [ ] 可以调用配置查询工具
- [ ] 智能决策流程正确
- [ ] Subagent 创建时传递 skills

#### 任务：创建增强版 Agno Subagent

**文件**：`nanobot/agent/subagent/enhanced_agno_subagent.py`

**功能**：
- 接收 skills 参数
- `_load_skills_content()` - 动态加载技能详细内容
- `_build_enhanced_agno_prompt()` - 构建增强的系统提示
- 在系统提示中注入技能内容

**实现要点**：
- 继承或参考原 `AgnoSubagentManager`
- 使用 `SkillLoader` 动态加载技能
- 修改 `spawn()` 方法接收 skills 参数
- 更新系统提示词模板

**验证**：
- [ ] 可以接收 skills 参数
- [ ] 技能内容正确加载
- [ ] 系统提示包含技能内容
- [ ] 执行时使用增强提示

#### 任务：创建配置文件

**文件 1**：`nanobot/config/agent_prompts.yaml`

**内容**：
- `main_agent.system_prompt` - MainAgent 系统提示词
- `sub_agent.system_prompt_template` - Subagent 系统提示词模板
- `agno_subagent.system_prompt_template` - Agno Subagent 特定提示词
- `ai_guidance` - 决策指导提示词

**要点**：
- 提示词要清晰、简洁
- 强调自主决策原则
- 说明工具和技能的使用方式

**文件 2**：更新 `nanobot/config/skill_mapping.yaml`

**内容**：
- 任务类型到技能的映射
- 默认技能列表
- 技能描述

**要点**：
- 确保映射关系合理
- 覆盖常见的任务类型

**验证**：
- [ ] 配置文件可以正确加载
- [ ] YAML 格式正确
- [ ] 提示词模板可以正确替换

---

### Phase 2：技能系统完善

**目标**：建立完整的技能生态系统

#### 任务 2.1：创建核心技能

**技能列表**：
1. **coding** - 编码技能
2. **debugging** - 调试技能
3. **testing** - 测试技能
4. **security** - 安全技能
5. **planning** - 规划技能
6. **writing** - 写作技能
7. **research** - 研究技能

**每个技能的结构**：
```
skills/<skill_name>/
├── SKILL.md（必需）
│   ├── YAML frontmatter
│   │   ├── name: 技能名称
│   │   ├── description: 技能描述
│   │   └── version: 版本
│   └── Markdown 正文
└── resources/（可选）
    ├── scripts/
    ├── references/
    └── assets/
```

**SKILL.md 写作原则**：
1. **YAML frontmatter**：
   - `name` - 技能名称
   - `description` - 清晰描述何时使用此技能
   - `version` - 版本号
   - `metadata` - 额外元数据（emoji、keywords 等）

2. **正文结构**：
   - 何时使用此技能
   - 能力说明
   - 使用原则
   - 代码模式/示例
   - 最佳实践
   - 参考资源
   - 工具使用说明

3. **写作风格**：
   - 简洁、清晰
   - 假设模型很聪明
   - 只添加模型不具备的知识
   - 使用代码示例而非长篇解释

**技能内容要求**：

**coding/SKILL.md**：
- 支持的语言（Python, JavaScript, Java, Go, Rust, SQL）
- 编码原则（清晰、错误处理、性能、安全）
- 代码模式（常用模式示例）
- 代码审查清单
- 性能优化技巧
- 安全最佳实践

**debugging/SKILL.md**：
- 调试方法论（理解、重现、隔离、定位、修复、验证）
- 常见错误类型（Python、JavaScript）
- 调试技巧（打印、断点、断言）
- 性能调试方法
- 日志记录指南

**testing/SKILL.md**：
- 测试类型（单元测试、集成测试、端到端测试）
- 测试框架（pytest, unittest, jest）
- 测试编写原则
- Mock 和 Stub 使用
- 测试覆盖率

**security/SKILL.md**：
- 安全原则
- 常见漏洞（SQL 注入、XSS、CSRF）
- 安全检查清单
- 加密和认证
- 安全审计

**planning/SKILL.md**：
- 任务分解方法
- 优先级管理
- 时间估算
- 风险评估
- 依赖管理

**writing/SKILL.md**：
- 写作原则（清晰、简洁、结构化）
- 文档类型（API 文档、用户手册、README）
- 写作模板
- 内容组织结构
- 多语言支持

**research/SKILL.md**：
- 信息收集方法
- 来源评估
- 数据分析技巧
- 报告写作
- 引用管理

**验证**：
- [ ] 每个技能都有 SKILL.md 文件
- [ ] YAML frontmatter 正确
- [ ] 内容简洁、有用
- [ ] 代码示例正确
- [ ] 遵循 OpenClaw 风格

#### 任务 2.2：完善 SkillLoader

**文件**：`nanobot/agent/skill_loader.py`

**改进**：
- `load_skills_for_task()` - 支持显式技能优先级
- `load_skill_content()` - 从 SKILL.md 文件加载内容
- `parse_skill_frontmatter()` - 解析 YAML frontmatter
- `get_available_skills()` - 扫描 skills 目录
- `validate_skills()` - 验证技能格式

**实现要点**：
- 支持从文件系统读取 SKILL.md
- 解析 YAML frontmatter 和 Markdown 正文
- 缓存已加载的技能内容
- 提供技能元数据查询

**验证**：
- [ ] 可以从文件系统读取技能
- [ ] YAML frontmatter 正确解析
- [ ] 技能内容正确加载
- [ ] 缓存机制有效

---

### Phase 3：工具系统增强

**目标**：提供丰富的工具支持

#### 任务 3.1：扩展工具库

**新增工具**：

1. **Git 工具**
   - `GitCloneTool` - 克隆仓库
   - `GitCommitTool` - 提交更改
   - `GitPushTool` - 推送到远程
   - `GitPullTool` - 拉取更新

2. **Docker 工具**
   - `DockerBuildTool` - 构建镜像
   - `DockerRunTool` - 运行容器
   - `DockerComposeTool` - 使用 docker-compose

3. **Cloud 工具**
   - `AWSCliTool` - AWS CLI 包装
   - `AzureCliTool` - Azure CLI 包装

4. **Database 工具**
   - `MySQLQueryTool` - MySQL 查询
   - `PostgreSQLQueryTool` - PostgreSQL 查询

**每个工具的实现要点**：
- 继承 `Tool` 基类
- 明确的参数定义
- 异步执行
- 完善的错误处理
- 详细的日志记录

#### 任务 3.2：风险评估机制

**文件**：`nanobot/agent/tools/risk_evaluator.py`

**功能**：
- `evaluate_tool_call()` - 评估工具调用的风险
- `get_risk_level()` - 获取风险等级
- `get_approval_message()` - 获取批准消息

**风险等级**：
- **LOW** - 安全，可以直接执行
- **MEDIUM** - 需要警告，可以执行
- **HIGH** - 需要用户批准

**高风险工具示例**：
- 删除文件/目录
- 执行系统命令
- 访问敏感数据
- 修改关键配置

**验证**：
- [ ] 风险评估准确
- [ ] 高风险操作被阻止
- [ ] 中等风险有警告
- [ ] 低风险直接执行

---

### Phase 4：集成和测试

**目标**：确保系统稳定性和可维护性

#### 任务 4.1：单元测试

**测试文件**：
- `tests/test_config_tools.py` - 配置查询工具测试
- `tests/test_skill_decision_handler.py` - 技能决策处理器测试
- `tests/test_enhanced_main_agent.py` - 增强版 MainAgent 测试
- `tests/test_enhanced_agno_subagent.py` - 增强版 Agno Subagent 测试
- `tests/test_skill_loader.py` - SkillLoader 测试
- `tests/test_risk_evaluator.py` - 风险评估器测试

**测试覆盖**：
- 正常流程测试
- 边界条件测试
- 错误处理测试
- 并发测试

**验证标准**：
- 测试覆盖率 > 80%
- 所有测试通过
- 无内存泄漏

#### 任务 4.2：集成测试

**测试场景**：
1. **端到端流程测试**
   - 用户输入 → MainAgent → Subagent → 结果
   - 验证完整流程

2. **技能加载测试**
   - 验证技能正确加载
   - 验证技能内容正确注入

3. **工具调用测试**
   - 验证工具正确调用
   - 验证工具参数正确传递
   - 验证工具结果正确返回

4. **并发测试**
   - 多个 Subagent 并发执行
   - 验证资源正确管理
   - 验证无竞态条件

#### 任务 4.3：性能测试

**测试指标**：
- 响应时间
- 内存使用
- CPU 使用率
- 并发处理能力

**性能目标**：
- MainAgent 响应时间 < 1s
- Subagent 创建时间 < 500ms
- 技能加载时间 < 100ms
- 支持 10+ 并发 Subagent

---

### Phase 5：文档和示例

**目标**：提供完整的文档和使用示例

#### 任务 5.1：用户文档

**文档列表**：

1. **README.md** - 项目概览
   - 项目介绍
   - 快速开始
   - 核心功能
   - 安装指南

2. **USER_GUIDE.md** - 用户指南
   - 如何使用 MainAgent
   - 如何创建任务
   - 如何查询状态
   - 常见问题

3. **SKILL_GUIDE.md** - 技能使用指南
   - 可用技能列表
   - 技能使用示例
   - 自定义技能

4. **API_REFERENCE.md** - API 参考
   - MainAgent API
   - Subagent API
   - 工具 API

#### 任务 5.2：开发者文档

**文档列表**：

1. **DEVELOPER_GUIDE.md** - 开发者指南
   - 开发环境搭建
   - 代码结构
   - 编码规范
   - 贡献指南

2. **ARCHITECTURE.md** - 架构文档
   - 系统架构
   - 组件说明
   - 数据流
   - 扩展点

3. **TESTING.md** - 测试文档
   - 测试策略
   - 如何编写测试
   - 运行测试

4. **CONTRIBUTING.md** - 贡献指南
   - 如何贡献
   - Pull Request 流程
   - 代码审查标准

#### 任务 5.3：示例和教程

**示例列表**：

1. **examples/simple_task.py** - 简单任务示例
2. **examples/coding_task.py** - 编码任务示例
3. **examples/debugging_task.py** - 调试任务示例
4. **examples/multi_subagent.py** - 多 Subagent 示例
5. **examples/custom_skill/** - 自定义技能示例

---

### Phase 6：发布和部署

**目标**：准备公开发布

#### 任务 6.1：版本管理

**任务**：
- 更新版本号到 v2.0.0
- 更新 CHANGELOG.md
- 创建 Git tag
- 构建发布包

#### 任务 6.2：CI/CD 配置

**任务**：
- 配置 GitHub Actions
- 自动化测试
- 自动化发布
- 文档自动生成

#### 任务 6.3：发布说明

**任务**：
- 撰写 Release Notes
- 突出新功能
- 列出破坏性变更
- 提供升级指南

---

## ✅ 验收标准

### 功能验收

- [ ] MainAgent 可以通过工具查询配置
- [ ] MainAgent 可以智能选择 skills
- [ ] MainAgent 可以自主决策不询问用户
- [ ] Subagent 可以接收 skills 列表
- [ ] Subagent 可以动态加载技能内容
- [ ] 技能内容被注入到系统提示
- [ ] 所有技能都可以正确加载
- [ ] 所有工具都可以正确调用

### 质量验收

- [ ] 代码符合 PEP8 规范
- [ ] 测试覆盖率 > 80%
- [ ] 所有测试通过
- [ ] 无内存泄漏
- [ ] 性能满足目标

### 文档验收

- [ ] 用户文档完整
- [ ] 开发者文档完整
- [ ] API 参考完整
- [ ] 示例代码可用
- [ ] 技能文档清晰

### 兼容性验收

- [ ] 向后兼容现有代码
- [ ] 可以平滑升级
- [ ] 无破坏性变更（除非明确说明）

---

## 📅 时间估算

### Phase 1：核心架构搭建
- 预估时间：3-5 天
- 关键路径：是

### Phase 2：技能系统完善
- 预估时间：5-7 天
- 关键路径：是

### Phase 3：工具系统增强
- 预估时间：3-5 天
- 关键路径：否

### Phase 4：集成和测试
- 预估时间：4-6 天
- 关键路径：是



### Phase 5：文档和示例
- 预估时间：3-4 天
- 关键路径：否

### Phase 6：发布和部署
- 预估时间：2-3 天
- 关键路径：是

**总预估时间**：20-30 天

---

## 🚀 执行建议

### 执行顺序

1. **先完成 Phase 1** - 建立基础架构
2. **并行 Phase 2 和 3** - 技能和工具可以并行开发
3. **完成 Phase 4** - 集成和测试
4. **完成 Phase 5** - 文档和示例
5. **完成 Phase 6** - 发布和部署

### 风险和缓解

**风险 1**：时间不足
- 缓解：优先完成 Phase 1 和 2，其他可以后续迭代

**风险 2**：技术难点
- 缓解：遇到难点时及时沟通，寻求帮助

**风险 3**：测试覆盖率不足
- 缓解：编写测试的同时编写代码（TDD）

**风险 4**：文档不完整
- 缓解：使用文档工具自动生成部分内容

### 成功标准

**成功**：
- 所有核心功能实现
- 测试覆盖率 > 80%
- 文档完整
- 性能满足目标
- 可以公开发布

**部分成功**：
- 核心功能实现
- 基本测试通过
- 基本文档完整
- 可以内部使用

**失败**：
- 核心功能未实现
- 测试不通过
- 无法运行

---

## 📞 联系和支持

### 联系人

- **项目负责人**：江亚运
- **架构设计**：参考 OpenClaw

### 技术支持

- **文档**：`docs/ARCHITECTURE_DESIGN.md`
- **示例**：`examples/`
- **测试**：`tests/`

### 问题反馈

- **GitHub Issues**：提交问题和建议
- **Pull Requests**：欢迎贡献

---

## 📝 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v2.0.0 | 2026-02-08 | 初始升级计划 | AI |

---

**记住**：这是一个迭代过程，可以根据实际情况调整计划。重要的是保持目标清晰，持续改进。
