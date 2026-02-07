"""
TaskDetector 单元测试
"""

import pytest

from nanobot.agent.planner.models import TaskType
from nanobot.agent.planner.task_detector import TaskDetector


class TestTaskDetector:
    """TaskDetector 测试类"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """测试 TaskDetector 初始化"""
        detector = TaskDetector()
        assert detector is not None
        assert len(detector.patterns) == 6

    @pytest.mark.asyncio
    async def test_detect_task_type_code_generation(self):
        """测试代码生成任务检测"""
        detector = TaskDetector()
        test_cases = [
            "编写一个Python函数",
            "实现一个计算器程序",
            "修复这个bug",
            "重构代码以提高性能",
        ]

        for input_text in test_cases:
            task_type = await detector.detect_task_type(input_text)
            assert task_type == TaskType.CODE_GENERATION

    @pytest.mark.asyncio
    async def test_detect_task_type_text_summarization(self):
        """测试文本摘要任务检测"""
        detector = TaskDetector()
        test_cases = ["总结这篇文章", "概括主要内容", "提取关键要点", "简述这篇报告"]

        for input_text in test_cases:
            task_type = await detector.detect_task_type(input_text)
            assert task_type == TaskType.TEXT_SUMMARIZATION

    @pytest.mark.asyncio
    async def test_detect_task_type_data_analysis(self):
        """测试数据分析任务检测"""
        detector = TaskDetector()
        test_cases = ["分析销售数据", "统计用户行为", "处理实验数据", "可视化分析结果"]

        for input_text in test_cases:
            task_type = await detector.detect_task_type(input_text)
            assert task_type == TaskType.DATA_ANALYSIS

    @pytest.mark.asyncio
    async def test_detect_task_type_web_search(self):
        """测试网络搜索任务检测"""
        detector = TaskDetector()
        test_cases = ["搜索最新新闻", "查找相关信息", "查询天气情况", "研究这个主题"]

        for input_text in test_cases:
            task_type = await detector.detect_task_type(input_text)
            assert task_type == TaskType.WEB_SEARCH

    @pytest.mark.asyncio
    async def test_detect_task_type_file_operation(self):
        """测试文件操作任务检测"""
        detector = TaskDetector()
        test_cases = ["创建一个新文件", "删除这个文件", "修改文件内容", "读取文件数据"]

        for input_text in test_cases:
            task_type = await detector.detect_task_type(input_text)
            assert task_type == TaskType.FILE_OPERATION

    @pytest.mark.asyncio
    async def test_detect_task_type_system_command(self):
        """测试系统命令任务检测"""
        detector = TaskDetector()
        test_cases = ["运行系统命令", "执行脚本", "安装软件", "配置环境"]

        for input_text in test_cases:
            task_type = await detector.detect_task_type(input_text)
            assert task_type == TaskType.SYSTEM_COMMAND

    @pytest.mark.asyncio
    async def test_detect_task_type_other(self):
        """测试其他类型任务检测"""
        detector = TaskDetector()
        test_cases = ["你好", "今天天气怎么样？", "再见"]

        for input_text in test_cases:
            task_type = await detector.detect_task_type(input_text)
            assert task_type == TaskType.OTHER

    @pytest.mark.asyncio
    async def test_detect_task_type_detailed(self):
        """测试详细任务检测结果"""
        detector = TaskDetector()
        input_text = "编写一个Python函数"

        result = await detector.detect_task_type_detailed(input_text)
        assert result.task_type == TaskType.CODE_GENERATION
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.matched_patterns) > 0

    @pytest.mark.asyncio
    async def test_is_task_type(self):
        """测试任务类型判断"""
        detector = TaskDetector()

        assert await detector.is_task_type("编写代码", TaskType.CODE_GENERATION) is True
        assert await detector.is_task_type("总结文章", TaskType.TEXT_SUMMARIZATION) is True
        assert await detector.is_task_type("搜索信息", TaskType.WEB_SEARCH) is True
        assert await detector.is_task_type("编写代码", TaskType.TEXT_SUMMARIZATION) is False

    @pytest.mark.asyncio
    async def test_get_confidence(self):
        """测试置信度获取"""
        detector = TaskDetector()

        # 高置信度
        high_confidence_input = "编写一个Python函数"
        high_confidence = await detector.get_confidence(
            high_confidence_input, TaskType.CODE_GENERATION
        )
        assert high_confidence > 0.7

        # 低置信度
        low_confidence_input = "你好"
        low_confidence = await detector.get_confidence(
            low_confidence_input, TaskType.CODE_GENERATION
        )
        assert low_confidence < 0.3

    @pytest.mark.asyncio
    async def test_has_multiple_matches(self):
        """测试多个匹配判断"""
        detector = TaskDetector()

        # 单个匹配
        single_match_input = "编写代码"
        assert await detector.has_multiple_matches(single_match_input) is False

        # 多个匹配
        multiple_match_input = "编写代码并总结结果"
        assert await detector.has_multiple_matches(multiple_match_input) is True

    @pytest.mark.asyncio
    async def test_get_top_task_types(self):
        """测试获取排名前 N 的任务类型"""
        detector = TaskDetector()

        input_text = "编写代码并分析数据"
        top_types = await detector.get_top_task_types(input_text, 2)

        assert len(top_types) == 2
        assert top_types[0]["task_type"] in [TaskType.CODE_GENERATION, TaskType.DATA_ANALYSIS]
        assert top_types[1]["task_type"] in [TaskType.CODE_GENERATION, TaskType.DATA_ANALYSIS]
        assert top_types[0]["confidence"] > top_types[1]["confidence"]

    @pytest.mark.asyncio
    async def test_confidence_threshold(self):
        """测试置信度阈值"""
        detector = TaskDetector()

        # 高置信度
        high_input = "编写一个Python函数来计算斐波那契数列"
        result = await detector.detect_task_type_detailed(high_input)
        assert result.confidence > 0.8

        # 中等置信度
        medium_input = "编写函数和分析数据"
        result = await detector.detect_task_type_detailed(medium_input)
        assert 0.5 < result.confidence < 0.8

        # 低置信度
        low_input = "做一些不太清楚的事情"
        result = await detector.detect_task_type_detailed(low_input)
        assert result.confidence < 0.5
