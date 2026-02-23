# Copyright (c) 2024. All rights reserved.
# This source code is licensed under the MIT license and a copy
# of the license can be found in the LICENSE file in the root directory.

"""
RAG System Enhancements

Advanced features: re-ranking, versioning, relevance scoring, incremental updates, validation, real-time sync.
"""


from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

# SQL constants
TENANT_FILTER_SQL = " AND tenant_id = %s"

if TYPE_CHECKING:
    from ...faas.shared.dal.document_dal import DocumentDAL  # type: ignore[import-untyped]
    from ...faas.shared.dal.document_version_dal import DocumentVersionDAL  # type: ignore[import-untyped]



@dataclass
class DocumentVersion:
    """Document version information."""

    version: int
    document_id: str
    content_hash: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelevanceScore:
    """Relevance score for a retrieved document."""

    document_id: str
    score: float
    method: str  # "similarity", "keyword", "hybrid", "reranked"
    details: Dict[str, Any] = field(default_factory=dict)


class DocumentReranker:
    """
    Advanced re-ranking algorithms for retrieved documents.
    """

    def __init__(self, rerank_method: str = "cross_encoder"):
        """
        Initialize re-ranker.
        
        Args:
            rerank_method (str): Input parameter for this operation.
        """
        self.rerank_method = rerank_method

    def rerank(
        self, query: str, documents: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Re-rank documents based on query relevance.
        
        Args:
            query (str): Input parameter for this operation.
            documents (List[Dict[str, Any]]): Input parameter for this operation.
            top_k (int): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        if not documents:
            return []

        # Simple re-ranking: boost documents with query terms in title
        reranked = []
        for doc in documents:
            score = doc.get("score", 0.0)
            title = doc.get("title", "").lower()
            content = doc.get("content", "").lower()
            query_lower = query.lower()

            # Boost score if query terms appear in title
            query_terms = query_lower.split()
            title_matches = sum(1 for term in query_terms if term in title)
            content_matches = sum(1 for term in query_terms if term in content)

            # Re-rank score
            rerank_score = score * 1.2 if title_matches > 0 else score
            rerank_score += (title_matches * 0.1) + (content_matches * 0.05)

            reranked.append({**doc, "rerank_score": rerank_score, "original_score": score})

        # Sort by rerank score
        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

        return reranked[:top_k]

    def rerank_with_cross_encoder(
        self, query: str, documents: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Re-rank using cross-encoder model (requires sentence-transformers).
        
        Args:
            query (str): Input parameter for this operation.
            documents (List[Dict[str, Any]]): Input parameter for this operation.
            top_k (int): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        try:
            from sentence_transformers import CrossEncoder  # type: ignore[import-not-found]

            # Initialize cross-encoder (lazy loading)
            if not hasattr(self, "_cross_encoder"):
                self._cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

            # Prepare pairs for scoring
            pairs = [[query, doc.get("content", "")[:512]] for doc in documents]

            # Get scores
            scores = self._cross_encoder.predict(pairs)

            # Combine with documents
            reranked = []
            for doc, score in zip(documents, scores):
                reranked.append(
                    {**doc, "rerank_score": float(score), "original_score": doc.get("score", 0.0)}
                )

            # Sort by rerank score
            reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

            return reranked[:top_k]

        except ImportError:
            # Fallback to simple re-ranking
            return self.rerank(query, documents, top_k)


class DocumentVersioning:
    """
    Document versioning for better management and retrieval.
    """

    def __init__(self, db: Any, document_version_dal: Optional[Any] = None):
        """
        Initialize document versioning.
        
        Args:
            db: Database connection/handle.
            document_version_dal: Optional DocumentVersionDAL instance for database persistence.
        """
        self.db = db
        # Initialize DocumentVersionDAL if not provided
        if document_version_dal is None:
            from ...faas.shared.dal.document_version_dal import DocumentVersionDAL
            self.document_version_dal = DocumentVersionDAL(db)
        else:
            self.document_version_dal = document_version_dal
        # Tables are assumed to exist (managed by migrations/DAL)

    async def initialize(self) -> None:
        """
        Initialize the versioning system (async setup).
        
        This method is kept for backward compatibility but no longer creates tables.
        Tables are assumed to exist (managed by migrations/DAL).
        """
        # Tables are assumed to exist (managed by migrations/DAL)
        pass

    async def create_version(
        self,
        document_id: str,
        content: str,
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentVersion:
        """
        Create a new document version.
        
        Args:
            document_id (str): Input parameter for this operation.
            content (str): Content text.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            DocumentVersion: Result of the operation.
        """
        # Use DAL to create version
        version_data = await self.document_version_dal.create_version(
            document_id=document_id,
            content=content,
            tenant_id=tenant_id,
            metadata=metadata,
        )

        return DocumentVersion(
            version=version_data["version"],
            document_id=version_data["document_id"],
            content_hash=version_data["content_hash"],
            created_at=version_data["created_at"],
            metadata=version_data["metadata"],
        )

    async def get_versions(
        self, document_id: str, tenant_id: Optional[str] = None
    ) -> List[DocumentVersion]:
        """
        Get all versions of a document.
        
        Args:
            document_id (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            List[DocumentVersion]: List result of the operation.
        """
        # Use DAL to get versions
        results = await self.document_version_dal.get_versions(document_id, tenant_id)

        return [
            DocumentVersion(
                version=r["version"],
                document_id=document_id,
                content_hash=r["content_hash"],
                created_at=r["created_at"],
                metadata=r.get("metadata", {}),
            )
            for r in results
        ]


class RelevanceScorer:
    """
    Explicit relevance scoring for retrieved documents.
    """

    def __init__(self):
        """Initialize relevance scorer."""
        pass

    def score(self, query: str, document: Dict[str, Any], method: str = "hybrid") -> RelevanceScore:
        """
        Score document relevance to query.
        
        Args:
            query (str): Input parameter for this operation.
            document (Dict[str, Any]): Input parameter for this operation.
            method (str): Input parameter for this operation.
        
        Returns:
            RelevanceScore: Result of the operation.
        """
        score = 0.0
        details = {}

        if method in ["similarity", "hybrid"]:
            similarity_score = document.get("score", 0.0)
            score += similarity_score * 0.6
            details["similarity_score"] = similarity_score

        if method in ["keyword", "hybrid"]:
            # Keyword matching score
            query_terms = query.lower().split()
            title = document.get("title", "").lower()
            content = document.get("content", "").lower()

            title_matches = sum(1 for term in query_terms if term in title)
            content_matches = sum(1 for term in query_terms if term in content)

            keyword_score = (title_matches * 0.3) + (content_matches * 0.1)
            score += keyword_score
            details["keyword_score"] = keyword_score
            details["title_matches"] = title_matches
            details["content_matches"] = content_matches

        return RelevanceScore(
            document_id=document.get("id", ""),
            score=min(1.0, score),  # Normalize to 0-1
            method=method,
            details=details,
        )


class IncrementalUpdater:
    """
    Incremental updates to avoid full re-embedding when documents are updated.
    """

    def __init__(self, db: Any, vector_ops: Any, document_dal: Optional[Any] = None):
        """
        Initialize incremental updater.
        
        Args:
            db: Database connection/handle.
            vector_ops: Vector operations instance.
            document_dal: Optional DocumentDAL instance for database persistence.
        """
        self.db = db
        self.vector_ops = vector_ops
        # Initialize DocumentDAL if not provided
        if document_dal is None:
            from ...faas.shared.dal.document_dal import DocumentDAL 
            self.document_dal = DocumentDAL(db)
        else:
            self.document_dal = document_dal

    async def should_reembed(
        self, document_id: str, new_content: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if document needs re-embedding.
        
        Args:
            document_id (str): Input parameter for this operation.
            new_content (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        # Get current document using DAL
        doc = await self.document_dal.load_document(document_id, tenant_id)

        if not doc:
            return True  # Document not found, needs embedding

        # Calculate hash from current content
        old_content = doc.get("content", "")
        old_hash = hashlib.sha256(old_content.encode()).hexdigest() if old_content else None
        new_hash = hashlib.sha256(new_content.encode()).hexdigest()

        return old_hash != new_hash

    async def incremental_update(
        self,
        document_id: str,
        new_content: str,
        gateway,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Perform incremental update if needed.
        
        Args:
            document_id (str): Input parameter for this operation.
            new_content (str): Input parameter for this operation.
            gateway (Any): Gateway client used for LLM calls.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        if not await self.should_reembed(document_id, new_content, tenant_id):
            # Only update metadata/content, no re-embedding needed
            # Use DAL to update document
            await self.document_dal.update_document(
                document_id=document_id,
                content=new_content,
                tenant_id=tenant_id,
            )
            return False  # No re-embedding performed

        # Full re-embedding needed
        return True


class DocumentValidator:
    """
    Enhanced document validation processes.
    """

    def __init__(self):
        """Initialize document validator."""
        self.validation_rules: List[Callable] = []

    def add_validation_rule(self, rule: Callable) -> None:
        """
        Add a validation rule.
        
        Args:
            rule (Callable): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        self.validation_rules.append(rule)

    def validate(
        self, title: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate a document.
        
        Args:
            title (str): Input parameter for this operation.
            content (str): Content text.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            Tuple[bool, List[str]]: True if the operation succeeds, else False.
        """
        errors = []

        # Default validations
        if not title or len(title.strip()) == 0:
            errors.append("Title is required")

        if not content or len(content.strip()) == 0:
            errors.append("Content is required")

        if len(content) > 1_000_000:  # 1MB limit
            errors.append("Content exceeds maximum size (1MB)")

        # Run custom validation rules
        for rule in self.validation_rules:
            try:
                is_valid, error_msg = rule(title, content, metadata)
                if not is_valid:
                    errors.append(error_msg)
            except Exception as e:
                errors.append(f"Validation rule error: {str(e)}")

        return len(errors) == 0, errors


class RealTimeSync:
    """
    Real-time document synchronization for up-to-date information.
    """

    def __init__(self, db, rag_system, document_dal: Optional[Any] = None):
        """
        Initialize real-time sync.
        
        Args:
            db (Any): Database connection/handle.
            rag_system (Any): Input parameter for this operation.
            document_dal: Optional DocumentDAL instance for database persistence.
        """
        self.db = db
        self.rag_system = rag_system
        self.sync_callbacks: List[Callable] = []
        # Initialize DocumentDAL if not provided
        if document_dal is None:
            from ...faas.shared.dal.document_dal import DocumentDAL 
            self.document_dal = DocumentDAL(db)
        else:
            self.document_dal = document_dal

    def add_sync_callback(self, callback: Callable) -> None:
        """
        Add a callback for document sync events.
        
        Args:
            callback (Callable): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        self.sync_callbacks.append(callback)

    async def sync_document(self, document_id: str, tenant_id: Optional[str] = None) -> bool:
        """
        Synchronize a document (re-process and update).
        
        Args:
            document_id (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        # Get document using DAL
        result = await self.document_dal.load_document(document_id, tenant_id)

        if not result:
            return False

        # Re-ingest document
        try:
            # Use async ingestion if available, otherwise wrap sync call
            if hasattr(self.rag_system, "ingest_document_async"):
                await self.rag_system.ingest_document_async(
                    title=result["title"],
                    content=result["content"],
                    tenant_id=tenant_id,
                    source=result.get("source"),
                    metadata=result.get("metadata"),
                )
            else:
                # Wrap sync call in thread pool
                await asyncio.to_thread(
                    self.rag_system.ingest_document,
                    title=result["title"],
                    content=result["content"],
                    tenant_id=tenant_id,
                    source=result.get("source"),
                    metadata=result.get("metadata"),
                )

            # Call sync callbacks
            for callback in self.sync_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(document_id, tenant_id)
                    else:
                        callback(document_id, tenant_id)
                except Exception:
                    pass  # Ignore callback errors

            return True

        except Exception:
            return False
