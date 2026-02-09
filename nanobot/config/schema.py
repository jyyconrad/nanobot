"""Configuration schema using Pydantic."""

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class WhatsAppConfig(BaseModel):
    """WhatsApp channel configuration."""

    enabled: bool = False
    bridge_url: str = "ws://localhost:3001"
    allow_from: list[str] = Field(default_factory=list)  # Allowed phone numbers


class TelegramConfig(BaseModel):
    """Telegram channel configuration."""

    enabled: bool = False
    token: str = ""  # Bot token from @BotFather
    allow_from: list[str] = Field(default_factory=list)  # Allowed user IDs or usernames
    proxy: str | None = (
        None  # HTTP/SOCKS5 proxy URL, e.g. "http://127.0.0.1:7890" or "socks5://127.0.0.1:1080"
    )


class FeishuConfig(BaseModel):
    """Feishu/Lark channel configuration using WebSocket long connection."""

    enabled: bool = False
    app_id: str = ""  # App ID from Feishu Open Platform
    app_secret: str = ""  # App Secret from Feishu Open Platform
    encrypt_key: str = ""  # Encrypt Key for event subscription (optional)
    verification_token: str = ""  # Verification Token for event subscription (optional)
    allow_from: list[str] = Field(default_factory=list)  # Allowed user open_ids


