"""
Request/Response models for LLMOps Service.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OperationType(str, Enum):
    """LLM operation types."""

    COMPLETION = "completion"
    EMBEDDING = "embedding"
    CHAT = "chat"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"


class OperationStatus(str, Enum):
    """Operation status."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    CANCELLED = "cancelled"


class LogOperationRequest(BaseModel):
    """Request to log an LLM operation."""

    operation_type: OperationType = Field(..., description="Type of operation")
    model: str = Field(..., description="Model used")
    prompt_tokens: int = Field(default=0, description="Prompt tokens")
    completion_tokens: int = Field(default=0, description="Completion tokens")
    total_tokens: int = Field(default=0, description="Total tokens")
    latency_ms: float = Field(default=0.0, description="Latency in milliseconds")
    cost_usd: float = Field(default=0.0, description="Cost in USD")
    status: OperationStatus = Field(default=OperationStatus.SUCCESS, description="Operation status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    agent_id: Optional[str] = Field(None, description="Agent ID if applicable")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class QueryOperationsRequest(BaseModel):
    """Request to query LLM operations."""

    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    agent_id: Optional[str] = Field(None, description="Filter by agent ID")
    model: Optional[str] = Field(None, description="Filter by model")
    operation_type: Optional[OperationType] = Field(None, description="Filter by operation type")
    status: Optional[OperationStatus] = Field(None, description="Filter by status")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class OperationResponse(BaseModel):
    """LLM operation response model."""

    operation_id: str
    operation_type: str
    model: str
    tenant_id: Optional[str] = None
    agent_id: Optional[str] = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    status: str
    error_message: Optional[str] = None
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class MetricsResponse(BaseModel):
    """Metrics response model."""

    total_operations: int
    total_tokens: int
    total_cost_usd: float
    average_latency_ms: float
    success_rate: float
    operations_by_type: Dict[str, int] = Field(default_factory=dict)
    operations_by_model: Dict[str, int] = Field(default_factory=dict)
    cost_by_model: Dict[str, float] = Field(default_factory=dict)
    tokens_by_model: Dict[str, int] = Field(default_factory=dict)


class CostAnalysisResponse(BaseModel):
    """Cost analysis response model."""

    total_cost_usd: float
    cost_by_model: Dict[str, float] = Field(default_factory=dict)
    cost_by_operation_type: Dict[str, float] = Field(default_factory=dict)
    cost_by_tenant: Dict[str, float] = Field(default_factory=dict)
    cost_trend: List[Dict[str, Any]] = Field(default_factory=list)
    period_start: str
    period_end: str

