"""
CancellationDetector 单元测试
"""

import pytest

from nanobot.agent.planner.cancellation_detector import CancellationDetector


class TestCancellationDetector:
    """CancellationDetector 测试类"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """测试 CancellationDetector 初始化"""
        detector = CancellationDetector()
        assert detector is not None
        assert len(detector.cancellation_patterns) == 4
        assert len(detector.confirmation_patterns) == 4

    @pytest.mark.asyncio
    async def test_is_cancellation_explicit(self):
        """测试明确取消指令检测"""
        detector = CancellationDetector()
        test_cases = ["取消当前任务", "停止执行操作", "终止任务", "放弃当前操作"]

        for input_text in test_cases:
            assert await detector.is_cancellation(input_text) is True

    @pytest.mark.asyncio
    async def test_is_cancellation_confirmation(self):
        """测试取消确认检测"""
        detector = CancellationDetector()
        test_cases = [
            "确定取消任务",
            "确认取消操作",
            "是否取消当前任务",
            "真的要取消吗",
        ]

        for input_text in test_cases:
            assert await detector.is_cancellation(input_text) is True

    @pytest.mark.asyncio
    async def test_is_cancellation_implied(self):
        """测试隐含取消指令检测"""
        detector = CancellationDetector()
        test_cases = ["我不想继续了", "不要继续执行了", "不必再运行了", "不需要继续了"]

        for input_text in test_cases:
            assert await detector.is_cancellation(input_text) is True

    @pytest.mark.asyncio
    async def test_is_cancellation_error(self):
        """测试错误相关取消指令检测"""
        detector = CancellationDetector()
        test_cases = [
            "程序出错了，停止执行",
            "操作失败了，取消任务",
            "有问题，终止操作",
            "代码有错误，停止运行",
        ]

        for input_text in test_cases:
            assert await detector.is_cancellation(input_text) is True

    @pytest.mark.asyncio
    async def test_is_not_cancellation(self):
        """测试非取消指令检测"""
        detector = CancellationDetector()
        test_cases = ["继续执行任务", "请继续操作", "我想继续", "任务完成了吗"]

        for input_text in test_cases:
            assert await detector.is_cancellation(input_text) is False

    @pytest.mark.asyncio
    async def test_get_reason(self):
        """测试取消原因提取"""
        detector = CancellationDetector()

        input_text = "因为程序出错，取消任务"
        reason = await detector.get_reason(input_text)
        assert "程序" in reason

        input_text = "由于网络问题，停止操作"
        reason = await detector.get_reason(input_text)
        assert "网络" in reason

        input_text = "取消任务，因为超时了"
        reason = await detector.get_reason(input_text)
        assert "超时" in reason

    @pytest.mark.asyncio
    async def test_get_reason_default(self):
        """测试默认取消原因"""
        detector = CancellationDetector()

        input_text = "取消任务"
        reason = await detector.get_reason(input_text)
        assert reason == "用户主动取消"

    @pytest.mark.asyncio
    async def test_is_confirmation(self):
        """测试取消确认检测"""
        detector = CancellationDetector()

        assert await detector.is_confirmation("确定取消任务") is True
        assert await detector.is_confirmation("取消任务") is False

    @pytest.mark.asyncio
    async def test_get_confidence(self):
        """测试置信度计算"""
        detector = CancellationDetector()

        # 高置信度
        high_input = "确定取消任务"
        high_confidence = await detector.get_confidence(high_input)
        assert high_confidence > 0.9

        # 中等置信度
        medium_input = "取消任务"
        medium_confidence = await detector.get_confidence(medium_input)
        assert 0.7 < medium_confidence < 0.9

        # 低置信度
        low_input = "我不想继续了"
        low_confidence = await detector.get_confidence(low_input)
        assert 0.5 < low_confidence < 0.7

    @pytest.mark.asyncio
    async def test_needs_confirmation(self):
        """测试是否需要确认"""
        detector = CancellationDetector()

        # 需要确认
        assert await detector.needs_confirmation("我不想继续了") is True
        assert await detector.needs_confirmation("不要继续了") is True

        # 不需要确认
        assert await detector.needs_confirmation("取消任务") is False
        assert await detector.needs_confirmation("确定取消任务") is False
        assert await detector.needs_confirmation("停止操作") is False

    @pytest.mark.asyncio
    async def test_get_cancellation_type(self):
        """测试取消类型获取"""
        detector = CancellationDetector()

        assert await detector.get_cancellation_type("取消任务") == "explicit"
        assert await detector.get_cancellation_type("确定取消任务") == "confirmation"
        assert await detector.get_cancellation_type("继续执行") is None

    @pytest.mark.asyncio
    async def test_extract_cancellation_target(self):
        """测试取消目标提取"""
        detector = CancellationDetector()

        # 测试包含目标的取消
        input_text = "取消当前任务"
        target = await detector.extract_cancellation_target(input_text)
        assert target == "当前"

        input_text = "停止执行操作"
        target = await detector.extract_cancellation_target(input_text)
        assert target == "执行"

        input_text = "终止这个任务"
        target = await detector.extract_cancellation_target(input_text)
        assert target == "这个"

    @pytest.mark.asyncio
    async def test_no_cancellation_target(self):
        """测试无取消目标的情况"""
        detector = CancellationDetector()

        input_text = "取消任务"
        target = await detector.extract_cancellation_target(input_text)
        assert target is None

        input_text = "停止操作"
        target = await detector.extract_cancellation_target(input_text)
        assert target is None

    @pytest.mark.asyncio
    async def test_cancellation_with_reason(self):
        """测试包含原因的取消"""
        detector = CancellationDetector()

        input_text = "程序出错了，取消任务"
        assert await detector.is_cancellation(input_text) is True
        reason = await detector.get_reason(input_text)
        assert "程序" in reason

        input_text = "因为网络问题，停止操作"
        assert await detector.is_cancellation(input_text) is True
        reason = await detector.get_reason(input_text)
        assert "网络" in reason

    @pytest.mark.asyncio
    async def test_confidence_comparison(self):
        """测试置信度比较"""
        detector = CancellationDetector()

        # 确认模式置信度最高
        confirmation_input = "确定取消任务"
        confirmation_confidence = await detector.get_confidence(confirmation_input)

        # 明确取消模式次之
        explicit_input = "取消任务"
        explicit_confidence = await detector.get_confidence(explicit_input)

        # 隐含取消模式最低
        implied_input = "我不想继续了"
        implied_confidence = await detector.get_confidence(implied_input)

        assert confirmation_confidence > explicit_confidence > implied_confidence
