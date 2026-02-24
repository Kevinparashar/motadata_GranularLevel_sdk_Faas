"""
Integration Tests for Vector Operations

Tests Vector Operations integration with:
- Vector Operations ↔ RAG (embedding storage and retrieval)
- Vector Operations ↔ Database (DAL operations)
- Vector Operations ↔ Index Manager (index creation and management)
- Vector Operations ↔ Gateway (embedding generation)
- Vector Operations ↔ Data Ingestion (document embeddings)
"""


from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.postgresql_database.vector_operations import VectorOperations
from src.core.postgresql_database.vector_index_manager import (
    IndexDistance,
    IndexType,
    VectorIndexManager,
)


@pytest.mark.integration
class TestVectorOperationsRAGIntegration:
    """Test Vector Operations integration with RAG System."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def mock_embedding_dal(self):
        """Create mock EmbeddingDAL."""
        dal = MagicMock()
        dal.insert_embedding = AsyncMock(return_value=1)
        dal.similarity_search = AsyncMock(return_value=[])
        dal.batch_insert_embeddings = AsyncMock()
        dal.get_embedding = AsyncMock(return_value=None)
        dal.delete_embeddings = AsyncMock(return_value=0)
        return dal

    @pytest.fixture
    def vector_ops(self, mock_db, mock_embedding_dal):
        """Create VectorOperations instance."""
        return VectorOperations(db=mock_db, embedding_dal=mock_embedding_dal)

    @pytest.mark.asyncio
    async def test_rag_stores_document_embeddings(self, vector_ops, mock_embedding_dal):
        """Test that RAG stores document embeddings via Vector Operations."""
        document_id = 123
        embedding = [0.1, 0.2, 0.3] * 512  # 1536-dim embedding
        tenant_id = "tenant_123"

        # Insert embedding (as RAG would do)
        embedding_id = await vector_ops.insert_embedding(
            document_id=document_id,
            embedding=embedding,
            model="text-embedding-3-small",
            tenant_id=tenant_id,
        )

        # Verify embedding was stored
        assert embedding_id == 1
        assert mock_embedding_dal.insert_embedding.called
        call_args = mock_embedding_dal.insert_embedding.call_args
        assert call_args.kwargs["document_id"] == document_id
        assert call_args.kwargs["tenant_id"] == tenant_id

    @pytest.mark.asyncio
    async def test_rag_retrieves_similar_documents(self, vector_ops, mock_embedding_dal):
        """Test that RAG retrieves similar documents via Vector Operations."""
        query_embedding = [0.1, 0.2, 0.3] * 512
        tenant_id = "tenant_123"

        # Mock similarity search results
        mock_embedding_dal.similarity_search.return_value = [
            {
                "id": 1,
                "document_id": 123,
                "similarity": 0.95,
                "metadata": {"title": "Doc 1", "content": "Content 1"},
            },
            {
                "id": 2,
                "document_id": 124,
                "similarity": 0.90,
                "metadata": {"title": "Doc 2", "content": "Content 2"},
            },
        ]

        # Perform similarity search (as RAG would do)
        results = await vector_ops.similarity_search(
            query_embedding=query_embedding,
            limit=10,
            threshold=0.7,
            tenant_id=tenant_id,
        )

        # Verify results
        assert len(results) == 2
        assert results[0]["similarity"] == 0.95
        assert mock_embedding_dal.similarity_search.called
        call_args = mock_embedding_dal.similarity_search.call_args
        assert call_args.kwargs["tenant_id"] == tenant_id

    @pytest.mark.asyncio
    async def test_rag_batch_inserts_embeddings(self, vector_ops, mock_embedding_dal):
        """Test that RAG can batch insert embeddings."""
        tenant_id = "tenant_123"
        embeddings_data = [
            (1, [0.1, 0.2, 0.3] * 512, "text-embedding-3-small"),
            (2, [0.4, 0.5, 0.6] * 512, "text-embedding-3-small"),
            (3, [0.7, 0.8, 0.9] * 512, "text-embedding-3-small"),
        ]

        # Batch insert embeddings
        await vector_ops.batch_insert_embeddings(embeddings_data, tenant_id=tenant_id)

        # Verify batch insert was called
        assert mock_embedding_dal.batch_insert_embeddings.called
        call_args = mock_embedding_dal.batch_insert_embeddings.call_args
        assert call_args.kwargs["tenant_id"] == tenant_id


@pytest.mark.integration
class TestVectorOperationsDatabaseIntegration:
    """Test Vector Operations integration with Database (DAL)."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def mock_embedding_dal(self):
        """Create mock EmbeddingDAL."""
        dal = MagicMock()
        dal.insert_embedding = AsyncMock(return_value=1)
        dal.similarity_search = AsyncMock(return_value=[])
        dal.get_embedding = AsyncMock(return_value={"id": 1, "embedding": [0.1, 0.2, 0.3]})
        dal.delete_embeddings = AsyncMock(return_value=1)
        dal.update_embedding = AsyncMock(return_value=True)
        return dal

    @pytest.fixture
    def vector_ops(self, mock_db, mock_embedding_dal):
        """Create VectorOperations instance."""
        return VectorOperations(db=mock_db, embedding_dal=mock_embedding_dal)

    @pytest.mark.asyncio
    async def test_embedding_persistence_via_dal(self, vector_ops, mock_embedding_dal):
        """Test that embeddings are persisted via DAL."""
        document_id = 123
        embedding = [0.1, 0.2, 0.3] * 512
        tenant_id = "tenant_123"

        # Insert embedding
        embedding_id = await vector_ops.insert_embedding(
            document_id=document_id,
            embedding=embedding,
            tenant_id=tenant_id,
        )

        # Verify DAL was used
        assert embedding_id == 1
        assert mock_embedding_dal.insert_embedding.called

    @pytest.mark.asyncio
    async def test_embedding_retrieval_via_dal(self, vector_ops, mock_embedding_dal):
        """Test that embeddings can be retrieved via DAL."""
        embedding_id = 1
        tenant_id = "tenant_123"

        # Get embedding
        embedding = await vector_ops.get_embedding(embedding_id, tenant_id=tenant_id)

        # Verify embedding was retrieved
        assert embedding is not None
        assert "id" in embedding
        assert mock_embedding_dal.get_embedding.called

    @pytest.mark.asyncio
    async def test_embedding_deletion_via_dal(self, vector_ops, mock_embedding_dal):
        """Test that embeddings can be deleted via DAL."""
        document_id = 123
        tenant_id = "tenant_123"

        # Delete embeddings
        deleted_count = await vector_ops.delete_embeddings(document_id, tenant_id=tenant_id)

        # Verify deletion
        assert deleted_count == 1
        assert mock_embedding_dal.delete_embeddings.called

    @pytest.mark.asyncio
    async def test_embedding_update_via_dal(self, vector_ops, mock_embedding_dal):
        """Test that embeddings can be updated via DAL."""
        embedding_id = 1
        new_embedding = [0.9, 0.8, 0.7] * 512
        tenant_id = "tenant_123"

        # Update embedding
        success = await vector_ops.update_embedding(
            embedding_id, new_embedding, tenant_id=tenant_id
        )

        # Verify update
        assert success is True
        assert mock_embedding_dal.update_embedding.called


