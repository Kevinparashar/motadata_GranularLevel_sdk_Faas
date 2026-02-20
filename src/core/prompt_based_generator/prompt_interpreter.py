"""
Prompt Interpreter

Core prompt interpretation logic for converting natural language prompts
into structured configurations for agents and tools.
"""


import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Protocol

from pydantic import BaseModel, Field

from ..utils.error_handler import create_error_with_suggestion
from ..utils.type_helpers import GatewayProtocol, MetadataDict
from .exceptions import PromptInterpretationError

# Constants
JSON_CODE_BLOCK_MARKER = "```json"


class CacheProtocol(Protocol):
    """Protocol for cache interface."""

    async def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[str]:
        """
        Get value from cache.
        
        Args:
            key (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Optional[str]: Returned text value.
        """
        ...

    async def set(
        self, key: str, value: str, ttl: Optional[int] = None, tenant_id: Optional[str] = None
    ) -> None:
        """
        Set value in cache.
        
        Args:
            key (str): Input parameter for this operation.
            value (str): Input parameter for this operation.
            ttl (Optional[int]): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        ...


class AgentRequirements(BaseModel):
    """Extracted agent requirements from prompt."""

    name: str
    description: str
    capabilities: List[str] = Field(default_factory=list)
    system_prompt: str
    required_tools: List[str] = Field(default_factory=list)
    memory_config: Dict[str, Any] = Field(default_factory=dict)
    max_context_tokens: int = 4000
    enable_tool_calling: bool = True
    metadata: MetadataDict = Field(default_factory=dict)


class ToolRequirements(BaseModel):
    """Extracted tool requirements from prompt."""

    name: str
    description: str
    function_name: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    return_type: str = "Any"
    code_template: Optional[str] = None
    metadata: MetadataDict = Field(default_factory=dict)


class PromptInterpreter:
    """
    Interprets natural language prompts to extract requirements.

    Uses LLM to analyze prompts and extract structured requirements
    for agent and tool creation.
    """

    def __init__(
        self,
        gateway: GatewayProtocol,
        otel_tracer: Optional[Any] = None,
        otel_metrics: Optional[Any] = None,
        codec_serializer: Optional[Any] = None,
    ):
        """
        Initialize prompt interpreter.
        
        Args:
            gateway (GatewayProtocol): Gateway client used for LLM calls.
            otel_tracer: Optional OTEL tracer for distributed tracing
            otel_metrics: Optional OTEL metrics for metrics collection
            codec_serializer: Optional CodecSerializer instance for message encoding/decoding
        """
        self.gateway = gateway

        # OTEL Integration (optional)
        self.otel_tracer: Optional[Any] = otel_tracer
        self.otel_metrics: Optional[Any] = otel_metrics

        # Initialize OTEL if not provided
        if self.otel_tracer is None:
            try:
                from ..otel_integration import create_otel_tracer

                self.otel_tracer = create_otel_tracer(service_name="prompt-interpreter")
            except (ImportError, Exception):
                self.otel_tracer = None

        if self.otel_metrics is None:
            try:
                from ..otel_integration import create_otel_metrics

                self.otel_metrics = create_otel_metrics(service_name="prompt-interpreter")
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
        self._agent_prompt_template = """You are an expert at analyzing requirements for AI agents. 
Given a user's natural language description, extract the following information:

