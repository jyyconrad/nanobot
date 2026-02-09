# 上下文监控钩子设计

## 📋 需求说明

添加一个默认钩子或配置，当上下文长度达到窗口的 60% 时触发上下文管理程序，使用当前的上下文管理体系管理输入的内容。

---

## 🎯 设计目标

1. **实时监控** - 在每次添加消息后检查上下文长度
2. **阈值触发** - 当达到窗口的 60% 时自动触发压缩
3. **智能压缩** - 使用已有的 ContextCompressorV2 进行压缩
4. **可配置** - 支持自定义阈值和压缩策略

---

## 🏗️ 核心设计

### 1. 上下文监控器（ContextMonitor）

```python
import logging
from typing import List, Dict, Optional, Callable
from datetime import datetime

class ContextMonitor:
    """
    上下文监控器

    功能：
    - 监控上下文长度
    - 当达到阈值时触发压缩
    - 使用 ContextCompressorV2 进行压缩
    - 支持自定义钩子
    """

    def __init__(
        self,
        context_compressor,
        max_tokens: int = 128000,  # Claude 3.5 Sonnet 默认窗口
        threshold_percent: float = 0.6,  # 60% 阈值
        hooks: Optional["HookSystem"] = None
    ):
        """
        初始化上下文监控器

        Args:
            context_compressor: 上下文压缩器实例
            max_tokens: 上下文窗口最大 token 数
            threshold_percent: 触发压缩的阈值百分比
            hooks: 钩子系统实例
        """
        self.compressor = context_compressor
        self.max_tokens = max_tokens
        self.threshold = max_tokens * threshold_percent
        self.hooks = hooks or HookSystem()
        self.logger = logging.getLogger(__name__)

        # 统计信息
        self.stats = {
            "total_checks": 0,
            "compressions_triggered": 0,
            "messages_compressed": 0,
            "tokens_saved": 0
        }

        # 注册默认钩子
        self._register_default_hooks()

    def check_and_compress(
        self,
        messages: List[Dict],
        compress_system: bool = False
    ) -> List[Dict]:
        """
        检查并压缩上下文

        Args:
            messages: 当前消息列表
            compress_system: 是否压缩系统消息（通常不压缩）

        Returns:
            压缩后的消息列表
        """
        self.stats["total_checks"] += 1

        # 计算当前 token 数
        current_tokens = self._count_tokens(messages)

        self.logger.debug(
            "Context check: %d / %d tokens (%.1f%%)",
            current_tokens,
            self.max_tokens,
            current_tokens / self.max_tokens * 100
        )

        # 检查是否达到阈值
        if current_tokens >= self.threshold:
            self.logger.info(
                "Context threshold reached (%.1f%%, triggering compression",
                current_tokens / self.max_tokens * 100
            )

            # 触发压缩前钩子
            self.hooks.trigger(
                "before_context_compression",
                current_tokens=current_tokens,
                max_tokens=self.max_tokens,
                threshold=self.threshold=self.threshold,
                messages_count=len(messages)
            )

            # 执行压缩
            compressed_messages, stats = self._compress_messages(
                messages,
                compress_system=compress_system
            )

            # 更新统计
            self.stats["compressions_triggered"] += 1
            self.stats["messages_compressed"] += len(messages) - len(compressed_messages)
            self.stats["tokens_saved"] += current_tokens - self._count_tokens(compressed_messages)

            # 触发压缩后钩子
            self.hooks.trigger(
                "after_context_compression",
                original_count=len(messages),
                compressed_count=len(compressed_messages),
                original_tokens=current_tokens,
                compressed_tokens=self._count_tokens(compressed_messages),
                compression_ratio=stats.compression_ratio
            )

            # 记录压缩结果
            self.logger.info(
                "Context compressed: %d → %d messages (%.1f%% ratio, %d tokens saved)",
                len(messages),
                len(compressed_messages),
                stats.compression_ratio * 100,
                self._count_tokens(messages) - self._count_tokens(compressed_messages)
            )

            return compressed_messages

        return messages

    def _count_tokens(self, messages: List[Dict]) -> int:
        """
        计算消息列表的总 token 数

        Args:
            messages: 消息列表

        Returns:
            总 token 数
        """
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += self.compressor.count_tokens(content)
            elif isinstance(content, list):
                # 多模态消息（文本 + 图片）
                for item in content:
                    if item.get("type") == "text":
                        text = item.get("text", "")
                        total += self.compressor.count_tokens(text)
                    # 图片 token 计算需要特殊处理，这里简化处理
                    elif item.get("type") == "image_url":
                        total += 85  # 假设每张图片约 85 tokens（Claude 3）
        return total

    def _compress_messages(
(
        self,
        messages: List[Dict],
        compress_system: bool = False
    ) -> tuple:
        """
        压缩消息列表

        Args:
            messages: 消息列表
            compress_system: 是否压缩系统消息

        Returns:
            (压缩后的消息列表, 压缩统计信息)
        """
        # 分离系统消息和其他消息
        system_messages = []
        other_messages = []

        for msg in messages:
            if msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)

        # 确定压缩目标
        if compress_system:
            # 压缩所有消息（包括系统消息）
            target_messages = messages
            compressed_messages, stats = self.compressor.compress_messages(
                target_messages,
                max_tokens=int(self.max_tokens * 0.8)  # 留 20% 余量
            )
        else:
            # 只压缩非系统消息
            compressed_other, stats = self.compressor.compress_messages(
                other_messages,
                max_tokens=int(self.max_tokens * 0.8) - self._count_tokens(system_messages)
            )
            # 重新组合
            compressed_messages = system_messages + compressed_other

        return compressed_messages, stats

    def _register_default_hooks(self):
        """注册默认钩子"""
        # 压缩前钩子：记录日志
        self.hooks.register(
            "before_context_compression",
            self._on_before_compression
        )

        # 压缩后钩子：记录日志并保存调试信息
        self.hooks.register(
            "after_context_compression",
            self._on_after_compression
        )

    def _on_before_compression(self, **kwargs):
        """压缩前默认处理"""
        current_tokens = kwargs.get("current_tokens", 0)
        threshold = kwargs.get("threshold", 0)

        self.logger.info(
            "Context compression triggered: %d tokens (threshold: %d tokens, %.1f%%)",
            current_tokens,
            int(threshold),
            current_tokens / threshold * 100
        )

    def _on_after_compression(self, **kwargs):
        """压缩后默认处理"""
        original_count = kwargs.get("original_count", 0)
        compressed_count = kwargs.get("compressed_count", 0)
        original_tokens = kwargs.get("original_tokens", 0)
        compressed_tokens = kwargs.get("compressed_tokens", 0)
        compression_ratio = kwargs.get("compression_ratio", 0)

        self.logger.info(
            "Context compressed: %d → %d messages (%.1f%%, %d → %d tokens)",
            original_count,
            compressed_count,
            compression_ratio * 100,
            original_tokens,
            compressed_tokens
        )

    def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return self.stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_checks": 0,
            "compressions_triggered": 0,
            "messages_compressed": 0,
            "tokens_saved": 0
        }
```

