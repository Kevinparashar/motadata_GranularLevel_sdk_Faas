"""
Prompt-Based Generator Exception Hierarchy

Exceptions specific to prompt-based agent and tool generation.
"""

from typing import Optional

from ..exceptions import SDKError


class PromptGeneratorError(SDKError):
    """Base exception for prompt-based generator errors."""

    pass


class PromptInterpretationError(PromptGeneratorError):
    """
    Raised when prompt interpretation fails.

    Attributes:
        prompt: The prompt that failed to interpret
        reason: Reason for interpretation failure
    """

    def __init__(
        self,
        message: str,
        prompt: Optional[str] = None,
        reason: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.prompt = prompt
        self.reason = reason


class AgentGenerationError(PromptGeneratorError):
    """
    Raised when agent generation from prompt fails.

    Attributes:
        prompt: The prompt used for generation
        agent_id: ID of the agent being generated
        stage: Stage where generation failed
    """

    def __init__(
        self,
        message: str,
        prompt: Optional[str] = None,
        agent_id: Optional[str] = None,
        stage: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.prompt = prompt
        self.agent_id = agent_id
        self.stage = stage


class ToolGenerationError(PromptGeneratorError):
    """
    Raised when tool generation from prompt fails.

    Attributes:
        prompt: The prompt used for generation
        tool_id: ID of the tool being generated
        stage: Stage where generation failed
    """

    def __init__(
        self,
        message: str,
        prompt: Optional[str] = None,
        tool_id: Optional[str] = None,
        stage: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.prompt = prompt
        self.tool_id = tool_id
        self.stage = stage


class CodeValidationError(PromptGeneratorError):
    """
    Raised when generated code fails validation.

    Attributes:
        code: The code that failed validation
        validation_errors: List of validation errors
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        validation_errors: Optional[list] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.code = code
        self.validation_errors = validation_errors or []


class AccessControlError(PromptGeneratorError):
    """
    Raised when access control check fails.

    Attributes:
        tenant_id: Tenant ID
        user_id: User ID
        resource_type: Type of resource (agent/tool)
        resource_id: Resource ID
        permission: Required permission
    """

    def __init__(
        self,
        message: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        permission: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message, original_error)
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.permission = permission
