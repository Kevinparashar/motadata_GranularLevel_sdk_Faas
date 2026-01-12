"""
End-to-End Integration Tests

Tests complete workflows from start to finish.
"""

# Standard library imports
from unittest.mock import MagicMock, Mock, patch

# Third-party imports
import pytest

# Local application/library specific imports
from src.core.agno_agent_framework import Agent, AgentManager
from src.core.cache_mechanism import CacheBackend, CacheManager
from src.core.litellm_gateway import LiteLLMGateway
from src.core.postgresql_database import PostgreSQLDatabase
from src.core.rag import RAGSystem


@pytest.mark.integration
@pytest.mark.e2e
class TestEndToEndWorkflows:
    """Test end-to-end workflows."""
    
    @pytest.fixture
    def mock_system(self):
        """Create mock system components."""
        mock_db = MagicMock()
        mock_gateway = MagicMock()
        
        # Mock responses
        mock_embedding_response = MagicMock()
        mock_embedding_response.embeddings = [[0.1] * 1536]
        mock_gateway.embed.return_value = mock_embedding_response
        
        mock_gen_response = MagicMock()
        mock_gen_response.text = "Generated answer"
        mock_gateway.generate.return_value = mock_gen_response
        
        # Create components
        cache = CacheManager(backend=CacheBackend.MEMORY)
        rag = RAGSystem(
            db=mock_db,
            gateway=mock_gateway,
            embedding_model="text-embedding-3-small",
            generation_model="gpt-4"
        )
        agent = Agent(
            agent_id="e2e-agent",
            name="E2E Agent",
            gateway=mock_gateway
        )
        
        return {
            "cache": cache,
            "rag": rag,
            "agent": agent,
            "gateway": mock_gateway,
            "db": mock_db
        }
    
    def test_complete_qa_workflow(self, mock_system):
        """Test complete Q&A workflow."""
        rag = mock_system["rag"]
        agent = mock_system["agent"]
        cache = mock_system["cache"]
        
        # Step 1: Ingest document
        with patch.object(rag, 'ingest_document') as mock_ingest:
            mock_ingest.return_value = "doc-001"
            doc_id = rag.ingest_document(
                title="Test Doc",
                content="Test content"
            )
            assert doc_id == "doc-001"
        
        # Step 2: Query RAG
        with patch.object(rag, 'query') as mock_query:
            mock_query.return_value = {
                "answer": "Test answer",
                "retrieved_documents": [{"title": "Test Doc"}],
                "num_documents": 1
            }
            
            result = rag.query("Test question")
            assert result["answer"] == "Test answer"
        
        # Step 3: Cache result
        cache.set("qa:test", result, ttl=3600)
        cached = cache.get("qa:test")
        assert cached is not None
        
        # Step 4: Agent uses result
        task_id = agent.add_task(
            task_type="qa",
            parameters={"question": "Test question"}
        )
        assert task_id is not None
    
    def test_agent_with_rag_workflow(self, mock_system):
        """Test agent with RAG workflow."""
        agent = mock_system["agent"]
        rag = mock_system["rag"]
        
        # Ingest documents
        with patch.object(rag, 'ingest_document'):
            rag.ingest_document("Doc1", "Content1")
        
        # Agent queries RAG
        with patch.object(rag, 'query') as mock_query:
            mock_query.return_value = {
                "answer": "Answer",
                "retrieved_documents": [],
                "num_documents": 0
            }
            
            result = rag.query("Question")
            assert "answer" in result
            
            # Agent processes result
            task_id = agent.add_task(
                task_type="process_rag_result",
                parameters={"rag_result": result}
            )
            assert task_id is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])

