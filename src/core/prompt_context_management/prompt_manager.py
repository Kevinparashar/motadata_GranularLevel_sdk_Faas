"""
Prompt and Context Management

Provides prompt templates, history tracking, and context window handling with
simple token estimation and truncation.
"""


import re
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ...faas.shared.dal.prompt_history_dal import PromptHistoryDAL  
    from ...faas.shared.dal.prompt_template_dal import PromptTemplateDAL


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
    """Prompt template store with version support and tenant isolation.
    
    Supports both in-memory storage (default) and database persistence via PromptTemplateDAL.
    """

    def __init__(self, template_dal: Optional["PromptTemplateDAL"] = None) -> None:
        """
        Initialize PromptStore.
        
        Args:
            template_dal: Optional PromptTemplateDAL instance for database persistence.
        """
        # Structure: {tenant_id: {template_name: {version: PromptTemplate}}}
        self._templates: Dict[Optional[str], Dict[str, Dict[str, PromptTemplate]]] = {}
        self._template_dal = template_dal

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
        
        # Persist to database if DAL is available
        if self._template_dal:
            import asyncio
            try:
                # Run async save in event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task
                    asyncio.create_task(
                        self._template_dal.save_template(
                            name=template.name,
                            version=template.version,
                            content=template.content,
                            tenant_id=tenant_id,
                            metadata=template.metadata,
                        )
                    )
                else:
                    loop.run_until_complete(
                        self._template_dal.save_template(
                            name=template.name,
                            version=template.version,
                            content=template.content,
                            tenant_id=tenant_id,
                            metadata=template.metadata,
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                asyncio.run(
                    self._template_dal.save_template(
                        name=template.name,
                        version=template.version,
                        content=template.content,
                        tenant_id=tenant_id,
                        metadata=template.metadata,
                    )
                )

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
        # Try in-memory first
        tenant_templates = self._templates.get(tenant_id, {})
        versions = tenant_templates.get(name)
        if versions:
            if version:
                return versions.get(version)
            # return latest version by lexical order
            latest_version = sorted(versions.keys())[-1]
            return versions[latest_version]
        
        # If not in memory and DAL is available, load from database
        if self._template_dal:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we can't use run_until_complete
                    # Return None and let caller handle async loading
                    return None
                else:
                    template_data = loop.run_until_complete(
                        self._template_dal.load_template(name, tenant_id, version)
                    )
                if template_data:
                    template = PromptTemplate(
                        name=template_data["name"],
                        version=template_data["version"],
                        content=template_data["content"],
                        tenant_id=tenant_id,
                        metadata=template_data.get("metadata", {}),
                    )
                    # Cache in memory
                    self._templates.setdefault(tenant_id, {}).setdefault(template.name, {})[
                        template.version
                    ] = template
                    return template
            except RuntimeError:
                # No event loop, create new one
                template_data = asyncio.run(
                    self._template_dal.load_template(name, tenant_id, version)
                )
                if template_data:
                    template = PromptTemplate(
                        name=template_data["name"],
                        version=template_data["version"],
                        content=template_data["content"],
                        tenant_id=tenant_id,
                        metadata=template_data.get("metadata", {}),
                    )
                    # Cache in memory
                    self._templates.setdefault(tenant_id, {}).setdefault(template.name, {})[
                        template.version
                    ] = template
                    return template
        
        return None


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

    def __init__(
        self,
        max_tokens: int = 4000,
        safety_margin: int = 200,
        otel_tracer: Optional[Any] = None,
        otel_metrics: Optional[Any] = None,
        codec_serializer: Optional[Any] = None,
        template_dal: Optional["PromptTemplateDAL"] = None,
        history_dal: Optional["PromptHistoryDAL"] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        context_id: Optional[str] = None,
        load_history_on_init: bool = True,
        require_persistence: bool = True,
    ) -> None:
        """
        __init__.
        
        Args:
            max_tokens (int): Input parameter for this operation.
            safety_margin (int): Input parameter for this operation.
            otel_tracer: Optional OTEL tracer for distributed tracing
            otel_metrics: Optional OTEL metrics for metrics collection
            codec_serializer: Optional CodecSerializer instance for message encoding/decoding
            template_dal: Optional PromptTemplateDAL instance for template persistence
            history_dal: Optional PromptHistoryDAL instance for history persistence (required for guaranteed persistence when tenant_id is set)
            tenant_id: Optional tenant ID for multi-tenant isolation
            user_id: Optional user ID for user-specific history
            context_id: Optional context ID (e.g., conversation_id, agent_id) for context-specific history
            load_history_on_init: Whether to load history from DAL on initialization (default: True)
            require_persistence: If True, raise ValueError when tenant_id is set but history_dal is not provided (default: True)
        
        Raises:
            ValueError: If require_persistence is True and tenant_id is set but history_dal is not provided.
        """
        # Guaranteed persistence: require history_dal when tenant_id is set
        if require_persistence and tenant_id and not history_dal:
            raise ValueError(
                "history_dal is required when tenant_id is provided for guaranteed persistence. "
                "Provide history_dal or set require_persistence=False to allow in-memory-only storage."
            )
        
        self.store = PromptStore(template_dal=template_dal)
        self.history: List[str] = []
        self._history_dal = history_dal
        self._tenant_id = tenant_id
        self._user_id = user_id
        self._context_id = context_id
        self.window = ContextWindowManager(max_tokens=max_tokens, safety_margin=safety_margin)
        
        # Load context window state from DAL if available
        if self._history_dal and self._tenant_id and load_history_on_init:
            self._load_context_window_state()
        
        # Load history from DAL if available
        if self._history_dal and self._tenant_id and load_history_on_init:
            self._load_history()

        # OTEL Integration (optional)
        self.otel_tracer: Optional[Any] = otel_tracer
        self.otel_metrics: Optional[Any] = otel_metrics

        # Initialize OTEL if not provided
        if self.otel_tracer is None:
            try:
                from ..otel_integration import create_otel_tracer

                self.otel_tracer = create_otel_tracer(service_name="prompt-context-manager")
            except (ImportError, Exception):
                self.otel_tracer = None

        if self.otel_metrics is None:
            try:
                from ..otel_integration import create_otel_metrics

                self.otel_metrics = create_otel_metrics(service_name="prompt-context-manager")
            except (ImportError, Exception):
                self.otel_metrics = None

        # CODEC Integration (optional)
        self.codec_serializer: Optional[Any] = codec_serializer

        # Initialize CODEC if not provided
        if self.codec_serializer is None:
            try:
                from ..codec_integration import create_codec_serializer

                self.codec_serializer = create_codec_serializer(codec_type="json")
            except (ImportError, Exception):
                self.codec_serializer = None

    def _load_history(self) -> None:
        """
        Load history from DAL on initialization.
        
        This method is called during initialization to restore history from persistent storage.
        """
        if not self._history_dal or not self._tenant_id:
            return
        
        try:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task
                    asyncio.create_task(self._load_history_async())
                else:
                    loop.run_until_complete(self._load_history_async())
            except RuntimeError:
                # No event loop, create new one
                asyncio.run(self._load_history_async())
        except Exception as e:
            logger = __import__("logging").getLogger(__name__)
            logger.debug(f"Failed to load history from DAL: {e}")

    async def _load_history_async(self) -> None:
        """Async helper to load history from DAL."""
        if not self._history_dal or not self._tenant_id:
            return
        
        try:
            history_records = await self._history_dal.get_history(
                tenant_id=self._tenant_id,
                user_id=self._user_id,
                context_id=self._context_id,
                limit=1000,  # Load up to 1000 recent prompts
                offset=0,
            )
            
            # Restore history in chronological order (oldest first)
            if history_records:
                self.history = [record["prompt"] for record in reversed(history_records)]
        except Exception as e:
            logger = __import__("logging").getLogger(__name__)
            logger.debug(f"Failed to load history from DAL: {e}")

    def _load_context_window_state(self) -> None:
        """
        Load context window state from DAL on initialization.
        
        This method is called during initialization to restore context window state from persistent storage.
        """
        if not self._history_dal or not self._tenant_id:
            return
        
        try:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task
                    asyncio.create_task(self._load_context_window_state_async())
                else:
                    loop.run_until_complete(self._load_context_window_state_async())
            except RuntimeError:
                # No event loop, create new one
                asyncio.run(self._load_context_window_state_async())
        except Exception as e:
            logger = __import__("logging").getLogger(__name__)
            logger.debug(f"Failed to load context window state from DAL: {e}")

    async def _load_context_window_state_async(self) -> None:
        """Async helper to load context window state from DAL."""
        if not self._history_dal or not self._tenant_id:
            return
        
        try:
            state = await self._history_dal.get_context_window_state(
                tenant_id=self._tenant_id,
                user_id=self._user_id,
                context_id=self._context_id,
            )
            
            if state:
                # Restore context window settings
                self.window.max_tokens = state.get("max_tokens", self.window.max_tokens)
                self.window.safety_margin = state.get("safety_margin", self.window.safety_margin)
                
                # Restore window state if available
                window_state = state.get("window_state")
                if window_state:
                    # Store window state for future use
                    self._window_state = window_state
        except Exception as e:
            logger = __import__("logging").getLogger(__name__)
            logger.debug(f"Failed to load context window state from DAL: {e}")

    def _save_context_window_state(self) -> None:
        """
        Save context window state to DAL.
        
        This method saves the current context window state for persistence.
        """
        if not self._history_dal or not self._tenant_id:
            return
        
        try:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task
                    asyncio.create_task(
                        self._history_dal.save_context_window_state(
                            tenant_id=self._tenant_id,
                            user_id=self._user_id,
                            context_id=self._context_id,
                            max_tokens=self.window.max_tokens,
                            safety_margin=self.window.safety_margin,
                            current_tokens=sum(self.window.estimate_tokens(p) for p in self.history),
                            window_state=getattr(self, "_window_state", None),
                        )
                    )
                else:
                    loop.run_until_complete(
                        self._history_dal.save_context_window_state(
                            tenant_id=self._tenant_id,
                            user_id=self._user_id,
                            context_id=self._context_id,
                            max_tokens=self.window.max_tokens,
                            safety_margin=self.window.safety_margin,
                            current_tokens=sum(self.window.estimate_tokens(p) for p in self.history),
                            window_state=getattr(self, "_window_state", None),
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                asyncio.run(
                    self._history_dal.save_context_window_state(
                        tenant_id=self._tenant_id,
                        user_id=self._user_id,
                        context_id=self._context_id,
                        max_tokens=self.window.max_tokens,
                        safety_margin=self.window.safety_margin,
                        current_tokens=sum(self.window.estimate_tokens(p) for p in self.history),
                        window_state=getattr(self, "_window_state", None),
                    )
                )
        except Exception as e:
            logger = __import__("logging").getLogger(__name__)
            logger.debug(f"Failed to save context window state to DAL: {e}")

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
        start_time = time.time()

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("prompt_context_manager.render") as trace:
                trace.set_attribute("prompt_context_manager.template_name", template_name)
                trace.set_attribute("prompt_context_manager.has_version", version is not None)
                trace.set_attribute("prompt_context_manager.variables_count", len(variables))
                from ..utils.tenant_utils import add_tenant_attributes_to_span
                add_tenant_attributes_to_span(trace, tenant_id, attribute_prefix="prompt_context_manager")

                try:
                    template = self.store.get(template_name, tenant_id=tenant_id, version=version)
                    if not template:
                        raise ValueError(
                            f"Template '{template_name}' not found for tenant '{tenant_id or 'global'}'"
                        )
                    # Basic Python format-style rendering
                    result = template.content.format(**variables)

                    duration = time.time() - start_time
                    trace.set_attribute("prompt_context_manager.result_length", len(result))

                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "prompt_context_manager.render.duration",
                            duration,
                            {"template_name": template_name},
                        )
                        self.otel_metrics.increment_counter(
                            "prompt_context_manager.operations",
                            amount=1.0,
                            attributes={
                                "operation": "render",
                                "status": "success",
                                "template_name": template_name,
                            },
                        )

                    return result
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "prompt_context_manager.render.duration",
                            duration,
                            {"status": "error"},
                        )
                        self.otel_metrics.increment_counter(
                            "prompt_context_manager.operations",
                            amount=1.0,
                            attributes={
                                "operation": "render",
                                "status": "error",
                                "error_type": type(e).__name__,
                            },
                        )
                    raise
        else:
            # No OTEL - execute without tracing
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
        start_time = time.time()

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("prompt_context_manager.add_template") as trace:
                trace.set_attribute("prompt_context_manager.template_name", name)
                trace.set_attribute("prompt_context_manager.template_version", version)
                trace.set_attribute("prompt_context_manager.content_length", len(content))
                trace.set_attribute("prompt_context_manager.has_metadata", metadata is not None)
                from ..utils.tenant_utils import add_tenant_attributes_to_span
                add_tenant_attributes_to_span(trace, tenant_id, attribute_prefix="prompt_context_manager")

                try:
                    tmpl = PromptTemplate(
                        name=name,
                        version=version,
                        content=content,
                        tenant_id=tenant_id,
                        metadata=metadata or {},
                    )
                    self.store.add(tmpl)

                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "prompt_context_manager.add_template.duration",
                            duration,
                            {"template_name": name},
                        )
                        self.otel_metrics.increment_counter(
                            "prompt_context_manager.operations",
                            amount=1.0,
                            attributes={
                                "operation": "add_template",
                                "status": "success",
                                "template_name": name,
                            },
                        )
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "prompt_context_manager.add_template.duration",
                            duration,
                            {"status": "error"},
                        )
                        self.otel_metrics.increment_counter(
                            "prompt_context_manager.operations",
                            amount=1.0,
                            attributes={
                                "operation": "add_template",
                                "status": "error",
                                "error_type": type(e).__name__,
                            },
                        )
                    raise
        else:
            # No OTEL - execute without tracing
            tmpl = PromptTemplate(
                name=name,
                version=version,
                content=content,
                tenant_id=tenant_id,
                metadata=metadata or {},
            )
            self.store.add(tmpl)

    def record_history(
        self,
        prompt: str,
        user_id: Optional[str] = None,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        record_history.
        
        Args:
            prompt (str): Prompt text sent to the model.
            user_id: Optional user identifier.
            context_id: Optional context identifier (e.g., conversation_id, agent_id).
            metadata: Optional metadata.
        
        Returns:
            None: Result of the operation.
        
        Raises:
            ValueError: If history_dal is required but not provided (guaranteed persistence mode).
        """
        self.history.append(prompt)
        
        # Use provided user_id/context_id or fall back to instance defaults
        effective_user_id = user_id or self._user_id
        effective_context_id = context_id or self._context_id
        
        # Guaranteed persistence: history_dal should be available if tenant_id is set
        # (This should have been validated in __init__, but check again for safety)
        if self._tenant_id and not self._history_dal:
            logger = __import__("logging").getLogger(__name__)
            logger.warning(
                "History DAL not available but tenant_id is set. "
                "History will be stored in-memory only. "
                "This should not happen if require_persistence=True (default)."
            )
        
        # Persist to database if DAL is available (guaranteed when tenant_id is set)
        if self._history_dal and self._tenant_id:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task
                    asyncio.create_task(
                        self._history_dal.save_history(
                            prompt=prompt,
                            tenant_id=self._tenant_id,
                            user_id=effective_user_id,
                            context_id=effective_context_id,
                            metadata=metadata,
                        )
                    )
                else:
                    loop.run_until_complete(
                        self._history_dal.save_history(
                            prompt=prompt,
                            tenant_id=self._tenant_id,
                            user_id=effective_user_id,
                            context_id=effective_context_id,
                            metadata=metadata,
                        )
                    )
            except RuntimeError:
                # No event loop, create new one
                asyncio.run(
                    self._history_dal.save_history(
                        prompt=prompt,
                        tenant_id=self._tenant_id,
                        user_id=effective_user_id,
                        context_id=effective_context_id,
                        metadata=metadata,
                    )
                )
            
            # Save context window state after recording history
            self._save_context_window_state()

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

    def update_context_window(
        self,
        max_tokens: Optional[int] = None,
        safety_margin: Optional[int] = None,
    ) -> None:
        """
        Update context window settings and persist to DAL.
        
        Args:
            max_tokens: Optional new maximum tokens value.
            safety_margin: Optional new safety margin value.
        
        Returns:
            None: Result of the operation.
        """
        if max_tokens is not None:
            self.window.max_tokens = max_tokens
        if safety_margin is not None:
            self.window.safety_margin = safety_margin
        
        # Persist context window state
        self._save_context_window_state()

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
            # Safer email regex to prevent ReDoS - use bounded character classes
            r"[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # emails - bounded pattern
        ]
        redacted = text
        for pat in patterns:
            redacted = re.sub(pat, "[REDACTED]", redacted)
        return redacted

    async def encode_template(
        self, template: PromptTemplate, schema_version: str = "1.0"
    ) -> bytes:
        """
        Encode PromptTemplate to bytes using codec serializer.
        
        Args:
            template: PromptTemplate instance to encode
            schema_version: Schema version to use
        
        Returns:
            Encoded bytes
        
        Raises:
            ValueError: If codec serializer is not configured
        """
        if not self.codec_serializer:
            # Try to import and use default codec serializer
            try:
                from ..codec_integration import encode_prompt_template
                return await encode_prompt_template(template, codec=None, schema_version=schema_version)
            except ImportError:
                raise ValueError(
                    "Codec serializer not configured and codec_integration not available. "
                    "Configure codec_serializer in PromptContextManager initialization or ensure codec_integration is available."
                )
        
        from ..codec_integration import encode_prompt_template
        return await encode_prompt_template(template, codec=self.codec_serializer, schema_version=schema_version)

    async def decode_template(
        self, payload: bytes, target_version: Optional[str] = None
    ) -> PromptTemplate:
        """
        Decode bytes to PromptTemplate using codec serializer.
        
        Args:
            payload: Encoded bytes to decode
            target_version: Target schema version (migrates if different)
        
        Returns:
            PromptTemplate instance
        
        Raises:
            ValueError: If codec serializer is not configured
        """
        if not self.codec_serializer:
            # Try to import and use default codec serializer
            try:
                from ..codec_integration import decode_prompt_template
                decoded_data = await decode_prompt_template(payload, codec=None, target_version=target_version)
                return PromptTemplate(**decoded_data)
            except ImportError:
                raise ValueError(
                    "Codec serializer not configured and codec_integration not available. "
                    "Configure codec_serializer in PromptContextManager initialization or ensure codec_integration is available."
                )
        
        from ..codec_integration import decode_prompt_template
        decoded_data = await decode_prompt_template(payload, codec=self.codec_serializer, target_version=target_version)
        return PromptTemplate(**decoded_data)
