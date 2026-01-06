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
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Ingest a document into the RAG system.
        
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
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Query the RAG system.
        """
        cache_key = f"rag:query:{query}:{top_k}:{threshold}:{max_tokens}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            retrieved_docs = self.retriever.retrieve(
                query=query,
                top_k=top_k,
                threshold=threshold
            )

            answer = self.generator.generate(
                query=query,
                context_documents=retrieved_docs,
                max_tokens=max_tokens
            )

            result = {
                "answer": answer,
                "retrieved_documents": retrieved_docs,
                "num_documents": len(retrieved_docs)
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
        max_tokens: int = 1000
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
        cache_key = f"rag:query:{query}:{top_k}:{threshold}:{max_tokens}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            retrieved_docs = self.retriever.retrieve(
                query=query,
                top_k=top_k,
                threshold=threshold
            )
            
            answer = await self.generator.generate_async(
                query=query,
                context_documents=retrieved_docs,
                max_tokens=max_tokens
            )
            
            result = {
                "answer": answer,
                "retrieved_documents": retrieved_docs,
                "num_documents": len(retrieved_docs)
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

