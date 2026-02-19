"""
Unit Tests for PromptContextManager OTEL Integration

Tests for OpenTelemetry integration within the PromptContextManager component.
"""

from unittest.mock import MagicMock

import pytest

from src.core.prompt_context_management.prompt_manager import PromptContextManager
from src.core.otel_integration import OTELMetrics, OTELTracer


class TestPromptContextManagerOTELIntegration:
    """Tests for PromptContextManager OTEL integration."""

    def test_prompt_context_manager_with_otel_tracer(self):
        """Test prompt context manager initialization with OTEL tracer."""
        tracer = OTELTracer(service_name="test-prompt-context-manager")
        
        manager = PromptContextManager(
            otel_tracer=tracer,
        )
        
        assert manager.otel_tracer is not None
        assert manager.otel_tracer.service_name == "test-prompt-context-manager"

    def test_prompt_context_manager_with_otel_metrics(self):
        """Test prompt context manager initialization with OTEL metrics."""
        metrics = OTELMetrics(service_name="test-prompt-context-manager")
        
        manager = PromptContextManager(
            otel_metrics=metrics,
        )
        
        assert manager.otel_metrics is not None
        assert manager.otel_metrics.service_name == "test-prompt-context-manager"

    def test_prompt_context_manager_without_otel(self):
        """Test prompt context manager works without OTEL configured."""
        manager = PromptContextManager()
        
        # OTEL should be auto-initialized if available
        # But it may be None if OTEL SDK is not installed
        assert manager is not None

    def test_render_with_otel(self):
        """Test render operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-prompt-context-manager")
        metrics = OTELMetrics(service_name="test-prompt-context-manager")
        
        manager = PromptContextManager(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Add a template first
        manager.add_template(
            name="test_template",
            version="1.0",
            content="Hello {name}!",
            tenant_id="tenant_123"
        )
        
        # Execute render - should not raise exception
        result = manager.render(
            template_name="test_template",
            variables={"name": "World"},
            tenant_id="tenant_123"
        )
        
        assert result == "Hello World!"
        assert manager.otel_tracer is not None
        assert manager.otel_metrics is not None

    def test_render_without_otel(self):
        """Test render operation without OTEL."""
        manager = PromptContextManager()
        manager.otel_tracer = None
        manager.otel_metrics = None
        
        # Add a template first
        manager.add_template(
            name="test_template",
            version="1.0",
            content="Hello {name}!",
        )
        
        result = manager.render(
            template_name="test_template",
            variables={"name": "World"}
        )
        
        assert result == "Hello World!"

    def test_render_error_with_otel(self):
        """Test render error handling with OTEL."""
        tracer = OTELTracer(service_name="test-prompt-context-manager")
        metrics = OTELMetrics(service_name="test-prompt-context-manager")
        
        manager = PromptContextManager(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Try to render non-existent template
        with pytest.raises(ValueError):
            manager.render(
                template_name="non_existent",
                variables={"name": "World"}
            )
        
        assert manager.otel_tracer is not None
        assert manager.otel_metrics is not None

    def test_add_template_with_otel(self):
        """Test add_template operation with OTEL tracing."""
        tracer = OTELTracer(service_name="test-prompt-context-manager")
        metrics = OTELMetrics(service_name="test-prompt-context-manager")
        
        manager = PromptContextManager(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Execute add_template - should not raise exception
        manager.add_template(
            name="test_template",
            version="1.0",
            content="Hello {name}!",
            tenant_id="tenant_123",
            metadata={"author": "test"}
        )
        
        # Verify template was added
        template = manager.store.get("test_template", tenant_id="tenant_123")
        assert template is not None
        assert template.name == "test_template"
        assert manager.otel_tracer is not None
        assert manager.otel_metrics is not None

    def test_add_template_without_otel(self):
        """Test add_template operation without OTEL."""
        manager = PromptContextManager()
        manager.otel_tracer = None
        manager.otel_metrics = None
        
        manager.add_template(
            name="test_template",
            version="1.0",
            content="Hello {name}!",
        )
        
        # Verify template was added
        template = manager.store.get("test_template")
        assert template is not None
        assert template.name == "test_template"

    def test_render_with_tenant_id_otel(self):
        """Test render with tenant_id and OTEL."""
        tracer = OTELTracer(service_name="test-prompt-context-manager")
        metrics = OTELMetrics(service_name="test-prompt-context-manager")
        
        manager = PromptContextManager(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Add template with tenant_id
        manager.add_template(
            name="tenant_template",
            version="1.0",
            content="Tenant: {tenant}",
            tenant_id="tenant_123"
        )
        
        result = manager.render(
            template_name="tenant_template",
            variables={"tenant": "tenant_123"},
            tenant_id="tenant_123"
        )
        
        assert result == "Tenant: tenant_123"
        assert manager.otel_tracer is not None

    def test_add_template_with_metadata_otel(self):
        """Test add_template with metadata and OTEL."""
        tracer = OTELTracer(service_name="test-prompt-context-manager")
        metrics = OTELMetrics(service_name="test-prompt-context-manager")
        
        manager = PromptContextManager(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        metadata = {"author": "test", "version": "1.0"}
        manager.add_template(
            name="metadata_template",
            version="1.0",
            content="Test content",
            metadata=metadata
        )
        
        template = manager.store.get("metadata_template")
        assert template is not None
        assert template.metadata == metadata
        assert manager.otel_tracer is not None

    def test_render_with_version_otel(self):
        """Test render with specific version and OTEL."""
        tracer = OTELTracer(service_name="test-prompt-context-manager")
        metrics = OTELMetrics(service_name="test-prompt-context-manager")
        
        manager = PromptContextManager(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        manager.add_template(
            name="versioned_template",
            version="1.0",
            content="Version 1: {name}",
        )
        manager.add_template(
            name="versioned_template",
            version="2.0",
            content="Version 2: {name}",
        )
        
        result = manager.render(
            template_name="versioned_template",
            variables={"name": "test"},
            version="1.0"
        )
        
        assert result == "Version 1: test"
        assert manager.otel_tracer is not None

    def test_add_template_error_with_otel(self):
        """Test add_template error handling with OTEL."""
        tracer = OTELTracer(service_name="test-prompt-context-manager")
        metrics = OTELMetrics(service_name="test-prompt-context-manager")
        
        manager = PromptContextManager(
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        # Mock store.add to raise an exception
        original_add = manager.store.add
        manager.store.add = MagicMock(side_effect=Exception("Store error"))
        
        with pytest.raises(Exception):
            manager.add_template(
                name="error_template",
                version="1.0",
                content="Test content",
            )
        
        assert manager.otel_tracer is not None
        assert manager.otel_metrics is not None
        
        # Restore original method
        manager.store.add = original_add

    def test_render_without_otel_with_version(self):
        """Test render without OTEL but with version parameter."""
        manager = PromptContextManager()
        manager.otel_tracer = None
        manager.otel_metrics = None
        
        manager.add_template(
            name="versioned_template",
            version="1.0",
            content="Version 1: {name}",
        )
        
        result = manager.render(
            template_name="versioned_template",
            variables={"name": "test"},
            version="1.0"
        )
        
        assert result == "Version 1: test"

    def test_context_window_manager_estimate_tokens(self):
        """Test ContextWindowManager estimate_tokens method."""
        from src.core.prompt_context_management.prompt_manager import ContextWindowManager
        
        manager = ContextWindowManager()
        tokens = manager.estimate_tokens("This is a test sentence")
        
        assert tokens == 5

    def test_context_window_manager_truncate(self):
        """Test ContextWindowManager truncate method."""
        from src.core.prompt_context_management.prompt_manager import ContextWindowManager
        
        manager = ContextWindowManager(max_tokens=10, safety_margin=2)
        text = "This is a very long sentence that should be truncated"
        result = manager.truncate(text)
        
        assert len(result.split()) <= 8  # max_tokens - safety_margin

    def test_context_window_manager_build_context(self):
        """Test ContextWindowManager build_context method."""
        from src.core.prompt_context_management.prompt_manager import ContextWindowManager
        
        manager = ContextWindowManager(max_tokens=20, safety_margin=2)
        messages = ["Message 1", "Message 2", "Message 3", "Message 4"]
        result = manager.build_context(messages)
        
        assert result is not None
        assert isinstance(result, str)

    def test_prompt_store_get_with_version(self):
        """Test PromptStore get method with version parameter."""
        from src.core.prompt_context_management.prompt_manager import PromptStore, PromptTemplate
        
        store = PromptStore()
        template1 = PromptTemplate(name="test", version="1.0", content="Version 1")
        template2 = PromptTemplate(name="test", version="2.0", content="Version 2")
        
        store.add(template1)
        store.add(template2)
        
        result = store.get("test", version="1.0")
        assert result is not None
        assert result.version == "1.0"

