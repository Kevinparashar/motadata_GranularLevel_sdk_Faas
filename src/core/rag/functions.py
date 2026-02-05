"""
RAG System - High-Level Functions

Factory functions, convenience functions, and utilities for RAG system.
"""


from typing import Any, Awaitable, Callable, Dict, List, Optional

from ..litellm_gateway import LiteLLMGateway
from ..postgresql_database.connection import DatabaseConnection
from .document_processor import DocumentProcessor
from .rag_system import RAGSystem

# ============================================================================
# Factory Functions
# ============================================================================


def create_rag_system(
    db: DatabaseConnection,
    gateway: LiteLLMGateway,
    embedding_model: str = "text-embedding-3-small",
    generation_model: str = "gpt-4",
    enable_memory: bool = True,
    memory_config: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> RAGSystem:
    """
    Create and configure a RAG system with default settings.

    Args:
        db: Database connection instance
        gateway: LiteLLM Gateway instance
        embedding_model: Model for embeddings
        generation_model: Model for generation
        enable_memory: Enable memory for conversation context
        memory_config: Optional memory configuration
        **kwargs: Additional RAG system configuration

    Returns:
        Configured RAGSystem instance

    Example:
        >>> db = DatabaseConnection(...)
        >>> gateway = LiteLLMGateway()
        >>> rag = create_rag_system(db, gateway, enable_memory=True)
    """
    return RAGSystem(
        db=db,
        gateway=gateway,
        embedding_model=embedding_model,
        generation_model=generation_model,
        enable_memory=enable_memory,
        memory_config=memory_config,
        **kwargs,
    )


def create_document_processor(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    chunking_strategy: str = "fixed",
    min_chunk_size: int = 50,
    max_chunk_size: int = 2000,
    enable_preprocessing: bool = True,
    enable_metadata_extraction: bool = True,
    metadata_schema: Optional[Any] = None,
    enable_multimodal: bool = True,
    gateway: Optional[LiteLLMGateway] = None,
) -> DocumentProcessor:
    """
    Create a document processor with specified configuration.

    Args:
        chunk_size: Size of chunks in characters
        chunk_overlap: Overlap between chunks
        chunking_strategy: Chunking strategy ("fixed", "sentence", "paragraph", "semantic")
        min_chunk_size: Minimum chunk size to keep (filters out tiny chunks)
        max_chunk_size: Maximum chunk size (splits oversized chunks)
        enable_preprocessing: Enable text preprocessing (normalization, cleaning)
        enable_metadata_extraction: Enable automatic metadata extraction
        metadata_schema: Optional metadata schema for validation

    Returns:
        DocumentProcessor instance

    Example:
        >>> processor = create_document_processor(
        ...     chunk_size=500,
        ...     chunking_strategy="sentence",
        ...     enable_preprocessing=True,
        ...     enable_metadata_extraction=True
        ... )
    """
    return DocumentProcessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunking_strategy=chunking_strategy,
        min_chunk_size=min_chunk_size,
        max_chunk_size=max_chunk_size,
        enable_preprocessing=enable_preprocessing,
        enable_metadata_extraction=enable_metadata_extraction,
        metadata_schema=metadata_schema,
        enable_multimodal=enable_multimodal,
        gateway=gateway,
    )


# ============================================================================
# High-Level Convenience Functions
# ============================================================================


