"""
Prompt-Based Generator

Enables creation of agents and tools from natural language prompts.
"""


from .access_control import AccessControl, Permission, ResourceType
from .agent_generator import AgentGenerator
from .exceptions import (
    AccessControlError,
    AgentGenerationError,
    CodeValidationError,
    PromptGeneratorError,
    PromptInterpretationError,
    ToolGenerationError,
)
from .feedback_integration import AgentFeedback, FeedbackCollector, ToolFeedback
from .functions import (
    check_permission,
    create_agent_from_prompt,
    create_tool_from_prompt,
    get_agent_feedback_stats,
    get_tool_feedback_stats,
    grant_permission,
    rate_agent,
    rate_tool,
)
from .generator_cache import GeneratorCache
from .prompt_interpreter import AgentRequirements, PromptInterpreter, ToolRequirements
from .tool_generator import ToolGenerator

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
