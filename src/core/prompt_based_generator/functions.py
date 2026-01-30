"""
Prompt-Based Generator - High-Level Functions

Factory functions and convenience functions for prompt-based agent and tool creation.
"""

from typing import Optional

from ..agno_agent_framework.agent import Agent
from ..agno_agent_framework.tools import Tool
from ..utils.error_handler import create_error_with_suggestion
from ..utils.type_helpers import ConfigDict, GatewayProtocol, ResultDict
from .access_control import AccessControl, Permission, ResourceType
from .agent_generator import AgentGenerator
from .exceptions import AgentGenerationError, CodeValidationError, ToolGenerationError
from .feedback_integration import FeedbackCollector
from .generator_cache import GeneratorCache
from .tool_generator import ToolGenerator

# Global instances (can be overridden)
_default_access_control = AccessControl()
_default_feedback_collector = FeedbackCollector()


async def create_agent_from_prompt(
    prompt: str,
    gateway: GatewayProtocol,
    agent_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    cache: Optional[GeneratorCache] = None,
    **kwargs: ConfigDict,
) -> Agent:
    """
    Create an agent from a natural language prompt.

    Args:
        prompt: Natural language description of desired agent
        gateway: LiteLLM Gateway instance
        agent_id: Optional agent ID (generated if not provided)
        tenant_id: Optional tenant ID
        user_id: Optional user ID
        cache: Optional GeneratorCache instance
        **kwargs: Additional agent configuration

    Returns:
        Configured Agent instance

    Raises:
        AgentGenerationError: If agent generation fails
        PromptInterpretationError: If prompt interpretation fails

    Example:
        >>> gateway = LiteLLMGateway()
        >>> agent = await create_agent_from_prompt(
        ...     prompt="Create a customer support agent that categorizes tickets",
        ...     gateway=gateway,
        ...     tenant_id="tenant_123"
        ... )
    """
    if not prompt or not prompt.strip():
        raise create_error_with_suggestion(
            AgentGenerationError,
            message="Prompt cannot be empty",
            suggestion="Provide a detailed description of the agent you want to create. Example: 'Create a customer support agent that categorizes tickets and suggests solutions'",
            prompt=prompt,
            agent_id=agent_id,
            stage="validation",
        )

    try:
        generator = AgentGenerator(gateway=gateway, cache=cache or GeneratorCache())

        agent = await generator.generate_agent_from_prompt(
            prompt=prompt, agent_id=agent_id, tenant_id=tenant_id, **kwargs
        )

        # Grant default permissions to creator
        if user_id and tenant_id:
            _default_access_control.grant_permission(
                tenant_id=tenant_id,
                user_id=user_id,
                resource_type=ResourceType.AGENT,
                resource_id=agent.agent_id,
                permission=Permission.ADMIN,
            )

        return agent
    except AgentGenerationError:
        # Re-raise as-is
        raise
    except Exception as e:
        raise create_error_with_suggestion(
            AgentGenerationError,
            message=f"Failed to create agent from prompt: {str(e)}",
            suggestion="Check that your prompt is clear and specific. Include details about capabilities, behavior, and requirements. Ensure the gateway is properly configured with a valid API key.",
            prompt=prompt,
            agent_id=agent_id,
            stage="generation",
            original_error=e,
        )


async def create_tool_from_prompt(
    prompt: str,
    gateway: GatewayProtocol,
    tool_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    cache: Optional[GeneratorCache] = None,
    **kwargs: ConfigDict,
) -> Tool:
    """
    Create a tool from a natural language prompt.

    Args:
        prompt: Natural language description of desired tool
        gateway: LiteLLM Gateway instance
        tool_id: Optional tool ID (generated if not provided)
        tenant_id: Optional tenant ID
        user_id: Optional user ID
        cache: Optional GeneratorCache instance
        **kwargs: Additional tool configuration

    Returns:
        Configured Tool instance

    Raises:
        ToolGenerationError: If tool generation fails
        CodeValidationError: If generated code is invalid
        PromptInterpretationError: If prompt interpretation fails

    Example:
        >>> gateway = LiteLLMGateway()
        >>> tool = await create_tool_from_prompt(
        ...     prompt="Create a tool that calculates ticket priority",
        ...     gateway=gateway,
        ...     tenant_id="tenant_123"
        ... )
    """
    if not prompt or not prompt.strip():
        raise create_error_with_suggestion(
            ToolGenerationError,
            message="Prompt cannot be empty",
            suggestion="Provide a detailed description of the tool you want to create. Include inputs, outputs, and behavior. Example: 'Create a tool that calculates priority. Inputs: urgency (1-5), impact (1-5). Output: priority score (1-5)'",
            prompt=prompt,
            tool_id=tool_id,
            stage="validation",
        )

    try:
        generator = ToolGenerator(gateway=gateway, cache=cache or GeneratorCache())

        tool = await generator.generate_tool_from_prompt(
            prompt=prompt, tool_id=tool_id, tenant_id=tenant_id, **kwargs
        )

        # Grant default permissions to creator
        if user_id and tenant_id:
            _default_access_control.grant_permission(
                tenant_id=tenant_id,
                user_id=user_id,
                resource_type=ResourceType.TOOL,
                resource_id=tool.tool_id,
                permission=Permission.ADMIN,
            )

        return tool
    except (ToolGenerationError, CodeValidationError):
        # Re-raise as-is
        raise
    except Exception as e:
        raise create_error_with_suggestion(
            ToolGenerationError,
            message=f"Failed to create tool from prompt: {str(e)}",
            suggestion="Ensure your prompt clearly specifies inputs, outputs, and the tool's behavior. Check that the gateway is properly configured. Review generated code for syntax errors.",
            prompt=prompt,
            tool_id=tool_id,
            stage="generation",
            original_error=e,
        )


