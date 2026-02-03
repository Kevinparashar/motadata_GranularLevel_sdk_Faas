"""
Prompt and Context Management

Provides prompt templates, history tracking, and context window handling with
simple token estimation and truncation.
"""



import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PromptTemplate:
    """
    PromptTemplate.
    
    This class groups related SDK behaviour in one place.
    Keep the public methods small and well-typed for easy maintenance.
    """
    name: str
    version: str
    content: str
    tenant_id: Optional[str] = None  # Tenant context for multi-tenant SaaS
    metadata: Dict[str, Any] = field(default_factory=dict)


class PromptStore:
    """In-memory prompt template store with version support and tenant isolation."""

    def __init__(self) -> None:
        # Structure: {tenant_id: {template_name: {version: PromptTemplate}}}
        """
        Initialize PromptStore.
        """
        self._templates: Dict[Optional[str], Dict[str, Dict[str, PromptTemplate]]] = {}

    def add(self, template: PromptTemplate) -> None:
        """
        add.
        
        Args:
            template (PromptTemplate): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        tenant_id = template.tenant_id
        self._templates.setdefault(tenant_id, {}).setdefault(template.name, {})[
            template.version
        ] = template

    def get(
        self, name: str, tenant_id: Optional[str] = None, version: Optional[str] = None
    ) -> Optional[PromptTemplate]:
        """
        get.
        
        Args:
            name (str): Name value.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            version (Optional[str]): Input parameter for this operation.
        
        Returns:
            Optional[PromptTemplate]: Result if available, else None.
        """
        tenant_templates = self._templates.get(tenant_id, {})
        versions = tenant_templates.get(name)
        if not versions:
            return None
        if version:
            return versions.get(version)
        # return latest version by lexical order
        latest_version = sorted(versions.keys())[-1]
        return versions[latest_version]


class ContextWindowManager:
    """
    Handles context window sizing and token estimation.
    A lightweight token estimator is used (word count based).
    """

    def __init__(self, max_tokens: int = 4000, safety_margin: int = 200) -> None:
        """
        __init__.
        
        Args:
            max_tokens (int): Input parameter for this operation.
            safety_margin (int): Input parameter for this operation.
        """
        self.max_tokens = max_tokens
        self.safety_margin = safety_margin

    def estimate_tokens(self, text: str) -> int:
        # Simple heuristic: tokens ~= words
        """
        estimate_tokens.
        
        Args:
            text (str): Input parameter for this operation.
        
        Returns:
            int: Result of the operation.
        """
        return len(text.split())

    def truncate(self, text: str, max_tokens: Optional[int] = None) -> str:
        """
        truncate.
        
        Args:
            text (str): Input parameter for this operation.
            max_tokens (Optional[int]): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        limit = (max_tokens or self.max_tokens) - self.safety_margin
        tokens = text.split()
        if len(tokens) <= limit:
            return text
        return " ".join(tokens[:limit])

    def build_context(self, messages: List[str], max_tokens: Optional[int] = None) -> str:
        """
        build_context.
        
        Args:
            messages (List[str]): Chat messages in role/content format.
            max_tokens (Optional[int]): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        limit = (max_tokens or self.max_tokens) - self.safety_margin
        context_tokens = 0
        selected: List[str] = []
        for msg in reversed(messages):
            msg_tokens = self.estimate_tokens(msg)
            if context_tokens + msg_tokens > limit:
                break
            selected.append(msg)
            context_tokens += msg_tokens
        # reverse to preserve order
        return "\n".join(reversed(selected))


class PromptContextManager:
    """
    Manages prompt templates, history, and context window handling.
    """

    def __init__(self, max_tokens: int = 4000, safety_margin: int = 200) -> None:
        """
        __init__.
        
        Args:
            max_tokens (int): Input parameter for this operation.
            safety_margin (int): Input parameter for this operation.
        """
        self.store = PromptStore()
        self.history: List[str] = []
        self.window = ContextWindowManager(max_tokens=max_tokens, safety_margin=safety_margin)

    def render(
        self,
        template_name: str,
        variables: Dict[str, Any],
        tenant_id: Optional[str] = None,
        version: Optional[str] = None,
    ) -> str:
        """
        render.
        
        Args:
            template_name (str): Input parameter for this operation.
            variables (Dict[str, Any]): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            version (Optional[str]): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        
        Raises:
            ValueError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        template = self.store.get(template_name, tenant_id=tenant_id, version=version)
        if not template:
            raise ValueError(
                f"Template '{template_name}' not found for tenant '{tenant_id or 'global'}'"
            )
        # Basic Python format-style rendering
        return template.content.format(**variables)

    def add_template(
        self,
        name: str,
        version: str,
        content: str,
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        add_template.
        
        Args:
            name (str): Name value.
            version (str): Input parameter for this operation.
            content (str): Content text.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            None: Result of the operation.
        """
        tmpl = PromptTemplate(
            name=name,
            version=version,
            content=content,
            tenant_id=tenant_id,
            metadata=metadata or {},
        )
        self.store.add(tmpl)

    def record_history(self, prompt: str) -> None:
        """
        record_history.
        
        Args:
            prompt (str): Prompt text sent to the model.
        
        Returns:
            None: Result of the operation.
        """
        self.history.append(prompt)

    def build_context_with_history(self, new_message: str) -> str:
        """
        build_context_with_history.
        
        Args:
            new_message (str): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        messages = self.history + [new_message]
        return self.window.build_context(messages)

    def truncate_prompt(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        truncate_prompt.
        
        Args:
            prompt (str): Prompt text sent to the model.
            max_tokens (Optional[int]): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        return self.window.truncate(prompt, max_tokens=max_tokens)

    def strip_sensitive(self, text: str, patterns: Optional[List[str]] = None) -> str:
        """
        Basic redaction for sensitive patterns (e.g., API keys, emails).
        
        Args:
            text (str): Input parameter for this operation.
            patterns (Optional[List[str]]): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        patterns = patterns or [
            r"[A-Za-z0-9]{32,}",  # generic key-like strings
            r"[\\w\\.-]+@[\\w\\.-]+",  # emails
        ]
        redacted = text
        for pat in patterns:
            redacted = re.sub(pat, "[REDACTED]", redacted)
        return redacted
