"""
Prompt System V2 - 提示词系统 V2 版本

支持渐进式上下文披露、钩子系统和可扩展的提示词管理。
与 PromptSystemV2 和 ContextBuilder 兼容共存。
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptSystemV2:
    """
    提示词系统 V2 版本

    特性：
    - 渐进式上下文披露
    - 钩子系统
    - 配置驱动加载
    - 缓存机制
    - 与现有系统兼容
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        workspace: Optional[Path] = None,
        config: Optional[Dict] = None,
        workspace_path: Optional[Path] = None,
    ):
        """
        初始化提示词系统 V2

        Args:
            config_path: 提示词配置文件路径
            workspace: 工作区路径
            config: 配置字典（如果已加载）
            workspace_path: 工作区路径（别名）
        """
        self.config_path = config_path or self._get_default_config_path()
        self.workspace = workspace or workspace_path or self._get_default_workspace()
        self.config = config or self._load_config(self.config_path)

        # 钩子系统
        self.hooks: Dict[str, List[Any]] = {
            "on_config_loaded": [],
            "on_prompts_loaded": [],
            "on_layer_loaded": [],
            "on_main_agent_prompt_built": [],
            "on_subagent_prompt_built": [],
            "on_prompt_ready": [],
            "on_agent_initialized": [],
            "on_agent_ready": [],
        }

        # 缓存
        self.prompts_cache: Dict[str, str] = {}
        self._cache_ttl: int = self.config.get("cache_ttl", 300)

        # 注册默认钩子
        self._register_default_hooks()

        logger.info(
            f"PromptSystemV2 initialized with config_path={self.config_path}, workspace={self.workspace}"
        )

    def _get_default_config_path(self) -> Path:
        """获取默认配置文件路径"""
        project_dir = Path(__file__).parent.parent
        return project_dir / "config" / "prompts" / "config.yaml"

    def _get_default_workspace(self) -> Path:
        """获取默认工作区路径"""
        # 查找工作区目录
        project_dir = Path(__file__).parent.parent
        if (project_dir / "workspace").exists():
            return project_dir / "workspace"
        elif (project_dir / "nanobot" / "workspace").exists():
            return project_dir / "nanobot" / "workspace"
        else:
            return project_dir / "workspace"

    def _load_config(self, config_path: Path) -> Dict:
        """加载配置文件"""
        if not config_path.exists():
            logger.warning(
                f"Prompt config file not found: {config_path}, using defaults"
            )
            return self._get_default_config()

        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "version": "1.0",
            "layers": {
                "core": {
                    "required": True,
                    "load_order": 1,
                    "files": [
                        {"path": "core/identity.md", "section": "identity"},
                        {"path": "core/soul.md", "section": "soul"},
                        {"path": "core/tools.md", "section": "tools"},
                        {"path": "core/heartbeat.md", "section": "heartbeat"},
                    ],
                },
                "workspace": {
                    "required": True,
                    "load_order": 2,
                    "files": [
                        {
                            "path": "workspace/agents.md",
                            "section": "agents",
                            "allow_override": True,
                        },
                        {
                            "path": "workspace/practices.md",
                            "section": "practices",
                            "allow_override": True,
                        },
                    ],
                },
                "user": {
                    "required": True,
                    "load_order": 3,
                    "files": [
                        {
                            "path": "user/profile.md",
                            "section": "user_profile",
                            "allow_override": True,
                        },
                        {
                            "path": "user/preferences.md",
                            "section": "preferences",
                            "allow_override": True,
                        },
                    ],
                },
                "memory": {
                    "required": False,
                    "load_order": 4,
                    "condition": "is_main_session",
                    "files": [
                        {"path": "memory/memory.md", "section": "long_term_memory"},
                        {
                            "source": "workspace",
                            "file": "MEMORY.md",
                            "section": "user_memory",
                        },
                    ],
                },
                "decisions": {
                    "required": False,
                    "load_order": 5,
                    "agent_types": ["main_agent"],
                    "files": [
                        {
                            "path": "decisions/task_analysis.md",
                            "key": "task_analysis_prompt",
                        },
                        {
                            "path": "decisions/skill_selection.md",
                            "key": "skill_selection_prompt",
                        },
                        {
                            "path": "decisions/agent_selection.md",
                            "key": "agent_selection_prompt",
                        },
                    ],
                },
            },
            "templates": {
                "main_agent": "{identity}\n\n{soul}\n\n{tools}\n\n{agents}\n\n{practices}\n\n{user_profile}\n\n{user_preferences}\n\n{long_term_memory}",
                "sub_agent": "{identity}\n\n{soul}\n\n{tools}\n\n## Task Description\n\n{task_description}\n\n## Available Tools\n{tools}\n\n## Skills\n{skills_content}\n\n## Best Practices\n{practices}\n\n## User Preferences\n{user_preferences}\n\n## Workspace\nYour workspace is at: {workspace}",
            },
        }

    # ========== 钩子系统方法 ==========

    def register_hook(self, hook_name: str, callback: Any) -> None:
        """
        注册钩子

        Args:
            hook_name: 钩子名称
            callback: 回调函数
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []

        self.hooks[hook_name].append(callback)
        logger.debug(f"Hook registered: {hook_name}")

    def unregister_hook(self, hook_name: str, callback: Any) -> None:
        """
        注销钩子
        """
        if hook_name in self.hooks and callback in self.hooks[hook_name]:
            self.hooks[hook_name].remove(callback)
            logger.debug(f"Hook unregistered: {hook_name}")

    def trigger(self, hook_name: str, **kwargs) -> None:
        """
        触发钩子

        Args:
            hook_name: 钩子名称
            **kwargs: 传递给钩子的参数
        """
        if hook_name not in self.hooks:
            logger.debug(f"No hooks registered for: {hook_name}")
            return

        logger.debug(f"Triggering hooks: {hook_name}")
        for callback in self.hooks[hook_name]:
            try:
                callback(**kwargs)
            except Exception as e:
                logger.error(f"Hook callback failed: {e}", exc_info=True)

    def _register_default_hooks(self) -> None:
        """注册默认钩子"""
        # 配置加载完成
        self.register_hook("on_config_loaded", self.on_config_loaded)
        # 提示词加载完成
        self.register_hook("on_prompts_loaded", self.on_prompts_loaded)
        # 单个层加载完成
        self.register_hook("on_layer_loaded", self.on_layer_loaded)
        # MainAgent 提示词构建完成
        self.register_hook(
            "on_main_agent_prompt_built", self.on_main_agent_prompt_built
        )
        # Subagent 提示词构建完成
        self.register_hook("on_subagent_prompt_built", self.on_subagent_prompt_built)
        # 任意提示词构建完成
        self.register_hook("on_prompt_ready", self.on_prompt_ready)
        # Agent 初始化完成
        self.register_hook("on_agent_initialized", self.on_agent_initialized)
        # Agent 准备好
        self.register_hook("on_agent_ready", self.on_agent_ready)

    # ========== 默认钩子实现 ==========

    def on_config_loaded(self, **kwargs) -> None:
        """配置加载完成后的默认处理"""
        config = kwargs.get("config", {})
        logger.info(f"PromptSystemV2 config loaded: version={config.get('version')}")

    def on_prompts_loaded(self, **kwargs) -> None:
        """所有提示词加载完成后的默认处理"""
        prompts = kwargs.get("prompts", {})
        logger.info(f"PromptSystemV2 prompts loaded: {len(prompts)} prompts loaded")

    def on_layer_loaded(self, **kwargs) -> None:
        """单个提示词层加载完成后的默认处理"""
        layer_name = kwargs.get("layer_name")
        content = kwargs.get("content", {})
        logger.debug(f"PromptSystemV2 layer loaded: {layer_name}")

    def on_main_agent_prompt_built(self, **kwargs) -> None:
        """MainAgent 提示词构建完成后的默认处理"""
        prompt = kwargs.get("prompt", "")
        sections = kwargs.get("sections", {})
        logger.info(
            f"PromptSystemV2 MainAgent prompt built: {len(prompt)} chars, {len(sections)} sections"
        )

    def on_subagent_prompt_built(self, **kwargs) -> None:
        """Subagent 提示词构建完成后的默认处理"""
        prompt = kwargs.get("prompt", "")
        logger.info(f"PromptSystemV2 Subagent prompt built: {len(prompt)} chars")

    def on_prompt_ready(self, **kwargs) -> None:
        """通用提示词构建完成后的默认处理"""
        logger.debug(f"PromptSystemV2 prompt ready")

    def on_agent_initialized(self, **kwargs) -> None:
        """Agent 初始化完成后的默认处理"""
        agent = kwargs.get("agent")
        session_key = kwargs.get("session_key")
        logger.info(f"PromptSystemV2 agent initialized: {session_key}")

    def on_agent_ready(self, **kwargs) -> None:
        """Agent 准备好后的默认处理"""
        agent = kwargs.get("agent")
        logger.info(f"PromptSystemV2 agent ready: {type(type(agent).__name__)}")

    # ========== 提示词加载方法 ==========

    def load_prompts(self, paths: Optional[List[str]] = None) -> None:
        """
        加载提示词文件

        Args:
            paths: 提示词文件路径列表，如果为 None 则使用配置的路径
        """
        # 触发配置加载钩子
        self.trigger("on_config_loaded", config=self.config)

        # 按层级加载提示词
        layers = self.config.get("layers", {})
        loaded_prompts = {}

        for layer_name, layer_config in sorted(
            layers.items(), key=lambda item: item[1].get("load_order", 999)
        ):
            # 检查条件是否满足
            condition = layer_config.get("condition")
            if condition == "is_main_session" and not self._is_main_session():
                logger.debug(f"Skipping layer {layer_name} (condition not met)")
                continue

            logger.debug(f"Loading layer: {layer_name}")
            layer_content = self._load_layer(layer_name, layer_config)
            loaded_prompts.update(layer_content)

            # 触发层加载完成钩子
            self.trigger(
                "on_layer_loaded", layer_name=layer_name, content=layer_content
            )

        # 触发提示词加载完成钩子
        self.trigger("on_prompts_loaded", prompts=loaded_prompts)

    def _load_layer(self, layer_name: str, layer_config: Dict) -> Dict[str, str]:
        """
        加载单个提示词层

        Args:
            layer_name: 层名称
            layer_config: 层配置

        Returns:
            加载的提示词内容字典
        """
        layer_content = {}

        for file_config in layer_config.get("files", []):
            file_path = file_config.get("path")
            section_name = file_config.get("section")
            allow_override = file_config.get("allow_override", False)

            # 检查是否有 workspace 覆盖
            override_content = None
            if allow_override:
                override_content = self._load_workspace_override(file_path)

            # 加载内置提示词
            builtin_content = self._load_builtin_prompt(file_path)

            # 使用覆盖内容或内置内容
            content = override_content or builtin_content

            if content:
                layer_content[section_name] = content

        return layer_content

    def _load_builtin_prompt(self, path: str) -> Optional[str]:
        """
        加载内置提示词文件

        Args:
            path: 相对于配置的文件路径

        Returns:
            提示词内容，如果不存在返回 None
        """
        # 检查 path 是否为 None
        if path is None:
            return None

        # 构建完整路径
        config_dir = self.config_path.parent
        full_path = config_dir / path

        if not full_path.exists():
            logger.debug(f"Prompt file not found: {full_path}")
            return None

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to load prompt file {full_path}: {e}")
            return None

    def _load_workspace_override(self, path: str) -> Optional[str]:
        """
        加载工作区覆盖提示词

        Args:
            path: 相对于配置的文件路径

        Returns:
            工作区中的提示词内容，如果不存在返回 None
        """
        # 检�找 workspace 中的对应文件
        workspace_file = self.workspace / path

        if not workspace_file.exists():
            return None

        try:
            with open(workspace_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(
                f"Failed to load workspace override file {workspace_file}: {e}"
            )
            return None

    def _is_main_session(self) -> bool:
        """
        判断是否是主会话

        Returns:
            是否为 main session
        """
        # 这里简化判断，实际应该从上下文获取
        # TODO: 从真实上下文判断
        return True  # 暂时返回 True，后续可以根据需要调整

    # ========== 提示词构建方法 ==========

    def build_main_agent_prompt(
        self, sections: Optional[Dict[str, str]] = None, **kwargs
    ) -> str:
        """
        构建 MainAgent 系统提示词

        Args:
            sections: 自定义的提示词部分（可选）
            **kwargs: 额外的变量

        Returns:
            完整的系统提示词字符串
        """
        # 加载提示词
        self.load_prompts()

        # 获取所有提示词（从内部缓存）
        all_sections = self.get_all_sections()

        # 提供默认值，确保所有模板变量都有值
        default_sections = {
            "identity": "",
            "soul": "",
            "tools": "",
            "agents": "",
            "practices": "",
            "user_profile": "",
            "user_preferences": "",
            "long_term_memory": "",
        }

        # 合并默认值和实际内容
        merged_sections = {**default_sections, **all_sections}

        # 合并用户提供的 sections
        if sections:
            merged_sections.update(sections)

        # 获取模板
        template = self.config.get("templates", {}).get("main_agent", "")

        # 替换变量 - 先用 merged_sections，然后用 kwargs 覆盖
        final_vars = {**merged_sections, **kwargs}
        prompt = template.format(**final_vars)

        # 触发钩子
        self.trigger("on_main_agent_prompt_built", prompt=prompt, sections=all_sections)

        return prompt

    def build_subagent_prompt(
        self,
        task_description: str,
        sections: Optional[Dict[str, str]] = None,
        skills: Optional[List[str]] = None,
        **kwargs,
    ) -> str:
        """
        构建 Subagent 系统提示词

        Args:
            task_description: 任务描述
            sections: 自定义的提示词部分（可选）
            skills: 技能列表（可选）
            **kwargs: 额外的变量

        Returns:
            完整的系统提示词字符串
        """
        # 加载核心层提示词
        core_sections = {}
        for layer_name in ["core", "workspace", "user"]:
            if layer_name in self.config.get("layers", {}):
                core_sections.update(
                    self._load_layer(layer_name, self.config["layers"][layer_name])
                )

        # 合并用户提供的 sections
        if sections:
            core_sections.update(sections)

        # 格式化技能
        skills_content = ""
        if skills:
            skills_content = "\n\n".join([f"- {skill}" for skill in skills])

        # 获取模板
        template = self.config.get("templates", {}).get("sub_agent", "")

        # 提供默认值，确保所有模板变量都有值
        default_sections = {
            "identity": "",
            "soul": "",
            "tools": "",
            "agents": "",
            "practices": "",
            "user_profile": "",
            "user_preferences": "",
            "long_term_memory": "",
        }

        # 合并默认值和实际内容
        merged_sections = {**default_sections, **core_sections}

        # 替换变量
        prompt = template.format(
            task_description=task_description,
            skills_content=skills_content,
            workspace=str(self.workspace.resolve()),
            **merged_sections,
            **kwargs,
        )

        # 触发钩子
        self.trigger("on_subagent_prompt_built", prompt=prompt)

        return prompt

    def get_all_sections(self) -> Dict[str, str]:
        """
        获取所有加载的提示词部分

        Returns:
            提示词部分字典
        """
        # 从所有层加载提示词
        all_sections = {}

        # 按顺序加载所有层
        layers = self.config.get("layers", {})
        for layer_name, layer_config in sorted(
            layers.items(), key=lambda item: item[1].get("load_order", 999)
        ):
            # 检查条件是否满足
            condition = layer_config.get("condition")
            if condition == "is_main_session" and not self._is_main_session():
                continue

            # 加载该层的所有文件
            layer_content = self._load_layer(layer_name, layer_config)
            all_sections.update(layer_content)

        # 更新缓存
        self.prompts_cache.update(all_sections)

        return all_sections

    # ========== 工具方法 ==========

    def update_config(self, config: Dict) -> None:
        """
        更新配置

        Args:
            config: 新的配置字典
        """
        self.config = config
        logger.info("PromptSystemV2 config updated")

    def get_config(self) -> Dict:
        """
        获取当前配置

        Returns:
            当前配置字典
        """
        return self.config.copy()

    def get_stats(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            "prompts_loaded": len(self.prompts_cache),
            "hooks_registered": {
                name: len(callbacks) for name, callbacks in self.hooks.items()
            },
            "cache_ttl": self._cache_ttl,
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        self.prompts_cache.clear()
        logger.info("PromptSystemV2 cache cleared")


# 全局实例（延迟初始化）
_prompt_system_v2_instance: Optional[PromptSystemV2] = None


def get_prompt_system_v2(
    config_path: Optional[Path] = None, workspace: Optional[Path] = None
) -> PromptSystemV2:
    """
    获取 PromptSystemV2 实例（单例模式）

    Args:
        config_path: 配置文件路径
        workspace: 工作区路径

    Returns:
        PromptSystemV2 实例
    """
    global _prompt_system_v2_instance

    if _prompt_system_v2_instance is None:
        _prompt_system_v2_instance = PromptSystemV2(
            config_path=config_path, workspace=workspace
        )

    return _prompt_system_v2_instance
