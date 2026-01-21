"""
RAG System

Complete Retrieval-Augmented Generation system.
"""

# Standard library imports
import logging
from typing import Any, Dict, List, Optional

# Local application/library specific imports
from ..agno_agent_framework.memory import AgentMemory, MemoryType
from ..cache_mechanism import CacheConfig, CacheMechanism
from ..litellm_gateway import LiteLLMGateway
from ..postgresql_database.connection import DatabaseConnection
from ..postgresql_database.vector_operations import VectorOperations
from ..postgresql_database.vector_index_manager import (
    VectorIndexManager,
    create_vector_index_manager,
    IndexType,
    IndexDistance
)
from .document_processor import DocumentChunk, DocumentProcessor
from .generator import RAGGenerator
from .retriever import Retriever

# Set up logger
logger = logging.getLogger(__name__)


class RAGSystem:
    """
    Complete RAG system integrating all components.

    Handles document ingestion, retrieval, and generation.
    """

    def __init__(
        self,
        db: DatabaseConnection,
        gateway: LiteLLMGateway,
        embedding_model: str = "text-embedding-3-small",
        generation_model: str = "gpt-4",
        cache: Optional[CacheMechanism] = None,
        cache_config: Optional[CacheConfig] = None,
        enable_memory: bool = True,
        memory_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize RAG system.

        Args:
            db: Database connection
            gateway: LiteLLM gateway
            embedding_model: Model for embeddings
            generation_model: Model for generation
            cache: Optional cache mechanism
            cache_config: Optional cache configuration
            enable_memory: Enable memory for conversation context
            memory_config: Optional memory configuration
        """
        self.db = db
        self.gateway = gateway
        self.embedding_model = embedding_model
        self.generation_model = generation_model
        self.cache = cache or CacheMechanism(cache_config or CacheConfig())

        # Initialize memory for conversation context
        self.memory: Optional[AgentMemory] = None
        if enable_memory:
            memory_config = memory_config or {}
            self.memory = AgentMemory(
                agent_id="rag_system",
                max_episodic=memory_config.get("max_episodic", 100),
                max_semantic=memory_config.get("max_semantic", 200),
                max_age_days=memory_config.get("max_age_days", 30),
                persistence_path=memory_config.get("persistence_path")
            )

        # Initialize components
        self.vector_ops = VectorOperations(db)
        
        # Initialize vector index manager
        self.index_manager = create_vector_index_manager(db)
        
        # Initialize document processor with multimodal support
        processor_kwargs = {
            "chunk_size": kwargs.get("chunk_size", 1000),
            "chunk_overlap": kwargs.get("chunk_overlap", 200),
            "chunking_strategy": kwargs.get("chunking_strategy", "fixed"),
            "min_chunk_size": kwargs.get("min_chunk_size", 50),
            "max_chunk_size": kwargs.get("max_chunk_size", 2000),
            "enable_preprocessing": kwargs.get("enable_preprocessing", True),
            "enable_metadata_extraction": kwargs.get("enable_metadata_extraction", True),
            "enable_multimodal": kwargs.get("enable_multimodal", True),
            "gateway": gateway  # Pass gateway for image description generation
        }
        self.document_processor = DocumentProcessor(**processor_kwargs)
        
        self.retriever = Retriever(
            vector_ops=self.vector_ops,
            gateway=gateway,
            embedding_model=embedding_model
        )
        self.generator = RAGGenerator(
            gateway=gateway,
            model=generation_model
        )

    def ingest_document(
        self,
        title: str,
        content: Optional[str] = None,
        file_path: Optional[str] = None,
        tenant_id: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Ingest a document into the RAG system.

        Supports both direct content and file paths for multi-modal data:
        - Text files: .txt, .md, .html, .json
        - Documents: .pdf, .doc, .docx
        - Audio: .mp3, .wav, .m4a, .ogg (with transcription)
        - Video: .mp4, .avi, .mov, .mkv (with transcription and frame extraction)
        - Images: .jpg, .png, .gif, .bmp (with OCR and description)

        Args:
            title: Document title
            content: Document content (if provided directly)
            file_path: Path to file (for multi-modal loading)
            tenant_id: Optional tenant ID for multi-tenant SaaS
            source: Optional source URL/path
            metadata: Optional metadata

        Returns:
            Document ID
        """
        # Load from file if file_path provided
        if file_path:
            content, loaded_metadata = self.document_processor.load_document(file_path)
            if metadata:
                metadata.update(loaded_metadata)
            else:
                metadata = loaded_metadata
            if not source:
                source = file_path
        
        # Ensure content is provided
        if not content:
            raise ValueError("Either 'content' or 'file_path' must be provided")
        
        # Insert document with tenant_id
        query = """
        INSERT INTO documents (title, content, metadata, source, tenant_id)
        VALUES (%s, %s, %s::jsonb, %s, %s)
        RETURNING id;
        """

        import json
        metadata_json = json.dumps(metadata or {})

        result = self.db.execute_query(
            query,
            (title, content, metadata_json, source, tenant_id),
            fetch_one=True
        )

        document_id = str(result['id'])

        # Process and chunk document
        chunks = self.document_processor.chunk_document(
            content=content,
            document_id=document_id,
            metadata=metadata
        )

        if not chunks:
            return document_id

        # Batch processing: Collect all chunk texts
        chunk_texts = [chunk.content for chunk in chunks]

        # Generate embeddings in batch (single API call)
        try:
            embedding_response = self.gateway.embed(
                texts=chunk_texts,
                model=self.embedding_model
            )

            # Map embeddings back to chunks
            embeddings_data = []
            if embedding_response.embeddings:
                for i, embedding in enumerate(embedding_response.embeddings):
                    if i < len(chunks):  # Ensure we have a matching chunk
                        embeddings_data.append((
                            int(document_id),
                            embedding,
                            self.embedding_model
                        ))
        except (ConnectionError, TimeoutError, ValueError) as e:
            # If batch fails due to network/timeout/validation errors, fall back to individual processing
            logger.warning(f"Batch embedding failed, falling back to individual processing: {e}")
            embeddings_data = []
            for chunk in chunks:
                try:
                    embedding_response = self.gateway.embed(
                        texts=[chunk.content],
                        model=self.embedding_model
                    )
                    if embedding_response.embeddings and len(embedding_response.embeddings) > 0:
                        embedding = embedding_response.embeddings[0]
                        embeddings_data.append((
                            int(document_id),
                            embedding,
                            self.embedding_model
                        ))
                except (ConnectionError, TimeoutError, ValueError) as chunk_error:
                    # Skip failed chunk embedding to keep ingestion resilient
                    logger.warning(f"Failed to embed chunk, skipping: {chunk_error}")
                    continue
                except Exception as chunk_error:
                    # Log unexpected errors but continue processing
                    logger.error(f"Unexpected error embedding chunk: {chunk_error}", exc_info=True)
                    continue

        # Batch insert embeddings
        if embeddings_data:
            self.vector_ops.batch_insert_embeddings(embeddings_data)
            
            # Auto-reindex after batch insert (non-blocking)
            try:
                self.index_manager.auto_reindex_on_embedding_change(
                    table_name="embeddings",
                    column_name="embedding"
                )
            except Exception as e:
                logger.warning(f"Auto-reindexing failed (non-critical): {str(e)}")

        return document_id

    def _rewrite_query(self, query: str) -> str:
        """
        Rewrite query to improve retrieval quality.

        Simple query rewriting: expand abbreviations, normalize terms.
        Can be extended with LLM-based query expansion.

        Args:
            query: Original query

        Returns:
            Rewritten query
        """
        # Basic query normalization
        rewritten = query.strip()

        # Expand common abbreviations
        abbreviations = {
            "AI": "artificial intelligence",
            "ML": "machine learning",
            "DL": "deep learning",
            "NLP": "natural language processing",
            "API": "application programming interface",
        }

        for abbr, full in abbreviations.items():
            rewritten = rewritten.replace(abbr, full)

        # Remove extra whitespace
        rewritten = " ".join(rewritten.split())

        return rewritten

    def query(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.7,
        max_tokens: int = 1000,
        use_query_rewriting: bool = True,
        retrieval_strategy: str = "vector",  # "vector", "hybrid", "keyword"
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG system with query optimization.

        Args:
            query: User query
            tenant_id: Optional tenant ID for multi-tenant SaaS (filters documents by tenant)
            top_k: Number of documents to retrieve
            threshold: Similarity threshold
            max_tokens: Maximum tokens in response
            use_query_rewriting: Whether to rewrite query for better retrieval
            retrieval_strategy: Retrieval strategy ("vector", "hybrid", "keyword")
            user_id: Optional user ID for memory context
            conversation_id: Optional conversation ID for memory context

        Returns:
            Dictionary with answer and retrieved documents
        """
        # Retrieve relevant memories if memory is enabled
        memories = []
        memory_context = ""
        if self.memory:
            memories = self.memory.retrieve(
                query=query,
                limit=5,
                memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC]
            )
            if memories:
                memory_context = "\n".join([
                    f"- {mem.content}" for mem in memories[:3]
                ])

        # Query rewriting for optimization
        original_query = query
        if use_query_rewriting:
            query = self._rewrite_query(query)

        # Include tenant_id in cache key for tenant isolation
        cache_key = f"rag:query:{tenant_id or 'global'}:{query}:{top_k}:{threshold}:{max_tokens}:{retrieval_strategy}"
        cached = self.cache.get(cache_key, tenant_id=tenant_id)
        if cached:
            return cached

        try:
            # Use hybrid retrieval if specified
            if retrieval_strategy == "hybrid":
                retrieved_docs = self.retriever.retrieve_hybrid(
                    query=query,
                    top_k=top_k,
                    threshold=threshold,
                    tenant_id=tenant_id
                )
            else:
                retrieved_docs = self.retriever.retrieve(
                    query=query,
                    top_k=top_k,
                    threshold=threshold,
                    tenant_id=tenant_id
                )

            # Enhance context with memory if available
            enhanced_context = retrieved_docs
            if memory_context:
                enhanced_context = [
                    {"title": "Previous Context", "content": memory_context, "source": "memory"}
                ] + retrieved_docs

            answer = self.generator.generate(
                query=original_query,  # Use original query for generation
                context_documents=enhanced_context,
                max_tokens=max_tokens
            )

            result = {
                "answer": answer,
                "retrieved_documents": retrieved_docs,
                "num_documents": len(retrieved_docs),
                "query_used": query if use_query_rewriting else original_query,
                "original_query": original_query,
                "memory_used": len(memories) if memories else 0
            }

            # Store in cache
            self.cache.set(cache_key, result, ttl=300, tenant_id=tenant_id)

            # Store in memory for future context
            if self.memory:
                self.memory.store(
                    content=f"Query: {original_query}\nAnswer: {answer}",
                    memory_type=MemoryType.EPISODIC,
                    importance=0.7,
                    metadata={
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "tenant_id": tenant_id,
                        "num_documents": len(retrieved_docs)
                    }
                )

            return result
        except (ConnectionError, TimeoutError) as e:
            # Network/connection errors
            logger.error(f"Network error during RAG query: {e}")
            return {
                "answer": None,
                "retrieved_documents": [],
                "num_documents": 0,
                "error": f"Network error: {str(e)}",
            }
        except ValueError as e:
            # Validation/parameter errors
            logger.error(f"Validation error during RAG query: {e}")
            return {
                "answer": None,
                "retrieved_documents": [],
                "num_documents": 0,
                "error": f"Validation error: {str(e)}",
            }
        except Exception as e:
            # Unexpected errors - log and return generic error
            logger.error(f"Unexpected error during RAG query: {e}", exc_info=True)
            return {
                "answer": None,
                "retrieved_documents": [],
                "num_documents": 0,
                "error": f"An error occurred: {str(e)}",
            }

    async def query_async(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.7,
        max_tokens: int = 1000,
        use_query_rewriting: bool = True,
        retrieval_strategy: str = "vector",
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG system asynchronously.

        Args:
            query: User query
            tenant_id: Optional tenant ID for multi-tenant SaaS
            top_k: Number of documents to retrieve
            threshold: Similarity threshold
            max_tokens: Maximum tokens in response
            use_query_rewriting: Whether to rewrite query
            retrieval_strategy: Retrieval strategy
            user_id: Optional user ID for memory context
            conversation_id: Optional conversation ID for memory context

        Returns:
            Dictionary with answer and retrieved documents
        """
        # RAG QUERY PROCESS: Step-by-step retrieval and generation

        # STEP 1: Retrieve relevant conversation memories (if memory enabled)
        # This provides context from previous conversations to improve answer relevance
        # Cost impact: Memory retrieval is free (no API call), improves answer quality
        memories = []
        memory_context = ""
        if self.memory:
            memories = self.memory.retrieve(
                query=query,
                limit=5,
                memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC]
            )
            if memories:
                memory_context = "\n".join([
                    f"- {mem.content}" for mem in memories[:3]
                ])

        # STEP 2: Query rewriting for optimization
        # Rewrites user query to be more effective for vector search
        # Example: "What is X?" → "Explain X in detail" (better for retrieval)
        original_query = query
        if use_query_rewriting:
            query = self._rewrite_query(query)

        # STEP 3: Check cache for previous identical queries
        # COST OPTIMIZATION: Cache hits avoid expensive embedding + generation calls
        # Cost saved per cache hit: ~$0.003-0.03 (embedding + generation)
        cache_key = f"rag:query:{tenant_id or 'global'}:{query}:{top_k}:{threshold}:{max_tokens}:{retrieval_strategy}"
        cached = self.cache.get(cache_key, tenant_id=tenant_id)
        if cached:
            return cached

        try:
            # STEP 4: Document retrieval (vector search in database)
            # This finds the most relevant document chunks for the query
            # Cost: ~$0.0001-0.001 per query (embedding generation for query)
            if retrieval_strategy == "hybrid":
                # Hybrid: Combines vector search + keyword search for better results
                retrieved_docs = self.retriever.retrieve_hybrid(
                    query=query,
                    top_k=top_k,
                    threshold=threshold,
                    tenant_id=tenant_id
                )
            else:
                # Vector-only: Fast, semantic similarity search
                retrieved_docs = self.retriever.retrieve(
                    query=query,
                    top_k=top_k,
                    threshold=threshold,
                    tenant_id=tenant_id
                )

            # STEP 5: Enhance context with memory if available
            # Combines retrieved documents with conversation memory for richer context
            # This enables RAG to answer questions using both documents and conversation history
            enhanced_context = retrieved_docs
            if memory_context:
                enhanced_context = [
                    {"title": "Previous Context", "content": memory_context, "source": "memory"}
                ] + retrieved_docs

            # STEP 6: Generate answer using LLM with retrieved context
            # This is the generation step: LLM creates answer from retrieved documents
            # Cost: ~$0.002-0.02 per generation (depends on model and context size)
            # Context size = retrieved documents + memory, affects token usage and cost
            answer = await self.generator.generate_async(
                query=original_query,  # Use original query for generation (not rewritten)
                context_documents=enhanced_context,
                max_tokens=max_tokens  # Limit response length to control cost
            )

            result = {
                "answer": answer,
                "retrieved_documents": retrieved_docs,
                "num_documents": len(retrieved_docs),
                "query_used": query if use_query_rewriting else original_query,
                "original_query": original_query,
                "memory_used": len(memories) if memories else 0
            }

            # Store in cache
            self.cache.set(cache_key, result, ttl=300, tenant_id=tenant_id)

            # Store in memory for future context
            if self.memory:
                self.memory.store(
                    content=f"Query: {original_query}\nAnswer: {answer}",
                    memory_type=MemoryType.EPISODIC,
                    importance=0.7,
                    metadata={
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "tenant_id": tenant_id,
                        "num_documents": len(retrieved_docs)
                    }
                )

            return result
        except (ConnectionError, TimeoutError) as e:
            # Network/connection errors
            logger.error(f"Network error during async RAG query: {e}")
            return {
                "answer": None,
                "retrieved_documents": [],
                "num_documents": 0,
                "error": f"Network error: {str(e)}",
            }
        except ValueError as e:
            # Validation/parameter errors
            logger.error(f"Validation error during async RAG query: {e}")
            return {
                "answer": None,
                "retrieved_documents": [],
                "num_documents": 0,
                "error": f"Validation error: {str(e)}",
            }
        except Exception as e:
            # Unexpected errors - log and return generic error
            logger.error(f"Unexpected error during async RAG query: {e}", exc_info=True)
            return {
                "answer": None,
                "retrieved_documents": [],
                "num_documents": 0,
                "error": f"An error occurred: {str(e)}",
            }

    async def ingest_document_async(
        self,
        title: str,
        content: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Ingest a document into the RAG system asynchronously with batch processing.

        Args:
            title: Document title
            content: Document content
            source: Optional source URL/path
            metadata: Optional metadata

        Returns:
            Document ID
        """
        # Insert document
        query = """
        INSERT INTO documents (title, content, metadata, source)
        VALUES (%s, %s, %s::jsonb, %s)
        RETURNING id;
        """

        import json
        metadata_json = json.dumps(metadata or {})

        result = self.db.execute_query(
            query,
            (title, content, metadata_json, source),
            fetch_one=True
        )

        document_id = str(result['id'])

        # Process and chunk document
        chunks = self.document_processor.chunk_document(
            content=content,
            document_id=document_id,
            metadata=metadata
        )

        if not chunks:
            return document_id

        # Batch processing: Collect all chunk texts
        chunk_texts = [chunk.content for chunk in chunks]

        # Generate embeddings in batch (single async API call)
        try:
            embedding_response = await self.gateway.embed_async(
                texts=chunk_texts,
                model=self.embedding_model
            )

            # Map embeddings back to chunks
            embeddings_data = []
            if embedding_response.embeddings:
                for i, embedding in enumerate(embedding_response.embeddings):
                    if i < len(chunks):  # Ensure we have a matching chunk
                        embeddings_data.append((
                            int(document_id),
                            embedding,
                            self.embedding_model
                        ))
        except (ConnectionError, TimeoutError, ValueError) as e:
            # If batch fails due to network/timeout/validation errors, fall back to individual processing
            logger.warning(f"Batch embedding failed in async ingestion, falling back to individual processing: {e}")
            embeddings_data = []
            for chunk in chunks:
                try:
                    embedding_response = await self.gateway.embed_async(
                        texts=[chunk.content],
                        model=self.embedding_model
                    )
                    if embedding_response.embeddings and len(embedding_response.embeddings) > 0:
                        embedding = embedding_response.embeddings[0]
                        embeddings_data.append((
                            int(document_id),
                            embedding,
                            self.embedding_model
                        ))
                except (ConnectionError, TimeoutError, ValueError) as chunk_error:
                    # Skip failed chunk embedding to keep ingestion resilient
                    logger.warning(f"Failed to embed chunk in async ingestion, skipping: {chunk_error}")
                    continue
                except Exception as chunk_error:
                    # Log unexpected errors but continue processing
                    logger.error(f"Unexpected error embedding chunk in async ingestion: {chunk_error}", exc_info=True)
                    continue

        # Batch insert embeddings
        if embeddings_data:
            self.vector_ops.batch_insert_embeddings(embeddings_data)
            
            # Auto-reindex after batch insert (non-blocking)
            try:
                self.index_manager.auto_reindex_on_embedding_change(
                    table_name="embeddings",
                    column_name="embedding"
                )
            except Exception as e:
                logger.warning(f"Auto-reindexing failed (non-critical): {str(e)}")

        return document_id

    def ingest_documents_batch(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> List[str]:
        """
        Ingest multiple documents in batch with optimized processing.

        Args:
            documents: List of document dicts with keys: title, content, source (optional), metadata (optional)
            batch_size: Number of documents to process in each batch

        Returns:
            List of document IDs
        """
        document_ids = []

        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            # Process each document in the batch
            for doc in batch:
                try:
                    doc_id = self.ingest_document(
                        title=doc.get("title", ""),
                        content=doc.get("content", ""),
                        source=doc.get("source"),
                        metadata=doc.get("metadata")
                    )
                    document_ids.append(doc_id)
                except (ValueError, ConnectionError) as e:
                    # Log specific errors but continue with other documents
                    logger.warning(f"Failed to ingest document in batch, skipping: {e}")
                    continue
                except Exception as e:
                    # Log unexpected errors but continue processing
                    logger.error(f"Unexpected error ingesting document in batch: {e}", exc_info=True)
                    continue

        return document_ids

    async def ingest_documents_batch_async(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> List[str]:
        """
        Ingest multiple documents in batch asynchronously with optimized processing.

        Args:
            documents: List of document dicts with keys: title, content, source (optional), metadata (optional)
            batch_size: Number of documents to process in each batch

        Returns:
            List of document IDs
        """
        import asyncio

        document_ids = []

        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            # Process batch concurrently
            tasks = []
            for doc in batch:
                task = self.ingest_document_async(
                    title=doc.get("title", ""),
                    content=doc.get("content", ""),
                    source=doc.get("source"),
                    metadata=doc.get("metadata")
                )
                tasks.append(task)

            # Wait for all documents in batch to complete
            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in batch_results:
                    if isinstance(result, Exception):
                        # Log error but continue
                        continue
                    else:
                        document_ids.append(result)
            except (ConnectionError, TimeoutError, ValueError) as e:
                # Log specific errors and continue with next batch
                logger.warning(f"Batch processing failed, continuing with next batch: {e}")
                continue
            except Exception as e:
                # Log unexpected errors but continue processing
                logger.error(f"Unexpected error in batch processing: {e}", exc_info=True)
                continue

        return document_ids

    def create_index(
        self,
        index_type: IndexType = IndexType.IVFFLAT,
        distance: IndexDistance = IndexDistance.COSINE,
        **kwargs: Any
    ) -> bool:
        """
        Create a vector index for optimal search performance.
        
        Args:
            index_type: Type of index (IVFFlat or HNSW)
            distance: Distance metric (cosine, l2, inner_product)
            **kwargs: Additional index parameters
        
        Returns:
            True if index created successfully
        """
        return self.index_manager.create_index(
            table_name="embeddings",
            column_name="embedding",
            index_type=index_type,
            distance=distance,
            **kwargs
        )
    
    def reindex(
        self,
        concurrently: bool = True
    ) -> List[str]:
        """
        Reindex all vector indexes (useful after embedding model changes or bulk updates).
        
        Args:
            concurrently: Whether to rebuild concurrently (non-blocking)
        
        Returns:
            List of reindexed index names
        """
        return self.index_manager.reindex_table(
            table_name="embeddings",
            concurrently=concurrently
        )
    
    def get_index_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all vector indexes.
        
        Returns:
            List of index information dictionaries
        """
        return self.index_manager.list_indexes(table_name="embeddings")

    def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing document in the RAG system.

        Args:
            document_id: Document ID to update
            title: Optional new title
            content: Optional new content (will re-process and re-embed)
            metadata: Optional new metadata

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Update document metadata
            updates = []
            params = []

            if title is not None:
                updates.append("title = %s")
                params.append(title)

            if metadata is not None:
                import json
                updates.append("metadata = %s::jsonb")
                params.append(json.dumps(metadata))

            if updates:
                query = f"""
                UPDATE documents
                SET {', '.join(updates)}
                WHERE id = %s;
                """
                params.append(document_id)
                self.db.execute_query(query, tuple(params))

            # If content changed, re-process document
            if content is not None:
                # Delete old chunks and embeddings
                self._delete_document_chunks(document_id)

                # Re-process and re-embed
                chunks = self.document_processor.chunk_document(
                    content=content,
                    document_id=document_id,
                    metadata=metadata
                )

                if chunks:
                    chunk_texts = [chunk.content for chunk in chunks]

                    # Generate embeddings in batch
                    embedding_response = self.gateway.embed(
                        texts=chunk_texts,
                        model=self.embedding_model
                    )

                    if embedding_response.embeddings:
                        embeddings_data = []
                        for i, embedding in enumerate(embedding_response.embeddings):
                            if i < len(chunks):
                                embeddings_data.append((
                                    int(document_id),
                                    embedding,
                                    self.embedding_model
                                ))

                        if embeddings_data:
                            self.vector_ops.batch_insert_embeddings(embeddings_data)
            
            # Auto-reindex after batch insert (non-blocking)
            try:
                self.index_manager.auto_reindex_on_embedding_change(
                    table_name="embeddings",
                    column_name="embedding"
                )
            except Exception as e:
                logger.warning(f"Auto-reindexing failed (non-critical): {str(e)}")

                # Update content in database
                query = "UPDATE documents SET content = %s WHERE id = %s;"
                self.db.execute_query(query, (content, document_id))

            # Invalidate cache for this document
            self.cache.invalidate_pattern(f"rag:doc:{document_id}")

            return True
        except (ConnectionError, ValueError) as e:
            # Log specific errors
            logger.error(f"Error updating document {document_id}: {e}")
            return False
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error updating document {document_id}: {e}", exc_info=True)
            return False

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its associated chunks/embeddings from the RAG system.

        Args:
            document_id: Document ID to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # Delete document chunks and embeddings
            self._delete_document_chunks(document_id)

            # Delete document
            query = "DELETE FROM documents WHERE id = %s;"
            self.db.execute_query(query, (document_id,))

            # Invalidate cache
            self.cache.invalidate_pattern(f"rag:doc:{document_id}")
            self.cache.invalidate_pattern(f"rag:query:*")

            return True
        except (ConnectionError, ValueError) as e:
            # Log specific errors
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error deleting document {document_id}: {e}", exc_info=True)
            return False

    def _delete_document_chunks(self, document_id: str) -> None:
        """
        Delete all chunks and embeddings for a document.

        Args:
            document_id: Document ID
        """
        # Delete embeddings
        query = "DELETE FROM embeddings WHERE document_id = %s;"
        self.db.execute_query(query, (document_id,))

        # Note: If you have a chunks table, delete from there too
        # query = "DELETE FROM chunks WHERE document_id = %s;"
        # self.db.execute_query(query, (document_id,))

