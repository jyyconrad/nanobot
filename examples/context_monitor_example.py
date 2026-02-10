#!/usr/bin/env python3
"""
ContextMonitor 使用示例

这个示例展示了如何使用 ContextMonitor 类来管理和监控对话上下文的token数量。
"""

import asyncio
import logging
from nanobot.agent.context_monitor import ContextMonitor, ContextMonitorConfig, ModelType


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def basic_usage_example():
    """基础使用示例"""
    logger.info("=== ContextMonitor 基础使用示例 ===")

    # 创建 ContextMonitor 实例
    config = ContextMonitorConfig(
        model=ModelType.GPT_3_5_TURBO.value,
        threshold=0.5,  # 降低阈值以便快速测试
        max_tokens=200,
        compression_strategy="truncation"
    )
    monitor = ContextMonitor(config)

    # 打印配置信息
    logger.info(f"模型: {monitor.config.model}")
    logger.info(f"上下文窗口大小: {monitor.max_context_tokens}")
    logger.info(f"压缩阈值: {monitor.config.threshold:.0%}")

    # 添加消息
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm fine, thank you! How can I help you?"},
        {"role": "user", "content": "Can you tell me about artificial intelligence?"},
        {"role": "assistant", "content": "Artificial Intelligence (AI) is a branch of computer science that deals with creating intelligent machines that can perform tasks that would typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, language understanding, and decision-making. AI technologies range from basic rule-based systems to advanced machine learning and deep learning models."}
    ]

    for msg in messages:
        logger.info(f"添加消息: {msg['role']} - {str(msg['content'])[:50]}...")
        monitor.add_message(msg)

    # 打印当前统计信息
    stats = monitor.get_stats()
    logger.info(f"当前统计信息: {stats}")

    # 检查是否需要压缩
    if monitor.check_threshold():
        logger.warning("上下文大小超过阈值，需要压缩")
        compressed = await monitor.compress_context()
        logger.info(f"压缩后消息数量: {len(compressed)}")
        logger.info(f"压缩后 token 数量: {monitor.token_count(compressed)}")

    logger.info("=== 示例完成 ===")


async def multimodal_example():
    """多模态消息支持示例"""
    logger.info("\n=== 多模态消息支持示例 ===")

    config = ContextMonitorConfig(
        model=ModelType.GPT_4.value,
        threshold=0.8
    )
    monitor = ContextMonitor(config)

    # 添加包含图像的多模态消息
    multimodal_msg = {
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc123"}}
        ]
    }

    monitor.add_message(multimodal_msg)

    # 计数
    token_count = monitor.token_count()
    logger.info(f"多模态消息 token 计数: {token_count}")


async def compression_strategy_example():
    """压缩策略示例"""
    logger.info("\n=== 压缩策略示例 ===")

    # 使用智能压缩策略
    config = ContextMonitorConfig(
        model=ModelType.GPT_4_TURBO.value,
        threshold=0.6,
        compression_strategy="intelligent"
    )
    monitor = ContextMonitor(config)

    # 添加大量消息
    for i in range(10):
        monitor.add_message({
            "role": "user",
            "content": f"这是第 {i+1} 条测试消息，用来测试上下文压缩功能。这条消息会很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长。"
        })
        monitor.add_message({
            "role": "assistant",
            "content": f"这是对第 {i+1} 条测试消息的回复。回复内容也很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长很长。"
        })

    # 打印统计信息
    stats = monitor.get_stats()
    logger.info(f"压缩前: 消息数={stats['total_messages']}, token数={stats['total_tokens']}")

    # 压缩
    compressed = await monitor.compress_context()
    logger.info(f"压缩后: 消息数={len(compressed)}, token数={monitor.token_count(compressed)}")

    # 打印压缩事件
    events = monitor.get_compression_events()
    logger.info(f"压缩事件数: {len(events)}")
    if events:
        event = events[0]
        logger.info(f"压缩率: {event.compression_ratio:.1%}")


async def main():
    """主函数"""
    await basic_usage_example()
    await multimodal_example()
    await compression_strategy_example()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序错误: {e}")
