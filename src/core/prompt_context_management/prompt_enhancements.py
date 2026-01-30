"""
Prompt System Enhancements

Dynamic prompting, automatic optimization, and fallback templates.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .prompt_manager import PromptStore, PromptTemplate


@dataclass
class FallbackTemplate:
    """Fallback template configuration."""

    primary_template: str
    fallback_template: str
    condition: Optional[Callable] = None  # Function that determines if fallback should be used


class DynamicPromptBuilder:
    """
    Dynamic prompting capabilities that adjust based on context.
    """

    def __init__(self, prompt_store: PromptStore):
        """
        Initialize dynamic prompt builder.

        Args:
            prompt_store: Prompt store instance
        """
        self.prompt_store = prompt_store
        self.context_adapters: List[Callable] = []

    def add_context_adapter(self, adapter: Callable) -> None:
        """
        Add a context adapter function.

        Args:
            adapter: Function that modifies prompt based on context
        """
        self.context_adapters.append(adapter)

    def build_dynamic_prompt(
        self,
        template_name: str,
        variables: Dict[str, Any],
        context: Dict[str, Any],
        tenant_id: Optional[str] = None,
        version: Optional[str] = None,
    ) -> str:
        """
        Build a dynamic prompt that adjusts based on context.

        Args:
            template_name: Base template name
            variables: Template variables
            context: Additional context for dynamic adjustment
            tenant_id: Optional tenant ID
            version: Optional template version

        Returns:
            Dynamically adjusted prompt
        """
        # Get base template
        template = self.prompt_store.get(template_name, tenant_id=tenant_id, version=version)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        # Start with base prompt
        prompt = template.content.format(**variables)

        # Apply context adapters
        for adapter in self.context_adapters:
            try:
                prompt = adapter(prompt, context, variables)
            except Exception:
                # Ignore adapter errors
                pass

        return prompt

    def adapt_for_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Adapt prompt based on context.

        Args:
            prompt: Base prompt
            context: Context information

        Returns:
            Adapted prompt
        """
        # Example: Add context-specific instructions
        if context.get("user_role") == "admin":
            prompt = f"[Admin Mode]\n{prompt}"

        if context.get("urgency") == "high":
            prompt = f"{prompt}\n\n[URGENT: Please prioritize this request]"

        if context.get("domain") == "technical":
            prompt = f"{prompt}\n\n[Technical Context: Provide detailed technical explanations]"

        return prompt


