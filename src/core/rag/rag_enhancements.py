"""
RAG System Enhancements

Advanced features: re-ranking, versioning, relevance scoring, incremental updates, validation, real-time sync.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from .document_processor import DocumentChunk


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
            rerank_method: Re-ranking method ("cross_encoder", "bm25", "hybrid")
        """
        self.rerank_method = rerank_method
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Re-rank documents based on query relevance.
        
        Args:
            query: Search query
            documents: List of retrieved documents with scores
            top_k: Number of top documents to return
        
        Returns:
            Re-ranked documents
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
            
            reranked.append({
                **doc,
                "rerank_score": rerank_score,
                "original_score": score
            })
        
        # Sort by rerank score
        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        return reranked[:top_k]
    
    def rerank_with_cross_encoder(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Re-rank using cross-encoder model (requires sentence-transformers).
        
        Args:
            query: Search query
            documents: List of retrieved documents
            top_k: Number of top documents to return
        
        Returns:
            Re-ranked documents
        """
        try:
            from sentence_transformers import CrossEncoder
            
            # Initialize cross-encoder (lazy loading)
            if not hasattr(self, '_cross_encoder'):
                self._cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            
            # Prepare pairs for scoring
            pairs = [[query, doc.get("content", "")[:512]] for doc in documents]
            
            # Get scores
            scores = self._cross_encoder.predict(pairs)
            
            # Combine with documents
            reranked = []
            for doc, score in zip(documents, scores):
                reranked.append({
                    **doc,
                    "rerank_score": float(score),
                    "original_score": doc.get("score", 0.0)
                })
            
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
    
    def __init__(self, db):
        """
        Initialize document versioning.
        
        Args:
            db: Database connection
        """
        self.db = db
        self._ensure_version_table()
    
    def _ensure_version_table(self) -> None:
        """Ensure document_versions table exists."""
        query = """
        CREATE TABLE IF NOT EXISTS document_versions (
            id SERIAL PRIMARY KEY,
            document_id VARCHAR(255) NOT NULL,
            version INTEGER NOT NULL,
            content_hash VARCHAR(64) NOT NULL,
            content TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tenant_id VARCHAR(255),
            UNIQUE(document_id, version)
        );
        CREATE INDEX IF NOT EXISTS idx_doc_versions_doc_id ON document_versions(document_id);
        CREATE INDEX IF NOT EXISTS idx_doc_versions_tenant ON document_versions(tenant_id);
        """
        self.db.execute_query(query)
    
    def create_version(
        self,
        document_id: str,
        content: str,
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentVersion:
        """
        Create a new document version.
        
        Args:
            document_id: Document ID
            content: Document content
            tenant_id: Optional tenant ID
            metadata: Optional metadata
        
        Returns:
            DocumentVersion object
        """
        # Calculate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Get current max version
        query = """
        SELECT MAX(version) as max_version
        FROM document_versions
        WHERE document_id = %s
        """
        result = self.db.execute_query(query, (document_id,), fetch_one=True)
        next_version = (result.get("max_version") or 0) + 1
        
        # Insert new version
        insert_query = """
        INSERT INTO document_versions (document_id, version, content_hash, content, metadata, tenant_id)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s)
        RETURNING id, created_at
        """
        metadata_json = json.dumps(metadata or {})
        result = self.db.execute_query(
            insert_query,
            (document_id, next_version, content_hash, content, metadata_json, tenant_id),
            fetch_one=True
        )
        
        return DocumentVersion(
            version=next_version,
            document_id=document_id,
            content_hash=content_hash,
            created_at=result["created_at"],
            metadata=metadata or {}
        )
    
    def get_versions(
        self,
        document_id: str,
        tenant_id: Optional[str] = None
    ) -> List[DocumentVersion]:
        """
        Get all versions of a document.
        
        Args:
            document_id: Document ID
            tenant_id: Optional tenant ID
        
        Returns:
            List of DocumentVersion objects
        """
        query = """
        SELECT version, content_hash, created_at, metadata
        FROM document_versions
        WHERE document_id = %s
        """
        params = [document_id]
        
        if tenant_id:
            query += " AND tenant_id = %s"
            params.append(tenant_id)
        
        query += " ORDER BY version DESC"
        
        results = self.db.execute_query(query, tuple(params), fetch_all=True)
        
        return [
            DocumentVersion(
                version=r["version"],
                document_id=document_id,
                content_hash=r["content_hash"],
                created_at=r["created_at"],
                metadata=r.get("metadata", {})
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
    
    def score(
        self,
        query: str,
        document: Dict[str, Any],
        method: str = "hybrid"
    ) -> RelevanceScore:
        """
        Score document relevance to query.
        
        Args:
            query: Search query
            document: Document to score
            method: Scoring method ("similarity", "keyword", "hybrid")
        
        Returns:
            RelevanceScore object
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
            details=details
        )


