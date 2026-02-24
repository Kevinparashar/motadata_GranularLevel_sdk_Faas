"""
Unit Tests for Codec Context DAL

Tests for codec encoding/decoding history and schema context persistence operations.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.faas.shared.dal.codec_context_dal import CodecContextDAL
from src.core.postgresql_database import DatabaseConnection


class TestCodecContextDAL:
    """Tests for CodecContextDAL."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        db = MagicMock(spec=DatabaseConnection)
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def dal(self, mock_db):
        """CodecContextDAL fixture."""
        return CodecContextDAL(mock_db)

    @pytest.mark.asyncio
    async def test_save_codec_operation_encode_success(self, dal, mock_db):
        """Test successful encode operation save."""
        mock_db.execute_query.return_value = {"operation_id": "op_123"}

        result = await dal.save_codec_operation(
            operation_id="op_123",
            operation_type="encode",
            message_type="agent_message",
            schema_version="1.0",
            codec_type="json",
            payload_size=1024,
            status="success",
        )

        assert result == "op_123"
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO codec_context" in call_args[0][0]
        params = call_args[1]["params"]
        assert params[0] == "op_123"
        assert params[1] == "encode"
        assert params[2] == "agent_message"
        assert params[3] == "1.0"

    @pytest.mark.asyncio
    async def test_save_codec_operation_decode_success(self, dal, mock_db):
        """Test successful decode operation save."""
        mock_db.execute_query.return_value = {"operation_id": "op_456"}

        result = await dal.save_codec_operation(
            operation_id="op_456",
            operation_type="decode",
            message_type="llm_request",
            schema_version="1.0",
            payload_size=512,
            status="success",
            validation_performed=True,
            validation_passed=True,
        )

        assert result == "op_456"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[1] == "decode"
        assert params[15] is True  # validation_performed
        assert params[16] is True  # validation_passed

    @pytest.mark.asyncio
    async def test_save_codec_operation_with_migration(self, dal, mock_db):
        """Test save codec operation with migration."""
        mock_db.execute_query.return_value = {"operation_id": "op_migrate"}

        result = await dal.save_codec_operation(
            operation_id="op_migrate",
            operation_type="decode",
            message_type="agent_message",
            schema_version="2.0",
            migration_used=True,
            source_version="1.0",
            target_version="2.0",
            status="success",
        )

        assert result == "op_migrate"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[12] is True  # migration_used
        assert params[13] == "1.0"  # source_version
        assert params[14] == "2.0"  # target_version

    @pytest.mark.asyncio
    async def test_save_codec_operation_with_error(self, dal, mock_db):
        """Test save codec operation with error."""
        mock_db.execute_query.return_value = {"operation_id": "op_error"}

        result = await dal.save_codec_operation(
            operation_id="op_error",
            operation_type="encode",
            message_type="agent_message",
            schema_version="1.0",
            status="error",
            error_message="Encoding failed",
            error_type="CodecEncodingError",
        )

        assert result == "op_error"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[9] == "error"  # status
        assert params[10] == "Encoding failed"  # error_message
        assert params[11] == "CodecEncodingError"  # error_type

    @pytest.mark.asyncio
    async def test_save_codec_operation_with_all_fields(self, dal, mock_db):
        """Test save codec operation with all fields."""
        mock_db.execute_query.return_value = {"operation_id": "op_full"}

        context_state = {"envelope_keys": ["schema_version", "message_type", "data"]}
        metadata = {"data_keys": ["from_agent", "to_agent", "content"]}

        result = await dal.save_codec_operation(
            operation_id="op_full",
            operation_type="encode",
            message_type="agent_message",
            schema_version="1.0",
            codec_type="json",
            tenant_id="tenant-1",
            user_id="user-1",
            correlation_id="corr-1",
            payload_size=2048,
            status="success",
            migration_used=False,
            validation_performed=True,
            validation_passed=True,
            context_state=context_state,
            metadata=metadata,
        )

        assert result == "op_full"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert json.loads(params[17]) == context_state  # context_state
        assert json.loads(params[18]) == metadata  # metadata

    @pytest.mark.asyncio
    async def test_get_codec_history_basic(self, dal, mock_db):
        """Test get codec history with basic filters."""
        mock_db.execute_query.return_value = [
            {
                "operation_id": "op1",
                "operation_type": "encode",
                "message_type": "agent_message",
                "status": "success",
            }
        ]

        results = await dal.get_codec_history(
            tenant_id="tenant-1",
            limit=10,
            offset=0,
        )

        assert len(results) == 1
        assert results[0]["operation_type"] == "encode"
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_codec_history_with_all_filters(self, dal, mock_db):
        """Test get codec history with all filters."""
        mock_db.execute_query.return_value = []

        results = await dal.get_codec_history(
            tenant_id="tenant-1",
            user_id="user-1",
            message_type="agent_message",
            operation_type="encode",
            schema_version="1.0",
            status="success",
            limit=50,
            offset=10,
        )

        assert results == []
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "message_type" in query
        assert "operation_type" in query
        assert "schema_version" in query
        assert "status" in query

    @pytest.mark.asyncio
    async def test_get_codec_history_with_json_parsing(self, dal, mock_db):
        """Test get codec history with JSON parsing."""
        mock_db.execute_query.return_value = [
            {
                "operation_id": "op1",
                "context_state": json.dumps({"keys": ["a", "b"]}),
                "metadata": json.dumps({"env": "prod"}),
            }
        ]

        results = await dal.get_codec_history()

        assert len(results) == 1
        assert isinstance(results[0]["context_state"], dict)
        assert isinstance(results[0]["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_schema_version_stats(self, dal, mock_db):
        """Test get schema version statistics."""
        mock_db.execute_query.return_value = [
            {
                "schema_version": "1.0",
                "usage_count": 100,
                "encode_count": 60,
                "decode_count": 40,
                "success_count": 95,
                "error_count": 5,
                "migration_count": 10,
                "avg_payload_size": 1024.5,
            }
        ]

        results = await dal.get_schema_version_stats(
            message_type="agent_message",
            tenant_id="tenant-1",
            time_range_hours=24,
        )

        assert len(results) == 1
        assert results[0]["schema_version"] == "1.0"
        assert results[0]["usage_count"] == 100
        assert results[0]["success_rate"] == pytest.approx(95.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_get_schema_version_stats_empty(self, dal, mock_db):
        """Test get schema version stats when no data."""
        mock_db.execute_query.return_value = None

        results = await dal.get_schema_version_stats()

        assert results == []

    @pytest.mark.asyncio
    async def test_get_serialization_context_state(self, dal, mock_db):
        """Test get serialization context state."""
        mock_db.execute_query.return_value = [
            {
                "operation_id": "op1",
                "correlation_id": "corr-1",
                "operation_type": "encode",
                "context_state": json.dumps({"state": "encoded"}),
            },
            {
                "operation_id": "op2",
                "correlation_id": "corr-1",
                "operation_type": "decode",
                "context_state": json.dumps({"state": "decoded"}),
            },
        ]

        results = await dal.get_serialization_context_state("corr-1", tenant_id="tenant-1")

        assert len(results) == 2
        assert all(r["correlation_id"] == "corr-1" for r in results)
        assert isinstance(results[0]["context_state"], dict)

    @pytest.mark.asyncio
    async def test_get_codec_operation_stats(self, dal, mock_db):
        """Test get codec operation statistics."""
        mock_db.execute_query.return_value = {
            "total_operations": 1000,
            "encode_operations": 600,
            "decode_operations": 400,
            "success_operations": 950,
            "error_operations": 50,
            "migration_operations": 100,
            "validation_operations": 800,
            "validation_passed_count": 780,
            "validation_failed_count": 20,
            "unique_message_types": 5,
            "unique_schema_versions": 3,
            "avg_payload_size": 1024.5,
            "max_payload_size": 5000,
            "min_payload_size": 100,
        }

        stats = await dal.get_codec_operation_stats(
            tenant_id="tenant-1",
            time_range_hours=24,
        )

        assert stats["total_operations"] == 1000
        assert stats["encode_operations"] == 600
        assert stats["decode_operations"] == 400
        assert stats["success_rate"] == pytest.approx(95.0, abs=0.1)
        assert stats["migration_rate"] == pytest.approx(10.0, abs=0.1)
        assert stats["validation_rate"] == pytest.approx(80.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_get_codec_operation_stats_empty(self, dal, mock_db):
        """Test get codec operation stats when no data."""
        mock_db.execute_query.return_value = None

        stats = await dal.get_codec_operation_stats()

        assert stats["total_operations"] == 0
        assert stats["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_message_type_stats(self, dal, mock_db):
        """Test get message type statistics."""
        mock_db.execute_query.return_value = [
            {
                "message_type": "agent_message",
                "usage_count": 500,
                "encode_count": 300,
                "decode_count": 200,
                "success_count": 480,
                "error_count": 20,
                "schema_versions_used": 2,
                "avg_payload_size": 1024.0,
            }
        ]

        results = await dal.get_message_type_stats(
            tenant_id="tenant-1",
            time_range_hours=24,
            limit=10,
        )

        assert len(results) == 1
        assert results[0]["message_type"] == "agent_message"
        assert results[0]["usage_count"] == 500
        assert results[0]["success_rate"] == pytest.approx(96.0, abs=0.1)

    @pytest.mark.asyncio
    async def test_cleanup_old_context(self, dal, mock_db):
        """Test cleanup old context."""
        mock_db.execute_query.return_value = 25

        result = await dal.cleanup_old_context(days=90, tenant_id="tenant-1")

        assert result == 25
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "DELETE FROM codec_context" in query
        assert "INTERVAL" in query

    @pytest.mark.asyncio
    async def test_cleanup_old_context_without_tenant(self, dal, mock_db):
        """Test cleanup old context without tenant."""
        mock_db.execute_query.return_value = 50

        result = await dal.cleanup_old_context(days=30)

        assert result == 50

    @pytest.mark.asyncio
    async def test_get_codec_history_empty(self, dal, mock_db):
        """Test get codec history with empty result."""
        mock_db.execute_query.return_value = None

        results = await dal.get_codec_history()

        assert results == []

    @pytest.mark.asyncio
    async def test_save_codec_operation_with_none_values(self, dal, mock_db):
        """Test save codec operation with None optional values."""
        mock_db.execute_query.return_value = {"operation_id": "op_none"}

        result = await dal.save_codec_operation(
            operation_id="op_none",
            operation_type="encode",
            message_type="test_message",
            schema_version="1.0",
        )

        assert result == "op_none"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[5] is None  # tenant_id
        assert params[6] is None  # user_id
        assert params[7] is None  # correlation_id

    @pytest.mark.asyncio
    async def test_get_serialization_context_state_without_tenant(self, dal, mock_db):
        """Test get serialization context state without tenant."""
        mock_db.execute_query.return_value = [{"operation_id": "op1"}]

        results = await dal.get_serialization_context_state("corr-1")

        assert len(results) == 1
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "AND tenant_id" not in query

