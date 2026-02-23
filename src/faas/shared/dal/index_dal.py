"""
Index Data Access Layer (DAL)

Provides database abstraction for vector index management operations.
Tables are assumed to exist (managed by migrations/DAL).
"""


import logging
import re
from typing import Any, Dict, List, Optional

from src.core.postgresql_database import DatabaseConnection 

logger = logging.getLogger(__name__)


class IndexDAL:
    """
    Data Access Layer for vector index management.

    Handles all database operations for vector index creation, deletion, and management.
    Tables are assumed to exist (managed by migrations/DAL).
    """

    def __init__(self, db_connection: DatabaseConnection):
        """
        Initialize Index DAL.

        Args:
            db_connection: Database connection instance.
        """
        self.db = db_connection

    async def create_index(
        self,
        index_name: str,
        table_name: str,
        column_name: str,
        index_type: str,
        distance_metric: str = "cosine",
        lists: Optional[int] = None,
        m: Optional[int] = None,
        ef_construction: Optional[int] = None,
    ) -> bool:
        """
        Create a vector index.

        Args:
            index_name: Index name.
            table_name: Table name.
            column_name: Column name.
            index_type: Index type (ivfflat or hnsw).
            distance_metric: Distance metric (cosine, l2, inner_product).
            lists: Number of lists for IVFFlat (optional).
            m: M parameter for HNSW (optional).
            ef_construction: ef_construction parameter for HNSW (optional).

        Returns:
            bool: True if index created successfully.
        """
        # Validate table_name to prevent SQL injection
        if not re.match(r"^[a-zA-Z0-9_.]+$", table_name):
            raise ValueError(
                f"Invalid table name: {table_name}. Only alphanumeric, underscore, and dot characters allowed."
            )

        # Validate column_name to prevent SQL injection
        if not re.match(r"^[a-zA-Z0-9_]+$", column_name):
            raise ValueError(
                f"Invalid column name: {column_name}. Only alphanumeric and underscore characters allowed."
            )

        # Validate index_name to prevent SQL injection
        if not re.match(r"^[a-zA-Z0-9_]+$", index_name):
            raise ValueError(
                f"Invalid index name: {index_name}. Only alphanumeric and underscore characters allowed."
            )

        if index_type.lower() == "ivfflat":
            if lists is None:
                lists = 100  # Default
            query = f"""
            CREATE INDEX IF NOT EXISTS "{index_name}"
            ON "{table_name}" USING ivfflat ("{column_name}" vector_{distance_metric}_ops)
            WITH (lists = {lists});
            """
        elif index_type.lower() == "hnsw":
            if m is None:
                m = 16  # Default
            if ef_construction is None:
                ef_construction = 64  # Default
            query = f"""
            CREATE INDEX IF NOT EXISTS "{index_name}"
            ON "{table_name}" USING hnsw ("{column_name}" vector_{distance_metric}_ops)
            WITH (m = {m}, ef_construction = {ef_construction});
            """
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

        try:
            await self.db.execute_query(query, fetch_all=False)
            return True
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False

    async def drop_index(self, index_name: str) -> bool:
        """
        Drop a vector index.

        Args:
            index_name: Index name.

        Returns:
            bool: True if index dropped successfully.
        """
        # Validate index_name to prevent SQL injection
        if not re.match(r"^[a-zA-Z0-9_]+$", index_name):
            raise ValueError(
                f"Invalid index name: {index_name}. Only alphanumeric and underscore characters allowed."
            )

        query = f'DROP INDEX IF EXISTS "{index_name}";'

        try:
            await self.db.execute_query(query, fetch_all=False)
            return True
        except Exception as e:
            logger.error(f"Failed to drop index {index_name}: {e}")
            return False

    async def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists.

        Args:
            index_name: Index name.

        Returns:
            bool: True if index exists, False otherwise.
        """
        # Validate index_name to prevent SQL injection
        if not re.match(r"^[a-zA-Z0-9_]+$", index_name):
            raise ValueError(
                f"Invalid index name: {index_name}. Only alphanumeric and underscore characters allowed."
            )

        query = """
        SELECT 1 FROM pg_indexes
        WHERE indexname = $1
        LIMIT 1;
        """

        result = await self.db.execute_query(
            query,
            params=(index_name,),
            fetch_one=True,
        )

        return result is not None

    async def get_table_row_count(
        self, table_name: str, tenant_id: Optional[str] = None
    ) -> int:
        """
        Get row count for a table.

        Args:
            table_name: Table name.
            tenant_id: Optional tenant identifier.

        Returns:
            int: Row count.
        """
        # Validate table_name to prevent SQL injection
        if not re.match(r"^[a-zA-Z0-9_.]+$", table_name):
            raise ValueError(
                f"Invalid table name: {table_name}. Only alphanumeric, underscore, and dot characters allowed."
            )

        if tenant_id:
            query = f'SELECT COUNT(*) as count FROM "{table_name}" WHERE tenant_id = $1;'
            result = await self.db.execute_query(query, (tenant_id,), fetch_one=True)
        else:
            query = f'SELECT COUNT(*) as count FROM "{table_name}";'
            result = await self.db.execute_query(query, fetch_one=True)

        return result.get("count", 0) if result else 0

    async def list_indexes(
        self, table_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all indexes, optionally filtered by table.

        Args:
            table_name: Optional table name filter.

        Returns:
            List[Dict[str, Any]]: List of index information.
        """
        if table_name:
            # Validate table_name to prevent SQL injection
            if not re.match(r"^[a-zA-Z0-9_.]+$", table_name):
                raise ValueError(
                    f"Invalid table name: {table_name}. Only alphanumeric, underscore, and dot characters allowed."
                )
            query = """
            SELECT indexname, tablename, indexdef
            FROM pg_indexes
            WHERE tablename = $1;
            """
            params = (table_name,)
        else:
            query = """
            SELECT indexname, tablename, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
            """
            params = None

        results = await self.db.execute_query(
            query,
            params=params,
            fetch_all=True,
        )

        return results if results else []

    async def reindex(self, index_name: str) -> bool:
        """
        Reindex an existing index.

        Args:
            index_name: Index name.

        Returns:
            bool: True if reindex successful.
        """
        # Validate index_name to prevent SQL injection
        if not re.match(r"^[a-zA-Z0-9_]+$", index_name):
            raise ValueError(
                f"Invalid index name: {index_name}. Only alphanumeric and underscore characters allowed."
            )

        query = f'REINDEX INDEX "{index_name}";'

        try:
            await self.db.execute_query(query, fetch_all=False)
            return True
        except Exception as e:
            logger.error(f"Failed to reindex {index_name}: {e}")
            return False

    async def get_index_info(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an index.

        Args:
            index_name: Index name.

        Returns:
            Optional[Dict[str, Any]]: Index information if found, else None.
        """
        # Validate index_name to prevent SQL injection
        if not re.match(r"^[a-zA-Z0-9_]+$", index_name):
            raise ValueError(
                f"Invalid index name: {index_name}. Only alphanumeric and underscore characters allowed."
            )

        query = """
        SELECT indexname, tablename, indexdef
        FROM pg_indexes
        WHERE indexname = $1
        LIMIT 1;
        """

        result = await self.db.execute_query(
            query,
            params=(index_name,),
            fetch_one=True,
        )

        return result if result else None

