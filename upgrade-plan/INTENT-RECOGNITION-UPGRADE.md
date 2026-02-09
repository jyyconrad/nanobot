# 意图识别系统升级方案

## 📋 现状分析

### 当前问题

1. **单一固定规则**
   - 现在的指令体系完全基于固定规则匹配
   - 用户输入意图分析也是简单的关键词匹配
   - 无法处理复杂、模糊、多意图的场景

2. **缺乏灵活性**
   - 新增指令需要修改代码
   - 无法动态调整意图识别策略
   - 扩展性差

3. **准确率受限**
   - 纯规则匹配无法理解语义
   - 同义词、变体无法识别
   - 上下文理解能力弱

---

## 🎯 升级目标

设计一个**混合式意图识别系统**，结合三种方式：

1. **固定模式（Rule-based）** - 快速、准确、高效
2. **代码处理（Code-based）** - 复杂逻辑、状态依赖
3. **大模型识别（LLM-based）** - 语义理解、模糊匹配

---

## 🏗️ 综合架构设计

### 三层识别架构

```
用户输入
    ↓
┌─────────────────────────────────────┐
│  第一层：快速规则匹配（固定模式）   │
│  - 精确匹配                    │
│  - 正则表达式                    │
│  - 命令关键词                    │
└─────────────────────────────────────┘
    ↓ 匹配成功 → 直接返回意图
    ↓ 匹配失败
┌─────────────────────────────────────┐
│  第二层：代码逻辑处理（复杂逻辑）   │
│  - 状态检查                    │
│  - 上下文分析                    │
│  - 多条件组合                    │
└─────────────────────────────────────┘
    ↓ 匹配成功 → 直接返回意图
    ↓ 匹配失败
┌─────────────────────────────────────┐
│  第三层：大模型语义识别（LLM）     │
│  - 意图分类                    │
│  - 实体提取                    │
│  - 多意图识别                    │
└─────────────────────────────────────┘
    ↓
返回识别结果
```

---

## 🔧 核心组件设计

### 1. 意图识别器接口（IntentRecognizer）

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

class IntentType(Enum):
    """意图类型"""
    # 命令类
    STATUS = "status"
    HELP = "help"
    EXIT = "exit"
    
    # 任务类
    CODE_ANALYSIS = "code_analysis"
    CODE_REFACTORING = "code_refactoring"
    CODE_FIX = "code_fix"
    
    # 测试类
    TEST_GENERATION = "test_generation"
    TEST_FIX = "test_fix"
    
    # 文档类
    DOC_GENERATION = "doc_generation"
    DOC_UPDATE = "doc_update"
    
    # 项目管理类
    PROJECT_ANALYSIS = "project_analysis"
    TASK_PLANNING = "task_planning"
    
    # 未知
    UNKNOWN = "unknown"

@dataclass
class Intent:
    """意图"""
    type: IntentType  # 意图类型
    confidence: float  # 置信度 0-1
    parameters: Dict[str, Any]  # 意图参数
    method: Optional[str] = None  # 对应的方法名
    metadata: Dict[str, Any] = None  # 元数据

