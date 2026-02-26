# Nanobot 上游集成实施计划

**文档版本：** v1.0  
**创建日期：** 2026-02-26  
**项目版本：** v0.4.0 → v0.5.0  
**上游版本：** HKUDS/nanobot @ v0.1.4.post2 (main: cc42510)  

---

## 📋 执行摘要

### 集成策略
采用**方案 A：关键修复 cherry-pick**，选择性集成上游关键修复和优化，保留本地 v0.4.0 扩展功能。

### 总体时间线
- **预计开始日期：** 2026-02-27
- **预计完成日期：** 2026-03-07
- **总工期：** 7 个工作日（56 小时）

### Phase 概览
| Phase | 名称 | 优先级 | 工期 | 依赖项 | Release 版本 |
|-------|------|--------|------|--------|--------------|
| **Phase 0** | 准备工作 | 🔴 最高 | 4h | 无 | - |
| **Phase 1** | 安全修复 | 🔴 最高 | 4h | Phase 0 | v0.4.1-security |
| **Phase 2** | 心跳重构 | 🟠 高 | 8h | Phase 1 | v0.4.2-heartbeat |
| **Phase 3** | MCP 与可靠性 | 🟡 中 | 6h | Phase 1 | v0.4.3-reliability |
| **Phase 4** | Matrix 渠道 | 🟡 中 | 10h | Matrix homeserver | v0.4.4-matrix |
| **Phase 5** | 飞书优化 | 🟢 低 | 6h | 飞书测试环境 | v0.4.5-feishu |

---

## 📂 Phase 0：准备工作

**工期：** 4 小时  
**状态：** ✅ 已完成

### 任务清单

#### 任务 0.1：上游仓库分析
- [x] 获取上游 commits 历史（最近 30+ commits）
- [x] 分析 release notes（v0.1.4 → v0.1.4.post2）
- [x] 识别关键 PR 和修复内容
- [x] 对比本地与上游架构差异

**输出：** 分析总结文档

#### 任务 0.2：差异对比
- [x] 代码行数对比（本地 ~50K vs 上游 ~4K 核心）
- [x] 目录结构对比
- [x] 依赖配置对比
- [x] 识别架构不兼容点

**关键发现：**
- 本地 Fork 已发展出独立功能体系（任务规划器、意图识别、上下文管理）
- 上游专注稳定性与可靠性（32 PRs merged, 14 new contributors）
- 架构差异巨大，不适合直接 merge

#### 任务 0.3：回滚策略实施
- [x] 创建自动化回滚脚本（4 个）
- [x] 创建备份/恢复脚本
- [x] 创建验证脚本
- [x] 编写完整回滚流程文档
- [x] 测试备份脚本功能

**输出：** 
- `scripts/rollback.sh`
- `scripts/backup-data.sh`
- `scripts/restore-data.sh`
- `scripts/verify-rollback.sh`
- `docs/ROLLBACK-PROCEDURE.md`

#### 任务 0.4：环境准备
- [ ] 添加上游 remote
```bash
git remote add upstream https://github.com/HKUDS/nanobot.git
git fetch upstream
```
- [ ] 创建集成分支模板
```bash
git checkout -b integrate/phase1-security
```
- [ ] 配置 CI/CD 流水线
- [ ] 准备测试环境

**验收标准：**
- [x] 回滚策略文档完成
- [x] 所有脚本测试通过
- [ ] 上游 remote 配置完成
- [ ] 分支策略确定

---

## 🔐 Phase 1：安全修复

**工期：** 4 小时  
**优先级：** 🔴 最高  
**Release 版本：** v0.4.1-security

### 集成内容

| PR | 标题 | 文件变更 | 风险等级 |
|----|------|----------|----------|
| #956 | fix(security): prevent path traversal | `nanobot/agent/tools/filesystem.py` | 低 |
| #1071 | fix: resolve API key at call time | `nanobot/providers/litellm_provider.py` | 中 |
| #1098 | fix(web): resolve API key on each call | `nanobot/providers/base.py` | 中 |

