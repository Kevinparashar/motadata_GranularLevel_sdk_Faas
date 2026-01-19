"""
Prompt-Based Generator

Enables creation of agents and tools from natural language prompts.
"""

from .functions import (
    create_agent_from_prompt,
    create_tool_from_prompt,
    rate_agent,
    rate_tool,
    grant_permission,
    check_permission,
    get_agent_feedback_stats,
    get_tool_feedback_stats
)
from .agent_generator import AgentGenerator
from .tool_generator import ToolGenerator
from .prompt_interpreter import PromptInterpreter, AgentRequirements, ToolRequirements
from .access_control import AccessControl, Permission, ResourceType
from .feedback_integration import FeedbackCollector, AgentFeedback, ToolFeedback
from .generator_cache import GeneratorCache
from .exceptions import (
    PromptGeneratorError,
    PromptInterpretationError,
    AgentGenerationError,
    ToolGenerationError,
    CodeValidationError,
    AccessControlError
)

__all__ = [
    # High-level functions
    "create_agent_from_prompt",
    "create_tool_from_prompt",
    "rate_agent",
    "rate_tool",
    "grant_permission",
    "check_permission",
    "get_agent_feedback_stats",
    "get_tool_feedback_stats",
    # Core classes
    "AgentGenerator",
    "ToolGenerator",
    "PromptInterpreter",
    "AgentRequirements",
    "ToolRequirements",
    "AccessControl",
    "Permission",
    "ResourceType",
    "FeedbackCollector",
    "AgentFeedback",
    "ToolFeedback",
    "GeneratorCache",
    # Exceptions
    "PromptGeneratorError",
    "PromptInterpretationError",
    "AgentGenerationError",
    "ToolGenerationError",
    "CodeValidationError",
    "AccessControlError",
]