@pytest.mark.integration
class TestVectorOperationsIndexManagerIntegration:
    """Test Vector Operations integration with Index Manager."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def mock_index_dal(self):
        """Create mock IndexDAL."""
        dal = MagicMock()
        dal.create_index = AsyncMock(return_value=True)
        dal.index_exists = AsyncMock(return_value=False)
        dal.list_indexes = AsyncMock(return_value=[])
        dal.get_index_info = AsyncMock(return_value=None)
        return dal

    @pytest.fixture
    def index_manager(self, mock_db, mock_index_dal):
        """Create VectorIndexManager instance."""
        return VectorIndexManager(db=mock_db, index_dal=mock_index_dal)

    @pytest.fixture
    def mock_embedding_dal(self):
        """Create mock EmbeddingDAL."""
        dal = MagicMock()
        dal.insert_embedding = AsyncMock(return_value=1)
        dal.similarity_search = AsyncMock(return_value=[])
        return dal

    @pytest.fixture
    def vector_ops(self, mock_db, mock_embedding_dal):
        """Create VectorOperations instance."""
        return VectorOperations(db=mock_db, embedding_dal=mock_embedding_dal)

    @pytest.mark.asyncio
    async def test_index_creation_for_vector_operations(
        self, index_manager, mock_index_dal, vector_ops
    ):
        """Test that indexes are created for vector operations."""
        table_name = "embeddings"
        column_name = "embedding"

        # Check if index exists
        exists = await index_manager.index_exists("embeddings_embedding_idx")

        # Create index if it doesn't exist
        if not exists:
            index_name = await index_manager.create_index(
                table_name=table_name,
                column_name=column_name,
                index_type=IndexType.IVFFLAT,
                distance=IndexDistance.COSINE,
                lists=100,
            )

            # Verify index creation
            assert index_name is not None
            assert mock_index_dal.create_index.called

    @pytest.mark.asyncio
    async def test_index_optimization_for_search(self, index_manager, mock_index_dal):
        """Test that indexes optimize similarity search."""
        # List existing indexes
        indexes = await index_manager.list_indexes("embeddings")

        # Verify indexes can be listed
        assert indexes is not None
        assert mock_index_dal.list_indexes.called

        # Get index info
        index_info = await index_manager.get_index_info("embeddings_embedding_idx")

        # Verify index info can be retrieved (may be None if index doesn't exist)
        # This test verifies the integration point exists
        assert index_info is None or isinstance(index_info, dict)


@pytest.mark.integration
class TestVectorOperationsGatewayIntegration:
    """Test Vector Operations integration with Gateway."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def mock_embedding_dal(self):
        """Create mock EmbeddingDAL."""
        dal = MagicMock()
        dal.insert_embedding = AsyncMock(return_value=1)
        return dal

    @pytest.fixture
    def vector_ops(self, mock_db, mock_embedding_dal):
        """Create VectorOperations instance."""
        return VectorOperations(db=mock_db, embedding_dal=mock_embedding_dal)

    @pytest.mark.asyncio
    async def test_gateway_embeddings_stored_in_vector_ops(
        self, vector_ops, mock_embedding_dal
    ):
        """Test that Gateway-generated embeddings are stored in Vector Operations."""
        document_id = 123
        embedding = [0.1, 0.2, 0.3] * 512  # Generated by Gateway
        tenant_id = "tenant_123"

        # Store embedding (as would happen after Gateway generates it)
        embedding_id = await vector_ops.insert_embedding(
            document_id=document_id,
            embedding=embedding,
            model="text-embedding-3-small",
            tenant_id=tenant_id,
        )

        # Verify embedding was stored
        assert embedding_id == 1
        assert mock_embedding_dal.insert_embedding.called


