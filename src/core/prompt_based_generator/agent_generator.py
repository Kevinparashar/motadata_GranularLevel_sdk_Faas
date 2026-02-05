"""
Agent Generator

Generates agents from natural language prompts using LLM interpretation.
"""


import uuid
from typing import Optional

from ..agno_agent_framework import Agent, AgentCapability
from ..utils.type_helpers import ConfigDict, GatewayProtocol
from .exceptions import AgentGenerationError
from .generator_cache import GeneratorCache
from .prompt_interpreter import PromptInterpreter


class AgentGenerator:
    """
    Generates agents from natural language prompts.

    Uses prompt interpretation to extract requirements and
    creates fully configured Agent instances.
    """

    def __init__(
        self,
        gateway: GatewayProtocol,
        interpreter: Optional[PromptInterpreter] = None,
        cache: Optional[GeneratorCache] = None,
    ):
        """
        Initialize agent generator.
        
        Args:
            gateway (GatewayProtocol): Gateway client used for LLM calls.
            interpreter (Optional[PromptInterpreter]): Input parameter for this operation.
            cache (Optional[GeneratorCache]): Cache instance used to store and fetch cached results.
        """
        self.gateway = gateway
        self.interpreter = interpreter or PromptInterpreter(gateway)
        self.cache = cache or GeneratorCache()

    async def generate_agent_from_prompt(
        self,
        prompt: str,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs: ConfigDict,
    ) -> Agent:
        """
        Generate an agent from a natural language prompt.
        
        Args:
            prompt (str): Prompt text sent to the model.
            agent_id (Optional[str]): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            **kwargs (ConfigDict): Input parameter for this operation.
        
        Returns:
            Agent: Result of the operation.
        
        Raises:
            AgentGenerationError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        try:
            # Generate agent ID if not provided
            if not agent_id:
                agent_id = f"agent_{uuid.uuid4().hex[:8]}"

            # Interpret prompt
            requirements = await self.interpreter.interpret_agent_prompt(
                prompt=prompt,
                cache=self.cache.cache if hasattr(self.cache, "cache") else None,  # type: ignore[arg-type]
                tenant_id=tenant_id,
            )

            # Create agent configuration
            agent_config = {
                "agent_id": agent_id,
                "name": requirements.name,
                "description": requirements.description,
                "gateway": self.gateway,
                "tenant_id": tenant_id,
                "llm_model": kwargs.get("llm_model"),
                "llm_provider": kwargs.get("llm_provider"),
                **kwargs,
            }

            # Create agent
            agent = Agent(**agent_config)

            # Add capabilities
            for capability_name in requirements.capabilities:
                capability = AgentCapability(
                    name=capability_name,
                    description=f"Capability: {capability_name}",
                    parameters={},
                )
                agent.capabilities.append(capability)

            # Configure memory if specified
            if requirements.memory_config:
                agent.attach_memory(
                    persistence_path=requirements.memory_config.get("persistence_path"),
                    max_episodic=requirements.memory_config.get("max_episodic", 500),
                    max_semantic=requirements.memory_config.get("max_semantic", 2000),
                    max_age_days=requirements.memory_config.get("max_age_days", 30),
                    tenant_id=tenant_id,
                )

            # Set system prompt if provided
            if requirements.system_prompt:
                agent.system_prompt = requirements.system_prompt
                agent.use_prompt_management = True
                agent.max_context_tokens = requirements.max_context_tokens

            # Enable tool calling if specified
            agent.enable_tool_calling = requirements.enable_tool_calling

            # Cache agent configuration
            await self.cache.cache_agent_config(
                agent_id=agent_id,
                config={
                    "name": requirements.name,
                    "description": requirements.description,
                    "capabilities": requirements.capabilities,
                    "system_prompt": requirements.system_prompt,
                    "memory_config": requirements.memory_config,
                    "max_context_tokens": requirements.max_context_tokens,
                },
                tenant_id=tenant_id,
            )

            return agent

        except Exception as e:
            if isinstance(e, AgentGenerationError):
                raise
            raise AgentGenerationError(
                message=f"Failed to generate agent from prompt: {str(e)}",
                prompt=prompt,
                agent_id=agent_id,
                stage="generation",
                original_error=e,
            )

    async def generate_agent_from_cached_config(
        self, agent_id: str, tenant_id: Optional[str] = None
    ) -> Optional[Agent]:
        """
        Generate an agent from cached configuration asynchronously.
        
        Args:
            agent_id (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Optional[Agent]: Result if available, else None.
        """
        config: Optional[ConfigDict] = await self.cache.get_cached_agent_config(agent_id, tenant_id=tenant_id)
        if not config:
            return None

        try:
            agent = Agent(
                agent_id=agent_id,
                name=config.get("name", "Generated Agent"),
                description=config.get("description", ""),
                gateway=self.gateway,
                tenant_id=tenant_id,
            )

            # Restore capabilities
            for cap_name in config.get("capabilities", []):
                agent.capabilities.append(
                    AgentCapability(
                        name=cap_name, description=f"Capability: {cap_name}", parameters={}
                    )
                )

            # Restore system prompt
            if config.get("system_prompt"):
                agent.system_prompt = config["system_prompt"]
                agent.use_prompt_management = True
                agent.max_context_tokens = config.get("max_context_tokens", 4000)

            return agent

        except Exception:
            return None
