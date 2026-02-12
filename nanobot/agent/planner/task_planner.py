"""
任务规划器

负责分析用户输入，识别任务类型，评估复杂度，并制定执行计划。
集成LLM调用进行智能任务分解，支持多轮澄清和详细步骤生成。
"""

from typing import Any, Dict, List, Optional, Union, ClassVar
import json
import re

from pydantic import BaseModel, Field

from nanobot.agent.planner.cancellation_detector import CancellationDetector
from nanobot.agent.planner.complexity_analyzer import ComplexityAnalyzer
from nanobot.agent.planner.correction_detector import CorrectionDetector
from nanobot.agent.planner.models import TaskPlan, TaskPriority, TaskType, TaskStep
from nanobot.agent.planner.task_detector import TaskDetector
from nanobot.providers import LiteLLMProvider, LLMProvider


class TaskPlanner(BaseModel):
    """任务规划器"""

    complexity_analyzer: ComplexityAnalyzer = Field(default_factory=ComplexityAnalyzer)
    task_detector: TaskDetector = Field(default_factory=TaskDetector)
    correction_detector: CorrectionDetector = Field(default_factory=CorrectionDetector)
    cancellation_detector: CancellationDetector = Field(default_factory=CancellationDetector)
    llm_provider: LLMProvider = Field(default_factory=LiteLLMProvider)

    class Config:
        """配置类"""

        arbitrary_types_allowed = True

    # 任务分解的Prompt模板
    TASK_DECOMPOSITION_PROMPT: ClassVar[str] = """你是一个专业的任务分解专家。请将用户的任务分解为详细的执行步骤。

任务描述：{user_input}

{context_info}

分解要求：
1. 每个步骤必须包含：
   - 步骤描述：具体要做什么
   - 预期输出：该步骤完成后会有什么结果
   - 验证标准：如何判断该步骤是否成功完成
2. 识别步骤之间的依赖关系（哪些步骤需要在其他步骤之前完成）
3. 判断哪些步骤可以并行执行
4. 识别是否有条件分支步骤（如：if 条件成立则执行）
5. 为每个步骤分配优先级（low/medium/high/urgent）
6. 识别任务依赖的外部资源或条件
7. 如果你需要更多信息来完善任务分解，请列出需要澄清的问题

请按照以下JSON格式返回结果：
{{
  "steps": [
    {{
      "id": "step1",
      "description": "步骤描述",
      "expected_output": "预期输出",
      "validation_criteria": "验证标准",
      "dependencies": ["step2"],
      "parallel": false,
      "condition": "if 条件成立则执行",
      "priority": "medium"
    }}
  ],
  "dependencies": ["外部依赖1", "外部依赖2"],
  "clarification_needed": false,
  "clarification_questions": ["需要澄清的问题1", "需要澄清的问题2"]
}}"""

    # 需求澄清的Prompt模板
    CLARIFICATION_PROMPT: ClassVar[str] = """你是一个专业的需求分析专家。请分析用户的任务描述，识别需要澄清的信息。

任务描述：{user_input}

已有的上下文信息：{context}

请识别以下内容：
1. 任务的范围是否明确
2. 所需的输入/输出是否清晰
3. 是否有未定义的术语或概念
4. 是否有相互矛盾的要求
5. 是否需要更多信息来制定详细计划

请列出需要澄清的问题，每个问题应该具体且有针对性。

返回格式：
{{
  "clarification_needed": true/false,
  "clarification_questions": ["问题1", "问题2"]
}}"""

    async def plan_task(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> Union[TaskPlan, Dict[str, str]]:
        """
        规划任务执行计划

        Args:
            user_input: 用户输入文本
            context: 上下文信息

        Returns:
            任务执行计划或修正/取消指令
        """
        try:
            # 对于明确的取消指令，先检查
            if "取消" in user_input or "停止" in user_input or "终止" in user_input:
                if await self.cancellation_detector.is_cancellation(user_input):
                    return {
                        "action": "cancel",
                        "reason": await self.cancellation_detector.get_reason(user_input),
                    }

            # 检查是否是修正指令
            correction = await self.correction_detector.detect_correction(user_input, context)
            if correction:
                return {"action": "correct", "correction": correction}

            # 再次检查是否是取消指令（以防之前漏检）
            if await self.cancellation_detector.is_cancellation(user_input):
                return {
                    "action": "cancel",
                    "reason": await self.cancellation_detector.get_reason(user_input),
                }

            # 检测任务类型
            task_type = await self.task_detector.detect_task_type(user_input)

            # 分析复杂度
            complexity = await self.complexity_analyzer.analyze_complexity(user_input, task_type)

            # 生成执行计划
            plan = await self._generate_plan(user_input, task_type, complexity, context)

            return plan

        except Exception as e:
            raise Exception(f"任务规划失败: {str(e)}")

    async def _generate_plan(
        self,
        user_input: str,
        task_type: TaskType,
        complexity: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskPlan:
        """
        生成任务执行计划

        Args:
            user_input: 用户输入文本
            task_type: 任务类型
            complexity: 任务复杂度
            context: 上下文信息

        Returns:
            任务执行计划
        """
        # 检查是否需要澄清需求
        clarification_needed, clarification_questions = await self._check_clarification_needed(
            user_input, context
        )

        if clarification_needed:
            return TaskPlan(
                task_type=task_type,
                priority=self._determine_priority(complexity, task_type),
                complexity=complexity,
                steps=[],
                estimated_time=0,
                requires_approval=True,
                clarification_needed=True,
                clarification_questions=clarification_questions,
                dependencies=[]
            )

        # 根据任务类型和复杂度生成执行步骤
        steps = await self._generate_steps(user_input, task_type, complexity, context)

        # 估算执行时间
        estimated_time = self._estimate_time(complexity, len(steps))

        # 确定优先级
        priority = self._determine_priority(complexity, task_type)

        # 确定是否需要用户批准
        requires_approval = self._requires_approval(complexity, task_type)

        # 检测任务依赖关系
        dependencies = await self._detect_external_dependencies(user_input, context)

        return TaskPlan(
            task_type=task_type,
            priority=priority,
            complexity=complexity,
            steps=steps,
            estimated_time=estimated_time,
            requires_approval=requires_approval,
            clarification_needed=False,
            clarification_questions=[],
            dependencies=dependencies
        )

    async def _check_clarification_needed(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, List[str]]:
        """
        检查是否需要澄清需求

        Args:
            user_input: 用户输入文本
            context: 上下文信息

        Returns:
            (是否需要澄清, 澄清问题列表)
        """
        context_str = json.dumps(context, ensure_ascii=False) if context else "无"

        prompt = self.CLARIFICATION_PROMPT.format(
            user_input=user_input,
            context=context_str
        )

        try:
            messages = [
                {"role": "system", "content": "你是一个专业的需求分析专家，擅长识别任务需求中的模糊点。"},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm_provider.chat(messages, temperature=0.2, max_tokens=1024)

            if response.content:
                data = self._parse_llm_response(response.content)
                return data.get("clarification_needed", False), data.get("clarification_questions", [])

        except Exception as e:
            print(f"检查澄清需求失败: {str(e)}")

        return False, []

    async def _detect_external_dependencies(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        检测任务的外部依赖关系

        Args:
            user_input: 用户输入文本
            context: 上下文信息

        Returns:
            依赖关系列表
        """
        dependencies = []

        # 简单的依赖检测逻辑
        if any(keyword in user_input for keyword in ["数据库", "API", "接口", "外部服务"]):
            dependencies.append("需要访问外部API或数据库")

        if any(keyword in user_input for keyword in ["文件", "文档", "数据"]):
            dependencies.append("需要访问本地文件或数据")

        if any(keyword in user_input for keyword in ["网络", "互联网"]):
            dependencies.append("需要网络连接")

        if any(keyword in user_input for keyword in ["权限", "访问"]):
            dependencies.append("需要特定权限或访问权限")

        return dependencies

    async def _generate_steps(
        self,
        user_input: str,
        task_type: TaskType,
        complexity: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[TaskStep]:
        """
        生成任务执行步骤（基于LLM的智能分解）

        Args:
            user_input: 用户输入文本
            task_type: 任务类型
            complexity: 任务复杂度
            context: 上下文信息

        Returns:
            执行步骤列表
        """
        # 简单任务使用默认步骤，复杂任务使用LLM分解
        if complexity < 0.4:
            return self._get_simple_task_steps(task_type)

        # 使用LLM进行智能任务分解
        return await self._decompose_task_with_llm(user_input, task_type, context)

    async def _decompose_task_with_llm(
        self, user_input: str, task_type: TaskType, context: Optional[Dict[str, Any]] = None
    ) -> List[TaskStep]:
        """
        使用LLM进行任务分解

        Args:
            user_input: 用户输入文本
            task_type: 任务类型
            context: 上下文信息

        Returns:
            执行步骤列表
        """
        context_info = ""
        if context:
            context_info = f"上下文信息：{json.dumps(context, ensure_ascii=False)}"

        prompt = self.TASK_DECOMPOSITION_PROMPT.format(
            user_input=user_input,
            context_info=context_info
        )

        try:
            messages = [
                {"role": "system", "content": "你是一个专业的任务分解专家，擅长将复杂任务分解为详细的执行步骤。"},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm_provider.chat(messages, temperature=0.3, max_tokens=4096)

            if response.content:
                # 解析LLM返回的JSON结果
                steps_data = self._parse_llm_response(response.content)
                return self._convert_to_task_steps(steps_data)

        except Exception as e:
            print(f"LLM任务分解失败，使用默认步骤: {str(e)}")

        #  fallback到默认步骤
        return self._get_simple_task_steps(task_type)

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """
        解析LLM返回的响应，提取JSON数据

        Args:
            content: LLM返回的文本内容

        Returns:
            解析后的JSON数据
        """
        # 尝试从响应中提取JSON部分
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except Exception as e:
                print(f"JSON解析失败: {str(e)}")

        # 如果没有JSON格式，返回默认结构
        return {"steps": [], "dependencies": [], "clarification_needed": False, "clarification_questions": []}

    def _convert_to_task_steps(self, data: Dict[str, Any]) -> List[TaskStep]:
        """
        将解析后的JSON数据转换为TaskStep对象

        Args:
            data: 解析后的JSON数据

        Returns:
            TaskStep对象列表
        """
        steps = []
        for i, step_data in enumerate(data.get("steps", [])):
            try:
                step = TaskStep(
                    id=f"step{i+1}",
                    description=step_data.get("description", f"步骤{i+1}"),
                    expected_output=step_data.get("expected_output", "完成该步骤"),
                    validation_criteria=step_data.get("validation_criteria", "步骤执行成功"),
                    dependencies=step_data.get("dependencies", []),
                    parallel=step_data.get("parallel", False),
                    condition=step_data.get("condition"),
                    priority=TaskPriority(step_data.get("priority", "medium"))
                )
                steps.append(step)
            except Exception as e:
                print(f"转换步骤数据失败: {str(e)}")

        if not steps:
            return [
                TaskStep(
                    id="step1",
                    description="分析任务需求",
                    expected_output="明确任务目标和范围",
                    validation_criteria="任务需求文档已创建",
                    dependencies=[],
                    parallel=False
                ),
                TaskStep(
                    id="step2",
                    description="执行任务",
                    expected_output="任务执行完成",
                    validation_criteria="任务结果符合预期",
                    dependencies=["step1"],
                    parallel=False
                ),
                TaskStep(
                    id="step3",
                    description="验证结果",
                    expected_output="任务结果已验证",
                    validation_criteria="结果通过质量检查",
                    dependencies=["step2"],
                    parallel=False
                )
            ]

        return steps

    def _get_simple_task_steps(self, task_type: TaskType) -> List[TaskStep]:
        """
        获取简单任务的默认步骤

        Args:
            task_type: 任务类型

        Returns:
            默认执行步骤列表
        """
        if task_type == TaskType.CODE_GENERATION:
            return [
                TaskStep(id="step1", description="分析代码需求", expected_output="明确功能需求和接口设计", validation_criteria="需求文档已创建", dependencies=[], parallel=False),
                TaskStep(id="step2", description="设计代码结构", expected_output="确定代码架构和模块划分", validation_criteria="架构设计文档已完成", dependencies=["step1"], parallel=False),
                TaskStep(id="step3", description="编写代码实现", expected_output="代码实现已完成", validation_criteria="代码通过语法检查", dependencies=["step2"], parallel=False),
                TaskStep(id="step4", description="测试代码功能", expected_output="代码功能测试通过", validation_criteria="所有测试用例通过", dependencies=["step3"], parallel=False),
                TaskStep(id="step5", description="优化代码性能", expected_output="代码性能已优化", validation_criteria="性能指标达标", dependencies=["step4"], parallel=False)
            ]
        elif task_type == TaskType.TEXT_SUMMARIZATION:
            return [
                TaskStep(id="step1", description="分析文本内容", expected_output="理解文本主题和结构", validation_criteria="文本内容已分析", dependencies=[], parallel=False),
                TaskStep(id="step2", description="提取关键信息", expected_output="提取文本中的关键要点", validation_criteria="关键信息已提取", dependencies=["step1"], parallel=False),
                TaskStep(id="step3", description="生成摘要", expected_output="文本摘要已生成", validation_criteria="摘要符合要求", dependencies=["step2"], parallel=False),
                TaskStep(id="step4", description="优化摘要质量", expected_output="摘要质量已优化", validation_criteria="摘要清晰准确", dependencies=["step3"], parallel=False)
            ]
        elif task_type == TaskType.DATA_ANALYSIS:
            return [
                TaskStep(id="step1", description="分析数据需求", expected_output="明确数据分析目标", validation_criteria="需求文档已创建", dependencies=[], parallel=False),
                TaskStep(id="step2", description="收集数据", expected_output="数据收集完成", validation_criteria="数据源已获取", dependencies=["step1"], parallel=False),
                TaskStep(id="step3", description="清理数据", expected_output="数据清理完成", validation_criteria="数据质量达标", dependencies=["step2"], parallel=False),
                TaskStep(id="step4", description="分析数据", expected_output="数据分析完成", validation_criteria="分析结果已生成", dependencies=["step3"], parallel=False),
                TaskStep(id="step5", description="可视化结果", expected_output="结果可视化完成", validation_criteria="图表清晰易读", dependencies=["step4"], parallel=False)
            ]
        elif task_type == TaskType.WEB_SEARCH:
            return [
                TaskStep(id="step1", description="分析搜索需求", expected_output="明确搜索关键词和范围", validation_criteria="搜索条件已确定", dependencies=[], parallel=False),
                TaskStep(id="step2", description="执行搜索", expected_output="搜索结果已获取", validation_criteria="搜索结果已返回", dependencies=["step1"], parallel=False),
                TaskStep(id="step3", description="处理搜索结果", expected_output="结果处理完成", validation_criteria="结果已筛选", dependencies=["step2"], parallel=False),
                TaskStep(id="step4", description="总结结果", expected_output="搜索结果已总结", validation_criteria="结果符合需求", dependencies=["step3"], parallel=False)
            ]
        elif task_type == TaskType.FILE_OPERATION:
            return [
                TaskStep(id="step1", description="分析文件操作需求", expected_output="明确文件操作类型", validation_criteria="操作类型已确定", dependencies=[], parallel=False),
                TaskStep(id="step2", description="执行文件操作", expected_output="文件操作完成", validation_criteria="操作执行成功", dependencies=["step1"], parallel=False),
                TaskStep(id="step3", description="验证操作结果", expected_output="操作结果已验证", validation_criteria="结果符合预期", dependencies=["step2"], parallel=False)
            ]
        elif task_type == TaskType.SYSTEM_COMMAND:
            return [
                TaskStep(id="step1", description="分析系统命令需求", expected_output="明确命令参数和选项", validation_criteria="命令已确定", dependencies=[], parallel=False),
                TaskStep(id="step2", description="执行系统命令", expected_output="命令执行完成", validation_criteria="命令执行成功", dependencies=["step1"], parallel=False),
                TaskStep(id="step3", description="检查命令结果", expected_output="命令结果已检查", validation_criteria="结果符合预期", dependencies=["step2"], parallel=False)
            ]
        else:
            return [
                TaskStep(id="step1", description="分析任务需求", expected_output="明确任务目标", validation_criteria="需求已理解", dependencies=[], parallel=False),
                TaskStep(id="step2", description="执行任务", expected_output="任务执行完成", validation_criteria="任务已完成", dependencies=["step1"], parallel=False),
                TaskStep(id="step3", description="检查结果", expected_output="结果已检查", validation_criteria="结果符合要求", dependencies=["step2"], parallel=False)
            ]

    def _estimate_time(self, complexity: float, step_count: int) -> int:
        """
        估算执行时间

        Args:
            complexity: 任务复杂度
            step_count: 步骤数量

        Returns:
            估计执行时间（秒）
        """
        if complexity < 0.3 and step_count <= 2:
            # 简单任务，快速执行
            return int(25 + complexity * 10 * step_count)
        elif complexity < 0.6:
            # 中等复杂度任务
            base_time = 40
            complexity_factor = 1 + complexity * 2
            step_factor = 1 + step_count * 0.15
            return int(base_time * complexity_factor * step_factor)
        else:
            # 复杂任务，需要更多时间
            base_time = 60
            complexity_factor = 1 + complexity * 3
            step_factor = 1 + step_count * 0.2
            return int(base_time * complexity_factor * step_factor)

    def _determine_priority(self, complexity: float, task_type: TaskType) -> TaskPriority:
        """
        确定任务优先级

        Args:
            complexity: 任务复杂度
            task_type: 任务类型

        Returns:
            任务优先级
        """
        if task_type == TaskType.SYSTEM_COMMAND or complexity > 0.8:
            return TaskPriority.URGENT
        elif task_type in [TaskType.CODE_GENERATION, TaskType.DATA_ANALYSIS] or complexity > 0.6:
            return TaskPriority.HIGH
        elif complexity > 0.4:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW

    def _requires_approval(self, complexity: float, task_type: TaskType) -> bool:
        """
        确定是否需要用户批准

        Args:
            complexity: 任务复杂度
            task_type: 任务类型

        Returns:
            是否需要用户批准
        """
        if task_type == TaskType.SYSTEM_COMMAND or complexity > 0.7:
            return True
        return False

    def _schedule_tasks(self, steps: List[TaskStep]) -> List[TaskStep]:
        """
        调度任务步骤，优化执行顺序

        Args:
            steps: 原始任务步骤列表

        Returns:
            调度后的任务步骤列表
        """
        # 1. 首先处理有依赖关系的步骤
        dependent_steps = [step for step in steps if step.dependencies]
        independent_steps = [step for step in steps if not step.dependencies]

        # 2. 按优先级排序
        priority_order = [TaskPriority.URGENT, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]

        # 3. 构建依赖图
        dependency_graph = self._build_dependency_graph(steps)

        # 4. 拓扑排序
        scheduled_steps = self._topological_sort(dependency_graph)

        # 5. 优化调度 - 识别可以并行执行的步骤
        parallel_groups = self._identify_parallel_groups(scheduled_steps)

        return self._generate_schedule_from_groups(parallel_groups)

    def _build_dependency_graph(self, steps: List[TaskStep]) -> Dict[str, List[str]]:
        """
        构建任务依赖图

        Args:
            steps: 任务步骤列表

        Returns:
            依赖图（步骤ID -> 依赖步骤ID列表）
        """
        graph = {}
        for step in steps:
            graph[step.id] = step.dependencies.copy()
        return graph

    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """
        拓扑排序，确定任务执行顺序

        Args:
            graph: 依赖图

        Returns:
            拓扑排序后的步骤ID列表
        """
        visited = set()
        result = []

        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            for dependency in graph.get(node, []):
                if dependency not in visited:
                    dfs(dependency)
            result.append(node)

        for node in graph:
            if node not in visited:
                dfs(node)

        return result

    def _identify_parallel_groups(self, sorted_steps: List[str]) -> List[List[str]]:
        """
        识别可以并行执行的步骤组

        Args:
            sorted_steps: 拓扑排序后的步骤ID列表

        Returns:
            并行执行组列表
        """
        groups = []
        current_group = []

        for step_id in sorted_steps:
            # 检查步骤是否可以并行执行
            step = next(s for s in self.steps if s.id == step_id)
            if step.parallel and len(current_group) > 0:
                current_group.append(step_id)
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [step_id]

        if current_group:
            groups.append(current_group)

        return groups

    def _generate_schedule_from_groups(self, parallel_groups: List[List[str]]) -> List[TaskStep]:
        """
        从并行组生成调度计划

        Args:
            parallel_groups: 并行执行组列表

        Returns:
            调度后的任务步骤列表
        """
        schedule = []

        for group in parallel_groups:
            if len(group) > 1:
                # 并行组，标记为可以并行执行
                for step_id in group:
                    step = next(s for s in self.steps if s.id == step_id)
                    schedule.append(step.copy(update={"parallel": True}))
            else:
                # 串行步骤
                step = next(s for s in self.steps if s.id == group[0])
                schedule.append(step.copy(update={"parallel": False}))

        return schedule

    async def is_complex_task(self, user_input: str) -> bool:
        """
        判断任务是否复杂

        Args:
            user_input: 用户输入文本

        Returns:
            是否为复杂任务
        """
        task_type = await self.task_detector.detect_task_type(user_input)
        complexity = await self.complexity_analyzer.analyze_complexity(user_input, task_type)
        return complexity > 0.6

    async def get_task_type(self, user_input: str) -> TaskType:
        """
        获取任务类型

        Args:
            user_input: 用户输入文本

        Returns:
            任务类型
        """
        return await self.task_detector.detect_task_type(user_input)
