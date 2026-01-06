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
        
        # Generate embeddings and store
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

