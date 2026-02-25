"""
Comprehensive tests for WorkflowDAL.

Tests all methods and edge cases to achieve >85% coverage.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.faas.shared.dal.workflow_dal import WorkflowDAL


class TestWorkflowDAL:
    """Test WorkflowDAL class."""

    @pytest.fixture
    def mock_db_connection(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def dal(self, mock_db_connection):
        """Create WorkflowDAL instance."""
        return WorkflowDAL(mock_db_connection)

    @pytest.mark.asyncio
    async def test_init(self, mock_db_connection):
        """Test WorkflowDAL initialization."""
        dal = WorkflowDAL(mock_db_connection)
        assert dal.db == mock_db_connection

    @pytest.mark.asyncio
    async def test_save_workflow_state_basic(self, dal, mock_db_connection):
        """Test save_workflow_state() with basic parameters."""
        await dal.save_workflow_state(
            workflow_id="workflow-1",
            status="running"
        )
        
        mock_db_connection.execute_query.assert_called_once()
        call_args = mock_db_connection.execute_query.call_args
        assert "INSERT INTO workflows" in call_args[0][0]
        assert call_args[1]["params"][0] == "workflow-1"
        assert call_args[1]["params"][1] == "running"

    @pytest.mark.asyncio
    async def test_save_workflow_state_with_all_params(self, dal, mock_db_connection):
        """Test save_workflow_state() with all parameters."""
        started_at = datetime(2024, 1, 1, 12, 0, 0)
        completed_at = datetime(2024, 1, 1, 12, 30, 0)
        
        await dal.save_workflow_state(
            workflow_id="workflow-1",
            status="completed",
            current_step="step-3",
            completed_steps=["step-1", "step-2"],
            failed_steps=[],
            step_results={"step-1": "result1", "step-2": "result2"},
            context={"var1": "value1"},
            error=None,
            tenant_id="tenant-1",
            started_at=started_at,
            completed_at=completed_at
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][2] == "step-3"
        assert call_args[1]["params"][3] == json.dumps(["step-1", "step-2"])
        assert call_args[1]["params"][4] == json.dumps([])
        assert call_args[1]["params"][5] == json.dumps({"step-1": "result1", "step-2": "result2"})
        assert call_args[1]["params"][6] == json.dumps({"var1": "value1"})
        assert call_args[1]["params"][8] == "tenant-1"
        assert call_args[1]["params"][9] == started_at
        assert call_args[1]["params"][10] == completed_at

    @pytest.mark.asyncio
    async def test_save_workflow_state_with_none_lists(self, dal, mock_db_connection):
        """Test save_workflow_state() with None lists."""
        await dal.save_workflow_state(
            workflow_id="workflow-1",
            status="pending",
            completed_steps=None,
            failed_steps=None,
            step_results=None,
            context=None
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert call_args[1]["params"][3] == json.dumps([])
        assert call_args[1]["params"][4] == json.dumps([])
        assert call_args[1]["params"][5] == json.dumps({})
        assert call_args[1]["params"][6] == json.dumps({})

    @pytest.mark.asyncio
    async def test_save_workflow_state_on_conflict_update(self, dal, mock_db_connection):
        """Test save_workflow_state() updates on conflict."""
        await dal.save_workflow_state(
            workflow_id="workflow-1",
            status="completed"
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert "ON CONFLICT" in call_args[0][0]
        assert "DO UPDATE SET" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_load_workflow_state_basic(self, dal, mock_db_connection):
        """Test load_workflow_state() with basic parameters."""
        mock_result = {
            "workflow_id": "workflow-1",
            "status": "running",
            "current_step": "step-2",
            "completed_steps": json.dumps(["step-1"]),
            "failed_steps": json.dumps([]),
            "step_results": json.dumps({"step-1": "result1"}),
            "context": json.dumps({"var1": "value1"}),
            "error": None,
            "started_at": datetime(2024, 1, 1, 12, 0, 0),
            "completed_at": None,
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime(2024, 1, 1, 12, 0, 0)
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.load_workflow_state("workflow-1")
        
        assert result is not None
        assert result["workflow_id"] == "workflow-1"
        assert result["status"] == "running"
        assert result["completed_steps"] == ["step-1"]
        assert result["failed_steps"] == []
        assert result["step_results"] == {"step-1": "result1"}
        assert result["context"] == {"var1": "value1"}

    @pytest.mark.asyncio
    async def test_load_workflow_state_with_tenant_id(self, dal, mock_db_connection):
        """Test load_workflow_state() with tenant_id."""
        mock_result = {
            "workflow_id": "workflow-1",
            "status": "running",
            "current_step": None,
            "completed_steps": json.dumps([]),
            "failed_steps": json.dumps([]),
            "step_results": json.dumps({}),
            "context": json.dumps({}),
            "error": None,
            "started_at": None,
            "completed_at": None,
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime(2024, 1, 1, 12, 0, 0)
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        _result = await dal.load_workflow_state("workflow-1", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $2" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_load_workflow_state_not_found(self, dal, mock_db_connection):
        """Test load_workflow_state() when workflow not found."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.load_workflow_state("nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_load_workflow_state_json_fields_as_dicts(self, dal, mock_db_connection):
        """Test load_workflow_state() when JSON fields are already dicts."""
        mock_result = {
            "workflow_id": "workflow-1",
            "status": "running",
            "current_step": None,
            "completed_steps": ["step-1"],  # Already a list
            "failed_steps": [],  # Already a list
            "step_results": {"step-1": "result1"},  # Already a dict
            "context": {"var1": "value1"},  # Already a dict
            "error": None,
            "started_at": None,
            "completed_at": None,
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
            "updated_at": datetime(2024, 1, 1, 12, 0, 0)
        }
        mock_db_connection.execute_query.return_value = mock_result
        
        result = await dal.load_workflow_state("workflow-1")
        
        assert result["completed_steps"] == ["step-1"]
        assert result["failed_steps"] == []
        assert result["step_results"] == {"step-1": "result1"}
        assert result["context"] == {"var1": "value1"}

    @pytest.mark.asyncio
    async def test_list_workflows_basic(self, dal, mock_db_connection):
        """Test list_workflows() with basic parameters."""
        mock_results = [
            {
                "workflow_id": "workflow-1",
                "status": "running",
                "current_step": "step-2",
                "error": None,
                "started_at": datetime(2024, 1, 1, 12, 0, 0),
                "completed_at": None,
                "created_at": datetime(2024, 1, 1, 12, 0, 0),
                "updated_at": datetime(2024, 1, 1, 12, 0, 0)
            }
        ]
        mock_db_connection.execute_query.return_value = mock_results
        
        result = await dal.list_workflows()
        
        assert len(result) == 1
        assert result[0]["workflow_id"] == "workflow-1"

    @pytest.mark.asyncio
    async def test_list_workflows_with_tenant_id(self, dal, mock_db_connection):
        """Test list_workflows() with tenant_id."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_workflows(tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_workflows_with_status(self, dal, mock_db_connection):
        """Test list_workflows() with status filter."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_workflows(status="completed")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND status = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_workflows_with_limit_offset(self, dal, mock_db_connection):
        """Test list_workflows() with limit and offset."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_workflows(limit=50, offset=10)
        
        call_args = mock_db_connection.execute_query.call_args
        assert "LIMIT $" in call_args[0][0]
        assert "OFFSET $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_workflows_with_all_filters(self, dal, mock_db_connection):
        """Test list_workflows() with all filters."""
        mock_results = []
        mock_db_connection.execute_query.return_value = mock_results
        
        _result = await dal.list_workflows(
            tenant_id="tenant-1",
            status="running",
            limit=20,
            offset=5
        )
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $" in call_args[0][0]
        assert "AND status = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_workflows_empty_result(self, dal, mock_db_connection):
        """Test list_workflows() with empty result."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.list_workflows()
        
        assert result == []

    @pytest.mark.asyncio
    async def test_delete_workflow_basic(self, dal, mock_db_connection):
        """Test delete_workflow() with basic parameters."""
        mock_db_connection.execute_query.return_value = 1  # Rows affected
        
        result = await dal.delete_workflow("workflow-1")
        
        assert result is True
        call_args = mock_db_connection.execute_query.call_args
        assert "DELETE FROM workflows" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_workflow_with_tenant_id(self, dal, mock_db_connection):
        """Test delete_workflow() with tenant_id."""
        mock_db_connection.execute_query.return_value = 1
        
        _result = await dal.delete_workflow("workflow-1", tenant_id="tenant-1")
        
        call_args = mock_db_connection.execute_query.call_args
        assert "AND tenant_id = $2" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_workflow_not_found(self, dal, mock_db_connection):
        """Test delete_workflow() when workflow not found."""
        mock_db_connection.execute_query.return_value = 0  # No rows affected
        
        result = await dal.delete_workflow("nonexistent")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_old_workflows_basic(self, dal, mock_db_connection):
        """Test cleanup_old_workflows() with basic parameters."""
        mock_db_connection.execute_query.return_value = 5  # Rows deleted
        
        result = await dal.cleanup_old_workflows(days=90)
        
        assert result == 5
        call_args = mock_db_connection.execute_query.call_args
        assert "DELETE FROM workflows" in call_args[0][0]
        assert "INTERVAL '90 days'" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_cleanup_old_workflows_with_tenant_id(self, dal, mock_db_connection):
        """Test cleanup_old_workflows() with tenant_id."""
        mock_db_connection.execute_query.return_value = 3
        
        result = await dal.cleanup_old_workflows(days=90, tenant_id="tenant-1")
        
        assert result == 3
        call_args = mock_db_connection.execute_query.call_args
        assert "WHERE tenant_id = $1 AND" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_cleanup_old_workflows_with_status(self, dal, mock_db_connection):
        """Test cleanup_old_workflows() with status filter."""
        mock_db_connection.execute_query.return_value = 2
        
        result = await dal.cleanup_old_workflows(days=90, status="completed")
        
        assert result == 2
        call_args = mock_db_connection.execute_query.call_args
        assert "AND status = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_cleanup_old_workflows_with_tenant_and_status(self, dal, mock_db_connection):
        """Test cleanup_old_workflows() with tenant_id and status."""
        mock_db_connection.execute_query.return_value = 1
        
        result = await dal.cleanup_old_workflows(
            days=90,
            tenant_id="tenant-1",
            status="completed"
        )
        
        assert result == 1
        call_args = mock_db_connection.execute_query.call_args
        assert "WHERE tenant_id = $1 AND" in call_args[0][0]
        assert "AND status = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_cleanup_old_workflows_no_rows_deleted(self, dal, mock_db_connection):
        """Test cleanup_old_workflows() when no rows deleted."""
        mock_db_connection.execute_query.return_value = None
        
        result = await dal.cleanup_old_workflows(days=90)
        
        assert result == 0

    @pytest.mark.asyncio
    async def test_cleanup_old_workflows_custom_days(self, dal, mock_db_connection):
        """Test cleanup_old_workflows() with custom days."""
        mock_db_connection.execute_query.return_value = 10
        
        _result = await dal.cleanup_old_workflows(days=60)
        
        call_args = mock_db_connection.execute_query.call_args
        assert "INTERVAL '60 days'" in call_args[0][0]

