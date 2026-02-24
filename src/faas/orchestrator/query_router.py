"""
Query Router for intent analysis and routing.

Analyzes user queries to determine intent and route to appropriate services.
"""

import hashlib
import json
import logging
from enum import Enum
from typing import Any, Dict, Optional, TYPE_CHECKING

from ...core.utils.type_helpers import GatewayProtocol

if TYPE_CHECKING:
    from ...faas.shared.dal.orchestrator_context_dal import OrchestratorContextDAL

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Query intent types for routing decisions."""

    AGENT_CHAT = "agent_chat"  # Chat with an agent
    AGENT_TASK = "agent_task"  # Execute agent task
    RAG_QUERY = "rag_query"  # Query documents/knowledge base
    DIRECT_LLM = "direct_llm"  # Direct LLM generation
    DOCUMENT_INGESTION = "document_ingestion"  # Upload/ingest documents
    PROMPT_GENERATION = "prompt_generation"  # Create agent/tool from prompt
    ML_PREDICTION = "ml_prediction"  # ML model prediction
    UNKNOWN = "unknown"  # Unknown intent (fallback to gateway)


class QueryRouter:
    """
    Router for analyzing query intent and determining routing strategy.

    Uses LLM-based intent classification to route queries to appropriate services.
    """

    def __init__(
        self,
        gateway: GatewayProtocol,
        enable_llm_classification: bool = True,
        cache: Optional[Any] = None,
        orchestrator_context_dal: Optional["OrchestratorContextDAL"] = None,
    ):
        """
        Initialize query router.

        Args:
            gateway: LiteLLM Gateway instance for intent classification
            enable_llm_classification: Whether to use LLM for intent analysis
            cache: Optional cache for intent classification results
            orchestrator_context_dal: Optional OrchestratorContextDAL for persistence
        """
        self.gateway = gateway
        self.enable_llm_classification = enable_llm_classification
        self.cache = cache
        self.orchestrator_context_dal = orchestrator_context_dal

        # Intent classification prompt template
        self._intent_prompt_template = """Analyze the following user query and determine the most appropriate intent.

Query: {query}

Available intents:
- agent_chat: User wants to chat with an AI agent (conversational, questions to an assistant)
- agent_task: User wants to execute a specific task with an agent (action-oriented, "do this", "execute")
- rag_query: User wants to query documents/knowledge base (questions about documents, "search", "find in docs")
- direct_llm: User wants direct LLM generation without context (simple text generation, summarization)
- document_ingestion: User wants to upload/ingest documents (file upload, "add document", "ingest")
- prompt_generation: User wants to create an agent or tool from a prompt ("create agent", "generate tool")
- ml_prediction: User wants ML model prediction (classification, prediction tasks)