---

## 🔧 集成到 Agent Loop

### 修改后的 AgentLoop 类

```python
class AgentLoop:
    """
    Agent 消息循环，集成上下文监控
    """

    def __init__(self, agent, context_monitor: Optional[ContextMonitor] = None):
        self.agent = agent
        self.context_monitor = context_monitor
        self.messages: List[Dict] = []

    async def process_message(self, message: str, media: List[str] = None) -> str:
        """
        处理用户消息

        Args:
            message: 用户消息
            media: 附件（图片等）

        Returns:
            助手回复
        """
        # 构建用户消息
        user_message = {"role": "user", "content": message}
        if media:
            # 处理多模态内容
            user_message["content"] = self._build_multimodal_content(message, media)

        # 添加到消息历史
        self.messages.append(user_message)

        # 检查并压缩上下文
        if self.context_monitor:
            self.messages = self.context_monitor.check_and_compress(self.messages)

        # 调用 LLM
        response = await self.agent.generate_response(self.messages)

        # 添加助手回复
        self.messages.append({"role": "assistant", "content": response})

        return response

    def _build_multimodal_content(self, text: str, media: List[str]) -> List[Dict]:
        """
        构建多模态内容

        Args:
            text: 文本内容
            media: 媒体文件路径

        Returns:
            多模态内容列表
        """
        import base64
        import mimetypes
        from pathlib import Path

        content = []

        # 添加图片
        for path in media:
            p = Path(path)
            if not p.exists():
                continue

            mime, _ = mimetypes.guess_type(path)
            if not mime or not mime.startswith("image/"):
                continue

            # 读取并编码图片
            b64 = base64.b64encode(p.read_bytes()).decode()
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"}
            })

        #最后添加文本
        content.append({"type": "text", "text": text})

        return content
```

