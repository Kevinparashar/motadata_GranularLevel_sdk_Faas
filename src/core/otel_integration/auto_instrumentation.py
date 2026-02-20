"""
OpenTelemetry Auto-Instrumentation Setup

Configures automatic instrumentation for FastAPI, HTTP clients, databases,
and other frameworks to capture telemetry without manual code changes.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Track which instrumentations have been enabled
_enabled_instrumentations: List[str] = []


def setup_fastapi_instrumentation(app: Optional[Any] = None) -> bool:
    """
    Setup FastAPI auto-instrumentation.
    
    Automatically traces HTTP requests, responses, and middleware in FastAPI applications.
    
    Args:
        app: FastAPI application instance (optional, can be instrumented later)
        
    Returns:
        True if instrumentation was successful, False otherwise
        
    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> setup_fastapi_instrumentation(app)
        True
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
        
        if app is not None:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI auto-instrumentation enabled")
            _enabled_instrumentations.append("fastapi")
            return True
        else:
            # Instrument all FastAPI apps
            FastAPIInstrumentor().instrument()
            logger.info("FastAPI auto-instrumentation enabled (global)")
            _enabled_instrumentations.append("fastapi")
            return True
    except ImportError:
        logger.debug("opentelemetry-instrumentation-fastapi not available, skipping FastAPI instrumentation")
        return False
    except Exception as e:
        logger.warning(f"Failed to setup FastAPI instrumentation: {e}")
        return False


def setup_httpx_instrumentation() -> bool:
    """
    Setup HTTPX client auto-instrumentation.
    
    Automatically traces HTTP requests made with httpx.AsyncClient and httpx.Client.
    
    Returns:
        True if instrumentation was successful, False otherwise
        
    Example:
        >>> setup_httpx_instrumentation()
        True
        >>> async with httpx.AsyncClient() as client:
        ...     response = await client.get("https://api.example.com")
        # Request is automatically traced
    """
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor  # type: ignore
        
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX auto-instrumentation enabled")
        _enabled_instrumentations.append("httpx")
        return True
    except ImportError:
        logger.debug("opentelemetry-instrumentation-httpx not available, skipping HTTPX instrumentation")
        return False
    except Exception as e:
        logger.warning(f"Failed to setup HTTPX instrumentation: {e}")
        return False


def setup_requests_instrumentation() -> bool:
    """
    Setup Requests library auto-instrumentation.
    
    Automatically traces HTTP requests made with the requests library.
    
    Returns:
        True if instrumentation was successful, False otherwise
        
    Example:
        >>> setup_requests_instrumentation()
        True
        >>> response = requests.get("https://api.example.com")
        # Request is automatically traced
    """
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor  # type: ignore
        
        RequestsInstrumentor().instrument()
        logger.info("Requests auto-instrumentation enabled")
        _enabled_instrumentations.append("requests")
        return True
    except ImportError:
        logger.debug("opentelemetry-instrumentation-requests not available, skipping Requests instrumentation")
        return False
    except Exception as e:
        logger.warning(f"Failed to setup Requests instrumentation: {e}")
        return False


def setup_asyncpg_instrumentation() -> bool:
    """
    Setup asyncpg (PostgreSQL) auto-instrumentation.
    
    Automatically traces database queries made with asyncpg.
    This also covers pgvector operations since they use asyncpg.
    
    Returns:
        True if instrumentation was successful, False otherwise
        
    Example:
        >>> setup_asyncpg_instrumentation()
        True
        >>> conn = await asyncpg.connect("postgresql://...")
        >>> await conn.fetch("SELECT * FROM users")
        # Query is automatically traced
    """
    try:
        from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor  # type: ignore
        
        AsyncPGInstrumentor().instrument()
        logger.info("asyncpg auto-instrumentation enabled")
        _enabled_instrumentations.append("asyncpg")
        return True
    except ImportError:
        logger.debug("opentelemetry-instrumentation-asyncpg not available, skipping asyncpg instrumentation")
        return False
    except Exception as e:
        logger.warning(f"Failed to setup asyncpg instrumentation: {e}")
        return False


