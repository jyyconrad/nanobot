"""LiteLLM provider implementation for multi-provider support."""

import os
from typing import Any

import litellm
from litellm import acompletion

from nanobot.providers.base import LLMProvider, LLMResponse, ToolCallRequest


class LiteLLMProvider(LLMProvider):
    """
    LLM provider using LiteLLM for multi-provider support.

    Supports OpenRouter, Anthropic, OpenAI, Gemini, and many other providers through
    a unified interface.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        default_model: str = "anthropic/claude-opus-4-5",
        custom_protocol: str | None = None,  # "openai" or "anthropic"
        custom_headers: dict[str, str] | None = None,
    ):
        # Store the initial API key - but it will be resolved dynamically on each call
        self._api_key = api_key
        self.api_base = api_base
        self.default_model = default_model
        self.custom_protocol = custom_protocol
        self.custom_headers = custom_headers or {}

        # Detect OpenRouter by api_key prefix or explicit api_base
        self.is_openrouter = (api_key and api_key.startswith("sk-or-")) or (
            api_base and "openrouter" in api_base
        )

        # Track if using custom provider with explicit protocol
        self.is_custom_openai = custom_protocol == "openai"
        self.is_custom_anthropic = custom_protocol == "anthropic"

        # Track if using ollama (check before vllm since ollama uses port 11434)
        self.is_ollama = "ollama" in default_model.lower() or (api_base and "11434" in api_base)

        # Track if using custom endpoint (vLLM, etc.) - exclude Ollama
        self.is_vllm = bool(api_base) and not self.is_openrouter and not self.is_ollama

        # Track if using volcengine
        self.is_volcengine = "volcengine" in default_model

        # Track if model uses custom/ prefix
        self.is_custom_model = default_model.startswith("custom/")

        # Configure LiteLLM based on provider (initial setup only)
        if api_key:
            self._set_initial_env_vars(api_key)

        if api_base:
            litellm.api_base = api_base

        # Disable LiteLLM logging noise
        litellm.suppress_debug_info = True

    @property
    def api_key(self) -> str | None:
        """Resolve API key on each call for hot-reload support.

        This allows API key changes to take effect without restarting the application.
        Priority: Environment Variable > Config File
        """
        # Check environment variables first (highest priority)
        if self.is_openrouter:
            return os.getenv("OPENROUTER_API_KEY") or self._api_key
        elif self.is_custom_openai or (self.is_custom_model and not self.is_custom_anthropic):
            return os.getenv("OPENAI_API_KEY") or self._api_key
        elif self.is_custom_anthropic:
            return os.getenv("ANTHROPIC_API_KEY") or self._api_key
        elif self.is_vllm or self.is_ollama:
            return os.getenv("OPENAI_API_KEY") or self._api_key
        elif "deepseek" in self.default_model:
            return os.getenv("DEEPSEEK_API_KEY") or self._api_key
        elif "anthropic" in self.default_model:
            return os.getenv("ANTHROPIC_API_KEY") or self._api_key
        elif "openai" in self.default_model or "gpt" in self.default_model:
            return os.getenv("OPENAI_API_KEY") or self._api_key
        elif "gemini" in self.default_model.lower():
            return os.getenv("GEMINI_API_KEY") or self._api_key
        elif (
            "zhipu" in self.default_model
            or "glm" in self.default_model
            or "zai" in self.default_model
        ):
            return os.getenv("ZHIPUAI_API_KEY") or self._api_key
        elif "volcengine" in self.default_model:
            return os.getenv("OPENAI_API_KEY") or self._api_key
        elif "groq" in self.default_model:
            return os.getenv("GROQ_API_KEY") or self._api_key

        # Fallback to stored value
        return self._api_key

    def _set_initial_env_vars(self, api_key: str) -> None:
        """Set environment variables during initialization (legacy support)."""
        if self.is_openrouter:
            os.environ["OPENROUTER_API_KEY"] = api_key
        elif self.is_custom_openai or (self.is_custom_model and not self.is_custom_anthropic):
            os.environ["OPENAI_API_KEY"] = api_key
        elif self.is_custom_anthropic:
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif self.is_vllm or self.is_ollama:
            os.environ["OPENAI_API_KEY"] = api_key
        elif "deepseek" in self.default_model:
            os.environ.setdefault("DEEPSEEK_API_KEY", api_key)
        elif "anthropic" in self.default_model:
            os.environ.setdefault("ANTHROPIC_API_KEY", api_key)
        elif "openai" in self.default_model or "gpt" in self.default_model:
            os.environ.setdefault("OPENAI_API_KEY", api_key)
        elif "gemini" in self.default_model.lower():
            os.environ.setdefault("GEMINI_API_KEY", api_key)
        elif (
            "zhipu" in self.default_model
            or "glm" in self.default_model
            or "zai" in self.default_model
        ):
            os.environ.setdefault("ZHIPUAI_API_KEY", api_key)
        elif "volcengine" in self.default_model:
            os.environ["OPENAI_API_KEY"] = api_key
        elif "groq" in self.default_model:
            os.environ.setdefault("GROQ_API_KEY", api_key)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Send a chat completion request via LiteLLM.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of tool definitions in OpenAI format.
            model: Model identifier (e.g., 'anthropic/claude-sonnet-4-5').
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            LLMResponse with content and/or tool calls.
        """
        model = model or self.default_model

        # Resolve API key dynamically on each call for hot-reload support
        current_api_key = self.api_key

        # Set environment variable before each call to ensure latest value is used
        if current_api_key:
            if self.is_openrouter:
                os.environ["OPENROUTER_API_KEY"] = current_api_key
            elif self.is_custom_openai or (self.is_custom_model and not self.is_custom_anthropic):
                os.environ["OPENAI_API_KEY"] = current_api_key
            elif self.is_custom_anthropic:
                os.environ["ANTHROPIC_API_KEY"] = current_api_key
            elif self.is_vllm or self.is_ollama:
                os.environ["OPENAI_API_KEY"] = current_api_key
            elif "deepseek" in model:
                os.environ["DEEPSEEK_API_KEY"] = current_api_key
            elif "anthropic" in model:
                os.environ["ANTHROPIC_API_KEY"] = current_api_key
            elif "openai" in model or "gpt" in model:
                os.environ["OPENAI_API_KEY"] = current_api_key
            elif "gemini" in model.lower():
                os.environ["GEMINI_API_KEY"] = current_api_key
            elif "zhipu" in model or "glm" in model or "zai" in model:
                os.environ["ZHIPUAI_API_KEY"] = current_api_key
            elif "volcengine" in model:
                os.environ["OPENAI_API_KEY"] = current_api_key
            elif "groq" in model:
                os.environ["GROQ_API_KEY"] = current_api_key

        # Handle custom/ prefix models
        if model.startswith("custom/"):
            base_model = model.replace("custom/", "")
            if self.is_custom_anthropic:
                model = f"anthropic/{base_model}"
            else:
                # Default to openai/ for OpenAI-compatible endpoints
                if not base_model.startswith("openai/"):
                    model = f"openai/{base_model}"
                else:
                    model = base_model

        # For volcengine, use OpenAI-compatible format
        if model.startswith("volcengine/"):
            model = model.replace("volcengine/", "openai/")

        # For Ollama using OpenAI-compatible API (port 11434 with /v1 endpoint)
        # Use 'openai/' prefix so LiteLLM uses the OpenAI-compatible API, not native Ollama API
        if self.is_ollama and not model.startswith("ollama/") and not model.startswith("openai/"):
            model = f"openai/{model}"

        # For OpenRouter, prefix model name if not already prefixed
        if self.is_openrouter and not model.startswith("openrouter/"):
            model = f"openrouter/{model}"

        # For Zhipu/Z.ai, ensure prefix is present (skip if already ollama/openai/)
        # Handle cases like "glm-4.7-flash" -> "zai/glm-4.7-flash"
        if ("glm" in model.lower() or "zhipu" in model.lower()) and not (
            model.startswith("zhipu/")
            or model.startswith("zai/")
            or model.startswith("openrouter/")
            or model.startswith("openai/")
            or model.startswith("ollama/")
        ):
            model = f"zai/{model}"

        # For vLLM, use hosted_vllm/ prefix per LiteLLM docs (skip if already ollama/openai/)
        # Don't add hosted_vllm/ if model already has openai/ prefix (e.g., for Alibaba DashScope)
        if self.is_vllm and not self.is_volcengine and not self.is_ollama:
            if not model.startswith("openai/"):
                model = f"hosted_vllm/{model}"

        # For Gemini, ensure gemini/ prefix if not already present
        if "gemini" in model.lower() and not model.startswith("gemini/"):
            model = f"gemini/{model}"

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": self._sanitize_empty_content(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Pass api_base directly for custom endpoints (vLLM, etc.)
        if self.api_base:
            kwargs["api_base"] = self.api_base

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = await acompletion(**kwargs)
            return self._parse_response(response)
        except Exception as e:
            # Return error as content for graceful handling
            return LLMResponse(
                content=f"Error calling LLM: {str(e)}",
                finish_reason="error",
            )

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse LiteLLM response into our standard format."""
        choice = response.choices[0]
        message = choice.message

        tool_calls = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                # Parse arguments from JSON string if needed
                args = tc.function.arguments
                if isinstance(args, str):
                    import json

                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}

                tool_calls.append(
                    ToolCallRequest(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    )
                )

        usage = {}
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        # Extract reasoning_content for thinking models (DeepSeek-R1, Kimi, etc.)
        reasoning_content = None
        if hasattr(message, "reasoning_content"):
            reasoning_content = message.reasoning_content
        elif hasattr(message, "parsed") and hasattr(message.parsed, "reasoning_content"):
            reasoning_content = message.parsed.reasoning_content
        elif isinstance(message, dict):
            reasoning_content = message.get("reasoning_content")
        elif hasattr(choice, "message") and isinstance(choice.message, dict):
            reasoning_content = choice.message.get("reasoning_content")
        elif hasattr(response, "choices") and len(response.choices) > 0:
            first_choice = response.choices[0]
            if hasattr(first_choice, "message") and isinstance(first_choice.message, dict):
                reasoning_content = first_choice.message.get("reasoning_content")

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason or "stop",
            usage=usage,
            reasoning_content=reasoning_content,
        )

    def get_default_model(self) -> str:
        """Get the default model."""
        return self.default_model
