# 意图识别系统升级方案 - 完善版

## 1. 完善后的实现计划

### 阶段一：基础架构搭建 (Day 1-2)

#### 任务1.1：创建核心接口和数据结构
- 实现 `IntentType` 枚举类，包含所有意图类型
- 实现 `Intent` 数据类，包含意图类型、置信度、参数等
- 实现 `IntentRecognizer` 抽象基类，定义统一接口
- 编写基础单元测试

#### 任务1.2：实现固定规则识别器
- 实现 `RuleBasedRecognizer` 类，支持精确匹配、正则表达式、关键词匹配
- 设计默认规则库，覆盖常见命令场景
- 实现规则管理接口（添加、删除、修改规则）
- 编写规则识别器的单元测试

#### 任务1.3：实现代码逻辑识别器
- 实现 `CodeBasedRecognizer` 类，支持复杂逻辑和状态依赖的意图识别
- 实现 git 状态检查、依赖检查、运行中任务检查等逻辑
- 编写代码逻辑识别器的单元测试

### 阶段二：大模型识别器实现 (Day 3-4)

#### 任务2.1：实现 LLM 识别器
- 实现 `LLMRecognizer` 类，集成大模型 API
- 设计意图定义和分类体系
- 实现提示词构建和响应解析逻辑
- 编写 LLM 识别器的单元测试

#### 任务2.2：优化 LLM 响应解析
- 实现 JSON Schema 验证机制
- 优化错误处理和降级策略
- 测试不同模型的响应差异

### 阶段三：综合识别器实现 (Day 5)

#### 任务3.1：实现综合识别器
- 实现 `HybridIntentRecognizer` 类，整合三层识别架构
- 实现优先级机制和降级策略
- 实现统计信息收集功能
- 编写综合识别器的单元测试

#### 任务3.2：测试性能和准确率
- 编写性能测试，比较不同识别器的速度
- 编写准确率测试，验证识别结果的正确性
- 优化识别器的性能

### 阶段四：Gateway 集成 (Day 6-7)

#### 任务4.1：修改 Gateway 消息处理流程
- 集成 `HybridIntentRecognizer` 到 Gateway
- 修改消息处理入口，使用意图识别结果路由到对应的处理逻辑
- 实现意图到方法的映射关系

#### 任务4.2：实现上下文构建
- 优化上下文构建逻辑，为识别器提供必要的上下文信息
- 实现上下文缓存机制

### 阶段五：测试和验证 (Day 8-10)

#### 任务5.1：编写集成测试
- 编写端到端测试，验证完整的意图识别流程
- 测试不同场景下的识别准确率
- 编写性能基准测试

#### 任务5.2：修复问题和优化
- 修复测试中发现的问题
- 优化识别器的准确率和性能
- 完善文档和示例代码

---

## 2. 三层识别器设计

### 2.1 识别器接口

```python
class IntentType(Enum):
    """意图类型枚举"""
    STATUS = "status"
    HELP = "help"
    EXIT = "exit"
    CODE_ANALYSIS = "code_analysis"
    CODE_REFACTORING = "code_refactoring"
    CODE_FIX = "code_fix"
    TEST_GENERATION = "test_generation"
    TEST_FIX = "test_fix"
    DOC_GENERATION = "doc_generation"
    DOC_UPDATE = "doc_update"
    PROJECT_ANALYSIS = "project_analysis"
    TASK_PLANNING = "task_planning"
    UNKNOWN = "unknown"

@dataclass
class Intent:
    """意图数据类"""
    type: IntentType
    confidence: float
    parameters: Dict[str, Any]
    method: Optional[str] = None
    metadata: Dict[str, Any] = None

class IntentRecognizer(ABC):
    """意图识别器接口"""
    
    @abstractmethod
    async def recognize(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> Optional[Intent]:
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        pass
```

### 2.2 固定规则识别器 (RuleBasedRecognizer)

```python
class RuleBasedRecognizer(IntentRecognizer):
    """
    固定规则识别器
    
    特点：
    - 速度快（<1ms）
    - 准确率高（100%）
    - 适合明确命令场景
    - 优先级：1（最高）
    """
    
    def __init__(self, rules: List[Dict] = None):
        self.rules = rules or self._default_rules()
    
    async def recognize(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> Optional[Intent]:
        input_lower = input_text.strip().lower()
        
        for rule in self.rules:
            for pattern in rule.get("patterns", []):
                match = re.match(pattern, input_lower)
                if match:
                    parameters = match.groupdict() if match.groupdict() else {}
                    return Intent(
                        type=rule["intent"],
                        confidence=1.0,
                        parameters=parameters,
                        method=rule.get("method"),
                        metadata={"matched_pattern": pattern, "recognizer": "rule_based"}
                    )
        return None
    
    # 规则管理方法
    def add_rule(self, rule: Dict):
        self.rules.append(rule)
    
    def remove_rule(self, name: str):
        self.rules = [r for r in self.rules if r.get("name") != name]
```