@pytest.mark.integration
class TestVectorOperationsDataIngestionIntegration:
    """Test Vector Operations integration with Data Ingestion."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def mock_embedding_dal(self):
        """Create mock EmbeddingDAL."""
        dal = MagicMock()
        dal.batch_insert_embeddings = AsyncMock()
        dal.insert_embedding = AsyncMock(return_value=1)
        return dal

    @pytest.fixture
    def vector_ops(self, mock_db, mock_embedding_dal):
        """Create VectorOperations instance."""
        return VectorOperations(db=mock_db, embedding_dal=mock_embedding_dal)

    @pytest.mark.asyncio
    async def test_data_ingestion_stores_document_embeddings(
        self, vector_ops, mock_embedding_dal
    ):
        """Test that Data Ingestion stores document embeddings."""
        tenant_id = "tenant_123"
        # Simulate multiple documents ingested
        embeddings_data = [
            (1, [0.1, 0.2, 0.3] * 512, "text-embedding-3-small"),
            (2, [0.4, 0.5, 0.6] * 512, "text-embedding-3-small"),
            (3, [0.7, 0.8, 0.9] * 512, "text-embedding-3-small"),
        ]

        # Batch insert embeddings (as Data Ingestion would do)
        await vector_ops.batch_insert_embeddings(embeddings_data, tenant_id=tenant_id)

        # Verify batch insert was called
        assert mock_embedding_dal.batch_insert_embeddings.called
        call_args = mock_embedding_dal.batch_insert_embeddings.call_args
        assert call_args.kwargs["tenant_id"] == tenant_id


@pytest.mark.integration
class TestVectorOperationsTenantIsolation:
    """Test tenant isolation in Vector Operations."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def mock_embedding_dal(self):
        """Create mock EmbeddingDAL."""
        dal = MagicMock()
        dal.insert_embedding = AsyncMock(return_value=1)
        dal.similarity_search = AsyncMock(return_value=[])
        return dal

    @pytest.fixture
    def vector_ops(self, mock_db, mock_embedding_dal):
        """Create VectorOperations instance."""
        return VectorOperations(db=mock_db, embedding_dal=mock_embedding_dal)

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_embeddings(self, vector_ops, mock_embedding_dal):
        """Test that embeddings are isolated per tenant."""
        tenant_a = "tenant_a"
        tenant_b = "tenant_b"
        document_id = 123
        embedding = [0.1, 0.2, 0.3] * 512

        # Insert embedding for tenant A
        await vector_ops.insert_embedding(
            document_id=document_id,
            embedding=embedding,
            tenant_id=tenant_a,
        )

        # Insert embedding for tenant B
        await vector_ops.insert_embedding(
            document_id=document_id,
            embedding=embedding,
            tenant_id=tenant_b,
        )

        # Verify tenant_id was passed to DAL
        assert mock_embedding_dal.insert_embedding.call_count == 2
        call_args_list = mock_embedding_dal.insert_embedding.call_args_list
        assert call_args_list[0].kwargs["tenant_id"] == tenant_a
        assert call_args_list[1].kwargs["tenant_id"] == tenant_b

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_similarity_search(self, vector_ops, mock_embedding_dal):
        """Test that similarity search is tenant-scoped."""
        tenant_a = "tenant_a"
        tenant_b = "tenant_b"
        query_embedding = [0.1, 0.2, 0.3] * 512

        # Search for tenant A
        await vector_ops.similarity_search(
            query_embedding=query_embedding,
            tenant_id=tenant_a,
        )

        # Search for tenant B
        await vector_ops.similarity_search(
            query_embedding=query_embedding,
            tenant_id=tenant_b,
        )

        # Verify tenant_id was passed to DAL
        assert mock_embedding_dal.similarity_search.call_count == 2
        call_args_list = mock_embedding_dal.similarity_search.call_args_list
        assert call_args_list[0].kwargs["tenant_id"] == tenant_a
        assert call_args_list[1].kwargs["tenant_id"] == tenant_b