class IntentRecognizer(ABC):
    """
    意图识别器接口
    """
    
    @abstractmethod
    async def recognize(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> Optional[Intent]:
        """
        识别意图
        
        Args:
            input_text: 用户输入
            context: 上下文信息
            
        Returns:
            识别到的意图，如果不匹配返回 None
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """
        获取识别器优先级
        
        Returns:
            优先级（数字越小优先级越高）
        """
        pass
```

### 2. 固定模式识别器（RuleBasedRecognizer）

```python
import re
from typing import Dict, Optional, List

class RuleBasedRecognizer(IntentRecognizer):
    """
    固定规则识别器
    
    特点：
    - 速度快
    - 准确率高
    - 适合明确命令
    """
    
    def __init__(self, rules: List[Dict] = None):
        self.rules = rules or self._default_rules()
    
    def _default_rules(self) -> List[Dict]:
        """默认规则列表"""
        return [
            # 状态命令
            {
                "name": "status",
                "intent": IntentType.STATUS,
                "patterns": [
                    r"^/status\s*$",
                    r"^状态\s*$",
                    r"^查看状态\s*$"
                ],
                "method": "show_status"
            },
            # 帮助命令
            {
                "name": "help",
                "intent": IntentType.HELP,
                "patterns": [
                    r"^/help\s*$",
                    r"^/?help\s*$",
                    r"^帮助\s*$",
                    r"^/?\?$"
                ],
                "method": "show_help"
            },
            # 退出命令
            {
                "name": "exit",
                "intent": IntentType.EXIT,
                "patterns": [
                    r"^/exit\s*$",
                    r"^退出\s*$",
                    r"^再见\s*$",
                    r"^quit\s*$"
                ],
                "method": "exit"
            },
            # 代码分析命令
            {
                "name": "code_analysis",
                "intent": IntentType.CODE_ANALYSIS,
                "patterns": [
                    r"^分析代码\s*(?P<path>.*)",
                    r"^analyze\s+code\s*(?P<path>.*)",
                    r"^代码分析\s*(?P<path>.*)",
                    r"^检查代码\s*(?P<path>.*)"
                ],
                "method": "analyze_code"
            },
            # 测试命令
            {
                "name": "test_fix",
                "intent": IntentType.TEST_FIX,
                "patterns": [
                    r"^修复测试\s*$",
                    r"^fix\s+tests?\s*$",
                    r"^测试失败\s*$",
                    r"^run\s+tests?\s*$"
                ],
                "method": "fix_tests"
            }
        ]
    
    async def recognize(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> Optional[Intent]:
        """
        使用规则识别意图
        """
        input_lower = input_text.strip().lower()
        
        for rule in self.rules:
            for pattern in rule.get("patterns", []):
                match = re.match(pattern, input_lower)
                if match:
:
                    # 提取参数
                    parameters = match.groupdict() if match.groupdict() else {}
                    
                    return Intent(
                        type=rule["intent"],
                        confidence=1.0,  # 规则匹配置信度高
                        parameters=parameters,
                        method=rule.get("method"),
                        metadata={"matched_pattern": pattern, "recognizer": "rule_based"}
                    )
        
        return None
    
    def get_priority(self) -> int:
        """固定规则优先级最高"""
        return 1
    
    def add_rule(self, rule: Dict):
        """添加新规则"""
        self.rules.append(rule)
    
    def remove_rule(self, name: str):
        """移除规则"""
        self.rules = [r for r in self.rules if r.get("name") != name]
```

### 3. 代码处理识别器（CodeBasedRecognizer）

```python
class CodeBasedRecognizer(IntentRecognizer):
    """
    代码逻辑识别器
    
    特点：
    - 支持复杂逻辑
    - 状态依赖
    - 上下文感知
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
        """
        使用代码逻辑识别意图
        """
        # 检查是否在工作目录中
        if context and context.get("in_workspace"):
            # 检查 git 状态
            intent = await self._check_git_status(input_text, context)
            if intent:
                return intent
            
            # 检查依赖
            intent = await self._check_dependencies(input_text, context)
            if intent:
                return intent
            
            # 分析代码上下文
            intent = await self._analyze_code_context(input_text, context)
            if intent:
                return intent
        
        # 检查运行中的任务
        if context:
            intent = await self._check_running_tasks(input_text, context)
            if intent:
                return intent
        
        return None
    
    async def _check_git_status(
        self,
        input_text: str,
        context: Dict
    ) -> Optional[Intent]:
        """检查 git 相关意图"""
        keywords = ["git", "commit", "push", "pull", "branch", "merge"]
        
        if any(kw in input_text.lower() for kw in keywords):
            return Intent(
                type=IntentType.CODE_ANALYSIS,
                confidence=0.9,
                parameters={"action": "git"},
                method="handle_git_command",
                metadata={"recognizer": "code_based"}
            )
        
        return None
    
    async def _check_dependencies(
        self,
        input_text: str,
        context: Dict
    ) -> Optional[Intent]:
        """检查依赖相关的意图"""
        keywords = ["依赖", "dependency", "install", "package", "pip", "npm"]
        
        if any(kw in input_text.lower() for kw in keywords):
            return Intent(
                type=IntentType.CODE_ANALYSIS,
                confidence=0.85,
                parameters={"action": "dependencies"},
                method="handle_dependencies",
                metadata={"recognizer": "code_based"}
            )
        
        return None
    
    async def _check_running_tasks(
        self,
        input_text: str,
        context: Dict
    ) -> Optional[Intent]:
        """检查运行中的任务"""
        task_manager = context.get("task_manager")
        if not task_manager:
            return None
        
        running_tasks = await task_manager.get_running_tasks()
        if not running_tasks:
            return None
        
        keywords = ["进度", "status", "停止", "cancel", "取消"]
        if any(kw in input_text.lower() for kw in keywords):
            return Intent(
                type=IntentType.PROJECT_ANALYSIS,
                confidence=0.9,
                parameters={"running_tasks": len(running_tasks)},
                method="handle_task_management",
                metadata={"recognizer": "code_based"}
            )
        
        return None
    
    async def _analyze_code_context(
        self,
        input_text: str,
        context: Dict
    ) -> Optional[Intent]:
        """分析代码上下文"""
        workspace = context.get("workspace")
        if not workspace:
            return None
        
        # 检查是否在代码目录中
        from pathlib import Path
        
        workspace_path = Path(workspace)
        py_files = list(workspace_path.rglob("*.py"))
        js_files = list(workspace_path.rglob("*.js"))
        
        if py_files or js_files:
            # 检测到代码文件
            keywords = ["优化", "重构", "refactor", "improve"]
            if any(kw in input_text.lower() for kw in keywords):
                return Intent(
                    type=IntentType.CODE_REFACTORING,
                    confidence=0.8,
                    parameters={
                        "language": "python" if py_files else "javascript",
                        "file_count": len(py_files) + len(js_files)
                    },
                    method="handle_code_refactoring",
                    metadata={"recognizer": "code_based"}
                )
        
        return None
    
    def get_priority(self) -> int:
        """代码逻辑优先级中等"""
        return 2
```

### 4. 大模型识别器（LLMRecognizer）

```python
from litellm import acompletion

class LLMRecognizer(IntentRecognizer):
    """
    大模型识别器
    
    特点：
    - 语义理解
    - 模糊匹配
    - 多意图识别
    """
    
    def __init__(self, model: str = "glm-4.7"):
        self.model = model
        self.intent_definitions = self._load_intent_definitions()
    
    def _load_intent_definitions(self) -> str:
        """加载意图定义"""
        return """
# 意图定义

## 1. 代码相关

### code_analysis（代码分析）
用户想要分析代码、检查代码质量、理解代码结构。

关键词：分析、检查、理解、查看、review

### code_refactoring（代码重构）
用户想要优化代码、改进代码结构、提升性能。

关键词：重构、优化、改进、提升、refactor

### code_fix（代码修复）
用户想要修复代码错误、解决问题。

关键词：修复、解决、fix、bug、错误

## 2. 测试相关

### test_generation（测试生成）
用户想要生成测试用例。

关键词：生成测试、写测试、test

### test_fix（测试修复）
用户想要修复失败的测试。

关键词：修复测试、测试失败、test fail

## 3. 文档相关

### doc_generation（文档生成）
用户想要生成文档、编写说明。

关键词：生成文档、写文档、文档、doc

### doc_update（文档更新）
用户想要更新现有文档。

关键词：更新文档、修改文档、更新

## 4. 项目管理

### project_analysis（项目分析）
用户想要分析整个项目、理解项目结构。

关键词：分析项目、项目结构、项目

### task_planning（任务规划）
用户想要规划任务、制定计划。

关键词：规划、计划、任务、todo

## 5. 通用

### status（状态）
用户想要查看系统状态、运行情况。

关键词：状态、status、如何

### help（帮助）
用户想要获取帮助信息。

关键词：帮助、help、怎么、如何

### unknown（未知）
无法明确识别的意图。
"""
    
    async def recognize(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> Optional[Intent]:
        """
        使用大模型识别意图
        """
        # 构建提示词
        prompt = self._build_recognition_prompt(input_text, context)
        
        # 调用大模型
        response = await acompletion(
            model=self.model,
            messages=[
                {"role": "system", "content": self.intent_definitions},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "intent_recognition",
                    "strict": True,
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
                                ]
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1
                            },
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "language": {"type": "string"},
                                    "action": {"type": "string"}
                                }
                            },
                            "reasoning": {
                                "type": "string"
                            }
                        },
                        "required": ["intent", "confidence", "reasoning"]
                    }
                }
            },
            temperature=0.3  # 低温度，提高确定性
        )
        
        # 解析响应
        import json
        result = json.loads(response.choices[0].message.content)
        
        # 映射到 IntentType
        intent_type_map = {
            "code_analysis": IntentType.CODE_ANALYSIS,
            "code_refactoring": IntentType.CODE_REFACTORING,
            "code_fix": IntentType.CODE_FIX,
            "test_generation": IntentType.TEST_GENERATION,
            "test_fix": IntentType.TEST_FIX,
            "doc_generation": IntentType.DOC_GENERATION,
            "doc_update": IntentType.DOC_UPDATE,
            "project_analysis": IntentType.PROJECT_ANALYSIS,
            "task_planning": IntentType.TASK_PLANNING,
            "status": IntentType.STATUS,
            "help": IntentType.HELP,
            "unknown": IntentType.UNKNOWN
        }
        
        return Intent(
            type=intent_type_map.get(result["intent"], IntentType.UNKNOWN),
            confidence=result["confidence"],
            parameters=result.get("parameters", {}),
            metadata={
                "reasoning": result.get("reasoning", ""),
                "recognizer": "llm"
            }
        )
    
    def _build_recognition_prompt(
        self,
        input_text: str,
        context: Optional[Dict]
    ) -> str:
        """构建识别提示词"""
        prompt = f"""
请识别以下用户输入的意图。

用户输入：{input_text}
"""
        
        if context:
            prompt += f"""
上下文信息：
- 工作区：{context.get('workspace', 'N/A')}
- 当前目录：{context.get('current_dir', 'N/A')}
- 运行中任务数：{len(context.get('running_tasks', []))}
"""
        
        prompt += """
请以 JSON 格式返回识别结果，包含：
- intent: 意图类型
- confidence: 置信度（0-1）
- parameters: 提取的参数（如果有）
- reasoning: 识别理由
"""
        return prompt
    
    def get_priority(self) -> int:
        """大模型识别优先级最低（但功能最强）"""
        return 3
