# Opencode Integration Design Document for Nanobot

## Executive Summary

This document outlines the integration of Opencode's advanced skill/agent/command architecture into Nanobot, creating a hybrid system that combines Nanobot's lightweight core with Opencode's sophisticated multi-expert workflows.

## Current System Analysis

### Nanobot Architecture (Current)

**Strengths:**
- Ultra-lightweight (~4,000 lines)
- Fast startup and low resource usage
- Clean, modular design
- Multi-channel support (Telegram, WhatsApp, Feishu)
- Tool-based extensible architecture

**Current Components:**
- `AgentLoop`: Core processing engine
- `Tool`: Base class for tools
- `SkillsLoader`: Loads markdown-based skills
- `MessageBus`: Event-based communication
- `SessionManager`: Conversation state management
- `LLMProvider`: Multi-provider abstraction

### Opencode Architecture (Reference)

**Strengths:**
- Expert-driven design (agents, skills, commands)
- Multi-expert orchestration
- Comprehensive testing workflows
- Rich UI/UX patterns
- Advanced code review and security patterns

**Key Patterns:**
- **Skills**: Specialized capabilities with frontmatter metadata
- **Agents**: Context-aware specialists with deep expertise
- **Commands**: Quick actions for common tasks
- **MCP Integration**: External tool connectivity

## Proposed Integration Architecture

### Core Principles

1. **Maintain Lightweight Base**: Keep Nanobot's 4,000-line core intact
2. **Progressive Enhancement**: Add Opencode patterns as optional modules
3. **Backward Compatible**: Existing tools/skills continue to work
4. **Expert-Driven**: Introduce specialist agents for complex tasks

### New Architecture Layers

```
┌─────────────────────────────────────────────────┐
│           Opencode Enhancement Layer             │
│  (Optional - Loaded on-demand)                   │
├─────────────────────────────────────────────────┤
│  • Expert Agents (code-reviewer, architect...) │
│  • Opencode Skills (security, frontend...)      │
│  • Command Handlers (/plan, /review, /debug)   │
│  • MCP Server Integration                       │
└─────────────────────────────────────────────────┘
            ↓ Uses
┌─────────────────────────────────────────────────┐
│           Nanobot Core Layer                    │
│  (Always present - lightweight)                 │
├─────────────────────────────────────────────────┤
│  • AgentLoop (enhanced with expert routing)    │
│  • Tool Registry (backward compatible)          │
│  • Skills Loader (extended metadata)           │
│  • Message Bus (event-based)                    │
│  • Session Manager (stateful conversations)     │
└─────────────────────────────────────────────────┘
```

## Detailed Design

### 1. Enhanced Skills System

**Current Nanobot Skills:**
- Simple markdown files with frontmatter
- Loaded as text into context
- Progressive loading via XML summary

**Enhanced Skills (Opencode Pattern):**

```python
# nanobot/skills/enhanced/skill.py
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

class SkillType(Enum):
    CORE = "core"           # Always loaded
    EXPERT = "expert"       # Loaded when needed
    FRAGMENT = "fragment"   # Part of larger workflow

@dataclass
class SkillMetadata:
    name: str
    description: str
    type: SkillType
    requires: list[str]    # Required tools/providers
    triggers: list[str]     # When to auto-load
    conflicts: list[str]    # Skills to exclude
    
    # Opencode extensions
    agent: str | None = None      # Associated expert agent
    workflow: str | None = None   # Workflow participation
    mcp_servers: list[str] = None # Required MCP servers

class EnhancedSkillsLoader(SkillsLoader):
    """Extended skills loader with Opencode features."""
    
    def __init__(self, workspace: Path, bus: MessageBus):
        super().__init__(workspace)
        self.bus = bus
        self._skill_cache: dict[str, SkillMetadata] = {}
    
    def load_skill_with_metadata(self, name: str) -> tuple[str, SkillMetadata | None]:
        """Load skill content and parse enhanced metadata."""
        content = self.load_skill(name)
        if not content:
            return "", None
        
        metadata = self._parse_opencode_metadata(content)
        return content, metadata
    
    def should_load_on_trigger(self, skill: str, message: str) -> bool:
        """Determine if skill should auto-load based on triggers."""
        meta = self._skill_cache.get(skill)
        if not meta:
            return False
        
        for trigger in meta.triggers:
            if trigger.lower() in message.lower():
                return True
        return False
    
    def get_conflicting_skills(self, skill: str) -> list[str]:
        """Get skills that conflict with given skill."""
        meta = self._skill_cache.get(skill)
        return meta.conflicts if meta else {b}
```

