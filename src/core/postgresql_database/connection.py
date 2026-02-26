"""
Database Connection Management

Handles PostgreSQL database connections with async connection pooling.
"""


# Standard library imports
import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, List, Optional, Tuple

# Third-party imports
try:
    import asyncpg
except ImportError:
    asyncpg = None

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database configuration."""

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="ai_app")
    user: str = Field(default="postgres")
    password: str = Field(default="")
    min_connections: int = Field(default=1)
    max_connections: int = Field(default=10)
    connection_timeout: int = Field(default=30)
    auto_create_extension: bool = Field(default=False, description="Automatically create pgvector extension if missing")

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """
        Create config from environment variables.
        
        Returns:
            'DatabaseConfig': Builder instance (returned for call chaining).
        """
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "ai_app"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "1")),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "10")),
        )


class DatabaseConnection:
    """
    PostgreSQL database connection manager with async connection pooling.
    
    Uses asyncpg for async database operations.
    """

    def __init__(self, config: DatabaseConfig):
        """
        Initialize database connection.
        
        Args:
            config (DatabaseConfig): Configuration object or settings.
        """
        self.config = config
        self.pool: Optional[Any] = None  # asyncpg.Pool when asyncpg is available
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self) -> None:
        """
        Create async connection pool.
        
        Returns:
            None: Result of the operation.
        
        Raises:
            ConnectionError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.connection_timeout,
            )
            
            # Verify pgvector extension after connection
            if not await self.verify_pgvector_extension():
                if self.config.auto_create_extension:
                    await self.create_pgvector_extension()
                else:
                    # Log warning but don't fail connection
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        "pgvector extension not found. Vector operations may fail. "
                        "Set auto_create_extension=True to automatically create it."
                    )
        except asyncpg.PostgresError as e:
            raise ConnectionError(f"Failed to create connection pool: {e}") from e
        except Exception as e:
            raise ConnectionError(f"Unexpected error creating connection pool: {e}") from e

    async def close(self) -> None:
        """
        Close all connections in pool.
        
        Returns:
            None: Result of the operation.
        """
        if self.pool:
            await self.pool.close()
            self.pool = None

    @asynccontextmanager
    async def get_connection(self):
        """
        Get a connection from the pool.
        
        Yields:
            asyncpg.Connection: Database connection
        """
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            yield conn

    def _convert_placeholders(self, query: str, param_count: int) -> str:
        """
        Convert %s placeholders to $1, $2, etc. for asyncpg.
        
        Args:
            query (str): SQL query with %s placeholders.
            param_count (int): Number of parameters.
        
        Returns:
            str: Query with $1, $2, etc. placeholders.
        """
        parts = query.split('%s')
        if len(parts) <= 1:
            # Query already uses $1, $2 format or has no placeholders
            return query
        
        # Rebuild query with numbered placeholders
        query_parts = []
        for i, part in enumerate(parts):
            query_parts.append(part)
            if i < len(parts) - 1:
                query_parts.append(f'${i + 1}')
        return ''.join(query_parts)

    async def execute_query(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
        fetch_one: bool = False,
        fetch_all: bool = True,
    ) -> Any:
        """
        Execute a query asynchronously.
        
        Args:
            query (str): SQL query to execute.
            params (Optional[Tuple[Any, ...]]): Query parameters.
            fetch_one (bool): Fetch only one row.
            fetch_all (bool): Fetch all rows.
        
        Returns:
            Any: Query results (dict, list of dicts, or row count).
        """
        if not self.pool:
            await self.connect()
        
        if not self.pool:
            raise ConnectionError("Failed to establish database connection")

        async with self.pool.acquire() as conn:
            query_converted = self._convert_placeholders(query, len(params)) if params else query
            params_tuple = params or ()

            if fetch_one:
                result = await conn.fetchrow(query_converted, *params_tuple)
                return dict(result) if result else None
            
            if fetch_all:
                results = await conn.fetch(query_converted, *params_tuple)
                return [dict(row) for row in results]
            
            # Execute without fetching
            result = await conn.execute(query_converted, *params_tuple)
            # Extract row count from result status
            return int(result.split()[-1]) if result else 0

    async def execute_transaction(
        self, queries: List[Tuple[str, Optional[Tuple[Any, ...]]]]
    ) -> None:
        """
        Execute multiple queries in a transaction asynchronously.
        
        Args:
            queries (List[Tuple[str, Optional[Tuple[Any, ...]]]]): List of (query, params) tuples.
        
        Returns:
            None: Result of the operation.
        
        Raises:
            asyncpg.PostgresError: Database error during transaction.
        """
        if not self.pool:
            await self.connect()
        
        if not self.pool:
            raise ConnectionError("Failed to establish database connection")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for query, params in queries:
                    if params:
                        query_converted = self._convert_placeholders(query, len(params))
                        await conn.execute(query_converted, *params)
                    else:
                        await conn.execute(query)

    async def check_connection(self) -> bool:
        """
        Check if database connection is working asynchronously.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        try:
            if not self.pool:
                await self.connect()
            
            if not self.pool:
                return False
            
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except (asyncpg.PostgresError, ConnectionError):
            return False
        except Exception:
            return False

    async def verify_pgvector_extension(self) -> bool:
        """
        Verify if pgvector extension is installed in the database.
        
        Returns:
            bool: True if pgvector extension exists, False otherwise.
        """
        try:
            if not self.pool:
                await self.connect()
            
            if not self.pool:
                return False
            
            # OTEL Integration (optional)
            tracer = None
            try:
                from ..otel_integration import create_otel_tracer
                tracer = create_otel_tracer(service_name="database-connection")
            except (ImportError, Exception):
                tracer = None
            
            if tracer:
                with tracer.start_trace("database.verify_pgvector_extension") as trace:
                    trace.set_attribute("database.name", self.config.database)
                    
                    try:
                        async with self.pool.acquire() as conn:
                            result = await conn.fetchval(
                                """
                                SELECT EXISTS(
                                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                                );
                                """
                            )
                            exists = bool(result) if result is not None else False
                            trace.set_attribute("pgvector.exists", exists)
                            return exists
                    except Exception as e:
                        trace.record_exception(e)
                        return False
            else:
                # No OTEL - execute without tracing
                async with self.pool.acquire() as conn:
                    result = await conn.fetchval(
                        """
                        SELECT EXISTS(
                            SELECT 1 FROM pg_extension WHERE extname = 'vector'
                        );
                        """
                    )
                    return bool(result) if result is not None else False
        except (asyncpg.PostgresError, ConnectionError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to verify pgvector extension: {e}")
            return False
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Unexpected error verifying pgvector extension: {e}")
            return False

    async def create_pgvector_extension(self) -> bool:
        """
        Create pgvector extension in the database (requires superuser privileges).
        
        Returns:
            bool: True if extension was created or already exists, False otherwise.
        """
        try:
            if not self.pool:
                await self.connect()
            
            if not self.pool:
                return False
            
            # OTEL Integration (optional)
            tracer = None
            try:
                from ..otel_integration import create_otel_tracer
                tracer = create_otel_tracer(service_name="database-connection")
            except (ImportError, Exception):
                tracer = None
            
            if tracer:
                with tracer.start_trace("database.create_pgvector_extension") as trace:
                    trace.set_attribute("database.name", self.config.database)
                    
                    try:
                        async with self.pool.acquire() as conn:
                            # Use IF NOT EXISTS to avoid errors if extension already exists
                            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                            trace.set_attribute("pgvector.created", True)
                            return True
                    except asyncpg.PostgresError as e:
                        trace.record_exception(e)
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Failed to create pgvector extension: {e}")
                        return False
                    except Exception as e:
                        trace.record_exception(e)
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"Unexpected error creating pgvector extension: {e}")
                        return False
            else:
                # No OTEL - execute without tracing
                async with self.pool.acquire() as conn:
                    # Use IF NOT EXISTS to avoid errors if extension already exists
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    return True
        except asyncpg.PostgresError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create pgvector extension: {e}")
            return False
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error creating pgvector extension: {e}")
            return False

    async def health_check(self) -> dict[str, Any]:
        """
        Perform comprehensive health check including pgvector extension.
        
        Returns:
            dict[str, Any]: Health check results with connection status and extension status.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        health_status = {
            "connection": False,
            "pgvector_extension": False,
            "database": self.config.database,
        }
        
        try:
            # Check basic connection
            health_status["connection"] = await self.check_connection()
            
            # Check pgvector extension if connection is working
            if health_status["connection"]:
                health_status["pgvector_extension"] = await self.verify_pgvector_extension()
            
            return health_status
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["error"] = str(e)
            return health_status

    # Synchronous wrappers for backward compatibility (will be deprecated)
    def execute_query_sync(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None,
        fetch_one: bool = False,
        fetch_all: bool = True,
    ) -> Any:
        """
        Synchronous wrapper for execute_query (DEPRECATED).
        
        Use execute_query() directly with await instead.
        This wrapper is provided for backward compatibility only.
        
        Args:
            query (str): SQL query to execute.
            params (Optional[Tuple[Any, ...]]): Query parameters.
            fetch_one (bool): Fetch only one row.
            fetch_all (bool): Fetch all rows.
        
        Returns:
            Any: Query results.
        """
        loop = self._get_or_create_event_loop()
        return loop.run_until_complete(
            self.execute_query(query, params, fetch_one, fetch_all)
        )

    def _get_or_create_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        Get existing event loop or create new one.
        
        Returns:
            asyncio.AbstractEventLoop: Event loop instance.
        
        Raises:
            RuntimeError: If called from within an async context.
        """
        try:
            # Check if we're already in an async context
            loop = asyncio.get_running_loop()
            # If we're already in an async context, we can't use run_until_complete
            # This is a safety check to prevent nested event loops
            raise RuntimeError(
                "Cannot use sync methods from async context. Use async methods instead."
            )
        except RuntimeError as e:
            # Check if this is our custom error or a "no running loop" error
            if "Cannot use sync methods" in str(e):
                raise  # Re-raise our custom error
            # Not in async context, safe to create/get event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop
