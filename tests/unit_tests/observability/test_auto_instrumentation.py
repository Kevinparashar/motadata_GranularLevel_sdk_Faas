"""
Unit Tests for OpenTelemetry Auto-Instrumentation

Tests for auto-instrumentation setup functions.
"""

from unittest.mock import MagicMock, patch

from src.core.otel_integration.auto_instrumentation import (
    setup_fastapi_instrumentation,
    setup_httpx_instrumentation,
    setup_requests_instrumentation,
    setup_asyncpg_instrumentation,
    setup_sqlalchemy_instrumentation,
    setup_redis_instrumentation,
    setup_all_instrumentation,
    get_enabled_instrumentations,
    is_instrumentation_enabled,
)


class TestFastAPIInstrumentation:
    """Tests for FastAPI auto-instrumentation."""

    def test_setup_fastapi_instrumentation_with_app(self):
        """Test setting up FastAPI instrumentation with app."""
        mock_app = MagicMock()
        
        mock_instrumentor_class = MagicMock()
        mock_instrumentor_class.instrument_app = MagicMock()
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.fastapi" in name:
                    return MagicMock(FastAPIInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_fastapi_instrumentation(mock_app)
            
            assert result is True
            mock_instrumentor_class.instrument_app.assert_called_once_with(mock_app)

    def test_setup_fastapi_instrumentation_without_app(self):
        """Test setting up FastAPI instrumentation without app."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.fastapi" in name:
                    return MagicMock(FastAPIInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_fastapi_instrumentation()
            
            assert result is True
            mock_instance.instrument.assert_called_once()

    def test_setup_fastapi_instrumentation_import_error(self):
        """Test FastAPI instrumentation when package not available."""
        with patch("builtins.__import__", side_effect=ImportError("No module")):
            result = setup_fastapi_instrumentation()
            
            assert result is False

    def test_setup_fastapi_instrumentation_exception(self):
        """Test FastAPI instrumentation handles exceptions."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.instrument = MagicMock(side_effect=Exception("Error"))
        mock_instrumentor_class.return_value = mock_instance
        mock_instrumentor_class.instrument_app = MagicMock(side_effect=Exception("Error"))
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.fastapi" in name:
                    return MagicMock(FastAPIInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_fastapi_instrumentation()
            
            assert result is False


class TestHTTPXInstrumentation:
    """Tests for HTTPX auto-instrumentation."""

    def test_setup_httpx_instrumentation_success(self):
        """Test setting up HTTPX instrumentation successfully."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.httpx" in name:
                    return MagicMock(HTTPXClientInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_httpx_instrumentation()
            
            assert result is True
            mock_instance.instrument.assert_called_once()

    def test_setup_httpx_instrumentation_import_error(self):
        """Test HTTPX instrumentation when package not available."""
        with patch("builtins.__import__", side_effect=ImportError("No module")):
            result = setup_httpx_instrumentation()
            
            assert result is False

    def test_setup_httpx_instrumentation_exception(self):
        """Test HTTPX instrumentation handles exceptions."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.instrument = MagicMock(side_effect=Exception("Error"))
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.httpx" in name:
                    return MagicMock(HTTPXClientInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_httpx_instrumentation()
            
            assert result is False


class TestRequestsInstrumentation:
    """Tests for Requests auto-instrumentation."""

    def test_setup_requests_instrumentation_success(self):
        """Test setting up Requests instrumentation successfully."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.requests" in name:
                    return MagicMock(RequestsInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_requests_instrumentation()
            
            assert result is True
            mock_instance.instrument.assert_called_once()

    def test_setup_requests_instrumentation_import_error(self):
        """Test Requests instrumentation when package not available."""
        with patch("builtins.__import__", side_effect=ImportError("No module")):
            result = setup_requests_instrumentation()
            
            assert result is False

    def test_setup_requests_instrumentation_exception(self):
        """Test Requests instrumentation handles exceptions."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.instrument = MagicMock(side_effect=Exception("Error"))
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.requests" in name:
                    return MagicMock(RequestsInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_requests_instrumentation()
            
            assert result is False


class TestAsyncPGInstrumentation:
    """Tests for asyncpg auto-instrumentation."""

    def test_setup_asyncpg_instrumentation_success(self):
        """Test setting up asyncpg instrumentation successfully."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.asyncpg" in name:
                    return MagicMock(AsyncPGInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_asyncpg_instrumentation()
            
            assert result is True
            mock_instance.instrument.assert_called_once()

    def test_setup_asyncpg_instrumentation_import_error(self):
        """Test asyncpg instrumentation when package not available."""
        with patch("builtins.__import__", side_effect=ImportError("No module")):
            result = setup_asyncpg_instrumentation()
            
            assert result is False

    def test_setup_asyncpg_instrumentation_exception(self):
        """Test asyncpg instrumentation handles exceptions."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.instrument = MagicMock(side_effect=Exception("Error"))
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.asyncpg" in name:
                    return MagicMock(AsyncPGInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_asyncpg_instrumentation()
            
            assert result is False


class TestSQLAlchemyInstrumentation:
    """Tests for SQLAlchemy auto-instrumentation."""

    def test_setup_sqlalchemy_instrumentation_with_engine(self):
        """Test setting up SQLAlchemy instrumentation with engine."""
        mock_engine = MagicMock()
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.sqlalchemy" in name:
                    return MagicMock(SQLAlchemyInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_sqlalchemy_instrumentation(mock_engine)
            
            assert result is True
            mock_instance.instrument.assert_called_once_with(engine=mock_engine, enable_commenter=True)

    def test_setup_sqlalchemy_instrumentation_without_engine(self):
        """Test setting up SQLAlchemy instrumentation without engine."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.sqlalchemy" in name:
                    return MagicMock(SQLAlchemyInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_sqlalchemy_instrumentation()
            
            assert result is True
            mock_instance.instrument.assert_called_once_with(enable_commenter=True)

    def test_setup_sqlalchemy_instrumentation_import_error(self):
        """Test SQLAlchemy instrumentation when package not available."""
        with patch("builtins.__import__", side_effect=ImportError("No module")):
            result = setup_sqlalchemy_instrumentation()
            
            assert result is False

    def test_setup_sqlalchemy_instrumentation_exception(self):
        """Test SQLAlchemy instrumentation handles exceptions."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.instrument = MagicMock(side_effect=Exception("Error"))
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.sqlalchemy" in name:
                    return MagicMock(SQLAlchemyInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_sqlalchemy_instrumentation()
            
            assert result is False


class TestRedisInstrumentation:
    """Tests for Redis auto-instrumentation."""

    def test_setup_redis_instrumentation_success(self):
        """Test setting up Redis instrumentation successfully."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.redis" in name:
                    return MagicMock(RedisInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_redis_instrumentation()
            
            assert result is True
            mock_instance.instrument.assert_called_once()

    def test_setup_redis_instrumentation_import_error(self):
        """Test Redis instrumentation when package not available."""
        with patch("builtins.__import__", side_effect=ImportError("No module")):
            result = setup_redis_instrumentation()
            
            assert result is False

    def test_setup_redis_instrumentation_exception(self):
        """Test Redis instrumentation handles exceptions."""
        mock_instrumentor_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.instrument = MagicMock(side_effect=Exception("Error"))
        mock_instrumentor_class.return_value = mock_instance
        
        with patch("builtins.__import__") as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if "opentelemetry.instrumentation.redis" in name:
                    return MagicMock(RedisInstrumentor=mock_instrumentor_class)
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            result = setup_redis_instrumentation()
            
            assert result is False


class TestSetupAllInstrumentation:
    """Tests for setup_all_instrumentation function."""

    def test_setup_all_instrumentation_all_enabled(self):
        """Test setting up all instrumentation with all enabled."""
        mock_app = MagicMock()
        
        with patch("src.core.otel_integration.auto_instrumentation.setup_fastapi_instrumentation", return_value=True) as mock_fastapi, \
             patch("src.core.otel_integration.auto_instrumentation.setup_httpx_instrumentation", return_value=True) as mock_httpx, \
             patch("src.core.otel_integration.auto_instrumentation.setup_requests_instrumentation", return_value=True) as mock_requests, \
             patch("src.core.otel_integration.auto_instrumentation.setup_asyncpg_instrumentation", return_value=True) as mock_asyncpg, \
             patch("src.core.otel_integration.auto_instrumentation.setup_redis_instrumentation", return_value=True) as mock_redis:
            
            results = setup_all_instrumentation(fastapi_app=mock_app)
            
            assert results["fastapi"] is True
            assert results["httpx"] is True
            assert results["requests"] is True
            assert results["asyncpg"] is True
            assert results["redis"] is True
            mock_fastapi.assert_called_once_with(mock_app)
            mock_httpx.assert_called_once()
            mock_requests.assert_called_once()
            mock_asyncpg.assert_called_once()
            mock_redis.assert_called_once()

    def test_setup_all_instrumentation_selective(self):
        """Test setting up instrumentation selectively."""
        with patch("src.core.otel_integration.auto_instrumentation.setup_fastapi_instrumentation", return_value=True) as mock_fastapi, \
             patch("src.core.otel_integration.auto_instrumentation.setup_httpx_instrumentation", return_value=True) as mock_httpx, \
             patch("src.core.otel_integration.auto_instrumentation.setup_requests_instrumentation", return_value=False) as mock_requests:
            
            results = setup_all_instrumentation(
                include_fastapi=True,
                include_httpx=True,
                include_requests=True,
                include_asyncpg=False,
                include_sqlalchemy=False,
                include_redis=False,
            )
            
            assert results["fastapi"] is True
            assert results["httpx"] is True
            assert results["requests"] is False
            assert "asyncpg" not in results
            assert "sqlalchemy" not in results
            assert "redis" not in results
            mock_fastapi.assert_called_once_with(None)
            mock_httpx.assert_called_once()
            mock_requests.assert_called_once()

    def test_setup_all_instrumentation_with_sqlalchemy_engine(self):
        """Test setting up all instrumentation with SQLAlchemy engine."""
        mock_engine = MagicMock()
        
        with patch("src.core.otel_integration.auto_instrumentation.setup_sqlalchemy_instrumentation", return_value=True) as mock_sqlalchemy:
            
            results = setup_all_instrumentation(
                sqlalchemy_engine=mock_engine,
                include_fastapi=False,
                include_httpx=False,
                include_requests=False,
                include_asyncpg=False,
                include_sqlalchemy=True,
                include_redis=False,
            )
            
            assert results["sqlalchemy"] is True
            mock_sqlalchemy.assert_called_once_with(mock_engine)

    def test_setup_all_instrumentation_all_failures(self):
        """Test setup_all_instrumentation when all fail."""
        with patch("src.core.otel_integration.auto_instrumentation.setup_fastapi_instrumentation", return_value=False), \
             patch("src.core.otel_integration.auto_instrumentation.setup_httpx_instrumentation", return_value=False), \
             patch("src.core.otel_integration.auto_instrumentation.setup_requests_instrumentation", return_value=False), \
             patch("src.core.otel_integration.auto_instrumentation.setup_asyncpg_instrumentation", return_value=False), \
             patch("src.core.otel_integration.auto_instrumentation.setup_redis_instrumentation", return_value=False):
            
            results = setup_all_instrumentation()
            
            assert results["fastapi"] is False
            assert results["httpx"] is False
            assert results["requests"] is False
            assert results["asyncpg"] is False
            assert results["redis"] is False


class TestInstrumentationTracking:
    """Tests for instrumentation tracking functions."""

    def test_get_enabled_instrumentations_empty(self):
        """Test getting enabled instrumentations when none are enabled."""
        # Clear any existing instrumentations by patching the list
        with patch("src.core.otel_integration.auto_instrumentation._enabled_instrumentations", []):
            result = get_enabled_instrumentations()
            
            assert result == []
            assert isinstance(result, list)

    def test_get_enabled_instrumentations_after_setup(self):
        """Test getting enabled instrumentations after setup."""
        with patch("src.core.otel_integration.auto_instrumentation._enabled_instrumentations", ["fastapi", "httpx"]):
            result = get_enabled_instrumentations()
            
            assert result == ["fastapi", "httpx"]
            # Verify it returns a copy
            result.append("test")
            assert "test" not in get_enabled_instrumentations()

    def test_is_instrumentation_enabled_true(self):
        """Test checking if instrumentation is enabled when it is."""
        with patch("src.core.otel_integration.auto_instrumentation._enabled_instrumentations", ["fastapi", "httpx"]):
            result = is_instrumentation_enabled("fastapi")
            
            assert result is True

    def test_is_instrumentation_enabled_false(self):
        """Test checking if instrumentation is enabled when it is not."""
        with patch("src.core.otel_integration.auto_instrumentation._enabled_instrumentations", ["fastapi"]):
            result = is_instrumentation_enabled("httpx")
            
            assert result is False

    def test_is_instrumentation_enabled_empty_list(self):
        """Test checking if instrumentation is enabled when list is empty."""
        with patch("src.core.otel_integration.auto_instrumentation._enabled_instrumentations", []):
            result = is_instrumentation_enabled("fastapi")
            
            assert result is False