def quick_rag_query(
    rag_system: RAGSystem,
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
    Quick RAG query without manual setup (high-level convenience).

    Args:
        rag_system: RAGSystem instance
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

    Example:
        >>> result = quick_rag_query(rag, "What is AI?")
        >>> print(result["answer"])
    """
    return rag_system.query(
        query=query,
        tenant_id=tenant_id,
        top_k=top_k,
        threshold=threshold,
        max_tokens=max_tokens,
        use_query_rewriting=use_query_rewriting,
        retrieval_strategy=retrieval_strategy,
        user_id=user_id,
        conversation_id=conversation_id,
    )


async def quick_rag_query_async(
    rag_system: RAGSystem,
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
    Quick async RAG query (high-level convenience).

    Args:
        rag_system: RAGSystem instance
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

    Example:
        >>> result = await quick_rag_query_async(rag, "What is AI?")
        >>> print(result["answer"])
    """
    return await rag_system.query_async(
        query=query,
        tenant_id=tenant_id,
        top_k=top_k,
        threshold=threshold,
        max_tokens=max_tokens,
        use_query_rewriting=use_query_rewriting,
        retrieval_strategy=retrieval_strategy,
        user_id=user_id,
        conversation_id=conversation_id,
    )


def ingest_document_simple(
    rag_system: RAGSystem,
    title: str,
    content: str,
    tenant_id: Optional[str] = None,
    source: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Ingest a document with simplified interface (high-level convenience).

    Args:
        rag_system: RAGSystem instance
        title: Document title
        content: Document content
        source: Optional source URL/path
        metadata: Optional metadata

    Returns:
        Document ID

    Example:
        >>> doc_id = ingest_document_simple(
        ...     rag,
        ...     "AI Guide",
        ...     "Artificial Intelligence is..."
        ... )
    """
    return rag_system.ingest_document(
        title=title, content=content, tenant_id=tenant_id, source=source, metadata=metadata
    )


async def ingest_document_simple_async(
    rag_system: RAGSystem,
    title: str,
    content: str,
    source: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Ingest a document asynchronously with simplified interface.

    Args:
        rag_system: RAGSystem instance
        title: Document title
        content: Document content
        source: Optional source URL/path
        metadata: Optional metadata

    Returns:
        Document ID

    Example:
        >>> doc_id = await ingest_document_simple_async(
        ...     rag,
        ...     "AI Guide",
        ...     "Artificial Intelligence is..."
        ... )
    """
    return await rag_system.ingest_document_async(
        title=title, content=content, source=source, metadata=metadata
    )


def batch_ingest_documents(
    rag_system: RAGSystem, documents: List[Dict[str, Any]], batch_size: int = 10
) -> List[str]:
    """
    Batch ingest multiple documents (high-level convenience).

    Args:
        rag_system: RAGSystem instance
        documents: List of document dicts with keys: title, content, source (optional), metadata (optional)
        batch_size: Number of documents to process in each batch

    Returns:
        List of document IDs

    Example:
        >>> docs = [
        ...     {"title": "Doc1", "content": "..."},
        ...     {"title": "Doc2", "content": "..."}
        ... ]
        >>> doc_ids = batch_ingest_documents(rag, docs)
    """
    return rag_system.ingest_documents_batch(documents=documents, batch_size=batch_size)


async def batch_ingest_documents_async(
    rag_system: RAGSystem, documents: List[Dict[str, Any]], batch_size: int = 10
) -> List[str]:
    """
    Batch ingest multiple documents asynchronously (high-level convenience).

    Args:
        rag_system: RAGSystem instance
        documents: List of document dicts
        batch_size: Number of documents to process in each batch

    Returns:
        List of document IDs

    Example:
        >>> doc_ids = await batch_ingest_documents_async(rag, docs)
    """
    return await rag_system.ingest_documents_batch_async(documents=documents, batch_size=batch_size)


# ============================================================================
# Utility Functions
# ============================================================================


def batch_process_documents(
    documents: List[Dict[str, Any]],
    processor: Callable[[Dict[str, Any]], Awaitable[Any]],
    batch_size: int = 10,
    max_concurrent: int = 5,
) -> List[Any]:
    """
    Process documents in batches with concurrency control.

    Args:
        documents: List of documents to process
        processor: Async function to process each document
        batch_size: Size of each batch
        max_concurrent: Maximum concurrent batches

    Returns:
        List of results

    Example:
        >>> results = batch_process_documents(
        ...     documents,
        ...     lambda doc: process_document(doc),
        ...     batch_size=10
        ... )
    """
    import asyncio
    from asyncio import Semaphore

    semaphore = Semaphore(max_concurrent)

    async def _process_batch(batch: List[Dict[str, Any]]) -> List[Any]:
        async with semaphore:
            tasks = [processor(doc) for doc in batch]
            return await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_all() -> List[Any]:
        results: List[Any] = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            batch_results = await _process_batch(batch)
            results.extend(batch_results)
        return results

    return asyncio.run(_process_all())


def update_document_simple(
    rag_system: RAGSystem,
    document_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Update a document in the RAG system (high-level convenience).

    Args:
        rag_system: RAGSystem instance
        document_id: Document ID to update
        title: Optional new title
        content: Optional new content (will re-process and re-embed)
        metadata: Optional new metadata

    Returns:
        True if update successful, False otherwise

    Example:
        >>> success = update_document_simple(
        ...     rag, "doc-123",
        ...     title="Updated Title",
        ...     content="Updated content"
        ... )
    """
    import asyncio
    return asyncio.run(rag_system.update_document(document_id, title, content, metadata))


def delete_document_simple(rag_system: RAGSystem, document_id: str) -> bool:
    """
    Delete a document from the RAG system (high-level convenience).

    Args:
        rag_system: RAGSystem instance
        document_id: Document ID to delete

    Returns:
        True if deletion successful, False otherwise

    Example:
        >>> success = delete_document_simple(rag, "doc-123")
    """
    import asyncio
    return asyncio.run(rag_system.delete_document(document_id))


__all__ = [
    # Factory functions
    "create_rag_system",
    "create_document_processor",
    # High-level convenience functions
    "quick_rag_query",
    "quick_rag_query_async",
    "ingest_document_simple",
    "ingest_document_simple_async",
    "batch_ingest_documents",
    "batch_ingest_documents_async",
    "update_document_simple",
    "delete_document_simple",
    # Utility functions
    "batch_process_documents",
]