def rate_agent(
    agent_id: str,
    rating: int,
    user_id: str,
    tenant_id: str,
    feedback_text: Optional[str] = None,
    effectiveness_score: Optional[float] = None,
    feedback_collector: Optional[FeedbackCollector] = None,
    **kwargs: ConfigDict,
) -> str:
    """
    Rate an agent and provide feedback.

    Args:
        agent_id: Agent ID
        rating: Rating (1-5)
        user_id: User ID
        tenant_id: Tenant ID
        feedback_text: Optional feedback text
        effectiveness_score: Optional effectiveness score (0.0-1.0)
        feedback_collector: Optional FeedbackCollector instance
        **kwargs: Additional metadata

    Returns:
        Feedback ID

    Example:
        >>> rate_agent(
        ...     agent_id="agent_123",
        ...     rating=5,
        ...     user_id="user_456",
        ...     tenant_id="tenant_123",
        ...     feedback_text="Very helpful!"
        ... )
    """
    collector = feedback_collector or _default_feedback_collector

    return collector.collect_agent_feedback(
        agent_id=agent_id,
        rating=rating,
        user_id=user_id,
        tenant_id=tenant_id,
        feedback_text=feedback_text,
        effectiveness_score=effectiveness_score,
        metadata=kwargs,
    )


def rate_tool(
    tool_id: str,
    rating: int,
    user_id: str,
    tenant_id: str,
    feedback_text: Optional[str] = None,
    performance_score: Optional[float] = None,
    feedback_collector: Optional[FeedbackCollector] = None,
    **kwargs: ConfigDict,
) -> str:
    """
    Rate a tool and provide feedback.

    Args:
        tool_id: Tool ID
        rating: Rating (1-5)
        user_id: User ID
        tenant_id: Tenant ID
        feedback_text: Optional feedback text
        performance_score: Optional performance score (0.0-1.0)
        feedback_collector: Optional FeedbackCollector instance
        **kwargs: Additional metadata

    Returns:
        Feedback ID

    Example:
        >>> rate_tool(
        ...     tool_id="tool_123",
        ...     rating=4,
        ...     user_id="user_456",
        ...     tenant_id="tenant_123",
        ...     feedback_text="Works well!"
        ... )
    """
    collector = feedback_collector or _default_feedback_collector

    return collector.collect_tool_feedback(
        tool_id=tool_id,
        rating=rating,
        user_id=user_id,
        tenant_id=tenant_id,
        feedback_text=feedback_text,
        performance_score=performance_score,
        metadata=kwargs,
    )


def grant_permission(
    tenant_id: str,
    user_id: str,
    resource_type: str,
    resource_id: str,
    permission: str,
    access_control: Optional[AccessControl] = None,
) -> None:
    """
    Grant permission to a user for a resource.

    Args:
        tenant_id: Tenant ID
        user_id: User ID
        resource_type: Type of resource ("agent" or "tool")
        resource_id: Resource ID
        permission: Permission to grant ("read", "execute", "create", "delete", "admin")
        access_control: Optional AccessControl instance

    Example:
        >>> grant_permission(
        ...     tenant_id="tenant_123",
        ...     user_id="user_456",
        ...     resource_type="agent",
        ...     resource_id="agent_789",
        ...     permission="execute"
        ... )
    """
    ac = access_control or _default_access_control

    ac.grant_permission(
        tenant_id=tenant_id,
        user_id=user_id,
        resource_type=ResourceType(resource_type),
        resource_id=resource_id,
        permission=Permission(permission),
    )


def check_permission(
    tenant_id: str,
    user_id: str,
    resource_type: str,
    resource_id: str,
    permission: str,
    access_control: Optional[AccessControl] = None,
) -> bool:
    """
    Check if user has permission for a resource.

    Args:
        tenant_id: Tenant ID
        user_id: User ID
        resource_type: Type of resource ("agent" or "tool")
        resource_id: Resource ID
        permission: Permission to check
        access_control: Optional AccessControl instance

    Returns:
        True if user has permission, False otherwise

    Example:
        >>> has_access = check_permission(
        ...     tenant_id="tenant_123",
        ...     user_id="user_456",
        ...     resource_type="agent",
        ...     resource_id="agent_789",
        ...     permission="execute"
        ... )
    """
    ac = access_control or _default_access_control

    return ac.check_permission(
        tenant_id=tenant_id,
        user_id=user_id,
        resource_type=ResourceType(resource_type),
        resource_id=resource_id,
        permission=Permission(permission),
    )


def get_agent_feedback_stats(
    agent_id: str,
    tenant_id: Optional[str] = None,
    feedback_collector: Optional[FeedbackCollector] = None,
) -> ResultDict:
    """
    Get feedback statistics for an agent.

    Args:
        agent_id: Agent ID
        tenant_id: Optional tenant ID filter
        feedback_collector: Optional FeedbackCollector instance

    Returns:
        Dictionary with feedback statistics
    """
    collector = feedback_collector or _default_feedback_collector

    return collector.get_agent_feedback_stats(agent_id, tenant_id=tenant_id)


def get_tool_feedback_stats(
    tool_id: str,
    tenant_id: Optional[str] = None,
    feedback_collector: Optional[FeedbackCollector] = None,
) -> ResultDict:
    """
    Get feedback statistics for a tool.

    Args:
        tool_id: Tool ID
        tenant_id: Optional tenant ID filter
        feedback_collector: Optional FeedbackCollector instance

    Returns:
        Dictionary with feedback statistics
    """
    collector = feedback_collector or _default_feedback_collector

    return collector.get_tool_feedback_stats(tool_id, tenant_id=tenant_id)
