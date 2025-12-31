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
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Query text
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            filters: Optional metadata filters
        
        Returns:
            List of relevant documents with similarity scores
        """
        # Generate query embedding
        query_embedding = self._get_embedding(query)
        
        # Perform similarity search
        results = self.vector_ops.similarity_search(
            query_embedding=query_embedding,
            limit=top_k,
            threshold=threshold,
            model=self.embedding_model
        )
        
        # Apply filters if provided
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
            raise ValueError("Gateway not available for embedding generation")
        
        response = self.gateway.embed(
            texts=[text],
            model=self.embedding_model
        )
        
        if response.embeddings and len(response.embeddings) > 0:
            return response.embeddings[0]
        
        raise ValueError("Failed to generate embedding")
    
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