### 2.3 代码逻辑识别器 (CodeBasedRecognizer)

```python
class CodeBasedRecognizer(IntentRecognizer):
    """
    代码逻辑识别器
    
    特点：
    - 支持复杂逻辑
    - 状态依赖
    - 上下文感知
    - 速度：快（~5ms）
    - 准确率：90%
    - 优先级：2
    """
    
    def __init__(self):
        self.handlers = {
            "check_git_status": self._check_git_status,
            "check_dependencies": self._check_dependencies,
            "check_running_tasks": self._check_running_tasks,
            "analyze_code_context": self._analyze_code_context
        }
    
    async def recognize(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> Optional[Intent]:
        if context and context.get("in_workspace"):
            intent = await self._check_git_status(input_text, context)
            if intent:
                return intent
                
            intent = await self._check_dependencies(input_text, context)
            if intent:
                return intent
                
            intent = await self._analyze_code_context(input_text, context)
            if intent:
                return intent
        
        if context:
            intent = await self._check_running_tasks(input_text, context)
            if intent:
                return intent
        
        return None
```

### 2.4 大模型识别器 (LLMRecognizer)

```python
class LLMRecognizer(IntentRecognizer):
    """
    大模型识别器
    
    特点：
    - 语义理解
    - 模糊匹配
    - 多意图识别
    - 速度：较慢（~800ms）
    - 准确率：85%
    - 优先级：3（最低）
    """
    
    def __init__(self, model: str = "glm-4.7"):
        self.model = model
        self.intent_definitions = self._load_intent_definitions()
    
    async def recognize(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> Optional[Intent]:
        prompt = self._build_recognition_prompt(input_text, context)
        
        response = await acompletion(
            model=self.model,
            messages=[
                {"role": "system", "content": self.intent_definitions},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": self._get_response_schema()
            },
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return self._parse_result(result)
```

### 2.5 综合识别器 (HybridIntentRecognizer)

```python
class HybridIntentRecognizer:
    """
    综合意图识别器
    
    按优先级依次尝试不同的识别器：
    1. 固定规则（优先级 1）- 快速、准确
    2. 代码逻辑（优先级 2）- 复杂、上下文
    3. 大模型（优先级 3）- 语义理解、模糊
    
    支持统计信息收集和降级策略
    """
    
    def __init__(
        self,
        recognizers: List[IntentRecognizer] = None,
        enable_fallback: bool = True,
        log_decisions: bool = True
    ):
        self.recognizers = recognizers or self._default_recognizers()
        self.enable_fallback = enable_fallback
        self.log_decisions = log_decisions
        self.stats = {
            "total_recognitions": 0,
            "rule_based_matches": 0,
            "code_based_matches": 0,
            "llm_based_matches": 0,
            "no_match": 0
        }
    
    async def recognize(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> Intent:
        self.stats["total_recognitions"] += 1
        
        sorted_recognizers = sorted(
            self.recognizers,
            key=lambda r: r.get_priority()
        )
        
        for recognizer in sorted_recognizers:
            try:
                intent = await recognizer.recognize(input_text, context)
                if intent:
                    self._update_stats(recognizer, intent)
                    return intent
            except Exception as e:
                logger.error(f"Recognizer {recognizer.__class__.__name__} failed: {e}")
        
        self.stats["no_match"] += 1
        return Intent(
            type=IntentType.UNKNOWN,
            confidence=0.0,
            parameters={},
            metadata={"recognizer": "none"}
        )
```

---

## 3. LLM 提示词设计

### 3.1 系统提示词

