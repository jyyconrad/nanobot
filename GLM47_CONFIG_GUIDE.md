# GLM-4.7 上下文窗口配置指南

## 🔍 参数含义说明

在 `~/.nanobot/config.json` 中，GLM-4.7 的配置如下：

```json
{
  "id": "glm-4.7",
  "contextWindow": 200000,  // 最大输入上下文
  "maxTokens": 8192         // 最大输出 Token 数
}
```

### contextWindow（输入窗口）

- **含义**: 模型支持的最大输入上下文
- **包含**: 系统提示词 + 历史消息 + 用户输入 + 工具调用结果
- **GLM-4.7**: 200,000 tokens

### maxTokens（输出限制）

- **含义**: 模型单次响应的最大输出 Token 数量
- **用途**: 控制响应长度，避免生成过长内容
- **GLM-4.7**: 8,192 tokens

### 总容量

```
总容量 = contextWindow（输入） + maxTokens（输出）
       = 200,000 + 8,192
       ≈ 208,192 tokens
```

---

## ⚙️ GLM-4.7 推荐配置

### 方案 1：保守配置（推荐）

适合大多数场景，平衡各部分空间占用：

```python
# nanobot/agent/context_compressor.py
async def compress(self, content: str, max_tokens: int = 20000) -> ...
async def compress_messages(self, messages: List[Dict], max_tokens: int = 100000) -> ...

# nanobot/agent/context_manager.py
async def build_context(self, session_id: str, task_type: Optional[str] = None, max_tokens: int = 20000) -> ...

# nanobot/session/manager.py
def get_history(self, max_messages: int = 200) -> ...
```

**分配**:
| 组件           | Tokens | 占比 |
| -------------- | ------ | ---- |
| 系统上下文      | 20,000 | 10%   |
| 历史消息        | 100,000 | 50%   |
| 工具调用空间      | 40,000 | 20%   |
| 输出            | 8,192  | 4%    |
| 缓冲        | 31,808 | 15.9% |

### 方案 2：激进配置（最大化历史）

适合需要长期记忆的对话场景：

```python
# nanobot/agent/context_compressor.py
async def compress(self, content: str, max_tokens: int = 15000) -> ...
async def compress_messages(self, messages: List[Dict], max_tokens: int = 130000) -> ...

# nanobot/agent/context_manager.py
async def build_context(self, session_id: str, task_type: Optional[str] = None, max_tokens: int = 15000) -> ...

# nanobot/session/manager.py
def get_history(self, max_messages: int = 300) -> ...
```

**分配**:
| 组件           | Tokens | 占比 |
| -------------- | ------ | ---- |
| 系统上下文      | 15,000 | 7.5%  |
| 历史消息        | 130,000 | 65%   |
| 工具调用空间      | 30,000 | 15%   |
| 输出            | 8,192  | 4%    |
| 缓冲        | 16,808 | 8.4%  |

---

## 📝 具体修改步骤

### 1. 修改 `nanobot/agent/context_compressor.py`

```python
# ========== 第 35 行 ==========
# 修改前
async def compress(self, content: str, max_tokens: int = 200) -> ...

# 修改后（保守配置）
async def compress(self, content: str, max_tokens: int = 20000) -> ...

# ========== 第 49 行 ==========
# 修改前
if len(content) <= max_tokens * 4:  # ❌ 错误的 Token 计算

# 修改后（使用准确的 Token 计算）
if len(content) <= max_tokens * 1.6:  # 1 token ≈ 1.6 字符

# ========== 第 56 行 ==========
# 修改前
compressed = content[: max_tokens * 4]  # ❌ 从开头截断，丢失最新内容

# 修改后
compressed = content[-max_tokens * 1.6:]  # 从尾部截断，保留最新内容

# ========== 第 127 行 ==========
# 修改前
async def compress_messages(self, messages: List[Dict], max_tokens: int = 50) -> ...

# 修改后（保守配置）
async def compress_messages(self, messages: List[Dict], max_tokens: int = 100000) -> ...
```

### 2. 修改 `nanobot/agent/context_manager.py`

```python
# ========== 第 67 行 ==========
# 修改前
async def build_context(self, session_id: str, task_type: Optional[str] = None, max_tokens: int = 4000) -> ...

# 修改后（保守配置）
async def build_context(self, session_id: str, task_type: Optional[str] = None, max_tokens: int = 20000) -> ...
```

### 3. 修改 `nanobot/session/manager.py`

```python
# ========== 第 34 行 ==========
# 修改前
def get_history(self, max_messages: int = 50) -> ...

# 修改后（保守配置）
def get_history(self, max_messages: int = 200) -> ...
# 注释: 200 条消息 * 平均 500 tokens/消息 = 100,000 tokens
```

