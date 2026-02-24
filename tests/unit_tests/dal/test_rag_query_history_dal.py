"""
Unit Tests for RAG Query History DAL

Tests for RAG query history persistence operations.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.faas.shared.dal.rag_query_history_dal import RAGQueryHistoryDAL
from src.core.postgresql_database import DatabaseConnection


class TestRAGQueryHistoryDAL:
    """Tests for RAGQueryHistoryDAL."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        db = MagicMock(spec=DatabaseConnection)
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def query_history_dal(self, mock_db):
        """RAGQueryHistoryDAL fixture."""
        return RAGQueryHistoryDAL(mock_db)

    @pytest.mark.asyncio
    async def test_save_query_success(self, query_history_dal, mock_db):
        """Test successful query save."""
        mock_db.execute_query.return_value = {"query_id": "test_query_123"}

        result = await query_history_dal.save_query(
            query="What is AI?",
            answer="AI is artificial intelligence",
            tenant_id="tenant-1",
            user_id="user-1",
            conversation_id="conv-1",
        )

        assert result == "test_query_123"
        mock_db.execute_query.assert_called_once()
        call_args = mock_db.execute_query.call_args
        assert "INSERT INTO rag_query_history" in call_args[0][0]
        assert call_args[1]["params"][1] == "What is AI?"
        assert call_args[1]["params"][2] == "AI is artificial intelligence"
        assert call_args[1]["params"][3] == "tenant-1"

    @pytest.mark.asyncio
    async def test_save_query_with_all_fields(self, query_history_dal, mock_db):
        """Test save query with all optional fields."""
        mock_db.execute_query.return_value = {"query_id": "test_query_456"}

        retrieved_docs = [{"id": 1, "content": "Doc 1"}, {"id": 2, "content": "Doc 2"}]
        metadata = {"top_k": 5, "threshold": 0.7}

        result = await query_history_dal.save_query(
            query="What is ML?",
            answer="ML is machine learning",
            tenant_id="tenant-1",
            user_id="user-1",
            conversation_id="conv-1",
            original_query="What is machine learning?",
            query_used="What is ML?",
            retrieved_documents=retrieved_docs,
            num_documents=2,
            memory_used=3,
            retrieval_strategy="vector",
            metadata=metadata,
        )

        assert result == "test_query_456"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        assert params[1] == "What is ML?"
        assert params[2] == "ML is machine learning"
        assert params[6] == "What is machine learning?"
        assert params[7] == "What is ML?"
        assert params[9] == 2  # num_documents (index 9, not 10)
        assert params[10] == 3  # memory_used (index 10, not 11)
        assert params[11] == "vector"  # retrieval_strategy (index 11, not 12)
        # Check JSON serialization
        assert json.loads(params[8]) == retrieved_docs
        assert json.loads(params[12]) == metadata  # metadata (index 12, not 13)

    @pytest.mark.asyncio
    async def test_get_query_history_basic(self, query_history_dal, mock_db):
        """Test get query history with basic filters."""
        mock_db.execute_query.return_value = [
            {
                "query_id": "q1",
                "query": "What is AI?",
                "answer": "AI is...",
                "tenant_id": "tenant-1",
                "created_at": datetime.now(),
            }
        ]

        results = await query_history_dal.get_query_history(
            tenant_id="tenant-1",
            limit=10,
            offset=0,
        )

        assert len(results) == 1
        assert results[0]["query"] == "What is AI?"
        mock_db.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_query_history_with_filters(self, query_history_dal, mock_db):
        """Test get query history with all filters."""
        mock_db.execute_query.return_value = []

        results = await query_history_dal.get_query_history(
            tenant_id="tenant-1",
            user_id="user-1",
            conversation_id="conv-1",
            limit=50,
            offset=10,
        )

        assert results == []
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_id" in query
        assert "user_id" in query
        assert "conversation_id" in query
        assert "LIMIT" in query
        assert "OFFSET" in query

    @pytest.mark.asyncio
    async def test_get_query_history_with_json_parsing(self, query_history_dal, mock_db):
        """Test get query history with JSON field parsing."""
        mock_db.execute_query.return_value = [
            {
                "query_id": "q1",
                "query": "Test",
                "answer": "Answer",
                "retrieved_documents": json.dumps([{"id": 1}]),
                "metadata": json.dumps({"key": "value"}),
            }
        ]

        results = await query_history_dal.get_query_history(tenant_id="tenant-1")

        assert len(results) == 1
        assert isinstance(results[0]["retrieved_documents"], list)
        assert isinstance(results[0]["metadata"], dict)

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, query_history_dal, mock_db):
        """Test get conversation history."""
        mock_db.execute_query.return_value = [
            {
                "query_id": "q1",
                "query": "Q1",
                "answer": "A1",
                "conversation_id": "conv-1",
            },
            {
                "query_id": "q2",
                "query": "Q2",
                "answer": "A2",
                "conversation_id": "conv-1",
            },
        ]

        results = await query_history_dal.get_conversation_history(
            conversation_id="conv-1",
            tenant_id="tenant-1",
            limit=50,
        )

        assert len(results) == 2
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "conversation_id = $1" in query
        assert "ORDER BY created_at ASC" in query

    @pytest.mark.asyncio
    async def test_get_conversation_history_without_tenant(self, query_history_dal, mock_db):
        """Test get conversation history without tenant filter."""
        mock_db.execute_query.return_value = []

        results = await query_history_dal.get_conversation_history(
            conversation_id="conv-1",
            limit=20,
        )

        assert results == []
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        # Check that tenant_id is not in WHERE clause (it's in SELECT, which is fine)
        assert "WHERE conversation_id = $1" in query
        assert "AND tenant_id" not in query

    @pytest.mark.asyncio
    async def test_delete_query_history_success(self, query_history_dal, mock_db):
        """Test successful query history deletion."""
        mock_db.execute_query.return_value = 1

        result = await query_history_dal.delete_query_history(
            query_id="q1",
            tenant_id="tenant-1",
        )

        assert result is True
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "DELETE FROM rag_query_history" in query
        assert "query_id = $1" in query
        assert "tenant_id = $2" in query

    @pytest.mark.asyncio
    async def test_delete_query_history_not_found(self, query_history_dal, mock_db):
        """Test delete query history when not found."""
        mock_db.execute_query.return_value = 0

        result = await query_history_dal.delete_query_history(
            query_id="q1",
            tenant_id="tenant-1",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_query_history_without_tenant(self, query_history_dal, mock_db):
        """Test delete query history without tenant filter."""
        mock_db.execute_query.return_value = 1

        result = await query_history_dal.delete_query_history(query_id="q1")

        assert result is True
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_id" not in query

    @pytest.mark.asyncio
    async def test_delete_conversation_history(self, query_history_dal, mock_db):
        """Test delete conversation history."""
        mock_db.execute_query.return_value = 5

        result = await query_history_dal.delete_conversation_history(
            conversation_id="conv-1",
            tenant_id="tenant-1",
        )

        assert result == 5
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "DELETE FROM rag_query_history" in query
        assert "conversation_id = $1" in query

    @pytest.mark.asyncio
    async def test_delete_conversation_history_without_tenant(self, query_history_dal, mock_db):
        """Test delete conversation history without tenant."""
        mock_db.execute_query.return_value = 3

        result = await query_history_dal.delete_conversation_history(
            conversation_id="conv-1"
        )

        assert result == 3

    @pytest.mark.asyncio
    async def test_cleanup_old_history(self, query_history_dal, mock_db):
        """Test cleanup old history."""
        mock_db.execute_query.return_value = 10

        result = await query_history_dal.cleanup_old_history(
            days=90,
            tenant_id="tenant-1",
        )

        assert result == 10
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "DELETE FROM rag_query_history" in query
        assert "INTERVAL" in query

    @pytest.mark.asyncio
    async def test_cleanup_old_history_without_tenant(self, query_history_dal, mock_db):
        """Test cleanup old history without tenant."""
        mock_db.execute_query.return_value = 20

        result = await query_history_dal.cleanup_old_history(days=30)

        assert result == 20

    @pytest.mark.asyncio
    async def test_get_query_stats_basic(self, query_history_dal, mock_db):
        """Test get query stats."""
        mock_db.execute_query.return_value = {
            "total_queries": 100,
            "total_conversations": 10,
            "total_users": 5,
            "avg_documents": 3.5,
            "avg_memory_used": 2.0,
        }

        stats = await query_history_dal.get_query_stats(tenant_id="tenant-1")

        assert stats["total_queries"] == 100
        assert stats["total_conversations"] == 10
        assert stats["total_users"] == 5
        assert stats["avg_documents"] == 3.5
        assert stats["avg_memory_used"] == 2.0

    @pytest.mark.asyncio
    async def test_get_query_stats_with_filters(self, query_history_dal, mock_db):
        """Test get query stats with all filters."""
        mock_db.execute_query.return_value = {
            "total_queries": 50,
            "total_conversations": 5,
            "total_users": 2,
            "avg_documents": 2.0,
            "avg_memory_used": 1.5,
        }

        stats = await query_history_dal.get_query_stats(
            tenant_id="tenant-1",
            user_id="user-1",
            conversation_id="conv-1",
        )

        assert stats["total_queries"] == 50
        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        assert "tenant_id" in query
        assert "user_id" in query
        assert "conversation_id" in query

    @pytest.mark.asyncio
    async def test_get_query_stats_empty(self, query_history_dal, mock_db):
        """Test get query stats when no data."""
        mock_db.execute_query.return_value = None

        stats = await query_history_dal.get_query_stats()

        assert stats["total_queries"] == 0
        assert stats["total_conversations"] == 0
        assert stats["total_users"] == 0
        assert stats["avg_documents"] == 0.0
        assert stats["avg_memory_used"] == 0.0

    @pytest.mark.asyncio
    async def test_get_query_history_empty_result(self, query_history_dal, mock_db):
        """Test get query history with empty result."""
        mock_db.execute_query.return_value = None

        results = await query_history_dal.get_query_history()

        assert results == []

    @pytest.mark.asyncio
    async def test_get_conversation_history_empty(self, query_history_dal, mock_db):
        """Test get conversation history with empty result."""
        mock_db.execute_query.return_value = None

        results = await query_history_dal.get_conversation_history(
            conversation_id="conv-1"
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_save_query_with_none_values(self, query_history_dal, mock_db):
        """Test save query with None optional values."""
        mock_db.execute_query.return_value = {"query_id": "test_123"}

        result = await query_history_dal.save_query(
            query="Test",
            answer="Answer",
        )

        assert result == "test_123"
        call_args = mock_db.execute_query.call_args
        params = call_args[1]["params"]
        # Check that None values are handled
        assert params[3] is None  # tenant_id
        assert params[4] is None  # user_id
        assert params[5] is None  # conversation_id