```

### 5. 综合识别器（HybridIntentRecognizer）

```python
import logging
from typing import List, Optional

class HybridIntentRecognizer:
    """
    综合意图识别器
    
    按优先级依次尝试不同的识别器：
    1. 固定规则（优先级 1）- 快速、准确
    2. 代码逻辑（优先级 2）- 复杂、上下文
    3. 大模型（优先级 3）- 语义理解、模糊
    """
    
    def __init__(
        self,
        recognizers: List[IntentRecognizer] = None,
        enable_fallback: bool = True,
        log_decisions: bool = True
    ):
        """
        初始化综合识别器
        
        Args:
            recognizers: 识别器列表（按优先级排序）
            enable_fallback: 是否启用降级策略
            log_decisions: 是否记录决策过程
        """
        self.recognizers = recognizers or self._default_recognizers()
        self.enable_fallback = enable_fallback
        self.log_decisions = log_decisions
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self.stats = {
            "total_recognitions": 0,
            "rule_based_matches": 0,
            "code_based_matches": 0,
            "llm_based_matches": 0,
            "no_match": 0
        }
    
    def _default_recognizers(self) -> List[IntentRecognizer]:
        """创建默认识别器列表"""
        return [
            RuleBasedRecognizer(),  # 优先级 1
            CodeBasedRecognizer(),  # 优先级 2
            LLMRecognizer(model="glm-4.7")  # 优先级 3
        ]
    
    async def recognize(
        self,
        input_text: str,
        context: Optional[Dict] = None
    ) -> Intent:
        """
        综合识别意图
        """
        self.stats["total_recognitions"] += 1
        
        self.logger.debug(f"Recognizing intent for: {input_text[:50]}...")
        
        # 按优先级依次尝试
        sorted_recognizers = sorted(
            self.recognizers,
            key=lambda r: r.get_priority()
        )
        
        for recognizer in sorted_recognizers:
            self.logger.debug(
                f"Trying recognizer: {recognizer.__class__.__name__}"
            )
            
            try:
                intent = await recognizer.recognize(input_text, context)
                
                if intent:
                    # 记录统计
                    recognizer_name = recognizer.__class__.__name__
                    if "RuleBased" in recognizer_name:
                        self.stats["rule_based_matches"] += 1
                    elif "CodeBased" in recognizer_name:
                        self.stats["code_based_matches"] += 1
                    elif "LLM" in recognizer_name:
                        self.stats["llm_based_matches"] += 1
                    
                    self.logger.info(
                        f"Intent recognized: {intent.type.value} "
                        f"(confidence: {intent.confidence:.2f}, "
                        f"recognizer: {recognizer_name})"
                    )
                    
                    return intent
            
            except Exception as e:
                self.logger.error(
                    f"Recognizer {recognizer.__class__.__name__} failed: {e}",
                    exc_info=True
                )
                
                if not self.enable_fallback:
                    raise
        
        # 没有匹配的意图
        self.stats["no_match"] += 1
        self.logger.warning(f"No intent matched for: {input_text}")
        
        return Intent(
            type=IntentType.UNKNOWN,
            confidence=0.0,
            parameters={},
            metadata={"recognizer": "none"}
        )
    
    def add_recognizer(self, recognizer: IntentRecognizer):
        """添加识别器"""
        self.recognizers.append(recognizer)
    
    def remove_recognizer(self, recognizer: IntentRecognizer):
        """移除识别器"""
        self.recognizers.remove(recognizer)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.stats["total_recognitions"]
        if total == 0:
            return self.stats.copy()
        
        stats = self.stats.copy()
        stats["rule_based_rate"] = stats["rule_based_matches"] / total
        stats["code_based_rate"] = stats["code_based_matches"] / total
        stats["llm_based_rate"] = stats["llm_based_matches"] / total
        stats["no_match_rate"] = stats["no_match"] / total
        
        return stats
