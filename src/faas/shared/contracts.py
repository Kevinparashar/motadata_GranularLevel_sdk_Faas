"""
Standard contracts for FaaS services.

Defines common request/response schemas and headers used across all services.
"""


from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import Header
from pydantic import BaseModel, ConfigDict, Field


class StandardHeaders(BaseModel):
    """Standard headers for all service requests."""

    tenant_id: str = Field(..., alias="X-Tenant-ID")
    user_id: Optional[str] = Field(None, alias="X-User-ID")
    correlation_id: str = Field(default_factory=lambda: str(uuid4()), alias="X-Correlation-ID")
    request_id: str = Field(default_factory=lambda: str(uuid4()), alias="X-Request-ID")

    model_config = ConfigDict(
        populate_by_name=True,
    )


class ServiceRequest(BaseModel):
    """Base request model for all services."""

    tenant_id: str
    user_id: Optional[str] = None
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tenant_id": "tenant_123",
                "user_id": "user_456",
                "correlation_id": "corr_789",
                "request_id": "req_abc123",
                "metadata": {},
            }
        }
    )


class ServiceResponse(BaseModel):
    """Base response model for all services."""

    success: bool = True
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    correlation_id: str
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {},
                "message": "Operation completed successfully",
                "correlation_id": "corr_789",
                "request_id": "req_abc123",
                "timestamp": "2024-01-01T00:00:00Z",
                "metadata": {},
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""

    success: bool = False
    error: Dict[str, Any]
    correlation_id: str
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input parameters",
                    "details": {},
                },
                "correlation_id": "corr_789",
                "request_id": "req_abc123",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        }
    )


def extract_headers(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
) -> StandardHeaders:
    """
    Extract standard headers from request.

    Args:
        x_tenant_id: Tenant ID from header
        x_user_id: User ID from header
        x_correlation_id: Correlation ID from header
        x_request_id: Request ID from header

    Returns:
        StandardHeaders object
    """
    return StandardHeaders(
        **{
            "X-Tenant-ID": x_tenant_id,
            "X-User-ID": x_user_id,
            "X-Correlation-ID": x_correlation_id or str(uuid4()),
            "X-Request-ID": x_request_id or str(uuid4()),
        }
    )