### 任务分解

#### 任务 1.1：路径遍历防护（1.5 小时）

**上游参考：** PR #956  
**目标文件：**
- `nanobot/agent/tools/filesystem.py`
- `nanobot/agent/tools/shell.py`

**变更内容：**
```python
# ❌ 旧实现（如果存在）
if not str(resolved_path).startswith(str(workspace)):
    raise SecurityError("Path traversal detected")

# ✅ 新实现
try:
    resolved_path.relative_to(workspace)
except ValueError:
    raise SecurityError("Path traversal detected")
```

**实施步骤：**
1. 检查本地 filesystem.py 中路径验证逻辑
2. 应用 `relative_to()` 修复
3. 更新相关测试用例
4. 运行安全测试

**测试：**
```bash
pytest tests/test_security.py::test_path_traversal -v
pytest tests/test_filesystem.py -v
```

**验收标准：**
- [ ] 路径遍历攻击被阻止
- [ ] workspace 内正常访问不受影响
- [ ] 所有 filesystem 测试通过

---

#### 任务 1.2：API 密钥热加载（2 小时）

**上游参考：** PR #1071, #1098  
**目标文件：**
- `nanobot/providers/litellm_provider.py`
- `nanobot/providers/base.py`

**变更内容：**
```python
# ✅ 添加@property 动态获取 API 密钥
@property
def api_key(self) -> str | None:
    """Resolve API key on each call for hot-reload support."""
    if self.is_openrouter:
        return os.getenv("OPENROUTER_API_KEY") or self._api_key
    elif self.is_custom_openai:
        return os.getenv("OPENAI_API_KEY") or self._api_key
    # ... 其他 provider
    return self._api_key
```

**实施步骤：**
1. 在 `LiteLLMProvider` 类中添加 `api_key` property
2. 为每个 provider 类型添加环境变量检查
3. 移除 `__init__` 中的固定赋值逻辑
4. 更新配置加载器
5. 编写热加载测试

**测试：**
```bash
pytest tests/test_providers.py::test_api_key_hot_reload -v
pytest tests/test_providers.py -v
```

**验收标准：**
- [ ] 修改配置文件后无需重启
- [ ] 环境变量优先级高于配置文件
- [ ] 向后兼容现有配置方式
- [ ] Provider 测试全部通过

---

#### 任务 1.3：文档更新（0.5 小时）

**目标文件：**
- `docs/security.md`
- `CHANGELOG.md`

**变更内容：**
- 更新安全配置说明
- 添加 API 密钥管理最佳实践
- 更新版本号到 v0.4.1-security

**验收标准：**
- [ ] 安全文档更新完成
- [ ] CHANGELOG 记录变更

---

### Phase 1 时间线

| 时间       | 任务          | 交付物                 |
| ---------- | ------------- | ---------------------- |
| Day 1 上午 | 任务 1.1      | 路径遍历修复完成      |
| Day 1 下午 | 任务 1.2+1.3  | API 密钥热加载+文档    |
| Day 1 傍晚 | 测试+Release  | v0.4.1-security 发布  |

---

## 💓 Phase 2：心跳重构

**工期：** 8 小时  
**优先级：** 🟠 高  
**Release 版本：** v0.4.2-heartbeat

### 集成内容

| PR | 标题 | 文件变更 | 风险等级 |
|----|------|----------|----------|
| #1102 | fix(heartbeat): replace HEARTBEAT_OK token | `nanobot/heartbeat/service.py` | 高 |
| #1054 | fix(heartbeat): deliver agent response | `nanobot/heartbeat/service.py` | 中 |
| #1115 | fix: stabilize system prompt | `nanobot/agent/context.py` | 中 |

### 任务分解

#### 任务 2.1：虚拟工具调用决策（4 小时）

**上游参考：** PR #1102, #1054  
**目标文件：**
- `nanobot/heartbeat/service.py`（重写）
- `nanobot/agent/loop.py`（心跳调用部分）

