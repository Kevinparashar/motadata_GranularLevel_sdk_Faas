"""
Unit Tests for Memory DAL

Tests database operations for agent memory persistence.
"""


import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.agno_agent_framework.memory import MemoryItem, MemoryType
from src.faas.shared.dal.memory_dal import MemoryDAL


class TestMemoryDAL:
    """Test MemoryDAL class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def memory_dal(self, mock_db):
        """Create a MemoryDAL instance."""
        return MemoryDAL(mock_db)

    @pytest.fixture
    def sample_memory(self):
        """Create a sample MemoryItem."""
        return MemoryItem(
            memory_id="mem_123",
            agent_id="agent1",
            memory_type=MemoryType.SHORT_TERM,
            content="Test memory content",
            importance=0.8,
            timestamp=datetime.now(),
            access_count=5,
            last_accessed=datetime.now(),
            metadata={"key": "value"},
            tags=["tag1", "tag2"],
        )

    @pytest.mark.asyncio
    async def test_save_memory(self, memory_dal, mock_db, sample_memory):
        """Test saving a memory item to database."""
        await memory_dal.save_memory(sample_memory, "tenant_123")

        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO agent_memory" in call_args[0][0]
        assert call_args[1]["params"][0] == "mem_123"
        assert call_args[1]["params"][1] == "agent1"
        assert call_args[1]["params"][2] == "tenant_123"
        assert call_args[1]["params"][3] == "short_term"

    @pytest.mark.asyncio
    async def test_save_memory_with_json(self, memory_dal, mock_db, sample_memory):
        """Test saving memory with JSON metadata and tags."""
        sample_memory.metadata = {"nested": {"key": "value"}, "list": [1, 2, 3]}
        sample_memory.tags = ["tag1", "tag2", "tag3"]

        await memory_dal.save_memory(sample_memory, "tenant_123")

        call_args = mock_db.execute_query.call_args
        metadata_param = call_args[1]["params"][9]  # metadata is 10th param (index 9)
        tags_param = call_args[1]["params"][10]  # tags is 11th param (index 10)

        assert isinstance(metadata_param, str)
        assert isinstance(tags_param, str)
        parsed_metadata = json.loads(metadata_param)
        assert parsed_metadata["nested"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_load_memories(self, memory_dal, mock_db):
        """Test loading memories from database."""
        rows = [
            {
                "memory_id": "mem_1",
                "agent_id": "agent1",
                "memory_type": "short_term",
                "content": "Content 1",
                "importance": 0.8,
                "timestamp": datetime.now(),
                "access_count": 1,
                "last_accessed": datetime.now(),
                "metadata": json.dumps({"key": "value"}),
                "tags": json.dumps(["tag1"]),
            },
            {
                "memory_id": "mem_2",
                "agent_id": "agent1",
                "memory_type": "long_term",
                "content": "Content 2",
                "importance": 0.9,
                "timestamp": datetime.now(),
                "access_count": 2,
                "last_accessed": datetime.now(),
                "metadata": json.dumps({}),
                "tags": json.dumps([]),
            },
        ]

        mock_db.execute_query.return_value = rows

        memories = await memory_dal.load_memories("agent1", "tenant_123")

        assert len(memories) == 2
        assert memories[0].memory_id == "mem_1"
        assert memories[0].memory_type == MemoryType.SHORT_TERM
        assert memories[1].memory_id == "mem_2"
        assert memories[1].memory_type == MemoryType.LONG_TERM

    @pytest.mark.asyncio
    async def test_load_memories_with_type_filter(self, memory_dal, mock_db):
        """Test loading memories filtered by type."""
        rows = [
            {
                "memory_id": "mem_1",
                "agent_id": "agent1",
                "memory_type": "short_term",
                "content": "Content 1",
                "importance": 0.8,
                "timestamp": datetime.now(),
                "access_count": 1,
                "last_accessed": datetime.now(),
                "metadata": json.dumps({}),
                "tags": json.dumps([]),
            },
        ]

        mock_db.execute_query.return_value = rows

        memories = await memory_dal.load_memories(
            "agent1", "tenant_123", memory_type=MemoryType.SHORT_TERM
        )

        assert len(memories) == 1
        call_args = mock_db.execute_query.call_args
        assert "memory_type = $3" in call_args[0][0]
        assert call_args[1]["params"][2] == "short_term"

    @pytest.mark.asyncio
    async def test_load_memories_empty(self, memory_dal, mock_db):
        """Test loading memories when none exist."""
        mock_db.execute_query.return_value = []

        memories = await memory_dal.load_memories("agent1", "tenant_123")

        assert len(memories) == 0

    @pytest.mark.asyncio
    async def test_load_memories_with_dict_metadata(self, memory_dal, mock_db):
        """Test loading memories when metadata is already a dict."""
        rows = [
            {
                "memory_id": "mem_1",
                "agent_id": "agent1",
                "memory_type": "short_term",
                "content": "Content 1",
                "importance": 0.8,
                "timestamp": datetime.now(),
                "access_count": 1,
                "last_accessed": datetime.now(),
                "metadata": {"key": "value"},  # Already a dict
                "tags": ["tag1"],  # Already a list
            },
        ]

        mock_db.execute_query.return_value = rows

        memories = await memory_dal.load_memories("agent1", "tenant_123")

        assert len(memories) == 1
        assert isinstance(memories[0].metadata, dict)
        assert memories[0].metadata["key"] == "value"

    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_dal, mock_db):
        """Test deleting a memory item."""
        mock_db.execute_query.return_value = 1  # 1 row deleted

        result = await memory_dal.delete_memory("mem_123", "agent1", "tenant_123")

        assert result is True
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "DELETE FROM agent_memory" in call_args[0][0]
        assert call_args[1]["params"][0] == "mem_123"

    @pytest.mark.asyncio
    async def test_delete_memory_not_found(self, memory_dal, mock_db):
        """Test deleting non-existent memory."""
        mock_db.execute_query.return_value = 0  # 0 rows deleted

        result = await memory_dal.delete_memory("nonexistent", "agent1", "tenant_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_all_agent_memories(self, memory_dal, mock_db):
        """Test deleting all memories for an agent."""
        mock_db.execute_query.return_value = 5  # 5 memories deleted

        count = await memory_dal.delete_all_agent_memories("agent1", "tenant_123")

        assert count == 5
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "DELETE FROM agent_memory" in call_args[0][0]
        assert call_args[1]["params"][0] == "agent1"

    @pytest.mark.asyncio
    async def test_get_memory_count(self, memory_dal, mock_db):
        """Test getting memory count."""
        mock_db.execute_query.return_value = {"count": 10}

        count = await memory_dal.get_memory_count("agent1", "tenant_123")

        assert count == 10
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "SELECT COUNT(*)" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_memory_count_with_type(self, memory_dal, mock_db):
        """Test getting memory count filtered by type."""
        mock_db.execute_query.return_value = {"count": 5}

        count = await memory_dal.get_memory_count(
            "agent1", "tenant_123", memory_type=MemoryType.SHORT_TERM
        )

        assert count == 5
        call_args = mock_db.execute_query.call_args
        assert "memory_type = $3" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_memory_count_empty(self, memory_dal, mock_db):
        """Test getting memory count when none exist."""
        mock_db.execute_query.return_value = None

        count = await memory_dal.get_memory_count("agent1", "tenant_123")

        assert count == 0

    @pytest.mark.asyncio
    async def test_update_memory_access_default(self, memory_dal, mock_db):
        """Test updating memory access with default increment."""
        mock_db.execute_query.return_value = 1  # 1 row updated

        result = await memory_dal.update_memory_access(
            "mem_123", "agent1", "tenant_123"
        )

        assert result is True
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "UPDATE agent_memory" in call_args[0][0]
        assert "access_count = access_count + 1" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_memory_access_with_values(self, memory_dal, mock_db):
        """Test updating memory access with specific values."""
        mock_db.execute_query.return_value = 1
        last_accessed = datetime.now()

        result = await memory_dal.update_memory_access(
            "mem_123",
            "agent1",
            "tenant_123",
            access_count=10,
            last_accessed=last_accessed,
        )

        assert result is True
        call_args = mock_db.execute_query.call_args
        assert "UPDATE agent_memory" in call_args[0][0]
        assert call_args[1]["params"][0] == 10
        assert call_args[1]["params"][1] == last_accessed

    @pytest.mark.asyncio
    async def test_update_memory_access_only_count(self, memory_dal, mock_db):
        """Test updating memory access with only access_count."""
        mock_db.execute_query.return_value = 1

        result = await memory_dal.update_memory_access(
            "mem_123", "agent1", "tenant_123", access_count=5
        )

        assert result is True
        call_args = mock_db.execute_query.call_args
        assert "access_count = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_memory_access_only_timestamp(self, memory_dal, mock_db):
        """Test updating memory access with only last_accessed."""
        mock_db.execute_query.return_value = 1
        last_accessed = datetime.now()

        result = await memory_dal.update_memory_access(
            "mem_123", "agent1", "tenant_123", last_accessed=last_accessed
        )

        assert result is True
        call_args = mock_db.execute_query.call_args
        assert "last_accessed = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_memory_access_not_found(self, memory_dal, mock_db):
        """Test updating access for non-existent memory."""
        mock_db.execute_query.return_value = 0  # 0 rows updated

        result = await memory_dal.update_memory_access(
            "nonexistent", "agent1", "tenant_123"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_update_memory_access_no_params(self, memory_dal, mock_db):
        """Test updating access with no parameters (should use defaults)."""
        mock_db.execute_query.return_value = 1

        result = await memory_dal.update_memory_access(
            "mem_123", "agent1", "tenant_123", access_count=None, last_accessed=None
        )

        assert result is True
        call_args = mock_db.execute_query.call_args
        assert "access_count = access_count + 1" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_search_memories(self, memory_dal, mock_db):
        """Test searching memories with text query."""
        rows = [
            {
                "memory_id": "mem_1",
                "agent_id": "agent1",
                "memory_type": "short_term",
                "content": "Test content",
                "importance": 0.8,
                "timestamp": datetime.now(),
                "access_count": 1,
                "last_accessed": datetime.now(),
                "metadata": json.dumps({}),
                "tags": json.dumps([]),
            },
        ]

        mock_db.execute_query.return_value = rows

        memories = await memory_dal.search_memories(
            "agent1", "tenant_123", query="test", limit=10, offset=0
        )

        assert len(memories) == 1
        call_args = mock_db.execute_query.call_args
        assert "content ILIKE" in call_args[0][0]
        assert "%test%" in call_args[1]["params"]

    @pytest.mark.asyncio
    async def test_search_memories_with_type_filter(self, memory_dal, mock_db):
        """Test searching memories with type filter."""
        rows = []

        mock_db.execute_query.return_value = rows

        memories = await memory_dal.search_memories(
            "agent1",
            "tenant_123",
            query="test",
            memory_type=MemoryType.SHORT_TERM,
            limit=10,
        )

        assert len(memories) == 0
        call_args = mock_db.execute_query.call_args
        assert "memory_type = $" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_search_memories_without_query(self, memory_dal, mock_db):
        """Test searching memories without text query."""
        rows = []

        mock_db.execute_query.return_value = rows

        memories = await memory_dal.search_memories(
            "agent1", "tenant_123", limit=10, offset=0
        )

        assert len(memories) == 0
        call_args = mock_db.execute_query.call_args
        assert "content ILIKE" not in call_args[0][0]

    @pytest.mark.asyncio
    async def test_search_memories_with_pagination(self, memory_dal, mock_db):
        """Test searching memories with pagination."""
        rows = []

        mock_db.execute_query.return_value = rows

        await memory_dal.search_memories(
            "agent1", "tenant_123", limit=5, offset=10
        )

        call_args = mock_db.execute_query.call_args
        assert "LIMIT $" in call_args[0][0]
        assert "OFFSET $" in call_args[0][0]
        # Verify limit and offset are in params
        params = call_args[1]["params"]
        assert 5 in params
        assert 10 in params