```markdown
# 意图识别系统

你是一个专业的意图识别助手，负责将用户的自然语言输入分类到预定义的意图类别中。

## 意图定义

### 代码相关

#### code_analysis（代码分析）
用户想要分析代码、检查代码质量、理解代码结构。
关键词：分析、检查、理解、查看、review

#### code_refactoring（代码重构）
用户想要优化代码、改进代码结构、提升性能。
关键词：重构、优化、改进、提升、refactor

#### code_fix（代码修复）
用户想要修复代码错误、解决问题。
关键词：修复、解决、fix、bug、错误

### 测试相关

#### test_generation（测试生成）
用户想要生成测试用例。
关键词：生成测试、写测试、test

#### test_fix（测试修复）
用户想要修复失败的测试。
关键词：修复测试、测试失败、test fail

### 文档相关

#### doc_generation（文档生成）
用户想要生成文档、编写说明。
关键词：生成文档、写文档、文档、doc

#### doc_update（文档更新）
用户想要更新现有文档。
关键词：更新文档、修改文档、更新

### 项目管理

#### project_analysis（项目分析）
用户想要分析整个项目、理解项目结构。
关键词：分析项目、项目结构、项目

#### task_planning（任务规划）
用户想要规划任务、制定计划。
关键词：规划、计划、任务、todo

### 通用

#### status（状态）
用户想要查看系统状态、运行情况。
关键词：状态、status、如何

#### help（帮助）
用户想要获取帮助信息。
关键词：帮助、help、怎么、如何

#### unknown（未知）
无法明确识别的意图。

## 识别要求

1. 严格按照上述定义进行意图分类
2. 识别时要考虑用户输入的上下文
3. 对于模糊的输入，选择最可能的意图
4. 如果无法识别，返回 unknown

## 响应格式

请以 JSON 格式返回识别结果，包含：
- intent: 意图类型（必须是上述定义的之一）
- confidence: 置信度（0-1）
- parameters: 提取的参数（如果有）
- reasoning: 识别理由
```

### 3.2 用户提示词模板

```
请识别以下用户输入的意图。

用户输入：{input_text}

上下文信息：
- 工作区：{workspace}
- 当前目录：{current_dir}
- 运行中任务数：{running_tasks_count}

请以 JSON 格式返回识别结果，包含：
- intent: 意图类型
- confidence: 置信度（0-1）
- parameters: 提取的参数（如果有）
- reasoning: 识别理由
```

---

## 4. JSON Schema 设计

### 4.1 LLM 响应格式定义

```json
{
  "name": "intent_recognition",
  "strict": true,
  "schema": {
    "type": "object",
    "properties": {
      "intent": {
        "type": "string",
        "enum": [
          "code_analysis",
          "code_refactoring",
          "code_fix",
          "test_generation",
          "test_fix",
          "doc_generation",
          "doc_update",
          "project_analysis",
          "task_planning",
          "status",
          "help",
          "unknown"
        ],
        "description": "识别到的意图类型"
      },
      "confidence": {
        "type": "number",
        "minimum": 0,
        "maximum": 1,
        "description": "识别的置信度（0-1）"
      },
      "parameters": {
        "type": "object",
        "properties": {
          "path": {"type": "string", "description": "文件或目录路径"},
          "language": {"type": "string", "description": "编程语言"},
          "action": {"type": "string", "description": "具体动作"},
          "task_id": {"type": "string", "description": "任务ID"}
        },
        "description": "提取的参数"
      },
      "reasoning": {
        "type": "string",
        "description": "识别理由"
      }
    },
    "required": ["intent", "confidence", "reasoning"]
  }
}
```

---

## 5. Gateway 集成

### 5.1 消息处理流程修改

```python
class Gateway:
    """
    Gateway 集成综合意图识别
    
    负责：
    - 用户消息接收
    - 意图识别
    - 根据意图路由到对应的处理逻辑
    """
    
    def __init__(self, config):
        self.config = config
        self.intent_recognizer = HybridIntentRecognizer()
        self.main_agent = None
    
    async def handle_message(self, message: str) -> str:
        """
        处理用户消息的主要入口
        
        Args:
            message: 用户输入的消息
            
        Returns:
            最终响应给用户的文本
        """
        # 识别意图
        context = self._build_context()
        intent = await self.intent_recognizer.recognize(message, context)
        
        # 根据意图执行
        if intent.type == IntentType.STATUS:
            return await self._handle_status(intent)
        elif intent.type == IntentType.HELP:
            return await self._handle_help(intent)
        elif intent.type == IntentType.CODE_ANALYSIS:
            return await self._handle_code_analysis(intent)
        elif intent.type == IntentType.TEST_FIX:
            return await self._handle_test_fix(intent)
        elif intent.type == IntentType.UNKNOWN:
            # 未知意图，交给 MainAgent 处理
            return await self.main_agent.process_message(message)
        else:
            # 其他意图也交给 MainAgent
            return await self.main_agent.process_message(message)
    
    def _build_context(self) -> Dict:
        """构建上下文"""
        return {
            "workspace": self.config.get("workspace"),
            "current_dir": os.getcwd(),
            "running_tasks": self._get_running_tasks(),
            "in_workspace": self._is_in_workspace()
        }
```

