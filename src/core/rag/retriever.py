# Copyright (c) 2024. All rights reserved.
# This source code is licensed under the MIT license and a copy
# of the license can be found in the LICENSE file in the root directory.

"""
Retriever

Handles document retrieval using vector similarity search.
"""


import logging
import time
from typing import Any, Dict, List, Optional

from typing import TYPE_CHECKING

from ..litellm_gateway import LiteLLMGateway
from ..postgresql_database.vector_operations import VectorOperations
from .exceptions import EmbeddingError

if TYPE_CHECKING:
    from ...faas.shared.dal.document_dal import DocumentDAL

logger = logging.getLogger(__name__)


class Retriever:
    """
    Document retriever using vector similarity search.

    Retrieves relevant documents based on query embeddings.
    """

    def __init__(
        self,
        vector_ops: VectorOperations,
        gateway: Optional[LiteLLMGateway] = None,
        embedding_model: str = "text-embedding-3-small",
        otel_tracer: Optional[Any] = None,
        otel_metrics: Optional[Any] = None,
        document_dal: Optional["DocumentDAL"] = None,
    ):
        """
        Initialize retriever.
        
        Args:
            vector_ops (VectorOperations): Input parameter for this operation.
            gateway (Optional[LiteLLMGateway]): Gateway client used for LLM calls.
            embedding_model (str): Input parameter for this operation.
            otel_tracer: Optional OTEL tracer for distributed tracing
            otel_metrics: Optional OTEL metrics for metrics collection
            document_dal: Optional DocumentDAL instance for keyword search operations.
        """
        self.vector_ops = vector_ops
        self.gateway = gateway
        self.embedding_model = embedding_model
        # Initialize DocumentDAL if not provided
        if document_dal is None:
            from ...faas.shared.dal.document_dal import DocumentDAL
            # Get database connection from vector_ops
            db = vector_ops.db if hasattr(vector_ops, "db") else None
            if db:
                self.document_dal = DocumentDAL(db)
            else:
                self.document_dal = None
        else:
            self.document_dal = document_dal

        # OTEL Integration (optional)
        self.otel_tracer: Optional[Any] = otel_tracer
        self.otel_metrics: Optional[Any] = otel_metrics

        # Initialize OTEL if not provided
        if self.otel_tracer is None:
            try:
                from ..otel_integration import create_otel_tracer

                self.otel_tracer = create_otel_tracer(service_name="rag-retriever")
            except (ImportError, Exception):
                self.otel_tracer = None

        if self.otel_metrics is None:
            try:
                from ..otel_integration import create_otel_metrics

                self.otel_metrics = create_otel_metrics(service_name="rag-retriever")
            except (ImportError, Exception):
                self.otel_metrics = None

    def retrieve(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            top_k (int): Input parameter for this operation.
            threshold (float): Input parameter for this operation.
            filters (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        start_time = time.time()

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("retriever.retrieve") as trace:
                trace.set_attribute("retriever.query", query[:100])  # Truncate for safety
                trace.set_attribute("retriever.top_k", top_k)
                trace.set_attribute("retriever.threshold", threshold)
                trace.set_attribute("retriever.embedding_model", self.embedding_model)
                from ..utils.tenant_utils import add_tenant_attributes_to_span
                add_tenant_attributes_to_span(trace, tenant_id, attribute_prefix="retriever")

                try:
                    # Generate query embedding
                    query_embedding = self._get_embedding(query)

                    # Add tenant_id to filters for tenant isolation
                    if tenant_id:
                        if filters is None:
                            filters = {}
                        filters["tenant_id"] = tenant_id

                    # Perform similarity search
                    import asyncio
                    def _run_async(coro):
                        """Helper to run async code from sync context."""
                        try:
                            _ = asyncio.get_running_loop()
                            raise RuntimeError(
                                "Cannot call sync retrieve() from async context. Use retrieve_async() instead."
                            )
                        except RuntimeError as e:
                            if "Cannot call sync" in str(e):
                                raise
                            return asyncio.run(coro)
                    results = _run_async(self.vector_ops.similarity_search(
                        query_embedding=query_embedding,
                        limit=top_k,
                        threshold=threshold,
                        model=self.embedding_model,
                    ))

                    # Apply additional filters if provided
                    if filters:
                        results = self._apply_filters(results, filters)

                    duration = time.time() - start_time
                    trace.set_attribute("retriever.results_count", len(results))

                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "retriever.retrieve.duration", duration, {"embedding_model": self.embedding_model}
                        )
                        self.otel_metrics.increment_counter(
                            "retriever.operations",
                            amount=1.0,
                            attributes={
                                "status": "success",
                                "embedding_model": self.embedding_model,
                                "results_count": len(results),
                            },
                        )

                    return results
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "retriever.retrieve.duration", duration, {"embedding_model": self.embedding_model}
                        )
                        self.otel_metrics.increment_counter(
                            "retriever.operations",
                            amount=1.0,
                            attributes={
                                "status": "error",
                                "embedding_model": self.embedding_model,
                                "error_type": type(e).__name__,
                            },
                        )
                    raise
        else:
            # No OTEL - execute without tracing
            # Generate query embedding
            query_embedding = self._get_embedding(query)

            # Add tenant_id to filters for tenant isolation
            if tenant_id:
                if filters is None:
                    filters = {}
                filters["tenant_id"] = tenant_id

            # Perform similarity search
            import asyncio
            def _run_async(coro):
                """Helper to run async code from sync context."""
                try:
                    _ = asyncio.get_running_loop()
                    raise RuntimeError(
                        "Cannot call sync retrieve() from async context. Use retrieve_async() instead."
                    )
                except RuntimeError as e:
                    if "Cannot call sync" in str(e):
                        raise
                    return asyncio.run(coro)
            results = _run_async(self.vector_ops.similarity_search(
                query_embedding=query_embedding,
                limit=top_k,
                threshold=threshold,
                model=self.embedding_model,
            ))

            # Apply additional filters if provided
            if filters:
                results = self._apply_filters(results, filters)

            return results

    async def retrieve_async(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query (async version).
        
        Args:
            query (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            top_k (int): Input parameter for this operation.
            threshold (float): Input parameter for this operation.
            filters (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        start_time = time.time()

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("retriever.retrieve") as trace:
                trace.set_attribute("retriever.query", query[:100])
                trace.set_attribute("retriever.top_k", top_k)
                trace.set_attribute("retriever.threshold", threshold)
                trace.set_attribute("retriever.embedding_model", self.embedding_model)
                from ..utils.tenant_utils import add_tenant_attributes_to_span
                add_tenant_attributes_to_span(trace, tenant_id, attribute_prefix="retriever")

                try:
                    # Generate query embedding
                    query_embedding = self._get_embedding(query)

                    # Add tenant_id to filters for tenant isolation
                    if tenant_id:
                        if filters is None:
                            filters = {}
                        filters["tenant_id"] = tenant_id

                    # Perform similarity search (async)
                    results = await self.vector_ops.similarity_search(
                        query_embedding=query_embedding,
                        limit=top_k,
                        threshold=threshold,
                        model=self.embedding_model,
                    )

                    # Apply additional filters if provided
                    if filters:
                        results = self._apply_filters(results, filters)

                    duration = time.time() - start_time
                    trace.set_attribute("retriever.results_count", len(results))

                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "retriever.retrieve.duration", duration, {"embedding_model": self.embedding_model}
                        )
                        self.otel_metrics.increment_counter(
                            "retriever.operations",
                            amount=1.0,
                            attributes={
                                "status": "success",
                                "embedding_model": self.embedding_model,
                                "results_count": len(results),
                            },
                        )

                    return results
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "retriever.retrieve.duration", duration, {"embedding_model": self.embedding_model}
                        )
                        self.otel_metrics.increment_counter(
                            "retriever.operations",
                            amount=1.0,
                            attributes={
                                "status": "error",
                                "embedding_model": self.embedding_model,
                                "error_type": type(e).__name__,
                            },
                        )
                    raise
        else:
            # No OTEL - execute without tracing
            # Generate query embedding
            query_embedding = self._get_embedding(query)

            # Add tenant_id to filters for tenant isolation
            if tenant_id:
                if filters is None:
                    filters = {}
                filters["tenant_id"] = tenant_id

            # Perform similarity search (async)
            results = await self.vector_ops.similarity_search(
                query_embedding=query_embedding,
                limit=top_k,
                threshold=threshold,
                model=self.embedding_model,
            )

            # Apply additional filters if provided
            if filters:
                results = self._apply_filters(results, filters)

            return results

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text.
        
        Args:
            text (str): Input parameter for this operation.
        
        Returns:
            List[float]: List result of the operation.
        
        Raises:
            EmbeddingError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if not self.gateway:
            raise EmbeddingError(
                message="Gateway not available for embedding generation", model=self.embedding_model
            )

        response = self.gateway.embed(texts=[text], model=self.embedding_model)

        if response.embeddings and len(response.embeddings) > 0:
            return response.embeddings[0]

        raise EmbeddingError(
            message="Failed to generate embedding: No embeddings returned",
            text=text,
            model=self.embedding_model,
        )

    def retrieve_hybrid(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining vector similarity and keyword search.
        
        Args:
            query (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            top_k (int): Input parameter for this operation.
            threshold (float): Input parameter for this operation.
            filters (Optional[Dict[str, Any]]): Input parameter for this operation.
            vector_weight (float): Input parameter for this operation.
            keyword_weight (float): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        start_time = time.time()

        # OTEL Integration
        if self.otel_tracer:
            with self.otel_tracer.start_trace("retriever.retrieve_hybrid") as trace:
                trace.set_attribute("retriever.query", query[:100])  # Truncate for safety
                trace.set_attribute("retriever.top_k", top_k)
                trace.set_attribute("retriever.threshold", threshold)
                trace.set_attribute("retriever.vector_weight", vector_weight)
                trace.set_attribute("retriever.keyword_weight", keyword_weight)
                trace.set_attribute("retriever.embedding_model", self.embedding_model)
                from ..utils.tenant_utils import add_tenant_attributes_to_span
                add_tenant_attributes_to_span(trace, tenant_id, attribute_prefix="retriever")

                try:
                    # Add tenant_id to filters for tenant isolation
                    if tenant_id:
                        if filters is None:
                            filters = {}
                        filters["tenant_id"] = tenant_id

                    # Vector-based retrieval
                    query_embedding = self._get_embedding(query)
                    import asyncio
                    vector_results = asyncio.run(self.vector_ops.similarity_search(
                        query_embedding=query_embedding,
                        limit=top_k * 2,  # Get more for re-ranking
                        threshold=threshold * 0.8,  # Lower threshold for hybrid
                        model=self.embedding_model,
                    ))

                    # Keyword-based retrieval (simple text search)
                    keyword_results = self._keyword_search(query, tenant_id=tenant_id, top_k=top_k * 2)

                    # Combine and re-rank results
                    combined = self._combine_results(
                        vector_results, keyword_results, vector_weight, keyword_weight
                    )

                    # Apply filters if provided
                    if filters:
                        combined = self._apply_filters(combined, filters)

                    # Return top_k results
                    results = combined[:top_k]

                    duration = time.time() - start_time
                    trace.set_attribute("retriever.results_count", len(results))
                    trace.set_attribute("retriever.vector_results_count", len(vector_results))
                    trace.set_attribute("retriever.keyword_results_count", len(keyword_results))

                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "retriever.retrieve_hybrid.duration", duration, {"embedding_model": self.embedding_model}
                        )
                        self.otel_metrics.increment_counter(
                            "retriever.operations",
                            amount=1.0,
                            attributes={
                                "operation": "hybrid",
                                "status": "success",
                                "embedding_model": self.embedding_model,
                                "results_count": len(results),
                            },
                        )

                    return results
                except Exception as e:
                    trace.record_exception(e)
                    duration = time.time() - start_time
                    if self.otel_metrics:
                        self.otel_metrics.record_histogram(
                            "retriever.retrieve_hybrid.duration", duration, {"embedding_model": self.embedding_model}
                        )
                        self.otel_metrics.increment_counter(
                            "retriever.operations",
                            amount=1.0,
                            attributes={
                                "operation": "hybrid",
                                "status": "error",
                                "embedding_model": self.embedding_model,
                                "error_type": type(e).__name__,
                            },
                        )
                    raise
        else:
            # No OTEL - execute without tracing
            # Add tenant_id to filters for tenant isolation
            if tenant_id:
                if filters is None:
                    filters = {}
                filters["tenant_id"] = tenant_id

            # Vector-based retrieval
            query_embedding = self._get_embedding(query)
            import asyncio
            vector_results = asyncio.run(self.vector_ops.similarity_search(
                query_embedding=query_embedding,
                limit=top_k * 2,  # Get more for re-ranking
                threshold=threshold * 0.8,  # Lower threshold for hybrid
                model=self.embedding_model,
            ))

            # Keyword-based retrieval (simple text search)
            keyword_results = self._keyword_search(query, tenant_id=tenant_id, top_k=top_k * 2)

            # Combine and re-rank results
            combined = self._combine_results(
                vector_results, keyword_results, vector_weight, keyword_weight
            )

            # Apply filters if provided
            if filters:
                combined = self._apply_filters(combined, filters)

            # Return top_k results
            return combined[:top_k]

    def _keyword_search(
        self, query: str, tenant_id: Optional[str] = None, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search on document content.
        
        Args:
            query (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            top_k (int): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        # Use DocumentDAL for keyword search (proper DAL architecture)
        if not self.document_dal:
            logger.warning("DocumentDAL not available, cannot perform keyword search")
            return []

        # Extract keywords from query
        keywords = query.lower().split()
        if not keywords:
            return []

        try:
            # Use DocumentDAL for keyword search
            import asyncio

            def _run_async(coro):
                """Helper to run async code from sync context."""
                try:
                    _ = asyncio.get_running_loop()
                    raise RuntimeError(
                        "Cannot call sync _keyword_search() from async context. Use retrieve_async() instead."
                    )
                except RuntimeError as e:
                    if "Cannot call sync" in str(e):
                        raise
                    return asyncio.run(coro)

            results = _run_async(
                self.document_dal.keyword_search(
                    keywords=keywords,
                    tenant_id=tenant_id,
                    limit=top_k,
                )
            )

            return results
        except Exception as e:
            logger.warning(f"Keyword search failed: {str(e)}")
            return []

    def _combine_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        vector_weight: float,
        keyword_weight: float,
    ) -> List[Dict[str, Any]]:
        """
        Combine and re-rank vector and keyword results.
        
        Args:
            vector_results (List[Dict[str, Any]]): Input parameter for this operation.
            keyword_results (List[Dict[str, Any]]): Input parameter for this operation.
            vector_weight (float): Input parameter for this operation.
            keyword_weight (float): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
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
                    combined_map[doc_id].get("vector_score", 0.0), result.get("similarity", 0.0)
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
                    combined_map[doc_id].get("keyword_score", 0.0), result.get("similarity", 0.0)
                )

        # Calculate combined scores
        combined_results = []
        for doc_id, result in combined_map.items():
            combined_score = (
                result.get("vector_score", 0.0) * vector_weight
                + result.get("keyword_score", 0.0) * keyword_weight
            )
            result["similarity"] = combined_score
            result["score_type"] = "hybrid"
            combined_results.append(result)

        # Sort by combined score
        combined_results.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)

        return combined_results

    def _apply_filters(
        self, results: List[Dict[str, Any]], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply metadata filters to results.
        
        Args:
            results (List[Dict[str, Any]]): Input parameter for this operation.
            filters (Dict[str, Any]): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        filtered = []

        for result in results:
            metadata = result.get("metadata", {})
            if isinstance(metadata, str):
                import json

                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata = {}

            match = True

            for key, value in filters.items():
                if key not in metadata or metadata[key] != value:
                    match = False
                    break

            if match:
                filtered.append(result)

        return filtered