**Opencode Skills Integration:**

```yaml
# nanobot/skills/security-review/SKILL.md
---
name: security-review
description: Security-first development patterns for authentication, input handling, and data protection
type: expert
agent: security-reviewer
triggers:
  - "security"
  - "authentication"
  - "vulnerability"
  - "OWASP"
conflicts: []
mcp_servers: []
requires:
  tools: ["web", "filesystem"]
---

# Security Review Skill Implementation
# ... (skill content follows)
```

### 2. Expert Agent System

**Concept:**
Expert agents are specialized LLM contexts trained/hinted for specific domains. They provide deep expertise beyond general-purpose capabilities.

```python
# nanobot/agent/experts/base.py
from abc import ABC, abstractmethod
from typing import Any

class ExpertAgent(ABC):
    """
    Base class for expert agents.
    
    Expert agents provide specialized knowledge and workflows
    for specific domains (security, frontend, backend, etc.).
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Expert agent name."""
        pass
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt defining expert's expertise."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of expert's capabilities."""
        pass
    
    @abstractmethod
    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze situation and provide expert guidance."""
        pass
    
    @property
    def requires_mcp_servers(self) -> list[str]:
        """MCP servers required by this expert."""
        return []
    
    @property
    def requires_skills(self) -> list[str]:
        """Skills required by this expert."""
        return []

class SecurityReviewer(ExpertAgent):
    """Security expert agent for vulnerability analysis."""
    
    @property
    def name(self) -> str:
        return "security-reviewer"
    
    @property
    def system_prompt(self) -> str:
        return """
You are a security expert specializing in:
- OWASP Top 10 vulnerabilities
- Secure coding practices
- Threat modeling
- Authentication and authorization
- Input validation and sanitization
- Cryptographic best practices

When analyzing code or designs:
1. Identify security vulnerabilities
2. Assess risk severity (Critical/High/Medium/Low)
3. Provide remediation steps
4. Suggest secure alternatives
5. Reference relevant security standards
"""
    
    @property
    def description(self) -> str:
        return "Security expert for vulnerability analysis and secure development"
    
    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze code for security issues."""
        # Implementation details...
        pass
    
    @property
    def requires_skills(self) -> list[str]:
        return ["security-review", "web"]
```

**Expert Agent Registry:**

```python
# nanobot/agent/experts/registry.py
from typing import Any

class ExpertAgentRegistry:
    """Registry for expert agents."""
    
    def __init__(self):
        self._experts: dict[str, ExpertAgent] = {}
        self._register_builtin_experts()
    
    def _register_builtin_experts(self):
        """Register built-in expert agents."""
        from nanobot.agent.experts.security import SecurityReviewer
        from nanobot.agent.experts.code_review import CodeReviewer
        from nanobot.agent.experts.frontend import FrontendExpert
        from nanobot.agent.experts.backend import BackendExpert
        
        self.register(SecurityReviewer())
        self.register(CodeReviewer())
        self.register(FrontendExpert())
        self.register(BackendExpert())
    
    def register(self, expert: ExpertAgent):
        """Register an expert agent."""
        self._experts[expert.name] = expert
    
    def get(self, name: str) -> ExpertAgent | None:
        """Get expert agent by name."""
        return self._experts.get(name)
    
    def list_experts(self) -> list[dict[str, str]]:
        """List all available experts."""
        return [
            {
                "name": expert.name,
                "description": expert.description,
                "requires_skills": expert.requires_skills,
                "requires_mcp": expert.requires_mcp_servers,
            }
            for expert in self._experts.values()
        ]
    
    def find_expert_for_task(self, task_description: str) -> ExpertAgent | None:
        """Find the best expert for a given task."""
        # Simple keyword matching (can be enhanced with LLM)
        keywords = task_description.lower().split()
        
        for expert in self._experts.values():
            for keyword in keywords:
                if keyword in expert.description.lower():
                    return expert
        
        return None
```

