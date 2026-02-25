"""
Unit tests for PromptManager coverage improvements.

Tests missing coverage paths in prompt_manager.py to achieve >85% coverage.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.prompt_context_management.prompt_manager import (
    ContextWindowManager,
    PromptContextManager,
    PromptStore,
    PromptTemplate,
)


class TestPromptStoreDALCoverage:
    """Test PromptStore DAL operations for coverage."""

    @pytest.fixture
    def mock_template_dal(self):
        """Create a mock PromptTemplateDAL."""
        dal = MagicMock()
        dal.save_template = AsyncMock(return_value="template-id-123")
        dal.load_template = AsyncMock(return_value={
            "name": "test_template",
            "version": "1.0",
            "content": "Test content",
            "metadata": {}
        })
        return dal

    def test_prompt_store_add_with_dal_running_loop(self, mock_template_dal):
        """Test PromptStore.add() with DAL when event loop is running."""
        store = PromptStore(template_dal=mock_template_dal)
        template = PromptTemplate(
            name="test_template",
            version="1.0",
            content="Test content",
            tenant_id="tenant-123"
        )
        
        # Mock running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = True
            mock_loop.return_value = mock_loop_instance
            
            with patch("asyncio.create_task") as mock_create_task:
                store.add(template)
                
                # Verify template was added to store
                assert store.get("test_template", tenant_id="tenant-123") == template
                # Verify create_task was called (for running loop)
                assert mock_create_task.called

    def test_prompt_store_add_with_dal_no_running_loop(self, mock_template_dal):
        """Test PromptStore.add() with DAL when event loop is not running."""
        store = PromptStore(template_dal=mock_template_dal)
        template = PromptTemplate(
            name="test_template",
            version="1.0",
            content="Test content",
            tenant_id="tenant-123"
        )
        
        # Mock non-running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = False
            mock_loop_instance.run_until_complete = MagicMock()
            mock_loop.return_value = mock_loop_instance
            
            store.add(template)
            
            # Verify template was added to store
            assert store.get("test_template", tenant_id="tenant-123") == template
            # Verify run_until_complete was called
            assert mock_loop_instance.run_until_complete.called

    def test_prompt_store_add_with_dal_runtime_error(self, mock_template_dal):
        """Test PromptStore.add() with DAL when RuntimeError occurs."""
        store = PromptStore(template_dal=mock_template_dal)
        template = PromptTemplate(
            name="test_template",
            version="1.0",
            content="Test content",
            tenant_id="tenant-123"
        )
        
        # Mock RuntimeError when getting event loop
        with patch("asyncio.get_event_loop", side_effect=RuntimeError("No event loop")):
            with patch("asyncio.run") as mock_run:
                store.add(template)
                
                # Verify template was added to store
                assert store.get("test_template", tenant_id="tenant-123") == template
                # Verify asyncio.run was called
                assert mock_run.called

    def test_prompt_store_get_with_dal_running_loop(self, mock_template_dal):
        """Test PromptStore.get() with DAL when event loop is running."""
        store = PromptStore(template_dal=mock_template_dal)
        
        # Mock running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = True
            mock_loop.return_value = mock_loop_instance
            
            # When loop is running, should return None
            result = store.get("test_template", tenant_id="tenant-123")
            assert result is None

    def test_prompt_store_get_with_dal_no_running_loop(self, mock_template_dal):
        """Test PromptStore.get() with DAL when event loop is not running."""
        store = PromptStore(template_dal=mock_template_dal)
        
        # Mock non-running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = False
            
            # run_until_complete should return the value directly, not a coroutine
            template_data = {
                "name": "test_template",
                "version": "1.0",
                "content": "Test content",
                "metadata": {}
            }
            mock_loop_instance.run_until_complete = MagicMock(return_value=template_data)
            mock_loop.return_value = mock_loop_instance
            
            result = store.get("test_template", tenant_id="tenant-123")
            
            # Verify template was loaded and cached
            assert result is not None
            assert result.name == "test_template"
            assert result.version == "1.0"
            # Verify it's cached
            assert store.get("test_template", tenant_id="tenant-123") == result

    def test_prompt_store_get_with_dal_runtime_error(self, mock_template_dal):
        """Test PromptStore.get() with DAL when RuntimeError occurs."""
        store = PromptStore(template_dal=mock_template_dal)
        
        # Mock RuntimeError when getting event loop
        with patch("asyncio.get_event_loop", side_effect=RuntimeError("No event loop")):
            with patch("asyncio.run") as mock_run:
                mock_run.return_value = {
                    "name": "test_template",
                    "version": "1.0",
                    "content": "Test content",
                    "metadata": {}
                }
                
                result = store.get("test_template", tenant_id="tenant-123")
                
                # Verify template was loaded
                assert result is not None
                assert result.name == "test_template"
                # Verify asyncio.run was called
                assert mock_run.called

    def test_prompt_store_get_with_dal_no_template_data(self, mock_template_dal):
        """Test PromptStore.get() with DAL when no template data is returned."""
        mock_template_dal.load_template = AsyncMock(return_value=None)
        store = PromptStore(template_dal=mock_template_dal)
        
        # Mock non-running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = False
            # run_until_complete should return None directly
            mock_loop_instance.run_until_complete = MagicMock(return_value=None)
            mock_loop.return_value = mock_loop_instance
            
            result = store.get("nonexistent", tenant_id="tenant-123")
            assert result is None


class TestPromptContextManagerDALCoverage:
    """Test PromptContextManager DAL operations for coverage."""

    @pytest.fixture
    def mock_history_dal(self):
        """Create a mock PromptHistoryDAL."""
        dal = MagicMock()
        dal.save_history = AsyncMock(return_value="history-id-123")
        dal.get_history = AsyncMock(return_value=[])
        dal.save_context_window_state = AsyncMock(return_value="state-id-123")
        dal.get_context_window_state = AsyncMock(return_value=None)
        return dal

    def test_load_history_running_loop(self, mock_history_dal):
        """Test _load_history() when event loop is running."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = True
            mock_loop.return_value = mock_loop_instance
            
            with patch("asyncio.create_task") as mock_create_task:
                manager._load_history()
                # Verify create_task was called
                assert mock_create_task.called

    def test_load_history_no_running_loop(self, mock_history_dal):
        """Test _load_history() when event loop is not running."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock non-running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = False
            # run_until_complete should be a regular mock, not AsyncMock
            mock_loop_instance.run_until_complete = MagicMock()
            mock_loop.return_value = mock_loop_instance
            
            manager._load_history()
            # Verify run_until_complete was called
            assert mock_loop_instance.run_until_complete.called

    def test_load_history_runtime_error(self, mock_history_dal):
        """Test _load_history() when RuntimeError occurs."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock RuntimeError
        with patch("asyncio.get_event_loop", side_effect=RuntimeError("No event loop")):
            with patch("asyncio.run") as mock_run:
                manager._load_history()
                # Verify asyncio.run was called
                assert mock_run.called

    @pytest.mark.asyncio
    async def test_load_history_async_with_records(self, mock_history_dal):
        """Test _load_history_async() with history records."""
        mock_history_dal.get_history.return_value = [
            {"prompt": "Prompt 1", "created_at": "2024-01-01T00:00:00"},
            {"prompt": "Prompt 2", "created_at": "2024-01-01T01:00:00"},
        ]
        
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        await manager._load_history_async()
        
        # Verify history was loaded
        assert len(manager.history) == 2
        assert manager.history[0] == "Prompt 2"  # Reversed order
        assert manager.history[1] == "Prompt 1"

    @pytest.mark.asyncio
    async def test_load_history_async_with_exception(self, mock_history_dal):
        """Test _load_history_async() with exception."""
        mock_history_dal.get_history.side_effect = Exception("DAL error")
        
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Should not raise, just log
        await manager._load_history_async()
        assert len(manager.history) == 0

    def test_load_context_window_state_running_loop(self, mock_history_dal):
        """Test _load_context_window_state() when event loop is running."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = True
            mock_loop.return_value = mock_loop_instance
            
            with patch("asyncio.create_task") as mock_create_task:
                manager._load_context_window_state()
                # Verify create_task was called
                assert mock_create_task.called

    def test_load_context_window_state_no_running_loop(self, mock_history_dal):
        """Test _load_context_window_state() when event loop is not running."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock non-running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = False
            # run_until_complete should be a regular mock, not AsyncMock
            mock_loop_instance.run_until_complete = MagicMock()
            mock_loop.return_value = mock_loop_instance
            
            manager._load_context_window_state()
            # Verify run_until_complete was called
            assert mock_loop_instance.run_until_complete.called

    def test_load_context_window_state_runtime_error(self, mock_history_dal):
        """Test _load_context_window_state() when RuntimeError occurs."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock RuntimeError
        with patch("asyncio.get_event_loop", side_effect=RuntimeError("No event loop")):
            with patch("asyncio.run") as mock_run:
                manager._load_context_window_state()
                # Verify asyncio.run was called
                assert mock_run.called

    @pytest.mark.asyncio
    async def test_load_context_window_state_async_with_state(self, mock_history_dal):
        """Test _load_context_window_state_async() with state."""
        mock_history_dal.get_context_window_state.return_value = {
            "max_tokens": 8000,
            "safety_margin": 300,
            "window_state": {"messages": ["msg1"]}
        }
        
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        _ = manager.window.max_tokens  # original_max_tokens assigned but unused
        
        await manager._load_context_window_state_async()
        
        # Verify state was loaded
        assert manager.window.max_tokens == 8000
        assert manager.window.safety_margin == 300
        assert hasattr(manager, "_window_state")

    @pytest.mark.asyncio
    async def test_load_context_window_state_async_with_exception(self, mock_history_dal):
        """Test _load_context_window_state_async() with exception."""
        mock_history_dal.get_context_window_state.side_effect = Exception("DAL error")
        
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Should not raise, just log
        await manager._load_context_window_state_async()

    def test_save_context_window_state_running_loop(self, mock_history_dal):
        """Test _save_context_window_state() when event loop is running."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = True
            mock_loop.return_value = mock_loop_instance
            
            with patch("asyncio.create_task") as mock_create_task:
                manager._save_context_window_state()
                # Verify create_task was called
                assert mock_create_task.called

    def test_save_context_window_state_no_running_loop(self, mock_history_dal):
        """Test _save_context_window_state() when event loop is not running."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock non-running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = False
            # run_until_complete should be a regular mock, not AsyncMock
            mock_loop_instance.run_until_complete = MagicMock()
            mock_loop.return_value = mock_loop_instance
            
            manager._save_context_window_state()
            # Verify run_until_complete was called
            assert mock_loop_instance.run_until_complete.called

    def test_save_context_window_state_runtime_error(self, mock_history_dal):
        """Test _save_context_window_state() when RuntimeError occurs."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock RuntimeError
        with patch("asyncio.get_event_loop", side_effect=RuntimeError("No event loop")):
            with patch("asyncio.run") as mock_run:
                manager._save_context_window_state()
                # Verify asyncio.run was called
                assert mock_run.called

    def test_save_context_window_state_exception(self, mock_history_dal):
        """Test _save_context_window_state() with exception."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock exception in save
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = False
            # run_until_complete should be a regular mock, not AsyncMock
            mock_loop_instance.run_until_complete = MagicMock(side_effect=Exception("Save error"))
            mock_loop.return_value = mock_loop_instance
            
            # Should not raise, just log
            manager._save_context_window_state()

    def test_record_history_with_dal_running_loop(self, mock_history_dal):
        """Test record_history() with DAL when event loop is running."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = True
            mock_loop.return_value = mock_loop_instance
            
            with patch("asyncio.create_task") as mock_create_task:
                manager.record_history("Test prompt")
                # Verify create_task was called
                assert mock_create_task.called

    def test_record_history_with_dal_no_running_loop(self, mock_history_dal):
        """Test record_history() with DAL when event loop is not running."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock non-running event loop
        with patch("asyncio.get_event_loop") as mock_loop:
            mock_loop_instance = MagicMock()
            mock_loop_instance.is_running.return_value = False
            # run_until_complete should be a regular mock, not AsyncMock
            mock_loop_instance.run_until_complete = MagicMock()
            mock_loop.return_value = mock_loop_instance
            
            manager.record_history("Test prompt")
            # Verify run_until_complete was called
            assert mock_loop_instance.run_until_complete.called

    def test_record_history_with_dal_runtime_error(self, mock_history_dal):
        """Test record_history() with DAL when RuntimeError occurs."""
        manager = PromptContextManager(
            history_dal=mock_history_dal,
            tenant_id="tenant-123",
            load_history_on_init=False
        )
        
        # Mock RuntimeError
        with patch("asyncio.get_event_loop", side_effect=RuntimeError("No event loop")):
            with patch("asyncio.run") as mock_run:
                manager.record_history("Test prompt")
                # Verify asyncio.run was called
                assert mock_run.called


class TestPromptContextManagerCodecCoverage:
    """Test PromptContextManager codec operations for coverage."""

    @pytest.fixture
    def mock_codec_serializer(self):
        """Create a mock codec serializer."""
        serializer = MagicMock()
        serializer.encode = AsyncMock(return_value=b"encoded_data")
        serializer.decode = AsyncMock(return_value={"name": "test", "version": "1.0", "content": "test", "metadata": {}})
        return serializer

    @pytest.mark.asyncio
    async def test_encode_template_with_codec(self, mock_codec_serializer):
        """Test encode_template() with codec serializer."""
        manager = PromptContextManager(
            codec_serializer=mock_codec_serializer,
            load_history_on_init=False
        )
        
        template = PromptTemplate(
            name="test_template",
            version="1.0",
            content="Test content"
        )
        
        with patch("src.core.codec_integration.encode_prompt_template") as mock_encode:
            mock_encode.return_value = b"encoded_data"
            result = await manager.encode_template(template)
            assert result == b"encoded_data"
            assert mock_encode.called

    # Note: ImportError tests for codec_integration are skipped as they require
    # complex mocking of module imports which is difficult to test reliably.
    # The code paths are covered by integration tests.

    @pytest.mark.asyncio
    async def test_decode_template_with_codec(self, mock_codec_serializer):
        """Test decode_template() with codec serializer."""
        manager = PromptContextManager(
            codec_serializer=mock_codec_serializer,
            load_history_on_init=False
        )
        
        with patch("src.core.codec_integration.decode_prompt_template") as mock_decode:
            mock_decode.return_value = {
                "name": "test_template",
                "version": "1.0",
                "content": "Test content",
                "metadata": {}
            }
            result = await manager.decode_template(b"encoded_data")
            assert result.name == "test_template"
            assert result.version == "1.0"
            assert mock_decode.called



class TestPromptContextManagerRenderCoverage:
    """Test PromptContextManager render operations for coverage."""

    def test_render_template_not_found_no_otel(self):
        """Test render() when template not found without OTEL."""
        manager = PromptContextManager(
            otel_tracer=None,
            otel_metrics=None,
            load_history_on_init=False
        )
        
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            manager.render("nonexistent", {"var": "value"})


class TestContextWindowManagerCoverage:
    """Test ContextWindowManager for coverage."""

    def test_build_context_break_condition(self):
        """Test build_context() break condition when limit is exceeded."""
        window = ContextWindowManager(max_tokens=100, safety_margin=10)
        
        # Create messages that exceed limit
        messages = ["short", "very long message " * 20, "another"]
        
        # build_context should select messages until limit is exceeded
        result = window.build_context(messages, max_tokens=50)
        
        # Should return a string with selected messages
        assert isinstance(result, str)
        # Should not include all messages due to limit
        assert len(result.split("\n")) < len(messages)

