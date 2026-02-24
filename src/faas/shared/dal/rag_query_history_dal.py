"""
Data Access Layer for RAG Query History.

Abstracts all database operations for RAG query history persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection

logger = logging.getLogger(__name__)


class RAGQueryHistoryDAL:
    """Data Access Layer for RAG query history persistence."""

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize RAGQueryHistoryDAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_query(
        self,
        query: str,
        answer: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        original_query: Optional[str] = None,
        query_used: Optional[str] = None,
        retrieved_documents: Optional[List[Dict[str, Any]]] = None,
        num_documents: int = 0,
        memory_used: int = 0,
        retrieval_strategy: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save RAG query to history.

        Args:
            query: Original query text.
            answer: Generated answer.
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            conversation_id: Optional conversation identifier.
            original_query: Optional original query (if rewritten).
            query_used: Optional query used for retrieval (if rewritten).
            retrieved_documents: Optional list of retrieved documents.
            num_documents: Number of documents retrieved.
            memory_used: Number of memories used.
            retrieval_strategy: Optional retrieval strategy used.
            metadata: Optional metadata.

        Returns:
            Query history record ID.
        """
        import uuid
        query_id = f"rag_query_{uuid.uuid4().hex[:16]}"
        
        result = await self.db.execute_query(
            """
            INSERT INTO rag_query_history (
                query_id, query, answer, tenant_id, user_id, conversation_id,
                original_query, query_used, retrieved_documents, num_documents,
                memory_used, retrieval_strategy, metadata, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10, $11, $12, $13::jsonb, CURRENT_TIMESTAMP)
            RETURNING query_id;
            """,
            params=(
                query_id,
                query,
                answer,
                tenant_id,
                user_id,
                conversation_id,
                original_query,
                query_used,
                json.dumps(retrieved_documents or []),
                num_documents,
                memory_used,
                retrieval_strategy,
                json.dumps(metadata or {}),
            ),
            fetch_one=True,
        )
        return str(result["query_id"]) if result else query_id

    async def get_query_history(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get RAG query history.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            conversation_id: Optional conversation identifier.
            limit: Maximum number of records to return.
            offset: Offset for pagination.

        Returns:
            List of query history records.
        """
        query = """
        SELECT 
            query_id, query, answer, tenant_id, user_id, conversation_id,
            original_query, query_used, retrieved_documents, num_documents,
            memory_used, retrieval_strategy, metadata, created_at
        FROM rag_query_history
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)
        if user_id:
            param_count += 1
            query += f" AND user_id = ${param_count}"
            params.append(user_id)
        if conversation_id:
            param_count += 1
            query += f" AND conversation_id = ${param_count}"
            params.append(conversation_id)

        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("retrieved_documents"):
                    record["retrieved_documents"] = (
                        json.loads(record["retrieved_documents"])
                        if isinstance(record["retrieved_documents"], str)
                        else record["retrieved_documents"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def get_conversation_history(
        self,
        conversation_id: str,
        tenant_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get query history for a specific conversation.

        Args:
            conversation_id: Conversation identifier.
            tenant_id: Tenant identifier for tenant isolation.
            limit: Maximum number of records to return.

        Returns:
            List of query history records for the conversation.
        """
        query = """
        SELECT 
            query_id, query, answer, tenant_id, user_id, conversation_id,
            original_query, query_used, retrieved_documents, num_documents,
            memory_used, retrieval_strategy, metadata, created_at
        FROM rag_query_history
        WHERE conversation_id = $1
        """
        params: List[Any] = [conversation_id]

        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)
            query += " ORDER BY created_at ASC LIMIT $3"
            params.append(limit)
        else:
            query += " ORDER BY created_at ASC LIMIT $2"
            params.append(limit)

        results = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        if results:
            for record in results:
                if record.get("retrieved_documents"):
                    record["retrieved_documents"] = (
                        json.loads(record["retrieved_documents"])
                        if isinstance(record["retrieved_documents"], str)
                        else record["retrieved_documents"]
                    )
                if record.get("metadata"):
                    record["metadata"] = (
                        json.loads(record["metadata"])
                        if isinstance(record["metadata"], str)
                        else record["metadata"]
                    )
        return results if results else []

    async def delete_query_history(
        self,
        query_id: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Delete query history record.

        Args:
            query_id: Query history record ID.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            True if deleted, False if not found.
        """
        query = """
        DELETE FROM rag_query_history
        WHERE query_id = $1
        """
        params: List[Any] = [query_id]
        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )
        return result > 0

    async def delete_conversation_history(
        self,
        conversation_id: str,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Delete all query history for a conversation.

        Args:
            conversation_id: Conversation identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM rag_query_history
        WHERE conversation_id = $1
        """
        params: List[Any] = [conversation_id]
        if tenant_id:
            query += " AND tenant_id = $2"
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=False,
        )
        return result if result else 0

    async def cleanup_old_history(
        self,
        days: int = 90,
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Clean up old query history records.

        Args:
            days: Number of days to keep (delete older records).
            tenant_id: Optional tenant identifier.

        Returns:
            Number of records deleted.
        """
        query = """
        DELETE FROM rag_query_history
        WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
        """ % days
        params: List[Any] = []
        if tenant_id:
            query = query.replace("WHERE", "WHERE tenant_id = $1 AND")
            params.append(tenant_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params) if params else None,
            fetch_all=False,
        )
        return result if result else 0

    async def get_query_stats(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get query statistics.

        Args:
            tenant_id: Tenant identifier for tenant isolation.
            user_id: Optional user identifier.
            conversation_id: Optional conversation identifier.

        Returns:
            Dictionary with query statistics.
        """
        query = """
        SELECT 
            COUNT(*) as total_queries,
            COUNT(DISTINCT conversation_id) as total_conversations,
            COUNT(DISTINCT user_id) as total_users,
            AVG(num_documents) as avg_documents,
            AVG(memory_used) as avg_memory_used
        FROM rag_query_history
        WHERE 1=1
        """
        params: List[Any] = []
        param_count = 0

        if tenant_id:
            param_count += 1
            query += f" AND tenant_id = ${param_count}"
            params.append(tenant_id)
        if user_id:
            param_count += 1
            query += f" AND user_id = ${param_count}"
            params.append(user_id)
        if conversation_id:
            param_count += 1
            query += f" AND conversation_id = ${param_count}"
            params.append(conversation_id)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        if result:
            return {
                "total_queries": result.get("total_queries", 0),
                "total_conversations": result.get("total_conversations", 0),
                "total_users": result.get("total_users", 0),
                "avg_documents": float(result.get("avg_documents", 0) or 0),
                "avg_memory_used": float(result.get("avg_memory_used", 0) or 0),
            }
        return {
            "total_queries": 0,
            "total_conversations": 0,
            "total_users": 0,
            "avg_documents": 0.0,
            "avg_memory_used": 0.0,
        }