### 5.2 意图到方法的映射

```python
class IntentMethodMapper:
    """
    意图到方法的映射器
    
    负责将识别到的意图映射到对应的处理方法
    """
    
    def __init__(self):
        self.mappings = {
            IntentType.STATUS: "show_status",
            IntentType.HELP: "show_help",
            IntentType.EXIT: "exit",
            IntentType.CODE_ANALYSIS: "analyze_code",
            IntentType.CODE_REFACTORING: "refactor_code",
            IntentType.CODE_FIX: "fix_code",
            IntentType.TEST_GENERATION: "generate_tests",
            IntentType.TEST_FIX: "fix_tests",
            IntentType.DOC_GENERATION: "generate_documentation",
            IntentType.DOC_UPDATE: "update_documentation",
            IntentType.PROJECT_ANALYSIS: "analyze_project",
            IntentType.TASK_PLANNING: "plan_tasks"
        }
    
    def get_method(self, intent_type: IntentType) -> Optional[str]:
        """
        根据意图类型获取对应的方法名
        
        Args:
            intent_type: 意图类型
            
        Returns:
            方法名，如果没有映射返回 None
        """
        return self.mappings.get(intent_type)
    
    def add_mapping(self, intent_type: IntentType, method_name: str):
        """添加意图到方法的映射"""
        self.mappings[intent_type] = method_name
    
    def remove_mapping(self, intent_type: IntentType):
        """移除意图到方法的映射"""
        if intent_type in self.mappings:
            del self.mappings[intent_type]
```

---

## 6. 测试计划

### 6.1 单元测试

#### 规则识别器测试
```python
class TestRuleBasedRecognizer:
    def test_exact_match(self):
        """测试精确匹配"""
        intent = await recognizer.recognize("/status")
        assert intent.type == IntentType.STATUS
        assert intent.confidence == 1.0
    
    def test_regex_match(self):
        """测试正则表达式匹配"""
        intent = await recognizer.recognize("分析代码 /path/to/file")
        assert intent.type == IntentType.CODE_ANALYSIS
        assert intent.parameters["path"] == "/path/to/file"
    
    def test_no_match(self):
        """测试不匹配的情况"""
        intent = await recognizer.recognize("随便说点什么")
        assert intent is None
```

#### 代码逻辑识别器测试
```python
class TestCodeBasedRecognizer:
    def test_git_status_recognition(self):
        """测试 git 相关意图识别"""
        intent = await recognizer.recognize("检查 git 状态", context={"in_workspace": True})
        assert intent.type == IntentType.CODE_ANALYSIS
        assert intent.parameters["action"] == "git"
    
    def test_dependencies_recognition(self):
        """测试依赖相关意图识别"""
        intent = await recognizer.recognize("安装依赖", context={"in_workspace": True})
        assert intent.type == IntentType.CODE_ANALYSIS
        assert intent.parameters["action"] == "dependencies"
```

#### LLM 识别器测试
```python
class TestLLMRecognizer:
    def test_semantic_recognition(self):
        """测试语义识别"""
        intent = await recognizer.recognize(
            "这个代码看起来有点乱，能帮我优化一下吗？"
        )
        assert intent.type in [IntentType.CODE_REFACTORING, IntentType.CODE_ANALYSIS]
        assert intent.confidence > 0.7
    
    def test_unknown_intent(self):
        """测试未知意图"""
        intent = await recognizer.recognize("今天天气怎么样？")
        assert intent.type == IntentType.UNKNOWN
```

### 6.2 集成测试

```python
class TestHybridIntentRecognizer:
    def test_recognition_priority(self):
        """测试识别器优先级"""
        # 规则识别器应该优先匹配
        intent = await recognizer.recognize("/status")
        assert intent.type == IntentType.STATUS
        assert intent.metadata["recognizer"] == "rule_based"
    
    def test_fallback_mechanism(self):
        """测试降级机制"""
        # 当规则和代码逻辑都不匹配时，应该使用 LLM 识别
        intent = await recognizer.recognize("帮我分析这个项目的架构")
        assert intent.type == IntentType.PROJECT_ANALYSIS
        assert intent.metadata["recognizer"] == "llm"
```

### 6.3 性能测试

