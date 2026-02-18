"""
Unit Tests for Agent Plugins

Tests plugin system functionality for agents.
"""


from unittest.mock import MagicMock, patch

import pytest

from src.core.agno_agent_framework.plugins import (
    AgentPlugin,
    ExamplePlugin,
    PluginHook,
    PluginManager,
    PluginStatus,
)


class TestPluginStatus:
    """Test PluginStatus enum."""

    def test_plugin_status_values(self):
        """Test PluginStatus enum values."""
        assert PluginStatus.LOADED == "loaded"
        assert PluginStatus.ACTIVE == "active"
        assert PluginStatus.INACTIVE == "inactive"
        assert PluginStatus.ERROR == "error"


class TestPluginHook:
    """Test PluginHook class."""

    def test_plugin_hook_init(self):
        """Test PluginHook initialization."""
        callback = lambda x: x * 2
        hook = PluginHook(hook_name="test_hook", callback=callback, priority=10)

        assert hook.hook_name == "test_hook"
        assert hook.callback == callback
        assert hook.priority == 10

    def test_plugin_hook_default_priority(self):
        """Test PluginHook with default priority."""
        callback = lambda x: x
        hook = PluginHook(hook_name="test_hook", callback=callback)

        assert hook.priority == 0


class TestAgentPlugin:
    """Test AgentPlugin base class."""

    def test_agent_plugin_init(self):
        """Test AgentPlugin initialization."""
        # Create a concrete implementation
        class TestPlugin(AgentPlugin):
            def initialize(self, agent):  # noqa: D102
                pass  # Test implementation

            def cleanup(self):  # noqa: D102
                pass  # Test implementation

        plugin = TestPlugin(
            plugin_id="plugin1",
            name="Test Plugin",
            version="2.0.0",
            description="Test description",
        )

        assert plugin.plugin_id == "plugin1"
        assert plugin.name == "Test Plugin"
        assert plugin.version == "2.0.0"
        assert plugin.description == "Test description"
        assert plugin.status == PluginStatus.LOADED
        assert plugin.hooks == []
        assert plugin.tools == []
        assert plugin.dependencies == []

    def test_register_hook(self):
        """Test register_hook method to cover lines 97-98."""
        class TestPlugin(AgentPlugin):
            def initialize(self, agent):  # noqa: D102
                pass  # Test implementation

            def cleanup(self):  # noqa: D102
                pass  # Test implementation

        plugin = TestPlugin(plugin_id="plugin1", name="Test")
        callback = lambda x: x

        plugin.register_hook("test_hook", callback, priority=5)

        assert len(plugin.hooks) == 1
        assert plugin.hooks[0].hook_name == "test_hook"
        assert plugin.hooks[0].callback == callback
        assert plugin.hooks[0].priority == 5

    def test_on_task_start(self):
        """Test on_task_start hook to cover line 110."""
        class TestPlugin(AgentPlugin):
            def initialize(self, agent):  # noqa: D102
                pass  # Test implementation

            def cleanup(self):  # noqa: D102
                pass  # Test implementation

        plugin = TestPlugin(plugin_id="plugin1", name="Test")
        task = MagicMock()

        result = plugin.on_task_start(task)

        assert result is None

    def test_on_task_complete(self):
        """Test on_task_complete hook to cover line 123."""
        class TestPlugin(AgentPlugin):
            def initialize(self, agent):  # noqa: D102
                pass  # Test implementation

            def cleanup(self):  # noqa: D102
                pass  # Test implementation

        plugin = TestPlugin(plugin_id="plugin1", name="Test")
        task = MagicMock()
        result = MagicMock()

        hook_result = plugin.on_task_complete(task, result)

        assert hook_result is None

    def test_on_message_received(self):
        """Test on_message_received hook to cover line 135."""
        class TestPlugin(AgentPlugin):
            def initialize(self, agent):  # noqa: D102
                pass  # Test implementation

            def cleanup(self):  # noqa: D102
                pass  # Test implementation

        plugin = TestPlugin(plugin_id="plugin1", name="Test")
        message = MagicMock()

        result = plugin.on_message_received(message)

        assert result is None


