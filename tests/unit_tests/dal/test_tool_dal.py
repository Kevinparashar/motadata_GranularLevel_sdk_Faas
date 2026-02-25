"""
Comprehensive tests for ToolDAL.

Tests all methods and edge cases to achieve >85% coverage.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.faas.shared.dal.tool_dal import ToolDAL


class TestToolDAL:
    """Test ToolDAL class."""

    @pytest.fixture
    def mock_db_connection(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def dal(self, mock_db_connection):
        """Create ToolDAL instance."""
        return ToolDAL(mock_db_connection)

    @pytest.mark.asyncio
    async def test_init(self, mock_db_connection):
        """Test ToolDAL initialization."""
        dal = ToolDAL(mock_db_connection)
        assert dal.db == mock_db_connection

    @pytest.mark.asyncio
    async def test_save_tool_basic(self, dal, mock_db_connection):
        """Test save_tool() with basic parameters."""
        await dal.save_tool(
            tool_id="tool-1",
            name="Test Tool",
            description="Test description",
            tool_type="function",
            parameters=[{"name": "param1", "type": "string"}]
        )
        
        mock_db_connection.execute_query.assert_called_once()
        call_args = mock_db_connection.execute_query.call_args
        assert "INSERT INTO tools" in call_args[0][0]
        assert call_args[1]["params"][0] == "tool-1"
        assert call_args[1]["params"][1] == "Test Tool"

    @pytest.mark.asyncio
    async def test_save_tool_with_all_params(self, dal, mock_db_connection):
        """Test save_tool() with all parameters."""
        parameters = [{"name": "param1", "type": "string"}]
        metadata = {"category": "utility"}
        tags = ["tag1", "tag2"]
        
        await dal.save_tool(
            tool_id="tool-1",
            name="Test Tool",
            description="Test description",
            tool_type="function",
            parameters=parameters,
            tenant_id="tenant-1",
            metadata=metadata,
            tags=tags
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][4] == json.dumps(parameters)
        assert call_args[1]["params"][5] == json.dumps(metadata)
        assert call_args[1]["params"][6] == json.dumps(tags)
        assert call_args[1]["params"][7] == "tenant-1"

    @pytest.mark.asyncio
    async def test_save_tool_with_none_metadata_tags(self, dal, mock_db_connection):
        """Test save_tool() with None metadata and tags."""
        await dal.save_tool(
            tool_id="tool-1",
            name="Test Tool",
            description="Test description",
            tool_type="function",
            parameters=[],
            metadata=None,
            tags=None
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][5] == json.dumps({})
        assert call_args[1]["params"][6] == json.dumps([])

    @pytest.mark.asyncio
    async def test_save_tool_on_conflict_update(self, dal, mock_db_connection):
        """Test save_tool() updates on conflict."""
        await dal.save_tool(
            tool_id="tool-1",
            name="Updated Tool",
            description="Updated description",
            tool_type="api",
            parameters=[]
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert "ON CONFLICT" in call_args[0][0]
        assert "DO UPDATE SET" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_load_tool_basic(self, dal, mock_db_connection):
        """Test load_tool() with basic parameters."""
        mock_result = {
            "tool_id": "tool-1",
            "name": "Test Tool",
            "description": "Test description",
            "tool_type": "function",
            "parameters": json.dumps([{"name": "param1"}]),
            "metadata": json.dumps({"key": "value"}),
            "tags": json.dumps(["tag1"])
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.load_tool("tool-1")
        
        assert result is not None
        assert result["tool_id"] == "tool-1"
        assert result["parameters"] == [{"name": "param1"}]
        assert result["metadata"] == {"key": "value"}
        assert result["tags"] == ["tag1"]

    @pytest.mark.asyncio
    async def test_load_tool_with_tenant_id(self, dal, mock_db_connection):
        """Test load_tool() with tenant_id."""
        mock_result = {
            "tool_id": "tool-1",
            "name": "Test Tool",
            "description": "Test description",
            "tool_type": "function",
            "parameters": None,
            "metadata": None,
            "tags": None
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        _result = await dal.load_tool("tool-1", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $2" in call_args[0][0]
        assert call_args[1]["params"][1] == "tenant-1"

    @pytest.mark.asyncio
    async def test_load_tool_not_found(self, dal, mock_db_connection):
        """Test load_tool() when tool not found."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.load_tool("nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_load_tool_parameters_as_dict(self, dal, mock_db_connection):
        """Test load_tool() when parameters is already a dict."""
        mock_result = {
            "tool_id": "tool-1",
            "name": "Test Tool",
            "description": "Test description",
            "tool_type": "function",
            "parameters": [{"name": "param1"}],  # Already a dict
            "metadata": None,
            "tags": None
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.load_tool("tool-1")
        
        assert result["parameters"] == [{"name": "param1"}]

    @pytest.mark.asyncio
    async def test_load_tool_metadata_as_dict(self, dal, mock_db_connection):
        """Test load_tool() when metadata is already a dict."""
        mock_result = {
            "tool_id": "tool-1",
            "name": "Test Tool",
            "description": "Test description",
            "tool_type": "function",
            "parameters": None,
            "metadata": {"key": "value"},  # Already a dict
            "tags": None
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.load_tool("tool-1")
        
        assert result["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_load_tool_tags_as_list(self, dal, mock_db_connection):
        """Test load_tool() when tags is already a list."""
        mock_result = {
            "tool_id": "tool-1",
            "name": "Test Tool",
            "description": "Test description",
            "tool_type": "function",
            "parameters": None,
            "metadata": None,
            "tags": ["tag1", "tag2"]  # Already a list
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.load_tool("tool-1")
        
        assert result["tags"] == ["tag1", "tag2"]

    @pytest.mark.asyncio
    async def test_list_tools_basic(self, dal, mock_db_connection):
        """Test list_tools() with basic parameters."""
        mock_results = [
            {
                "tool_id": "tool-1",
                "name": "Tool 1",
                "description": "Description 1",
                "tool_type": "function",
                "parameters": json.dumps([{"name": "param1"}]),
                "metadata": None,
                "tags": None
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_tools()
        
        assert len(result) == 1
        call_args = mock_db_connection.execute_query.call_args
        assert "SELECT tool_id" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_tools_with_tenant_id(self, dal, mock_db_connection):
        """Test list_tools() with tenant_id."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_tools(tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_tools_with_tool_type(self, dal, mock_db_connection):
        """Test list_tools() with tool_type filter."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_tools(tool_type="function")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tool_type = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_tools_with_tags(self, dal, mock_db_connection):
        """Test list_tools() with tags filter."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_tools(tags=["tag1", "tag2"])
        
        call_args = mock_db_connection.execute_query.call_args
        assert "tags::jsonb @>" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_tools_with_limit_offset(self, dal, mock_db_connection):
        """Test list_tools() with limit and offset."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_tools(limit=50, offset=10)
        
        call_args = mock_db_connection.execute_query.call_args
        assert "LIMIT $" in call_args[0][0]
        assert "OFFSET $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_tools_with_all_filters(self, dal, mock_db_connection):
        """Test list_tools() with all filters."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_tools(
            tenant_id="tenant-1",
            tool_type="function",
            tags=["tag1"],
            limit=20,
            offset=5
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $" in call_args[0][0]
        assert "AND tool_type = $" in call_args[0][0]
        assert "tags::jsonb @>" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_tools_parses_json_fields(self, dal, mock_db_connection):
        """Test list_tools() parses JSON fields correctly."""
        mock_results = [
            {
                "tool_id": "tool-1",
                "name": "Tool 1",
                "description": "Description 1",
                "tool_type": "function",
                "parameters": json.dumps([{"name": "param1"}]),
                "metadata": json.dumps({"key": "value"}),
                "tags": json.dumps(["tag1"])
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_tools()
        
        assert result[0]["parameters"] == [{"name": "param1"}]
        assert result[0]["metadata"] == {"key": "value"}
        assert result[0]["tags"] == ["tag1"]

    @pytest.mark.asyncio
    async def test_list_tools_empty_result(self, dal, mock_db_connection):
        """Test list_tools() with empty result."""
        mock_db_connection.execute_query.return_value = None
        
        _result = await dal.list_tools()
        
        assert _result == []

    @pytest.mark.asyncio
    async def test_delete_tool_basic(self, dal, mock_db_connection):
        """Test delete_tool() with basic parameters."""
        mock_db_connection.execute_query.return_value = 1  # Rows affected
        
        result = await dal.delete_tool("tool-1")
        
        assert result is True
        call_args = mock_db_connection.execute_query.call_args
        assert "DELETE FROM tools" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_tool_with_tenant_id(self, dal, mock_db_connection):
        """Test delete_tool() with tenant_id."""
        mock_db_connection.execute_query.return_value = 1
        
        _result = await dal.delete_tool("tool-1", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $2" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_tool_not_found(self, dal, mock_db_connection):
        """Test delete_tool() when tool not found."""
        mock_db_connection.execute_query.return_value = 0  # No rows affected
        
        result = await dal.delete_tool("nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_tool_exists_basic(self, dal, mock_db_connection):
        """Test tool_exists() with basic parameters."""
        mock_db_connection.execute_query.return_value = {"1": 1}  # Row exists
        
        result = await dal.tool_exists("tool-1")
        
        assert result is True
        call_args = mock_db_connection.execute_query.call_args
        assert "SELECT 1 FROM tools" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_tool_exists_with_tenant_id(self, dal, mock_db_connection):
        """Test tool_exists() with tenant_id."""
        mock_db_connection.execute_query.return_value = {"1": 1}
        
        _result = await dal.tool_exists("tool-1", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $2" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_tool_exists_not_found(self, dal, mock_db_connection):
        """Test tool_exists() when tool does not exist."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.tool_exists("nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_list_tools_parameters_as_dict(self, dal, mock_db_connection):
        """Test list_tools() when parameters is already a dict."""
        mock_results = [
            {
                "tool_id": "tool-1",
                "name": "Tool 1",
                "description": "Description 1",
                "tool_type": "function",
                "parameters": [{"name": "param1"}],  # Already a dict
                "metadata": None,
                "tags": None
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_tools()
        
        assert result[0]["parameters"] == [{"name": "param1"}]

    @pytest.mark.asyncio
    async def test_list_tools_metadata_as_dict(self, dal, mock_db_connection):
        """Test list_tools() when metadata is already a dict."""
        mock_results = [
            {
                "tool_id": "tool-1",
                "name": "Tool 1",
                "description": "Description 1",
                "tool_type": "function",
                "parameters": None,
                "metadata": {"key": "value"},  # Already a dict
                "tags": None
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_tools()
        
        assert result[0]["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_list_tools_tags_as_list(self, dal, mock_db_connection):
        """Test list_tools() when tags is already a list."""
        mock_results = [
            {
                "tool_id": "tool-1",
                "name": "Tool 1",
                "description": "Description 1",
                "tool_type": "function",
                "parameters": None,
                "metadata": None,
                "tags": ["tag1", "tag2"]  # Already a list
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_tools()
        
        assert result[0]["tags"] == ["tag1", "tag2"]