### 3. Command System

**Concept:**
Commands are quick, predefined actions for common tasks. They provide shortcuts for complex workflows.

```python
# nanobot/agent/commands/base.py
from abc import ABC, abstractmethod
from typing import Any

class Command(ABC):
    """
    Base class for commands.
    
    Commands are quick actions for common tasks like code review,
    planning, testing, etc.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Command name (e.g., 'review', 'plan')."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Command description."""
        pass
    
    @property
    def aliases(self) -> list[str]:
        """Command aliases."""
        return []
    
    @property
    def arguments(self) -> dict[str, Any]:
        """Argument schema (JSON Schema)."""
        return {}
    
    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> str:
        """Execute the command."""
        pass

class ReviewCommand(Command):
    """Code review command."""
    
    @property
    def name(self) -> str:
        return "review"
    
    @property
    def description(self) -> str:
        return "Request a code review for current changes"
    
    @property
    def aliases(self) -> list[str]:
        return ["code-review", "cr"]
    
    @property
    def arguments(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Files to review (empty = all changes)",
                }
            },
        }
    
    async def execute(self, context: dict[str, Any]) -> str:
        """Execute code review."""
        # Use security-reviewer expert
        expert = context["experts"].get("security-reviewer")
        if not expert:
            return "Security reviewer expert not available"
        
        # Analyze changes
        analysis = await expert.analyze({
            "files": context.get("args", {}).get("files", []),
            "workspace": context["workspace"],
        })
        
        return analysis.get("report", "Review completed")
```

**Command Registry:**

```python
# nanobot/agent/commands/registry.py
from nanobot.agent.commands.base import Command

class CommandRegistry:
    """Registry for commands."""
    
    def __init__(self):
        self._commands: dict[str, Command] = {}
        self._register_builtin_commands()
    
    def _register_builtin_commands(self):
        """Register built-in commands."""
        from nanobot.agent.commands.review import ReviewCommand
        from nanobot.agent.commands.plan import PlanCommand
        from nanobot.agent.commands.test import TestCommand
        from nanobot.agent.commands.debug import DebugCommand
        
        self.register(ReviewCommand())
        self.register(PlanCommand())
        self.register(TestCommand())
        self.register(DebugCommand())
    
    def register(self, command: Command):
        """Register a command."""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command
    
    def get(self, name: str) -> Command | None:
        """Get command by name or alias."""
        return self._commands.get(name)
    
    def list_commands(self) -> list[dict[str, Any]]:
        """List all available commands."""
        seen = set()
        commands = []
        
        for cmd in self._commands.values():
            if cmd.name not in seen:
                seen.add(cmd.name)
                commands.append({
                    "name": cmd.name,
                    "description": cmd.description,
                    "aliases": cmd.aliases,
                    "arguments": cmd.arguments,
                })
        
        return commands
    
    def parse_command(self, message: str) -> tuple[str | None, dict[str, Any]]:
        """Parse command from message."""
        if not message.startswith("/"):
            return None, {}
        
        parts = message[1:].split(maxsplit=1)
        command_name = parts[0]
        args_str = parts[1] if len(parts) > 1 else ""
        
        command = self.get(command_name)
        if not command:
            return None, {}
        
        # Parse arguments (simplified)
        args = {}
        if args_str:
            args = {"raw": args_str}
        
        return command_name, args
```

### 4. Enhanced Agent Loop

**Integration Point:**
The Agent Loop is enhanced to recognize and route to experts, skills, and commands.