class TestPluginManager:
    """Test PluginManager class."""

    @pytest.fixture
    def manager(self):
        """Create a PluginManager instance."""
        return PluginManager()

    @pytest.fixture
    def mock_plugin(self):
        """Create a mock plugin."""
        class TestPlugin(AgentPlugin):
            def initialize(self, agent):
                self.status = PluginStatus.ACTIVE

            def cleanup(self):
                self.status = PluginStatus.INACTIVE

        return TestPlugin(plugin_id="plugin1", name="Test Plugin")

    def test_init(self, manager):
        """Test PluginManager initialization."""
        assert len(manager._plugins) == 0
        assert len(manager._hooks) == 0

    def test_register_plugin_success(self, manager, mock_plugin):
        """Test register_plugin with successful initialization to cover lines 167-175."""
        mock_agent = MagicMock()

        manager.register_plugin(mock_plugin, mock_agent)

        assert mock_plugin.plugin_id in manager._plugins
        assert manager._plugins[mock_plugin.plugin_id] == mock_plugin
        assert mock_plugin.status == PluginStatus.ACTIVE

    def test_register_plugin_without_agent(self, manager, mock_plugin):
        """Test register_plugin without agent."""
        manager.register_plugin(mock_plugin)

        assert mock_plugin.plugin_id in manager._plugins
        assert mock_plugin.status == PluginStatus.LOADED  # Not initialized

    def test_register_plugin_with_hooks(self, manager, mock_plugin):
        """Test register_plugin with hooks to cover lines 178-183."""
        callback1 = MagicMock()
        callback2 = MagicMock()
        mock_plugin.register_hook("hook1", callback1, priority=10)
        mock_plugin.register_hook("hook1", callback2, priority=5)

        manager.register_plugin(mock_plugin)

        assert "hook1" in manager._hooks
        assert len(manager._hooks["hook1"]) == 2
        # Should be sorted by priority (descending)
        assert manager._hooks["hook1"][0].priority == 10
        assert manager._hooks["hook1"][1].priority == 5

    def test_register_plugin_missing_dependency(self, manager):
        """Test register_plugin with missing dependency to cover lines 162-164."""
        class TestPlugin(AgentPlugin):
            def initialize(self, agent):  # noqa: D102
                pass  # Test implementation

            def cleanup(self):  # noqa: D102
                pass  # Test implementation

        plugin = TestPlugin(
            plugin_id="plugin1",
            name="Test",
            dependencies=["missing_plugin"],
        )

        with pytest.raises(ValueError, match="Plugin dependency 'missing_plugin' not found"):
            manager.register_plugin(plugin)

    def test_register_plugin_initialization_error(self, manager):
        """Test register_plugin when initialization fails to cover lines 171-173."""
        class FailingPlugin(AgentPlugin):
            def initialize(self, agent):
                raise RuntimeError("Initialization failed")

            def cleanup(self):  # noqa: D102
                pass  # Test implementation

        plugin = FailingPlugin(plugin_id="plugin1", name="Failing")
        mock_agent = MagicMock()

        with pytest.raises(RuntimeError, match="Failed to initialize plugin"):
            manager.register_plugin(plugin, mock_agent)

        assert plugin.status == PluginStatus.ERROR

    def test_load_plugin_from_module(self, manager):
        """Test load_plugin_from_module to cover lines 202-210."""
        # Create a test module class that can be instantiated
        class TestModulePlugin(AgentPlugin):
            def __init__(self):
                import uuid
                super().__init__(
                    plugin_id=str(uuid.uuid4()),
                    name="TestModulePlugin",
                )

            def initialize(self, agent):  # noqa: D102
                pass  # Test implementation

            def cleanup(self):  # noqa: D102
                pass  # Test implementation

        # Mock importlib to return our test module
        mock_module = MagicMock()
        mock_module.TestModulePlugin = TestModulePlugin

        with patch("src.core.agno_agent_framework.plugins.importlib") as mock_importlib:
            mock_importlib.import_module.return_value = mock_module
            plugin = manager.load_plugin_from_module("test_module", "TestModulePlugin")

        assert isinstance(plugin, TestModulePlugin)
        assert plugin.plugin_id in manager._plugins

    def test_load_plugin_from_module_error(self, manager):
        """Test load_plugin_from_module when module import fails."""
        with patch("src.core.agno_agent_framework.plugins.importlib.import_module", side_effect=ImportError("Module not found")):
            with pytest.raises(RuntimeError, match="Failed to load plugin"):
                manager.load_plugin_from_module("nonexistent_module", "PluginClass")

    def test_load_plugin_from_module_class_not_found(self, manager):
        """Test load_plugin_from_module when class not found."""
        mock_module = MagicMock()
        # Make getattr raise AttributeError when accessing PluginClass
        original_getattr = getattr
        def getattr_side_effect(obj, name, default=None):
            if name == "PluginClass":
                raise AttributeError("Class not found")
            return original_getattr(obj, name, default)

        with patch("src.core.agno_agent_framework.plugins.importlib") as mock_importlib:
            mock_importlib.import_module.return_value = mock_module
            with patch("src.core.agno_agent_framework.plugins.getattr", side_effect=getattr_side_effect):
                with pytest.raises(RuntimeError, match="Failed to load plugin"):
                    manager.load_plugin_from_module("test_module", "PluginClass")

    def test_get_plugin(self, manager, mock_plugin):
        """Test get_plugin method."""
        manager.register_plugin(mock_plugin)

        retrieved = manager.get_plugin("plugin1")
        assert retrieved == mock_plugin

        not_found = manager.get_plugin("nonexistent")
        assert not_found is None

    def test_list_plugins(self, manager, mock_plugin):
        """Test list_plugins method."""
        manager.register_plugin(mock_plugin)

        plugins = manager.list_plugins()

        assert len(plugins) == 1
        assert mock_plugin in plugins

    def test_execute_hooks(self, manager, mock_plugin):
        """Test execute_hooks method to cover lines 245-256."""
        callback1 = MagicMock(return_value="result1")
        callback2 = MagicMock(return_value="result2")
        mock_plugin.register_hook("test_hook", callback1, priority=10)
        mock_plugin.register_hook("test_hook", callback2, priority=5)

        manager.register_plugin(mock_plugin)

        results = manager.execute_hooks("test_hook", "arg1", kwarg1="value1")

        assert len(results) == 2
        assert "result1" in results
        assert "result2" in results
        callback1.assert_called_once_with("arg1", kwarg1="value1")
        callback2.assert_called_once_with("arg1", kwarg1="value1")

    def test_execute_hooks_nonexistent(self, manager):
        """Test execute_hooks with nonexistent hook name."""
        results = manager.execute_hooks("nonexistent_hook")

        assert results == []

    def test_execute_hooks_with_exception(self, manager, mock_plugin):
        """Test execute_hooks when callback raises exception."""
        def failing_callback(*args, **kwargs):
            raise ValueError("Callback failed")

        mock_plugin.register_hook("test_hook", failing_callback)
        manager.register_plugin(mock_plugin)

        # Should not raise, just print error
        results = manager.execute_hooks("test_hook")

        assert results == []

    def test_unregister_plugin(self, manager, mock_plugin):
        """Test unregister_plugin method to cover lines 268-280."""
        mock_plugin.register_hook("test_hook", MagicMock())
        manager.register_plugin(mock_plugin)

        manager.unregister_plugin("plugin1")

        assert "plugin1" not in manager._plugins
        assert mock_plugin.status == PluginStatus.INACTIVE
        assert "test_hook" not in manager._hooks or len(manager._hooks["test_hook"]) == 0

    def test_unregister_plugin_nonexistent(self, manager):
        """Test unregister_plugin with nonexistent plugin."""
        # Should not raise
        manager.unregister_plugin("nonexistent")


class TestExamplePlugin:
    """Test ExamplePlugin class."""

    def test_example_plugin_init(self):
        """Test ExamplePlugin initialization."""
        plugin = ExamplePlugin()

        assert plugin.name == "ExamplePlugin"
        assert plugin.description == "Example plugin for demonstration"
        assert plugin.plugin_id is not None

    def test_example_plugin_initialize(self):
        """Test ExamplePlugin initialize method to cover lines 296-306."""
        plugin = ExamplePlugin()
        mock_agent = MagicMock()

        plugin.initialize(mock_agent)

        assert plugin.status == PluginStatus.ACTIVE

    def test_example_plugin_cleanup(self):
        """Test ExamplePlugin cleanup method to cover lines 308-315."""
        plugin = ExamplePlugin()
        plugin.status = PluginStatus.ACTIVE

        plugin.cleanup()

        assert plugin.status == PluginStatus.INACTIVE