**关键变更：**
1. 添加 `_HEARTBEAT_TOOL` 定义（虚拟工具）
2. 重写 `_decide()` 方法使用工具调用而非文本匹配
3. 移除 `HEARTBEAT_OK_TOKEN` 检测逻辑
4. 添加 `on_notify` 回调支持

**上游代码参考：**
```python
_HEARTBEAT_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "heartbeat",
            "description": "Report heartbeat decision after reviewing tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["skip", "run"],
                        "description": "skip = nothing to do, run = has active tasks",
                    },
                },
                "required": ["action"],
            },
        },
    }
]
```

**实施步骤：**
1. 备份当前 heartbeat/service.py
2. 重写 HeartbeatService 类
3. 实现虚拟工具调用逻辑
4. 更新 Agent Loop 集成
5. 编写单元测试
6. 性能测试（验证静默心跳）

**测试：**
```bash
pytest tests/test_heartbeat.py -v
pytest tests/e2e/test_heartbeat_silent.py -v
```

**验收标准：**
- [ ] 无任务时不触发 LLM 调用（静默）
- [ ] 有任务时正常触发执行阶段
- [ ] 心跳间隔可配置
- [ ] 支持手动触发测试
- [ ] 性能测试通过（LLM 调用减少 50%+）

---

#### 任务 2.2：Prompt 缓存优化（3 小时）

**上游参考：** PR #1115  
**目标文件：**
- `nanobot/agent/context.py`
- `nanobot/agent/prompt_builder.py`

**关键变更：**
```python
# ❌ 旧方式（破坏缓存）
system_prompt = f"""
Current time: {datetime.now()}
Session: {session_id}
...其他动态内容"""

# ✅ 新方式（稳定 system prompt）
system_prompt = """固定系统指令..."""
# 动态内容移至 user message
user_message = {
    "role": "user",
    "content": f"[系统信息] 当前时间：{datetime.now()}\n{实际用户输入}"
}
```

**实施步骤：**
1. 分析当前 context.py 中的 prompt 构建逻辑
2. 分离稳定系统指令和动态上下文
3. 更新 prompt builder
4. 修改 context manager
5. 编写缓存稳定性测试

**测试：**
```bash
pytest tests/test_context.py::test_prompt_stability -v
# 手动验证：监控 LLM API cache hit rate
```

**验收标准：**
- [ ] System prompt 内容稳定（哈希一致）
- [ ] 动态上下文正确传递到 user message
- [ ] LLM API cache 命中率提升
- [ ] 上下文测试通过

---

#### 任务 2.3：文档更新（1 小时）

**目标文件：**
- `docs/heartbeat.md`
- `docs/prompt-cache.md`
- `CHANGELOG.md`

**验收标准：**
- [ ] 心跳机制文档更新
- [ ] Prompt 缓存优化说明
- [ ] CHANGELOG 记录

---

### Phase 2 时间线

| 时间       | 任务          | 交付物                 |
| ---------- | ------------- | ---------------------- |
| Day 2 上午 | 任务 2.1      | 虚拟工具调用实现      |
| Day 2 下午 | 任务 2.1 继续 | 心跳测试通过          |
| Day 3 上午 | 任务 2.2      | Prompt 缓存优化完成   |
| Day 3 下午 | 测试+Release  | v0.4.2-heartbeat 发布 |

---

## 🛠️ Phase 3：MCP 与可靠性修复

**工期：** 6 小时  
**优先级：** 🟡 中  
**Release 版本：** v0.4.3-reliability

### 集成内容

| PR | 标题 | 文件变更 | 风险等级 |
|----|------|----------|----------|
| #950 | fix(mcp): add 30s timeout | `nanobot/agent/tools/mcp.py` | 中 |
| #1062 | fix(mcp): Remove default timeout | `nanobot/agent/tools/mcp.py` | 中 |
| #949 | fix(provider): filter empty content | `nanobot/providers/base.py` | 低 |
| #947 | fix(context): Fix reasoning_content | `nanobot/providers/litellm_provider.py` | 低 |
| #1061 | Fix: memory consolidation TypeError | `nanobot/agent/memory.py` | 低 |
| #1179 | fix: parallel subagent cancellation | `nanobot/agent/subagent/manager.py` | 中 |

