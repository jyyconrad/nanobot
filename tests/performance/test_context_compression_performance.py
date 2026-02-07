"""
测试上下文压缩性能
测量不同大小的对话压缩时间和压缩率
"""

import asyncio
import time

import pytest

from nanobot.agent.context_compressor import ContextCompressor


@pytest.mark.asyncio
async def test_context_compression_time():
    """测试不同大小对话的压缩时间"""
    compressor = ContextCompressor()

    # 测试小对话
    small_conversation = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！我是 Nanobot，有什么可以帮助你的吗？"},
    ]

    start_time = time.time()
    compressed, stats = await compressor.compress_messages(small_conversation)
    small_time = time.time() - start_time
    assert small_time < 0.1  # 小对话压缩应在 0.1 秒内

    # 测试中等对话
    medium_conversation = []
    for i in range(20):
        medium_conversation.append({"role": "user", "content": f"问题 {i}"})
        medium_conversation.append({"role": "assistant", "content": f"回答 {i}"})

    start_time = time.time()
    compressed, stats = await compressor.compress_messages(medium_conversation)
    medium_time = time.time() - start_time
    assert medium_time < 0.5  # 中等对话压缩应在 0.5 秒内

    # 测试大对话
    large_conversation = []
    for i in range(100):
        large_conversation.append({"role": "user", "content": f"问题 {i}"})
        large_conversation.append({"role": "assistant", "content": f"回答 {i}"})

    start_time = time.time()
    compressed, stats = await compressor.compress_messages(large_conversation)
    large_time = time.time() - start_time
    assert large_time < 2.0  # 大对话压缩应在 2 秒内

    print("压缩时间测试通过:")
    print(f"  小对话: {small_time:.3f} 秒")
    print(f"  中等对话: {medium_time:.3f} 秒")
    print(f"  大对话: {large_time:.3f} 秒")


@pytest.mark.asyncio
async def test_context_compression_ratio():
    """测试对话压缩率"""
    compressor = ContextCompressor()

    conversation = []
    for i in range(50):
        conversation.append({"role": "user", "content": f"问题 {i}"})
        conversation.append({"role": "assistant", "content": f"回答 {i}"})

    # 计算原始对话长度
    original_length = sum(len(msg["content"]) for msg in conversation)

    # 压缩对话
    compressed, stats = await compressor.compress_messages(conversation)

    # 计算压缩后长度
    compressed_length = sum(len(msg["content"]) for msg in compressed)

    # 计算压缩率
    compression_ratio = 1 - (compressed_length / original_length)

    print("压缩率测试通过:")
    print(f"  原始长度: {original_length} 字符")
    print(f"  压缩后长度: {compressed_length} 字符")
    print(f"  压缩率: {compression_ratio:.2%}")

    assert compression_ratio > 0.3  # 压缩率应至少 30%


if __name__ == "__main__":
    asyncio.run(test_context_compression_time())
    asyncio.run(test_context_compression_ratio())
    print("所有性能测试通过！")
