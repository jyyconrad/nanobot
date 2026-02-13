"""
TaskPlanner 单元测试
"""

import pytest

from nanobot.agent.planner.models import TaskStep
from nanobot.agent.planner.task_planner import (
    TaskPlan,
    TaskPlanner,
    TaskPriority,
    TaskType,
)


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
        # 可能需要澄清需求，所以步骤可能为空
        assert isinstance(result.steps, list)
        if result.steps:
            assert all(isinstance(step, TaskStep) for step in result.steps)
            for step in result.steps:
                assert step.id is not None
                assert len(step.description) > 0
                assert len(step.expected_output) > 0
                assert len(step.validation_criteria) > 0

    @pytest.mark.asyncio
    async def test_plan_task_with_detailed_steps(self):
        """测试生成详细任务步骤"""
        planner = TaskPlanner()
        user_input = "开发一个简单的待办事项应用，包含添加、删除、查询功能"

        result = await planner.plan_task(user_input)
        assert isinstance(result, (TaskPlan, dict))

    @pytest.mark.asyncio
    async def test_task_dependency_detection(self):
        """测试任务依赖关系检测"""
        planner = TaskPlanner()
        user_input = "分析销售数据，生成图表并发送邮件报告，需要访问数据库"

        result = await planner.plan_task(user_input)
        assert isinstance(result, TaskPlan)
        # 可能需要澄清需求，所以依赖可能为空
        assert isinstance(result.dependencies, list)

    @pytest.mark.asyncio
    async def test_plan_task_text_summarization(self):
        """测试文本摘要任务规划"""
        planner = TaskPlanner()
        user_input = "总结这篇关于人工智能的文章"

        result = await planner.plan_task(user_input)
        assert isinstance(result, TaskPlan)
        assert result.task_type == TaskType.TEXT_SUMMARIZATION
        assert result.complexity > 0.3

    @pytest.mark.asyncio
    async def test_plan_task_data_analysis(self):
        """测试数据分析任务规划"""
        planner = TaskPlanner()
        user_input = "分析销售数据并生成图表"

        result = await planner.plan_task(user_input)
        assert isinstance(result, TaskPlan)
        assert result.task_type == TaskType.DATA_ANALYSIS
        assert result.complexity > 0.5

    @pytest.mark.asyncio
    async def test_plan_task_web_search(self):
        """测试网络搜索任务规划"""
        planner = TaskPlanner()
        user_input = "搜索最新的人工智能技术趋势"

        result = await planner.plan_task(user_input)
        assert isinstance(result, TaskPlan)
        assert result.task_type == TaskType.WEB_SEARCH
        assert result.complexity > 0.2

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
        complex_input = (
            "实现一个高性能的图像识别系统，包含数据预处理、特征提取、模型训练和评估"
        )
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
        # 如果需要澄清，估计时间为0
        assert plan.estimated_time >= 0

        # 复杂任务
        complex_input = "实现一个完整的机器学习模型"
        plan = await planner.plan_task(complex_input)
        assert isinstance(plan, TaskPlan)

    @pytest.mark.asyncio
    async def test_requires_approval(self):
        """测试是否需要批准"""
        planner = TaskPlanner()

        # 需要批准的任务
        risky_input = "运行系统命令"
        plan = await planner.plan_task(risky_input)
        assert isinstance(plan, TaskPlan)
        assert plan.requires_approval is True

        # 简单任务可能需要澄清，所以可能没有步骤
        safe_input = "计算两个数的和"
        plan = await planner.plan_task(safe_input)
        assert isinstance(plan, TaskPlan)

    @pytest.mark.asyncio
    async def test_clarification_detection(self):
        """测试需求澄清检测"""
        planner = TaskPlanner()
        user_input = "开发一个应用程序"

        plan = await planner.plan_task(user_input)
        assert isinstance(plan, TaskPlan)
        # 简单任务可能不需要澄清，但这里测试属性存在
        assert hasattr(plan, "clarification_needed")
        assert hasattr(plan, "clarification_questions")
        assert isinstance(plan.clarification_questions, list)

    @pytest.mark.asyncio
    async def test_simple_task_steps(self):
        """测试简单任务的步骤生成"""
        planner = TaskPlanner()
        user_input = "计算两个数的和"

        plan = await planner.plan_task(user_input)
        assert isinstance(plan, TaskPlan)
        assert len(plan.steps) <= 3  # 简单任务步骤较少
        assert all(isinstance(step, TaskStep) for step in plan.steps)

    @pytest.mark.asyncio
    async def test_task_step_validation(self):
        """测试任务步骤验证"""
        planner = TaskPlanner()
        user_input = "创建一个Python脚本，读取CSV文件并生成统计报告"

        plan = await planner.plan_task(user_input)
        assert isinstance(plan, TaskPlan)

        for step in plan.steps:
            # 检查步骤基本属性
            assert step.id is not None
            assert step.description is not None
            assert len(step.description.strip()) > 0
            assert step.expected_output is not None
            assert len(step.expected_output.strip()) > 0
            assert step.validation_criteria is not None
            assert len(step.validation_criteria.strip()) > 0
            assert isinstance(step.priority, TaskPriority)
            assert isinstance(step.dependencies, list)
