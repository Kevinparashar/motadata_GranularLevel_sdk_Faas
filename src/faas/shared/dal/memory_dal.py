"""
Memory Data Access Layer (DAL)

Provides database abstraction for agent memory persistence.
Tables are assumed to exist (managed by migrations/DAL).
"""


import json
import logging
from datetime import datetime
from typing import Any, List, Optional

from src.core.agno_agent_framework.memory import MemoryItem, MemoryType  
from src.core.postgresql_database import DatabaseConnection 

logger = logging.getLogger(__name__)


class MemoryDAL:
    """
    Data Access Layer for agent memory persistence.

    Handles all database operations for memory items.
    Tables are assumed to exist (managed by migrations/DAL).
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize Memory DAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def save_memory(self, memory: MemoryItem, tenant_id: str) -> None:
        """
        Save memory item to database.

        Args:
            memory: MemoryItem instance to save.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            None: Result of the operation.
        """
        await self.db.execute_query(
            """
            INSERT INTO agent_memory (
                memory_id, agent_id, tenant_id, memory_type, content,
                importance, timestamp, access_count, last_accessed, metadata, tags
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (memory_id) DO UPDATE SET
                content = EXCLUDED.content,
                importance = EXCLUDED.importance,
                timestamp = EXCLUDED.timestamp,
                access_count = EXCLUDED.access_count,
                last_accessed = EXCLUDED.last_accessed,
                metadata = EXCLUDED.metadata,
                tags = EXCLUDED.tags,
                updated_at = CURRENT_TIMESTAMP
            """,
            params=(
                memory.memory_id,
                memory.agent_id,
                tenant_id,
                memory.memory_type.value,
                memory.content,
                memory.importance,
                memory.timestamp,
                memory.access_count,
                memory.last_accessed,
                json.dumps(memory.metadata),
                json.dumps(memory.tags),
            ),
            fetch_all=False,
        )

    async def load_memories(
        self,
        agent_id: str,
        tenant_id: str,
        memory_type: Optional[MemoryType] = None,
    ) -> List[MemoryItem]:
        """
        Load memories from database.

        Args:
            agent_id: Agent identifier.
            tenant_id: Tenant identifier for tenant isolation.
            memory_type: Optional filter by memory type.

        Returns:
            List[MemoryItem]: List of memory items.
        """
        query = """
            SELECT * FROM agent_memory
            WHERE agent_id = $1 AND tenant_id = $2
        """
        params: List[Any] = [agent_id, tenant_id]

        if memory_type:
            query += " AND memory_type = $3"
            params.append(memory_type.value)

        query += " ORDER BY timestamp ASC"

        rows = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_all=True,
        )

        memories: List[MemoryItem] = []
        if rows:
            for row in rows:
                memories.append(
                    MemoryItem(
                        memory_id=row["memory_id"],
                        agent_id=row["agent_id"],
                        memory_type=MemoryType(row["memory_type"]),
                        content=row["content"],
                        importance=row["importance"],
                        timestamp=row["timestamp"],
                        access_count=row["access_count"],
                        last_accessed=row["last_accessed"],
                        metadata=(
                            json.loads(row["metadata"])
                            if isinstance(row["metadata"], str)
                            else row["metadata"]
                        ),
                        tags=(
                            json.loads(row["tags"])
                            if isinstance(row["tags"], str)
                            else row["tags"]
                        ),
                    )
                )

        return memories

    async def delete_memory(
        self, memory_id: str, agent_id: str, tenant_id: str
    ) -> bool:
        """
        Delete memory item from database.

        Args:
            memory_id: Memory identifier.
            agent_id: Agent identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            bool: True if deleted, False if not found.
        """
        result = await self.db.execute_query(
            """
            DELETE FROM agent_memory
            WHERE memory_id = $1 AND agent_id = $2 AND tenant_id = $3
            """,
            params=(memory_id, agent_id, tenant_id),
            fetch_all=False,
        )

        return result > 0

    async def delete_all_agent_memories(
        self, agent_id: str, tenant_id: str
    ) -> int:
        """
        Delete all memories for an agent.

        Args:
            agent_id: Agent identifier.
            tenant_id: Tenant identifier for tenant isolation.

        Returns:
            int: Number of memories deleted.
        """
        result = await self.db.execute_query(
            """
            DELETE FROM agent_memory
            WHERE agent_id = $1 AND tenant_id = $2
            """,
            params=(agent_id, tenant_id),
            fetch_all=False,
        )

        return result

    async def get_memory_count(
        self,
        agent_id: str,
        tenant_id: str,
        memory_type: Optional[MemoryType] = None,
    ) -> int:
        """
        Get count of memories for an agent.

        Args:
            agent_id: Agent identifier.
            tenant_id: Tenant identifier for tenant isolation.
            memory_type: Optional filter by memory type.

        Returns:
            int: Count of memories.
        """
        query = """
            SELECT COUNT(*) as count FROM agent_memory
            WHERE agent_id = $1 AND tenant_id = $2
        """
        params: List[Any] = [agent_id, tenant_id]

        if memory_type:
            query += " AND memory_type = $3"
            params.append(memory_type.value)

        result = await self.db.execute_query(
            query,
            params=tuple(params),
            fetch_one=True,
        )

        return result["count"] if result else 0

    async def update_memory_access(
        self,
        memory_id: str,
        agent_id: str,
        tenant_id: str,
        access_count: Optional[int] = None,
        last_accessed: Optional[datetime] = None,
    ) -> bool:
        """
        Update memory access information.

        Args:
            memory_id: Memory identifier.
            agent_id: Agent identifier.
            tenant_id: Tenant identifier for tenant isolation.
            access_count: Optional new access count.
            last_accessed: Optional new last accessed timestamp.

        Returns:
            bool: True if updated, False if not found.
        """
        if access_count is None and last_accessed is None:
            # Default to incrementing access_count and updating last_accessed
            result = await self.db.execute_query(
                """
                UPDATE agent_memory
                SET access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE memory_id = $1 AND agent_id = $2 AND tenant_id = $3
                """,
                params=(memory_id, agent_id, tenant_id),
                fetch_all=False,
            )
        else:
            # Use provided values
            update_fields = []
            params: List[Any] = []
            param_index = 1

            if access_count is not None:
                update_fields.append(f"access_count = ${param_index}")
                params.append(access_count)
                param_index += 1

            if last_accessed is not None:
                update_fields.append(f"last_accessed = ${param_index}")
                params.append(last_accessed)
                param_index += 1

            if update_fields:
                update_fields.append("updated_at = CURRENT_TIMESTAMP")
                params.extend([memory_id, agent_id, tenant_id])

                query = f"""
                    UPDATE agent_memory
                    SET {', '.join(update_fields)}
                    WHERE memory_id = ${param_index} AND agent_id = ${param_index + 1} AND tenant_id = ${param_index + 2}
                """

                result = await self.db.execute_query(
                    query,
                    params=tuple(params),
                    fetch_all=False,
                )
            else:
                return False

        return result > 0

    async def search_memories(
        self,
        agent_id: str,
        tenant_id: str,
        query: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[MemoryItem]:
        """
        Search memories with optional text search.

        Args:
            agent_id: Agent identifier.
            tenant_id: Tenant identifier for tenant isolation.
            query: Optional text search query.
            memory_type: Optional filter by memory type.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List[MemoryItem]: List of matching memory items.
        """
        sql_query = """
            SELECT * FROM agent_memory
            WHERE agent_id = $1 AND tenant_id = $2
        """
        params: List[Any] = [agent_id, tenant_id]
        param_count = 2

        if memory_type:
            param_count += 1
            sql_query += f" AND memory_type = ${param_count}"
            params.append(memory_type.value)

        if query:
            param_count += 1
            sql_query += f" AND content ILIKE ${param_count}"
            params.append(f"%{query}%")

        sql_query += " ORDER BY importance DESC, timestamp DESC"
        param_count += 1
        sql_query += f" LIMIT ${param_count}"
        params.append(limit)
        param_count += 1
        sql_query += f" OFFSET ${param_count}"
        params.append(offset)

        rows = await self.db.execute_query(
            sql_query,
            params=tuple(params),
            fetch_all=True,
        )

        memories: List[MemoryItem] = []
        if rows:
            for row in rows:
                memories.append(
                    MemoryItem(
                        memory_id=row["memory_id"],
                        agent_id=row["agent_id"],
                        memory_type=MemoryType(row["memory_type"]),
                        content=row["content"],
                        importance=row["importance"],
                        timestamp=row["timestamp"],
                        access_count=row["access_count"],
                        last_accessed=row["last_accessed"],
                        metadata=(
                            json.loads(row["metadata"])
                            if isinstance(row["metadata"], str)
                            else row["metadata"]
                        ),
                        tags=(
                            json.loads(row["tags"])
                            if isinstance(row["tags"], str)
                            else row["tags"]
                        ),
                    )
                )

        return memories

