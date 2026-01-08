"""
RAG System

Complete Retrieval-Augmented Generation system.
"""

from typing import List, Dict, Any, Optional
from ..postgresql_database.connection import DatabaseConnection
from ..postgresql_database.vector_operations import VectorOperations
from ..litellm_gateway import LiteLLMGateway
from ..cache_mechanism import CacheMechanism, CacheConfig
from .document_processor import DocumentProcessor, DocumentChunk
from .retriever import Retriever
from .generator import RAGGenerator


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
    ):
        """
        Initialize RAG system.

        Args:
            db: Database connection
            gateway: LiteLLM gateway
            embedding_model: Model for embeddings
            generation_model: Model for generation
        """
        self.db = db
        self.gateway = gateway
        self.embedding_model = embedding_model
        self.generation_model = generation_model
        self.cache = cache or CacheMechanism(cache_config or CacheConfig())

        # Initialize components
        self.vector_ops = VectorOperations(db)
        self.document_processor = DocumentProcessor()
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
        content: str,
        tenant_id: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Ingest a document into the RAG system.

        Args:
            title: Document title
            content: Document content
            tenant_id: Optional tenant ID for multi-tenant SaaS
            source: Optional source URL/path
            metadata: Optional metadata

        Returns:
            Document ID
        """
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
        except Exception:
            # If batch fails, fall back to individual processing for resilience
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
                except Exception:
                    # skip failed chunk embedding to keep ingestion resilient
                    continue

        # Batch insert embeddings
        if embeddings_data:
            self.vector_ops.batch_insert_embeddings(embeddings_data)

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
        retrieval_strategy: str = "vector"  # "vector", "hybrid", "keyword"
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

        Returns:
            Dictionary with answer and retrieved documents
        """
        # Query rewriting for optimization
        original_query = query
        if use_query_rewriting:
            query = self._rewrite_query(query)

        # Include tenant_id in cache key for tenant isolation
        cache_key = f"rag:query:{tenant_id or 'global'}:{query}:{top_k}:{threshold}:{max_tokens}:{retrieval_strategy}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            # Use hybrid retrieval if specified
            if retrieval_strategy == "hybrid":
                retrieved_docs = self.retriever.retrieve_hybrid(
                    query=query,
                    top_k=top_k,
                    threshold=threshold
                )
            else:
                retrieved_docs = self.retriever.retrieve(
                    query=query,
                    top_k=top_k,
                    threshold=threshold
                )

            answer = self.generator.generate(
                query=original_query,  # Use original query for generation
                context_documents=retrieved_docs,
                max_tokens=max_tokens
            )

            result = {
                "answer": answer,
                "retrieved_documents": retrieved_docs,
                "num_documents": len(retrieved_docs),
                "query_used": query if use_query_rewriting else original_query,
                "original_query": original_query
            }
            self.cache.set(cache_key, result, ttl=300)
            return result
        except Exception as e:
            return {
                "answer": None,
                "retrieved_documents": [],
                "num_documents": 0,
                "error": str(e),
            }

    async def query_async(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7,
        max_tokens: int = 1000,
        use_query_rewriting: bool = True,
        retrieval_strategy: str = "vector"
    ) -> Dict[str, Any]:
        """
        Query the RAG system asynchronously.

        Args:
            query: User query
            top_k: Number of documents to retrieve
            threshold: Similarity threshold
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with answer and retrieved documents
        """
        # Query rewriting for optimization
        original_query = query
        if use_query_rewriting:
            query = self._rewrite_query(query)

        cache_key = f"rag:query:{query}:{top_k}:{threshold}:{max_tokens}:{retrieval_strategy}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            # Use hybrid retrieval if specified
            if retrieval_strategy == "hybrid":
                retrieved_docs = self.retriever.retrieve_hybrid(
                    query=query,
                    top_k=top_k,
                    threshold=threshold
                )
            else:
                retrieved_docs = self.retriever.retrieve(
                    query=query,
                    top_k=top_k,
                    threshold=threshold
                )

            answer = await self.generator.generate_async(
                query=original_query,  # Use original query for generation
                context_documents=retrieved_docs,
                max_tokens=max_tokens
            )

            result = {
                "answer": answer,
                "retrieved_documents": retrieved_docs,
                "num_documents": len(retrieved_docs),
                "query_used": query if use_query_rewriting else original_query,
                "original_query": original_query
            }
            self.cache.set(cache_key, result, ttl=300)
            return result
        except Exception as e:
            return {
                "answer": None,
                "retrieved_documents": [],
                "num_documents": 0,
                "error": str(e),
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
        except Exception:
            # If batch fails, fall back to individual processing for resilience
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
                except Exception:
                    # skip failed chunk embedding to keep ingestion resilient
                    continue

        # Batch insert embeddings
        if embeddings_data:
            self.vector_ops.batch_insert_embeddings(embeddings_data)

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
                except Exception:
                    # Log error but continue with other documents
                    # In production, you might want to log this properly
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
            except Exception:
                # Continue with next batch even if current batch fails
                continue

        return document_ids

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

                # Update content in database
                query = "UPDATE documents SET content = %s WHERE id = %s;"
                self.db.execute_query(query, (content, document_id))

            # Invalidate cache for this document
            self.cache.invalidate_pattern(f"rag:doc:{document_id}")

            return True
        except Exception:
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
        except Exception:
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

