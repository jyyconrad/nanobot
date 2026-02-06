# Agent Development Guide

This guide is for AI agents working on the nanobot codebase.

## Development Commands

### Build & Install
```bash
pip install -e .              # Install in editable mode
pip install -e ".[feishu]"   # Install with Feishu support
pip install -e ".[dev]"       # Install with dev dependencies

cd bridge && npm install && npm run build  # Build WhatsApp bridge
cd bridge && npm run dev                  # Run bridge in dev mode
```

### Testing
```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest tests/test_tool_validation.py          # Run single test file
pytest tests/test_tool_validation.py::test_validate_params_missing_required  # Run single test
pytest -k "test_validate"       # Run tests matching pattern
pytest --cov=nanobot            # Run with coverage
pytest --cov=nanobot --cov-report=html  # HTML coverage report
```

### Linting & Formatting
```bash
ruff check .                    # Check code style
ruff check --fix .              # Auto-fix issues
ruff format .                   # Format code
ruff check --select I .         # Check imports only
ruff check nanobot/providers/litellm_provider.py  # Check single file
```

## Code Style Guidelines

### Python Version & Requirements
- Python >= 3.11 (tested on 3.11, 3.12)
- Node.js >= 20.0 (for WhatsApp bridge)
- Use modern Python features: type hints, dataclasses, async/await

### Imports
- Group imports in order: standard library, third-party, local
- Use absolute imports for local modules: `from nanobot.xxx import yyy`
- Avoid wildcard imports: `from module import *`
- Keep imports sorted and minimal

```python
# Correct
import asyncio
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel

from nanobot.providers.base import LLMProvider
```

### Type Hints
- Always add type hints to function signatures and class attributes
- Use `str | None` instead of `Optional[str]` (Python 3.10+ style)
- Use `list[dict[str, Any]]` instead of `List[Dict[str, Any]]`
- Annotate async functions properly: `async def function_name(...) -> ReturnType`

```python
def get_config(config_path: Path | None = None) -> Config:
    """Load configuration from file."""
    return load_config(config_path)

async def chat(messages: list[dict[str, Any]]) -> LLMResponse:
    """Send chat completion request."""
    return await provider.chat(messages)
```

### Naming Conventions
- Classes: `PascalCase` - e.g., `AgentLoop`, `LLMProvider`, `ToolRegistry`
- Functions/Methods: `snake_case` - e.g., `get_config_path`, `load_config`
- Constants: `UPPER_SNAKE_CASE` - e.g., `MAX_ITERATIONS`, `DEFAULT_MODEL`
- Private methods: `_prefix` - e.g., `_parse_response`, `_validate_params`
- Modules/files: `snake_case.py` - e.g., `agent_loop.py`, `config_loader.py`

### Code Structure
- Keep functions focused and under 50 lines when possible
- Use dataclasses for simple data structures (see `providers/base.py`)
- Use Pydantic models for configuration and validation (see `config/schema.py`)
- Use abstract base classes for provider interfaces (see `LLMProvider`)
- All I/O operations (network, disk) should be async

```python
# Use dataclass for simple structures
@dataclass
class ToolCallRequest:
    id: str
    name: str
    arguments: dict[str, Any]

# Use Pydantic for config
class AgentDefaults(BaseModel):
    model: str = "anthropic/claude-opus-4-5"
    max_tokens: int = 8192
```

### Error Handling
- Use try/except for error-prone operations
- Log errors with `logger.error()` from loguru
- Return `LLLMResponse` with error content for graceful handling
- Validate inputs early and provide clear error messages
- Never expose stack traces to end users

```python
try:
    response = await acompletion(**kwargs)
    return self._parse_response(response)
except Exception as e:
    return LLMResponse(
        content=f"Error calling LLM: {str(e)}",
        finish_reason="error",
    )
```

### Docstrings
- Use triple quotes for module/class/function docstrings
- Describe purpose, parameters, and return values
- Keep them concise and accurate

```python
def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from file or create default.

    Args:
        config_path: Optional path to config file. Uses default if not provided.

    Returns:
        Loaded configuration object.
    """
```

### Line Length & Formatting
- Maximum line length: 100 characters
- Use ruff for automatic formatting
- Run `ruff check --fix .` before committing
- No trailing whitespace

### Pydantic Models
- Use `Field(default_factory=list)` for mutable defaults
- Use `str | None` for optional fields
- Add validators in model methods when needed
- Use `model_validate()` for safe parsing

```python
class ProvidersConfig(BaseModel):
    anthropic: ProviderConfig = Field(default_factory=ProviderConfig)
    openai: ProviderConfig = Field(default_factory=ProviderConfig)
```

### Async/Await
- Use `asyncio` for concurrent operations
- All LLM calls should be async (see `LiteLLMProvider.chat`)
- Use `await` when calling async functions
- Create tasks with `asyncio.create_task()` for parallel execution

### Testing
- Write tests in `tests/` directory
- Use pytest for test framework
- Test name should describe what it validates
- Mock external dependencies (LLM, network, file system)
- Test both success and error cases
- Keep tests simple and focused

```python
def test_validate_params_missing_required() -> None:
    tool = SampleTool()
    errors = tool.validate_params({"query": "hi"})
    assert "missing required count" in "; ".join(errors)
```

### Configuration
- Config file location: `~/.nanobot/config.json`
- Workspace location: `~/.nanobot/workspace/`
- Use `Config` class from `config/schema` for type-safe config access
- Convert camelCase to snake_case in `config/loader`

### Tool Development
- Extend `Tool` base class from `agent/tools/base.py`
- Implement `name`, `description`, `parameters` properties
- Implement `async def execute(self, **kwargs) -> str`
- Use JSON Schema for parameters validation
- Register tools in `ToolRegistry`

### Agent Loop Pattern
1. Receive messages from message bus
2. Build context with history, memory, skills
3. Call LLM with tools
4. Execute tool calls
5. Send responses back via message bus

## Project Structure
- `nanobot/agent/` - Core agent logic (loop, memory, tools, subagent)
- `nanobot/providers/` - LLM provider implementations (LiteLLM, base)
- `nanobot/channels/` - Chat integrations (Telegram, WhatsApp, Feishu)
- `nanobot/config/` - Configuration loading and schema
- `nanobot/cli/` - Command-line interface commands
- `nanobot/bus/` - Message bus and event handling
- `nanobot/skills/` - Bundled agent skills
- `nanobot/session/` - Session management
- `nanobot/cron/` - Scheduled tasks
- `nanobot/heartbeat/` - Proactive wake-up
- `bridge/` - WhatsApp bridge (Node.js + TypeScript)
- `tests/` - Test files

## Key Patterns
- **Message Bus**: Use `MessageBus` for decoupled communication
- **Context Builder**: Build prompts from memory, history, skills
- **Tool Registry**: Register and validate tools before execution
- **Provider Abstraction**: Support multiple LLM providers via `LLMProvider`
- **Session Management**: Track conversation state per user/channel
