"""
ComplexityAnalyzer 单元测试
"""

import pytest
import asyncio
from nanobot.agent.planner.complexity_analyzer import ComplexityAnalyzer
from nanobot.agent.planner.task_planner import TaskType


class TestComplexityAnalyzer:
    """ComplexityAnalyzer 测试类"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """测试 ComplexityAnalyzer 初始化"""
        analyzer = ComplexityAnalyzer()
        assert analyzer is not None
        assert len(analyzer.type_weights) == 7
        assert len(analyzer.text_features) == 5
        assert len(analyzer.domain_terms) == 6

    @pytest.mark.asyncio
    async def test_analyze_complexity_code_generation(self):
        """测试代码生成任务复杂度分析"""
        analyzer = ComplexityAnalyzer()
        user_input = "编写一个Python函数来计算斐波那契数列，包括递归和迭代两种实现方式"
        task_type = TaskType.CODE_GENERATION

        complexity = await analyzer.analyze_complexity(user_input, task_type)
        assert 0.0 <= complexity <= 1.0
        assert complexity > 0.5

    @pytest.mark.asyncio
    async def test_analyze_complexity_text_summarization(self):
        """测试文本摘要任务复杂度分析"""
        analyzer = ComplexityAnalyzer()
        user_input = "总结这篇关于人工智能的文章"
        task_type = TaskType.TEXT_SUMMARIZATION

        complexity = await analyzer.analyze_complexity(user_input, task_type)
        assert 0.0 <= complexity <= 1.0
        assert complexity > 0.3

    @pytest.mark.asyncio
    async def test_analyze_complexity_data_analysis(self):
        """测试数据分析任务复杂度分析"""
        analyzer = ComplexityAnalyzer()
        user_input = "分析销售数据并生成图表"
        task_type = TaskType.DATA_ANALYSIS

        complexity = await analyzer.analyze_complexity(user_input, task_type)
        assert 0.0 <= complexity <= 1.0
        assert complexity > 0.4

    @pytest.mark.asyncio
    async def test_analyze_complexity_web_search(self):
        """测试网络搜索任务复杂度分析"""
        analyzer = ComplexityAnalyzer()
        user_input = "搜索最新的人工智能技术趋势"
        task_type = TaskType.WEB_SEARCH

        complexity = await analyzer.analyze_complexity(user_input, task_type)
        assert 0.0 <= complexity <= 1.0
        assert complexity > 0.2

    @pytest.mark.asyncio
    async def test_analyze_detailed(self):
        """测试详细复杂度分析"""
        analyzer = ComplexityAnalyzer()
        user_input = "编写一个Python函数来计算斐波那契数列"
        task_type = TaskType.CODE_GENERATION

        result = await analyzer.analyze_detailed(user_input, task_type)
        assert hasattr(result, "total_score")
        assert hasattr(result, "features")
        assert hasattr(result, "explanation")
        assert 0.0 <= result.total_score <= 1.0
        assert len(result.features) == 5
        assert len(result.explanation) > 0

    @pytest.mark.asyncio
    async def test_is_complex(self):
        """测试复杂任务判断"""
        analyzer = ComplexityAnalyzer()
        user_input = "实现一个高性能的图像识别系统，包含数据预处理、特征提取、模型训练和评估，支持多种深度学习框架和算法，具有实时处理能力，能够处理各种图像格式和分辨率，具有高准确率和低延迟，支持批量处理和实时推理，具有可扩展性和可维护性，支持多语言识别和多场景应用，支持图像增强和预处理功能，支持模型量化和优化，支持多GPU并行训练和推理加速，支持边缘设备部署和离线推理，支持图像分割和目标检测功能"
        task_type = TaskType.CODE_GENERATION

        assert await analyzer.is_complex(user_input, task_type, 0.6) is True

        simple_input = "计算两个数的和"
        assert await analyzer.is_complex(simple_input, task_type, 0.6) is False

    @pytest.mark.asyncio
    async def test_get_complexity_category(self):
        """测试复杂度类别获取"""
        analyzer = ComplexityAnalyzer()
        user_input = "实现一个高性能的图像识别系统，包含数据预处理、特征提取、模型训练和评估"
        task_type = TaskType.CODE_GENERATION

        category = await analyzer.get_complexity_category(user_input, task_type)
        assert category in ["非常复杂", "复杂", "中等", "简单", "非常简单"]

        simple_input = "计算两个数的和"
        simple_category = await analyzer.get_complexity_category(simple_input, task_type)
        assert simple_category in ["简单", "非常简单", "中等"]

    @pytest.mark.asyncio
    async def test_complexity_comparison(self):
        """测试复杂度比较"""
        analyzer = ComplexityAnalyzer()

        # 简单任务
        simple_input = "计算两个数的和"
        simple_complexity = await analyzer.analyze_complexity(simple_input, TaskType.CODE_GENERATION)

        # 中等复杂任务
        medium_input = "编写一个Python函数来计算斐波那契数列"
        medium_complexity = await analyzer.analyze_complexity(medium_input, TaskType.CODE_GENERATION)

        # 复杂任务
        complex_input = "实现一个高性能的图像识别系统，包含数据预处理、特征提取、模型训练和评估"
        complex_complexity = await analyzer.analyze_complexity(complex_input, TaskType.CODE_GENERATION)

        assert simple_complexity < medium_complexity < complex_complexity

    @pytest.mark.asyncio
    async def test_length_feature(self):
        """测试文本长度特征对复杂度的影响"""
        analyzer = ComplexityAnalyzer()
        short_input = "编写一个函数"
        long_input = "编写一个复杂的Python函数，实现数据分析功能，包括数据加载、预处理、特征工程、模型训练和评估，支持多种数据格式和模型算法，具有良好的错误处理和性能优化"

        short_complexity = await analyzer.analyze_complexity(short_input, TaskType.CODE_GENERATION)
        long_complexity = await analyzer.analyze_complexity(long_input, TaskType.CODE_GENERATION)

        assert short_complexity < long_complexity

    @pytest.mark.asyncio
    async def test_domain_terms_feature(self):
        """测试领域术语特征对复杂度的影响"""
        analyzer = ComplexityAnalyzer()
        basic_input = "编写一个函数"
        domain_input = "实现一个机器学习模型，包含特征提取、模型训练、模型评估和结果可视化"

        basic_complexity = await analyzer.analyze_complexity(basic_input, TaskType.DATA_ANALYSIS)
        domain_complexity = await analyzer.analyze_complexity(domain_input, TaskType.DATA_ANALYSIS)

        assert basic_complexity < domain_complexity