1. Agent name (short, descriptive)
2. Agent description (detailed)
3. List of capabilities (what the agent can do)
4. System prompt (instructions for the agent's behavior)
5. Required tools (list of tool names/descriptions needed)
6. Memory configuration (if needed)
7. Context token limit (default: 4000)

User prompt: {prompt}

Respond with a JSON object containing:
{{
    "name": "agent name",
    "description": "detailed description",
    "capabilities": ["capability1", "capability2"],
    "system_prompt": "system prompt text",
    "required_tools": ["tool1", "tool2"],
    "memory_config": {{"max_episodic": 500, "max_semantic": 2000}},
    "max_context_tokens": 4000,
    "enable_tool_calling": true,
    "metadata": {{}}
}}

Only return valid JSON, no additional text."""

        self._tool_prompt_template = """You are an expert at analyzing requirements for AI tools. 
Given a user's natural language description, extract the following information:

1. Tool name (short, descriptive)
2. Tool description (detailed)
3. Function name (Python function name)
4. Parameters (list of parameter definitions with name, type, description, required)
5. Return type (Python type)
6. Code template (Python code implementing the tool)

User prompt: {prompt}

Respond with a JSON object containing:
{{
    "name": "tool name",
    "description": "detailed description",
    "function_name": "function_name",
    "parameters": [
        {{"name": "param1", "type": "str", "description": "param description", "required": true}}
    ],
    "return_type": "int",
    "code_template": "def function_name(param1: str) -> int:\\n    # implementation\\n    return result",
    "metadata": {{}}
}}

Only return valid JSON, no additional text."""

    def _hash_prompt(self, prompt: str) -> str:
        """
        Generate hash for prompt caching.
        
        Args:
            prompt (str): Prompt text sent to the model.
        
        Returns:
            str: Returned text value.
        """
        return hashlib.sha256(prompt.encode()).hexdigest()

    async def interpret_agent_prompt(
        self, prompt: str, cache: Optional[CacheProtocol] = None, tenant_id: Optional[str] = None
    ) -> AgentRequirements:
        """
        Interpret a prompt for agent creation.
        
        Args:
            prompt (str): Prompt text sent to the model.
            cache (Optional[CacheProtocol]): Cache instance used to store and fetch cached results.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            AgentRequirements: Result of the operation.
        
        Raises:
            create_error_with_suggestion: Raised when this function detects an invalid state or when an underlying call fails.
        """
        start_time = time.time()

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("prompt_interpreter.interpret_agent") as trace:
                trace.set_attribute("prompt_interpreter.type", "agent")
                trace.set_attribute("prompt_interpreter.prompt_length", len(prompt))
                trace.set_attribute("prompt_interpreter.has_cache", cache is not None)
                from ..utils.tenant_utils import add_tenant_attributes_to_span
                add_tenant_attributes_to_span(trace, tenant_id, attribute_prefix="prompt_interpreter")

                try:
                    # Check cache first
                    if cache:
                        prompt_hash = self._hash_prompt(prompt)
                        cached = await cache.get(f"agent_interpretation:{prompt_hash}", tenant_id=tenant_id)
                        if cached:
                            try:
                                requirements = AgentRequirements(**json.loads(cached))
                                trace.set_attribute("prompt_interpreter.cache_hit", True)

                                duration = time.time() - start_time
                                if self.otel_metrics:
                                    self.otel_metrics.record_histogram(
                                        "prompt_interpreter.interpret_agent.duration",
                                        duration,
                                        {"cache_hit": "true"},
                                    )
                                    self.otel_metrics.increment_counter(
                                        "prompt_interpreter.operations",
                                        amount=1.0,
                                        attributes={
                                            "type": "agent",
                                            "status": "success",
                                            "cache_hit": "true",
                                        },
                                    )

                                return requirements
                            except (json.JSONDecodeError, KeyError, TypeError) as e:
                                # Cache invalid, continue with interpretation
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.debug(f"Invalid cached agent interpretation, re-interpreting: {e}")

                    # Use LLM to interpret prompt
                    formatted_prompt = self._agent_prompt_template.format(prompt=prompt)

                    response = await self.gateway.generate_async(
                        prompt=formatted_prompt, model="gpt-4", temperature=0.3, max_tokens=2000
                    )

                    # Parse JSON response
                    response_text = response.text.strip()

                    # Extract JSON from response (handle markdown code blocks)
                    if JSON_CODE_BLOCK_MARKER in response_text:
                        response_text = response_text.split(JSON_CODE_BLOCK_MARKER)[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()

                    config = json.loads(response_text)

                    # Create AgentRequirements object
                    requirements = AgentRequirements(**config)

                    # Cache the interpretation
                    if cache:
                        prompt_hash = self._hash_prompt(prompt)
                        await cache.set(
                            f"agent_interpretation:{prompt_hash}",
                            json.dumps(config),
                            tenant_id=tenant_id,
                            ttl=86400,  # 24 hours
                        )

                    duration = time.time() - start_time
                    trace.set_attribute("prompt_interpreter.cache_hit", False)
                    trace.set_attribute("prompt_interpreter.agent_name", requirements.name)

                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "prompt_interpreter.interpret_agent.duration",
                            duration,
                            {"cache_hit": "false"},
                        )
                        self.otel_metrics.increment_counter(
                            "prompt_interpreter.operations",
                            amount=1.0,
                            attributes={
                                "type": "agent",
                                "status": "success",
                                "cache_hit": "false",
                            },
                        )

                    return requirements

                except json.JSONDecodeError as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "prompt_interpreter.interpret_agent.duration",
                            duration,
                            {"status": "error"},
                        )
                        self.otel_metrics.increment_counter(
                            "prompt_interpreter.operations",
                            amount=1.0,
                            attributes={
                                "type": "agent",
                                "status": "error",
                                "error_type": "json_parse_error",
                            },
                        )
                    raise create_error_with_suggestion(
                        PromptInterpretationError,
                        message=f"Failed to parse LLM response as JSON: {str(e)}",
                        suggestion="The LLM response was not valid JSON. Try rephrasing your prompt to be more specific about the agent requirements. The system expects structured JSON output.",
                        prompt=prompt,
                        reason="json_parse_error",
                        original_error=e,
                    )
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "prompt_interpreter.interpret_agent.duration",
                            duration,
                            {"status": "error"},
                        )
                        self.otel_metrics.increment_counter(
                            "prompt_interpreter.operations",
                            amount=1.0,
                            attributes={
                                "type": "agent",
                                "status": "error",
                                "error_type": type(e).__name__,
                            },
                        )
                    raise create_error_with_suggestion(
                        PromptInterpretationError,
                        message=f"Failed to interpret agent prompt: {str(e)}",
                        suggestion="Ensure your prompt clearly describes the agent's purpose, capabilities, and requirements. Check that the gateway is properly configured and the LLM provider is accessible.",
                        prompt=prompt,
                        reason="interpretation_error",
                        original_error=e,
                    )
        else:
            # No OTEL - execute without tracing
            # Check cache first
            if cache:
                prompt_hash = self._hash_prompt(prompt)
                cached = await cache.get(f"agent_interpretation:{prompt_hash}", tenant_id=tenant_id)
                if cached:
                    try:
                        return AgentRequirements(**json.loads(cached))
                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        # Cache invalid, continue with interpretation
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.debug(f"Invalid cached agent interpretation, re-interpreting: {e}")

            # Use LLM to interpret prompt
            formatted_prompt = self._agent_prompt_template.format(prompt=prompt)

            response = await self.gateway.generate_async(
                prompt=formatted_prompt, model="gpt-4", temperature=0.3, max_tokens=2000
            )

            # Parse JSON response
            response_text = response.text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if JSON_CODE_BLOCK_MARKER in response_text:
                response_text = response_text.split(JSON_CODE_BLOCK_MARKER)[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            config = json.loads(response_text)

            # Create AgentRequirements object
            requirements = AgentRequirements(**config)

            # Cache the interpretation
            if cache:
                prompt_hash = self._hash_prompt(prompt)
                await cache.set(
                    f"agent_interpretation:{prompt_hash}",
                    json.dumps(config),
                    tenant_id=tenant_id,
                    ttl=86400,  # 24 hours
                )

            return requirements

    async def interpret_tool_prompt(
        self, prompt: str, cache: Optional[CacheProtocol] = None, tenant_id: Optional[str] = None
    ) -> ToolRequirements:
        """
        Interpret a prompt for tool creation.
        
        Args:
            prompt (str): Prompt text sent to the model.
            cache (Optional[CacheProtocol]): Cache instance used to store and fetch cached results.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            ToolRequirements: Result of the operation.
        
        Raises:
            create_error_with_suggestion: Raised when this function detects an invalid state or when an underlying call fails.
        """
        start_time = time.time()

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("prompt_interpreter.interpret_tool") as trace:
                trace.set_attribute("prompt_interpreter.type", "tool")
                trace.set_attribute("prompt_interpreter.prompt_length", len(prompt))
                trace.set_attribute("prompt_interpreter.has_cache", cache is not None)
                from ..utils.tenant_utils import add_tenant_attributes_to_span
                add_tenant_attributes_to_span(trace, tenant_id, attribute_prefix="prompt_interpreter")

                try:
                    # Check cache first
                    if cache:
                        prompt_hash = self._hash_prompt(prompt)
                        cached = await cache.get(f"tool_interpretation:{prompt_hash}", tenant_id=tenant_id)
                        if cached:
                            try:
                                requirements = ToolRequirements(**json.loads(cached))
                                trace.set_attribute("prompt_interpreter.cache_hit", True)

                                duration = time.time() - start_time
                                if self.otel_metrics:
                                    self.otel_metrics.record_histogram(
                                        "prompt_interpreter.interpret_tool.duration",
                                        duration,
                                        {"cache_hit": "true"},
                                    )
                                    self.otel_metrics.increment_counter(
                                        "prompt_interpreter.operations",
                                        amount=1.0,
                                        attributes={
                                            "type": "tool",
                                            "status": "success",
                                            "cache_hit": "true",
                                        },
                                    )

                                return requirements
                            except (json.JSONDecodeError, KeyError, TypeError) as e:
                                # Cache invalid, continue with interpretation
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.debug(f"Invalid cached tool interpretation, re-interpreting: {e}")

                    # Use LLM to interpret prompt
                    formatted_prompt = self._tool_prompt_template.format(prompt=prompt)

                    response = await self.gateway.generate_async(
                        prompt=formatted_prompt, model="gpt-4", temperature=0.3, max_tokens=2000
                    )

                    # Parse JSON response
                    response_text = response.text.strip()

                    # Extract JSON from response (handle markdown code blocks)
                    if JSON_CODE_BLOCK_MARKER in response_text:
                        response_text = response_text.split(JSON_CODE_BLOCK_MARKER)[1].split("```")[0].strip()
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0].strip()

                    config = json.loads(response_text)

                    # Create ToolRequirements object
                    requirements = ToolRequirements(**config)

                    # Cache the interpretation
                    if cache:
                        prompt_hash = self._hash_prompt(prompt)
                        await cache.set(
                            f"tool_interpretation:{prompt_hash}",
                            json.dumps(config),
                            tenant_id=tenant_id,
                            ttl=86400,  # 24 hours
                        )

                    duration = time.time() - start_time
                    trace.set_attribute("prompt_interpreter.cache_hit", False)
                    trace.set_attribute("prompt_interpreter.tool_name", requirements.name)

                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "prompt_interpreter.interpret_tool.duration",
                            duration,
                            {"cache_hit": "false"},
                        )
                        self.otel_metrics.increment_counter(
                            "prompt_interpreter.operations",
                            amount=1.0,
                            attributes={
                                "type": "tool",
                                "status": "success",
                                "cache_hit": "false",
                            },
                        )

                    return requirements

                except json.JSONDecodeError as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "prompt_interpreter.interpret_tool.duration",
                            duration,
                            {"status": "error"},
                        )
                        self.otel_metrics.increment_counter(
                            "prompt_interpreter.operations",
                            amount=1.0,
                            attributes={
                                "type": "tool",
                                "status": "error",
                                "error_type": "json_parse_error",
                            },
                        )
                    raise create_error_with_suggestion(
                        PromptInterpretationError,
                        message=f"Failed to parse LLM response as JSON: {str(e)}",
                        suggestion="The LLM response was not valid JSON. Try rephrasing your prompt to clearly specify inputs, outputs, and the tool's behavior. The system expects structured JSON output.",
                        prompt=prompt,
                        reason="json_parse_error",
                        original_error=e,
                    )
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "prompt_interpreter.interpret_tool.duration",
                            duration,
                            {"status": "error"},
                        )
                        self.otel_metrics.increment_counter(
                            "prompt_interpreter.operations",
                            amount=1.0,
                            attributes={
                                "type": "tool",
                                "status": "error",
                                "error_type": type(e).__name__,
                            },
                        )
                    raise create_error_with_suggestion(
                        PromptInterpretationError,
                        message=f"Failed to interpret tool prompt: {str(e)}",
                        suggestion="Ensure your prompt clearly describes the tool's inputs, outputs, and behavior. Include parameter types and return types. Check that the gateway is properly configured.",
                        prompt=prompt,
                        reason="interpretation_error",
                        original_error=e,
                    )
        else:
            # No OTEL - execute without tracing
            # Check cache first
            if cache:
                prompt_hash = self._hash_prompt(prompt)
                cached = await cache.get(f"tool_interpretation:{prompt_hash}", tenant_id=tenant_id)
                if cached:
                    try:
                        return ToolRequirements(**json.loads(cached))
                    except (json.JSONDecodeError, KeyError, TypeError) as e:
                        # Cache invalid, continue with interpretation
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.debug(f"Invalid cached tool interpretation, re-interpreting: {e}")

            # Use LLM to interpret prompt
            formatted_prompt = self._tool_prompt_template.format(prompt=prompt)

            response = await self.gateway.generate_async(
                prompt=formatted_prompt, model="gpt-4", temperature=0.3, max_tokens=2000
            )

            # Parse JSON response
            response_text = response.text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if JSON_CODE_BLOCK_MARKER in response_text:
                response_text = response_text.split(JSON_CODE_BLOCK_MARKER)[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            config = json.loads(response_text)

            # Create ToolRequirements object
            requirements = ToolRequirements(**config)

            # Cache the interpretation
            if cache:
                prompt_hash = self._hash_prompt(prompt)
                await cache.set(
                    f"tool_interpretation:{prompt_hash}",
                    json.dumps(config),
                    tenant_id=tenant_id,
                    ttl=86400,  # 24 hours
                )

            return requirements

    async def encode_agent_requirements(
        self, requirements: AgentRequirements, schema_version: str = "1.0"
    ) -> bytes:
        """
        Encode AgentRequirements to bytes using codec serializer.
        
        Args:
            requirements: AgentRequirements instance to encode
            schema_version: Schema version to use
        
        Returns:
            Encoded bytes
        
        Raises:
            PromptInterpretationError: If codec serializer is not configured
        """
        if not self.codec_serializer:
            # Try to import and use default codec serializer
            try:
                from ..codec_integration import encode_agent_requirements
                return await encode_agent_requirements(requirements, codec=None, schema_version=schema_version)
            except ImportError:
                raise create_error_with_suggestion(
                    PromptInterpretationError,
                    message="Codec serializer not configured and codec_integration not available",
                    suggestion="Configure codec_serializer in PromptInterpreter initialization or ensure codec_integration is available",
                    reason="codec_not_configured",
                )
        
        from ..codec_integration import encode_agent_requirements
        return await encode_agent_requirements(requirements, codec=self.codec_serializer, schema_version=schema_version)

    async def decode_agent_requirements(
        self, payload: bytes, target_version: Optional[str] = None
    ) -> AgentRequirements:
        """
        Decode bytes to AgentRequirements using codec serializer.
        
        Args:
            payload: Encoded bytes to decode
            target_version: Target schema version (migrates if different)
        
        Returns:
            AgentRequirements instance
        
        Raises:
            PromptInterpretationError: If codec serializer is not configured
        """
        if not self.codec_serializer:
            # Try to import and use default codec serializer
            try:
                from ..codec_integration import decode_agent_requirements
                decoded_data = await decode_agent_requirements(payload, codec=None, target_version=target_version)
                return AgentRequirements(**decoded_data)
            except ImportError:
                raise create_error_with_suggestion(
                    PromptInterpretationError,
                    message="Codec serializer not configured and codec_integration not available",
                    suggestion="Configure codec_serializer in PromptInterpreter initialization or ensure codec_integration is available",
                    reason="codec_not_configured",
                )
        
        from ..codec_integration import decode_agent_requirements
        decoded_data = await decode_agent_requirements(payload, codec=self.codec_serializer, target_version=target_version)
        return AgentRequirements(**decoded_data)

    async def encode_tool_requirements(
        self, requirements: ToolRequirements, schema_version: str = "1.0"
    ) -> bytes:
        """
        Encode ToolRequirements to bytes using codec serializer.
        
        Args:
            requirements: ToolRequirements instance to encode
            schema_version: Schema version to use
        
        Returns:
            Encoded bytes
        
        Raises:
            PromptInterpretationError: If codec serializer is not configured
        """
        if not self.codec_serializer:
            # Try to import and use default codec serializer
            try:
                from ..codec_integration import encode_tool_requirements
                return await encode_tool_requirements(requirements, codec=None, schema_version=schema_version)
            except ImportError:
                raise create_error_with_suggestion(
                    PromptInterpretationError,
                    message="Codec serializer not configured and codec_integration not available",
                    suggestion="Configure codec_serializer in PromptInterpreter initialization or ensure codec_integration is available",
                    reason="codec_not_configured",
                )
        
        from ..codec_integration import encode_tool_requirements
        return await encode_tool_requirements(requirements, codec=self.codec_serializer, schema_version=schema_version)

    async def decode_tool_requirements(
        self, payload: bytes, target_version: Optional[str] = None
    ) -> ToolRequirements:
        """
        Decode bytes to ToolRequirements using codec serializer.
        
        Args:
            payload: Encoded bytes to decode
            target_version: Target schema version (migrates if different)
        
        Returns:
            ToolRequirements instance
        
        Raises:
            PromptInterpretationError: If codec serializer is not configured
        """
        if not self.codec_serializer:
            # Try to import and use default codec serializer
            try:
                from ..codec_integration import decode_tool_requirements
                decoded_data = await decode_tool_requirements(payload, codec=None, target_version=target_version)
                return ToolRequirements(**decoded_data)
            except ImportError:
                raise create_error_with_suggestion(
                    PromptInterpretationError,
                    message="Codec serializer not configured and codec_integration not available",
                    suggestion="Configure codec_serializer in PromptInterpreter initialization or ensure codec_integration is available",
                    reason="codec_not_configured",
                )
        
        from ..codec_integration import decode_tool_requirements
        decoded_data = await decode_tool_requirements(payload, codec=self.codec_serializer, target_version=target_version)
        return ToolRequirements(**decoded_data)
