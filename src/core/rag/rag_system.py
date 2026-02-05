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
from ..postgresql_database.vector_index_manager import (
    IndexDistance,
    IndexType,
    create_vector_index_manager,
)
from ..postgresql_database.vector_operations import VectorOperations
from .document_processor import DocumentProcessor
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
        **kwargs: Any,
    ):
        """
        Initialize RAG system.
        
        Args:
            db (DatabaseConnection): Database connection/handle.
            gateway (LiteLLMGateway): Gateway client used for LLM calls.
            embedding_model (str): Input parameter for this operation.
            generation_model (str): Input parameter for this operation.
            cache (Optional[CacheMechanism]): Cache instance used to store and fetch cached results.
            cache_config (Optional[CacheConfig]): Input parameter for this operation.
            enable_memory (bool): Flag to enable or disable memory.
            memory_config (Optional[Dict[str, Any]]): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
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
                persistence_path=memory_config.get("persistence_path"),
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
            "gateway": gateway,  # Pass gateway for image description generation
        }
        self.document_processor = DocumentProcessor(**processor_kwargs)

        self.retriever = Retriever(
            vector_ops=self.vector_ops, gateway=gateway, embedding_model=embedding_model
        )
        self.generator = RAGGenerator(gateway=gateway, model=generation_model)

    async def _load_document_from_file(
        self, file_path: str, metadata: Optional[Dict[str, Any]]
    ) -> tuple[str, Dict[str, Any], str]:
        """
        Load document from file path asynchronously.
        
        Args:
            file_path (str): Path of the input file.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            tuple[str, Dict[str, Any], str]: Dictionary result of the operation.
        """
        content, loaded_metadata = await self.document_processor.load_document(file_path)
        if metadata:
            metadata.update(loaded_metadata)
        else:
            metadata = loaded_metadata
        return content, metadata, file_path

    async def _insert_document_to_db(
        self, title: str, content: str, metadata: Optional[Dict[str, Any]], source: Optional[str], tenant_id: Optional[str]
    ) -> str:
        """
        Insert document into database and return document ID.
        
        Args:
            title (str): Input parameter for this operation.
            content (str): Content text.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
            source (Optional[str]): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            str: Returned text value.
        """
        import json

        query = """
        INSERT INTO documents (title, content, metadata, source, tenant_id)
        VALUES (%s, %s, %s::jsonb, %s, %s)
        RETURNING id;
        """
        metadata_json = json.dumps(metadata or {})
        result = await self.db.execute_query(
            query, (title, content, metadata_json, source, tenant_id), fetch_one=True
        )
        return str(result["id"])

    def _generate_embeddings_batch(
        self, chunk_texts: List[str], document_id: str
    ) -> List[tuple]:
        """
        Generate embeddings in batch.
        
        Args:
            chunk_texts (List[str]): Input parameter for this operation.
            document_id (str): Input parameter for this operation.
        
        Returns:
            List[tuple]: List result of the operation.
        """
        try:
            embedding_response = self.gateway.embed(texts=chunk_texts, model=self.embedding_model)
            embeddings_data = []
            if embedding_response.embeddings:
                for i, embedding in enumerate(embedding_response.embeddings):
                    if i < len(chunk_texts):
                        embeddings_data.append((int(document_id), embedding, self.embedding_model))
            return embeddings_data
        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.warning(f"Batch embedding failed, falling back to individual processing: {e}")
            return []

    def _generate_embeddings_individual(
        self, chunks: List[Any], document_id: str
    ) -> List[tuple]:
        """
        Generate embeddings individually as fallback.
        
        Args:
            chunks (List[Any]): Input parameter for this operation.
            document_id (str): Input parameter for this operation.
        
        Returns:
            List[tuple]: List result of the operation.
        """
        embeddings_data = []
        for chunk in chunks:
            try:
                embedding_response = self.gateway.embed(
                    texts=[chunk.content], model=self.embedding_model
                )
                if embedding_response.embeddings and len(embedding_response.embeddings) > 0:
                    embedding = embedding_response.embeddings[0]
                    embeddings_data.append((int(document_id), embedding, self.embedding_model))
            except (ConnectionError, TimeoutError, ValueError) as chunk_error:
                logger.warning(f"Failed to embed chunk, skipping: {chunk_error}")
                continue
            except Exception as chunk_error:
                logger.error(f"Unexpected error embedding chunk: {chunk_error}", exc_info=True)
                continue
        return embeddings_data

    def _process_embeddings(
        self, chunks: List[Any], document_id: str
    ) -> List[tuple]:
        """
        Process embeddings with batch fallback to individual.
        
        Args:
            chunks (List[Any]): Input parameter for this operation.
            document_id (str): Input parameter for this operation.
        
        Returns:
            List[tuple]: List result of the operation.
        """
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings_data = self._generate_embeddings_batch(chunk_texts, document_id)
        if not embeddings_data:
            embeddings_data = self._generate_embeddings_individual(chunks, document_id)
        return embeddings_data

    async def _store_embeddings(self, embeddings_data: List[tuple]) -> None:
        """
        Store embeddings and trigger reindexing.
        
        Args:
            embeddings_data (List[tuple]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        if not embeddings_data:
            return

        await self.vector_ops.batch_insert_embeddings(embeddings_data)
        try:
            await self.index_manager.auto_reindex_on_embedding_change(
                table_name="embeddings", column_name="embedding"
            )
        except Exception as e:
            logger.warning(f"Auto-reindexing failed (non-critical): {str(e)}")

    def ingest_document(
        self,
        title: str,
        content: Optional[str] = None,
        file_path: Optional[str] = None,
        tenant_id: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
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
            title (str): Input parameter for this operation.
            content (Optional[str]): Content text.
            file_path (Optional[str]): Path of the input file.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            source (Optional[str]): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            str: Returned text value.
        
        Raises:
            ValueError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        import asyncio

        if file_path:
            # Call async method from sync context
            content, metadata, source = asyncio.run(self._load_document_from_file(file_path, metadata))

        if not content:
            raise ValueError("Either 'content' or 'file_path' must be provided")

        # Call async method from sync context
        document_id = asyncio.run(self._insert_document_to_db(title, content, metadata, source, tenant_id))

        chunks = self.document_processor.chunk_document(
            content=content, document_id=document_id, metadata=metadata
        )

        if not chunks:
            return document_id

        embeddings_data = self._process_embeddings(chunks, document_id)
        asyncio.run(self._store_embeddings(embeddings_data))

        return document_id

    def _rewrite_query(self, query: str) -> str:
        """
        Rewrite query to improve retrieval quality.
        
        Simple query rewriting: expand abbreviations, normalize terms.
                                Can be extended with LLM-based query expansion.
        
        Args:
            query (str): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
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
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query the RAG system with query optimization.
        
        Args:
            query (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            top_k (int): Input parameter for this operation.
            threshold (float): Input parameter for this operation.
            max_tokens (int): Input parameter for this operation.
            use_query_rewriting (bool): Input parameter for this operation.
            retrieval_strategy (str): Input parameter for this operation.
            user_id (Optional[str]): User identifier (used for auditing or personalization).
            conversation_id (Optional[str]): Conversation identifier (used for context or memory).
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        import asyncio

        # Retrieve relevant memories if memory is enabled
        memories = []
        memory_context = ""
        if self.memory:
            memories = asyncio.run(self.memory.retrieve(
                query=query, limit=5
            ))
            if memories:
                memory_context = "\n".join([f"- {mem.content}" for mem in memories[:3]])

        # Query rewriting for optimization
        original_query = query
        if use_query_rewriting:
            query = self._rewrite_query(query)

        # Include tenant_id in cache key for tenant isolation
        cache_key = f"rag:query:{tenant_id or 'global'}:{query}:{top_k}:{threshold}:{max_tokens}:{retrieval_strategy}"
        cached = asyncio.run(self.cache.get(cache_key, tenant_id=tenant_id))
        if cached:
            return cached

        try:
            # Use hybrid retrieval if specified
            if retrieval_strategy == "hybrid":
                retrieved_docs = self.retriever.retrieve_hybrid(
                    query=query, top_k=top_k, threshold=threshold, tenant_id=tenant_id
                )
            else:
                retrieved_docs = self.retriever.retrieve(
                    query=query, top_k=top_k, threshold=threshold, tenant_id=tenant_id
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
                max_tokens=max_tokens,
            )

            result = {
                "answer": answer,
                "retrieved_documents": retrieved_docs,
                "num_documents": len(retrieved_docs),
                "query_used": query if use_query_rewriting else original_query,
                "original_query": original_query,
                "memory_used": len(memories) if memories else 0,
            }

            # Store in cache
            asyncio.run(self.cache.set(cache_key, result, ttl=300, tenant_id=tenant_id))

            # Store in memory for future context
            if self.memory:
                asyncio.run(self.memory.store(
                    content=f"Query: {original_query}\nAnswer: {answer}",
                    memory_type=MemoryType.EPISODIC,
                    importance=0.7,
                    metadata={
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "tenant_id": tenant_id,
                        "num_documents": len(retrieved_docs),
                    },
                ))

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
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query the RAG system asynchronously.
        
        Args:
            query (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            top_k (int): Input parameter for this operation.
            threshold (float): Input parameter for this operation.
            max_tokens (int): Input parameter for this operation.
            use_query_rewriting (bool): Input parameter for this operation.
            retrieval_strategy (str): Input parameter for this operation.
            user_id (Optional[str]): User identifier (used for auditing or personalization).
            conversation_id (Optional[str]): Conversation identifier (used for context or memory).
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        # RAG QUERY PROCESS: Step-by-step retrieval and generation

        # STEP 1: Retrieve relevant conversation memories (if memory enabled)
        # This provides context from previous conversations to improve answer relevance
        # Cost impact: Memory retrieval is free (no API call), improves answer quality
        memories = []
        memory_context = ""
        if self.memory:
            memories = await self.memory.retrieve(
                query=query, limit=5
            )
            if memories:
                memory_context = "\n".join([f"- {mem.content}" for mem in memories[:3]])

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
        cached = await self.cache.get(cache_key, tenant_id=tenant_id)
        if cached:
            return cached

        try:
            # STEP 4: Document retrieval (vector search in database)
            # This finds the most relevant document chunks for the query
            # Cost: ~$0.0001-0.001 per query (embedding generation for query)
            if retrieval_strategy == "hybrid":
                # Hybrid: Combines vector search + keyword search for better results
                retrieved_docs = self.retriever.retrieve_hybrid(
                    query=query, top_k=top_k, threshold=threshold, tenant_id=tenant_id
                )
            else:
                # Vector-only: Fast, semantic similarity search
                retrieved_docs = self.retriever.retrieve(
                    query=query, top_k=top_k, threshold=threshold, tenant_id=tenant_id
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
                max_tokens=max_tokens,  # Limit response length to control cost
            )

            result = {
                "answer": answer,
                "retrieved_documents": retrieved_docs,
                "num_documents": len(retrieved_docs),
                "query_used": query if use_query_rewriting else original_query,
                "original_query": original_query,
                "memory_used": len(memories) if memories else 0,
            }

            # Store in cache
            await self.cache.set(cache_key, result, ttl=300, tenant_id=tenant_id)

            # Store in memory for future context
            if self.memory:
                await self.memory.store(
                    content=f"Query: {original_query}\nAnswer: {answer}",
                    memory_type=MemoryType.EPISODIC,
                    importance=0.7,
                    metadata={
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "tenant_id": tenant_id,
                        "num_documents": len(retrieved_docs),
                    },
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

    async def _try_batch_embeddings(
        self, chunk_texts: List[str], document_id: str
    ) -> Optional[List[tuple]]:
        """
        Try to generate embeddings in batch, return None if it fails.
        
        Args:
            chunk_texts (List[str]): Input parameter for this operation.
            document_id (str): Input parameter for this operation.
        
        Returns:
            Optional[List[tuple]]: List result of the operation.
        """
        try:
            embedding_response = await self.gateway.embed_async(
                texts=chunk_texts, model=self.embedding_model
            )
            
            embeddings_data = []
            if embedding_response.embeddings:
                for i, embedding in enumerate(embedding_response.embeddings):
                    if i < len(chunk_texts):
                        embeddings_data.append((int(document_id), embedding, self.embedding_model))
            return embeddings_data
        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.warning(f"Batch embedding failed, falling back to individual processing: {e}")
            return None

    async def _fallback_individual_embeddings(
        self, chunks: List[Any], document_id: str
    ) -> List[tuple]:
        """
        Generate embeddings individually as fallback.
        
        Args:
            chunks (List[Any]): Input parameter for this operation.
            document_id (str): Input parameter for this operation.
        
        Returns:
            List[tuple]: List result of the operation.
        """
        embeddings_data = []
        for chunk in chunks:
            try:
                embedding_response = await self.gateway.embed_async(
                    texts=[chunk.content], model=self.embedding_model
                )
                if embedding_response.embeddings and len(embedding_response.embeddings) > 0:
                    embedding = embedding_response.embeddings[0]
                    embeddings_data.append((int(document_id), embedding, self.embedding_model))
            except (ConnectionError, TimeoutError, ValueError) as chunk_error:
                logger.warning(f"Failed to embed chunk, skipping: {chunk_error}")
                continue
            except Exception as chunk_error:
                logger.error(f"Unexpected error embedding chunk: {chunk_error}", exc_info=True)
                continue
        return embeddings_data

    async def _store_embeddings_and_reindex(self, embeddings_data: List[tuple]) -> None:
        """
        Store embeddings and trigger reindexing.
        
        Args:
            embeddings_data (List[tuple]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        if embeddings_data:
            await self.vector_ops.batch_insert_embeddings(embeddings_data)
            try:
                await self.index_manager.auto_reindex_on_embedding_change(
                    table_name="embeddings", column_name="embedding"
                )
            except Exception as e:
                logger.warning(f"Auto-reindexing failed (non-critical): {str(e)}")

    async def ingest_document_async(
        self,
        title: str,
        content: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Ingest a document into the RAG system asynchronously with batch processing.
        
        Args:
            title (str): Input parameter for this operation.
            content (str): Content text.
            source (Optional[str]): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            str: Returned text value.
        """
        # Insert document
        query = """
        INSERT INTO documents (title, content, metadata, source)
        VALUES (%s, %s, %s::jsonb, %s)
        RETURNING id;
        """

        import json

        metadata_json = json.dumps(metadata or {})

        result = await self.db.execute_query(
            query, (title, content, metadata_json, source), fetch_one=True
        )

        document_id = str(result["id"])

        # Process and chunk document
        chunks = self.document_processor.chunk_document(
            content=content, document_id=document_id, metadata=metadata
        )

        if not chunks:
            return document_id

        # Batch processing: Collect all chunk texts
        chunk_texts = [chunk.content for chunk in chunks]

        # Try batch embeddings first, fall back to individual if needed
        embeddings_data = await self._try_batch_embeddings(chunk_texts, document_id)
        if embeddings_data is None:
            embeddings_data = await self._fallback_individual_embeddings(chunks, document_id)

        # Store embeddings and reindex
        await self._store_embeddings_and_reindex(embeddings_data)

        return document_id

    def ingest_documents_batch(
        self, documents: List[Dict[str, Any]], batch_size: int = 10
    ) -> List[str]:
        """
        Ingest multiple documents in batch with optimized processing.
        
        Args:
            documents (List[Dict[str, Any]]): Input parameter for this operation.
            batch_size (int): Input parameter for this operation.
        
        Returns:
            List[str]: List result of the operation.
        """
        document_ids = []

        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]

            # Process each document in the batch
            for doc in batch:
                try:
                    doc_id = self.ingest_document(
                        title=doc.get("title", ""),
                        content=doc.get("content", ""),
                        source=doc.get("source"),
                        metadata=doc.get("metadata"),
                    )
                    document_ids.append(doc_id)
                except (ValueError, ConnectionError) as e:
                    # Log specific errors but continue with other documents
                    logger.warning(f"Failed to ingest document in batch, skipping: {e}")
                    continue
                except Exception as e:
                    # Log unexpected errors but continue processing
                    logger.error(
                        f"Unexpected error ingesting document in batch: {e}", exc_info=True
                    )
                    continue

        return document_ids

    async def ingest_documents_batch_async(
        self, documents: List[Dict[str, Any]], batch_size: int = 10
    ) -> List[str]:
        """
        Ingest multiple documents in batch asynchronously with optimized processing.
        
        Args:
            documents (List[Dict[str, Any]]): Input parameter for this operation.
            batch_size (int): Input parameter for this operation.
        
        Returns:
            List[str]: List result of the operation.
        """
        import asyncio

        document_ids = []

        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]

            # Process batch concurrently
            tasks = []
            for doc in batch:
                task = self.ingest_document_async(
                    title=doc.get("title", ""),
                    content=doc.get("content", ""),
                    source=doc.get("source"),
                    metadata=doc.get("metadata"),
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

    async def create_index(
        self,
        index_type: IndexType = IndexType.IVFFLAT,
        distance: IndexDistance = IndexDistance.COSINE,
        **kwargs: Any,
    ) -> str:
        """
        Create a vector index for optimal search performance.
        
        Args:
            index_type (IndexType): Input parameter for this operation.
            distance (IndexDistance): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            str: The name of the created or existing index.
        """
        return await self.index_manager.create_index(
            table_name="embeddings",
            column_name="embedding",
            index_type=index_type,
            distance=distance,
            **kwargs,
        )

    async def reindex(self, concurrently: bool = True) -> List[str]:
        """
        Reindex all vector indexes (useful after embedding model changes or bulk updates).
        
        Args:
            concurrently (bool): Input parameter for this operation.
        
        Returns:
            List[str]: List result of the operation.
        """
        return await self.index_manager.reindex_table(table_name="embeddings", concurrently=concurrently)

    async def get_index_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all vector indexes.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        return await self.index_manager.list_indexes(table_name="embeddings")

    def _build_document_update_query(
        self, title: Optional[str], metadata: Optional[Dict[str, Any]]
    ) -> tuple:
        """
        Build SQL query and params for document metadata updates.
        
        Args:
            title (Optional[str]): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            tuple: Result of the operation.
        """
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = %s")
            params.append(title)
        
        if metadata is not None:
            import json
            updates.append("metadata = %s::jsonb")
            params.append(json.dumps(metadata))
        
        return updates, params

    async def _generate_and_store_embeddings(
        self, chunks: List[Any], document_id: str
    ) -> None:
        """
        Generate embeddings for chunks and store them.
        
        Args:
            chunks (List[Any]): Input parameter for this operation.
            document_id (str): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        if not chunks:
            return
        
        chunk_texts = [chunk.content for chunk in chunks]
        embedding_response = await self.gateway.embed_async(
            texts=chunk_texts, model=self.embedding_model
        )
        
        if embedding_response.embeddings:
            embeddings_data = []
            for i, embedding in enumerate(embedding_response.embeddings):
                if i < len(chunks):
                    embeddings_data.append((int(document_id), embedding, self.embedding_model))
            
            if embeddings_data:
                await self.vector_ops.batch_insert_embeddings(embeddings_data)

    async def _update_document_content(
        self, document_id: str, content: str, metadata: Optional[Dict[str, Any]]
    ) -> None:
        """
        Re-process and update document content.
        
        Args:
            document_id (str): Input parameter for this operation.
            content (str): Content text.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            None: Result of the operation.
        """
        # Delete old chunks and embeddings
        await self._delete_document_chunks(document_id)
        
        # Re-process and re-embed
        chunks = self.document_processor.chunk_document(
            content=content, document_id=document_id, metadata=metadata
        )
        
        await self._generate_and_store_embeddings(chunks, document_id)
        
        # Auto-reindex
        try:
            await self.index_manager.auto_reindex_on_embedding_change(
                table_name="embeddings", column_name="embedding"
            )
        except Exception as e:
            logger.warning(f"Auto-reindexing failed (non-critical): {str(e)}")
        
        # Update content in database
        query = "UPDATE documents SET content = %s WHERE id = %s;"
        await self.db.execute_query(query, (content, document_id))

    async def update_document(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update an existing document in the RAG system.
        
        Args:
            document_id (str): Input parameter for this operation.
            title (Optional[str]): Input parameter for this operation.
            content (Optional[str]): Content text.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        try:
            # Update document metadata
            updates, params = self._build_document_update_query(title, metadata)
            
            if updates:
                query = f"""
                UPDATE documents
                SET {', '.join(updates)}
                WHERE id = %s;
                """
                params.append(document_id)
                await self.db.execute_query(query, tuple(params))

            # If content changed, re-process document
            if content is not None:
                await self._update_document_content(document_id, content, metadata)

            # Invalidate cache for this document
            await self.cache.invalidate_pattern(f"rag:doc:{document_id}")

            return True
        except (ConnectionError, ValueError) as e:
            # Log specific errors
            logger.error(f"Error updating document {document_id}: {e}")
            return False
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error updating document {document_id}: {e}", exc_info=True)
            return False

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its associated chunks/embeddings from the RAG system.
        
        Args:
            document_id (str): Input parameter for this operation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        try:
            # Delete document chunks and embeddings
            await self._delete_document_chunks(document_id)

            # Delete document
            query = "DELETE FROM documents WHERE id = %s;"
            await self.db.execute_query(query, (document_id,))

            # Invalidate cache
            await self.cache.invalidate_pattern(f"rag:doc:{document_id}")
            await self.cache.invalidate_pattern("rag:query:*")

            return True
        except (ConnectionError, ValueError) as e:
            # Log specific errors
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error deleting document {document_id}: {e}", exc_info=True)
            return False

    async def _delete_document_chunks(self, document_id: str) -> None:
        """
        Delete all chunks and embeddings for a document.
        
        Args:
            document_id (str): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        # Delete embeddings
        query = "DELETE FROM embeddings WHERE document_id = %s;"
        await self.db.execute_query(query, (document_id,))

        # Note: If you have a chunks table, delete from there too
        # query = "DELETE FROM chunks WHERE document_id = %s;"
        # await self.db.execute_query(query, (document_id,))