```python
# nanobot/agent/loop.py (enhanced)
class AgentLoop:
    """
    Enhanced agent loop with Opencode integration.
    """
    
    def __init__(
        self,
        bus: MessageBus,
        provider: LLMProvider,
        workspace: Path,
        model: str | None = None,
        max_iterations: int = 20,
        brave_api_key: str | None = None,
        exec_config: "ExecToolConfig | None" = None,
    ):
        # Original initialization
        self.bus = bus
        self.provider = provider
        self.workspace = workspace
        self.model = model or provider.get_default_model()
        self.max_iterations = max_iterations
        self.brave_api_key = brave_api_key
        self.exec_config = exec_config or ExecToolConfig()
        
        self.context = ContextBuilder(workspace)
        self.sessions = SessionManager(workspace)
        self.tools = ToolRegistry()
        self.subagents = SubagentManager(
            provider=provider,
            workspace=workspace,
            bus=bus,
            model=self.model,
            brave_api_key=brave_api_key,
            exec_config=self.exec_config,
        )
        
        # Opencode enhancements
        from nanobot.agent.experts.registry import ExpertAgentRegistry
        from nanobot.agent.commands.registry import CommandRegistry
        from nanobot.agent.skills.enhanced.loader import EnhancedSkillsLoader
        
        self.experts = ExpertAgentRegistry()
        self.commands = CommandRegistry()
        self.skills = EnhancedSkillsLoader(workspace, bus)
        
        self._running = False
        self._register_default_tools()
    
    async def _process_message(self, msg: InboundMessage) -> OutboundMessage | None:
        """
        Enhanced message processing with command and expert routing.
        """
        # Check for commands first
        command_name, args = self.commands.parse_command(msg.content)
        if command_name:
            return await self._handle_command(msg, command_name, args)
        
        # Check for expert auto-routing
        expert = self.experts.find_expert_for_task(msg.content)
        if expert:
            logger.info(f"Routing to expert: {expert.name}")
            return await self._handle_expert(msg, expert)
        
        # Check for skill auto-loading
        self._load_triggered_skills(msg.content)
        
        # Original processing
        return await self._original_process_message(msg)
    
    async def _handle_command(self, msg: InboundMessage, command_name: str, args: dict[str, Any]) -> OutboundMessage:
        """Handle a command execution."""
        command = self.commands.get(command_name)
        if not command:
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"Unknown command: /{command_name}",
            )
        
        try:
            result = await command.execute({
                "args": args,
                "workspace": self.workspace,
                "experts": self.experts,
                "skills": self.skills,
                "tools": self.tools,
                "session": self.sessions.get_or_create(msg.session_key),
            })
            
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=result,
            )
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"Error executing command: {str(e)}",
            )
    
    async def _handle_expert(self, msg: InboundMessage, expert: ExpertAgent) -> OutboundMessage:
        """Handle expert agent routing."""
        try:
            # Load required skills
            for skill_name in expert.requires_skills:
                skill_content, skill_meta = self.skills.load_skill_with_metadata(skill_name)
                if skill_content:
                    self.context.add_skill(skill_name, skill_content)
            
            # Run expert analysis
            session = self.sessions.get_or_create(msg.session_key)
            context = {
                "message": msg.content,
                "history": session.get_history(),
                "workspace": str(self.workspace),
            }
            
            analysis = await expert.analyze(context)
            
            # Add expert response to context
            if "guidance" in analysis:
                session.add_message("expert", f"[{expert.name}] {analysis['guidance']}")
                self.sessions.save(session)
            
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=analysis.get("response", "Analysis completed"),
            )
        except Exception as e:
            logger.error(f"Expert processing error: {e}")
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"Error in {expert.name}: {str(e)}",
            )
    
    def _load_triggered_skills(self, message: str) -> None:
        """Auto-load skills based on triggers."""
        available_skills = self.skills.list_skills(filter_unavailable=False)
        
        for skill_info in available_skills:
            skill_name = skill_info["name"]
            if self.skills.should_load_on_trigger(skill_name, message):
                logger.info(f"Auto-loading skill: {skill_name}")
                content = self.skills.load_skill(skill_name)
                if content:
                    self.context.add_skill(skill_name, content)
```

### 5. MCP Server Integration

**Concept:**
Model Context Protocol (MCP) servers provide external tools and capabilities.

