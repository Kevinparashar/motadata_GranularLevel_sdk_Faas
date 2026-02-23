"""
Data Access Layer (DAL) for FaaS Services

Provides database abstraction for all entity persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""

from .agent_dal import AgentDAL
from .document_dal import DocumentDAL
from .document_version_dal import DocumentVersionDAL
from .memory_dal import MemoryDAL
from .model_dal import ModelDAL
from .model_version_dal import ModelVersionDAL
from .prompt_history_dal import PromptHistoryDAL
from .prompt_template_dal import PromptTemplateDAL
from .session_dal import SessionDAL
from .tool_dal import ToolDAL
from .tool_execution_dal import ToolExecutionDAL
from .workflow_dal import WorkflowDAL

__all__ = [
    "SessionDAL",
    "MemoryDAL",
    "AgentDAL",
    "DocumentDAL",
    "DocumentVersionDAL",
    "ModelDAL",
    "ModelVersionDAL",
    "PromptTemplateDAL",
    "PromptHistoryDAL",
    "ToolDAL",
    "ToolExecutionDAL",
    "WorkflowDAL",
]