### 任务分解

#### 任务 3.1：MCP 超时配置（2 小时）

**上游参考：** PR #950, #1062  
**目标文件：** `nanobot/agent/tools/mcp.py`

**变更内容：**
```python
class MCPToolWrapper(Tool):
    def __init__(self, session, server_name, tool_def, tool_timeout: int = 30):
        self._tool_timeout = tool_timeout  # 可配置超时
    
    async def execute(self, **kwargs: Any) -> str:
        try:
            result = await asyncio.wait_for(
                self._session.call_tool(...),
                timeout=self._tool_timeout
            )
        except asyncio.TimeoutError:
            return f"(MCP tool call timed out after {self._tool_timeout}s)"
```

**配置示例：**
```yaml
mcp_servers:
  - name: github
    url: https://mcp.github.com
    tool_timeout: 60  # 秒
```

**验收标准：**
- [ ] MCP 工具超时可配置
- [ ] 超时后返回友好错误而非挂起
- [ ] HTTP 传输无默认超时

---

#### 任务 3.2：空内容块过滤（1 小时）

**上游参考：** PR #949  
**目标文件：**
- `nanobot/providers/base.py`
- `nanobot/providers/litellm_provider.py`

**变更内容：**
添加 `_sanitize_empty_content()` 静态方法。

**验收标准：**
- [ ] MCP 工具返回空内容时不触发 API 400 错误
- [ ] 空内容被替换为 `"(empty)"` 标记

---

#### 任务 3.3：DeepSeek reasoning_content 规范化（1 小时）

**上游参考：** PR #947  
**目标文件：** `nanobot/providers/litellm_provider.py`

**变更内容：**
```python
# ✅ 多来源兼容处理
reasoning_content = (
    getattr(response, "reasoning_content", None) or
    response.get("reasoning_content") or
    response.get("choices", [{}])[0].get("reasoning_content")
)
```

**验收标准：**
- [ ] DeepSeek 模型推理内容正确提取
- [ ] 其他 provider（Kimi 等）兼容

---

#### 任务 3.4：子代理并行取消（1.5 小时）

**上游参考：** PR #1179  
**目标文件：** `nanobot/agent/subagent/manager.py`

**变更内容：**
```python
# ✅ 并行取消
async def cancel_by_session(self, session_key: str) -> None:
    task_ids = list(self._session_tasks.get(session_key, []))
    await asyncio.gather(*[
        self._running_tasks[tid].cancel() 
        for tid in task_ids 
        if tid in self._running_tasks
    ])
```

**验收标准：**
- [ ] `/stop` 命令并行取消所有子代理
- [ ] 取消速度快于串行方式
- [ ] 清理回调正确执行

---

#### 任务 3.5：Memory consolidation TypeError 修复（0.5 小时）

**上游参考：** PR #1061  
**目标文件：** `nanobot/agent/memory.py`

**验收标准：**
- [ ] LLM 返回 dict 参数时不触发 TypeError
- [ ] Memory consolidation 测试通过

---

### Phase 3 时间线

| 时间       | 任务                     | 交付物                  |
| ---------- | ------------------------ | ----------------------- |
| Day 4 上午 | 任务 3.1+3.2             | MCP 超时+空内容过滤    |
| Day 4 下午 | 任务 3.3+3.4+3.5         | 可靠性修复完成          |
| Day 4 傍晚 | 测试+Release             | v0.4.3-reliability 发布 |

---

## 📱 Phase 4：Matrix 渠道集成

**工期：** 10 小时  
**优先级：** 🟡 中  
**Release 版本：** v0.4.4-matrix  
**前置依赖：** Matrix homeserver 部署完成

