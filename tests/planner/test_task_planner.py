"""
TaskPlanner 单元测试
"""

import pytest

from nanobot.agent.planner.task_planner import TaskPlan, TaskPlanner, TaskPriority, TaskType


class TestTaskPlanner:
    """TaskPlanner 测试类"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """测试 TaskPlanner 初始化"""
        planner = TaskPlanner()
        assert planner is not None
        assert planner.complexity_analyzer is not None
        assert planner.task_detector is not None
        assert planner.correction_detector is not None
        assert planner.cancellation_detector is not None

    @pytest.mark.asyncio
    async def test_plan_task_code_generation(self):
        """测试代码生成任务规划"""
        planner = TaskPlanner()
        user_input = "编写一个Python函数来计算斐波那契数列"

        result = await planner.plan_task(user_input)
        assert isinstance(result, TaskPlan)
        assert result.task_type == TaskType.CODE_GENERATION
        assert result.complexity > 0.5
        assert len(result.steps) >= 3

    @pytest.mark.asyncio
    async def test_plan_task_text_summarization(self):
        """测试文本摘要任务规划"""
        planner = TaskPlanner()
        user_input = "总结这篇关于人工智能的文章"

        result = await planner.plan_task(user_input)
        assert isinstance(result, TaskPlan)
        assert result.task_type == TaskType.TEXT_SUMMARIZATION
        assert result.complexity > 0.3
        assert len(result.steps) >= 3

    @pytest.mark.asyncio
    async def test_plan_task_data_analysis(self):
        """测试数据分析任务规划"""
        planner = TaskPlanner()
        user_input = "分析销售数据并生成图表"

        result = await planner.plan_task(user_input)
        assert isinstance(result, TaskPlan)
        assert result.task_type == TaskType.DATA_ANALYSIS
        assert result.complexity > 0.5
        assert len(result.steps) >= 4

    @pytest.mark.asyncio
    async def test_plan_task_web_search(self):
        """测试网络搜索任务规划"""
        planner = TaskPlanner()
        user_input = "搜索最新的人工智能技术趋势"

        result = await planner.plan_task(user_input)
        assert isinstance(result, TaskPlan)
        assert result.task_type == TaskType.WEB_SEARCH
        assert result.complexity > 0.2
        assert len(result.steps) >= 3

    @pytest.mark.asyncio
    async def test_plan_task_cancellation(self):
        """测试取消指令检测"""
        planner = TaskPlanner()
        user_input = "取消当前任务"

        result = await planner.plan_task(user_input)
        assert isinstance(result, dict)
        assert result["action"] == "cancel"
        assert "reason" in result

    @pytest.mark.asyncio
    async def test_plan_task_correction(self):
        """测试修正指令检测"""
        planner = TaskPlanner()
        user_input = "修改代码中的错误"
        context = {"last_task": {"description": "编写Python函数"}}

        result = await planner.plan_task(user_input, context)
        assert isinstance(result, dict)
        assert result["action"] == "correct"
        assert "correction" in result

    @pytest.mark.asyncio
    async def test_is_complex_task(self):
        """测试复杂任务判断"""
        planner = TaskPlanner()

        # 复杂任务
        complex_input = "实现一个高性能的图像识别系统，包含数据预处理、特征提取、模型训练和评估"
        assert await planner.is_complex_task(complex_input) is True

        # 简单任务
        simple_input = "计算两个数的和"
        assert await planner.is_complex_task(simple_input) is False

    @pytest.mark.asyncio
    async def test_get_task_type(self):
        """测试任务类型获取"""
        planner = TaskPlanner()

        input1 = "编写代码"
        assert await planner.get_task_type(input1) == TaskType.CODE_GENERATION

        input2 = "总结文章"
        assert await planner.get_task_type(input2) == TaskType.TEXT_SUMMARIZATION

        input3 = "搜索信息"
        assert await planner.get_task_type(input3) == TaskType.WEB_SEARCH

    @pytest.mark.asyncio
    async def test_task_priority(self):
        """测试任务优先级"""
        planner = TaskPlanner()

        # 高优先级任务
        high_input = "部署生产环境"
        plan = await planner.plan_task(high_input)
        assert isinstance(plan, TaskPlan)
        assert plan.priority in [TaskPriority.URGENT, TaskPriority.HIGH]

        # 低优先级任务
        low_input = "读取一个文本文件"
        plan = await planner.plan_task(low_input)
        assert isinstance(plan, TaskPlan)
        assert plan.priority in [TaskPriority.LOW, TaskPriority.MEDIUM]

    @pytest.mark.asyncio
    async def test_estimated_time(self):
        """测试估计执行时间"""
        planner = TaskPlanner()

        # 简单任务
        simple_input = "计算两个数的和"
        plan = await planner.plan_task(simple_input)
        assert isinstance(plan, TaskPlan)
        assert plan.estimated_time < 60

        # 复杂任务
        complex_input = "实现一个完整的机器学习模型"
        plan = await planner.plan_task(complex_input)
        assert isinstance(plan, TaskPlan)
        assert plan.estimated_time > 120

    @pytest.mark.asyncio
    async def test_requires_approval(self):
        """测试是否需要批准"""
        planner = TaskPlanner()

        # 需要批准的任务
        risky_input = "运行系统命令"
        plan = await planner.plan_task(risky_input)
        assert isinstance(plan, TaskPlan)
        assert plan.requires_approval is True

        # 不需要批准的任务
        safe_input = "计算两个数的和"
        plan = await planner.plan_task(safe_input)
        assert isinstance(plan, TaskPlan)
        assert plan.requires_approval is False
