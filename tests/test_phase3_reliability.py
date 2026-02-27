"""Phase 3 可靠性修复测试用例

测试内容包括：
- 空内容块过滤（_sanitize_empty_content 方法）
- DeepSeek reasoning_content 处理
- LLMResponse reasoning_content 字段
"""

from nanobot.providers.base import LLMProvider, LLMResponse, ToolCallRequest


class TestEmptyContentSanitization:
    """测试空内容块过滤功能"""

    def test_empty_string_content_replaced(self):
        """测试空字符串内容被替换"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": ""},
            {"role": "user", "content": "World"},
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        assert len(sanitized) == 3
        assert sanitized[1]["role"] == "assistant"
        assert sanitized[1]["content"] == "(empty)"
        assert sanitized[0]["content"] == "Hello"

    def test_empty_string_content_with_tool_calls_set_to_none(self):
        """测试带 tool_calls 的助手消息空内容设为 None"""
        messages = [
            {"role": "assistant", "content": "", "tool_calls": [{"id": "call_1"}]},
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        assert len(sanitized) == 1
        assert sanitized[0]["role"] == "assistant"
        assert sanitized[0]["content"] is None
        assert sanitized[0]["tool_calls"] == [{"id": "call_1"}]

    def test_list_content_filters_empty_text_items(self):
        """测试列表内容中的空文本项被过滤"""
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Hello"},
                    {"type": "text", "text": ""},
                    {"type": "text", "text": "World"},
                ],
            }
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        assert len(sanitized) == 1
        content = sanitized[0]["content"]
        assert isinstance(content, list)
        assert len(content) == 2
        assert content[0]["text"] == "Hello"
        assert content[1]["text"] == "World"

    def test_list_content_filters_all_empty_sets_to_empty_placeholder(self):
        """测试列表内容全部为空时替换为占位符"""
        messages = [
            {"role": "assistant", "content": [{"type": "text", "text": ""}]},
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        assert len(sanitized) == 1
        assert sanitized[0]["content"] == "(empty)"

    def test_list_content_filters_empty_input_text(self):
        """测试 input_text 类型的空内容被过滤"""
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "input_text", "text": "Input"},
                    {"type": "input_text", "text": ""},
                ],
            }
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        assert len(sanitized) == 1
        content = sanitized[0]["content"]
        assert isinstance(content, list)
        assert len(content) == 1
        assert content[0]["type"] == "input_text"
        assert content[0]["text"] == "Input"

    def test_list_content_filters_empty_output_text(self):
        """测试 output_text 类型的空内容被过滤"""
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "output_text", "text": "Output"},
                    {"type": "output_text", "text": ""},
                ],
            }
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        assert len(sanitized) == 1
        content = sanitized[0]["content"]
        assert isinstance(content, list)
        assert len(content) == 1
        assert content[0]["type"] == "output_text"
        assert content[0]["text"] == "Output"

    def test_normal_messages_unchanged(self):
        """测试正常消息不被修改"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        assert sanitized == messages

    def test_list_content_with_non_text_types_unchanged(self):
        """测试列表内容中非文本类型不被修改"""
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "image", "url": "https://example.com/image.png"},
                    {"type": "file", "name": "document.pdf"},
                ],
            }
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        assert sanitized == messages

    def test_empty_list_content_without_tool_calls(self):
        """测试空列表内容（无 tool_calls）替换为占位符"""
        messages = [
            {"role": "assistant", "content": []},
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        assert len(sanitized) == 1
        assert sanitized[0]["content"] == "(empty)"

    def test_empty_list_content_with_tool_calls(self):
        """测试空列表内容（有 tool_calls）设为 None"""
        messages = [
            {"role": "assistant", "content": [], "tool_calls": [{"id": "call_1"}]},
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        assert len(sanitized) == 1
        assert sanitized[0]["content"] is None
        assert sanitized[0]["tool_calls"] == [{"id": "call_1"}]

    def test_multiple_empty_messages(self):
        """测试多个空消息都被正确处理"""
        messages = [
            {"role": "assistant", "content": ""},
            {"role": "user", "content": ""},
            {"role": "assistant", "content": ""},
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        assert len(sanitized) == 3
        assert sanitized[0]["content"] == "(empty)"
        assert sanitized[1]["content"] == "(empty)"
        assert sanitized[2]["content"] == "(empty)"

    def test_whitespace_only_content_treated_as_empty(self):
        """测试只有空白字符的内容被视为空"""
        messages = [
            {"role": "assistant", "content": "   "},
        ]

        sanitized = LLMProvider._sanitize_empty_content(messages)

        # 空白字符不是完全空字符串，应该保持不变
        assert len(sanitized) == 1
        assert sanitized[0]["content"] == "   "


class TestReasoningContent:
    """测试 reasoning_content 字段处理"""

    def test_llm_response_with_reasoning_content(self):
        """测试 LLMResponse 支持 reasoning_content 字段"""
        response = LLMResponse(
            content="Final answer",
            reasoning_content="Step-by-step reasoning...",
        )

        assert response.content == "Final answer"
        assert response.reasoning_content == "Step-by-step reasoning..."

    def test_llm_response_without_reasoning_content(self):
        """测试 LLMResponse 不包含 reasoning_content 时默认为 None"""
        response = LLMResponse(content="Answer")

        assert response.content == "Answer"
        assert response.reasoning_content is None

    def test_llm_response_with_tool_calls_and_reasoning(self):
        """测试带工具调用和推理内容的响应"""
        response = LLMResponse(
            content="Done",
            tool_calls=[ToolCallRequest(id="call_1", name="search", arguments={"query": "test"})],
            reasoning_content="Thinking process...",
        )

        assert response.content == "Done"
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "search"
        assert response.reasoning_content == "Thinking process..."

    def test_llm_response_has_tool_calls_property(self):
        """测试 has_tool_calls 属性正常工作"""
        response_without_tools = LLMResponse(content="Answer")
        response_with_tools = LLMResponse(
            content="Done",
            tool_calls=[ToolCallRequest(id="call_1", name="search", arguments={})],
        )

        assert response_without_tools.has_tool_calls is False
        assert response_with_tools.has_tool_calls is True

    def test_llm_response_empty_reasoning_content(self):
        """测试空的 reasoning_content"""
        response = LLMResponse(
            content="Answer",
            reasoning_content="",
        )

        assert response.reasoning_content == ""

    def test_llm_response_all_fields(self):
        """测试 LLMResponse 所有字段"""
        response = LLMResponse(
            content="Final answer",
            tool_calls=[ToolCallRequest(id="call_1", name="tool", arguments={"arg": "val"})],
            finish_reason="stop",
            usage={
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
            reasoning_content="Reasoning steps...",
        )

        assert response.content == "Final answer"
        assert len(response.tool_calls) == 1
        assert response.finish_reason == "stop"
        assert response.usage["total_tokens"] == 150
        assert response.reasoning_content == "Reasoning steps..."