def setup_sqlalchemy_instrumentation(engine: Optional[Any] = None) -> bool:
    """
    Setup SQLAlchemy auto-instrumentation.
    
    Automatically traces database queries made with SQLAlchemy.
    
    Args:
        engine: SQLAlchemy engine instance (optional)
        
    Returns:
        True if instrumentation was successful, False otherwise
        
    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine("postgresql://...")
        >>> setup_sqlalchemy_instrumentation(engine)
        True
    """
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor  # type: ignore
        
        if engine is not None:
            SQLAlchemyInstrumentor().instrument(engine=engine, enable_commenter=True)
            logger.info("SQLAlchemy auto-instrumentation enabled for engine")
        else:
            SQLAlchemyInstrumentor().instrument(enable_commenter=True)
            logger.info("SQLAlchemy auto-instrumentation enabled (global)")
        _enabled_instrumentations.append("sqlalchemy")
        return True
    except ImportError:
        logger.debug("opentelemetry-instrumentation-sqlalchemy not available, skipping SQLAlchemy instrumentation")
        return False
    except Exception as e:
        logger.warning(f"Failed to setup SQLAlchemy instrumentation: {e}")
        return False


def setup_redis_instrumentation() -> bool:
    """
    Setup Redis/Dragonfly auto-instrumentation.
    
    Automatically traces cache operations made with redis/aioredis.
    Works with Dragonfly since it's Redis-compatible.
    
    Returns:
        True if instrumentation was successful, False otherwise
        
    Example:
        >>> setup_redis_instrumentation()
        True
        >>> import redis
        >>> r = redis.Redis()
        >>> r.get("key")
        # Operation is automatically traced
    """
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor  # type: ignore
        
        RedisInstrumentor().instrument()
        logger.info("Redis/Dragonfly auto-instrumentation enabled")
        _enabled_instrumentations.append("redis")
        return True
    except ImportError:
        logger.debug("opentelemetry-instrumentation-redis not available, skipping Redis instrumentation")
        return False
    except Exception as e:
        logger.warning(f"Failed to setup Redis instrumentation: {e}")
        return False


def setup_all_instrumentation(
    fastapi_app: Optional[Any] = None,
    sqlalchemy_engine: Optional[Any] = None,
    include_fastapi: bool = True,
    include_httpx: bool = True,
    include_requests: bool = True,
    include_asyncpg: bool = True,
    include_sqlalchemy: bool = False,
    include_redis: bool = True,
) -> Dict[str, bool]:
    """
    Setup all available auto-instrumentation.
    
    Convenience function to enable all instrumentation at once.
    
    Args:
        fastapi_app: FastAPI application instance (optional)
        sqlalchemy_engine: SQLAlchemy engine instance (optional)
        include_fastapi: Whether to include FastAPI instrumentation
        include_httpx: Whether to include HTTPX instrumentation
        include_requests: Whether to include Requests instrumentation
        include_asyncpg: Whether to include asyncpg instrumentation
        include_sqlalchemy: Whether to include SQLAlchemy instrumentation
        include_redis: Whether to include Redis instrumentation
        
    Returns:
        Dictionary with instrumentation results (key: instrumentation name, value: success bool)
        
    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> results = setup_all_instrumentation(fastapi_app=app)
        >>> print(results)
        {'fastapi': True, 'httpx': True, 'requests': True, ...}
    """
    results: Dict[str, bool] = {}
    
    if include_fastapi:
        results["fastapi"] = setup_fastapi_instrumentation(fastapi_app)
    
    if include_httpx:
        results["httpx"] = setup_httpx_instrumentation()
    
    if include_requests:
        results["requests"] = setup_requests_instrumentation()
    
    if include_asyncpg:
        results["asyncpg"] = setup_asyncpg_instrumentation()
    
    if include_sqlalchemy:
        results["sqlalchemy"] = setup_sqlalchemy_instrumentation(sqlalchemy_engine)
    
    if include_redis:
        results["redis"] = setup_redis_instrumentation()
    
    logger.info(f"Auto-instrumentation setup complete: {results}")
    return results


def get_enabled_instrumentations() -> List[str]:
    """
    Get list of enabled instrumentations.
    
    Returns:
        List of enabled instrumentation names
    """
    return _enabled_instrumentations.copy()


def is_instrumentation_enabled(name: str) -> bool:
    """
    Check if a specific instrumentation is enabled.
    
    Args:
        name: Instrumentation name (e.g., "fastapi", "httpx")
        
    Returns:
        True if enabled, False otherwise
    """
    return name in _enabled_instrumentations

