"""
Unit Tests for Model DAL

Tests database operations for ML model persistence.
Follows @cursorrules.md: Success ≥2, Edge ≥2, Failure ≥2
"""


import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.faas.shared.dal.model_dal import ModelDAL


class TestModelDAL:
    """Test ModelDAL class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def model_dal(self, mock_db):
        """Create a ModelDAL instance."""
        return ModelDAL(mock_db)

    # Success Cases (≥2)
    @pytest.mark.asyncio
    async def test_register_model_success(self, model_dal, mock_db):
        """Test successfully registering a model."""
        mock_db.execute_query.return_value = {"id": "model_record_123"}

        result = await model_dal.register_model(
            model_id="model_123",
            model_type="classification",
            model_path="/path/to/model",
            version="1.0.0",
            tenant_id="tenant_456",
            metadata={"accuracy": 0.95},
        )

        assert result == "model_record_123"
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO ml_models" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_model_success(self, model_dal, mock_db):
        """Test successfully getting a model."""
        mock_db.execute_query.return_value = {
            "id": "model_record_123",
            "model_id": "model_123",
            "model_type": "classification",
            "model_path": "/path/to/model",
            "version": "1.0.0",
            "metadata": json.dumps({"accuracy": 0.95}),
            "created_at": datetime.now(timezone.utc),
        }

        result = await model_dal.get_model("model_123", "1.0.0", "tenant_456")

        assert result is not None
        assert result["model_id"] == "model_123"
        assert isinstance(result["metadata"], dict)

    @pytest.mark.asyncio
    async def test_list_models_success(self, model_dal, mock_db):
        """Test successfully listing models."""
        mock_db.execute_query.return_value = [
            {"model_id": "model_1", "model_type": "classification"},
            {"model_id": "model_2", "model_type": "regression"},
        ]

        result = await model_dal.list_models("tenant_456", limit=10, offset=0)

        assert len(result) == 2
        assert result[0]["model_id"] == "model_1"

    @pytest.mark.asyncio
    async def test_delete_model_success(self, model_dal, mock_db):
        """Test successfully deleting a model."""
        mock_db.execute_query.return_value = 1  # 1 row deleted

        result = await model_dal.delete_model("model_123", "1.0.0", "tenant_456")

        assert result is True
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_archive_model_success(self, model_dal, mock_db):
        """Test successfully archiving a model."""
        mock_db.execute_query.return_value = 1  # 1 row updated

        result = await model_dal.archive_model("model_123", "1.0.0", "tenant_456")

        assert result is True
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_model_exists_success(self, model_dal, mock_db):
        """Test successfully checking model existence."""
        mock_db.execute_query.return_value = {"1": 1}

        result = await model_dal.model_exists("model_123", "1.0.0", "tenant_456")

        assert result is True

    # Edge Cases (≥2)
    @pytest.mark.asyncio
    async def test_get_model_without_version(self, model_dal, mock_db):
        """Test getting model without version."""
        mock_db.execute_query.return_value = {
            "model_id": "model_123",
            "version": "1.0.0",
            "metadata": json.dumps({}),
        }

        result = await model_dal.get_model("model_123", None, "tenant_456")

        assert result is not None
        call_args = mock_db.execute_query.call_args
        assert "version" not in call_args[0][0] or "ORDER BY" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_models_with_type_filter(self, model_dal, mock_db):
        """Test listing models with type filter."""
        mock_db.execute_query.return_value = [{"model_id": "model_1"}]

        result = await model_dal.list_models(
            "tenant_456", model_type="classification", limit=10, offset=0
        )

        assert len(result) == 1
        call_args = mock_db.execute_query.call_args
        assert "model_type" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_models_empty_result(self, model_dal, mock_db):
        """Test listing models with empty result."""
        mock_db.execute_query.return_value = None

        result = await model_dal.list_models("tenant_456")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_model_with_string_metadata(self, model_dal, mock_db):
        """Test getting model with string JSON metadata."""
        mock_db.execute_query.return_value = {
            "model_id": "model_123",
            "metadata": '{"key": "value"}',  # String JSON
        }

        result = await model_dal.get_model("model_123", None, "tenant_456")

        assert result is not None
        assert isinstance(result["metadata"], dict)

    @pytest.mark.asyncio
    async def test_delete_model_without_version(self, model_dal, mock_db):
        """Test deleting model without version."""
        mock_db.execute_query.return_value = 1

        result = await model_dal.delete_model("model_123", None, "tenant_456")

        assert result is True
        call_args = mock_db.execute_query.call_args
        assert "version" not in call_args[0][0] or "$" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_model_exists_not_found(self, model_dal, mock_db):
        """Test checking existence of non-existent model."""
        mock_db.execute_query.return_value = None

        result = await model_dal.model_exists("nonexistent", None, "tenant_456")

        assert result is False

    # Failure Cases (≥2)
    @pytest.mark.asyncio
    async def test_get_model_not_found(self, model_dal, mock_db):
        """Test getting non-existent model."""
        mock_db.execute_query.return_value = None

        result = await model_dal.get_model("nonexistent", None, "tenant_456")

        assert result is None

    @pytest.mark.asyncio
    async def test_register_model_database_error(self, model_dal, mock_db):
        """Test registering model with database error."""
        mock_db.execute_query.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await model_dal.register_model(
                model_id="model_123",
                model_type="classification",
                model_path="/path/to/model",
                version="1.0.0",
                tenant_id="tenant_456",
            )