class ChannelsConfig(BaseModel):
    """Configuration for chat channels."""

    whatsapp: WhatsAppConfig = Field(default_factory=WhatsAppConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    feishu: FeishuConfig = Field(default_factory=FeishuConfig)


class AgentDefaults(BaseModel):
    """Default agent configuration."""

    workspace: str = "~/.nanobot/workspace"
    model: str = "anthropic/claude-opus-4-5"
    max_tokens: int = 8192
    temperature: float = 0.7
    max_tool_iterations: int = 20


class AgentsConfig(BaseModel):
    """Agent configuration."""

    defaults: AgentDefaults = Field(default_factory=AgentDefaults)
    main_agent: Optional[Dict[str, Any]] = Field(default_factory=dict)
    subagents: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProviderConfig(BaseModel):
    """LLM provider configuration."""

    api_key: str = ""
    api_base: str | None = None


class ProvidersConfig(BaseModel):
    """Configuration for LLM providers."""

    anthropic: ProviderConfig = Field(default_factory=ProviderConfig)
    openai: ProviderConfig = Field(default_factory=ProviderConfig)
    openrouter: ProviderConfig = Field(default_factory=ProviderConfig)
    deepseek: ProviderConfig = Field(default_factory=ProviderConfig)
    groq: ProviderConfig = Field(default_factory=ProviderConfig)
    zhipu: ProviderConfig = Field(default_factory=ProviderConfig)
    vllm: ProviderConfig = Field(default_factory=ProviderConfig)
    gemini: ProviderConfig = Field(default_factory=ProviderConfig)
    volcengine: ProviderConfig = Field(default_factory=ProviderConfig)


class GatewayConfig(BaseModel):
    """Gateway/server configuration."""

    host: str = "0.0.0.0"
    port: int = 9910


class WebSearchConfig(BaseModel):
    """Web search tool configuration."""

    api_key: str = ""  # Brave Search API key
    max_results: int = 5


class WebToolsConfig(BaseModel):
    """Web tools configuration."""

    search: WebSearchConfig = Field(default_factory=WebSearchConfig)


class ExecToolConfig(BaseModel):
    """Shell exec tool configuration."""

    timeout: int = 60
    restrict_to_workspace: bool = False  # If true, block commands accessing paths outside workspace


class ToolsConfig(BaseModel):
    """Tools configuration."""

    web: WebToolsConfig = Field(default_factory=WebToolsConfig)
    exec: ExecToolConfig = Field(default_factory=ExecToolConfig)


class TaskMonitoringConfig(BaseModel):
    """Task monitoring configuration."""

    enabled: bool = True
    check_interval: int = 3600  # seconds
    max_task_duration: int = 86400  # seconds
    auto_cleanup: bool = True
    cleanup_delay: int = 3600  # seconds


class CronJobConfig(BaseModel):
    """Cron job configuration."""

    enabled: bool = True
    config_path: str = "~/.nanobot/cron-job-config.json"
    log_level: str = "INFO"


class OpencodeSkillsConfig(BaseModel):
    """Opencode skills configuration."""

    enabled: bool = False  # 是否启用 opencode skills
    source_dir: str = "~/.config/opencode/skills"  # opencode skills 源目录
    skills: list[str] = Field(
        default_factory=lambda: ["code-review", "code-refactoring", "backend-dev"]
    )  # 要加载的 skills 列表


class OpencodeCommandsConfig(BaseModel):
    """Opencode commands configuration."""

    enabled: bool = False  # 是否启用 opencode commands
    source_dir: str = "~/.config/opencode/commands"  # opencode commands 源目录
    commands: list[str] = Field(
        default_factory=lambda: ["review", "optimize", "test", "fix", "commit", "debug"]
    )  # 要加载的 commands 列表


class OpencodeAgentsConfig(BaseModel):
    """Opencode agents configuration."""

    enabled: bool = False  # 是否启用 opencode agents
    source_dir: str = "~/.config/opencode/agents"  # opencode agents 源目录
    agents: list[str] = Field(
        default_factory=lambda: ["code-reviewer", "frontend-developer", "backend-developer"]
    )  # 要加载的 agents 列表


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    name: str = Field(..., description="MCP server name")
    url: str = Field(..., description="MCP server URL")
    auth_token: Optional[str] = Field(None, description="Authentication token")
    auth_type: str = Field("bearer", description="Authentication type (bearer, basic, etc.)")


class OpencodeConfig(BaseModel):
    """Opencode integration configuration."""

    enabled: bool = False  # 是否启用 opencode 集成
    skills: OpencodeSkillsConfig = Field(default_factory=OpencodeSkillsConfig)
    commands: OpencodeCommandsConfig = Field(default_factory=OpencodeCommandsConfig)
    agents: OpencodeAgentsConfig = Field(default_factory=OpencodeAgentsConfig)
    mcp_servers: list[MCPServerConfig] = Field(default_factory=list, description="MCP server configurations")


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""

    task: TaskMonitoringConfig = Field(default_factory=TaskMonitoringConfig)
    cron: CronJobConfig = Field(default_factory=CronJobConfig)


class Config(BaseSettings):
    """Root configuration for nanobot."""

    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    opencode: OpencodeConfig = Field(default_factory=OpencodeConfig)

    @classmethod
    def load(cls, config_path: str | None = None) -> "Config":
        """Load configuration from file or environment variables."""
        if config_path:
            import yaml

            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)

            # 兼容性处理：旧格式配置迁移
            migrated_data = cls._migrate_config(config_data)
            return cls(**migrated_data)
        return cls()

    @classmethod
    def _migrate_config(cls, config_data: dict) -> dict:
        """迁移旧格式配置到新格式"""
        migrated = {}

        # 处理旧格式的 agent 配置
        if "agent" in config_data:
            migrated["agents"] = {"defaults": {}}
            if "name" in config_data["agent"]:
                # 旧格式的 agent.name 没有直接对应的新字段，我们可以忽略或放在 main_agent 中
                pass
            if "version" in config_data["agent"]:
                pass
            if "max_history" in config_data["agent"]:
                pass

        # 处理旧格式的 llm 配置
        if "llm" in config_data:
            if "agents" not in migrated:
                migrated["agents"] = {"defaults": {}}
            if "model" in config_data["llm"]:
                migrated["agents"]["defaults"]["model"] = config_data["llm"]["model"]
            if "temperature" in config_data["llm"]:
                migrated["agents"]["defaults"]["temperature"] = config_data["llm"]["temperature"]

        # 处理旧格式的 database 配置
        if "database" in config_data:
            pass  # 新格式中没有直接的 database 配置

        # 处理 legacy 格式的 bot 配置
        if "bot" in config_data:
            if "agents" not in migrated:
                migrated["agents"] = {"defaults": {}}
            if "name" in config_data["bot"]:
                pass
            if "max_memory" in config_data["bot"]:
                pass

        # 处理 legacy 格式的 ai 配置
        if "ai" in config_data:
            if "agents" not in migrated:
                migrated["agents"] = {"defaults": {}}
            if "engine" in config_data["ai"]:
                migrated["agents"]["defaults"]["model"] = config_data["ai"]["engine"]
            if "temp" in config_data["ai"]:
                migrated["agents"]["defaults"]["temperature"] = config_data["ai"]["temp"]

        # 处理 legacy 格式的 db 配置
        if "db" in config_data:
            pass

        # 保留新格式的配置字段
        for key in ["agents", "channels", "providers", "gateway", "tools", "monitoring"]:
            if key in config_data and key not in migrated:
                migrated[key] = config_data[key]

        return migrated

    @property
    def workspace_path(self) -> Path:
        """Get expanded workspace path."""
        return Path(self.agents.defaults.workspace).expanduser()

    def get_opencode_skills_config(self) -> dict | None:
        """Get opencode skills configuration if enabled."""
        if not self.opencode.enabled:
            return None
        if not self.opencode.skills.enabled:
            return None
        return {
            "enabled": True,
            "source_dir": self.opencode.skills.source_dir,
            "skills": self.opencode.skills.skills,
        }

    def get_opencode_commands_config(self) -> dict | None:
        """Get opencode commands configuration if enabled."""
        if not self.opencode.enabled:
            return None
        if not self.opencode.commands.enabled:
            return None
        return {
            "enabled": True,
            "source_dir": self.opencode.commands.source_dir,
            "commands": self.opencode.commands.commands,
        }

    def get_opencode_agents_config(self) -> dict | None:
        """Get opencode agents configuration if enabled."""
        if not self.opencode.enabled:
            return None
        if not self.opencode.agents.enabled:
            return None
        return {
            "enabled": True,
            "source_dir": self.opencode.agents.source_dir,
            "agents": self.opencode.agents.agents,
        }

    def get_opencode_mcp_config(self) -> dict | None:
        """Get opencode MCP servers configuration if enabled."""
        if not self.opencode.enabled:
            return None
        if not self.opencode.mcp_servers:
            return None
        return {
            "enabled": True,
            "mcp_servers": [
                {
                    "name": server.name,
                    "url": server.url,
                    "auth_token": server.auth_token,
                    "auth_type": server.auth_type,
                }
                for server in self.opencode.mcp_servers
            ],
        }

    def get_api_key(self) -> str | None:
        """Get API key in priority order: OpenRouter > DeepSeek > Anthropic > OpenAI > Gemini > Zhipu > Groq > vLLM > Volcengine."""
        return (
            self.providers.openrouter.api_key
            or self.providers.deepseek.api_key
            or self.providers.anthropic.api_key
            or self.providers.openai.api_key
            or self.providers.gemini.api_key
            or self.providers.zhipu.api_key
            or self.providers.groq.api_key
            or self.providers.vllm.api_key
            or self.providers.volcengine.api_key
            or None
        )

    def get_api_base(self) -> str | None:
        """Get API base URL if using OpenRouter, Zhipu, vLLM or Volcengine."""
        if self.providers.openrouter.api_key:
            return self.providers.openrouter.api_base or "https://openrouter.ai/api/v1"
        if self.providers.zhipu.api_key:
            return self.providers.zhipu.api_base
        if self.providers.vllm.api_base:
            return self.providers.vllm.api_base
        if self.providers.volcengine.api_key:
            return self.providers.volcengine.api_base
        return None

    class Config:
        env_prefix = "NANOBOT_"
        env_nested_delimiter = "__"
