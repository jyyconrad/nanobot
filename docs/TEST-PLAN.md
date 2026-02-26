# Nanobot 上游集成测试计划

**文档版本：** v1.0  
**创建日期：** 2026-02-26  
**适用范围：** Phase 1-5 所有集成阶段  

---

## 📋 目录

1. [测试策略概述](#测试策略概述)
2. [测试环境配置](#测试环境配置)
3. [Phase 1 测试计划](#phase-1-测试计划)
4. [Phase 2 测试计划](#phase-2-测试计划)
5. [Phase 3 测试计划](#phase-3-测试计划)
6. [Phase 4 测试计划](#phase-4-测试计划)
7. [Phase 5 测试计划](#phase-5-测试计划)
8. [E2E 测试计划](#e2e-测试计划)
9. [性能测试计划](#性能测试计划)
10. [测试报告模板](#测试报告模板)

---

## 🎯 测试策略概述

### 测试金字塔

```
        ┌───────────────┐
        │   E2E 测试     │  10%
        │   (10 个用例)   │
        ├───────────────┤
        │  集成测试      │  20%
        │  (30 个用例)    │
        ├───────────────┤
        │  单元测试      │  70%
        │  (100+ 个用例)  │
        └───────────────┘
```

### 测试覆盖率要求

| 测试类型 | 覆盖率要求 | 执行频率 |
|----------|------------|----------|
| 单元测试 | ≥ 80%      | 每次提交  |
| 集成测试 | ≥ 95% 通过 | 每日构建  |
| E2E 测试 | 100% 通过  | 发布前    |

### 测试工具链

| 工具 | 用途 | 版本 |
|------|------|------|
| pytest | 单元测试框架 | ≥7.0.0 |
| pytest-asyncio | 异步测试支持 | ≥0.21.0 |
| pytest-cov | 覆盖率报告 | ≥7.0.0 |
| pytest-mock | Mock 支持 | ≥3.15.0 |
| httpx-mock | HTTP 请求模拟 | 最新 |

---

## 🖥️ 测试环境配置

### 环境要求

| 环境 | 用途 | 配置要求 |
|------|------|----------|
| **开发环境** | 单元测试 | Python 3.11+, 8GB RAM |
| **集成环境** | 集成测试 | Python 3.11+, 16GB RAM, 外部服务访问 |
| **E2E 环境** | 端到端测试 | 完整部署，真实渠道配置 |

### 测试数据准备

#### 1. 单元测试数据
```python
# tests/fixtures.py
@pytest.fixture
def sample_config():
    return {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "api_key": "test-key",
    }

@pytest.fixture
def mock_llm_response():
    return LLMResponse(
        content="Test response",
        tool_calls=[],
        finish_reason="stop"
    )
```

#### 2. 集成测试数据
```python
# tests/integration/fixtures.py
@pytest.fixture
async def test_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "HEARTBEAT.md").write_text("# Test")
    return workspace
```

#### 3. E2E 测试数据
```python
# tests/e2e/fixtures.py
@pytest.fixture
def matrix_test_account():
    return {
        "homeserver": "https://matrix.org",
        "user_id": "@testbot:matrix.org",
        "access_token": "xxx",
    }
```

---

## 🔐 Phase 1 测试计划

### 测试范围

| 功能 | 测试类型 | 用例数 | 优先级 |
|------|----------|--------|--------|
| 路径遍历防护 | 单元测试 | 5 | P0 |
| API 密钥热加载 | 单元测试 | 4 | P0 |
| 配置文件加载 | 集成测试 | 3 | P1 |

---

### 测试用例 1.1：路径遍历防护

**测试文件：** `tests/test_security.py`

#### 用例 1.1.1：阻止路径遍历攻击
```python
class TestPathTraversal:
    """Test path traversal prevention."""
    
    async def test_block_path_traversal_outside_workspace(self):
        """Test that paths outside workspace are blocked."""
        tool = ReadFileTool(workspace=Path("/workspace"))
        
        with pytest.raises(SecurityError) as exc_info:
            await tool.execute(path="/etc/passwd")
        
        assert "Path traversal detected" in str(exc_info.value)
    
    async def test_block_path_traversal_with_dotdot(self):
        """Test that ../ sequences are blocked."""
        tool = ReadFileTool(workspace=Path("/workspace"))
        
        with pytest.raises(SecurityError):
            await tool.execute(path="../../../etc/passwd")
    
    async def test_allow_valid_paths_within_workspace(self):
        """Test that valid paths within workspace are allowed."""
        tool = ReadFileTool(workspace=Path("/workspace"))
        
        # Should not raise
        result = await tool.execute(path="/workspace/file.txt")
        assert result is not None
```

**验收标准：**
- [ ] 所有路径遍历攻击被阻止
- [ ] workspace 内正常访问不受影响
- [ ] 错误消息清晰明确

---

### 测试用例 1.2：API 密钥热加载

**测试文件：** `tests/test_providers.py`

#### 用例 1.2.1：环境变量优先级
```python
class TestAPIKeyHotReload:
    """Test API key hot-reload functionality."""
    
    def test_env_var_priority(self, monkeypatch):
        """Test that environment variables take priority."""
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        
        provider = LiteLLMProvider(api_key="config-key")
        
        # Property should return env var value
        assert provider.api_key == "env-key"
    
    def test_config_fallback(self, monkeypatch):
        """Test fallback to config value when no env var."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        provider = LiteLLMProvider(api_key="config-key")
        
        assert provider.api_key == "config-key"
    
    async def test_key_change_without_restart(self, monkeypatch):
        """Test that API key changes take effect without restart."""
        monkeypatch.setenv("OPENAI_API_KEY", "key-1")
        
        provider = LiteLLMProvider(api_key="key-1")
        assert provider.api_key == "key-1"
        
        # Change env var
        monkeypatch.setenv("OPENAI_API_KEY", "key-2")
        
        # Should reflect new value without restart
        assert provider.api_key == "key-2"
```

**验收标准：**
- [ ] 环境变量优先级高于配置
- [ ] 配置变更无需重启生效
- [ ] 向后兼容现有方式

---

### Phase 1 测试执行

```bash
# 运行安全测试
pytest tests/test_security.py -v --cov=nanobot.agent.tools

# 运行 Provider 测试
pytest tests/test_providers.py -v --cov=nanobot.providers

# 生成覆盖率报告
pytest tests/test_security.py tests/test_providers.py --cov=nanobot --cov-report=html
```

---

## 💓 Phase 2 测试计划

### 测试范围

| 功能 | 测试类型 | 用例数 | 优先级 |
|------|----------|--------|--------|
| 虚拟工具调用决策 | 单元测试 | 6 | P0 |
| 静默心跳验证 | 集成测试 | 4 | P0 |
| Prompt 缓存优化 | 集成测试 | 5 | P1 |

---

### 测试用例 2.1：虚拟工具调用决策

**测试文件：** `tests/test_heartbeat.py`

#### 用例 2.1.1：工具调用决策
```python
class TestHeartbeatToolCall:
    """Test heartbeat tool call decision mechanism."""
    
    async def test_skip_action_when_no_tasks(self, mock_provider):
        """Test that heartbeat returns 'skip' when no tasks."""
        mock_provider.set_response(
            tool_calls=[ToolCallRequest(
                id="1",
                name="heartbeat",
                arguments={"action": "skip"}
            )]
        )
        
        heartbeat = HeartbeatService(workspace=Path("/tmp"))
        action, tasks = await heartbeat._decide("empty content")
        
        assert action == "skip"
    
    async def test_run_action_when_has_tasks(self, mock_provider):
        """Test that heartbeat returns 'run' when tasks exist."""
        mock_provider.set_response(
            tool_calls=[ToolCallRequest(
                id="1",
                name="heartbeat",
                arguments={"action": "run", "tasks": "Task 1"}
            )]
        )
        
        heartbeat = HeartbeatService(workspace=Path("/tmp"))
        action, tasks = await heartbeat._decide("has tasks")
        
        assert action == "run"
        assert tasks == "Task 1"
```

---

### 测试用例 2.2：静默心跳验证

**测试文件：** `tests/integration/test_heartbeat_silent.py`

#### 用例 2.2.1：无任务时静默
```python
class TestHeartbeatSilent:
    """Test that heartbeat is silent when no tasks."""
    
    async def test_no_llm_call_when_empty_heartbeat(self):
        """Test that no LLM call is made when HEARTBEAT.md is empty."""
        llm_call_count = 0
        
        async def mock_chat(*args, **kwargs):
            nonlocal llm_call_count
            llm_call_count += 1
            return LLMResponse(content="OK")
        
        heartbeat = HeartbeatService(
            workspace=empty_workspace,
            on_heartbeat=mock_chat
        )
        
        await heartbeat._tick()
        
        # Should not call LLM when no tasks
        assert llm_call_count == 0
    
    async def test_llm_call_when_has_tasks(self):
        """Test that LLM is called when tasks exist."""
        llm_call_count = 0
        
        async def mock_chat(*args, **kwargs):
            nonlocal llm_call_count
            llm_call_count += 1
            return LLMResponse(content="completed")
        
        heartbeat = HeartbeatService(
            workspace=workspace_with_tasks,
            on_heartbeat=mock_chat
        )
        
        await heartbeat._tick()
        
        # Should call LLM when tasks exist
        assert llm_call_count == 1
```

---

### 测试用例 2.3：Prompt 缓存优化

**测试文件：** `tests/test_context.py`

#### 用例 2.3.1：System prompt 稳定性
```python
class TestPromptStability:
    """Test prompt cache optimization."""
    
    def test_system_prompt_is_stable(self):
        """Test that system prompt content doesn't change."""
        builder1 = ContextBuilder(workspace=Path("/tmp"))
        builder2 = ContextBuilder(workspace=Path("/tmp"))
        
        prompt1 = builder1.build_system_prompt()
        prompt2 = builder2.build_system_prompt()
        
        # Should be identical for cache reuse
        assert prompt1 == prompt2
        assert hash(prompt1) == hash(prompt2)
    
    def test_dynamic_context_in_user_message(self):
        """Test that dynamic context is moved to user message."""
        builder = ContextBuilder(workspace=Path("/tmp"))
        
        system_prompt = builder.build_system_prompt()
        user_message = builder.build_user_message("test")
        
        # System prompt should not contain timestamps
        assert "current time" not in system_prompt.lower()
        
        # User message should contain dynamic context
        assert "当前时间" in user_message or "current time" in user_message.lower()
```

---

### Phase 2 测试执行

```bash
# 运行心跳测试
pytest tests/test_heartbeat.py -v --cov=nanobot.heartbeat

# 运行上下文测试
pytest tests/test_context.py -v --cov=nanobot.agent.context

# E2E 心跳流程测试
pytest tests/e2e/test_heartbeat_flow.py -v

# 生成覆盖率报告
pytest tests/test_heartbeat.py tests/test_context.py --cov=nanobot --cov-report=html
```

---

## 🛠️ Phase 3 测试计划

### 测试范围

| 功能 | 测试类型 | 用例数 | 优先级 |
|------|----------|--------|--------|
| MCP 超时配置 | 单元测试 | 4 | P1 |
| 空内容块过滤 | 单元测试 | 5 | P1 |
| DeepSeek reasoning_content | 单元测试 | 3 | P2 |
| 子代理并行取消 | 集成测试 | 4 | P1 |
| Memory consolidation | 单元测试 | 3 | P2 |

---

### 测试用例 3.1：MCP 超时配置

**测试文件：** `tests/test_mcp.py`

#### 用例 3.1.1：工具超时触发
```python
class TestMCPTimeout:
    """Test MCP tool timeout configuration."""
    
    async def test_tool_timeout_triggers(self):
        """Test that timeout is triggered for slow tools."""
        tool = MCPToolWrapper(
            session=mock_session,
            server_name="test",
            tool_def=mock_tool_def,
            tool_timeout=1  # 1 second timeout
        )
        
        mock_session.call_tool = asyncio.sleep(10)  # Simulate slow tool
        
        with pytest.raises(asyncio.TimeoutError):
            await tool.execute()
    
    async def test_timeout_error_message(self):
        """Test that timeout returns user-friendly message."""
        tool = MCPToolWrapper(
            session=mock_session,
            server_name="test",
            tool_def=mock_tool_def,
            tool_timeout=30
        )
        
        mock_session.call_tool = asyncio.sleep(60)
        
        result = await tool.execute()
        
        assert "timed out after 30s" in result
```

---

### 测试用例 3.2：空内容块过滤

**测试文件：** `tests/test_providers.py`

#### 用例 3.2.1：空字符串过滤
```python
class TestEmptyContentSanitization:
    """Test empty content block filtering."""
    
    def test_sanitize_empty_string_content(self):
        """Test that empty string content is sanitized."""
        messages = [{"role": "user", "content": ""}]
        
        result = LLMProvider._sanitize_empty_content(messages)
        
        assert result[0]["content"] == "(empty)"
    
    def test_sanitize_empty_list_content(self):
        """Test that empty list content is sanitized."""
        messages = [{"role": "assistant", "content": []}]
        
        result = LLMProvider._sanitize_empty_content(messages)
        
        assert result[0]["content"] == "(empty)"
    
    def test_preserve_non_empty_content(self):
        """Test that non-empty content is preserved."""
        messages = [{"role": "user", "content": "Hello"}]
        
        result = LLMProvider._sanitize_empty_content(messages)
        
        assert result[0]["content"] == "Hello"
    
    def test_filter_empty_text_blocks(self):
        """Test that empty text blocks in list are filtered."""
        messages = [{
            "role": "assistant",
            "content": [
                {"type": "text", "text": ""},
                {"type": "text", "text": "Valid"},
                {"type": "text", "text": ""}
            ]
        }]
        
        result = LLMProvider._sanitize_empty_content(messages)
        
        assert len(result[0]["content"]) == 1
        assert result[0]["content"][0]["text"] == "Valid"
```

---

### 测试用例 3.3：子代理并行取消

**测试文件：** `tests/test_subagent.py`

#### 用例 3.3.1：并行取消性能
```python
class TestParallelCancellation:
    """Test parallel subagent cancellation."""
    
    async def test_parallel_cancellation_faster(self):
        """Test that parallel cancellation is faster than sequential."""
        manager = SubagentManager(...)
        
        # Create 10 tasks
        for i in range(10):
            task_id = f"task-{i}"
            manager._running_tasks[task_id] = asyncio.create_task(
                asyncio.sleep(10)
            )
            manager._session_tasks["session1"].add(task_id)
        
        # Measure parallel cancellation time
        start = time.time()
        await manager.cancel_by_session("session1")
        parallel_time = time.time() - start
        
        # Should be much faster than sequential (10 seconds)
        assert parallel_time < 2.0  # Should complete in < 2 seconds
```

---

### Phase 3 测试执行

```bash
# 运行 MCP 测试
pytest tests/test_mcp.py -v --cov=nanobot.agent.tools.mcp

# 运行 Provider 测试
pytest tests/test_providers.py::TestEmptyContentSanitization -v

# 运行子代理测试
pytest tests/test_subagent.py::TestParallelCancellation -v

# 生成覆盖率报告
pytest tests/test_mcp.py tests/test_providers.py tests/test_subagent.py \
    --cov=nanobot --cov-report=html
```

---

## 📱 Phase 4 测试计划

### 测试范围

| 功能 | 测试类型 | 用例数 | 优先级 |
|------|----------|--------|--------|
| Matrix 连接 | 单元测试 | 5 | P0 |
| 消息收发 | 集成测试 | 8 | P0 |
| E2EE 加密 | 集成测试 | 4 | P1 |
| 群聊策略 | 集成测试 | 6 | P1 |
| 媒体文件处理 | 集成测试 | 4 | P2 |

---

### 测试用例 4.1：Matrix 连接

**测试文件：** `tests/channels/test_matrix.py`

#### 用例 4.1.1：客户端连接
```python
class TestMatrixConnection:
    """Test Matrix client connection."""
    
    async def test_connect_to_homeserver(self, matrix_config):
        """Test successful connection to homeserver."""
        channel = MatrixChannel(matrix_config, mock_bus)
        
        await channel.start()
        
        assert channel.is_connected
        assert channel.client is not None
    
    async def test_connect_with_invalid_token(self, matrix_config):
        """Test connection fails with invalid token."""
        matrix_config.access_token = "invalid-token"
        
        channel = MatrixChannel(matrix_config, mock_bus)
        
        with pytest.raises(AuthenticationError):
            await channel.start()
```

---

### 测试用例 4.2：消息收发

**测试文件：** `tests/integration/test_matrix_channel.py`

#### 用例 4.2.1：发送消息
```python
class TestMatrixMessaging:
    """Test Matrix messaging."""
    
    async def test_send_text_message(self, matrix_channel):
        """Test sending text message to Matrix room."""
        msg = OutboundMessage(
            channel="matrix",
            chat_id="!room:matrix.org",
            content="Hello from Nanobot"
        )
        
        await matrix_channel.send(msg)
        
        # Verify message was sent (check mock or actual room)
        assert message_sent
```

---

### Phase 4 测试执行

```bash
# 运行 Matrix 单元测试
pytest tests/channels/test_matrix.py -v

# 运行 Matrix 集成测试（需要 homeserver）
pytest tests/integration/test_matrix_channel.py -v

# E2E 测试
pytest tests/e2e/test_matrix_conversation.py -v

# 生成覆盖率报告
pytest tests/channels/ --cov=nanobot.channels --cov-report=html
```

---

## ✨ Phase 5 测试计划

### 测试范围

| 功能 | 测试类型 | 用例数 | 优先级 |
|------|----------|--------|--------|
| 富文本图片提取 | 单元测试 | 4 | P1 |
| 文件下载 API | 集成测试 | 3 | P1 |
| 分享卡片解析 | 单元测试 | 4 | P2 |

---

### 测试用例 5.1：富文本图片提取

**测试文件：** `tests/channels/test_feishu_images.py`

#### 用例 5.1.1：图片 URL 提取
```python
class TestFeishuImageExtraction:
    """Test Feishu rich text image extraction."""
    
    def test_extract_images_from_rich_text(self):
        """Test extracting image URLs from rich text."""
        content = {
            "elements": [
                {"tag": "text", "text": "Hello"},
                {"tag": "img", "image_key": "img-123"},
                {"tag": "text", "text": "World"},
                {"tag": "img", "image_key": "img-456"}
            ]
        }
        
        images = _extract_rich_text_images(content)
        
        assert len(images) == 2
        assert "img-123" in images
        assert "img-456" in images
    
    def test_extract_with_no_images(self):
        """Test extraction when no images present."""
        content = {
            "elements": [
                {"tag": "text", "text": "Hello"},
                {"tag": "link", "url": "https://example.com"}
            ]
        }
        
        images = _extract_rich_text_images(content)
        
        assert len(images) == 0
```

---

### Phase 5 测试执行

```bash
# 运行飞书测试
pytest tests/channels/test_feishu.py -v

# 运行图片提取测试
pytest tests/channels/test_feishu_images.py -v

# 生成覆盖率报告
pytest tests/channels/test_feishu*.py --cov=nanobot.channels.feishu --cov-report=html
```

---

## 🎬 E2E 测试计划

### E2E 测试场景

| 场景 | 描述 | Phase | 用例数 |
|------|------|-------|--------|
| 完整对话流程 | 用户发送消息 → 处理 → 回复 | All | 5 |
| 心跳触发流程 | 心跳检测 → 任务执行 → 通知 | Phase 2 | 3 |
| 子代理工作流 | 主代理 → 创建子代理 → 结果汇总 | Phase 3 | 4 |
| Matrix 对话 | Matrix 用户 ↔ Bot 完整对话 | Phase 4 | 4 |
| 飞书富文本 | 飞书富文本消息处理 | Phase 5 | 3 |

---

### E2E 测试用例示例

**测试文件：** `tests/e2e/test_conversation.py`

```python
class TestEndToEndConversation:
    """E2E conversation flow tests."""
    
    async def test_full_conversation_flow(self):
        """Test complete conversation from user to response."""
        # Setup
        user_message = InboundMessage(
            channel="tui",
            chat_id="user-1",
            content="What's the weather today?"
        )
        
        # Send message
        await message_bus.publish_inbound(user_message)
        
        # Wait for response (with timeout)
        response = await asyncio.wait_for(
            message_bus.consume_outbound(),
            timeout=30.0
        )
        
        # Verify
        assert response is not None
        assert response.channel == "tui"
        assert len(response.content) > 0
    
    async def test_conversation_with_tool_call(self):
        """Test conversation that involves tool calls."""
        user_message = InboundMessage(
            channel="tui",
            chat_id="user-1",
            content="List files in current directory"
        )
        
        await message_bus.publish_inbound(user_message)
        
        # Should call exec tool
        response = await asyncio.wait_for(
            message_bus.consume_outbound(),
            timeout=30.0
        )
        
        assert "file" in response.content.lower() or "directory" in response.content.lower()
```

---

### E2E 测试执行

```bash
# 运行所有 E2E 测试
pytest tests/e2e/ -v --tb=short

# 运行特定场景
pytest tests/e2e/test_conversation.py -v
pytest tests/e2e/test_heartbeat_flow.py -v
pytest tests/e2e/test_matrix_conversation.py -v

# 生成 HTML 报告
pytest tests/e2e/ --html=reports/e2e-report.html --self-contained-html
```

---

## 📊 性能测试计划

### 性能指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 心跳响应时间 | < 1 秒 | 时间戳对比 |
| MCP 工具调用延迟 | < 5 秒 | 工具执行时间 |
| 子代理创建时间 | < 2 秒 | 创建到运行时间 |
| 消息处理吞吐量 | > 100 msg/s | 压力测试 |
| 内存使用率 | < 500MB | 系统监控 |

---

### 性能测试用例

**测试文件：** `tests/performance/test_heartbeat.py`

```python
class TestHeartbeatPerformance:
    """Heartbeat performance tests."""
    
    async def test_heartbeat_response_time(self):
        """Test heartbeat response time."""
        heartbeat = HeartbeatService(...)
        
        start = time.time()
        await heartbeat._tick()
        elapsed = time.time() - start
        
        # Should complete within 1 second
        assert elapsed < 1.0
    
    async def test_silent_heartbeat_no_llm_call(self):
        """Test that silent heartbeat doesn't call LLM."""
        call_count = 0
        
        async def mock_chat(*args, **kwargs):
            nonlocal call_count
            call_count += 1
        
        heartbeat = HeartbeatService(
            workspace=empty_workspace,
            on_heartbeat=mock_chat
        )
        
        start = time.time()
        for _ in range(10):
            await heartbeat._tick()
        elapsed = time.time() - start
        
        # No LLM calls should be made
        assert call_count == 0
        # Should be very fast (< 0.1s per tick)
        assert elapsed < 1.0
```

---

### 性能测试执行

```bash
# 运行性能测试
pytest tests/performance/ -v --tb=short

# 生成性能报告
pytest tests/performance/ --benchmark-json=reports/performance.json
```

---

## 📝 测试报告模板

### Phase 测试报告模板

```markdown
# Phase X 测试报告

**Phase 名称：** [名称]  
**测试日期：** YYYY-MM-DD  
**测试执行人：** XXX  

## 测试总结

| 测试类型 | 通过 | 失败 | 跳过 | 覆盖率 |
|----------|------|------|------|--------|
| 单元测试 | XX   | 0    | 0    | XX%    |
| 集成测试 | XX   | 0    | 0    | XX%    |
| E2E 测试 | XX   | 0    | 0    | XX%    |
| **总计** | **XX** | **0** | **0** | **XX%** |

## 测试环境

- Python 版本：3.11.x
- pytest 版本：7.x.x
- 操作系统：macOS/Linux

## 关键发现

### ✅ 通过的测试
- [测试用例 1]
- [测试用例 2]

### ⚠️ 失败/跳过的测试
- [无]

### 📊 性能指标
- 心跳响应时间：XX ms
- MCP 工具调用延迟：XX ms
- 内存使用率：XX MB

## 问题与风险

| 问题 | 严重程度 | 状态 |
|------|----------|------|
| [无] | - | - |

## 结论

[通过/不通过] - Phase X 测试完成，满足发布标准。

## 附录

- [覆盖率报告链接]
- [性能报告链接]
- [完整测试日志]
```

---

## 🎯 测试准入/准出标准

### 准入标准（开始测试前）
- [ ] 代码审查完成
- [ ] 单元测试编写完成
- [ ] 测试环境准备就绪
- [ ] 测试数据准备完成

### 准出标准（测试完成后）
- [ ] 所有 P0 测试通过
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试通过率 ≥ 95%
- [ ] E2E 测试 100% 通过
- [ ] 性能指标达标
- [ ] 测试报告完成

---

## 📚 相关文档

- [实施计划](./IMPLEMENTATION-PHASES.md)
- [回滚流程](./ROLLBACK-PROCEDURE.md)
- [测试最佳实践](./TESTING-BEST-PRACTICES.md)

---

**文档结束**
