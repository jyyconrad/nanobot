"""
ContextCompressor 单元测试 - 测试上下文压缩功能

测试 ContextCompressor 的核心功能：
- 上下文压缩
- 消息总结
- 压缩统计
- 边界条件和错误处理
"""

import pytest

from nanobot.agent.context_compressor import ContextCompressor


class TestContextCompressor:
    """ContextCompressor 单元测试类"""

    @pytest.fixture
    def compressor(self):
        """创建 ContextCompressor 实例"""
        return ContextCompressor()

    @pytest.mark.asyncio
    async def test_compress_short_content(self, compressor):
        """测试压缩短内容（不应压缩）"""
        short_content = "这是一个简短的测试内容"
        compressed, stats = await compressor.compress(short_content)

        assert compressed == short_content
        assert stats.compression_ratio == 1.0
        assert stats.original_length == stats.compressed_length

    @pytest.mark.asyncio
    async def test_compress_long_content(self, compressor):
        """测试压缩长内容"""
        long_content = "测试 " * 10000  # 增大内容长度
        compressed, stats = await compressor.compress(long_content, max_tokens=2000)  # 降低限制

        assert len(compressed) < len(long_content)
        assert stats.compression_ratio < 1.0
        assert stats.original_length > stats.compressed_length

    @pytest.mark.asyncio
    async def test_summarize_messages(self, compressor):
        """测试消息总结功能"""
        messages = [
            {"role": "user", "content": "我需要你帮我修复一个代码错误"},
            {"role": "assistant", "content": "我会帮你分析和修复代码错误"},
            {"role": "user", "content": "代码位于 nanobot/agent/context.py 文件中"},
            {"role": "assistant", "content": "我来检查这个文件"},
            {"role": "user", "content": "错误是在处理长上下文时发生的"},
            {"role": "assistant", "content": "我找到了问题所在，需要优化压缩算法"},
        ]

        summary = await compressor.summarize_messages(messages)

        assert len(summary) < sum(len(msg["content"]) for msg in messages)
        assert any(keyword in summary for keyword in ["代码错误", "压缩算法"])

    @pytest.mark.asyncio
    async def test_summarize_empty_messages(self, compressor):
        """测试总结空消息列表"""
        summary = await compressor.summarize_messages([])
        assert summary == ""

    @pytest.mark.asyncio
    async def test_compress_messages(self, compressor):
        """测试压缩消息列表"""
        # 创建一个非常长的消息列表
        messages = []
        for i in range(10):
            messages.append({"role": "user", "content": f"这是一个非常长的测试消息{i}，" * 20})
            messages.append({"role": "assistant", "content": f"这是一个非常长的回复消息{i}，" * 20})

        compressed_messages, stats = await compressor.compress_messages(messages)

        assert len(compressed_messages) <= len(messages)
        assert stats.compression_ratio < 1.0

    @pytest.mark.asyncio
    async def test_compress_messages_with_system(self, compressor):
        """测试包含系统消息的压缩"""
        messages = [
            {"role": "system", "content": "系统初始化"},
            {"role": "user", "content": "我需要你帮我修复一个代码错误"},
            {"role": "assistant", "content": "我会帮你分析和修复代码错误"},
        ]

        compressed_messages, stats = await compressor.compress_messages(messages)

        # 验证系统消息被保留
        assert any(msg["role"] == "system" for msg in compressed_messages)

    @pytest.mark.asyncio
    async def test_compress_with_custom_token_limit(self, compressor):
        """测试自定义令牌限制的压缩"""
        long_content = "测试 " * 1000
        compressed, stats = await compressor.compress(long_content, max_tokens=100)

        assert len(compressed) < len(long_content)
        assert stats.compression_ratio < 0.5  # 应该压缩到很小

    @pytest.mark.asyncio
    async def test_compress_with_zero_length_content(self, compressor):
        """测试压缩空内容"""
        compressed, stats = await compressor.compress("")
        assert compressed == ""
        assert stats.original_length == 0
        assert stats.compressed_length == 0
        assert stats.compression_ratio == 1.0

    @pytest.mark.asyncio
    async def test_summary_includes_task_keywords(self, compressor):
        """测试总结包含任务关键词"""
        messages = [
            {"role": "user", "content": "我需要你帮我完成一个编码任务"},
            {"role": "assistant", "content": "我会帮你完成这个任务"},
            {"role": "user", "content": "任务要求编写一个 ContextManager 类"},
            {"role": "assistant", "content": "我来帮你编写这个类"},
        ]

        summary = await compressor.summarize_messages(messages)

        assert "任务" in summary
        assert "编码" in summary or "编写" in summary

    @pytest.mark.asyncio
    async def test_summary_includes_decisions(self, compressor):
        """测试总结包含决定"""
        messages = [
            {"role": "user", "content": "我需要你帮我做个决定"},
            {"role": "assistant", "content": "我会帮你分析选项"},
            {"role": "user", "content": "我应该使用 Python 还是 JavaScript？"},
            {"role": "assistant", "content": "我建议使用 Python，因为它更适合这个任务"},
        ]

        summary = await compressor.summarize_messages(messages)

        assert "决定" in summary
        assert any(lang in summary for lang in ["Python", "JavaScript"])

    @pytest.mark.asyncio
    async def test_summary_includes_results(self, compressor):
        """测试总结包含结果"""
        messages = [
            {"role": "user", "content": "任务完成了吗？"},
            {"role": "assistant", "content": "任务已经成功完成"},
            {"role": "user", "content": "结果是什么？"},
            {"role": "assistant", "content": "我们成功优化了代码性能，提升了 30%"},
        ]

        summary = await compressor.summarize_messages(messages)

        assert "完成" in summary
        assert "30%" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
