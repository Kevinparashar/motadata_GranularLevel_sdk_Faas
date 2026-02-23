"""
Unit Tests for LLMOps DAL

Tests database operations for LLM operations logging and metrics.
Follows @cursorrules.md: Success ≥2, Edge ≥2, Failure ≥2
"""


import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.faas.shared.dal.llmops_dal import LLMOpsDAL


class TestLLMOpsDAL:
    """Test LLMOpsDAL class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def llmops_dal(self, mock_db):
        """Create an LLMOpsDAL instance."""
        return LLMOpsDAL(mock_db)

    # Success Cases (≥2)
    @pytest.mark.asyncio
    async def test_save_operation_success(self, llmops_dal, mock_db):
        """Test successfully saving an LLM operation."""
        mock_db.execute_query.return_value = {"id": "record_123"}

        result = await llmops_dal.save_operation(
            operation_id="op_123",
            operation_type="completion",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=250.5,
            cost_usd=0.01,
            status="success",
            tenant_id="tenant_456",
            agent_id="agent_789",
            metadata={"key": "value"},
        )

        assert result == "record_123"
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO llm_operations" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_operations_success(self, llmops_dal, mock_db):
        """Test successfully getting operations."""
        mock_db.execute_query.return_value = [
            {
                "id": "record_1",
                "operation_id": "op_1",
                "operation_type": "completion",
                "model": "gpt-4",
                "metadata": json.dumps({"key": "value"}),
            },
            {
                "id": "record_2",
                "operation_id": "op_2",
                "operation_type": "embedding",
                "model": "text-embedding-3-small",
                "metadata": json.dumps({"key2": "value2"}),
            },
        ]

        result = await llmops_dal.get_operations(
            tenant_id="tenant_456", limit=10, offset=0
        )

        assert len(result) == 2
        assert result[0]["operation_id"] == "op_1"
        assert isinstance(result[0]["metadata"], dict)  # Should be parsed from JSON
        assert isinstance(result[1]["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_metrics_success(self, llmops_dal, mock_db):
        """Test successfully getting metrics."""
        mock_db.execute_query.return_value = {
            "total_operations": 100,
            "total_tokens": 50000,
            "total_cost_usd": 5.0,
            "average_latency_ms": 250.5,
            "success_count": 95,
            "error_count": 5,
        }

        # Mock by_model query
        async def mock_query(*args, **kwargs):
            if "GROUP BY model" in args[0]:
                return [
                    {
                        "model": "gpt-4",
                        "count": 50,
                        "tokens": 25000,
                        "cost_usd": 2.5,
                        "avg_latency_ms": 300.0,
                    },
                    {
                        "model": "gpt-3.5-turbo",
                        "count": 50,
                        "tokens": 25000,
                        "cost_usd": 2.5,
                        "avg_latency_ms": 200.0,
                    },
                ]
            elif "GROUP BY operation_type" in args[0]:
                return [
                    {"operation_type": "completion", "count": 80, "tokens": 40000},
                    {"operation_type": "embedding", "count": 20, "tokens": 10000},
                ]
            else:
                return {
                    "total_operations": 100,
                    "total_tokens": 50000,
                    "total_cost_usd": 5.0,
                    "average_latency_ms": 250.5,
                    "success_count": 95,
                    "error_count": 5,
                }

        mock_db.execute_query.side_effect = mock_query

        result = await llmops_dal.get_metrics(
            tenant_id="tenant_456", time_range_hours=24
        )

        assert result["total_operations"] == 100
        assert result["total_tokens"] == 50000
        assert result["total_cost_usd"] == 5.0
        assert "by_model" in result
        assert "by_type" in result
        assert result["success_rate"] == 0.95
        assert result["error_rate"] == 0.05

    @pytest.mark.asyncio
    async def test_get_cost_analysis_success(self, llmops_dal, mock_db):
        """Test successfully getting cost analysis."""
        mock_db.execute_query.return_value = [
            {
                "model": "gpt-4",
                "total_cost": 3.0,
                "avg_cost_per_operation": 0.06,
                "operation_count": 50,
            },
            {
                "model": "gpt-3.5-turbo",
                "total_cost": 2.0,
                "avg_cost_per_operation": 0.04,
                "operation_count": 50,
            },
        ]

        result = await llmops_dal.get_cost_analysis(
            tenant_id="tenant_456", time_range_hours=30 * 24
        )

        assert result["total_cost_usd"] == 5.0
        assert "by_model" in result
        assert "gpt-4" in result["by_model"]
        assert result["by_model"]["gpt-4"]["total_cost"] == 3.0

    @pytest.mark.asyncio
    async def test_get_operation_success(self, llmops_dal, mock_db):
        """Test successfully getting a single operation."""
        mock_db.execute_query.return_value = {
            "id": "record_123",
            "operation_id": "op_123",
            "operation_type": "completion",
            "model": "gpt-4",
            "metadata": json.dumps({"key": "value"}),
        }

        result = await llmops_dal.get_operation("op_123", tenant_id="tenant_456")

        assert result is not None
        assert result["operation_id"] == "op_123"
        assert isinstance(result["metadata"], dict)  # Should be parsed

    @pytest.mark.asyncio
    async def test_delete_old_operations_success(self, llmops_dal, mock_db):
        """Test successfully deleting old operations."""
        mock_db.execute_query.return_value = 50  # 50 operations deleted

        result = await llmops_dal.delete_old_operations(
            tenant_id="tenant_456", older_than_days=90
        )

        assert result == 50
        mock_db.execute_query.assert_called_once()

    # Edge Cases (≥2)
    @pytest.mark.asyncio
    async def test_save_operation_without_optional_fields(self, llmops_dal, mock_db):
        """Test saving operation without optional fields."""
        mock_db.execute_query.return_value = {"id": "record_123"}

        result = await llmops_dal.save_operation(
            operation_id="op_123",
            operation_type="completion",
            model="gpt-4",
        )

        assert result == "record_123"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        # Should have None for optional fields
        assert params[10] is None  # tenant_id
        assert params[11] is None  # agent_id

    @pytest.mark.asyncio
    async def test_get_operations_empty(self, llmops_dal, mock_db):
        """Test getting operations when none exist."""
        mock_db.execute_query.return_value = None

        result = await llmops_dal.get_operations(tenant_id="tenant_456")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_metrics_no_operations(self, llmops_dal, mock_db):
        """Test getting metrics when no operations exist."""
        mock_db.execute_query.return_value = {
            "total_operations": 0,
            "total_tokens": None,
            "total_cost_usd": None,
            "average_latency_ms": None,
            "success_count": 0,
            "error_count": 0,
        }

        # Mock by_model and by_type queries to return empty
        async def mock_query(*args, **kwargs):
            if "GROUP BY" in args[0]:
                return []
            else:
                return {
                    "total_operations": 0,
                    "total_tokens": None,
                    "total_cost_usd": None,
                    "average_latency_ms": None,
                    "success_count": 0,
                    "error_count": 0,
                }

        mock_db.execute_query.side_effect = mock_query

        result = await llmops_dal.get_metrics(tenant_id="tenant_456")

        assert result["total_operations"] == 0
        assert result["total_tokens"] == 0
        assert result["total_cost_usd"] == 0.0
        assert result["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_operation_not_found(self, llmops_dal, mock_db):
        """Test getting operation that doesn't exist."""
        mock_db.execute_query.return_value = None

        result = await llmops_dal.get_operation("op_999", tenant_id="tenant_456")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_operations_with_filters(self, llmops_dal, mock_db):
        """Test getting operations with all filters."""
        mock_db.execute_query.return_value = []

        result = await llmops_dal.get_operations(
            tenant_id="tenant_456",
            agent_id="agent_789",
            time_range_hours=24,
            limit=50,
            offset=10,
        )

        assert result == []
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_id" in query
        assert "agent_id" in query
        assert "created_at >=" in query

    @pytest.mark.asyncio
    async def test_get_operations_with_string_metadata(self, llmops_dal, mock_db):
        """Test getting operations with string JSON metadata."""
        mock_db.execute_query.return_value = [
            {
                "id": "record_1",
                "operation_id": "op_1",
                "metadata": '{"key": "value"}',  # String JSON
            }
        ]

        result = await llmops_dal.get_operations(tenant_id="tenant_456")

        assert len(result) == 1
        assert isinstance(result[0]["metadata"], dict)  # Should be parsed

    # Failure Cases (≥2)
    @pytest.mark.asyncio
    async def test_save_operation_database_error(self, llmops_dal, mock_db):
        """Test handling database error during save."""
        mock_db.execute_query.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await llmops_dal.save_operation(
                operation_id="op_123",
                operation_type="completion",
                model="gpt-4",
            )

    @pytest.mark.asyncio
    async def test_get_metrics_database_error(self, llmops_dal, mock_db):
        """Test handling database error during metrics retrieval."""
        mock_db.execute_query.side_effect = Exception("Query execution failed")

        with pytest.raises(Exception, match="Query execution failed"):
            await llmops_dal.get_metrics(tenant_id="tenant_456")

    @pytest.mark.asyncio
    async def test_delete_old_operations_database_error(self, llmops_dal, mock_db):
        """Test handling database error during delete."""
        mock_db.execute_query.side_effect = Exception("Delete operation failed")

        with pytest.raises(Exception, match="Delete operation failed"):
            await llmops_dal.delete_old_operations(tenant_id="tenant_456", older_than_days=90)

    @pytest.mark.asyncio
    async def test_get_cost_analysis_database_error(self, llmops_dal, mock_db):
        """Test handling database error during cost analysis."""
        mock_db.execute_query.side_effect = Exception("Cost analysis query failed")

        with pytest.raises(Exception, match="Cost analysis query failed"):
            await llmops_dal.get_cost_analysis(tenant_id="tenant_456")

