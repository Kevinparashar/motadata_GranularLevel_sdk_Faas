"""
Unit tests for prompt_enhancements.py
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.core.prompt_context_management.prompt_enhancements import (
    DynamicPromptBuilder,
    EnhancedPromptContextManager,
    FallbackTemplate,
    FallbackTemplateManager,
    PromptOptimizer,
)
from src.core.prompt_context_management.prompt_manager import PromptStore, PromptTemplate


class TestFallbackTemplate:
    """Tests for FallbackTemplate dataclass."""

    def test_init(self):
        """Test FallbackTemplate initialization."""
        template = FallbackTemplate(
            primary_template="primary",
            fallback_template="fallback",
        )

        assert template.primary_template == "primary"
        assert template.fallback_template == "fallback"
        assert template.condition is None

    def test_init_with_condition(self):
        """Test FallbackTemplate initialization with condition."""
        def condition(ctx):
            return ctx.get("use_fallback", False)

        template = FallbackTemplate(
            primary_template="primary",
            fallback_template="fallback",
            condition=condition,
        )

        assert template.condition is not None
        assert template.condition({"use_fallback": True}) is True


class TestDynamicPromptBuilder:
    """Tests for DynamicPromptBuilder class."""

    @pytest.fixture
    def mock_prompt_store(self):
        """Create mock PromptStore."""
        store = MagicMock(spec=PromptStore)
        template = PromptTemplate(
            name="test_template",
            content="Hello {name}",
            version="1.0",
        )
        store.get = Mock(return_value=template)
        return store

    @pytest.fixture
    def builder(self, mock_prompt_store):
        """Create DynamicPromptBuilder instance."""
        return DynamicPromptBuilder(mock_prompt_store)

    def test_init(self, mock_prompt_store):
        """Test DynamicPromptBuilder initialization."""
        builder = DynamicPromptBuilder(mock_prompt_store)

        assert builder.prompt_store == mock_prompt_store
        assert builder.context_adapters == []

    def test_add_context_adapter(self, builder):
        """Test add_context_adapter."""
        def adapter(prompt, context, variables):
            return prompt + " [adapted]"

        builder.add_context_adapter(adapter)

        assert len(builder.context_adapters) == 1
        assert builder.context_adapters[0] == adapter

    def test_add_multiple_context_adapters(self, builder):
        """Test adding multiple context adapters."""
        def adapter1(prompt, context, variables):
            return prompt + " [adapter1]"

        def adapter2(prompt, context, variables):
            return prompt + " [adapter2]"

        builder.add_context_adapter(adapter1)
        builder.add_context_adapter(adapter2)

        assert len(builder.context_adapters) == 2

    def test_build_dynamic_prompt_basic(self, builder, mock_prompt_store):
        """Test build_dynamic_prompt basic usage."""
        variables = {"name": "World"}
        context = {}

        result = builder.build_dynamic_prompt(
            template_name="test_template",
            variables=variables,
            context=context,
        )

        assert result == "Hello World"
        mock_prompt_store.get.assert_called_once_with("test_template", tenant_id=None, version=None)

    def test_build_dynamic_prompt_with_tenant_id(self, builder, mock_prompt_store):
        """Test build_dynamic_prompt with tenant_id."""
        variables = {"name": "World"}
        context = {}

        result = builder.build_dynamic_prompt(
            template_name="test_template",
            variables=variables,
            context=context,
            tenant_id="tenant-1",
        )

        assert result == "Hello World"
        mock_prompt_store.get.assert_called_once_with("test_template", tenant_id="tenant-1", version=None)

    def test_build_dynamic_prompt_with_version(self, builder, mock_prompt_store):
        """Test build_dynamic_prompt with version."""
        variables = {"name": "World"}
        context = {}

        result = builder.build_dynamic_prompt(
            template_name="test_template",
            variables=variables,
            context=context,
            version="2.0",
        )

        assert result == "Hello World"
        mock_prompt_store.get.assert_called_once_with("test_template", tenant_id=None, version="2.0")

    def test_build_dynamic_prompt_template_not_found(self, builder, mock_prompt_store):
        """Test build_dynamic_prompt when template not found."""
        mock_prompt_store.get.return_value = None

        with pytest.raises(ValueError, match="Template 'test_template' not found"):
            builder.build_dynamic_prompt(
                template_name="test_template",
                variables={},
                context={},
            )

    def test_build_dynamic_prompt_with_adapter(self, builder, mock_prompt_store):
        """Test build_dynamic_prompt with context adapter."""
        def adapter(prompt, context, variables):
            return prompt + " [adapted]"

        builder.add_context_adapter(adapter)

        variables = {"name": "World"}
        context = {}

        result = builder.build_dynamic_prompt(
            template_name="test_template",
            variables=variables,
            context=context,
        )

        assert result == "Hello World [adapted]"

    def test_build_dynamic_prompt_with_adapter_error(self, builder, mock_prompt_store):
        """Test build_dynamic_prompt when adapter raises error."""
        def adapter(prompt, context, variables):
            raise RuntimeError("Adapter error")

        builder.add_context_adapter(adapter)

        variables = {"name": "World"}
        context = {}

        # Should not raise, adapter errors are ignored
        result = builder.build_dynamic_prompt(
            template_name="test_template",
            variables=variables,
            context=context,
        )

        assert result == "Hello World"

    def test_adapt_for_context_admin(self, builder):
        """Test adapt_for_context with admin role."""
        prompt = "Test prompt"
        context = {"user_role": "admin"}

        result = builder.adapt_for_context(prompt, context)

        assert "[Admin Mode]" in result
        assert result.startswith("[Admin Mode]")

    def test_adapt_for_context_urgency(self, builder):
        """Test adapt_for_context with urgency."""
        prompt = "Test prompt"
        context = {"urgency": "high"}

        result = builder.adapt_for_context(prompt, context)

        assert "[URGENT: Please prioritize this request]" in result

    def test_adapt_for_context_domain(self, builder):
        """Test adapt_for_context with technical domain."""
        prompt = "Test prompt"
        context = {"domain": "technical"}

        result = builder.adapt_for_context(prompt, context)

        assert "[Technical Context: Provide detailed technical explanations]" in result

    def test_adapt_for_context_multiple(self, builder):
        """Test adapt_for_context with multiple context values."""
        prompt = "Test prompt"
        context = {
            "user_role": "admin",
            "urgency": "high",
            "domain": "technical",
        }

        result = builder.adapt_for_context(prompt, context)

        assert "[Admin Mode]" in result
        assert "[URGENT: Please prioritize this request]" in result
        assert "[Technical Context: Provide detailed technical explanations]" in result

    def test_adapt_for_context_no_context(self, builder):
        """Test adapt_for_context with no context."""
        prompt = "Test prompt"
        context = {}

        result = builder.adapt_for_context(prompt, context)

        assert result == "Test prompt"


class TestPromptOptimizer:
    """Tests for PromptOptimizer class."""

    @pytest.fixture
    def optimizer(self):
        """Create PromptOptimizer instance."""
        return PromptOptimizer()

    def test_init(self, optimizer):
        """Test PromptOptimizer initialization."""
        assert optimizer.optimization_rules == []
        assert optimizer.optimization_history == []

    def test_add_optimization_rule(self, optimizer):
        """Test add_optimization_rule."""
        def rule(prompt, context):
            return prompt + " [optimized]"

        optimizer.add_optimization_rule(rule)

        assert len(optimizer.optimization_rules) == 1
        assert optimizer.optimization_rules[0] == rule

    def test_add_multiple_optimization_rules(self, optimizer):
        """Test adding multiple optimization rules."""
        def rule1(prompt, context):
            return prompt + " [rule1]"

        def rule2(prompt, context):
            return prompt + " [rule2]"

        optimizer.add_optimization_rule(rule1)
        optimizer.add_optimization_rule(rule2)

        assert len(optimizer.optimization_rules) == 2

    def test_optimize_basic(self, optimizer):
        """Test optimize basic usage."""
        prompt = "Test prompt"

        result = optimizer.optimize(prompt)

        assert result == prompt
        assert len(optimizer.optimization_history) == 1

    def test_optimize_with_rule(self, optimizer):
        """Test optimize with optimization rule."""
        def rule(prompt, context):
            return prompt + " [optimized]"

        optimizer.add_optimization_rule(rule)

        prompt = "Test prompt"
        result = optimizer.optimize(prompt)

        assert result == "Test prompt [optimized]"
        assert len(optimizer.optimization_history) == 1

    def test_optimize_with_context(self, optimizer):
        """Test optimize with context."""
        def rule(prompt, context):
            return prompt + f" [context: {context.get('key', 'none')}]"

        optimizer.add_optimization_rule(rule)

        prompt = "Test prompt"
        context = {"key": "value"}
        result = optimizer.optimize(prompt, context)

        assert result == "Test prompt [context: value]"

    def test_optimize_with_rule_error(self, optimizer):
        """Test optimize when rule raises error."""
        def rule(prompt, context):
            raise RuntimeError("Rule error")

        optimizer.add_optimization_rule(rule)

        prompt = "Test prompt"
        # Should not raise, rule errors are ignored
        result = optimizer.optimize(prompt)

        assert result == prompt

    def test_optimize_records_history(self, optimizer):
        """Test optimize records in history."""
        prompt = "Test prompt"
        context = {"key": "value"}

        result = optimizer.optimize(prompt, context)

        assert len(optimizer.optimization_history) == 1
        history_entry = optimizer.optimization_history[0]
        assert history_entry["original"] == prompt
        assert history_entry["optimized"] == result
        assert history_entry["context"] == context
        assert "timestamp" in history_entry

    def test_optimize_for_clarity_whitespace(self, optimizer):
        """Test optimize_for_clarity removes redundant whitespace."""
        prompt = "Test    prompt   with    multiple   spaces"

        result = optimizer.optimize_for_clarity(prompt)

        assert result == "Test prompt with multiple spaces."

    def test_optimize_for_clarity_adds_period(self, optimizer):
        """Test optimize_for_clarity adds period if missing."""
        prompt = "Test prompt"

        result = optimizer.optimize_for_clarity(prompt)

        assert result.endswith(".")
        assert result == "Test prompt."

    def test_optimize_for_clarity_preserves_ending(self, optimizer):
        """Test optimize_for_clarity preserves existing ending."""
        prompt = "Test prompt!"

        result = optimizer.optimize_for_clarity(prompt)

        assert result.endswith("!")
        assert result == "Test prompt!"

    def test_optimize_for_clarity_question_mark(self, optimizer):
        """Test optimize_for_clarity preserves question mark."""
        prompt = "Test prompt?"

        result = optimizer.optimize_for_clarity(prompt)

        assert result.endswith("?")
        assert result == "Test prompt?"

    def test_optimize_for_length_short(self, optimizer):
        """Test optimize_for_length with short prompt."""
        prompt = "Short prompt"

        result = optimizer.optimize_for_length(prompt, max_length=2000)

        assert result == prompt

    def test_optimize_for_length_long(self, optimizer):
        """Test optimize_for_length with long prompt."""
        prompt = "A" * 3000

        result = optimizer.optimize_for_length(prompt, max_length=2000)

        assert len(result) <= 2000

    def test_optimize_for_length_truncates_at_sentence(self, optimizer):
        """Test optimize_for_length truncates at sentence boundaries."""
        prompt = "First sentence. Second sentence. Third sentence. " + "A" * 2000

        result = optimizer.optimize_for_length(prompt, max_length=100)

        # Should truncate at sentence boundary
        assert len(result) <= 100

    def test_optimize_for_length_no_sentences(self, optimizer):
        """Test optimize_for_length with no sentence boundaries."""
        prompt = "A" * 3000

        result = optimizer.optimize_for_length(prompt, max_length=2000)

        assert len(result) == 2000

    def test_optimize_for_specificity_no_change(self, optimizer):
        """Test optimize_for_specificity with specific prompt."""
        prompt = "Please provide detailed information about the topic."

        result = optimizer.optimize_for_specificity(prompt)

        assert result == prompt

    def test_optimize_for_specificity_adds_specificity(self, optimizer):
        """Test optimize_for_specificity adds specificity marker."""
        prompt = "Tell me something about things and stuff etc"

        result = optimizer.optimize_for_specificity(prompt)

        assert "Please provide specific and detailed information." in result

    def test_optimize_for_specificity_vague_indicators(self, optimizer):
        """Test optimize_for_specificity detects vague indicators."""
        vague_prompts = [
            "Tell me something",
            "What about things?",
            "Explain stuff",
            "Show me etc",
        ]

        for prompt in vague_prompts:
            result = optimizer.optimize_for_specificity(prompt)
            assert "Please provide specific and detailed information." in result


class TestFallbackTemplateManager:
    """Tests for FallbackTemplateManager class."""

    @pytest.fixture
    def mock_prompt_store(self):
        """Create mock PromptStore."""
        store = MagicMock(spec=PromptStore)
        return store

    @pytest.fixture
    def manager(self, mock_prompt_store):
        """Create FallbackTemplateManager instance."""
        return FallbackTemplateManager(mock_prompt_store)

    def test_init(self, mock_prompt_store):
        """Test FallbackTemplateManager initialization."""
        manager = FallbackTemplateManager(mock_prompt_store)

        assert manager.prompt_store == mock_prompt_store
        assert manager.fallbacks == {}
        assert manager.default_fallback is None

    def test_register_fallback(self, manager):
        """Test register_fallback."""
        manager.register_fallback("primary", "fallback")

        assert "primary" in manager.fallbacks
        fallback = manager.fallbacks["primary"]
        assert fallback.primary_template == "primary"
        assert fallback.fallback_template == "fallback"
        assert fallback.condition is None

    def test_register_fallback_with_condition(self, manager):
        """Test register_fallback with condition."""
        def condition(ctx):
            return ctx.get("use_fallback", False)

        manager.register_fallback("primary", "fallback", condition=condition)

        assert "primary" in manager.fallbacks
        fallback = manager.fallbacks["primary"]
        assert fallback.condition is not None

    def test_set_default_fallback(self, manager):
        """Test set_default_fallback."""
        manager.set_default_fallback("default_template")

        assert manager.default_fallback == "default_template"

    def test_get_template_with_fallback_primary_found(self, manager, mock_prompt_store):
        """Test get_template_with_fallback when primary template is found."""
        template = PromptTemplate(name="primary", content="Primary content", version="1.0")
        mock_prompt_store.get.return_value = template

        result = manager.get_template_with_fallback("primary")

        assert result == template
        mock_prompt_store.get.assert_called_once_with("primary", tenant_id=None, version=None)

    def test_get_template_with_fallback_primary_not_found_uses_configured(self, manager, mock_prompt_store):
        """Test get_template_with_fallback uses configured fallback when primary not found."""
        manager.register_fallback("primary", "fallback")
        fallback_template = PromptTemplate(name="fallback", content="Fallback content", version="1.0")
        mock_prompt_store.get.side_effect = [None, fallback_template]

        result = manager.get_template_with_fallback("primary")

        assert result == fallback_template

    def test_get_template_with_fallback_uses_default(self, manager, mock_prompt_store):
        """Test get_template_with_fallback uses default fallback."""
        manager.set_default_fallback("default")
        default_template = PromptTemplate(name="default", content="Default content", version="1.0")
        
        # Mock get: first call (primary) returns None, second call (default) returns template
        calls = []
        def get_side_effect(name, tenant_id=None, version=None):
            calls.append(name)
            if name == "primary":
                return None
            elif name == "default":
                return default_template
            return None
        
        mock_prompt_store.get.side_effect = get_side_effect

        result = manager.get_template_with_fallback("primary")

        assert result == default_template
        # Should call get for "primary" first, then "default"
        assert "primary" in calls
        assert "default" in calls

    def test_get_template_with_fallback_conditional_true(self, manager, mock_prompt_store):
        """Test get_template_with_fallback with conditional fallback (condition true)."""
        def condition(ctx):
            return ctx.get("use_fallback", False)

        manager.register_fallback("primary", "fallback", condition=condition)
        primary_template = PromptTemplate(name="primary", content="Primary", version="1.0")
        fallback_template = PromptTemplate(name="fallback", content="Fallback", version="1.0")
        mock_prompt_store.get.side_effect = [primary_template, fallback_template]

        result = manager.get_template_with_fallback("primary", context={"use_fallback": True})

        assert result == fallback_template

    def test_get_template_with_fallback_conditional_false(self, manager, mock_prompt_store):
        """Test get_template_with_fallback with conditional fallback (condition false)."""
        def condition(ctx):
            return ctx.get("use_fallback", False)

        manager.register_fallback("primary", "fallback", condition=condition)
        primary_template = PromptTemplate(name="primary", content="Primary", version="1.0")
        mock_prompt_store.get.return_value = primary_template

        result = manager.get_template_with_fallback("primary", context={"use_fallback": False})

        assert result == primary_template

    def test_get_template_with_fallback_conditional_no_condition(self, manager, mock_prompt_store):
        """Test get_template_with_fallback with fallback that has no condition."""
        manager.register_fallback("primary", "fallback", condition=None)
        primary_template = PromptTemplate(name="primary", content="Primary", version="1.0")
        mock_prompt_store.get.return_value = primary_template

        result = manager.get_template_with_fallback("primary", context={})

        assert result == primary_template

    def test_get_template_with_fallback_conditional_error(self, manager, mock_prompt_store):
        """Test get_template_with_fallback when condition raises error."""
        def condition(ctx):
            raise RuntimeError("Condition error")

        manager.register_fallback("primary", "fallback", condition=condition)
        primary_template = PromptTemplate(name="primary", content="Primary", version="1.0")
        mock_prompt_store.get.return_value = primary_template

        # Should not raise, condition errors are ignored
        result = manager.get_template_with_fallback("primary", context={})

        assert result == primary_template

    def test_render_with_fallback_success(self, manager, mock_prompt_store):
        """Test render_with_fallback success."""
        template = PromptTemplate(name="primary", content="Hello {name}", version="1.0")
        mock_prompt_store.get.return_value = template

        result = manager.render_with_fallback("primary", {"name": "World"})

        assert result == "Hello World"

    def test_render_with_fallback_not_found(self, manager, mock_prompt_store):
        """Test render_with_fallback when template not found."""
        mock_prompt_store.get.return_value = None

        with pytest.raises(ValueError, match="Template 'primary' not found"):
            manager.render_with_fallback("primary", {})

    def test_render_with_fallback_with_tenant_id(self, manager, mock_prompt_store):
        """Test render_with_fallback with tenant_id."""
        template = PromptTemplate(name="primary", content="Hello {name}", version="1.0")
        mock_prompt_store.get.return_value = template

        result = manager.render_with_fallback("primary", {"name": "World"}, tenant_id="tenant-1")

        assert result == "Hello World"
        mock_prompt_store.get.assert_called_with("primary", tenant_id="tenant-1", version=None)


class TestEnhancedPromptContextManager:
    """Tests for EnhancedPromptContextManager class."""

    def test_init(self):
        """Test EnhancedPromptContextManager initialization."""
        with patch("src.core.prompt_context_management.prompt_manager.PromptContextManager") as mock_pcm_class:
            mock_base = MagicMock()
            mock_store = MagicMock(spec=PromptStore)
            mock_base.store = mock_store
            mock_pcm_class.return_value = mock_base

            manager = EnhancedPromptContextManager(max_tokens=5000, safety_margin=300)

            assert manager.base_manager is not None
            assert manager.dynamic_builder is not None
            assert manager.optimizer is not None
            assert manager.fallback_manager is not None
            mock_pcm_class.assert_called_once_with(max_tokens=5000, safety_margin=300)

    def test_render_basic(self):
        """Test render basic usage."""
        with patch("src.core.prompt_context_management.prompt_manager.PromptContextManager") as mock_pcm_class:
            mock_base = MagicMock()
            mock_store = MagicMock(spec=PromptStore)
            template = PromptTemplate(name="test", content="Hello {name}", version="1.0")
            mock_store.get.return_value = template
            mock_base.store = mock_store
            mock_pcm_class.return_value = mock_base

            manager = EnhancedPromptContextManager()
            manager.optimizer.optimize = Mock(side_effect=lambda p, c=None: p)

            result = manager.render("test", {"name": "World"})

            assert result == "Hello World"

    def test_render_with_fallback_disabled(self):
        """Test render with fallback disabled."""
        with patch("src.core.prompt_context_management.prompt_manager.PromptContextManager") as mock_pcm_class:
            mock_base = MagicMock()
            mock_store = MagicMock(spec=PromptStore)
            mock_base.store = mock_store
            mock_base.render = Mock(return_value="Base render result")
            mock_pcm_class.return_value = mock_base

            manager = EnhancedPromptContextManager()
            manager.optimizer.optimize = Mock(side_effect=lambda p, c=None: p)

            result = manager.render("test", {"name": "World"}, use_fallback=False)

            assert result == "Base render result"
            mock_base.render.assert_called_once()

    def test_render_with_optimization_disabled(self):
        """Test render with optimization disabled."""
        with patch("src.core.prompt_context_management.prompt_manager.PromptContextManager") as mock_pcm_class:
            mock_base = MagicMock()
            mock_store = MagicMock(spec=PromptStore)
            template = PromptTemplate(name="test", content="Hello {name}", version="1.0")
            mock_store.get.return_value = template
            mock_base.store = mock_store
            mock_pcm_class.return_value = mock_base

            manager = EnhancedPromptContextManager()
            manager.optimizer.optimize = Mock()

            result = manager.render("test", {"name": "World"}, optimize=False)

            assert result == "Hello World"
            manager.optimizer.optimize.assert_not_called()

    def test_render_with_context(self):
        """Test render with context."""
        with patch("src.core.prompt_context_management.prompt_manager.PromptContextManager") as mock_pcm_class:
            mock_base = MagicMock()
            mock_store = MagicMock(spec=PromptStore)
            template = PromptTemplate(name="test", content="Hello {name}", version="1.0")
            mock_store.get.return_value = template
            mock_base.store = mock_store
            mock_pcm_class.return_value = mock_base

            manager = EnhancedPromptContextManager()
            manager.dynamic_builder.build_dynamic_prompt = Mock(return_value="Dynamic prompt")
            manager.optimizer.optimize = Mock(side_effect=lambda p, c=None: p)

            result = manager.render("test", {"name": "World"}, context={"key": "value"})

            assert result == "Dynamic prompt"
            manager.dynamic_builder.build_dynamic_prompt.assert_called_once()

    def test_render_with_tenant_id(self):
        """Test render with tenant_id."""
        with patch("src.core.prompt_context_management.prompt_manager.PromptContextManager") as mock_pcm_class:
            mock_base = MagicMock()
            mock_store = MagicMock(spec=PromptStore)
            template = PromptTemplate(name="test", content="Hello {name}", version="1.0")
            mock_store.get.return_value = template
            mock_base.store = mock_store
            mock_pcm_class.return_value = mock_base

            manager = EnhancedPromptContextManager()
            manager.optimizer.optimize = Mock(side_effect=lambda p, c=None: p)

            result = manager.render("test", {"name": "World"}, tenant_id="tenant-1")

            assert result == "Hello World"

    def test_render_with_version(self):
        """Test render with version."""
        with patch("src.core.prompt_context_management.prompt_manager.PromptContextManager") as mock_pcm_class:
            mock_base = MagicMock()
            mock_store = MagicMock(spec=PromptStore)
            template = PromptTemplate(name="test", content="Hello {name}", version="1.0")
            mock_store.get.return_value = template
            mock_base.store = mock_store
            mock_pcm_class.return_value = mock_base

            manager = EnhancedPromptContextManager()
            manager.optimizer.optimize = Mock(side_effect=lambda p, c=None: p)

            result = manager.render("test", {"name": "World"}, version="2.0")

            assert result == "Hello World"

    def test_render_fallback_to_base_manager(self):
        """Test render falls back to base manager when template not found."""
        with patch("src.core.prompt_context_management.prompt_manager.PromptContextManager") as mock_pcm_class:
            mock_base = MagicMock()
            mock_store = MagicMock(spec=PromptStore)
            mock_store.get.return_value = None  # Template not found
            mock_base.store = mock_store
            mock_base.render = Mock(return_value="Base render result")
            mock_pcm_class.return_value = mock_base

            manager = EnhancedPromptContextManager()
            manager.optimizer.optimize = Mock(side_effect=lambda p, c=None: p)

            result = manager.render("test", {"name": "World"})

            assert result == "Base render result"
            mock_base.render.assert_called_once()