class PromptOptimizer:
    """
    Automatic prompt optimization techniques to maximize effectiveness.
    """

    def __init__(self):
        """Initialize prompt optimizer."""
        self.optimization_rules: List[Callable] = []
        self.optimization_history: List[Dict[str, Any]] = []

    def add_optimization_rule(self, rule: Callable) -> None:
        """
        Add an optimization rule.

        Args:
            rule: Function that optimizes a prompt
        """
        self.optimization_rules.append(rule)

    def optimize(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Optimize a prompt.

        Args:
            prompt: Prompt to optimize
            context: Optional context

        Returns:
            Optimized prompt
        """
        optimized = prompt

        # Apply optimization rules
        for rule in self.optimization_rules:
            try:
                optimized = rule(optimized, context or {})
            except Exception:
                # Ignore rule errors
                pass

        # Record optimization
        self.optimization_history.append(
            {
                "original": prompt,
                "optimized": optimized,
                "timestamp": datetime.now().isoformat(),
                "context": context,
            }
        )

        return optimized

    def optimize_for_clarity(self, prompt: str) -> str:
        """
        Optimize prompt for clarity.

        Args:
            prompt: Prompt to optimize

        Returns:
            Optimized prompt
        """
        # Remove redundant whitespace
        prompt = re.sub(r"\s+", " ", prompt)
        prompt = prompt.strip()

        # Ensure proper sentence structure
        if not prompt.endswith((".", "!", "?")):
            prompt += "."

        return prompt

    def optimize_for_length(self, prompt: str, max_length: int = 2000) -> str:
        """
        Optimize prompt length.

        Args:
            prompt: Prompt to optimize
            max_length: Maximum length

        Returns:
            Optimized prompt
        """
        if len(prompt) <= max_length:
            return prompt

        # Truncate intelligently (at sentence boundaries)
        sentences = re.split(r"([.!?]\s+)", prompt)
        truncated = ""

        for i in range(0, len(sentences), 2):
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
            if len(truncated + sentence) > max_length:
                break
            truncated += sentence

        return truncated or prompt[:max_length]

    def optimize_for_specificity(self, prompt: str) -> str:
        """
        Optimize prompt for specificity.

        Args:
            prompt: Prompt to optimize

        Returns:
            Optimized prompt
        """
        # Add specificity markers if missing
        if "be specific" not in prompt.lower() and "detailed" not in prompt.lower():
            # Check if prompt is vague
            vague_indicators = ["something", "things", "stuff", "etc"]
            if any(indicator in prompt.lower() for indicator in vague_indicators):
                prompt += "\n\nPlease provide specific and detailed information."

        return prompt


class FallbackTemplateManager:
    """
    Fallback templates to ensure continuity if a template is not found.
    """

    def __init__(self, prompt_store: PromptStore):
        """
        Initialize fallback template manager.

        Args:
            prompt_store: Prompt store instance
        """
        self.prompt_store = prompt_store
        self.fallbacks: Dict[str, FallbackTemplate] = {}
        self.default_fallback: Optional[str] = None

    def register_fallback(
        self, primary_template: str, fallback_template: str, condition: Optional[Callable] = None
    ) -> None:
        """
        Register a fallback template.

        Args:
            primary_template: Primary template name
            fallback_template: Fallback template name
            condition: Optional condition function
        """
        self.fallbacks[primary_template] = FallbackTemplate(
            primary_template=primary_template,
            fallback_template=fallback_template,
            condition=condition,
        )

    def set_default_fallback(self, template_name: str) -> None:
        """
        Set default fallback template.

        Args:
            template_name: Default fallback template name
        """
        self.default_fallback = template_name

    def _try_conditional_fallback(
        self,
        template_name: str,
        tenant_id: Optional[str],
        version: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> Optional[PromptTemplate]:
        """Try to use conditional fallback if condition is met."""
        if template_name not in self.fallbacks:
            return None
        
        fallback_config = self.fallbacks[template_name]
        if not fallback_config.condition:
            return None
        
        try:
            if fallback_config.condition(context or {}):
                return self.prompt_store.get(
                    fallback_config.fallback_template,
                    tenant_id=tenant_id,
                    version=version,
                )
        except Exception:
            pass
        
        return None

    def _get_configured_fallback(
        self,
        template_name: str,
        tenant_id: Optional[str],
        version: Optional[str],
    ) -> Optional[PromptTemplate]:
        """Get the configured fallback template."""
        if template_name not in self.fallbacks:
            return None
        
        fallback_config = self.fallbacks[template_name]
        return self.prompt_store.get(
            fallback_config.fallback_template,
            tenant_id=tenant_id,
            version=version,
        )

    def _get_default_fallback(
        self,
        tenant_id: Optional[str],
        version: Optional[str],
    ) -> Optional[PromptTemplate]:
        """Get the default fallback template."""
        if not self.default_fallback:
            return None
        
        return self.prompt_store.get(
            self.default_fallback,
            tenant_id=tenant_id,
            version=version,
        )

    def get_template_with_fallback(
        self,
        template_name: str,
        tenant_id: Optional[str] = None,
        version: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[PromptTemplate]:
        """
        Get template with fallback support.

        Args:
            template_name: Primary template name
            tenant_id: Optional tenant ID
            version: Optional template version
            context: Optional context for condition evaluation

        Returns:
            Template (primary or fallback)
        """
        # Try primary template
        template = self.prompt_store.get(template_name, tenant_id=tenant_id, version=version)

        if template:
            # Check if conditional fallback should be used
            conditional_fallback = self._try_conditional_fallback(
                template_name, tenant_id, version, context
            )
            return conditional_fallback if conditional_fallback else template

        # Primary not found, try configured fallback
        fallback = self._get_configured_fallback(template_name, tenant_id, version)
        if fallback:
            return fallback

        # Try default fallback
        return self._get_default_fallback(tenant_id, version)

    def render_with_fallback(
        self,
        template_name: str,
        variables: Dict[str, Any],
        tenant_id: Optional[str] = None,
        version: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render template with fallback support.

        Args:
            template_name: Primary template name
            variables: Template variables
            tenant_id: Optional tenant ID
            version: Optional template version
            context: Optional context

        Returns:
            Rendered prompt

        Raises:
            ValueError: If no template (including fallbacks) is found
        """
        template = self.get_template_with_fallback(
            template_name, tenant_id=tenant_id, version=version, context=context
        )

        if not template:
            raise ValueError(
                f"Template '{template_name}' not found and no fallback available "
                f"for tenant '{tenant_id or 'global'}'"
            )

        return template.content.format(**variables)


class EnhancedPromptContextManager:
    """
    Enhanced prompt context manager with all new features.
    """

    def __init__(self, max_tokens: int = 4000, safety_margin: int = 200):
        """
        Initialize enhanced prompt context manager.

        Args:
            max_tokens: Maximum tokens
            safety_margin: Safety margin for token estimation
        """
        from .prompt_manager import PromptContextManager

        self.base_manager = PromptContextManager(max_tokens=max_tokens, safety_margin=safety_margin)
        self.dynamic_builder = DynamicPromptBuilder(self.base_manager.store)
        self.optimizer = PromptOptimizer()
        self.fallback_manager = FallbackTemplateManager(self.base_manager.store)

        # Add default optimization rules
        self.optimizer.add_optimization_rule(self.optimizer.optimize_for_clarity)
        self.optimizer.add_optimization_rule(self.optimizer.optimize_for_specificity)

    def render(
        self,
        template_name: str,
        variables: Dict[str, Any],
        tenant_id: Optional[str] = None,
        version: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        optimize: bool = True,
        use_fallback: bool = True,
    ) -> str:
        """
        Render prompt with all enhancements.

        Args:
            template_name: Template name
            variables: Template variables
            tenant_id: Optional tenant ID
            version: Optional template version
            context: Optional context for dynamic adjustment
            optimize: Whether to optimize the prompt
            use_fallback: Whether to use fallback templates

        Returns:
            Rendered and enhanced prompt
        """
        # Get template with fallback
        if use_fallback:
            template = self.fallback_manager.get_template_with_fallback(
                template_name, tenant_id=tenant_id, version=version, context=context
            )
            if template:
                prompt = template.content.format(**variables)
            else:
                # Fallback to base manager
                prompt = self.base_manager.render(
                    template_name, variables, tenant_id=tenant_id, version=version
                )
        else:
            prompt = self.base_manager.render(
                template_name, variables, tenant_id=tenant_id, version=version
            )

        # Apply dynamic adjustments
        if context:
            prompt = self.dynamic_builder.build_dynamic_prompt(
                template_name, variables, context, tenant_id=tenant_id, version=version
            )

        # Optimize if requested
        if optimize:
            prompt = self.optimizer.optimize(prompt, context)

        return prompt