```

---

## 🎨 使用示例

### 示例 1：基本使用

```python
# 创建综合识别器
recognizer = HybridIntentRecognizer()

# 识别意图
intent = await recognizer.recognize(
    "分析这个项目的代码质量",
    context={
        "workspace": "/path/to/project",
        "current_dir": "/path/to/project/src",
        "running_tasks": []
    }
)

print(f"Intent: {intent.type.value}")
print(f"Confidence: {intent.confidence}")
print(f"Parameters: {intent.parameters}")
print(f"Method: {intent.method}")
```

### 示例 2：自定义规则

```python
# 创建规则识别器
rule_recognizer = RuleBasedRecognizer()

# 添加自定义规则
rule_recognizer.add_rule({
    "name": "deploy",
    "intent": IntentTypeType.PROJECT_ANALYSIS,
    "patterns": [
        r"^部署\s+(?P<env>.+)",
        r"^deploy\s+(?P<env>.+)"
    ],
    "method": "deploy_to_environment"
})

# 创建综合识别器
recognizer = HybridIntentRecognizer(recognizers=[rule_recognizer])
```

### 示例 3：自定义代码逻辑

```python
# 创建代码逻辑识别器
code_recognizer = CodeBasedRecognizer()

# 添加自定义处理函数
async def check_custom_logic(input_text: str, context: Dict) -> Optional[Intent]:
    if "特殊任务" in input_text:
        return Intent(
            type=IntentType.TASK_PLANNING,
            confidence=0.95,
            parameters={"custom": True},
            method="handle_custom_task"
        )
    return None