class IncrementalUpdater:
    """
    Incremental updates to avoid full re-embedding when documents are updated.
    """
    
    def __init__(self, db, vector_ops):
        """
        Initialize incremental updater.
        
        Args:
            db: Database connection
            vector_ops: Vector operations instance
        """
        self.db = db
        self.vector_ops = vector_ops
    
    def should_reembed(
        self,
        document_id: str,
        new_content: str,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Check if document needs re-embedding.
        
        Args:
            document_id: Document ID
            new_content: New document content
            tenant_id: Optional tenant ID
        
        Returns:
            True if re-embedding needed, False otherwise
        """
        # Get current content hash
        query = """
        SELECT content_hash
        FROM documents
        WHERE id = %s
        """
        params = [document_id]
        
        if tenant_id:
            query += " AND tenant_id = %s"
            params.append(tenant_id)
        
        result = self.db.execute_query(query, tuple(params), fetch_one=True)
        
        if not result:
            return True  # Document not found, needs embedding
        
        old_hash = result.get("content_hash")
        new_hash = hashlib.sha256(new_content.encode()).hexdigest()
        
        return old_hash != new_hash
    
    async def incremental_update(
        self,
        document_id: str,
        new_content: str,
        gateway,
        embedding_model: str,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Perform incremental update if needed.
        
        Args:
            document_id: Document ID
            new_content: New document content
            gateway: LiteLLM gateway
            embedding_model: Embedding model
            tenant_id: Optional tenant ID
        
        Returns:
            True if update was performed, False otherwise
        """
        if not self.should_reembed(document_id, new_content, tenant_id):
            # Only update metadata/content, no re-embedding needed
            query = """
            UPDATE documents
            SET content = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            params = [new_content, document_id]
            
            if tenant_id:
                query += " AND tenant_id = %s"
                params.append(tenant_id)
            
            self.db.execute_query(query, tuple(params))
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
            rule: Validation function that returns (is_valid, error_message)
        """
        self.validation_rules.append(rule)
    
    def validate(
        self,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate a document.
        
        Args:
            title: Document title
            content: Document content
            metadata: Optional metadata
        
        Returns:
            Tuple of (is_valid, list_of_errors)
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
    
    def __init__(self, db, rag_system):
        """
        Initialize real-time sync.
        
        Args:
            db: Database connection
            rag_system: RAG system instance
        """
        self.db = db
        self.rag_system = rag_system
        self.sync_callbacks: List[Callable] = []
    
    def add_sync_callback(self, callback: Callable) -> None:
        """
        Add a callback for document sync events.
        
        Args:
            callback: Callback function to call on sync
        """
        self.sync_callbacks.append(callback)
    
    async def sync_document(
        self,
        document_id: str,
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Synchronize a document (re-process and update).
        
        Args:
            document_id: Document ID
            tenant_id: Optional tenant ID
        
        Returns:
            True if sync successful
        """
        # Get document
        query = """
        SELECT title, content, source, metadata
        FROM documents
        WHERE id = %s
        """
        params = [document_id]
        
        if tenant_id:
            query += " AND tenant_id = %s"
            params.append(tenant_id)
        
        result = self.db.execute_query(query, tuple(params), fetch_one=True)
        
        if not result:
            return False
        
        # Re-ingest document
        try:
            self.rag_system.ingest_document(
                title=result["title"],
                content=result["content"],
                tenant_id=tenant_id,
                source=result.get("source"),
                metadata=result.get("metadata")
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


# Import asyncio for async operations
import asyncio


