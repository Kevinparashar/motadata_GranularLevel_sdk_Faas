"""
Cache Strategy for feature-specific caching strategies.

Provides different caching strategies for different AI features.
"""

import hashlib
import json
import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CacheStrategyType(str, Enum):
    """Cache strategy types."""

    CONVERSATION = "conversation"  # Cache based on conversation context
    QUERY = "query"  # Cache based on exact query match
    SEMANTIC = "semantic"  # Cache based on semantic similarity (future)
    NONE = "none"  # No caching


class CacheStrategy:
    """
    Cache strategy for generating cache keys and determining TTL.

    Provides different strategies for different AI features.
    """

    def __init__(self, strategy_type: CacheStrategyType = CacheStrategyType.QUERY):
        """
        Initialize cache strategy.

        Args:
            strategy_type: Type of cache strategy to use
        """
        self.strategy_type = strategy_type

    def generate_cache_key(
        self,
        feature: str,
        query: str,
        tenant_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate cache key based on strategy.

        Args:
            feature: AI feature name (agent_chat, rag_query, etc.)
            query: User query text
            tenant_id: Optional tenant ID
            context: Optional context (session_id, conversation_id, etc.)

        Returns:
            Cache key string
        """
        if self.strategy_type == CacheStrategyType.NONE:
            return ""

        if self.strategy_type == CacheStrategyType.CONVERSATION:
            return self._generate_conversation_key(feature, query, tenant_id, context)

        if self.strategy_type == CacheStrategyType.QUERY:
            return self._generate_query_key(feature, query, tenant_id, context)

        # Default to query key
        return self._generate_query_key(feature, query, tenant_id, context)

    def _generate_conversation_key(
        self,
        feature: str,
        query: str,
        tenant_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate cache key based on conversation context.

        Args:
            feature: AI feature name
            query: User query text
            tenant_id: Optional tenant ID
            context: Optional context

        Returns:
            Cache key string
        """
        key_parts = ["orchestrator", feature]

        if tenant_id:
            key_parts.append(f"tenant:{tenant_id}")

        # Include conversation/session context
        if context:
            session_id = context.get("session_id") or context.get("conversation_id")
            if session_id:
                key_parts.append(f"session:{session_id}")

        # Include query (normalized)
        normalized_query = query.strip().lower()
        query_hash = hashlib.sha256(normalized_query.encode()).hexdigest()[:16]
        key_parts.append(f"query:{query_hash}")

        # Include relevant context for cache differentiation
        if context:
            relevant_keys = ["agent_id", "model", "top_k", "threshold"]
            context_parts = []
            for key in relevant_keys:
                if key in context:
                    context_parts.append(f"{key}:{context[key]}")
            if context_parts:
                context_str = ":".join(context_parts)
                context_hash = hashlib.sha256(context_str.encode()).hexdigest()[:8]
                key_parts.append(f"ctx:{context_hash}")

        return ":".join(key_parts)

    def _generate_query_key(
        self,
        feature: str,
        query: str,
        tenant_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate cache key based on exact query match.

        Args:
            feature: AI feature name
            query: User query text
            tenant_id: Optional tenant ID
            context: Optional context

        Returns:
            Cache key string
        """
        key_parts = ["orchestrator", feature]

        if tenant_id:
            key_parts.append(f"tenant:{tenant_id}")

        # Normalize query
        normalized_query = query.strip().lower()
        query_hash = hashlib.sha256(normalized_query.encode()).hexdigest()
        key_parts.append(f"query:{query_hash}")

        # Include relevant context
        if context:
            context_data = {}
            relevant_keys = ["agent_id", "model", "top_k", "threshold", "max_tokens"]
            for key in relevant_keys:
                if key in context:
                    context_data[key] = context[key]

            if context_data:
                context_str = json.dumps(context_data, sort_keys=True, default=str)
                context_hash = hashlib.sha256(context_str.encode()).hexdigest()[:16]
                key_parts.append(f"ctx:{context_hash}")

        return ":".join(key_parts)

    def get_ttl(self, feature: str) -> int:
        """
        Get TTL for feature based on strategy.

        Args:
            feature: AI feature name

        Returns:
            TTL in seconds
        """
        # Feature-specific TTLs
        ttl_map = {
            "agent_chat": 300,  # 5 minutes
            "agent_task": 600,  # 10 minutes
            "rag_query": 3600,  # 1 hour
            "direct_llm": 1800,  # 30 minutes
            "document_ingestion": 0,  # No cache (always fresh)
            "prompt_generation": 86400,  # 24 hours
            "ml_prediction": 1800,  # 30 minutes
        }

        return ttl_map.get(feature, 300)  # Default 5 minutes

    def should_cache(self, feature: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Determine if request should be cached.

        Args:
            feature: AI feature name
            context: Optional context

        Returns:
            True if should cache, False otherwise
        """
        # Don't cache document ingestion
        if feature == "document_ingestion":
            return False

        # Don't cache if explicitly disabled
        if context and context.get("cache_enabled") is False:
            return False

        return True


def get_cache_strategy(
    strategy_type: CacheStrategyType = CacheStrategyType.QUERY,
) -> CacheStrategy:
    """
    Get cache strategy instance.

    Args:
        strategy_type: Type of cache strategy

    Returns:
        CacheStrategy instance
    """
    return CacheStrategy(strategy_type=strategy_type)

