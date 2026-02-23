"""
Unit tests for llmops.py
"""

import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from src.core.llmops.llmops import (
    LLMOps,
    LLMOperation,
    LLMOperationStatus,
    LLMOperationType,
)


class TestLLMOperationType:
    """Tests for LLMOperationType enum."""

    def test_operation_type_values(self):
        """Test LLMOperationType enum values."""
        assert LLMOperationType.COMPLETION == "completion"
        assert LLMOperationType.EMBEDDING == "embedding"
        assert LLMOperationType.CHAT == "chat"
        assert LLMOperationType.FUNCTION_CALLING == "function_calling"
        assert LLMOperationType.STREAMING == "streaming"


class TestLLMOperationStatus:
    """Tests for LLMOperationStatus enum."""

    def test_operation_status_values(self):
        """Test LLMOperationStatus enum values."""
        assert LLMOperationStatus.SUCCESS == "success"
        assert LLMOperationStatus.ERROR == "error"
        assert LLMOperationStatus.TIMEOUT == "timeout"
        assert LLMOperationStatus.RATE_LIMITED == "rate_limited"
        assert LLMOperationStatus.CANCELLED == "cancelled"


class TestLLMOperation:
    """Tests for LLMOperation dataclass."""

    def test_llm_operation_init_minimal(self):
        """Test LLMOperation initialization with minimal parameters."""
        operation = LLMOperation(
            operation_id="test-id",
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
        )
        assert operation.operation_id == "test-id"
        assert operation.operation_type == LLMOperationType.COMPLETION
        assert operation.model == "gpt-4"
        assert operation.tenant_id is None
        assert operation.agent_id is None
        assert operation.prompt_tokens == 0
        assert operation.completion_tokens == 0
        assert operation.total_tokens == 0
        assert abs(operation.latency_ms - 0.0) < 0.001
        assert abs(operation.cost_usd - 0.0) < 0.001
        assert operation.status == LLMOperationStatus.SUCCESS
        assert operation.error_message is None
        assert isinstance(operation.timestamp, datetime)
        assert operation.metadata == {}

    def test_llm_operation_init_all_params(self):
        """Test LLMOperation initialization with all parameters."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        metadata = {"key": "value"}
        operation = LLMOperation(
            operation_id="test-id",
            operation_type=LLMOperationType.CHAT,
            model="gpt-3.5-turbo",
            tenant_id="tenant-1",
            agent_id="agent-1",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=250.5,
            cost_usd=0.001,
            status=LLMOperationStatus.ERROR,
            error_message="Test error",
            timestamp=timestamp,
            metadata=metadata,
        )
        assert operation.operation_id == "test-id"
        assert operation.operation_type == LLMOperationType.CHAT
        assert operation.model == "gpt-3.5-turbo"
        assert operation.tenant_id == "tenant-1"
        assert operation.agent_id == "agent-1"
        assert operation.prompt_tokens == 100
        assert operation.completion_tokens == 50
        assert operation.total_tokens == 150
        assert abs(operation.latency_ms - 250.5) < 0.001
        assert abs(operation.cost_usd - 0.001) < 0.001
        assert operation.status == LLMOperationStatus.ERROR
        assert operation.error_message == "Test error"
        assert operation.timestamp == timestamp
        assert operation.metadata == metadata


class TestLLMOps:
    """Tests for LLMOps class."""

    def test_init_default(self):
        """Test LLMOps initialization with default parameters."""
        llmops = LLMOps()
        assert llmops.storage_path is None
        assert llmops.enable_logging is True
        assert llmops.enable_cost_tracking is True
        assert llmops.operations == []
        assert llmops.max_operations_in_memory == 10000
        assert len(llmops.model_costs) > 0
        assert "gpt-4" in llmops.model_costs

    def test_init_with_storage_path(self):
        """Test LLMOps initialization with storage path."""
        storage_path = "/tmp/llmops.json"
        llmops = LLMOps(storage_path=storage_path)
        assert llmops.storage_path == Path(storage_path)
        assert llmops.enable_logging is True
        assert llmops.enable_cost_tracking is True

    def test_init_with_logging_disabled(self):
        """Test LLMOps initialization with logging disabled."""
        llmops = LLMOps(enable_logging=False)
        assert llmops.enable_logging is False

    def test_init_with_cost_tracking_disabled(self):
        """Test LLMOps initialization with cost tracking disabled."""
        llmops = LLMOps(enable_cost_tracking=False)
        assert llmops.enable_cost_tracking is False

    @pytest.mark.asyncio
    async def test_initialize_no_storage_path(self):
        """Test initialize() when storage_path is None."""
        llmops = LLMOps()
        await llmops.initialize()
        assert llmops.operations == []

    @pytest.mark.asyncio
    async def test_initialize_storage_path_not_exists(self):
        """Test initialize() when storage_path doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "nonexistent.json"
            llmops = LLMOps(storage_path=str(storage_path))
            await llmops.initialize()
            assert llmops.operations == []

    @pytest.mark.asyncio
    async def test_initialize_loads_existing_operations(self):
        """Test initialize() loads existing operations from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "llmops.json"
            # Create existing operations file
            data = {
                "operations": [
                    {
                        "operation_id": "id1",
                        "operation_type": "completion",
                        "model": "gpt-4",
                        "tenant_id": "tenant-1",
                        "agent_id": "agent-1",
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "total_tokens": 150,
                        "latency_ms": 250.5,
                        "cost_usd": 0.001,
                        "status": "success",
                        "error_message": None,
                        "timestamp": "2024-01-01T12:00:00",
                        "metadata": {"key": "value"},
                    }
                ]
            }
            storage_path.write_text(json.dumps(data), encoding="utf-8")

            llmops = LLMOps(storage_path=str(storage_path))
            await llmops.initialize()

            assert len(llmops.operations) == 1
            assert llmops.operations[0].operation_id == "id1"
            assert llmops.operations[0].model == "gpt-4"

    @pytest.mark.asyncio
    async def test_initialize_load_error_handling(self):
        """Test initialize() handles load errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "llmops.json"
            # Create invalid JSON file
            storage_path.write_text("invalid json", encoding="utf-8")

            llmops = LLMOps(storage_path=str(storage_path))
            await llmops.initialize()

            # Should handle error gracefully and have empty operations
            assert llmops.operations == []

    @pytest.mark.asyncio
    async def test_log_operation_basic(self):
        """Test log_operation() with basic parameters."""
        llmops = LLMOps(enable_logging=True)
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
        )

        assert operation_id is not None
        assert len(llmops.operations) == 1
        assert llmops.operations[0].operation_type == LLMOperationType.COMPLETION
        assert llmops.operations[0].model == "gpt-4"
        assert llmops.operations[0].prompt_tokens == 100
        assert llmops.operations[0].completion_tokens == 50
        assert llmops.operations[0].total_tokens == 150

    @pytest.mark.asyncio
    async def test_log_operation_with_all_params(self):
        """Test log_operation() with all parameters."""
        llmops = LLMOps(enable_logging=True)
        metadata = {"key": "value"}
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.CHAT,
            model="gpt-3.5-turbo",
            prompt_tokens=200,
            completion_tokens=100,
            latency_ms=500.0,
            status=LLMOperationStatus.ERROR,
            error_message="Test error",
            tenant_id="tenant-1",
            agent_id="agent-1",
            metadata=metadata,
        )

        assert operation_id is not None
        assert len(llmops.operations) == 1
        assert llmops.operations[0].tenant_id == "tenant-1"
        assert llmops.operations[0].agent_id == "agent-1"
        assert llmops.operations[0].status == LLMOperationStatus.ERROR
        assert llmops.operations[0].error_message == "Test error"
        assert llmops.operations[0].metadata == metadata

    @pytest.mark.asyncio
    async def test_log_operation_logging_disabled(self):
        """Test log_operation() when logging is disabled."""
        llmops = LLMOps(enable_logging=False)
        operation_id = await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
        )

        assert operation_id == ""
        assert len(llmops.operations) == 0

    @pytest.mark.asyncio
    async def test_log_operation_cost_calculation(self):
        """Test log_operation() calculates cost correctly."""
        llmops = LLMOps(enable_logging=True, enable_cost_tracking=True)
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=1_000_000,  # 1M tokens
            completion_tokens=500_000,  # 0.5M tokens
        )

        operation = llmops.operations[0]
        # gpt-4: prompt $30/1M, completion $60/1M
        # Expected: (1 * 30) + (0.5 * 60) = 30 + 30 = 60
        assert abs(operation.cost_usd - 60.0) < 0.01

    @pytest.mark.asyncio
    async def test_log_operation_cost_tracking_disabled(self):
        """Test log_operation() when cost tracking is disabled."""
        llmops = LLMOps(enable_logging=True, enable_cost_tracking=False)
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        assert abs(llmops.operations[0].cost_usd - 0.0) < 0.001

    @pytest.mark.asyncio
    async def test_log_operation_model_with_slash(self):
        """Test log_operation() handles model names with slashes."""
        llmops = LLMOps(enable_logging=True, enable_cost_tracking=True)
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="openai/gpt-4",
            prompt_tokens=1_000_000,
            completion_tokens=0,
        )

        operation = llmops.operations[0]
        # Should extract "gpt-4" from "openai/gpt-4"
        assert abs(operation.cost_usd - 30.0) < 0.01

    @pytest.mark.asyncio
    async def test_log_operation_unknown_model(self):
        """Test log_operation() handles unknown model names."""
        llmops = LLMOps(enable_logging=True, enable_cost_tracking=True)
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="unknown-model",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        assert abs(llmops.operations[0].cost_usd - 0.0) < 0.001

    @pytest.mark.asyncio
    async def test_log_operation_trims_when_exceeds_max(self):
        """Test log_operation() trims operations when exceeding max."""
        llmops = LLMOps(enable_logging=True)
        llmops.max_operations_in_memory = 5

        # Add 7 operations
        for _ in range(7):
            await llmops.log_operation(
                operation_type=LLMOperationType.COMPLETION,
                model="gpt-4",
            )

        # Should only keep last 5
        assert len(llmops.operations) == 5

    @pytest.mark.asyncio
    async def test_log_operation_persists(self):
        """Test log_operation() persists to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "llmops.json"
            llmops = LLMOps(storage_path=str(storage_path), enable_logging=True)

            await llmops.log_operation(
                operation_type=LLMOperationType.COMPLETION,
                model="gpt-4",
            )

            # Wait a bit for async persist to complete
            await asyncio.sleep(0.1)

            assert storage_path.exists()
            data = json.loads(storage_path.read_text(encoding="utf-8"))
            assert len(data["operations"]) == 1
            assert data["operations"][0]["model"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_get_metrics_no_operations(self):
        """Test get_metrics() with no operations."""
        llmops = LLMOps()
        metrics = await llmops.get_metrics()

        assert metrics["total_operations"] == 0
        assert metrics["total_tokens"] == 0
        assert abs(metrics["total_cost_usd"] - 0.0) < 0.001
        assert abs(metrics["average_latency_ms"] - 0.0) < 0.001
        assert abs(metrics["success_rate"] - 0.0) < 0.001
        assert abs(metrics["error_rate"] - 0.0) < 0.001
        assert metrics["by_model"] == {}
        assert metrics["by_type"] == {}

    @pytest.mark.asyncio
    async def test_get_metrics_with_operations(self):
        """Test get_metrics() with various operations."""
        llmops = LLMOps(enable_logging=True)

        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=250.0,
            status=LLMOperationStatus.SUCCESS,
        )
        await llmops.log_operation(
            operation_type=LLMOperationType.CHAT,
            model="gpt-3.5-turbo",
            prompt_tokens=200,
            completion_tokens=100,
            latency_ms=150.0,
            status=LLMOperationStatus.ERROR,
        )

        metrics = await llmops.get_metrics()

        assert metrics["total_operations"] == 2
        assert metrics["total_tokens"] == 450  # 150 + 300
        assert abs(metrics["average_latency_ms"] - 200.0) < 0.001  # (250 + 150) / 2
        assert abs(metrics["success_rate"] - 0.5) < 0.001  # 1 success / 2 total
        assert abs(metrics["error_rate"] - 0.5) < 0.001  # 1 error / 2 total
        assert "gpt-4" in metrics["by_model"]
        assert "gpt-3.5-turbo" in metrics["by_model"]
        assert metrics["by_type"]["completion"] == {"count": 1, "tokens": 150}
        assert metrics["by_type"]["chat"] == {"count": 1, "tokens": 300}

    @pytest.mark.asyncio
    async def test_get_metrics_with_tenant_filter(self):
        """Test get_metrics() with tenant filtering."""
        llmops = LLMOps(enable_logging=True)

        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            tenant_id="tenant-1",
        )
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            tenant_id="tenant-2",
        )

        metrics = await llmops.get_metrics(tenant_id="tenant-1")

        assert metrics["total_operations"] == 1
        assert metrics["by_model"]["gpt-4"]["count"] == 1

    @pytest.mark.asyncio
    async def test_get_metrics_with_agent_filter(self):
        """Test get_metrics() with agent filtering."""
        llmops = LLMOps(enable_logging=True)

        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            agent_id="agent-1",
        )
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            agent_id="agent-2",
        )

        metrics = await llmops.get_metrics(agent_id="agent-1")

        assert metrics["total_operations"] == 1

    @pytest.mark.asyncio
    async def test_get_metrics_with_time_range(self):
        """Test get_metrics() with time range filtering."""
        llmops = LLMOps(enable_logging=True)

        # Add an old operation (outside 24 hour window)
        old_operation = LLMOperation(
            operation_id="old-id",
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            timestamp=datetime.now() - timedelta(hours=25),
        )
        llmops.operations.append(old_operation)

        # Add a recent operation
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
        )

        metrics = await llmops.get_metrics(time_range_hours=24)

        # Should only include the recent operation
        assert metrics["total_operations"] == 1

    @pytest.mark.asyncio
    async def test_get_metrics_with_time_range_none(self):
        """Test get_metrics() with time_range_hours=None."""
        llmops = LLMOps(enable_logging=True)

        # Add a recent operation
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
        )

        # When time_range_hours is None, cutoff is set to datetime.now()
        # So only operations with timestamp >= now() are included
        # Since all operations have timestamps in the past, this effectively returns no operations
        metrics = await llmops.get_metrics(time_range_hours=None)

        # Should return empty metrics (no operations match timestamp >= now())
        assert metrics["total_operations"] == 0

    @pytest.mark.asyncio
    async def test_get_metrics_by_model_averages(self):
        """Test get_metrics() calculates average latency by model."""
        llmops = LLMOps(enable_logging=True)

        # Add multiple operations for same model
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            latency_ms=100.0,
        )
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            latency_ms=200.0,
        )

        metrics = await llmops.get_metrics()

        # Average should be (100 + 200) / 2 = 150
        assert abs(metrics["by_model"]["gpt-4"]["avg_latency_ms"] - 150.0) < 0.001

    @pytest.mark.asyncio
    async def test_get_cost_summary_basic(self):
        """Test get_cost_summary() with basic operations."""
        llmops = LLMOps(enable_logging=True, enable_cost_tracking=True)

        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=1_000_000,
            completion_tokens=500_000,
        )

        summary = await llmops.get_cost_summary()

        assert summary["total_cost_usd"] > 0
        assert summary["total_tokens"] == 1_500_000
        assert summary["cost_per_1k_tokens"] > 0
        assert "gpt-4" in summary["by_model"]

    @pytest.mark.asyncio
    async def test_get_cost_summary_with_tenant_filter(self):
        """Test get_cost_summary() with tenant filtering."""
        llmops = LLMOps(enable_logging=True, enable_cost_tracking=True)

        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=1000,
            tenant_id="tenant-1",
        )
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=2000,
            tenant_id="tenant-2",
        )

        summary = await llmops.get_cost_summary(tenant_id="tenant-1")

        assert summary["total_tokens"] == 1000

    @pytest.mark.asyncio
    async def test_get_cost_summary_with_time_range(self):
        """Test get_cost_summary() with time range filtering."""
        llmops = LLMOps(enable_logging=True, enable_cost_tracking=True)

        # Add old operation
        old_operation = LLMOperation(
            operation_id="old-id",
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=1000,
            timestamp=datetime.now() - timedelta(hours=25),
        )
        llmops.operations.append(old_operation)

        # Add recent operation
        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=2000,
        )

        summary = await llmops.get_cost_summary(time_range_hours=24)

        assert summary["total_tokens"] == 2000

    @pytest.mark.asyncio
    async def test_get_cost_summary_zero_tokens(self):
        """Test get_cost_summary() handles zero tokens correctly."""
        llmops = LLMOps(enable_logging=True)
        summary = await llmops.get_cost_summary()

        assert abs(summary["total_cost_usd"] - 0.0) < 0.001
        assert summary["total_tokens"] == 0
        assert abs(summary["cost_per_1k_tokens"] - 0.0) < 0.001
        assert summary["by_model"] == {}

    @pytest.mark.asyncio
    async def test_get_cost_summary_by_model_calculation(self):
        """Test get_cost_summary() calculates cost per 1k tokens by model."""
        llmops = LLMOps(enable_logging=True, enable_cost_tracking=True)

        await llmops.log_operation(
            operation_type=LLMOperationType.COMPLETION,
            model="gpt-4",
            prompt_tokens=2000,
            completion_tokens=1000,
        )

        summary = await llmops.get_cost_summary()

        gpt4_data = summary["by_model"]["gpt-4"]
        assert gpt4_data["tokens"] == 3000
        assert gpt4_data["cost_usd"] > 0
        assert gpt4_data["cost_per_1k_tokens"] > 0

    @pytest.mark.asyncio
    async def test_persist_no_storage_path(self):
        """Test _persist() when storage_path is None."""
        llmops = LLMOps()
        # Should not raise error
        await llmops._persist()

    @pytest.mark.asyncio
    async def test_persist_success(self):
        """Test _persist() successfully writes to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "llmops.json"
            llmops = LLMOps(storage_path=str(storage_path), enable_logging=True)

            await llmops.log_operation(
                operation_type=LLMOperationType.COMPLETION,
                model="gpt-4",
            )

            # Wait for persist to complete
            await asyncio.sleep(0.1)

            assert storage_path.exists()
            data = json.loads(storage_path.read_text(encoding="utf-8"))
            assert "operations" in data
            assert len(data["operations"]) == 1

    @pytest.mark.asyncio
    async def test_persist_only_recent_operations(self):
        """Test _persist() only persists recent operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "llmops.json"
            llmops = LLMOps(storage_path=str(storage_path), enable_logging=True)

            # Add more than 1000 operations directly to avoid 1500 persist calls
            # We'll add them directly and then call persist once
            for i in range(1500):
                operation = LLMOperation(
                    operation_id=f"id-{i}",
                    operation_type=LLMOperationType.COMPLETION,
                    model="gpt-4",
                )
                llmops.operations.append(operation)

            # Now persist once
            await llmops._persist()

            # Wait for persist to complete
            await asyncio.sleep(0.1)

            data = json.loads(storage_path.read_text(encoding="utf-8"))
            # Should only persist last 1000
            assert len(data["operations"]) == 1000

    @pytest.mark.asyncio
    async def test_persist_error_handling(self):
        """Test _persist() handles errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "llmops.json"
            llmops = LLMOps(storage_path=str(storage_path), enable_logging=True)

            await llmops.log_operation(
                operation_type=LLMOperationType.COMPLETION,
                model="gpt-4",
            )

            # Make storage_path parent read-only to cause error
            storage_path.parent.chmod(0o444)

            try:
                # Should not raise error, just fail silently
                await llmops._persist()
            finally:
                # Restore permissions
                storage_path.parent.chmod(0o755)

    @pytest.mark.asyncio
    async def test_load_no_storage_path(self):
        """Test _load() when storage_path is None."""
        llmops = LLMOps()
        await llmops._load()
        assert llmops.operations == []

    @pytest.mark.asyncio
    async def test_load_file_not_exists(self):
        """Test _load() when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "nonexistent.json"
            llmops = LLMOps(storage_path=str(storage_path))
            await llmops._load()
            assert llmops.operations == []

    @pytest.mark.asyncio
    async def test_load_success(self):
        """Test _load() successfully loads from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "llmops.json"
            data = {
                "operations": [
                    {
                        "operation_id": "id1",
                        "operation_type": "completion",
                        "model": "gpt-4",
                        "tenant_id": "tenant-1",
                        "agent_id": "agent-1",
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "total_tokens": 150,
                        "latency_ms": 250.5,
                        "cost_usd": 0.001,
                        "status": "success",
                        "error_message": None,
                        "timestamp": "2024-01-01T12:00:00",
                        "metadata": {"key": "value"},
                    }
                ]
            }
            storage_path.write_text(json.dumps(data), encoding="utf-8")

            llmops = LLMOps(storage_path=str(storage_path))
            await llmops._load()

            assert len(llmops.operations) == 1
            assert llmops.operations[0].operation_id == "id1"
            assert llmops.operations[0].metadata == {"key": "value"}

    @pytest.mark.asyncio
    async def test_load_error_handling_invalid_json(self):
        """Test _load() handles invalid JSON gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "llmops.json"
            storage_path.write_text("invalid json", encoding="utf-8")

            llmops = LLMOps(storage_path=str(storage_path))
            await llmops._load()

            # Should handle error gracefully
            assert llmops.operations == []

    @pytest.mark.asyncio
    async def test_load_error_handling_missing_key(self):
        """Test _load() handles missing keys gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "llmops.json"
            # Missing required keys
            data = {
                "operations": [
                    {
                        "operation_id": "id1",
                        # Missing operation_type, model, etc.
                    }
                ]
            }
            storage_path.write_text(json.dumps(data), encoding="utf-8")

            llmops = LLMOps(storage_path=str(storage_path))
            await llmops._load()

            # Should handle error gracefully
            assert llmops.operations == []

    @pytest.mark.asyncio
    async def test_load_error_handling_io_error(self):
        """Test _load() handles IO errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "llmops.json"
            storage_path.write_text('{"operations": []}', encoding="utf-8")

            llmops = LLMOps(storage_path=str(storage_path))

            # Make file unreadable
            storage_path.chmod(0o000)

            try:
                await llmops._load()
                # Should handle error gracefully
                assert llmops.operations == []
            finally:
                # Restore permissions
                storage_path.chmod(0o644)

