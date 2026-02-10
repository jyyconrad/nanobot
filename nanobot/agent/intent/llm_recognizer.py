"""
基于大模型的意图识别器

实现基于 LLM API 调用、Few-shot 示例和自定义提示词的意图识别功能。
"""

import logging
import json
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Dict, Any, Union
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """大模型提供商枚举"""
    GLM = "glm"
    GPT = "gpt"
    DOUBAO = "doubao"
    CLAUDE = "claude"
    QWEN = "qwen"


@dataclass
class LLMSample:
    """Few-shot 示例数据类"""
    text: str
    intent: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMRecognitionResult:
    """大模型识别结果数据类"""
    intent: str
    confidence: float
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return (f"LLMRecognitionResult(intent='{self.intent}', "
                f"confidence={self.confidence:.2f})")


class LLMClient(ABC):
    """大模型客户端抽象基类"""

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """
        聊天补全接口

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大令牌数
            **kwargs: 其他参数

        Returns:
            模型响应文本
        """
        pass


class MockLLMClient(LLMClient):
    """模拟 LLM 客户端，用于测试"""

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """返回模拟响应"""
        logger.debug("使用 MockLLMClient 响应")
        return json.dumps({
            "intent": "general.query",
            "confidence": 0.75,
            "reasoning": "无法确定具体意图，默认归类为一般查询"
        }, ensure_ascii=False)


class LLMRecognizer:
    """
    基于大模型的意图识别器

    支持 LLM API 调用、Few-shot 示例和自定义提示词的意图识别。

    示例用法:
        >>> from nanobot.agent.intent.llm_recognizer import LLMRecognizer, LLMProvider, MockLLMClient
        >>> recognizer = LLMRecognizer(
        ...     provider=LLMProvider.DOUBAO,
        ...     api_key="your-api-key",
        ...     model="doubao-pro-32k"
        ... )
        >>> recognizer.set_client(MockLLMClient())
        >>> result = recognizer.recognize("我想预订一张机票")
        >>> print(result)
        LLMRecognitionResult(intent='general.query', confidence=0.75)
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.DOUBAO,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

        self.samples: List[LLMSample] = []
        self._client: Optional[LLMClient] = None
        self._default_prompt = self._get_default_prompt()
        self._custom_prompt: Optional[str] = None

        logger.debug(
            f"LLMRecognizer 初始化完成，提供商: {provider.value}, 模型: {model}"
        )

    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """你是一个专业的意图识别助手。
请分析用户输入的文本，识别其意图。
返回格式必须为 JSON，包含以下字段：
- intent: 识别到的意图名称（字符串）
- confidence: 置信度 (0-1 之间的小数)
- reasoning: 识别理由（可选，但建议提供）

可识别的意图列表：
- greeting: 问候类
- weather.query: 天气查询
- flight.query: 航班查询
- hotel.query: 酒店查询
- general.query: 一般查询
- complaint: 投诉
- thanks: 感谢
- goodbye: 告别

注意：
1. 只返回有效的 JSON，不要包含其他文本
2. 确保 intent 在上述列表中，或返回 'general.query' 作为默认值
3. confidence 应反映你的确定程度
"""

    def set_client(self, client: LLMClient) -> None:
        """
        设置自定义 LLM 客户端

        Args:
            client: LLM 客户端实例
        """
        self._client = client
        logger.debug("LLM 客户端已设置")

    def get_client(self) -> LLMClient:
        """
        获取 LLM 客户端（如果未设置则创建默认客户端）

        Returns:
            LLM 客户端实例
        """
        if self._client is not None:
            return self._client

        # 创建默认客户端（使用 mock）
        logger.warning("未设置 LLM 客户端，使用 MockLLMClient")
        self._client = MockLLMClient()
        return self._client

    def add_sample(self, text: str, intent: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        添加 Few-shot 示例

        Args:
            text: 示例文本
            intent: 示例意图
            metadata: 元数据
        """
        if metadata is None:
            metadata = {}

        self.samples.append(
            LLMSample(text=text, intent=intent, metadata=metadata)
        )
        logger.debug(f"添加示例: {intent} -> {text}")

    def add_samples(self, samples: List[Dict[str, str]]) -> None:
        """
        添加多个示例

        Args:
            samples: 示例列表，每个示例包含 'text' 和 'intent' 字段
        """
        for sample in samples:
            self.add_sample(sample["text"], sample["intent"])

    def clear_samples(self) -> None:
        """清除所有示例"""
        self.samples.clear()
        logger.debug("所有示例已清除")

    def set_prompt(self, prompt: str) -> None:
        """
        设置自定义提示词

        Args:
            prompt: 提示词文本
        """
        self._custom_prompt = prompt
        logger.debug("自定义提示词已设置")

    def get_prompt(self) -> str:
        """
        获取当前使用的提示词

        Returns:
            提示词文本
        """
        return self._custom_prompt or self._default_prompt

    def recognize(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[LLMRecognitionResult]:
        """
        识别文本的意图

        Args:
            text: 待识别的文本
            context: 上下文信息

        Returns:
            识别结果，若识别失败则返回 None
        """
        if context is None:
            context = {}

        logger.debug(f"开始使用 LLM 识别文本: {text}")

        try:
            client = self.get_client()
            prompt = self._build_recognition_prompt(text)
            response = client.chat_completion(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                model=self.model,
                temperature=0.0
            )

            result = self._parse_response(response)
            if result:
                logger.debug(f"LLM 识别结果: {result}")
                return result

        except Exception as e:
            logger.error(f"LLM 识别失败: {e}", exc_info=True)

        logger.debug("LLM 识别未返回有效结果")
        return None

    def _build_recognition_prompt(self, text: str) -> str:
        """
        构建识别提示词

        Args:
            text: 待识别文本

        Returns:
            完整提示词
        """
        prompt = self.get_prompt()

        # 添加示例
        if self.samples:
            prompt += "\n\n示例：\n"
            for sample in self.samples:
                prompt += f"- 文本: {sample.text}\n"
                prompt += f"  意图: {sample.intent}\n"

        return prompt

    def _parse_response(self, response: str) -> Optional[LLMRecognitionResult]:
        """
        解析 LLM 响应

        Args:
            response: 原始响应文本

        Returns:
            解析后的识别结果
        """
        try:
            # 提取 JSON 部分
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1]

            data = json.loads(response.strip())

            return LLMRecognitionResult(
                intent=data.get("intent", "general.query"),
                confidence=data.get("confidence", 0.7),
                reasoning=data.get("reasoning"),
                metadata={}
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"响应解析失败: {e}", exc_info=True)

        return None

    def recognize_batch(
        self,
        texts: List[str],
        contexts: Optional[List[Dict[str, Any]]] = None
    ) -> List[Optional[LLMRecognitionResult]]:
        """
        批量识别文本的意图

        Args:
            texts: 待识别的文本列表
            contexts: 上下文信息列表

        Returns:
            识别结果列表
        """
        if contexts is None:
            contexts = [{} for _ in texts]

        results = []
        for i, (text, context) in enumerate(zip(texts, contexts)):
            logger.debug(f"处理批量识别任务 {i+1}/{len(texts)}: {text}")
            results.append(self.recognize(text, context))

        return results

    @property
    def sample_count(self) -> int:
        """示例数量"""
        return len(self.samples)

    def __repr__(self):
        return (f"LLMRecognizer(provider={self.provider.value}, "
                f"model={self.model}, "
                f"samples={self.sample_count})")