### 集成内容

| PR | 标题 | 文件变更 | 风险等级 |
|----|------|----------|----------|
| #420 | feat: add Matrix (Element) channel | `nanobot/channels/matrix.py` (新增) | 中 |
| #1191 | refactor: optimize matrix channel | `nanobot/channels/matrix.py` | 低 |

### 任务分解

#### 任务 4.1：依赖安装（0.5 小时）

**变更文件：** `pyproject.toml`

```toml
[project.optional-dependencies]
matrix = [
    "matrix-nio[e2e]>=0.25.2",
    "mistune>=3.0.0,<4.0.0",
    "nh3>=0.2.17,<1.0.0",
]
```

**安装命令：**
```bash
pip install nanobot-ai[matrix]
```

---

#### 任务 4.2：配置定义（1 小时）

**目标文件：** `nanobot/config/schema.py`

```python
class MatrixConfig(Base):
    """Matrix (Element) channel configuration."""
    enabled: bool = False
    homeserver: str = "https://matrix.org"
    access_token: str = ""
    user_id: str = ""  # @bot:matrix.org
    device_id: str = ""
    e2ee_enabled: bool = True
    sync_stop_grace_seconds: int = 2
    max_media_bytes: int = 20 * 1024 * 1024
    allow_from: list[str] = Field(default_factory=list)
    group_policy: Literal["open", "mention", "allowlist"] = "open"
    group_allow_from: list[str] = Field(default_factory=list)
    allow_room_mentions: bool = False
```

---

#### 任务 4.3：渠道实现（5 小时）

**目标文件：** `nanobot/channels/matrix.py`（新增，682 行）

**核心功能：**
- WebSocket 连接到 Matrix homeserver
- 支持端到端加密（E2EE）
- 群聊策略（open/mention/allowlist）
- 媒体文件处理（图片、文件）
- 消息格式化（Markdown → Matrix HTML）

**实施步骤：**
1. 从上游 cherry-pick matrix.py
2. 调整导入路径适配本地架构
3. 集成到 ChannelManager
4. 编写单元测试
5. 集成测试（需要真实 homeserver）

---

#### 任务 4.4：渠道管理集成（1 小时）

**目标文件：** `nanobot/channels/manager.py`

```python
# Matrix channel
if self.config.channels.matrix.enabled:
    from nanobot.channels.matrix import MatrixChannel
    self.channels["matrix"] = MatrixChannel(
        self.config.channels.matrix,
        self.bus
    )
```

---

#### 任务 4.5：配置文档（2.5 小时）

**目标文件：** `docs/channels/matrix.md`（新增）

**内容包括：**
- Matrix homeserver 部署指南
- Bot 账号创建流程
- 配置参数说明
- 常见问题排查

---

### Phase 4 时间线

| 时间       | 任务          | 交付物                 |
| ---------- | ------------- | ---------------------- |
| Day 5 上午 | 任务 4.1+4.2  | 依赖安装+配置定义     |
| Day 5 下午 | 任务 4.3      | Matrix 渠道实现       |
| Day 6 上午 | 任务 4.3 继续 | 渠道集成完成          |
| Day 6 下午 | 任务 4.4+4.5  | 文档+测试             |
| Day 6 傍晚 | Release       | v0.4.4-matrix 发布    |

---

## ✨ Phase 5：飞书渠道优化

**工期：** 6 小时  
**优先级：** 🟢 低  
**Release 版本：** v0.4.5-feishu  
**前置依赖：** 飞书测试环境

### 集成内容

| PR | 标题 | 文件变更 | 风险等级 |
|----|------|----------|----------|
| #1090 | feat(feishu): support images in post | `nanobot/channels/feishu.py` | 中 |
| #986 | fix(feishu): replace file.get | `nanobot/channels/feishu.py` | 低 |

### 关键差异分析

