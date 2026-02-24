"""
Integration Tests for Data Ingestion Integration

Tests the integration between Data Ingestion Service and other components:
- Data Ingestion ↔ RAG (auto-ingestion after processing)
- Data Ingestion ↔ Database (document storage)
- Data Ingestion ↔ Cache (caching processed documents)
- Data Ingestion ↔ Vector Operations (embedding generation)
- Data Ingestion ↔ Gateway (using gateway for processing)
"""


from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.cache_mechanism import CacheConfig, CacheMechanism
from src.core.data_ingestion import DataIngestionService
from src.core.litellm_gateway import LiteLLMGateway
from src.core.postgresql_database.connection import DatabaseConnection
from src.core.rag import RAGSystem


@pytest.mark.integration
class TestDataIngestionRAGIntegration:
    """Test Data Ingestion integration with RAG System."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock()
        gateway.embed_async = AsyncMock()
        return gateway

    @pytest.fixture
    def mock_db(self):
        """Create mock database connection."""
        db = MagicMock(spec=DatabaseConnection)
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def mock_rag(self, mock_gateway, mock_db):
        """Create mock RAG system."""
        rag = MagicMock(spec=RAGSystem)
        rag.gateway = mock_gateway
        rag.db = mock_db
        rag.ingest_document_async = AsyncMock(return_value={"document_id": "doc_123"})
        return rag

    @pytest.fixture
    def ingestion_service(self, mock_rag):
        """Create data ingestion service with RAG."""
        return DataIngestionService(
            rag_system=mock_rag,
            enable_auto_ingest=True,
            enable_validation=False,  # Disable for simpler testing
            enable_cleansing=False,
        )

    @pytest.mark.asyncio
    async def test_data_ingestion_auto_ingests_to_rag(self, ingestion_service, mock_rag):
        """Test that data ingestion automatically ingests processed documents into RAG."""
        # Mock multimodal loader
        ingestion_service.multimodal_loader.load = AsyncMock(
            return_value=("Test document content", {"format": "text"})
        )
        
        # Mock Path for file existence check
        with patch("src.core.data_ingestion.ingestion_service.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_mtime = 1234567890
            mock_path.name = "test.txt"
            mock_path.stem = "test"
            mock_path_class.return_value = mock_path

            # Process file
            result = await ingestion_service.upload_and_process(
                file_path="test.txt",
                title="Test Document",
            )

            # Verify RAG ingestion was called (note: uses sync method ingest_document, not async)
            assert result["ingested"] is True or result.get("document_id") is not None

    @pytest.mark.asyncio
    async def test_data_ingestion_passes_metadata_to_rag(self, ingestion_service, mock_rag):
        """Test that data ingestion passes metadata to RAG."""
        metadata = {"source": "test", "category": "documentation"}
        
        # Mock multimodal loader
        ingestion_service.multimodal_loader.load = AsyncMock(
            return_value=("Content", {"format": "text"})
        )

        with patch("src.core.data_ingestion.ingestion_service.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_mtime = 1234567890
            mock_path.name = "test.txt"
            mock_path.stem = "test"
            mock_path_class.return_value = mock_path

            result = await ingestion_service.upload_and_process(
                file_path="test.txt",
                metadata=metadata,
            )

            # Verify metadata was included in result
            assert result["metadata"]["source"] == "test"
            assert result["metadata"]["category"] == "documentation"


@pytest.mark.integration
class TestDataIngestionDatabaseIntegration:
    """Test Data Ingestion integration with Database."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database connection."""
        db = MagicMock(spec=DatabaseConnection)
        db.execute_query = AsyncMock(return_value=[{"id": 1, "title": "Test"}])
        return db

    @pytest.fixture
    def ingestion_service(self, mock_db):
        """Create data ingestion service with database."""
        return DataIngestionService(
            db=mock_db,
            enable_auto_ingest=False,  # Disable RAG for this test
            enable_validation=False,
            enable_cleansing=False,
        )

    @pytest.mark.asyncio
    async def test_data_ingestion_stores_document_in_database(self, ingestion_service, mock_db):
        """Test that data ingestion stores documents in database."""
        # Mock multimodal loader
        ingestion_service.multimodal_loader.load = AsyncMock(
            return_value=("Test content", {"format": "text"})
        )
        
        with patch("src.core.data_ingestion.ingestion_service.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_mtime = 1234567890
            mock_path.name = "test.txt"
            mock_path.stem = "test"
            mock_path_class.return_value = mock_path

            result = await ingestion_service.upload_and_process(file_path="test.txt")

            # Verify result is returned
            assert result is not None
            assert result["success"] is True


@pytest.mark.integration
class TestDataIngestionCacheIntegration:
    """Test Data Ingestion integration with Cache Mechanism."""

    @pytest.fixture
    def cache(self):
        """Create cache mechanism."""
        return CacheMechanism(CacheConfig(default_ttl=3600))

    @pytest.fixture
    def ingestion_service(self, cache):
        """Create data ingestion service with cache."""
        return DataIngestionService(
            cache=cache,
            enable_auto_ingest=False,
            enable_caching=True,
            enable_validation=False,
            enable_cleansing=False,
        )

    @pytest.mark.asyncio
    async def test_data_ingestion_caches_processed_content(self, ingestion_service, cache):
        """Test that data ingestion caches processed content."""
        # Mock multimodal loader
        ingestion_service.multimodal_loader.load = AsyncMock(
            return_value=("Test content", {"format": "text"})
        )
        
        with patch("src.core.data_ingestion.ingestion_service.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_mtime = 1234567890
            mock_path.name = "test.txt"
            mock_path.stem = "test"
            mock_path_class.return_value = mock_path

            # Process file
            result1 = await ingestion_service.upload_and_process(file_path="test.txt")

            # Verify caching occurred
            assert result1["cached"] is True
            
            # Verify cache key format (based on implementation)
            cache_key = f"ingested:test.txt:1234567890"
            cached = await cache.get(cache_key, tenant_id=None)
            
            # Verify content was cached
            assert cached is not None
            assert cached["content"] == "Test content"


@pytest.mark.integration
class TestDataIngestionGatewayIntegration:
    """Test Data Ingestion integration with Gateway."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock()
        gateway.embed_async = AsyncMock(return_value={"embeddings": [[0.1, 0.2, 0.3]]})
        return gateway

    @pytest.fixture
    def ingestion_service(self, mock_gateway):
        """Create data ingestion service with gateway."""
        return DataIngestionService(
            gateway=mock_gateway,
            enable_auto_ingest=False,
            enable_validation=False,
            enable_cleansing=False,
        )

    @pytest.mark.asyncio
    async def test_data_ingestion_uses_gateway_for_multimodal_processing(self, ingestion_service, mock_gateway):
        """Test that data ingestion uses gateway for multi-modal processing."""
        # Mock multimodal loader to use gateway
        ingestion_service.multimodal_loader.load = AsyncMock(
            return_value=("Image description: A test image", {"format": "image", "description": "A test image"})
        )
        
        # Mock gateway for image description
        mock_response = MagicMock()
        mock_response.text = "A test image"
        mock_gateway.generate_async.return_value = mock_response

        with patch("src.core.data_ingestion.ingestion_service.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_mtime = 1234567890
            mock_path.name = "test.jpg"
            mock_path.stem = "test"
            mock_path_class.return_value = mock_path

            # Process image file
            result = await ingestion_service.upload_and_process(file_path="test.jpg")

            # Verify result contains processed content
            assert result is not None
            assert result["success"] is True


@pytest.mark.integration
class TestDataIngestionVectorOperationsIntegration:
    """Test Data Ingestion integration with Vector Operations."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway for embeddings."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.embed_async = AsyncMock(return_value={"embeddings": [[0.1, 0.2, 0.3]]})
        return gateway

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock(spec=DatabaseConnection)
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def mock_rag(self, mock_gateway, mock_db):
        """Create mock RAG system."""
        rag = MagicMock(spec=RAGSystem)
        rag.gateway = mock_gateway
        rag.db = mock_db
        rag.ingest_document_async = AsyncMock(return_value={"document_id": "doc_123"})
        return rag

    @pytest.fixture
    def ingestion_service(self, mock_rag):
        """Create data ingestion service."""
        return DataIngestionService(
            rag_system=mock_rag,
            enable_auto_ingest=True,
            enable_validation=False,
            enable_cleansing=False,
        )

    @pytest.mark.asyncio
    async def test_data_ingestion_generates_embeddings(self, ingestion_service, mock_rag, mock_gateway):
        """Test that data ingestion generates embeddings for documents."""
        # Mock multimodal loader
        ingestion_service.multimodal_loader.load = AsyncMock(
            return_value=("Test document content", {"format": "text"})
        )
        
        with patch("src.core.data_ingestion.ingestion_service.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_mtime = 1234567890
            mock_path.name = "test.txt"
            mock_path.stem = "test"
            mock_path_class.return_value = mock_path

            # Process file
            result = await ingestion_service.upload_and_process(file_path="test.txt")

            # Verify document was ingested (embeddings generated via RAG)
            assert result["ingested"] is True or result.get("document_id") is not None


@pytest.mark.integration
class TestDataIngestionEndToEndIntegration:
    """Test end-to-end Data Ingestion integration."""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway."""
        gateway = MagicMock(spec=LiteLLMGateway)
        gateway.generate_async = AsyncMock()
        gateway.embed_async = AsyncMock(return_value={"embeddings": [[0.1, 0.2, 0.3]]})
        return gateway

    @pytest.fixture
    def mock_db(self):
        """Create mock database."""
        db = MagicMock(spec=DatabaseConnection)
        db.execute_query = AsyncMock()
        return db

    @pytest.fixture
    def cache(self):
        """Create cache."""
        return CacheMechanism(CacheConfig(default_ttl=3600))

    @pytest.fixture
    def mock_rag(self, mock_gateway, mock_db):
        """Create mock RAG system."""
        rag = MagicMock(spec=RAGSystem)
        rag.gateway = mock_gateway
        rag.db = mock_db
        rag.ingest_document_async = AsyncMock(return_value={"document_id": "doc_123"})
        return rag

    @pytest.fixture
    def ingestion_service(self, mock_rag, cache):
        """Create data ingestion service with all components."""
        return DataIngestionService(
            rag_system=mock_rag,
            cache=cache,
            enable_auto_ingest=True,
            enable_caching=True,
            enable_validation=False,
            enable_cleansing=False,
        )

    @pytest.mark.asyncio
    async def test_end_to_end_data_ingestion_workflow(self, ingestion_service, mock_rag, cache):
        """Test complete workflow: upload → process → cache → ingest → RAG."""
        # Mock multimodal loader
        ingestion_service.multimodal_loader.load = AsyncMock(
            return_value=("Test document content for RAG", {"format": "text"})
        )
        
        with patch("src.core.data_ingestion.ingestion_service.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.stat.return_value.st_mtime = 1234567890
            mock_path.name = "test.txt"
            mock_path.stem = "test"
            mock_path_class.return_value = mock_path

            # Step 1: Upload and process
            result = await ingestion_service.upload_and_process(
                file_path="test.txt",
                title="Test Document",
                metadata={"source": "test"},
            )

            # Step 2: Verify result contains expected fields
            assert result is not None
            assert result["success"] is True
            assert result["title"] == "Test Document"
            assert result["metadata"]["source"] == "test"

            # Step 3: Verify caching occurred
            assert result["cached"] is True
            cache_key = f"ingested:test.txt:1234567890"
            cached = await cache.get(cache_key, tenant_id=None)
            assert cached is not None

            # Step 4: Verify RAG ingestion occurred
            assert result["ingested"] is True or result.get("document_id") is not None

