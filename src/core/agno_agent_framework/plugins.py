"""
Agent Plugins

Plugin system for extending agent capabilities.
"""

from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from enum import Enum
import importlib
import inspect


class PluginStatus(str, Enum):
    """Plugin status enumeration."""
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class PluginHook(BaseModel):
    """Plugin hook definition."""
    hook_name: str
    callback: Callable
    priority: int = 0  # Higher priority executes first

    class Config:
        arbitrary_types_allowed = True


class AgentPlugin(BaseModel, ABC):
    """
    Base class for agent plugins.

    Plugins extend agent functionality by providing
    hooks, tools, and custom behaviors.
    """

    plugin_id: str
    name: str
    version: str = "1.0.0"
    description: str = ""

    status: PluginStatus = PluginStatus.LOADED

    # Plugin capabilities
    hooks: List[PluginHook] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)  # Tool IDs provided by plugin
    dependencies: List[str] = Field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def initialize(self, agent: Any) -> None:
        """
        Initialize the plugin.

        Args:
            agent: Agent instance
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass

    def register_hook(
        self,
        hook_name: str,
        callback: Callable,
        priority: int = 0
    ) -> None:
        """
        Register a plugin hook.

        Args:
            hook_name: Name of the hook
            callback: Callback function
            priority: Hook priority
        """
        hook = PluginHook(
            hook_name=hook_name,
            callback=callback,
            priority=priority
        )
        self.hooks.append(hook)

    def on_task_start(self, task: Any) -> Optional[Any]:
        """
        Hook called when a task starts.

        Args:
            task: Task being started

        Returns:
            Optional modified task
        """
        return None

    def on_task_complete(self, task: Any, result: Any) -> Optional[Any]:
        """
        Hook called when a task completes.

        Args:
            task: Completed task
            result: Task result

        Returns:
            Optional modified result
        """
        return None

    def on_message_received(self, message: Any) -> Optional[Any]:
        """
        Hook called when a message is received.

        Args:
            message: Received message

        Returns:
            Optional modified message
        """
        return None


class PluginManager:
    """Manager for agent plugins."""

    def __init__(self):
        """Initialize plugin manager."""
        self._plugins: Dict[str, AgentPlugin] = {}
        self._hooks: Dict[str, List[PluginHook]] = {}

    def register_plugin(
        self,
        plugin: AgentPlugin,
        agent: Optional[Any] = None
    ) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin to register
            agent: Optional agent instance for initialization
        """
        # Check dependencies
        for dep in plugin.dependencies:
            if dep not in self._plugins:
                raise ValueError(f"Plugin dependency '{dep}' not found")

        # Initialize plugin
        if agent:
            try:
                plugin.initialize(agent)
                plugin.status = PluginStatus.ACTIVE
            except Exception as e:
                plugin.status = PluginStatus.ERROR
                raise RuntimeError(f"Failed to initialize plugin {plugin.name}: {e}")

        self._plugins[plugin.plugin_id] = plugin

        # Register hooks
        for hook in plugin.hooks:
            if hook.hook_name not in self._hooks:
                self._hooks[hook.hook_name] = []
            self._hooks[hook.hook_name].append(hook)
            # Sort by priority
            self._hooks[hook.hook_name].sort(key=lambda h: h.priority, reverse=True)

    def load_plugin_from_module(
        self,
        module_path: str,
        plugin_class_name: str,
        agent: Optional[Any] = None
    ) -> AgentPlugin:
        """
        Load a plugin from a Python module.

        Args:
            module_path: Path to Python module
            plugin_class_name: Name of plugin class
            agent: Optional agent instance

        Returns:
            Loaded plugin
        """
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, plugin_class_name)
            plugin = plugin_class()

            self.register_plugin(plugin, agent)
            return plugin
        except Exception as e:
            raise RuntimeError(f"Failed to load plugin from {module_path}: {e}")

    def get_plugin(self, plugin_id: str) -> Optional[AgentPlugin]:
        """
        Get a plugin by ID.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Plugin or None
        """
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> List[AgentPlugin]:
        """
        List all registered plugins.

        Returns:
            List of plugins
        """
        return list(self._plugins.values())

    def execute_hooks(
        self,
        hook_name: str,
        *args,
        **kwargs
    ) -> List[Any]:
        """
        Execute all hooks for a hook name.

        Args:
            hook_name: Name of hook to execute
            *args: Hook arguments
            **kwargs: Hook keyword arguments

        Returns:
            List of hook results
        """
        results = []

        if hook_name in self._hooks:
            for hook in self._hooks[hook_name]:
                try:
                    result = hook.callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    # Log error but continue with other hooks
                    print(f"Hook {hook_name} failed: {e}")

        return results

    def unregister_plugin(self, plugin_id: str) -> None:
        """
        Unregister a plugin.

        Args:
            plugin_id: Plugin identifier
        """
        plugin = self._plugins.get(plugin_id)
        if plugin:
            plugin.cleanup()
            plugin.status = PluginStatus.INACTIVE

            # Remove hooks
            for hook in plugin.hooks:
                if hook.hook_name in self._hooks:
                    self._hooks[hook.hook_name] = [
                        h for h in self._hooks[hook.hook_name]
                        if h not in plugin.hooks
                    ]

            self._plugins.pop(plugin_id, None)


class ExamplePlugin(AgentPlugin):
    """Example plugin implementation."""

    def __init__(self):
        """Initialize example plugin."""
        import uuid
        super().__init__(
            plugin_id=str(uuid.uuid4()),
            name="ExamplePlugin",
            description="Example plugin for demonstration"
        )

    def initialize(self, agent: Any) -> None:
        """Initialize the plugin."""
        self.status = PluginStatus.ACTIVE

    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        self.status = PluginStatus.INACTIVE