Respond with ONLY the intent name (e.g., "agent_chat") and optionally a confidence score (0.0-1.0) in JSON format:
{{"intent": "intent_name", "confidence": 0.95, "reasoning": "brief explanation"}}"""

    def _hash_query(self, query: str) -> str:
        """
        Generate hash for query caching.

        Args:
            query: User query text

        Returns:
            Hash string
        """
        return hashlib.sha256(query.encode()).hexdigest()

    async def analyze_intent(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze query intent using LLM or pattern matching.

        Args:
            query: User query text
            tenant_id: Optional tenant ID for caching
            context: Optional context (conversation history, metadata)
            user_id: Optional user identifier
            conversation_id: Optional conversation identifier
            session_id: Optional session identifier
            correlation_id: Optional correlation ID

        Returns:
            Dictionary with intent, confidence, and reasoning
        """
        if not query or not query.strip():
            return {
                "intent": QueryIntent.UNKNOWN.value,
                "confidence": 0.0,
                "reasoning": "Empty query",
            }

        # Check cache first
        cache_hit = False
        analysis_method = "llm" if self.enable_llm_classification else "pattern"
        if self.cache and tenant_id:
            cache_key = f"intent:{tenant_id}:{self._hash_query(query)}"
            cached = await self.cache.get(cache_key, tenant_id=tenant_id)
            if cached:
                logger.debug(f"Cache hit for intent analysis: {query[:50]}")
                cache_hit = True
                analysis_method = "cached"
                # Save to DAL if available
                if self.orchestrator_context_dal:
                    try:
                        await self.orchestrator_context_dal.save_intent_analysis(
                            query=query,
                            intent=cached.get("intent", QueryIntent.UNKNOWN.value),
                            confidence=cached.get("confidence", 0.0),
                            reasoning=cached.get("reasoning"),
                            tenant_id=tenant_id,
                            user_id=user_id,
                            conversation_id=conversation_id,
                            session_id=session_id,
                            correlation_id=correlation_id,
                            analysis_method=analysis_method,
                            cache_hit=True,
                            context_used=context,
                        )
                    except Exception as e:
                        logger.debug(f"Failed to save intent analysis to DAL: {e}")
                return cached

        # Use LLM classification if enabled
        if self.enable_llm_classification:
            intent_result = await self._classify_with_llm(query, context)
            analysis_method = "llm"
        else:
            # Fallback to pattern matching
            intent_result = self._classify_with_patterns(query)
            analysis_method = "pattern"

        # Cache result
        if self.cache and tenant_id:
            cache_key = f"intent:{tenant_id}:{self._hash_query(query)}"
            await self.cache.set(cache_key, intent_result, tenant_id=tenant_id, ttl=3600)

        # Save to DAL if available
        if self.orchestrator_context_dal:
            try:
                await self.orchestrator_context_dal.save_intent_analysis(
                    query=query,
                    intent=intent_result.get("intent", QueryIntent.UNKNOWN.value),
                    confidence=intent_result.get("confidence", 0.0),
                    reasoning=intent_result.get("reasoning"),
                    tenant_id=tenant_id,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    session_id=session_id,
                    correlation_id=correlation_id,
                    analysis_method=analysis_method,
                    cache_hit=cache_hit,
                    context_used=context,
                )
            except Exception as e:
                logger.debug(f"Failed to save intent analysis to DAL: {e}")

        return intent_result

    async def _classify_with_llm(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify intent using LLM.

        Args:
            query: User query text
            context: Optional context

        Returns:
            Intent classification result
        """
        try:
            prompt = self._intent_prompt_template.format(query=query)
            if context:
                prompt += f"\n\nContext: {json.dumps(context, default=str)}"

            response = await self.gateway.generate_async(
                prompt=prompt,
                model="gpt-4",
                max_tokens=200,
                temperature=0.1,  # Low temperature for consistent classification
            )

            # Parse JSON response
            response_text = response.text.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            try:
                result = json.loads(response_text)
                intent_name = result.get("intent", QueryIntent.UNKNOWN.value)
                confidence = float(result.get("confidence", 0.5))
                reasoning = result.get("reasoning", "")

                # Validate intent
                try:
                    QueryIntent(intent_name)
                except ValueError:
                    logger.warning(f"Invalid intent from LLM: {intent_name}, falling back to pattern matching")
                    return self._classify_with_patterns(query)

                return {
                    "intent": intent_name,
                    "confidence": confidence,
                    "reasoning": reasoning,
                }
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Failed to parse LLM intent response: {e}, falling back to pattern matching")
                return self._classify_with_patterns(query)

        except Exception as e:
            logger.error(f"LLM intent classification failed: {e}, falling back to pattern matching")
            return self._classify_with_patterns(query)

    def _classify_with_patterns(self, query: str) -> Dict[str, Any]:
        """
        Classify intent using pattern matching (fallback).

        Args:
            query: User query text

        Returns:
            Intent classification result
        """
        query_lower = query.lower()

        # Pattern matching rules
        if any(
            keyword in query_lower
            for keyword in ["create agent", "generate agent", "make agent", "build agent"]
        ):
            return {
                "intent": QueryIntent.PROMPT_GENERATION.value,
                "confidence": 0.8,
                "reasoning": "Pattern match: agent creation keywords",
            }

        if any(
            keyword in query_lower
            for keyword in ["create tool", "generate tool", "make tool", "build tool"]
        ):
            return {
                "intent": QueryIntent.PROMPT_GENERATION.value,
                "confidence": 0.8,
                "reasoning": "Pattern match: tool creation keywords",
            }

        if any(
            keyword in query_lower
            for keyword in ["upload", "ingest", "add document", "process file", "import document"]
        ):
            return {
                "intent": QueryIntent.DOCUMENT_INGESTION.value,
                "confidence": 0.8,
                "reasoning": "Pattern match: document ingestion keywords",
            }

        if any(
            keyword in query_lower
            for keyword in [
                "search",
                "find in",
                "query document",
                "knowledge base",
                "in the docs",
                "from documents",
            ]
        ):
            return {
                "intent": QueryIntent.RAG_QUERY.value,
                "confidence": 0.75,
                "reasoning": "Pattern match: document query keywords",
            }

        if any(
            keyword in query_lower
            for keyword in ["execute", "run task", "perform", "do this", "complete task"]
        ):
            return {
                "intent": QueryIntent.AGENT_TASK.value,
                "confidence": 0.7,
                "reasoning": "Pattern match: task execution keywords",
            }

        if any(
            keyword in query_lower
            for keyword in ["chat", "talk", "conversation", "ask", "help", "assistant"]
        ):
            return {
                "intent": QueryIntent.AGENT_CHAT.value,
                "confidence": 0.7,
                "reasoning": "Pattern match: conversational keywords",
            }

        # Default to direct LLM for simple queries
        if len(query.split()) < 10:
            return {
                "intent": QueryIntent.DIRECT_LLM.value,
                "confidence": 0.6,
                "reasoning": "Pattern match: short query, likely direct generation",
            }

        # Unknown intent
        return {
            "intent": QueryIntent.UNKNOWN.value,
            "confidence": 0.5,
            "reasoning": "No pattern match, defaulting to unknown",
        }


def create_query_router(
    gateway: GatewayProtocol,
    enable_llm_classification: bool = True,
    cache: Optional[Any] = None,
    orchestrator_context_dal: Optional["OrchestratorContextDAL"] = None,
) -> QueryRouter:
    """
    Create a query router instance.

    Args:
        gateway: LiteLLM Gateway instance
        enable_llm_classification: Whether to use LLM for intent analysis
        cache: Optional cache for intent classification results
        orchestrator_context_dal: Optional OrchestratorContextDAL for persistence

    Returns:
        QueryRouter instance
    """
    return QueryRouter(
        gateway=gateway,
        enable_llm_classification=enable_llm_classification,
        cache=cache,
        orchestrator_context_dal=orchestrator_context_dal,
    )

