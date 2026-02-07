# Agents.md - Agent 管理文件

## 当前状态
本项目已完成所有核心任务，包括：
- 修复了 Planner 模块的所有测试失败
- 创建了完整的集成测试套件
- 格式化了项目代码
- 完善了项目文档

## 核心功能模块
- **MainAgent**：主代理，负责处理用户请求和管理子代理
- **TaskPlanner**：任务规划器，负责任务识别、规划和调度
- **ContextManager**：上下文管理器，负责处理对话上下文和记忆
- **SubagentManager**：子代理管理器，负责管理子代理的生命周期
- **DecisionMaker**：决策器，负责处理用户请求并生成响应

## 测试状态
- **总测试数**：392 个
- **通过测试数**：392 个
- **总体覆盖率**：28%
- **核心模块覆盖率**：
  - context_manager.py：77%
  - context_compressor.py：25%
  - context_expander.py：21%
  - enhanced_memory.py：40%
  - skill_loader.py：40%
  - cancellation_detector.py：31%
  - complexity_analyzer.py：59%
  - correction_detector.py：33%
  - task_detector.py：30%
  - task_planner.py：64%

## 文档状态
- **API 文档**：已创建，包含所有公共接口的详细说明
- **架构文档**：已创建，描述了项目的整体架构和组件
- **部署文档**：已创建，提供了详细的部署步骤
- **实施计划**：已创建，包含项目的实施步骤和时间估算
- **完成报告**：已创建，总结了项目的实施过程和成果

## 代码质量
- **检查工具**：Ruff
- **结果**：无错误，代码符合规范
- **格式化**：已完成，使用 `ruff format .`

## 未来计划
1. 提高总体测试覆盖率到 60% 以上
2. 为 channels、cli、cron 模块添加基础测试
3. 优化低覆盖率模块的测试覆盖
4. 运行 `ruff format .` 并修复所有警告
5. 优化代码架构，减少技术债务
6. 提高总体测试覆盖率到 80% 以上
7. 添加更多边缘情况的测试

## 团队协作
- **项目负责人**：JiangYayun
- **开发人员**：JiangYayun
- **测试人员**：JiangYayun
- **文档人员**：JiangYayun

## 沟通渠道
- **主要沟通方式**：Feishu
- **备用沟通方式**：微信

## 项目文件结构
```
nanobot/
├── data/              # 数据存储目录
├── docs/              # 文档目录
├── memory/            # 记忆存储目录
├── nanobot/           # 核心代码目录
├── scripts/           # 脚本目录
├── tests/             # 测试目录
├── upgrade-plan/      # 升级计划目录
├── workspace/         # 工作区目录
├── AGENTS.md          # Agent 管理文件
├── COMPLETION_REPORT.md # 项目完成报告
├── IMPLEMENTATION_SUMMARY.md # 实施总结
├── MEMORY.md          # 项目状态记忆
├── README.md          # 项目说明文件
└── pyproject.toml     # 项目配置文件
```

## 快速启动
1. 安装依赖：`pip install -e .`
2. 运行测试：`python -m pytest tests/ -v`
3. 启动代理：`nanobot agent`

## 注意事项
- 项目使用 Python 3.13 开发
- 所有代码符合 Ruff 规范
- 所有测试通过
- 项目使用 Pydantic 2.0，存在一些警告，需要在未来版本中修复
