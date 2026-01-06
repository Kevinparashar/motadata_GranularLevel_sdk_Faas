"""
Prompt and Context Management

Provides prompt templates, history tracking, and context window handling with
simple token estimation and truncation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PromptTemplate:
    name: str
    version: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class PromptStore:
    """In-memory prompt template store with version support."""

    def __init__(self) -> None:
        self._templates: Dict[str, Dict[str, PromptTemplate]] = {}

    def add(self, template: PromptTemplate) -> None:
        self._templates.setdefault(template.name, {})[template.version] = template

    def get(self, name: str, version: Optional[str] = None) -> Optional[PromptTemplate]:
        versions = self._templates.get(name)
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
        self.max_tokens = max_tokens
        self.safety_margin = safety_margin

    def estimate_tokens(self, text: str) -> int:
        # Simple heuristic: tokens ~= words
        return len(text.split())

    def truncate(self, text: str, max_tokens: Optional[int] = None) -> str:
        limit = (max_tokens or self.max_tokens) - self.safety_margin
        tokens = text.split()
        if len(tokens) <= limit:
            return text
        return " ".join(tokens[:limit])

    def build_context(self, messages: List[str], max_tokens: Optional[int] = None) -> str:
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
        self.store = PromptStore()
        self.history: List[str] = []
        self.window = ContextWindowManager(max_tokens=max_tokens, safety_margin=safety_margin)

    def render(self, template_name: str, variables: Dict[str, Any], version: Optional[str] = None) -> str:
        template = self.store.get(template_name, version=version)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        # Basic Python format-style rendering
        return template.content.format(**variables)

    def add_template(self, name: str, version: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        tmpl = PromptTemplate(name=name, version=version, content=content, metadata=metadata or {})
        self.store.add(tmpl)

    def record_history(self, prompt: str) -> None:
        self.history.append(prompt)

    def build_context_with_history(self, new_message: str) -> str:
        messages = self.history + [new_message]
        return self.window.build_context(messages)

    def truncate_prompt(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        return self.window.truncate(prompt, max_tokens=max_tokens)

    def strip_sensitive(self, text: str, patterns: Optional[List[str]] = None) -> str:
        """
        Basic redaction for sensitive patterns (e.g., API keys, emails).
        """
        patterns = patterns or [
            r"[A-Za-z0-9]{32,}",  # generic key-like strings
            r"[\\w\\.-]+@[\\w\\.-]+",  # emails
        ]
        redacted = text
        for pat in patterns:
            redacted = re.sub(pat, "[REDACTED]", redacted)
        return redacted