```python
class TestPerformance:
    def test_rule_based_speed(self):
        """测试规则识别器的速度"""
        start = time.time()
        for _ in range(1000):
            await recognizer.recognize("/status")
        duration = time.time() - start
        assert duration < 0.1  # 1000次匹配应该在0.1秒内完成
    
    def test_llm_recognition_speed(self):
        """测试 LLM 识别器的速度"""
        start = time.time()
        intent = await recognizer.recognize("帮我分析这个项目")
        duration = time.time() - start
        assert duration < 2.0  # LLM 识别应该在2秒内完成
```

---

## 7. 性能分析

### 7.1 预期响应时间

| 识别器 | 平均响应时间 | 95th 分位数 | 99th 分位数 |
|--------|-------------|------------|------------|
| RuleBasedRecognizer | <1ms | <2ms | <5ms |
| CodeBasedRecognizer | ~5ms | <10ms | <20ms |
| LLMRecognizer | ~800ms | <1.5s | <2s |

### 7.2 准确率预期

| 识别器 | 准确率 | 覆盖场景 |
|--------|--------|---------|
| RuleBasedRecognizer | 100% | 明确命令、关键词匹配 |
| CodeBasedRecognizer | 90% | 复杂逻辑、状态依赖 |
| LLMRecognizer | 85% | 语义理解、模糊匹配 |
| HybridIntentRecognizer | 95% | 综合场景 |

### 7.3 资源消耗

- **内存**: 每个识别器实例占用 <10MB
- **CPU**: RuleBased 和 CodeBased 识别器对 CPU 消耗极低
- **网络**: LLMRecognizer 会有 API 调用开销

---

## 8. 风险评估

### 8.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| LLM API 不稳定 | 识别失败或延迟高 | 中 | 实现重试机制和降级策略 |
| LLM 识别准确率波动 | 识别结果不准确 | 中 | 定期评估和优化提示词 |
| 上下文构建开销大 | 影响整体响应时间 | 低 | 实现上下文缓存机制 |

### 8.2 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 意图分类不完整 | 无法识别新场景 | 中 | 定期更新意图定义和规则库 |
| 参数提取不准确 | 影响后续处理 | 中 | 优化参数提取逻辑和测试 |
| 用户体验下降 | 响应慢或识别错误 | 低 | 持续监控和优化性能 |

### 8.3 安全风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 敏感信息泄露 | 用户输入包含敏感信息 | 低 | 实现输入过滤和脱敏 |
| LLM 响应不安全 | 可能返回有害内容 | 低 | 实现内容审核机制 |

---

## 9. 验收标准

### 9.1 功能验收标准

- [ ] 所有意图类型能够被正确识别
- [ ] 识别准确率达到 95% 以上
- [ ] 平均响应时间 < 100ms（不含 LLM）
- [ ] LLM 识别响应时间 < 2秒
- [ ] 支持规则和代码逻辑的动态更新
- [ ] 集成到 Gateway 系统正常工作

### 9.2 测试验收标准

- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试覆盖率 > 60%
- [ ] 所有测试通过
- [ ] 性能测试达标

### 9.3 文档验收标准

- [ ] API 文档完整
- [ ] 部署和配置说明清晰
- [ ] 使用示例和最佳实践
- [ ] 故障排除指南

### 9.4 性能验收标准

- [ ] 规则识别器响应时间 < 1ms
- [ ] 综合识别器平均响应时间 < 500ms
- [ ] 系统能够处理高并发请求
- [ ] 资源消耗在可接受范围内

---

## 10. 部署和维护

### 10.1 部署架构

```
用户输入 → Gateway → IntentRecognizer → Handler
                ↓
            ContextBuilder
                ↓
            LLM API
```

### 10.2 监控和维护

- 监控识别器的成功率和响应时间
- 定期检查和更新规则库
- 监控 LLM API 的可用性和性能
- 收集用户反馈，持续优化识别模型

### 10.3 版本升级

- 支持识别器的热更新
- 提供版本兼容性保障
- 记录变更历史和升级指南

---

## 11. 总结

本次意图识别系统升级方案基于三层架构（固定规则 → 代码逻辑 → 大模型），提供了高效、准确且灵活的意图识别能力。通过优先级机制确保快速匹配优先，语义理解兜底，同时支持动态扩展和优化。

方案强调了测试驱动开发（TDD），覆盖了单元测试、集成测试和性能测试，确保系统的质量和稳定性。部署和维护方面也提供了详细的规划，包括监控、升级和故障排除。

通过实施这个方案，Nanobot 将能够：
- 快速识别明确命令
- 处理复杂场景和状态依赖
- 理解模糊和自然语言输入
- 动态扩展新的意图类型
- 提供高质量的用户体验
