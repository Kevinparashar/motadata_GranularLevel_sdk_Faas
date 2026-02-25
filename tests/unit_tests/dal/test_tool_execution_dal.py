"""
Comprehensive tests for ToolExecutionDAL.

Tests all methods and edge cases to achieve >85% coverage.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.faas.shared.dal.tool_execution_dal import ToolExecutionDAL


class TestToolExecutionDAL:
    """Test ToolExecutionDAL class."""

    @pytest.fixture
    def mock_db_connection(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def dal(self, mock_db_connection):
        """Create ToolExecutionDAL instance."""
        return ToolExecutionDAL(mock_db_connection)

    @pytest.mark.asyncio
    async def test_init(self, mock_db_connection):
        """Test ToolExecutionDAL initialization."""
        dal = ToolExecutionDAL(mock_db_connection)
        assert dal.db == mock_db_connection

    @pytest.mark.asyncio
    async def test_save_execution_basic(self, dal, mock_db_connection):
        """Test save_execution() with basic parameters."""
        mock_db_connection.execute_query.return_value = {"id": "exec-123"}
        
        result = await dal.save_execution(
            tool_id="tool-1",
            status="success"
        )
        
        assert result == "exec-123"
        call_args = mock_db_connection.execute_query.call_args
        assert "INSERT INTO tool_executions" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_save_execution_with_all_params(self, dal, mock_db_connection):
        """Test save_execution() with all parameters."""
        mock_db_connection.execute_query.return_value = {"id": "exec-123"}
        
        result = await dal.save_execution(
            tool_id="tool-1",
            agent_id="agent-1",
            arguments={"arg1": "value1"},
            result={"output": "result"},
            status="success",
            error=None,
            tenant_id="tenant-1",
            execution_time_ms=150.5,
            metadata={"key": "value"}
        )
        
        assert result == "exec-123"
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][0] == "tool-1"
        assert call_args[1]["params"][1] == "agent-1"

    @pytest.mark.asyncio
    async def test_save_execution_with_simple_result(self, dal, mock_db_connection):
        """Test save_execution() with simple result types."""
        mock_db_connection.execute_query.return_value = {"id": "exec-123"}
        
        # Test with string result
        await dal.save_execution(tool_id="tool-1", result="simple string")
        
        # Test with int result
        await dal.save_execution(tool_id="tool-1", result=42)
        
        # Test with float result
        await dal.save_execution(tool_id="tool-1", result=3.14)
        
        # Test with bool result
        await dal.save_execution(tool_id="tool-1", result=True)
        
        # Test with None result
        await dal.save_execution(tool_id="tool-1", result=None)

    @pytest.mark.asyncio
    async def test_save_execution_with_complex_result(self, dal, mock_db_connection):
        """Test save_execution() with complex result that needs JSON serialization."""
        mock_db_connection.execute_query.return_value = {"id": "exec-123"}
        
        complex_result = {"nested": {"data": [1, 2, 3]}}
        await dal.save_execution(tool_id="tool-1", result=complex_result)
        
        call_args = mock_db_connection.execute_query.call_args
        # Result should be JSON string
        assert isinstance(call_args[1]["params"][3], str)

    @pytest.mark.asyncio
    async def test_save_execution_result_serialization_error(self, dal, mock_db_connection):
        """Test save_execution() when result serialization fails."""
        mock_db_connection.execute_query.return_value = {"id": "exec-123"}
        
        # Create an object that can't be JSON serialized
        class Unserializable:
            pass
        
        await dal.save_execution(tool_id="tool-1", result=Unserializable())
        
        call_args = mock_db_connection.execute_query.call_args
        # Should fall back to str() conversion
        assert call_args[1]["params"][3] is not None

    @pytest.mark.asyncio
    async def test_save_execution_with_none_arguments_metadata(self, dal, mock_db_connection):
        """Test save_execution() with None arguments and metadata."""
        mock_db_connection.execute_query.return_value = {"id": "exec-123"}
        
        await dal.save_execution(
            tool_id="tool-1",
            arguments=None,
            metadata=None
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][2] == json.dumps({})
        assert call_args[1]["params"][8] == json.dumps({})

    @pytest.mark.asyncio
    async def test_get_executions_basic(self, dal, mock_db_connection):
        """Test get_executions() with basic parameters."""
        mock_results = [
            {
                "id": "exec-1",
                "tool_id": "tool-1",
                "agent_id": "agent-1",
                "arguments": json.dumps({"arg1": "value1"}),
                "result": "result1",
                "status": "success",
                "error": None,
                "execution_time_ms": 100.0,
                "metadata": json.dumps({"key": "value"}),
                "created_at": "2024-01-01"
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.get_executions()
        
        assert len(result) == 1
        assert result[0]["id"] == "exec-1"

    @pytest.mark.asyncio
    async def test_get_executions_with_tool_id(self, dal, mock_db_connection):
        """Test get_executions() with tool_id filter."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.get_executions(tool_id="tool-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tool_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_executions_with_agent_id(self, dal, mock_db_connection):
        """Test get_executions() with agent_id filter."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.get_executions(agent_id="agent-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND agent_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_executions_with_tenant_id(self, dal, mock_db_connection):
        """Test get_executions() with tenant_id filter."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.get_executions(tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_executions_with_status(self, dal, mock_db_connection):
        """Test get_executions() with status filter."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.get_executions(status="error")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND status = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_executions_with_all_filters(self, dal, mock_db_connection):
        """Test get_executions() with all filters."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.get_executions(
            tool_id="tool-1",
            agent_id="agent-1",
            tenant_id="tenant-1",
            status="success",
            limit=50,
            offset=10
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tool_id = $" in call_args[0][0]
        assert "AND agent_id = $" in call_args[0][0]
        assert "AND tenant_id = $" in call_args[0][0]
        assert "AND status = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_executions_parses_json_fields(self, dal, mock_db_connection):
        """Test get_executions() parses JSON fields correctly."""
        mock_results = [
            {
                "id": "exec-1",
                "tool_id": "tool-1",
                "agent_id": "agent-1",
                "arguments": json.dumps({"arg1": "value1"}),
                "result": json.dumps({"output": "result"}),
                "status": "success",
                "error": None,
                "execution_time_ms": 100.0,
                "metadata": json.dumps({"key": "value"}),
                "created_at": "2024-01-01"
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.get_executions()
        
        assert result[0]["arguments"] == {"arg1": "value1"}
        assert result[0]["metadata"] == {"key": "value"}
        assert result[0]["result"] == {"output": "result"}

    @pytest.mark.asyncio
    async def test_get_executions_arguments_as_dict(self, dal, mock_db_connection):
        """Test get_executions() when arguments is already a dict."""
        mock_results = [
            {
                "id": "exec-1",
                "tool_id": "tool-1",
                "agent_id": None,
                "arguments": {"arg1": "value1"},  # Already a dict
                "result": None,
                "status": "success",
                "error": None,
                "execution_time_ms": None,
                "metadata": None,
                "created_at": "2024-01-01"
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.get_executions()
        
        assert result[0]["arguments"] == {"arg1": "value1"}

    @pytest.mark.asyncio
    async def test_get_executions_metadata_as_dict(self, dal, mock_db_connection):
        """Test get_executions() when metadata is already a dict."""
        mock_results = [
            {
                "id": "exec-1",
                "tool_id": "tool-1",
                "agent_id": None,
                "arguments": None,
                "result": None,
                "status": "success",
                "error": None,
                "execution_time_ms": None,
                "metadata": {"key": "value"},  # Already a dict
                "created_at": "2024-01-01"
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.get_executions()
        
        assert result[0]["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_executions_result_not_json(self, dal, mock_db_connection):
        """Test get_executions() when result is not JSON."""
        mock_results = [
            {
                "id": "exec-1",
                "tool_id": "tool-1",
                "agent_id": None,
                "arguments": None,
                "result": "plain string result",  # Not JSON
                "status": "success",
                "error": None,
                "execution_time_ms": None,
                "metadata": None,
                "created_at": "2024-01-01"
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.get_executions()
        
        # Should remain as string if not valid JSON
        assert result[0]["result"] == "plain string result"

    @pytest.mark.asyncio
    async def test_get_executions_result_json_decode_error(self, dal, mock_db_connection):
        """Test get_executions() when result JSON decode fails."""
        mock_results = [
            {
                "id": "exec-1",
                "tool_id": "tool-1",
                "agent_id": None,
                "arguments": None,
                "result": "{invalid json}",  # Invalid JSON
                "status": "success",
                "error": None,
                "execution_time_ms": None,
                "metadata": None,
                "created_at": "2024-01-01"
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.get_executions()
        
        # Should remain as string if JSON decode fails
        assert result[0]["result"] == "{invalid json}"

    @pytest.mark.asyncio
    async def test_get_executions_empty_result(self, dal, mock_db_connection):
        """Test get_executions() with empty result."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.get_executions()
        
        assert result == []

    @pytest.mark.asyncio
    async def test_cleanup_old_executions_basic(self, dal, mock_db_connection):
        """Test cleanup_old_executions() with basic parameters."""
        mock_db_connection.execute_query.return_value = 5  # Rows deleted
        
        result = await dal.cleanup_old_executions(days=30)
        
        assert result == 5
        call_args = mock_db_connection.execute_query.call_args
        assert "DELETE FROM tool_executions" in call_args[0][0]
        assert "INTERVAL '30 days'" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_cleanup_old_executions_with_tenant_id(self, dal, mock_db_connection):
        """Test cleanup_old_executions() with tenant_id."""
        mock_db_connection.execute_query.return_value = 3
        
        result = await dal.cleanup_old_executions(days=30, tenant_id="tenant-1")
        
        assert result == 3
        call_args = mock_db_connection.execute_query.call_args
        assert "WHERE tenant_id = $1 AND" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_cleanup_old_executions_no_rows_deleted(self, dal, mock_db_connection):
        """Test cleanup_old_executions() when no rows deleted."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.cleanup_old_executions(days=30)
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_executions_custom_days(self, dal, mock_db_connection):
        """Test cleanup_old_executions() with custom days."""
        mock_db_connection.execute_query.return_value = 10
        
        _result = await dal.cleanup_old_executions(days=60)
        
        call_args = mock_db_connection.execute_query.call_args
        assert "INTERVAL '60 days'" in call_args[0][0]