| 项目         | 本地   | 上游   | 策略     |
| ------------ | ------ | ------ | -------- |
| 代码行数     | 282 行 | 759 行 | **手动合并** |
| 富文本支持   | ❌     | ✅     | 集成功能 |
| 文件下载 API | 旧版本 | 修复版 | 集成修复 |
| 图片提取    | 基础   | 增强   | 集成功能 |

**注意：** 本地飞书渠道已大幅扩展，不能直接覆盖，需手动合并关键功能。

### 任务分解

#### 任务 5.1：富文本图片提取（2 小时）

**上游参考：** PR #1090  
**目标文件：** `nanobot/channels/feishu.py`

**集成功能：**
```python
def _extract_rich_text_images(content: dict) -> list[str]:
    """从富文本消息提取图片 URL。"""
    elements = content.get("elements", [])
    image_urls = []
    for elem in elements:
        if elem.get("tag") == "img":
            image_urls.append(elem.get("image_key"))
    return image_urls
```

---

#### 任务 5.2：文件下载 API 修复（1.5 小时）

**变更内容：**
```python
# ❌ 旧 API
from lark_oapi.api.im.v1 import GetFileRequest

# ✅ 新 API
from lark_oapi.api.im.v1 import GetMessageResourceRequest
```

---

#### 任务 5.3：分享卡片内容提取（2 小时）

**集成功能：**
- `share_chat`：共享聊天
- `share_user`：共享用户
- `share_calendar_event`：共享日历事件
- `interactive`：交互式卡片

---

#### 任务 5.4：文档更新（0.5 小时）

**目标文件：**
- `docs/channels/feishu.md`
- `CHANGELOG.md`

---

### Phase 5 时间线

| 时间       | 任务          | 交付物                 |
| ---------- | ------------- | ---------------------- |
| Day 7 上午 | 任务 5.1+5.2  | 富文本+API 修复        |
| Day 7 下午 | 任务 5.3+5.4  | 分享卡片+文档          |
| Day 7 傍晚 | 测试+Release  | v0.4.5-feishu 发布     |

---

## 🧪 测试策略

### 测试金字塔
```
        E2E 测试 (10%)
       /            \
      /  集成测试 (20%) \
     /__________________\
    /    单元测试 (70%)    \
```

### 各 Phase 测试要求

| Phase   | 单元测试 | 集成测试 | E2E 测试 |
| ------- | -------- | -------- | -------- |
| Phase 1 | ✅ 必需  | ✅ 必需  | ❌ 可选  |
| Phase 2 | ✅ 必需  | ✅ 必需  | ✅ 必需  |
| Phase 3 | ✅ 必需  | ✅ 必需  | ❌ 可选  |
| Phase 4 | ✅ 必需  | ✅ 必需  | ✅ 必需  |
| Phase 5 | ✅ 必需  | ✅ 必需  | ✅ 必需  |

### 测试覆盖率要求
- **单元测试覆盖率：** ≥ 80%
- **集成测试通过率：** ≥ 95%
- **E2E 测试通过率：** 100%

---

## ⚠️ 风险评估

### 技术风险

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 架构冲突 | 高 | 高 | cherry-pick 而非 merge |
| 功能回归 | 中 | 高 | 完整测试覆盖 |
| 数据丢失 | 低 | 高 | 备份 + 回滚策略 |
| 渠道中断 | 中 | 中 | 逐个渠道测试 |
| Matrix homeserver 延迟 | 中 | 中 | Phase 4 可调整顺序 |

### 缓解措施
1. **每个 Phase 独立分支**：`feature/phaseX-xxx`
2. **自动化回滚脚本**：15 分钟内完成回滚
3. **完整测试套件**：每个 Phase 必须通过测试
4. **分阶段部署**：避免一次性发布风险

---

## 📦 依赖更新