@pytest.mark.integration
class TestVectorOperationsEndToEndIntegration:
    """Test end-to-end Vector Operations integration scenarios."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock()
        db.execute_query = AsyncMock(return_value=[])
        return db

    @pytest.fixture
    def mock_embedding_dal(self):
        """Create mock EmbeddingDAL."""
        dal = MagicMock()
        dal.insert_embedding = AsyncMock(return_value=1)
        dal.similarity_search = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "document_id": 123,
                    "similarity": 0.95,
                    "metadata": {"title": "Doc 1"},
                }
            ]
        )
        dal.batch_insert_embeddings = AsyncMock()
        dal.get_embedding = AsyncMock(return_value={"id": 1, "embedding": [0.1, 0.2, 0.3]})
        return dal

    @pytest.fixture
    def vector_ops(self, mock_db, mock_embedding_dal):
        """Create VectorOperations instance."""
        return VectorOperations(db=mock_db, embedding_dal=mock_embedding_dal)

    @pytest.mark.asyncio
    async def test_end_to_end_vector_workflow(self, vector_ops, mock_embedding_dal):
        """Test complete vector operations workflow."""
        tenant_id = "tenant_123"

        # Step 1: Insert embeddings
        embedding_id = await vector_ops.insert_embedding(
            document_id=123,
            embedding=[0.1, 0.2, 0.3] * 512,
            tenant_id=tenant_id,
        )

        # Step 2: Retrieve embedding
        embedding = await vector_ops.get_embedding(embedding_id, tenant_id=tenant_id)

        # Step 3: Perform similarity search
        results = await vector_ops.similarity_search(
            query_embedding=[0.1, 0.2, 0.3] * 512,
            tenant_id=tenant_id,
        )

        # Verify all operations completed
        assert embedding_id == 1
        assert embedding is not None
        assert len(results) > 0
        assert mock_embedding_dal.insert_embedding.called
        assert mock_embedding_dal.get_embedding.called
        assert mock_embedding_dal.similarity_search.called

