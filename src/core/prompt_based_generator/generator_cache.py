"""
Generator Cache

Specialized caching for prompt interpretations and generated configurations.
"""


from typing import Optional

from ..cache_mechanism import CacheConfig, CacheMechanism
from ..utils.type_helpers import ConfigDict


class GeneratorCache:
    """
    Specialized cache for prompt-based generator.

    Provides caching for:
    - Prompt interpretations (24 hour TTL)
    - Agent configurations (7 day TTL)
    - Tool schemas (7 day TTL)
    - Generated code (30 day TTL)
    """

    def __init__(self, cache: Optional[CacheMechanism] = None):
        """
        Initialize generator cache.
        
        Args:
            cache (Optional[CacheMechanism]): Cache instance used to store and fetch cached results.
        """
        self.cache = cache or CacheMechanism(
            CacheConfig(namespace="prompt_generator", default_ttl=86400)  # 24 hours default
        )

        # TTL configurations
        self.ttl_config = {
            "prompt_interpretation": 86400,  # 24 hours
            "agent_config": 604800,  # 7 days
            "tool_schema": 604800,  # 7 days
            "tool_code": 2592000,  # 30 days
        }

    def cache_prompt_interpretation(
        self, prompt_hash: str, interpretation: ConfigDict, tenant_id: Optional[str] = None
    ) -> None:
        """
        Cache prompt interpretation.
        
        Args:
            prompt_hash (str): Input parameter for this operation.
            interpretation (ConfigDict): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        import json

        self.cache.set(
            f"interpretation:{prompt_hash}",
            json.dumps(interpretation),
            tenant_id=tenant_id,
            ttl=self.ttl_config["prompt_interpretation"],
        )

    def get_cached_interpretation(
        self, prompt_hash: str, tenant_id: Optional[str] = None
    ) -> Optional[ConfigDict]:
        """
        Get cached prompt interpretation.
        
        Args:
            prompt_hash (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Optional[ConfigDict]: Result if available, else None.
        """
        import json

        cached = self.cache.get(f"interpretation:{prompt_hash}", tenant_id=tenant_id)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                return None
        return None

    def cache_agent_config(
        self, agent_id: str, config: ConfigDict, tenant_id: Optional[str] = None
    ) -> None:
        """
        Cache agent configuration.
        
        Args:
            agent_id (str): Input parameter for this operation.
            config (ConfigDict): Configuration object or settings.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        import json

        self.cache.set(
            f"agent_config:{agent_id}",
            json.dumps(config),
            tenant_id=tenant_id,
            ttl=self.ttl_config["agent_config"],
        )

    def get_cached_agent_config(
        self, agent_id: str, tenant_id: Optional[str] = None
    ) -> Optional[ConfigDict]:
        """
        Get cached agent configuration.
        
        Args:
            agent_id (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Optional[ConfigDict]: Result if available, else None.
        """
        import json

        cached = self.cache.get(f"agent_config:{agent_id}", tenant_id=tenant_id)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                return None
        return None

    def cache_tool_schema(
        self, tool_id: str, schema: ConfigDict, tenant_id: Optional[str] = None
    ) -> None:
        """
        Cache tool schema.
        
        Args:
            tool_id (str): Tool identifier.
            schema (ConfigDict): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        import json

        self.cache.set(
            f"tool_schema:{tool_id}",
            json.dumps(schema),
            tenant_id=tenant_id,
            ttl=self.ttl_config["tool_schema"],
        )

    def get_cached_tool_schema(
        self, tool_id: str, tenant_id: Optional[str] = None
    ) -> Optional[ConfigDict]:
        """
        Get cached tool schema.
        
        Args:
            tool_id (str): Tool identifier.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Optional[ConfigDict]: Result if available, else None.
        """
        import json

        cached = self.cache.get(f"tool_schema:{tool_id}", tenant_id=tenant_id)
        if cached:
            try:
                return json.loads(cached)
            except Exception:
                return None
        return None

    def cache_tool_code(self, tool_id: str, code: str, tenant_id: Optional[str] = None) -> None:
        """
        Cache generated tool code.
        
        Args:
            tool_id (str): Tool identifier.
            code (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        self.cache.set(
            f"tool_code:{tool_id}", code, tenant_id=tenant_id, ttl=self.ttl_config["tool_code"]
        )

    def get_cached_tool_code(self, tool_id: str, tenant_id: Optional[str] = None) -> Optional[str]:
        """
        Get cached tool code.
        
        Args:
            tool_id (str): Tool identifier.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Optional[str]: Returned text value.
        """
        cached = self.cache.get(f"tool_code:{tool_id}", tenant_id=tenant_id)
        return cached if isinstance(cached, str) else None

    def invalidate_pattern(self, pattern: str, tenant_id: Optional[str] = None) -> None:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        self.cache.invalidate_pattern(pattern, tenant_id=tenant_id)

    def clear_all(self, tenant_id: Optional[str] = None) -> None:
        """
        Clear all cached entries for tenant.
        
        Args:
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        self.cache.invalidate_pattern("", tenant_id=tenant_id)