### pyproject.toml 变更
```toml
[project]
version = "0.4.1"  # 每个阶段递增

[dependencies]
# 版本约束更新
typer = ">=0.20.0,<1.0.0"        # 0.9.0 → 0.20.0
litellm = ">=1.81.5,<2.0.0"      # 1.0.0 → 1.81.5
pydantic = ">=2.12.0,<3.0.0"     # 2.0.0 → 2.12.0
pydantic-settings = ">=2.12.0,<3.0.0"
websockets = ">=16.0,<17.0"      # 12.0 → 16.0
websocket-client = ">=1.9.0,<2.0.0"
httpx = ">=0.28.0,<1.0.0"        # 0.25.0 → 0.28.0
loguru = ">=0.7.3,<1.0.0"        # 0.7.0 → 0.7.3
readability-lxml = ">=0.8.4,<1.0.0"
rich = ">=14.0.0,<15.0.0"        # 13.0.0 → 14.0.0
croniter = ">=6.0.0,<7.0.0"      # 2.0.0 → 6.0.0
python-telegram-bot = ">=22.0,<23.0"  # 21.0 → 22.0

# 新增依赖
oauth-cli-kit = ">=0.1.3,<1.0.0"
dingtalk-stream = ">=0.24.0,<1.0.0"
lark-oapi = ">=1.5.0,<2.0.0"
socksio = ">=1.0.0,<2.0.0"
python-socketio = ">=5.16.0,<6.0.0"
msgpack = ">=1.1.0,<2.0.0"
slack-sdk = ">=3.39.0,<4.0.0"
slackify-markdown = ">=0.2.0,<1.0.0"
qq-botpy = ">=1.2.0,<2.0.0"
python-socks = ">=2.8.0,<3.0.0"
prompt-toolkit = ">=3.0.50,<4.0.0"
mcp = ">=1.26.0,<2.0.0"
json-repair = ">=0.57.0,<1.0.0"

[project.optional-dependencies]
# 新增 Matrix 支持
matrix = [
    "matrix-nio[e2e]>=0.25.2",
    "mistune>=3.0.0,<4.0.0",
    "nh3>=0.2.17,<1.0.0",
]
```

---

## 🔧 Git 工作流

### 分支策略
```
main
├── feature/phase1-security
├── feature/phase2-heartbeat
├── feature/phase3-reliability
├── feature/phase4-matrix
└── feature/phase5-feishu
```

### 发布流程
```bash
# Phase 1 示例
git checkout main
git checkout -b feature/phase1-security
# ... 实施 + 测试 ...
git commit -m "feat: 集成上游安全修复 (PR #956, #1071, #1098)"
git push origin feature/phase1-security

# 创建 PR 并合并
gh pr create --title "Phase 1: 安全修复" --body "集成路径遍历防护和 API 密钥热加载"
gh pr merge --merge --delete-branch

# 创建 release tag
git tag v0.4.1-security
git push origin v0.4.1-security

# GitHub Release
gh release create v0.4.1-security --title "v0.4.1-security" --notes "安全修复 release"
```

---

## ✅ 验收标准

### Phase 验收清单

| Phase   | 代码完成 | 测试通过 | 文档更新 | Release 发布 |
| ------- | -------- | -------- | -------- | ------------ |
| Phase 1 | ✅       | ✅       | ✅       | ✅           |
| Phase 2 | ✅       | ✅       | ✅       | ✅           |
| Phase 3 | ✅       | ✅       | ✅       | ✅           |
| Phase 4 | ✅       | ✅       | ✅       | ✅           |
| Phase 5 | ✅       | ✅       | ✅       | ✅           |

### 总体成功指标
- [ ] 所有 Phase 完成并发布
- [ ] 测试覆盖率 ≥ 80%
- [ ] 无 P0/P1 级别 bug
- [ ] 回滚演练成功
- [ ] 团队培训完成

---

## 📚 相关文档

- [回滚流程](./docs/ROLLBACK-PROCEDURE.md)
- [回滚实施总结](./docs/ROLLBACK-IMPLEMENTATION-SUMMARY.md)
- [上游集成分析](./UPGRADE-PLAN-v0.5.0.md)
- [测试计划](./docs/TEST-PLAN.md)

---

**文档结束**