```python
# nanobot/mcp/client.py
from typing import Any, AsyncIterator

class MCPServer:
    """MCP server connection."""
    
    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.config = config
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect to MCP server."""
        # Implementation...
        pass
    
    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools from server."""
        pass
    
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the server."""
        pass

class MCPClient:
    """Client for managing MCP server connections."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._servers: dict[str, MCPServer] = {}
    
    async def load_servers(self) -> None:
        """Load and connect to configured servers."""
        # Load from config
        # Connect to each server
        pass
    
    async def get_available_tools(self) -> list[dict[str, Any]]:
        """Get all available tools from all servers."""
        tools = []
        for server in self._servers.values():
            server_tools = await server.list_tools()
            tools.extend(server_tools)
        return tools
```

## Configuration

**Enhanced Config Schema:**

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    }
  },
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5"
    },
    "experts": {
      "enabled": true,
      "auto_route": true,
      "available": [
        "security-reviewer",
        "code-reviewer",
        "frontend-expert",
        "backend-expert"
      ]
    }
  },
  "commands": {
    "enabled": true,
    "prefix": "/"
  },
  "skills": {
    "auto_load": true,
    "builtin_dir": "~/.nanobot/skills"
  },
  "mcp": {
    "enabled": true,
    "servers": {
      "filesystem": {
        "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed"]
      },
      "brave-search": {
        "command": ["npx", "-y", "@modelcontextprotocol/server-brave-search"],
        "env": {
          "BRAVE_API_KEY": "BSA-xxx"
        }
      }
    }
  },
  "tools": {
    "web": {
      "search": {
        "apiKey": "BSA-xxx"
      }
    }
  }
}
```

## Migration Strategy

### Phase 1: Foundation (Week 1-2)
- Implement `EnhancedSkillsLoader` with backward compatibility
- Add `ExpertAgent` base class and registry
- Implement `Command` base class and registry
- Update configuration schema

### Phase 2: Core Experts (Week 3-4)
- Implement `SecurityReviewer` expert
- Implement `CodeReviewer` expert
- Implement basic commands (`/review`, `/plan`)
- Add expert routing to `AgentLoop`

### Phase 3: Opencode Skills (Week 5-6)
- Port `security-review` skill
- Port `code-review` skill
- Port `tdd-workflow` skill
- Add skill auto-loading

### Phase 4: Advanced Features (Week 7-8)
- Implement MCP client
- Add frontend/backend experts
- Add more commands (`/test`, `/debug`, `/optimize`)
- Performance optimization

### Phase 5: Documentation & Testing (Week 9-10)
- Write comprehensive documentation
- Add integration tests
- Create examples and tutorials
- Performance benchmarks

## Benefits

1. **Maintained Lightweight Core**: Nanobot stays fast and small
2. **Progressive Enhancement**: Advanced features load only when needed
3. **Expert-Driven Development**: Specialized knowledge for complex tasks
4. **Quick Actions**: Commands for common workflows
5. **External Integration**: MCP servers provide limitless extensibility
6. **Backward Compatible**: Existing tools/skills continue to work

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Increased complexity | Keep core separate, optional loading |
| Performance impact | Lazy loading experts/skills |
| Breaking changes | Maintain backward compatibility |
| Resource usage | Limit concurrent experts |

## Success Metrics

- Core Nanobot remains <5,000 lines
- Startup time <2 seconds
- Memory overhead <50MB (without enhancements)
- Expert routing accuracy >85%
- Command execution time <1 second

## References

- [Opencode QUICK_START.md](.config/opencode/QUICK_START.md)
- [Backend Dev Skill](.config/opencode/skills/backend-dev/SKILL.md)
- [Frontend Design Skill](.config/opencode/skills/frontend-design/SKILL.md)
- [Code Review Skill](.config/opencode/skills/code-review/SKILL.md)
- [Frontend Developer Agent](.config/opencode/agent/frontend-developer.md)
- [Review Command](.config/opencode/commands/review.md)

## Conclusion

This design enables Nanobot to leverage Opencode's sophisticated patterns while maintaining its lightweight core. The progressive enhancement approach ensures fast startup for basic use cases while providing powerful capabilities when needed.

The modular design allows for incremental implementation and testing, reducing risk while delivering value at each phase.