---

## 📊 配置选项

### 在配置文件中添加上下文监控配置

```yaml
# nanobot_config.yaml
agents:
  defaults:
    workspace: "~/.nanobot/workspace"
    model: "glm4.7"
    max_tokens: 8192
    temperature: 0.7
  main_agent:
    name: "Main Agent"
    description: "Main orchestration agent"

# 上下文管理配置
context_management:
  enabled: true  # 是否启用上下文管理

  # 窗口配置
  window:
    max_tokens: 128000  # 最大 token 数（Claude 3.5 Sonnet）
    threshold_percent: 0.6  # 触发压缩的阈值百分比

  # 压缩配置
  compression:
    enabled: true
    algorithm: "intelligent"  # 算法：intelligent, simple, aggressive
    preserve_system: true  # 是否保留系统消息
    preserve_last_n: 3  # 保留最后 N 条用户消息

  # 监控配置
  monitoring:
    enabled: true
    log_compressions: true  # 记录压缩事件
    save_compression_stats: true  # 保存压缩统计
    stats_file: "~/.nanobot/workspace/debug/compression_stats.json"

  # 缓存配置
  cache:
    enabled: true
    ttl: 300  # 缓存时间（秒）
```

---

## 🎨 钩子示例

### 示例 1：记录压缩事件到文件

```python
def log_compression_event(**kwargs):
    """记录压缩事件到文件"""
    from datetime import datetime
    import json

    event = {
        "timestamp": datetime.now().isoformat(),
        "event": "context_compression",
        "details": kwargs
    }

    # 写入日志文件
    log_file = Path.home() / ".nanobot" / "workspace" / "debug" / "compression_log.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

# 注册钩子
context_monitor.hooks.register("after_context_compression", log_compression_event)
```

### 示例 2：发送压缩通知

```python
async def notify_compression(**kwargs):
    """发送压缩通知"""
    compression_ratio = kwargs.get("compression_ratio", 0)
    original_tokens = kwargs.get("original_tokens", 0)
    compressed_tokens = kwargs.get("compressed_tokens", 0)

    message = (
        f"⚠️ Context auto-compressed\n"
        f"Original: {original_tokens:,} tokens\n"
        f"Compressed: {compressed_tokens:,} tokens\n"
        f"Ratio: {compression_ratio:.1%}"
    )

    # 通过飞书发送通知
    await send_feishu_message(message)

# 注册钩子
context_monitor.hooks.register("after_context_compression", notify_compression)
```

### 示例 3：动态调整阈值

```python
def adjust_threshold(**kwargs):
    """根据使用情况动态调整阈值"""
    original_tokens = kwargs.get("original_tokens", 0)
    max_tokens = kwargs.get("max_tokens", 128000)

    # 如果经常接近窗口上限，提高阈值
    if original_tokens / max_tokens > 0.8:
        new_threshold = 0.5  # 降低到 50%，更早触发压缩
        context_monitor.threshold = max_tokens * new_threshold
        logging.info(f"Adjusted compression threshold to {new_threshold:.0%}")

# 注册钩子
context_monitor.hooks.register("after_context_compression", adjust_threshold)
```

### 示例：在压缩时分析模式

```python
async def analyze_compression_patterns(**kwargs):
    """分析压缩模式"""
    original_count = kwargs.get("original_count", 0)
    compressed_count = kwargs.get("compressed_count", 0)

    # 计算被压缩的消息比例
    ratio = (original_count - compressed_count) / original_count if original_count > 0 else 0

    # 如果压缩比例过高，可能存在长对话
    if ratio > 0.5:
        logging.warning(
            f"High compression ratio detected: {ratio:.1%}. "
            "Consider increasing max_tokens or changing conversation strategy."
        )

# 注册钩子
context_monitor.hooks.register("after_context_compression", analyze_compression_patterns)
```

