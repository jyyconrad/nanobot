# Nanobot Agent Instructions

## Build / Lint / Test Commands

### Project Setup
```bash
# Install in development mode
pip install -e ".[dev]"

# Install dependencies only
pip install -e .
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_context_expander.py

# Run specific test class
pytest tests/test_context_expander.py::TestContextExpander

# Run single test method
pytest tests/test_context_expander.py::TestContextExpander::test_expand_with_task_type

# Run with coverage
pytest --cov=nanobot --cov-report=html

# Run with verbose output
pytest -v

# Run async tests only
pytest -k "asyncio"
```

### Linting and Formatting
```bash
# Run ruff linter
ruff check .

# Run ruff formatter
ruff format .

# Fix auto-fixable issues
ruff check --fix .

# Check specific files
ruff check nanobot/agent/subagent/manager.py
```

### Build Commands
```bash
# Build package
python -m build

# Build wheel only
python -m build --wheel

# Build sdist only
python -m build --sdist
```

---

## Code Style Guidelines

### Python Version
- Target: Python 3.11+
- Use modern Python 3.11+ syntax (e.g., `str | None` instead of `Optional[str]`)

### Line Length
- Max: 100 characters
- Enforced by ruff

### Imports
Order imports with blank lines between groups:
```python
# Standard library imports
import asyncio
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
import httpx
from loguru import logger
from pydantic import BaseModel

# Local imports
from nanobot.agent.task import Task, TaskStatus
from nanobot.utils.helpers import get_workspace_path
```

### Type Hints
- Use modern type hint syntax (Python 3.11+):
```python
# Preferred
def process_data(data: str | None) -> list[str: str]:
    ...

# Alternative for older Python
def process_data(data: Optional[str]) -> List[str]:
    ...
```

### Naming Conventions
- **Classes**: PascalCase (`SubagentManager`, `ProgressTracker`)
- **Functions/Methods**: snake_case (`create_subagent`, `track_progress`)
- **Variables**: snake_case (`task_id`, `progress_history`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Private members**: class._snake_case (`self._task_manager`)

### Docstrings
Use Google-style docstrings:
```python
def create_subagent(self, task: str) -> str:
    """
    Create a new Subagent.

    Args:
        task: Task description

    Returns:
        Subagent instance ID

    Raises:
        ValueError: If task is invalid
    """
```

### Error Handling
- Use try/except with specific exceptions
- Log errors using loguru:
```python
from loguru import logger

try:
    result = await some_async_operation()
except ValueError as e:
    logger.error(f"Invalid input: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Handle or re-raise appropriately
```

### Async/Await
- Always use `async def` for async functions
- Use `await` for all async calls
- Mark async test functions with `@pytest.mark.asyncio`:
```python
@pytest.mark.asyncio
async def test_async_function(self):
    result = await async_operation()
    assert result is not None
```

### Data Validation
- Use Pydantic models for data structures:
```python
from pydantic import BaseModel, Field

class TaskConfig(BaseModel):
    """Task configuration."""
    task_id: str
    description: str
    priority: int = Field(default=1, ge=1)
```

### Logging
- Use loguru for all logging:
```python
from loguru import logger

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Testing
- Use pytest for all tests
- Use fixtures for setup/teardown:
```python
@pytest.fixture
def manager():
    """Create a manager instance for testing."""
    return SubagentManager()
```
- Follow arrange-act-assert pattern
- Write descriptive test names

### File Organization
- Keep files focused and small (200-400 lines max)
- One class per file preferred
- Use __init__.py for package exports
- Place tests in mirror directory structure under `tests/`

### Dependencies
- Check existing codebase before adding new dependencies
- Prefer using existing libraries (e.g., httpx over requests)
- Update pyproject.toml when adding new dependencies

### Git Commit Guidelines
- Use conventional commits:
  - `feat:` - New feature
  - `fix:` - Bug fix
  - `refactor:` - Code refactoring
  - `docs:` - Documentation
  - `test:` - Tests
  - `chore:` - Maintenance

---

## Project-Specific Notes

### Core Architecture
- **Agent System**: Main agent + subagents for parallel task execution
- **Context Management**: Compression and expansion for efficient context handling
- **Skill System**: Dynamic skill loading based on task types
- **Tool Integration**: MCP (Model Context Protocol) for tool access

### Key Modules
- `nanobot/agent/`: Core agent logic (main agent, subagents, task management)
- `nanobot/config/`: Configuration handling with Pydantic
- `nanobot/channels/`: Communication channels (Telegram, WhatsApp, Feishu)
- `nanobot/monitor/`: Progress tracking and monitoring
- `nanobot/skills/`: Skill definitions and loading

### Testing Focus
- Test async functions with pytest-asyncio
- Test Pydantic model validation
- Test error handling paths
- Aim for 80%+ coverage on critical paths

### Performance Considerations
- Use async/await for I/O operations
- Cache frequently accessed data
- Be mindful of context size (use compression for large contexts)
