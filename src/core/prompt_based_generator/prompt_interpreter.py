"""
Prompt Interpreter

Core prompt interpretation logic for converting natural language prompts
into structured configurations for agents and tools.
"""

import hashlib
import json
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
        """Get value from cache."""
        ...

    async def set(
        self, key: str, value: str, ttl: Optional[int] = None, tenant_id: Optional[str] = None
    ) -> None:
        """Set value in cache."""
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

    def __init__(self, gateway: GatewayProtocol):
        """
        Initialize prompt interpreter.

        Args:
            gateway: LiteLLM Gateway instance for LLM calls
        """
        self.gateway = gateway
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
        """Generate hash for prompt caching."""
        return hashlib.sha256(prompt.encode()).hexdigest()

    async def interpret_agent_prompt(
        self, prompt: str, cache: Optional[CacheProtocol] = None, tenant_id: Optional[str] = None
    ) -> AgentRequirements:
        """
        Interpret a prompt for agent creation.

        Args:
            prompt: Natural language description of desired agent
            cache: Optional cache mechanism for storing interpretations
            tenant_id: Optional tenant ID for cache isolation

        Returns:
            AgentRequirements object with extracted requirements

        Raises:
            PromptInterpretationError: If interpretation fails
        """
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

        try:
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

        except json.JSONDecodeError as e:
            raise create_error_with_suggestion(
                PromptInterpretationError,
                message=f"Failed to parse LLM response as JSON: {str(e)}",
                suggestion="The LLM response was not valid JSON. Try rephrasing your prompt to be more specific about the agent requirements. The system expects structured JSON output.",
                prompt=prompt,
                reason="json_parse_error",
                original_error=e,
            )
        except Exception as e:
            raise create_error_with_suggestion(
                PromptInterpretationError,
                message=f"Failed to interpret agent prompt: {str(e)}",
                suggestion="Ensure your prompt clearly describes the agent's purpose, capabilities, and requirements. Check that the gateway is properly configured and the LLM provider is accessible.",
                prompt=prompt,
                reason="interpretation_error",
                original_error=e,
            )

    async def interpret_tool_prompt(
        self, prompt: str, cache: Optional[CacheProtocol] = None, tenant_id: Optional[str] = None
    ) -> ToolRequirements:
        """
        Interpret a prompt for tool creation.

        Args:
            prompt: Natural language description of desired tool
            cache: Optional cache mechanism for storing interpretations
            tenant_id: Optional tenant ID for cache isolation

        Returns:
            ToolRequirements object with extracted requirements

        Raises:
            PromptInterpretationError: If interpretation fails
        """
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

        try:
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

        except json.JSONDecodeError as e:
            raise create_error_with_suggestion(
                PromptInterpretationError,
                message=f"Failed to parse LLM response as JSON: {str(e)}",
                suggestion="The LLM response was not valid JSON. Try rephrasing your prompt to clearly specify inputs, outputs, and the tool's behavior. The system expects structured JSON output.",
                prompt=prompt,
                reason="json_parse_error",
                original_error=e,
            )
        except Exception as e:
            raise create_error_with_suggestion(
                PromptInterpretationError,
                message=f"Failed to interpret tool prompt: {str(e)}",
                suggestion="Ensure your prompt clearly describes the tool's inputs, outputs, and behavior. Include parameter types and return types. Check that the gateway is properly configured.",
                prompt=prompt,
                reason="interpretation_error",
                original_error=e,
            )
