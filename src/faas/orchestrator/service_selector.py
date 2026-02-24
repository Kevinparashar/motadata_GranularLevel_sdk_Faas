"""
Service Selector for mapping intents to FaaS services.

Maps query intents to appropriate service endpoints and routing strategies.
"""

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

from .query_router import QueryIntent

if TYPE_CHECKING:
    from ...faas.shared.dal.orchestrator_context_dal import OrchestratorContextDAL

logger = logging.getLogger(__name__)


class ServiceSelector:
    """
    Selects appropriate FaaS service based on query intent.

    Maps intents to service endpoints and provides routing configuration.
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        orchestrator_context_dal: Optional["OrchestratorContextDAL"] = None,
    ):
        """
        Initialize service selector.

        Args:
            config: Optional service configuration
            orchestrator_context_dal: Optional OrchestratorContextDAL for persistence
        """
        self.config = config
        self.orchestrator_context_dal = orchestrator_context_dal

        # Intent to service mapping
        self._intent_service_map: Dict[str, Dict[str, Any]] = {
            QueryIntent.AGENT_CHAT.value: {
                "service": "agent",
                "endpoint": "/api/v1/agents/{agent_id}/chat",
                "method": "POST",
                "requires_agent_id": True,
                "fallback_service": "gateway",
            },
            QueryIntent.AGENT_TASK.value: {
                "service": "agent",
                "endpoint": "/api/v1/agents/{agent_id}/execute",
                "method": "POST",
                "requires_agent_id": True,
                "fallback_service": "gateway",
            },
            QueryIntent.RAG_QUERY.value: {
                "service": "rag",
                "endpoint": "/api/v1/rag/query",
                "method": "POST",
                "requires_agent_id": False,
                "fallback_service": "gateway",
            },
            QueryIntent.DIRECT_LLM.value: {
                "service": "gateway",
                "endpoint": "/api/v1/gateway/generate",
                "method": "POST",
                "requires_agent_id": False,
                "fallback_service": None,
            },
            QueryIntent.DOCUMENT_INGESTION.value: {
                "service": "rag",
                "endpoint": "/api/v1/rag/documents",
                "method": "POST",
                "requires_agent_id": False,
                "fallback_service": "data_ingestion",
            },
            QueryIntent.PROMPT_GENERATION.value: {
                "service": "prompt_generator",
                "endpoint": "/api/v1/prompt/agents",
                "method": "POST",
                "requires_agent_id": False,
                "fallback_service": "gateway",
            },
            QueryIntent.ML_PREDICTION.value: {
                "service": "ml",
                "endpoint": "/api/v1/ml/models/{model_id}/predict",
                "method": "POST",
                "requires_agent_id": False,
                "fallback_service": "gateway",
            },
            QueryIntent.UNKNOWN.value: {
                "service": "gateway",
                "endpoint": "/api/v1/gateway/generate",
                "method": "POST",
                "requires_agent_id": False,
                "fallback_service": None,
            },
        }

    def select_service(
        self,
        intent: str,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Select service and endpoint based on intent.

        Args:
            intent: Query intent (from QueryRouter)
            query: User query text
            context: Optional context (agent_id, model_id, etc.)
            tenant_id: Optional tenant ID
            user_id: Optional user identifier
            correlation_id: Optional correlation ID
            request_id: Optional request ID

        Returns:
            Service routing configuration
        """
        # Get base routing config
        routing_config = self._intent_service_map.get(intent, self._intent_service_map[QueryIntent.UNKNOWN.value])

        # Build routing configuration
        service_name = routing_config["service"]
        endpoint_template = routing_config["endpoint"]
        method = routing_config["method"]
        requires_agent_id = routing_config.get("requires_agent_id", False)
        fallback_service = routing_config.get("fallback_service")

        # Resolve endpoint with context
        endpoint = endpoint_template
        fallback_used = False
        routing_reason = None
        if requires_agent_id:
            agent_id = self._extract_agent_id(context, query)
            if agent_id:
                endpoint = endpoint_template.replace("{agent_id}", agent_id)
                routing_reason = f"Agent ID {agent_id} found in context"
            elif fallback_service:
                # Fallback to gateway if agent_id not available
                logger.warning(f"Agent ID required but not found, falling back to {fallback_service}")
                result = self._get_fallback_config(fallback_service, query)
                fallback_used = True
                # Save routing decision (fire-and-forget)
                self._save_routing_decision_async(
                    intent, query, result["service"], result["endpoint"],
                    f"Fallback to {fallback_service} (agent_id not found)",
                    tenant_id, user_id, correlation_id, request_id,
                    fallback_used, fallback_service, result,
                )
                return result
            else:
                # Cannot route without agent_id
                logger.error(f"Cannot route {intent} without agent_id")
                result = self._get_fallback_config("gateway", query)
                fallback_used = True
                # Save routing decision (fire-and-forget)
                self._save_routing_decision_async(
                    intent, query, result["service"], result["endpoint"],
                    "Fallback to gateway (agent_id required but not found)",
                    tenant_id, user_id, correlation_id, request_id,
                    fallback_used, "gateway", result,
                )
                return result

        # Handle model_id for ML predictions
        if "{model_id}" in endpoint:
            model_id = self._extract_model_id(context, query)
            if model_id:
                endpoint = endpoint.replace("{model_id}", model_id)
                routing_reason = f"Model ID {model_id} found in context"
            elif fallback_service:
                result = self._get_fallback_config(fallback_service, query)
                fallback_used = True
                # Save routing decision (fire-and-forget)
                self._save_routing_decision_async(
                    intent, query, result["service"], result["endpoint"],
                    f"Fallback to {fallback_service} (model_id not found)",
                    tenant_id, user_id, correlation_id, request_id,
                    fallback_used, fallback_service, result,
                )
                return result
            else:
                result = self._get_fallback_config("gateway", query)
                fallback_used = True
                # Save routing decision (fire-and-forget)
                self._save_routing_decision_async(
                    intent, query, result["service"], result["endpoint"],
                    "Fallback to gateway (model_id required but not found)",
                    tenant_id, user_id, correlation_id, request_id,
                    fallback_used, "gateway", result,
                )
                return result

        # Build request payload based on intent
        payload = self._build_payload(intent, query, context)

        result = {
            "service": service_name,
            "endpoint": endpoint,
            "method": method,
            "payload": payload,
            "intent": intent,
            "fallback_service": fallback_service,
        }

        # Save routing decision (fire-and-forget)
        self._save_routing_decision_async(
            intent, query, service_name, endpoint, routing_reason or "Standard routing",
            tenant_id, user_id, correlation_id, request_id,
            fallback_used, fallback_service, result,
        )

        return result

    def _save_routing_decision_async(
        self,
        intent: str,
        query: str,
        service_name: str,
        endpoint: str,
        routing_reason: Optional[str],
        tenant_id: Optional[str],
        user_id: Optional[str],
        correlation_id: Optional[str],
        request_id: Optional[str],
        fallback_used: bool,
        fallback_service: Optional[str],
        routing_config: Dict[str, Any],
    ) -> None:
        """Helper method to save routing decision asynchronously (fire-and-forget)."""
        if not self.orchestrator_context_dal:
            return
        
        try:
            import asyncio
            try:
                asyncio.get_running_loop()
                # We're in an async context, create a task
                asyncio.create_task(
                    self.orchestrator_context_dal.save_routing_decision(
                        intent=intent,
                        query=query,
                        service_name=service_name,
                        endpoint=endpoint,
                        routing_reason=routing_reason,
                        tenant_id=tenant_id,
                        user_id=user_id,
                        correlation_id=correlation_id,
                        request_id=request_id,
                        fallback_used=fallback_used,
                        fallback_service=fallback_service,
                        routing_config=routing_config,
                    )
                )
            except RuntimeError:
                # No event loop running, skip
                pass
        except Exception as e:
            logger.debug(f"Failed to save routing decision to DAL: {e}")

    def _extract_agent_id(self, context: Optional[Dict[str, Any]], query: str) -> Optional[str]:
        """
        Extract agent ID from context or query.

        Args:
            context: Optional context dictionary
            query: User query text

        Returns:
            Agent ID if found, None otherwise
        """
        if context:
            agent_id = context.get("agent_id") or context.get("agentId")
            if agent_id:
                return str(agent_id)

        # Try to extract from query (simple pattern matching)
        query_lower = query.lower()
        if "agent" in query_lower:
            # Look for patterns like "agent_123" or "agent-123"
            import re

            patterns = [
                r"agent[_\s-]?([a-zA-Z0-9_-]+)",
                r"agent\s+([a-zA-Z0-9_-]+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    return match.group(1)

        return None

    def _extract_model_id(self, context: Optional[Dict[str, Any]], query: str) -> Optional[str]:
        """
        Extract model ID from context or query.

        Args:
            context: Optional context dictionary
            query: User query text

        Returns:
            Model ID if found, None otherwise
        """
        if context:
            model_id = context.get("model_id") or context.get("modelId")
            if model_id:
                return str(model_id)

        return None

    def _build_payload(self, intent: str, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build request payload based on intent.

        Args:
            intent: Query intent
            query: User query text
            context: Optional context

        Returns:
            Request payload dictionary
        """
        payload: Dict[str, Any] = {}

        if intent == QueryIntent.AGENT_CHAT.value:
            payload = {
                "message": query,
                "session_id": context.get("session_id") if context else None,
                "stream": context.get("stream", False) if context else False,
            }

        elif intent == QueryIntent.AGENT_TASK.value:
            payload = {
                "task_type": context.get("task_type", "general") if context else "general",
                "parameters": context.get("parameters", {"prompt": query}) if context else {"prompt": query},
                "priority": context.get("priority", 0) if context else 0,
            }

        elif intent == QueryIntent.RAG_QUERY.value:
            payload = {
                "query": query,
                "top_k": context.get("top_k", 5) if context else 5,
                "threshold": context.get("threshold", 0.7) if context else 0.7,
                "metadata_filters": context.get("metadata_filters", {}) if context else {},
            }

        elif intent == QueryIntent.DIRECT_LLM.value:
            payload = {
                "prompt": query,
                "model": context.get("model", "gpt-4") if context else "gpt-4",
                "max_tokens": context.get("max_tokens", 1000) if context else 1000,
                "temperature": context.get("temperature", 0.7) if context else 0.7,
                "stream": context.get("stream", False) if context else False,
            }

        elif intent == QueryIntent.DOCUMENT_INGESTION.value:
            payload = {
                "title": context.get("title", "Untitled Document") if context else "Untitled Document",
                "content": query if query else "",
                "source": context.get("source") if context else None,
                "metadata": context.get("metadata", {}) if context else {},
            }

        elif intent == QueryIntent.PROMPT_GENERATION.value:
            payload = {
                "prompt": query,
                "agent_id": context.get("agent_id") if context else None,
                "llm_model": context.get("llm_model", "gpt-4") if context else "gpt-4",
                "cache_enabled": context.get("cache_enabled", True) if context else True,
            }

        elif intent == QueryIntent.ML_PREDICTION.value:
            payload = {
                "input_data": context.get("input_data", {"query": query}) if context else {"query": query},
            }

        else:
            # Unknown intent - default to direct LLM
            payload = {
                "prompt": query,
                "model": "gpt-4",
                "max_tokens": 1000,
            }

        return payload

    def _get_fallback_config(self, service_name: str, query: str) -> Dict[str, Any]:
        """
        Get fallback service configuration.

        Args:
            service_name: Fallback service name
            query: User query text

        Returns:
            Fallback routing configuration
        """
        if service_name == "gateway":
            return {
                "service": "gateway",
                "endpoint": "/api/v1/gateway/generate",
                "method": "POST",
                "payload": {"prompt": query, "model": "gpt-4", "max_tokens": 1000},
                "intent": QueryIntent.DIRECT_LLM.value,
                "fallback_service": None,
            }

        # Default fallback
        return {
            "service": "gateway",
            "endpoint": "/api/v1/gateway/generate",
            "method": "POST",
            "payload": {"prompt": query, "model": "gpt-4", "max_tokens": 1000},
            "intent": QueryIntent.UNKNOWN.value,
            "fallback_service": None,
        }


def create_service_selector(
    config: Optional[Any] = None,
    orchestrator_context_dal: Optional["OrchestratorContextDAL"] = None,
) -> ServiceSelector:
    """
    Create a service selector instance.

    Args:
        config: Optional service configuration
        orchestrator_context_dal: Optional OrchestratorContextDAL for persistence

    Returns:
        ServiceSelector instance
    """
    return ServiceSelector(config=config, orchestrator_context_dal=orchestrator_context_dal)

