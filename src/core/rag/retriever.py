"""
Retriever

Handles document retrieval using vector similarity search.
"""

from typing import List, Dict, Any, Optional
from ..postgresql_database.vector_operations import VectorOperations
from ..litellm_gateway import LiteLLMGateway


class Retriever:
    """
    Document retriever using vector similarity search.

    Retrieves relevant documents based on query embeddings.
    """

    def __init__(
        self,
        vector_ops: VectorOperations,
        gateway: Optional[LiteLLMGateway] = None,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize retriever.

        Args:
            vector_ops: Vector operations instance
            gateway: Optional LiteLLM gateway for embedding generation
            embedding_model: Model to use for embeddings
        """
        self.vector_ops = vector_ops
        self.gateway = gateway
        self.embedding_model = embedding_model
        # Access database connection from vector_ops for keyword search
        self.db = vector_ops.db if hasattr(vector_ops, 'db') else None

    def retrieve(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Query text
            tenant_id: Optional tenant ID for multi-tenant SaaS (filters documents by tenant)
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            filters: Optional metadata filters

        Returns:
            List of relevant documents with similarity scores
        """
        # Generate query embedding
        query_embedding = self._get_embedding(query)

        # Add tenant_id to filters for tenant isolation
        if tenant_id:
            if filters is None:
                filters = {}
            filters['tenant_id'] = tenant_id

        # Perform similarity search
        results = self.vector_ops.similarity_search(
            query_embedding=query_embedding,
            limit=top_k,
            threshold=threshold,
            model=self.embedding_model,
            filters=filters
        )

        # Apply additional filters if provided
        if filters:
            results = self._apply_filters(results, filters)

        return results

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not self.gateway:
            raise EmbeddingError(
                message="Gateway not available for embedding generation",
                model=self.embedding_model
            )

        response = self.gateway.embed(
            texts=[text],
            model=self.embedding_model
        )

        if response.embeddings and len(response.embeddings) > 0:
            return response.embeddings[0]

        raise EmbeddingError(
            message="Failed to generate embedding: No embeddings returned",
            text=text,
            model=self.embedding_model
        )

    def retrieve_hybrid(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining vector similarity and keyword search.

        Args:
            query: Query text
            tenant_id: Optional tenant ID for multi-tenant SaaS (filters documents by tenant)
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            filters: Optional metadata filters
            vector_weight: Weight for vector similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)

        Returns:
            List of relevant documents with combined scores
        """
        # Add tenant_id to filters for tenant isolation
        if tenant_id:
            if filters is None:
                filters = {}
            filters['tenant_id'] = tenant_id

        # Vector-based retrieval
        query_embedding = self._get_embedding(query)
        vector_results = self.vector_ops.similarity_search(
            query_embedding=query_embedding,
            limit=top_k * 2,  # Get more for re-ranking
            threshold=threshold * 0.8,  # Lower threshold for hybrid
            model=self.embedding_model,
            filters=filters
        )

        # Keyword-based retrieval (simple text search)
        keyword_results = self._keyword_search(query, tenant_id=tenant_id, top_k=top_k * 2)

        # Combine and re-rank results
        combined = self._combine_results(
            vector_results,
            keyword_results,
            vector_weight,
            keyword_weight
        )

        # Apply filters if provided
        if filters:
            combined = self._apply_filters(combined, filters)

        # Return top_k results
        return combined[:top_k]

    def _keyword_search(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search on document content.

        Args:
            query: Query text
            tenant_id: Optional tenant ID for multi-tenant SaaS (filters documents by tenant)
            top_k: Maximum number of results

        Returns:
            List of documents matching keywords
        """
        # Extract keywords from query
        keywords = query.lower().split()

        # Simple keyword matching query with tenant filtering
        # In production, you might use full-text search (tsvector in PostgreSQL)
        if tenant_id:
            query_sql = """
            SELECT d.id, d.title, d.content, d.metadata, d.source,
                   COUNT(*) as keyword_matches
            FROM documents d
            WHERE (LOWER(d.content) LIKE ANY(ARRAY[%s])
               OR LOWER(d.title) LIKE ANY(ARRAY[%s]))
              AND d.tenant_id = %s
            GROUP BY d.id, d.title, d.content, d.metadata, d.source
            ORDER BY keyword_matches DESC, d.id
            LIMIT %s;
            """
        else:
            query_sql = """
            SELECT d.id, d.title, d.content, d.metadata, d.source,
                   COUNT(*) as keyword_matches
            FROM documents d
            WHERE LOWER(d.content) LIKE ANY(ARRAY[%s])
               OR LOWER(d.title) LIKE ANY(ARRAY[%s])
            GROUP BY d.id, d.title, d.content, d.metadata, d.source
            ORDER BY keyword_matches DESC, d.id
            LIMIT %s;
            """

        # Create LIKE patterns for each keyword
        like_patterns = [f"%{keyword}%" for keyword in keywords]

        # Get database connection from vector_ops
        db = getattr(self.vector_ops, 'db', None)
        if not db:
            # Fallback: try to get from vector_ops connection attribute
            db = getattr(self.vector_ops, 'connection', None)

        if not db:
            return []  # Cannot perform keyword search without database

        try:
            results = db.execute_query(
                query_sql,
                (like_patterns, like_patterns, limit),
                fetch_all=True
            )

            # Format results similar to vector search
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "id": str(row["id"]),
                    "title": row.get("title", ""),
                    "content": row.get("content", ""),
                    "metadata": row.get("metadata", {}),
                    "source": row.get("source"),
                    "similarity": row.get("keyword_matches", 0) / len(keywords),  # Normalize score
                    "score_type": "keyword"
                })

            return formatted_results
        except Exception:
            # Fallback to empty results if keyword search fails
            return []

    def _combine_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        vector_weight: float,
        keyword_weight: float
    ) -> List[Dict[str, Any]]:
        """
        Combine and re-rank vector and keyword results.

        Args:
            vector_results: Vector similarity results
            keyword_results: Keyword search results
            vector_weight: Weight for vector scores
            keyword_weight: Weight for keyword scores

        Returns:
            Combined and re-ranked results
        """
        # Create a map of document_id -> result
        combined_map = {}

        # Add vector results
        for result in vector_results:
            doc_id = str(result.get("id", ""))
            if doc_id not in combined_map:
                combined_map[doc_id] = result.copy()
                combined_map[doc_id]["vector_score"] = result.get("similarity", 0.0)
                combined_map[doc_id]["keyword_score"] = 0.0
            else:
                combined_map[doc_id]["vector_score"] = max(
                    combined_map[doc_id].get("vector_score", 0.0),
                    result.get("similarity", 0.0)
                )

        # Add keyword results
        for result in keyword_results:
            doc_id = str(result.get("id", ""))
            if doc_id not in combined_map:
                combined_map[doc_id] = result.copy()
                combined_map[doc_id]["vector_score"] = 0.0
                combined_map[doc_id]["keyword_score"] = result.get("similarity", 0.0)
            else:
                combined_map[doc_id]["keyword_score"] = max(
                    combined_map[doc_id].get("keyword_score", 0.0),
                    result.get("similarity", 0.0)
                )

        # Calculate combined scores
        combined_results = []
        for doc_id, result in combined_map.items():
            combined_score = (
                result.get("vector_score", 0.0) * vector_weight +
                result.get("keyword_score", 0.0) * keyword_weight
            )
            result["similarity"] = combined_score
            result["score_type"] = "hybrid"
            combined_results.append(result)

        # Sort by combined score
        combined_results.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)

        return combined_results

    def _apply_filters(
        self,
        results: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply metadata filters to results.

        Args:
            results: Search results
            filters: Filter criteria

        Returns:
            Filtered results
        """
        filtered = []

        for result in results:
            metadata = result.get('metadata', {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}

            match = True

            for key, value in filters.items():
                if key not in metadata or metadata[key] != value:
                    match = False
                    break

            if match:
                filtered.append(result)

        return filtered

