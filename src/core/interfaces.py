"""
Component Interfaces

Interfaces for swappable components to enable dynamic component swapping.
All components are in src/core/ as peer components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AgentFrameworkInterface(ABC):
    """Interface for agent frameworks (Agno, LangChain, etc.)."""
    
    @abstractmethod
    def create_agent(self, agent_id: str, config: Dict[str, Any]) -> Any:
        """Create an agent instance."""
        pass
    
    @abstractmethod
    async def execute_task(self, agent: Any, task: Dict[str, Any]) -> Any:
        """Execute a task with an agent."""
        pass
    
    @abstractmethod
    def send_message(self, from_agent: str, to_agent: str, message: Any) -> None:
        """Send message between agents."""
        pass


class DatabaseInterface(ABC):
    """Interface for database implementations."""
    
    @abstractmethod
    def connect(self) -> None:
        """Connect to database."""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a database query."""
        pass
    
    @abstractmethod
    def store_embedding(self, document_id: int, embedding: List[float], model: str) -> int:
        """Store an embedding vector."""
        pass
    
    @abstractmethod
    def similarity_search(
        self,
        query_embedding: List[float],
        limit: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Perform similarity search."""
        pass


class CacheInterface(ABC):
    """Interface for cache implementations."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""
        pass


class ComponentFactory:
    """Factory for creating swappable components."""
    
    @staticmethod
    def create_agent_framework(framework_type: str, config: Dict[str, Any]) -> AgentFrameworkInterface:
        """
        Create agent framework instance.
        
        Args:
            framework_type: Framework type ("agno", "langchain", etc.)
            config: Framework configuration
        
        Returns:
            Agent framework instance
        """
        if framework_type == "agno":
            from src.core.agno_agent_framework import AgnoAgentFramework
            return AgnoAgentFramework(config)
        elif framework_type == "langchain":
            from src.core.langchain_agent_framework import LangChainAgentFramework
            return LangChainAgentFramework(config)
        else:
            raise ValueError(f"Unknown agent framework: {framework_type}")
    
    @staticmethod
    def create_database(db_type: str, config: Dict[str, Any]) -> DatabaseInterface:
        """
        Create database instance.
        
        Args:
            db_type: Database type ("postgresql", "mongodb", etc.)
            config: Database configuration
        
        Returns:
            Database instance
        """
        if db_type == "postgresql":
            from src.core.postgresql_database import PostgreSQLDatabase
            return PostgreSQLDatabase(config)
        else:
            raise ValueError(f"Unknown database type: {db_type}")
    
    @staticmethod
    def create_cache(cache_type: str, config: Dict[str, Any]) -> CacheInterface:
        """
        Create cache instance.
        
        Args:
            cache_type: Cache type ("redis", "memory", "database")
            config: Cache configuration
        
        Returns:
            Cache instance
        """
        if cache_type == "redis":
            from src.core.cache_mechanism import RedisCache
            return RedisCache(config)
        elif cache_type == "memory":
            from src.core.cache_mechanism import MemoryCache
            return MemoryCache(config)
        else:
            raise ValueError(f"Unknown cache type: {cache_type}")
    
    @staticmethod
    def create_pool(pool_type: str, config: Dict[str, Any]) -> Any:
        """
        Create pool instance.
        
        Args:
            pool_type: Pool type ("connection", "thread")
            config: Pool configuration
        
        Returns:
            Pool instance
        """
        if pool_type == "connection":
            from pool_implementation import ConnectionPool
            return ConnectionPool(config)
        elif pool_type == "thread":
            from pool_implementation import ThreadPool
            return ThreadPool(config)
        else:
            raise ValueError(f"Unknown pool type: {pool_type}")
    
    @staticmethod
    def create_connectivity_client(client_type: str, config: Dict[str, Any]) -> Any:
        """
        Create connectivity client instance.
        
        Args:
            client_type: Client type ("http", "websocket")
            config: Client configuration
        
        Returns:
            Client instance
        """
        if client_type == "http":
            from connectivity_clients import HTTPClient
            return HTTPClient(config)
        elif client_type == "websocket":
            from connectivity_clients import WebSocketClient
            return WebSocketClient(config)
        else:
            raise ValueError(f"Unknown client type: {client_type}")
        else:
            raise ValueError(f"Unknown cache type: {cache_type}")