---

## 🔧 可选：使用配置文件

创建 `~/.nanobot/context_config.yaml`：

```yaml
# GLM-4.7 上下文配置
model: glm-4.7
context_window: 200000  # 模型的输入窗口（不要修改）
max_output: 8192         # 模型的输出限制（不要修改）

# Nanobot 内部配置
system_context:
  max_tokens: 20000      # 系统提示词最大 Token 数

history_context:
  max_tokens: 100000     # 历史消息最大 Token 数
  max_messages: 200       # 最多消息数量
  average_tokens_per_message: 500  # 每条消息的平均 Token 数

tool_context:
  max_tokens: 40000      # 工具调用结果最大 Token 数
  max_tool_calls: 50      # 最多工具调用次数

compression:
  enabled: true
  strategy: "intelligent"  # intelligent, simple, none
  keep_latest: 0.7         # 保留最新内容的比例
  summarize_old: true       # 是否总结旧消息
```

然后在代码中读取：

```python
import yaml

with open("~/.nanobot/context_config.yaml") as f:
    config = yaml.safe_load(f)

system_context_limit = config["system_context"]["max_tokens"]
history_context_limit = config["history_context"]["max_tokens"]
```

---

## 📊 Token 数换算参考

### 消息数量换算

假设平均每条消息 500 tokens：

```python
max_messages = history_context_limit / 500
# 保守配置: 100,000 / 500 = 200 条消息
# 激进配置: 130,000 / 500 = 260 条消息
```

### 字符数换算

GLM-4.7 的 Token/字符比例（经验值）：

```python
# 中文文本
tokens = len(chinese_text) / 1.5  # 1 token ≈ 1.5 字符

# 英文文本
tokens = len(english_text) / 4  # 1 token ≈ 4 字符

# 混合文本（保守估计）
tokens = (len(text) / 1.6)  # 1 token ≈ 1.6 字符
```

---

## 🧪 验证配置

运行以下测试：

```python
import tiktoken

# GLM-4.7 使用 cl100k_base 编码（与 GPT-4 相同）
encoding = tiktoken.get_encoding("cl100k_base")

# 测试文本
text = """
# 系统上下文
你是一个 AI 助手，帮助用户处理编程任务。

# 技能上下文
### coding
支持多种编程语言

# 记忆上下文
用户之前要求编写 Python 函数

# 消息历史
[消息 1] 用户: 请帮我写一个函数
[消息 2] 助手: 好的，我来帮你写
"""

# 计算 Token 数量
tokens = encoding.encode(text)
print(f"文本长度: {len(text)} 字符")
print(f"Token 数量: {len(tokens)}")
print(f"使用比例: {len(tokens) / 200000 * 100:.1f}% of context window")

# 验证是否超过限制
if len(tokens) > 20000:
    print(f"⚠️  超过系统上下文限制: {len(tokens) - 20000} tokens")
```

---

## 📈 实际使用建议

### 场景 1：短对话（日常问答）

```python
# 使用默认保守配置即可
system_context: 20,000 tokens
history_context: 100,000 tokens
```

### 场景 2：长对话（持续编码）

```python
# 适当增加历史系统上下文
system_context: 15,000 tokens
history_context: 130,000 tokens
```

### 场景 3：复杂任务（代码审查、大型项目）

```python
# 增加系统上下文，减少历史
system_context: 30,000 tokens  # 更多技能和项目上下文
history_context: 80,000 tokens  # 减少历史消息
tool_context: 50,000 tokens   # 更多工具调用结果
```

---

## 🚨 注意事项

1. **不要修改 contextWindow 和 maxTokens**
   - 这些是模型固有能力参数
   - 修改会导致 API 调用失败

2. **内部配置可以灵活调整**
   - `max_tokens` 参数是 Nanobot 的内部限制
   - 可以根据实际需求调整

3. **监控实际 Token 使用**
   - 添加日志记录实际的 Token 使用量
   - 根据实际情况调整配置

4. **考虑网络延迟**
   - 上下文越大，传输时间越长
   - 平衡上下文大小和响应速度

---

## 🔗 参考资料

- [GLM-4.7 官方文档](https://open.bigmodel.cn/dev/howuse/model)
- [Token 计算工具](https://platform.openai.com/tokenizer)
- [上下文管理最佳实践](https://docs.anthropic.com/claude/docs/context-windows)

---

**生成时间**: 2025-02-09
**适用模型**: GLM-4.7 (200k 上下文窗口）
