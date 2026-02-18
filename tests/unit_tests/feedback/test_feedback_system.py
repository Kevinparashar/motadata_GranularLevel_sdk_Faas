"""
Unit tests for feedback_system.py
"""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.core.feedback_loop.feedback_system import (
    FeedbackItem,
    FeedbackLoop,
    FeedbackStatus,
    FeedbackType,
)


class TestFeedbackType:
    """Tests for FeedbackType enum."""

    def test_feedback_type_values(self):
        """Test FeedbackType enum values."""
        assert FeedbackType.CORRECTION == "correction"
        assert FeedbackType.RATING == "rating"
        assert FeedbackType.USEFUL == "useful"
        assert FeedbackType.IMPROVEMENT == "improvement"
        assert FeedbackType.ERROR == "error"


class TestFeedbackStatus:
    """Tests for FeedbackStatus enum."""

    def test_feedback_status_values(self):
        """Test FeedbackStatus enum values."""
        assert FeedbackStatus.PENDING == "pending"
        assert FeedbackStatus.PROCESSED == "processed"
        assert FeedbackStatus.APPLIED == "applied"
        assert FeedbackStatus.IGNORED == "ignored"


class TestFeedbackItem:
    """Tests for FeedbackItem dataclass."""

    def test_feedback_item_init_minimal(self):
        """Test FeedbackItem initialization with minimal parameters."""
        item = FeedbackItem(
            feedback_id="test-id",
            query="test query",
            response="test response",
            feedback_type=FeedbackType.CORRECTION,
            content="corrected content",
        )
        assert item.feedback_id == "test-id"
        assert item.query == "test query"
        assert item.response == "test response"
        assert item.feedback_type == FeedbackType.CORRECTION
        assert item.content == "corrected content"
        assert isinstance(item.timestamp, datetime)
        assert item.status == FeedbackStatus.PENDING
        assert item.metadata == {}
        assert item.tenant_id is None
        assert item.agent_id is None
        assert item.tool_id is None

    def test_feedback_item_init_all_params(self):
        """Test FeedbackItem initialization with all parameters."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        metadata = {"key": "value"}
        item = FeedbackItem(
            feedback_id="test-id",
            query="test query",
            response="test response",
            feedback_type=FeedbackType.RATING,
            content="5",
            timestamp=timestamp,
            status=FeedbackStatus.PROCESSED,
            metadata=metadata,
            tenant_id="tenant-1",
            agent_id="agent-1",
            tool_id="tool-1",
        )
        assert item.feedback_id == "test-id"
        assert item.query == "test query"
        assert item.response == "test response"
        assert item.feedback_type == FeedbackType.RATING
        assert item.content == "5"
        assert item.timestamp == timestamp
        assert item.status == FeedbackStatus.PROCESSED
        assert item.metadata == metadata
        assert item.tenant_id == "tenant-1"
        assert item.agent_id == "agent-1"
        assert item.tool_id == "tool-1"


class TestFeedbackLoop:
    """Tests for FeedbackLoop class."""

    def test_init_default(self):
        """Test FeedbackLoop initialization with default parameters."""
        loop = FeedbackLoop()
        assert loop.storage_path is None
        assert loop.auto_process is True
        assert loop.feedback_queue == []
        assert loop.processed_feedback == []
        assert len(loop.callbacks) == 5
        assert FeedbackType.CORRECTION in loop.callbacks
        assert FeedbackType.RATING in loop.callbacks
        assert FeedbackType.USEFUL in loop.callbacks
        assert FeedbackType.IMPROVEMENT in loop.callbacks
        assert FeedbackType.ERROR in loop.callbacks

    def test_init_with_storage_path(self):
        """Test FeedbackLoop initialization with storage path."""
        storage_path = "/tmp/feedback.json"
        loop = FeedbackLoop(storage_path=storage_path)
        assert loop.storage_path == Path(storage_path)
        assert loop.auto_process is True

    def test_init_with_auto_process_false(self):
        """Test FeedbackLoop initialization with auto_process=False."""
        loop = FeedbackLoop(auto_process=False)
        assert loop.auto_process is False

    @pytest.mark.asyncio
    async def test_initialize_no_storage_path(self):
        """Test initialize() when storage_path is None."""
        loop = FeedbackLoop()
        await loop.initialize()
        assert loop.feedback_queue == []
        assert loop.processed_feedback == []

    @pytest.mark.asyncio
    async def test_initialize_storage_path_not_exists(self):
        """Test initialize() when storage_path doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "nonexistent.json"
            loop = FeedbackLoop(storage_path=str(storage_path))
            await loop.initialize()
            assert loop.feedback_queue == []
            assert loop.processed_feedback == []

    @pytest.mark.asyncio
    async def test_initialize_loads_existing_feedback(self):
        """Test initialize() loads existing feedback from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.json"
            # Create existing feedback file
            data = {
                "feedback_queue": [
                    {
                        "feedback_id": "id1",
                        "query": "query1",
                        "response": "response1",
                        "feedback_type": "correction",
                        "content": "content1",
                        "timestamp": "2024-01-01T12:00:00",
                        "status": "pending",
                        "metadata": {},
                        "tenant_id": "tenant-1",
                        "agent_id": "agent-1",
                    }
                ],
                "processed_feedback": [
                    {
                        "feedback_id": "id2",
                        "query": "query2",
                        "response": "response2",
                        "feedback_type": "rating",
                        "content": "5",
                        "timestamp": "2024-01-01T13:00:00",
                        "status": "processed",
                        "metadata": {"key": "value"},
                        "tenant_id": None,
                        "agent_id": None,
                    }
                ],
            }
            storage_path.write_text(json.dumps(data), encoding="utf-8")

            loop = FeedbackLoop(storage_path=str(storage_path))
            await loop.initialize()

            assert len(loop.feedback_queue) == 1
            assert loop.feedback_queue[0].feedback_id == "id1"
            assert len(loop.processed_feedback) == 1
            assert loop.processed_feedback[0].feedback_id == "id2"

    @pytest.mark.asyncio
    async def test_initialize_load_error_handling(self):
        """Test initialize() handles load errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.json"
            # Create invalid JSON file
            storage_path.write_text("invalid json", encoding="utf-8")

            loop = FeedbackLoop(storage_path=str(storage_path))
            await loop.initialize()

            # Should handle error gracefully and have empty queues
            assert loop.feedback_queue == []
            assert loop.processed_feedback == []

    @pytest.mark.asyncio
    async def test_record_feedback_basic(self):
        """Test record_feedback() with basic parameters."""
        loop = FeedbackLoop(auto_process=False)
        feedback_id = await loop.record_feedback(
            query="test query",
            response="test response",
            feedback_type=FeedbackType.CORRECTION,
            content="corrected content",
        )

        assert feedback_id is not None
        assert len(loop.feedback_queue) == 1
        assert loop.feedback_queue[0].query == "test query"
        assert loop.feedback_queue[0].response == "test response"
        assert loop.feedback_queue[0].feedback_type == FeedbackType.CORRECTION
        assert loop.feedback_queue[0].content == "corrected content"

    @pytest.mark.asyncio
    async def test_record_feedback_with_all_params(self):
        """Test record_feedback() with all parameters."""
        loop = FeedbackLoop(auto_process=False)
        metadata = {"key": "value"}
        feedback_id = await loop.record_feedback(
            query="test query",
            response="test response",
            feedback_type=FeedbackType.RATING,
            content="5",
            tenant_id="tenant-1",
            agent_id="agent-1",
            metadata=metadata,
        )

        assert feedback_id is not None
        assert len(loop.feedback_queue) == 1
        assert loop.feedback_queue[0].tenant_id == "tenant-1"
        assert loop.feedback_queue[0].agent_id == "agent-1"
        assert loop.feedback_queue[0].metadata == metadata

    @pytest.mark.asyncio
    async def test_record_feedback_with_auto_process(self):
        """Test record_feedback() with auto_process=True."""
        callback_called = False

        async def mock_callback(feedback: FeedbackItem) -> None:
            nonlocal callback_called
            callback_called = True
            await asyncio.sleep(0)

        loop = FeedbackLoop(auto_process=True)
        loop.register_callback(FeedbackType.CORRECTION, mock_callback)  # type: ignore[arg-type]

        with patch.object(loop, "_persist", new_callable=AsyncMock):
            feedback_id = await loop.record_feedback(
                query="test query",
                response="test response",
                feedback_type=FeedbackType.CORRECTION,
                content="corrected content",
            )

        assert feedback_id is not None
        assert callback_called
        assert len(loop.processed_feedback) == 1
        assert len(loop.feedback_queue) == 0

    @pytest.mark.asyncio
    async def test_record_feedback_persists(self):
        """Test record_feedback() persists to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.json"
            loop = FeedbackLoop(storage_path=str(storage_path), auto_process=False)

            await loop.record_feedback(
                query="test query",
                response="test response",
                feedback_type=FeedbackType.CORRECTION,
                content="corrected content",
            )

            # Wait a bit for async persist to complete
            await asyncio.sleep(0.1)

            assert storage_path.exists()
            data = json.loads(storage_path.read_text(encoding="utf-8"))
            assert len(data["feedback_queue"]) == 1
            assert data["feedback_queue"][0]["query"] == "test query"

    @pytest.mark.asyncio
    async def test_process_feedback_not_found(self):
        """Test process_feedback() when feedback_id not found."""
        loop = FeedbackLoop()
        result = await loop.process_feedback("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_process_feedback_with_sync_callback(self):
        """Test process_feedback() with synchronous callback."""
        callback_called = False
        received_feedback = None

        def sync_callback(feedback: FeedbackItem) -> None:
            nonlocal callback_called, received_feedback
            callback_called = True
            received_feedback = feedback

        loop = FeedbackLoop(auto_process=False)
        loop.register_callback(FeedbackType.CORRECTION, sync_callback)

        feedback_id = await loop.record_feedback(
            query="test query",
            response="test response",
            feedback_type=FeedbackType.CORRECTION,
            content="corrected content",
        )

        with patch.object(loop, "_persist", new_callable=AsyncMock):
            result = await loop.process_feedback(feedback_id)

        assert result is True
        assert callback_called
        assert received_feedback  # Callback should have set this
        assert received_feedback.feedback_id == feedback_id
        assert len(loop.processed_feedback) == 1
        assert loop.processed_feedback[0].status == FeedbackStatus.PROCESSED
        assert len(loop.feedback_queue) == 0

    @pytest.mark.asyncio
    async def test_process_feedback_with_async_callback(self):
        """Test process_feedback() with asynchronous callback."""
        callback_called = False
        received_feedback = None

        async def async_callback(feedback: FeedbackItem) -> None:
            nonlocal callback_called, received_feedback
            callback_called = True
            received_feedback = feedback
            await asyncio.sleep(0)

        loop = FeedbackLoop(auto_process=False)
        loop.register_callback(FeedbackType.RATING, async_callback)  # type: ignore[arg-type]

        feedback_id = await loop.record_feedback(
            query="test query",
            response="test response",
            feedback_type=FeedbackType.RATING,
            content="5",
        )

        with patch.object(loop, "_persist", new_callable=AsyncMock):
            result = await loop.process_feedback(feedback_id)

        assert result is True
        assert callback_called
        assert received_feedback  # Callback should have set this
        assert received_feedback.feedback_id == feedback_id

    @pytest.mark.asyncio
    async def test_process_feedback_with_multiple_callbacks(self):
        """Test process_feedback() with multiple callbacks."""
        callback_count = 0

        def callback1(feedback: FeedbackItem) -> None:
            nonlocal callback_count
            callback_count += 1

        async def callback2(feedback: FeedbackItem) -> None:
            nonlocal callback_count
            callback_count += 1
            await asyncio.sleep(0)

        loop = FeedbackLoop(auto_process=False)
        loop.register_callback(FeedbackType.CORRECTION, callback1)
        loop.register_callback(FeedbackType.CORRECTION, callback2)  # type: ignore[arg-type]

        feedback_id = await loop.record_feedback(
            query="test query",
            response="test response",
            feedback_type=FeedbackType.CORRECTION,
            content="corrected content",
        )

        with patch.object(loop, "_persist", new_callable=AsyncMock):
            result = await loop.process_feedback(feedback_id)

        assert result is True
        assert callback_count == 2

    @pytest.mark.asyncio
    async def test_process_feedback_callback_error_handling(self):
        """Test process_feedback() handles callback errors gracefully."""
        def failing_callback(feedback: FeedbackItem) -> None:
            raise RuntimeError("Callback error")

        loop = FeedbackLoop(auto_process=False)
        loop.register_callback(FeedbackType.CORRECTION, failing_callback)

        feedback_id = await loop.record_feedback(
            query="test query",
            response="test response",
            feedback_type=FeedbackType.CORRECTION,
            content="corrected content",
        )

        with patch.object(loop, "_persist", new_callable=AsyncMock):
            result = await loop.process_feedback(feedback_id)

        # Should still process successfully despite callback error
        assert result is True
        assert len(loop.processed_feedback) == 1

    @pytest.mark.asyncio
    async def test_process_feedback_persists(self):
        """Test process_feedback() persists after processing."""
        loop = FeedbackLoop(auto_process=False)

        feedback_id = await loop.record_feedback(
            query="test query",
            response="test response",
            feedback_type=FeedbackType.CORRECTION,
            content="corrected content",
        )

        persist_called = False

        async def mock_persist() -> None:
            nonlocal persist_called
            persist_called = True
            await asyncio.sleep(0)

        loop._persist = mock_persist
        await loop.process_feedback(feedback_id)

        assert persist_called

    def test_register_callback_new_type(self):
        """Test register_callback() for new feedback type."""
        loop = FeedbackLoop()

        def callback(feedback: FeedbackItem) -> None:
            pass

        # Register callback for a type that doesn't exist in callbacks dict
        # This shouldn't happen in practice, but test the code path
        loop.callbacks.clear()
        loop.register_callback(FeedbackType.CORRECTION, callback)

        assert FeedbackType.CORRECTION in loop.callbacks
        assert len(loop.callbacks[FeedbackType.CORRECTION]) == 1

    def test_register_callback_existing_type(self):
        """Test register_callback() for existing feedback type."""
        loop = FeedbackLoop()

        def callback1(feedback: FeedbackItem) -> None:
            # No-op callback for testing
            pass

        def callback2(feedback: FeedbackItem) -> None:
            # No-op callback for testing
            pass

        loop.register_callback(FeedbackType.CORRECTION, callback1)
        loop.register_callback(FeedbackType.CORRECTION, callback2)

        assert len(loop.callbacks[FeedbackType.CORRECTION]) == 2

    def test_get_feedback_stats_no_feedback(self):
        """Test get_feedback_stats() with no feedback."""
        loop = FeedbackLoop()
        stats = loop.get_feedback_stats()

        assert stats["total"] == 0
        assert stats["pending"] == 0
        assert stats["processed"] == 0
        # by_type should have all feedback types initialized to 0
        assert stats["by_type"]["correction"] == 0
        assert stats["by_type"]["rating"] == 0
        assert stats["by_type"]["useful"] == 0
        assert stats["by_type"]["improvement"] == 0
        assert stats["by_type"]["error"] == 0

    @pytest.mark.asyncio
    async def test_get_feedback_stats_with_feedback(self):
        """Test get_feedback_stats() with various feedback types."""
        loop = FeedbackLoop(auto_process=False)

        await loop.record_feedback(
            query="query1",
            response="response1",
            feedback_type=FeedbackType.CORRECTION,
            content="content1",
        )
        await loop.record_feedback(
            query="query2",
            response="response2",
            feedback_type=FeedbackType.RATING,
            content="5",
        )

        # Process one feedback
        feedback_id = loop.feedback_queue[0].feedback_id
        with patch.object(loop, "_persist", new_callable=AsyncMock):
            await loop.process_feedback(feedback_id)

        stats = loop.get_feedback_stats()

        assert stats["total"] == 2
        assert stats["pending"] == 1
        assert stats["processed"] == 1
        assert stats["by_type"]["correction"] == 1
        assert stats["by_type"]["rating"] == 1

    @pytest.mark.asyncio
    async def test_get_feedback_stats_with_tenant_id(self):
        """Test get_feedback_stats() with tenant filtering."""
        loop = FeedbackLoop(auto_process=False)

        await loop.record_feedback(
            query="query1",
            response="response1",
            feedback_type=FeedbackType.CORRECTION,
            content="content1",
            tenant_id="tenant-1",
        )
        await loop.record_feedback(
            query="query2",
            response="response2",
            feedback_type=FeedbackType.RATING,
            content="5",
            tenant_id="tenant-2",
        )

        stats = loop.get_feedback_stats(tenant_id="tenant-1")

        assert stats["total"] == 1
        assert stats["pending"] == 1
        assert stats["processed"] == 0
        assert stats["by_type"]["correction"] == 1
        assert stats["by_type"]["rating"] == 0

    def test_get_learning_insights_no_feedback(self):
        """Test get_learning_insights() with no feedback."""
        loop = FeedbackLoop()
        insights = loop.get_learning_insights()

        assert insights["total_corrections"] == 0
        assert insights["total_ratings"] == 0
        assert insights["total_errors"] == 0
        assert insights["common_corrections"] == {}
        assert insights["error_patterns"] == []
        assert abs(insights["average_rating"] - 0.0) < 0.001

    @pytest.mark.asyncio
    async def test_get_learning_insights_with_corrections(self):
        """Test get_learning_insights() with corrections."""
        loop = FeedbackLoop(auto_process=False)

        # Add multiple corrections with similar queries
        for i in range(3):
            feedback_id = await loop.record_feedback(
                query=f"similar query pattern {i}",
                response=f"response{i}",
                feedback_type=FeedbackType.CORRECTION,
                content=f"correction{i}",
            )
            with patch.object(loop, "_persist", new_callable=AsyncMock):
                await loop.process_feedback(feedback_id)

        insights = loop.get_learning_insights()

        assert insights["total_corrections"] == 3
        assert len(insights["common_corrections"]) > 0

    @pytest.mark.asyncio
    async def test_get_learning_insights_with_ratings(self):
        """Test get_learning_insights() with ratings."""
        loop = FeedbackLoop(auto_process=False)

        # Add ratings
        for rating in ["4", "5", "3"]:
            feedback_id = await loop.record_feedback(
                query="test query",
                response="test response",
                feedback_type=FeedbackType.RATING,
                content=rating,
            )
            with patch.object(loop, "_persist", new_callable=AsyncMock):
                await loop.process_feedback(feedback_id)

        insights = loop.get_learning_insights()

        assert insights["total_ratings"] == 3
        # Average of 4, 5, 3 is 4.0
        assert abs(insights["average_rating"] - 4.0) < 0.001

    @pytest.mark.asyncio
    async def test_get_learning_insights_with_invalid_ratings(self):
        """Test get_learning_insights() handles invalid rating values."""
        loop = FeedbackLoop(auto_process=False)

        # Add valid and invalid ratings
        for rating in ["5", "invalid", "4"]:
            feedback_id = await loop.record_feedback(
                query="test query",
                response="test response",
                feedback_type=FeedbackType.RATING,
                content=rating,
            )
            with patch.object(loop, "_persist", new_callable=AsyncMock):
                await loop.process_feedback(feedback_id)

        insights = loop.get_learning_insights()

        assert insights["total_ratings"] == 3
        # Only valid ratings (5 and 4) should be counted, average is 4.5
        assert abs(insights["average_rating"] - 4.5) < 0.001

    @pytest.mark.asyncio
    async def test_get_learning_insights_with_errors(self):
        """Test get_learning_insights() with errors."""
        loop = FeedbackLoop(auto_process=False)

        # Add errors with different error types
        for error_type in ["timeout", "timeout", "network"]:
            feedback_id = await loop.record_feedback(
                query="test query",
                response="test response",
                feedback_type=FeedbackType.ERROR,
                content="error message",
                metadata={"error_type": error_type},
            )
            with patch.object(loop, "_persist", new_callable=AsyncMock):
                await loop.process_feedback(feedback_id)

        insights = loop.get_learning_insights()

        assert insights["total_errors"] == 3
        assert len(insights["error_patterns"]) == 2
        # timeout should have count 2, network should have count 1
        error_types = {p["type"]: p["count"] for p in insights["error_patterns"]}
        assert error_types["timeout"] == 2
        assert error_types["network"] == 1

    @pytest.mark.asyncio
    async def test_get_learning_insights_with_tenant_id(self):
        """Test get_learning_insights() with tenant filtering."""
        loop = FeedbackLoop(auto_process=False)

        # Add feedback for different tenants
        feedback_id1 = await loop.record_feedback(
            query="query1",
            response="response1",
            feedback_type=FeedbackType.CORRECTION,
            content="content1",
            tenant_id="tenant-1",
        )
        feedback_id2 = await loop.record_feedback(
            query="query2",
            response="response2",
            feedback_type=FeedbackType.RATING,
            content="5",
            tenant_id="tenant-2",
        )

        with patch.object(loop, "_persist", new_callable=AsyncMock):
            await loop.process_feedback(feedback_id1)
            await loop.process_feedback(feedback_id2)

        insights = loop.get_learning_insights(tenant_id="tenant-1")

        assert insights["total_corrections"] == 1
        assert insights["total_ratings"] == 0

    @pytest.mark.asyncio
    async def test_persist_no_storage_path(self):
        """Test _persist() when storage_path is None."""
        loop = FeedbackLoop()
        # Should not raise error
        await loop._persist()

    @pytest.mark.asyncio
    async def test_persist_success(self):
        """Test _persist() successfully writes to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.json"
            loop = FeedbackLoop(storage_path=str(storage_path), auto_process=False)

            await loop.record_feedback(
                query="test query",
                response="test response",
                feedback_type=FeedbackType.CORRECTION,
                content="corrected content",
            )

            # Process one feedback
            feedback_id = loop.feedback_queue[0].feedback_id
            await loop.process_feedback(feedback_id)

            # Wait for persist to complete
            await asyncio.sleep(0.1)

            assert storage_path.exists()
            data = json.loads(storage_path.read_text(encoding="utf-8"))
            assert "feedback_queue" in data
            assert "processed_feedback" in data
            assert len(data["processed_feedback"]) == 1

    @pytest.mark.asyncio
    async def test_persist_error_handling(self):
        """Test _persist() handles errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.json"
            loop = FeedbackLoop(storage_path=str(storage_path), auto_process=False)

            await loop.record_feedback(
                query="test query",
                response="test response",
                feedback_type=FeedbackType.CORRECTION,
                content="corrected content",
            )

            # Make storage_path parent read-only to cause error
            storage_path.parent.chmod(0o444)

            try:
                # Should not raise error, just log warning
                await loop._persist()
            finally:
                # Restore permissions
                storage_path.parent.chmod(0o755)

    @pytest.mark.asyncio
    async def test_load_no_storage_path(self):
        """Test _load() when storage_path is None."""
        loop = FeedbackLoop()
        await loop._load()
        assert loop.feedback_queue == []
        assert loop.processed_feedback == []

    @pytest.mark.asyncio
    async def test_load_file_not_exists(self):
        """Test _load() when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "nonexistent.json"
            loop = FeedbackLoop(storage_path=str(storage_path))
            await loop._load()
            assert loop.feedback_queue == []
            assert loop.processed_feedback == []

    @pytest.mark.asyncio
    async def test_load_success(self):
        """Test _load() successfully loads from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.json"
            data = {
                "feedback_queue": [
                    {
                        "feedback_id": "id1",
                        "query": "query1",
                        "response": "response1",
                        "feedback_type": "correction",
                        "content": "content1",
                        "timestamp": "2024-01-01T12:00:00",
                        "status": "pending",
                        "metadata": {"key": "value"},
                        "tenant_id": "tenant-1",
                        "agent_id": "agent-1",
                    }
                ],
                "processed_feedback": [
                    {
                        "feedback_id": "id2",
                        "query": "query2",
                        "response": "response2",
                        "feedback_type": "rating",
                        "content": "5",
                        "timestamp": "2024-01-01T13:00:00",
                        "status": "processed",
                        "metadata": {},
                        "tenant_id": None,
                        "agent_id": None,
                    }
                ],
            }
            storage_path.write_text(json.dumps(data), encoding="utf-8")

            loop = FeedbackLoop(storage_path=str(storage_path))
            await loop._load()

            assert len(loop.feedback_queue) == 1
            assert loop.feedback_queue[0].feedback_id == "id1"
            assert loop.feedback_queue[0].metadata == {"key": "value"}
            assert len(loop.processed_feedback) == 1
            assert loop.processed_feedback[0].feedback_id == "id2"

    @pytest.mark.asyncio
    async def test_load_error_handling_invalid_json(self):
        """Test _load() handles invalid JSON gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.json"
            storage_path.write_text("invalid json", encoding="utf-8")

            loop = FeedbackLoop(storage_path=str(storage_path))
            await loop._load()

            # Should handle error gracefully
            assert loop.feedback_queue == []
            assert loop.processed_feedback == []

    @pytest.mark.asyncio
    async def test_load_error_handling_missing_key(self):
        """Test _load() handles missing keys gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.json"
            # Missing required keys
            data = {
                "feedback_queue": [
                    {
                        "feedback_id": "id1",
                        # Missing query, response, etc.
                    }
                ],
            }
            storage_path.write_text(json.dumps(data), encoding="utf-8")

            loop = FeedbackLoop(storage_path=str(storage_path))
            await loop._load()

            # Should handle error gracefully
            assert loop.feedback_queue == []
            assert loop.processed_feedback == []

    @pytest.mark.asyncio
    async def test_load_error_handling_io_error(self):
        """Test _load() handles IO errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.json"
            storage_path.write_text('{"feedback_queue": []}', encoding="utf-8")

            loop = FeedbackLoop(storage_path=str(storage_path))

            # Make file unreadable
            storage_path.chmod(0o000)

            try:
                await loop._load()
                # Should handle error gracefully
                assert loop.feedback_queue == []
                assert loop.processed_feedback == []
            finally:
                # Restore permissions
                storage_path.chmod(0o644)

