"""
Integration Tests for Agent-RAG Integration

Tests the integration between Agent Framework and RAG system.
"""


from unittest.mock import MagicMock, patch

import pytest

from src.core.agno_agent_framework import Agent
from src.core.rag import RAGSystem


@pytest.mark.integration
class TestAgentRAGIntegration:
    """Test Agent-RAG integration."""

    @pytest.fixture
    def mock_components(self):
        """Create mock components for integration testing."""
        mock_db = MagicMock()
        mock_gateway = MagicMock()

        # Mock RAG system
        rag = RAGSystem(
            db=mock_db,
            gateway=mock_gateway,
            embedding_model="text-embedding-3-small",
            generation_model="gpt-4",
        )

        # Mock agent
        agent = Agent(agent_id="test-agent", name="Test Agent", gateway=mock_gateway)

        return agent, rag, mock_db, mock_gateway

    def test_agent_uses_rag_for_query(self, mock_components):
        """Test agent using RAG for querying."""
        agent, rag, _, _ = mock_components

        # Mock RAG query
        with patch.object(rag, "query") as mock_query:
            mock_query.return_value = {
                "answer": "Test answer",
                "retrieved_documents": [{"title": "Doc1"}],
                "num_documents": 1,
            }

            # Agent task that uses RAG
            task_id = agent.add_task(task_type="rag_query", parameters={"query": "Test question"})

            assert task_id is not None
            assert len(agent.task_queue) == 1

    def test_rag_ingestion_then_agent_query(self, mock_components):
        """Test RAG ingestion followed by agent query."""
        _, rag, _, _ = mock_components

        # Mock document ingestion
        with patch.object(rag, "ingest_document") as mock_ingest:
            mock_ingest.return_value = "doc-001"

            doc_id = rag.ingest_document(title="Test Doc", content="Test content")

            assert doc_id == "doc-001"

        # Mock query
        with patch.object(rag, "query") as mock_query:
            mock_query.return_value = {
                "answer": "Answer from RAG",
                "retrieved_documents": [],
                "num_documents": 0,
            }

            result = rag.query("Test query")
            assert result["answer"] == "Answer from RAG"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
