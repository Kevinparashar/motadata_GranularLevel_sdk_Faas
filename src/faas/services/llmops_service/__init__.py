"""
LLMOps Service

FaaS service for LLM operations monitoring and analytics.
"""

from .service import LLMOpsService, create_llmops_service

__all__ = [
    "LLMOpsService",
    "create_llmops_service",
]
