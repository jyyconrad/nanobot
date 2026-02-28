# Changelog

## [0.4.4] - 2026-02-28

### 新增功能

- **Matrix 渠道集成**：
  - WebSocket 长连接同步消息
  - 端到端加密（E2EE）支持
  - 群组策略（open/mention/allowlist）
  - 媒体文件处理（图片、音频、视频、文件）
  - Markdown 到 Matrix HTML 渲染
  - 线程消息支持

- **上游 PR 合并**：
  - PR #1083: path_append 配置（扩展 PATH 环境变量）
  - PR #1214: 支持显式选择 provider

### 配置更新

- 新增 `matrix` 可选依赖：`matrix-nio[e2e]`, `mistune`, `nh3`
- 新增 `MatrixConfig` 配置类
- ExecToolConfig 新增 `path_append` 字段
- AgentDefaults 新增 `provider` 字段

---

## [0.4.3] - 2026-02-28

### 新增功能

- **空内容过滤**：
  - `_sanitize_empty_content()` 方法过滤空内容块
  - 防止 MCP 工具返回空内容时触发 API 400 错误

- **DeepSeek reasoning_content 支持**：
  - 在 `LLMResponse` 中添加 `reasoning_content` 字段
  - 支持思维模型（DeepSeek-R1、Kimi 等）的推理内容提取

### 测试

- 添加 18 个可靠性测试用例

---

## [0.4.2] - 2026-02-28

### 新增功能

- **心跳重构**：
  - 虚拟工具调用决策机制
  - 静默心跳（无任务时不触发 LLM 调用）
  - 大幅降低 API 成本

### 修复问题

- 移除不可靠的 `HEARTBEAT_OK_TOKEN` 检测逻辑

---

## [0.4.1] - 2026-02-28

### 安全修复

- **路径遍历防护**：
  - `_resolve_path()` 辅助函数
  - ReadFileTool/WriteFileTool/ListDirTool 支持 workspace 和 allowed_dir 参数

- **API 密钥热加载**：
  - `api_key` 属性动态解析
  - 环境变量优先级高于配置文件
  - 配置更改无需重启即可生效

### 测试

- 添加 13 个安全测试用例

---

## [0.4.0] - 2026-02-14

### 新增功能

- **多渠道集成**：
  - 飞书渠道支持
  - WebChat 渠道支持  
  - TUI 终端渠道支持
  - 渠道管理器和路由策略

- **架构优化**：
  - 子代理管理机制
  - 并发处理优化
  - 错误恢复机制
  - 服务间通信优化

- **用户体验改进**：
  - 交互流程优化
  - 反馈机制改进
  - 可视化效果增强
  - 进度条显示
  - 实时状态更新

- **系统稳定性**：
  - 监控和日志记录
  - 性能优化
  - 系统可运维性
  - 配置热重载
  - 优雅关闭

### 修复问题

- 修复 Pydantic V2 deprecation warnings（将 class-based config 改为 ConfigDict）
- 修复代码审查问题
- 优化性能瓶颈

### 技术改进

- 升级到 Pydantic V2
- 增强的测试覆盖
- 代码质量优化
- 文档完善

---

## [0.2.1] - 2026-02-12

### 版本说明

这是一个中间版本，主要包含：

- 基础架构搭建
- 核心功能实现
- 初始测试覆盖

---

## [0.1.x] - 2026-02-12 之前

### 初始版本

- 项目启动
- 基础功能开发
- 架构设计
