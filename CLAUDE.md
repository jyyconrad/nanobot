# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Nanobot is a lightweight Python AI Agent framework built on the Agno framework. It uses a MainAgent + Subagent architecture for parallel task execution, with support for multiple LLM providers via LiteLLM.

- **Language**: Python 3.11+
- **Package Name**: `nanobot-ai` (PyPI)
- **Current Version**: v0.2.1
- **Entry Point**: `nanobot` CLI command

## Build, Lint, and Test Commands

### Project Setup

```bash
# Install in development mode (includes all dev dependencies)
pip install -e ".[dev]"

# Install production dependencies only
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

# Run with coverage report (generates htmlcov/ directory)
pytest --cov=nanobot --cov-report=html

# Run with verbose output
pytest -v
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
# Build package (creates dist/ directory with wheel and sdist)
python -m build

# Build wheel only
python -m build --wheel

# Build sdist only
python -m build --sdist
```

## High-Level Architecture

### MainAgent + Subagent Architecture

The system follows a hierarchical agent pattern:

1. **MainAgent** (`nanobot/agent/loop.py`): Central orchestrator that receives user messages, coordinates subagents, and manages the overall conversation flow.

2. **Subagents** (`nanobot/agent/subagent/`): Specialized agents spawned by MainAgent for parallel task execution. Each subagent handles a specific task and reports back.

3. **SubagentManager** (`nanobot/agent/subagent/manager.py`): Manages the lifecycle of subagents - creation, monitoring, and termination.

### Key Architectural Components

```
Gateway (nanobot/api/gateway.py)
    ↓
AgentLoop (nanobot/agent/loop.py)
    ↓
MainAgent → Router → Planner → Decision
    ↓
SubagentManager → Subagent Pool
    ↓
Tools / LLM Providers
```

1. **Gateway** (`nanobot/api/gateway.py`): FastAPI-based HTTP/WebSocket server that receives messages from external sources (CLI, Telegram, WhatsApp, etc.) and routes them to the AgentLoop.

2. **Router** (`nanobot/agent/intent/router.py`): Analyzes incoming messages and determines the appropriate handling path (direct response, task planning, skill invocation, etc.).

3. **Planner** (`nanobot/agent/planner/`): Breaks down complex tasks into subtasks with dependency management and execution ordering.

4. **Decision Maker** (`nanobot/agent/decision/`): Evaluates when to ask users for clarification vs. making autonomous decisions.

5. **Context Manager** (`nanobot/agent/memory/context.py`): Handles context window management, compression, and memory retrieval.

### Tool System (MCP)

Tools are implemented using the Model Context Protocol (MCP):

- **Built-in Tools** (`nanobot/agent/tools/`): File operations, shell execution, web search/fetch, message sending.
- **MCP Integration** (`nanobot/agent/mcp/`): Client/server implementation for external tool providers.
- **Skill System** (`nanobot/skills/`): Higher-level capabilities composed of multiple tools (GitHub operations, code analysis, etc.).

### LLM Provider Architecture

The system uses LiteLLM for unified access to multiple LLM providers (`nanobot/providers/`):

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- OpenRouter (aggregated access)
- Azure OpenAI
- Google (Gemini)
- Local models via vLLM

Configuration is managed via `~/.nanobot/config.json` or environment variables.

## Development Workflow

### CLI Commands

The `nanobot` CLI provides these main commands:

```bash
# Initialize configuration and workspace
nanobot onboard

# Start the gateway server
nanobot gateway --port 9910

# Interact with the agent (single message)
nanobot agent -m "Hello, help me review code"

# Interactive agent mode
nanobot agent

# Run in development mode (with hot reload)
nanobot run --dev
```

### Project Structure

```
nanobot/                    # Core framework code
├── nanobot/               # Main package
│   ├── agent/             # Agent system (loop, subagents, planning)
│   ├── api/               # Gateway and HTTP/WebSocket API
│   ├── bus/               # Message bus for inter-component communication
│   ├── channels/          # Communication channels (Telegram, WhatsApp, Feishu)
│   ├── cli/               # Command-line interface
│   ├── commands/          # Built-in commands (commit, review, test, etc.)
│   ├── config/            # Configuration management (Pydantic-based)
│   ├── cron/              # Scheduled tasks (cron jobs)
│   ├── heartbeat/         # Heartbeat service for health monitoring
│   ├── monitor/           # Progress tracking and monitoring
│   ├── providers/         # LLM provider abstractions (LiteLLM-based)
│   ├── session/           # Session management
│   ├── skills/            # Skill definitions and loading
│   └── utils/             # Utility functions
├── tests/                 # Test suite
├── docs/                  # Documentation
├── scripts/               # Helper scripts
├── config/                # Configuration templates
└── skills/                # Custom skill implementations
```

### Key Files

- `nanobot/__init__.py`: Package version and exports
- `nanobot/__main__.py`: Entry point for `python -m nanobot`
- `nanobot/cli/commands.py`: CLI command definitions
- `nanobot/agent/loop.py`: Core agent loop implementation
- `nanobot/api/gateway.py`: FastAPI gateway server
- `pyproject.toml`: Project metadata and dependencies

## Testing Guidelines

- Tests use `pytest` with `pytest-asyncio` for async support
- Async test functions should use `@pytest.mark.asyncio` decorator
- Aim for 80%+ coverage on critical paths
- Use fixtures for test setup/teardown
- Mirror the directory structure of the source code in `tests/`

## Code Style

- Python 3.11+ features encouraged (union types with `|`, match statements)
- Line length: 100 characters (enforced by ruff)
- Import order: stdlib, third-party, local (separated by blank lines)
- Use Google-style docstrings
- Use `loguru` for logging
- Use Pydantic for data validation
