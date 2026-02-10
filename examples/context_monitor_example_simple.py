#!/usr/bin/env python3
"""
ContextMonitor 使用示例 - 简化版

这个示例展示了 ContextMonitor 的基本功能
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


async def simple_example():
    """简单示例"""
    logger.info("=== ContextMonitor 简单示例 ===")

    # 创建 ContextMonitor 实例
    config = ContextMonitorConfig(
        model=ModelType.GPT_3_5_TURBO.value,
        threshold=0.5,  # 50% 阈值
        max_tokens=200,  # 小窗口以便快速测试
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
        {"role": "user", "content": "Can you tell me about Python programming?"},
        {"role": "assistant", "content": "Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms, including procedural, object-oriented, and functional programming."}
    ]

    for msg in messages:
        logger.info(f"添加消息: {msg['role']}")
        monitor.add_message(msg)

    # 打印当前统计信息
    stats = monitor.get_stats()
    logger.info(f"当前统计信息:")
    logger.info(f"  消息数: {stats['total_messages']}")
    logger.info(f"  Token数: {stats['total_tokens']}")
    logger.info(f"  阈值: {stats['threshold_tokens']}")
    logger.info(f"  是否超过阈值: {stats['is_over_threshold']}")

    # 检查是否需要压缩
    if monitor.check_threshold():
        logger.warning("上下文大小超过阈值，正在压缩...")
        compressed = await monitor.compress_context()
        logger.info(f"压缩后:")
        logger.info(f"  消息数: {len(compressed)}")
        logger.info(f"  Token数: {monitor.token_count(compressed)}")

    logger.info("=== 示例完成 ===")


async def main():
    """主函数"""
    await simple_example()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序错误: {e}")