---

## 📈 监控和统计

### 获取压缩统计信息

```python
# 获取统计信息
stats = context_monitor.get_stats()
print(f"Total checks: {stats['total_checks']}")
print(f"Compressions triggered: {stats['compressions_triggered']}")
print(f"Messages compressed: {stats['messages_compressed']}")
print(f"Tokens saved: {stats['tokens_saved']}")
```

### 输出示例

```
Context Monitor Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total checks:               1,234
Compressions triggered:         89
Messages compressed:          456
Tokens saved:           1,234,567

Compression rate:             7.2% (89/1234)
Average messages/compression:  5.1
Average tokens saved:     13,871
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🎯 钩子列表

| 钩子名称 | 触发时机 | 参数 | 用途 |
|---------|---------|------|------|
| before_context_compression | 上下文压缩前 | current_tokens, max_tokens, threshold, messages_count | 记录日志、分析模式 |
| after_context_compression | 上下文压缩后 | original_count, compressed_count, original_tokens, compressed_tokens, compression_ratio | 记录统计、发送通知、动态调整 |

---

## ✅ 实施检查清单

### 核心功能
- [ ] 实现 ContextMonitor 类
- [ ] 实现 token 计数方法
- [ ] 实现消息压缩方法
- [ ] 实现阈值检查
- [ ] 集成 ContextCompressorV2

### 集成到 Agent
- [ ] 修改 AgentLoop 集成监控
- [ ] 在 process_message 中调用检查
- [ ] 支持多模态内容

### 配置支持
- [ ] 添加配置选项
- [ ] 支持启用/禁用
- [ ] 支持自定义阈值
- [ ] 支持选择压缩策略

### 钩子系统
- [ ] 实现 before_context_compression 钩子
- [ ] 实现 after_context_compression 钩子
- [ ] 注册默认钩子
- [ ] 支持自定义钩子

### 测试
- [ ] 测试阈值触发
- [ ] 测试压缩效果
- [ ] 测试多模态消息
- [ ] 测试钩子执行
- [ ] 测试统计信息

---

## 🔍 使用示例

### 示例 1：基本使用

```python
from nanobot.agent.context_compressor_v2 import ContextCompressor
from nanobot.agent.context_monitor import ContextMonitor

# 创建压缩器
compressor = ContextCompressor()

# 创建监控器（60% 阈值）
monitor = ContextMonitor(
    context_compressor=compressor,
    max_tokens=128000,
    threshold_percent=0.6
)

# 处理消息
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
    # ... 更多消息
]

# 检查并压缩
compressed_messages = monitor.check_and_compress(messages)

# 获取统计
stats = monitor.get_stats()
print(f"Compressions triggered: {stats['compressions_triggered']}")
```

### 示例 2：与 Agent Loop 集成

```python
from nanobot.agent.loop import AgentLoop
from nanobot.agent.context_monitor import ContextMonitor

# 创建上下文监控器
context_monitor = ContextMonitor(
        context_compressor=compressor,
        max_tokens=128000,
        threshold_percent=0.6
)

# 创建 Agent Loop（传入监控器）
loop = AgentLoop(
    agent=main_agent,
    context_monitor=context_monitor
)

# 处理消息（自动监控和压缩）
response = await loop.process_message("What is the weather today?")
```

### 示例 3：自定义钩子

```python
# 注册自定义钩子
def my_compression_hook(**kwargs):
    compression_ratio = kwargs.get("compression_ratio", 0)
    print(f"Compression ratio: {compression_ratio:.1%}")

context_monitor.hooks.register(
    "after_context_compression",
    my_compression_hook
)
```

---

## 📝 总结

上下文监控钩子系统提供了自动化的上下文管理：

✅ **实时监控** - 在每次添加消息后检查长度
✅ **阈值触发** - 达到 60% 时自动压缩
✅ **智能压缩** - 使用 ContextCompressorV2 进行压缩
✅ **可配置** - 支持自定义阈值和策略
✅ **钩子扩展** - 支持压缩前后钩子
✅ **统计监控** - 提供详细的压缩统计
