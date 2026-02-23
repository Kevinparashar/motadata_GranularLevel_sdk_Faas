"""
Unit Tests for Model Version DAL

Tests database operations for ML model version persistence.
Follows @cursorrules.md: Success ≥2, Edge ≥2, Failure ≥2
"""


import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.faas.shared.dal.model_version_dal import ModelVersionDAL


class TestModelVersionDAL:
    """Test ModelVersionDAL class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def model_version_dal(self, mock_db):
        """Create a ModelVersionDAL instance."""
        return ModelVersionDAL(mock_db)

    # Success Cases (≥2)
    @pytest.mark.asyncio
    async def test_register_version_success(self, model_version_dal, mock_db):
        """Test successfully registering a model version."""
        mock_db.execute_query.return_value = {"id": "version_record_123"}

        result = await model_version_dal.register_version(
            model_id="model_123",
            version="1.0.0",
            model_path="/path/to/model",
            tenant_id="tenant_456",
            metrics={"accuracy": 0.95},
            hyperparameters={"lr": 0.01},
            metadata={"extra": "data"},
        )

        assert result == "version_record_123"
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO ml_model_versions" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_version_success(self, model_version_dal, mock_db):
        """Test successfully getting a model version."""
        mock_db.execute_query.return_value = {
            "id": "version_record_123",
            "model_id": "model_123",
            "version": "1.0.0",
            "metrics": json.dumps({"accuracy": 0.95}),
            "hyperparameters": json.dumps({"lr": 0.01}),
            "metadata": json.dumps({"extra": "data"}),
        }

        result = await model_version_dal.get_version("model_123", "1.0.0", "tenant_456")

        assert result is not None
        assert result["model_id"] == "model_123"
        assert isinstance(result["metrics"], dict)
        assert isinstance(result["hyperparameters"], dict)

    @pytest.mark.asyncio
    async def test_list_versions_success(self, model_version_dal, mock_db):
        """Test successfully listing versions."""
        mock_db.execute_query.return_value = [
            {"version": "1.0.0", "model_id": "model_123"},
            {"version": "1.1.0", "model_id": "model_123"},
        ]

        result = await model_version_dal.list_versions("model_123", "tenant_456", limit=10, offset=0)

        assert len(result) == 2
        assert result[0]["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_delete_version_success(self, model_version_dal, mock_db):
        """Test successfully deleting a version."""
        mock_db.execute_query.return_value = 1  # 1 row deleted

        result = await model_version_dal.delete_version("model_123", "1.0.0", "tenant_456")

        assert result is True
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_compare_versions_success(self, model_version_dal, mock_db):
        """Test successfully comparing versions."""
        # Mock get_version calls
        mock_db.execute_query.side_effect = [
            {
                "version": "1.0.0",
                "metrics": json.dumps({"accuracy": 0.90}),
                "hyperparameters": json.dumps({"lr": 0.01}),
            },
            {
                "version": "1.1.0",
                "metrics": json.dumps({"accuracy": 0.95}),
                "hyperparameters": json.dumps({"lr": 0.02}),
            },
        ]

        result = await model_version_dal.compare_versions(
            "model_123", "1.0.0", "1.1.0", "tenant_456"
        )

        assert "metrics" in result or "hyperparameters" in result

    # Edge Cases (≥2)
    @pytest.mark.asyncio
    async def test_list_versions_with_environment_filter(self, model_version_dal, mock_db):
        """Test listing versions with environment filter."""
        mock_db.execute_query.return_value = [{"version": "1.0.0"}]

        result = await model_version_dal.list_versions(
            "model_123", "tenant_456", environment="prod", limit=10, offset=0
        )

        assert len(result) == 1
        call_args = mock_db.execute_query.call_args
        assert "environment" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_version_with_string_json(self, model_version_dal, mock_db):
        """Test getting version with string JSON fields."""
        mock_db.execute_query.return_value = {
            "version": "1.0.0",
            "metrics": '{"accuracy": 0.95}',  # String JSON
            "hyperparameters": '{"lr": 0.01}',  # String JSON
            "metadata": '{"extra": "data"}',  # String JSON
        }

        result = await model_version_dal.get_version("model_123", "1.0.0", "tenant_456")

        assert result is not None
        assert isinstance(result["metrics"], dict)
        assert isinstance(result["hyperparameters"], dict)

    @pytest.mark.asyncio
    async def test_list_versions_empty_result(self, model_version_dal, mock_db):
        """Test listing versions with empty result."""
        mock_db.execute_query.return_value = None

        result = await model_version_dal.list_versions("model_123", "tenant_456")

        assert result == []

    @pytest.mark.asyncio
    async def test_compare_versions_one_missing(self, model_version_dal, mock_db):
        """Test comparing versions when one is missing."""
        mock_db.execute_query.side_effect = [
            {"version": "1.0.0", "metrics": json.dumps({})},  # v1 exists
            None,  # v2 doesn't exist
        ]

        result = await model_version_dal.compare_versions(
            "model_123", "1.0.0", "1.1.0", "tenant_456"
        )

        assert "error" in result

    @pytest.mark.asyncio
    async def test_delete_version_not_found(self, model_version_dal, mock_db):
        """Test deleting non-existent version."""
        mock_db.execute_query.return_value = 0  # 0 rows deleted

        result = await model_version_dal.delete_version("model_123", "nonexistent", "tenant_456")

        assert result is False

    # Failure Cases (≥2)
    @pytest.mark.asyncio
    async def test_get_version_not_found(self, model_version_dal, mock_db):
        """Test getting non-existent version."""
        mock_db.execute_query.return_value = None

        result = await model_version_dal.get_version("model_123", "nonexistent", "tenant_456")

        assert result is None

    @pytest.mark.asyncio
    async def test_register_version_database_error(self, model_version_dal, mock_db):
        """Test registering version with database error."""
        mock_db.execute_query.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await model_version_dal.register_version(
                model_id="model_123",
                version="1.0.0",
                model_path="/path/to/model",
                tenant_id="tenant_456",
            )