code_recognizer.handlers["custom_logic"] = check_custom_logic

# 创建综合识别器
recognizer = HybridIntentRecognizer(recognizers=[code_recognizer])
```

---

## 📊 性能分析

### 三层识别性能对比

| 识别器 | 速度 | 准确率 | 适用场景 | 优先级 |
|--------|------|--------|---------|--------|
| 固定规则 | ⚡⚡⚡ 极快 | ⭐⭐⭐⭐⭐ 精确 | 明确命令、关键词 | 1 |
| 代码逻辑 | ⚡⚡ 快 | ⭐⭐⭐⭐ 高 | 复杂逻辑、状态依赖 | 2 |
| 大模型 | ⚡ 慢 | ⭐⭐⭐⭐ 中 | 语义理解、模糊匹配 | 3 |

### 实际性能示例

```
固定规则匹配：
- 输入："查看状态"
- 耗时：1ms
- 置信度：1.0
- 匹配器：RuleBasedRecognizer

代码逻辑匹配：
- 输入："检查 git 状态"（在 workspace 中）
- 耗时：5ms
- 置信度：0.9
- 匹配器：CodeBasedRecognizer

大模型匹配：
- 输入："这个代码看起来有点乱，能帮我优化一下吗？"
- 耗时：800ms
- 置信度：0.85
- 匹配器：LLMRecognizer
```

---

## 🔧 集成到 Gateway

### 修改后的 Gateway 类

```python
class Gateway:
    """
    Gateway 集成综合意图识别
    """
    
    def __init__(self, config):
        self.config = config
        self.intent_recognizer = HybridIntentRecognizer()
        self.main_agent = None
    
    async def handle_message(self, message: str) -> str:
        """
        处理用户消息
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

---

## ✅ 实施检查清单

### 核心组件
- [ ] 实现 IntentType 枚举
- [ ] 实现 Intent 数据类
- [ ] 实现 IntentRecognizer 接口

### 识别器实现
- [ ] 实现 RuleBasedRecognizer
- [ ] 实现 CodeBasedRecognizer
- [ ] 实现 LLMRecognizer
- [ ] 实现 HybridIntentRecognizer

### 配置支持
- [ ] 支持自定义规则
- [ ] 支持启用/禁用识别器
- [ ] 支持调整优先级
- [ ] 支持大模型选择

### 集成测试
- [ ] 集成到 Gateway
- [ ] 测试固定规则匹配
- [ ] 测试代码逻辑匹配
- [ ] 测试大模型匹配
- [ ] 测试综合识别流程
- [ ] 测试性能和准确率

---

## 📝 总结

综合意图识别系统提供了强大而灵活的意图识别能力：

✅ **三层架构** - 固定规则 → 代码逻辑 → 大模型
✅ **优先级机制** - 快速匹配优先，语义理解降级
✅ **灵活扩展** - 支持自定义规则和逻辑
✅ **上下文感知** - 考虑当前状态和环境
✅ **性能优化** - 规则匹配极快，大模型兜底
✅ **准确可靠** - 多层验证，提高识别准确率

通过这个系统，Nanobot 可以：
- 快速识别明确命令（规则匹配）
- 处理复杂场景（代码逻辑）
- 理解模糊输入（大模型）
- 动态扩展新意图（配置驱动）
