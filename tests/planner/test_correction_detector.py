"""
CorrectionDetector 单元测试
"""

import pytest

from nanobot.agent.planner.correction_detector import CorrectionDetector


class TestCorrectionDetector:
    """CorrectionDetector 测试类"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """测试 CorrectionDetector 初始化"""
        detector = CorrectionDetector()
        assert detector is not None
        assert len(detector.correction_patterns) == 6
        assert len(detector.negation_patterns) == 5

    @pytest.mark.asyncio
    async def test_detect_correction_change(self):
        """测试修改类型修正检测"""
        detector = CorrectionDetector()
        test_cases = ["修改代码中的错误", "变更文件内容", "更改输入参数", "调整算法参数"]

        for input_text in test_cases:
            correction = await detector.detect_correction(input_text)
            assert correction is not None
            assert correction.type == "change"
            assert len(correction.content) > 0
            assert 0.0 <= correction.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_detect_correction_add(self):
        """测试添加类型修正检测"""
        detector = CorrectionDetector()
        test_cases = ["添加新功能", "增加输入验证", "补充文档说明", "新增测试用例"]

        for input_text in test_cases:
            correction = await detector.detect_correction(input_text)
            assert correction is not None
            assert correction.type == "add"
            assert len(correction.content) > 0
            assert 0.0 <= correction.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_detect_correction_remove(self):
        """测试删除类型修正检测"""
        detector = CorrectionDetector()
        test_cases = ["删除不必要的代码", "移除多余的文件", "去掉无效的配置", "取消过时的功能"]

        for input_text in test_cases:
            correction = await detector.detect_correction(input_text)
            assert correction is not None
            assert correction.type == "remove"
            assert len(correction.content) > 0
            assert 0.0 <= correction.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_detect_correction_fix(self):
        """测试修复类型修正检测"""
        detector = CorrectionDetector()
        test_cases = ["修复代码中的错误", "修正计算错误", "改错语法问题", "修复运行时异常"]

        for input_text in test_cases:
            correction = await detector.detect_correction(input_text)
            assert correction is not None
            assert correction.type == "fix"
            assert len(correction.content) > 0
            assert 0.0 <= correction.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_detect_correction_improve(self):
        """测试优化类型修正检测"""
        detector = CorrectionDetector()
        test_cases = ["优化算法性能", "改进用户体验", "提升代码可读性", "完善错误处理"]

        for input_text in test_cases:
            correction = await detector.detect_correction(input_text)
            assert correction is not None
            assert correction.type == "improve"
            assert len(correction.content) > 0
            assert 0.0 <= correction.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_detect_correction_clarify(self):
        """测试澄清类型修正检测"""
        detector = CorrectionDetector()
        test_cases = ["澄清需求说明", "说明参数用途", "解释功能说明", "明确设计思路"]

        for input_text in test_cases:
            correction = await detector.detect_correction(input_text)
            assert correction is not None
            assert correction.type == "clarify"
            assert len(correction.content) > 0
            assert 0.0 <= correction.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_detect_correction_negation(self):
        """测试否定句检测"""
        detector = CorrectionDetector()
        test_cases = ["不是修改代码", "不要变更文件", "不必删除功能", "不需要添加内容"]

        for input_text in test_cases:
            correction = await detector.detect_correction(input_text)
            assert correction is None

    @pytest.mark.asyncio
    async def test_is_correction(self):
        """测试是否是修正指令"""
        detector = CorrectionDetector()

        assert await detector.is_correction("修改代码") is True
        assert await detector.is_correction("总结文章") is False
        assert await detector.is_correction("你好") is False

    @pytest.mark.asyncio
    async def test_get_correction_type(self):
        """测试修正类型获取"""
        detector = CorrectionDetector()

        assert await detector.get_correction_type("修改代码") == "change"
        assert await detector.get_correction_type("添加功能") == "add"
        assert await detector.get_correction_type("删除文件") == "remove"
        assert await detector.get_correction_type("总结文章") is None

    @pytest.mark.asyncio
    async def test_get_correction_target(self):
        """测试修正目标提取"""
        detector = CorrectionDetector()

        # 测试包含目标的修正
        input_text = "对代码进行修改"
        correction = await detector.detect_correction(input_text)
        assert correction.target == "代码"

        input_text = "针对文档的修改"
        correction = await detector.detect_correction(input_text)
        assert correction.target == "文档"

    @pytest.mark.asyncio
    async def test_detect_correction_from_context(self):
        """测试从上下文检测修正"""
        detector = CorrectionDetector()

        context = {"last_task": {"description": "编写Python函数"}}
        correction = await detector.detect_correction("修改这个函数", context)
        assert correction is not None
        assert correction.type == "adjust"
        assert correction.target == "编写Python函数"
        assert 0.0 <= correction.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_no_correction_without_context(self):
        """测试无上下文时的修正检测"""
        detector = CorrectionDetector()

        correction = await detector.detect_correction("修改这个函数")
        assert correction is None

    @pytest.mark.asyncio
    async def test_related_to_last_task(self):
        """测试与上一个任务的相关性"""
        detector = CorrectionDetector()

        context = {"last_task": {"description": "编写Python函数"}}
        correction = await detector.detect_correction("修改代码", context)
        assert correction is not None

        unrelated_context = {"last_task": {"description": "搜索天气"}}
        correction = await detector.detect_correction("修改代码", unrelated_context)
        assert correction is None

    @pytest.mark.asyncio
    async def test_confidence_levels(self):
        """测试置信度水平"""
        detector = CorrectionDetector()

        # 高置信度
        high_input = "修改代码中的错误"
        high_correction = await detector.detect_correction(high_input)
        assert high_correction.confidence > 0.8

        # 中等置信度
        medium_input = "调整这个参数"
        medium_correction = await detector.detect_correction(medium_input)
        assert 0.5 < medium_correction.confidence < 0.8

        # 低置信度（来自上下文）
        context = {"last_task": {"description": "编写Python函数"}}
        low_input = "修改这个函数"
        low_correction = await detector.detect_correction(low_input, context)
        assert 0.5 < low_correction.confidence < 0.8
