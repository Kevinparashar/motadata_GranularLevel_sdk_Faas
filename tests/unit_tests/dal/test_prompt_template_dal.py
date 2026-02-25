"""
Comprehensive tests for PromptTemplateDAL.

Tests all methods and edge cases to achieve >85% coverage.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.faas.shared.dal.prompt_template_dal import PromptTemplateDAL


class TestPromptTemplateDAL:
    """Test PromptTemplateDAL class."""

    @pytest.fixture
    def mock_db_connection(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def dal(self, mock_db_connection):
        """Create PromptTemplateDAL instance."""
        return PromptTemplateDAL(mock_db_connection)

    @pytest.mark.asyncio
    async def test_init(self, mock_db_connection):
        """Test PromptTemplateDAL initialization."""
        dal = PromptTemplateDAL(mock_db_connection)
        assert dal.db == mock_db_connection

    @pytest.mark.asyncio
    async def test_save_template_basic(self, dal, mock_db_connection):
        """Test save_template() with basic parameters."""
        await dal.save_template(
            name="test_template",
            version="1.0",
            content="Test content"
        )
        
        mock_db_connection.execute_query.assert_called_once()
        call_args = mock_db_connection.execute_query.call_args
        assert "INSERT INTO prompt_templates" in call_args[0][0]
        assert call_args[1]["params"][0] == "test_template"
        assert call_args[1]["params"][1] == "1.0"
        assert call_args[1]["params"][2] == "Test content"

    @pytest.mark.asyncio
    async def test_save_template_with_tenant_id(self, dal, mock_db_connection):
        """Test save_template() with tenant_id."""
        await dal.save_template(
            name="test_template",
            version="1.0",
            content="Test content",
            tenant_id="tenant-1"
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][4] == "tenant-1"

    @pytest.mark.asyncio
    async def test_save_template_with_metadata(self, dal, mock_db_connection):
        """Test save_template() with metadata."""
        metadata = {"key": "value", "type": "prompt"}
        await dal.save_template(
            name="test_template",
            version="1.0",
            content="Test content",
            metadata=metadata
        )
        
        call_args = mock_db_connection.execute_query.call_args
        metadata_json = call_args[1]["params"][3]
        assert json.loads(metadata_json) == metadata

    @pytest.mark.asyncio
    async def test_save_template_with_none_metadata(self, dal, mock_db_connection):
        """Test save_template() with None metadata."""
        await dal.save_template(
            name="test_template",
            version="1.0",
            content="Test content",
            metadata=None
        )
        
        call_args = mock_db_connection.execute_query.call_args
        metadata_json = call_args[1]["params"][3]
        assert json.loads(metadata_json) == {}

    @pytest.mark.asyncio
    async def test_save_template_on_conflict_update(self, dal, mock_db_connection):
        """Test save_template() updates on conflict."""
        await dal.save_template(
            name="test_template",
            version="1.0",
            content="Updated content"
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert "ON CONFLICT" in call_args[0][0]
        assert "DO UPDATE SET" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_load_template_with_version(self, dal, mock_db_connection):
        """Test load_template() with specific version."""
        mock_result = {
            "name": "test_template",
            "version": "1.0",
            "content": "Test content",
            "metadata": json.dumps({"key": "value"}),
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01"
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.load_template("test_template", version="1.0")
        
        assert result is not None
        assert result["name"] == "test_template"
        assert result["version"] == "1.0"
        assert result["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_load_template_with_version_and_tenant(self, dal, mock_db_connection):
        """Test load_template() with version and tenant_id."""
        mock_result = {
            "name": "test_template",
            "version": "1.0",
            "content": "Test content",
            "metadata": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01"
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        _result = await dal.load_template("test_template", version="1.0", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $3" in call_args[0][0]
        assert call_args[1]["params"][2] == "tenant-1"

    @pytest.mark.asyncio
    async def test_load_template_without_version(self, dal, mock_db_connection):
        """Test load_template() without version (latest)."""
        mock_result = {
            "name": "test_template",
            "version": "2.0",
            "content": "Latest content",
            "metadata": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01"
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        _result = await dal.load_template("test_template")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "ORDER BY version DESC LIMIT 1" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_load_template_without_version_with_tenant(self, dal, mock_db_connection):
        """Test load_template() without version but with tenant_id."""
        mock_result = {
            "name": "test_template",
            "version": "1.0",
            "content": "Test content",
            "metadata": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01"
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        _result = await dal.load_template("test_template", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $2" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_load_template_not_found(self, dal, mock_db_connection):
        """Test load_template() when template not found."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.load_template("nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_load_template_metadata_as_dict(self, dal, mock_db_connection):
        """Test load_template() when metadata is already a dict."""
        mock_result = {
            "name": "test_template",
            "version": "1.0",
            "content": "Test content",
            "metadata": {"key": "value"},  # Already a dict
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01"
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.load_template("test_template")
        
        assert result["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_list_templates_basic(self, dal, mock_db_connection):
        """Test list_templates() with basic parameters."""
        mock_results = [
            {"name": "template1", "version": "1.0", "content": "Content1", "metadata": None, "created_at": "2024-01-01", "updated_at": "2024-01-01"},
            {"name": "template2", "version": "1.0", "content": "Content2", "metadata": None, "created_at": "2024-01-01", "updated_at": "2024-01-01"}
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_templates()
        
        assert len(result) == 2
        call_args = mock_db_connection.execute_query.call_args
        assert "DISTINCT ON (name)" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_templates_with_tenant_id(self, dal, mock_db_connection):
        """Test list_templates() with tenant_id."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_templates(tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "WHERE tenant_id = $1" in call_args[0][0]
        assert call_args[1]["params"][0] == "tenant-1"

    @pytest.mark.asyncio
    async def test_list_templates_with_limit_offset(self, dal, mock_db_connection):
        """Test list_templates() with limit and offset."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_templates(limit=50, offset=10)
        
        call_args = mock_db_connection.execute_query.call_args
        assert "LIMIT $" in call_args[0][0]
        assert "OFFSET $" in call_args[0][0]
        assert call_args[1]["params"][-2] == 50
        assert call_args[1]["params"][-1] == 10

    @pytest.mark.asyncio
    async def test_list_templates_with_metadata_parsing(self, dal, mock_db_connection):
        """Test list_templates() parses metadata correctly."""
        mock_results = [
            {"name": "template1", "version": "1.0", "content": "Content1", "metadata": json.dumps({"key": "value"}), "created_at": "2024-01-01", "updated_at": "2024-01-01"}
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_templates()
        
        assert result[0]["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_list_templates_empty_result(self, dal, mock_db_connection):
        """Test list_templates() with empty result."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.list_templates()
        
        assert result == []

    @pytest.mark.asyncio
    async def test_list_versions_basic(self, dal, mock_db_connection):
        """Test list_versions() with basic parameters."""
        mock_results = [
            {"name": "template1", "version": "2.0", "content": "Content2", "metadata": None, "created_at": "2024-01-01", "updated_at": "2024-01-01"},
            {"name": "template1", "version": "1.0", "content": "Content1", "metadata": None, "created_at": "2024-01-01", "updated_at": "2024-01-01"}
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_versions("template1")
        
        assert len(result) == 2
        call_args = mock_db_connection.execute_query.call_args
        assert "ORDER BY version DESC" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_versions_with_tenant_id(self, dal, mock_db_connection):
        """Test list_versions() with tenant_id."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_versions("template1", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $2" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_versions_with_metadata_parsing(self, dal, mock_db_connection):
        """Test list_versions() parses metadata correctly."""
        mock_results = [
            {"name": "template1", "version": "1.0", "content": "Content1", "metadata": json.dumps({"key": "value"}), "created_at": "2024-01-01", "updated_at": "2024-01-01"}
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_versions("template1")
        
        assert result[0]["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_list_versions_empty_result(self, dal, mock_db_connection):
        """Test list_versions() with empty result."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.list_versions("template1")
        
        assert result == []

    @pytest.mark.asyncio
    async def test_delete_template_basic(self, dal, mock_db_connection):
        """Test delete_template() with basic parameters."""
        mock_db_connection.execute_query.return_value = 1  # Rows affected
        
        result = await dal.delete_template("template1")
        
        assert result is True
        call_args = mock_db_connection.execute_query.call_args
        assert "DELETE FROM prompt_templates" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_template_with_version(self, dal, mock_db_connection):
        """Test delete_template() with specific version."""
        mock_db_connection.execute_query.return_value = 1
        
        _result = await dal.delete_template("template1", version="1.0")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND version = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_template_with_tenant_id(self, dal, mock_db_connection):
        """Test delete_template() with tenant_id."""
        mock_db_connection.execute_query.return_value = 1
        
        _result = await dal.delete_template("template1", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_template_with_version_and_tenant(self, dal, mock_db_connection):
        """Test delete_template() with version and tenant_id."""
        mock_db_connection.execute_query.return_value = 1
        
        _result = await dal.delete_template("template1", version="1.0", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND version = $" in call_args[0][0]
        assert "AND tenant_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, dal, mock_db_connection):
        """Test delete_template() when template not found."""
        mock_db_connection.execute_query.return_value = 0  # No rows affected
        
        result = await dal.delete_template("nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_template_exists_basic(self, dal, mock_db_connection):
        """Test template_exists() with basic parameters."""
        mock_db_connection.execute_query.return_value = {"1": 1}  # Row exists
        
        result = await dal.template_exists("template1")
        
        assert result is True
        call_args = mock_db_connection.execute_query.call_args
        assert "SELECT 1 FROM prompt_templates" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_template_exists_with_version(self, dal, mock_db_connection):
        """Test template_exists() with version."""
        mock_db_connection.execute_query.return_value = {"1": 1}
        
        _result = await dal.template_exists("template1", version="1.0")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND version = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_template_exists_with_tenant_id(self, dal, mock_db_connection):
        """Test template_exists() with tenant_id."""
        mock_db_connection.execute_query.return_value = {"1": 1}
        
        _result = await dal.template_exists("template1", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_template_exists_with_version_and_tenant(self, dal, mock_db_connection):
        """Test template_exists() with version and tenant_id."""
        mock_db_connection.execute_query.return_value = {"1": 1}
        
        _result = await dal.template_exists("template1", version="1.0", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND version = $" in call_args[0][0]
        assert "AND tenant_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_template_exists_not_found(self, dal, mock_db_connection):
        """Test template_exists() when template does not exist."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.template_exists("nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_list_templates_metadata_as_dict(self, dal, mock_db_connection):
        """Test list_templates() when metadata is already a dict."""
        mock_results = [
            {"name": "template1", "version": "1.0", "content": "Content1", "metadata": {"key": "value"}, "created_at": "2024-01-01", "updated_at": "2024-01-01"}
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_templates()
        
        assert result[0]["metadata"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_list_versions_metadata_as_dict(self, dal, mock_db_connection):
        """Test list_versions() when metadata is already a dict."""
        mock_results = [
            {"name": "template1", "version": "1.0", "content": "Content1", "metadata": {"key": "value"}, "created_at": "2024-01-01", "updated_at": "2024-01-01"}
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_versions("template1")
        
        assert result[0]["metadata"] == {"key": "value"}

