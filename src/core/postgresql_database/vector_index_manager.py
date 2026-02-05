"""
Vector Index Management

Provides comprehensive index management for pgvector, including creation,
monitoring, and reindexing of IVFFlat and HNSW indexes.

All methods are async-first for production scalability.
"""


# Standard library imports
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

# Local application/library specific imports
from .connection import DatabaseConnection


class DatabaseError(Exception):
    """Database operation error."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize DatabaseError.
        
        Args:
            message (str): Error message.
            operation (Optional[str]): Operation that failed.
            original_error (Optional[Exception]): Original exception.
        """
        self.message = message
        self.operation = operation
        self.original_error = original_error
        super().__init__(self.message)


class VectorIndexError(Exception):
    """Vector index operation error."""

    def __init__(
        self,
        message: str,
        index_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize VectorIndexError.
        
        Args:
            message (str): Error message.
            index_name (Optional[str]): Index name that caused error.
            original_error (Optional[Exception]): Original exception.
        """
        self.message = message
        self.index_name = index_name
        self.original_error = original_error
        super().__init__(self.message)


logger = logging.getLogger(__name__)


class IndexType(str, Enum):
    """Supported index types for pgvector."""

    IVFFLAT = "ivfflat"
    HNSW = "hnsw"


class IndexDistance(str, Enum):
    """Distance metrics for vector indexes."""

    COSINE = "cosine"
    L2 = "l2"
    INNER_PRODUCT = "inner_product"


class VectorIndexManager:
    """
    Manages vector indexes for optimal search performance.

    Supports IVFFlat and HNSW indexes with automatic reindexing
    when embeddings change or models are updated.
    
    All methods are async-first for production scalability.
    """

    def __init__(self, db: DatabaseConnection):
        """
        Initialize vector index manager.
        
        Args:
            db (DatabaseConnection): Database connection/handle.
        """
        self.db = db

    def _get_distance_opclass(self, distance: IndexDistance) -> str:
        """
        Get the operator class for the given distance metric.
        
        Args:
            distance (IndexDistance): Distance metric.
        
        Returns:
            str: Operator class name.
        """
        if distance == IndexDistance.COSINE:
            return "vector_cosine_ops"
        elif distance == IndexDistance.L2:
            return "vector_l2_ops"
        else:  # inner_product
            return "vector_ip_ops"

    def _build_ivfflat_query(
        self, index_name: str, table_name: str, column_name: str, opclass: str, lists: int
    ) -> str:
        """
        Build IVFFlat index creation query.
        
        Args:
            index_name (str): Name for the index.
            table_name (str): Table name.
            column_name (str): Column name.
            opclass (str): Operator class.
            lists (int): Number of lists for IVFFlat.
        
        Returns:
            str: SQL query string.
        """
        return f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON {table_name} USING ivfflat ({column_name} {opclass})
        WITH (lists = {lists});
        """

    def _build_hnsw_query(
        self,
        index_name: str,
        table_name: str,
        column_name: str,
        opclass: str,
        m: int,
        ef_construction: int,
    ) -> str:
        """
        Build HNSW index creation query.
        
        Args:
            index_name (str): Name for the index.
            table_name (str): Table name.
            column_name (str): Column name.
            opclass (str): Operator class.
            m (int): HNSW m parameter.
            ef_construction (int): HNSW ef_construction parameter.
        
        Returns:
            str: SQL query string.
        """
        return f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON {table_name} USING hnsw ({column_name} {opclass})
        WITH (m = {m}, ef_construction = {ef_construction});
        """

    async def create_index(
        self,
        table_name: str = "embeddings",
        column_name: str = "embedding",
        index_type: IndexType = IndexType.IVFFLAT,
        distance: IndexDistance = IndexDistance.COSINE,
        lists: Optional[int] = None,  # For IVFFlat
        m: Optional[int] = None,  # For HNSW
        ef_construction: Optional[int] = None,  # For HNSW
        tenant_id: Optional[str] = None,
    ) -> str:
        """
        Create a vector index on the specified table and column asynchronously.
        
        Args:
            table_name (str): Table name.
            column_name (str): Column name.
            index_type (IndexType): Type of index (IVFFLAT or HNSW).
            distance (IndexDistance): Distance metric.
            lists (Optional[int]): Number of lists for IVFFlat.
            m (Optional[int]): HNSW m parameter.
            ef_construction (Optional[int]): HNSW ef_construction parameter.
            tenant_id (Optional[str]): Tenant identifier for multi-tenancy.
        
        Returns:
            str: The name of the created or existing index.
        
        Raises:
            DatabaseError: If index creation fails.
        """
        index_name = self._get_index_name(table_name, column_name, index_type, tenant_id)

        # Check if index already exists
        if await self.index_exists(index_name):
            logger.info(f"Index {index_name} already exists")
            return index_name

        # Get distance operator class
        opclass = self._get_distance_opclass(distance)

        # Build index creation query based on type
        if index_type == IndexType.IVFFLAT:
            # Calculate lists parameter if not provided
            if lists is None:
                row_count = await self._get_table_row_count(table_name, tenant_id)
                lists = max(100, int(row_count**0.5)) if row_count > 0 else 100
                logger.info(f"Calculated IVFFlat lists: {lists} (based on {row_count} rows)")
            query = self._build_ivfflat_query(index_name, table_name, column_name, opclass, lists)
        else:  # HNSW
            # Set default parameters if not provided
            m = m or 16
            ef_construction = ef_construction or 64
            query = self._build_hnsw_query(
                index_name, table_name, column_name, opclass, m, ef_construction
            )

        try:
            await self.db.execute_query(query, fetch_all=False)
            logger.info(
                f"Created {index_type.value} index {index_name} on {table_name}.{column_name}"
            )
            return index_name
        except Exception as e:
            error_msg = f"Failed to create index {index_name}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(message=error_msg, operation="create_index", original_error=e) from e

    async def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists asynchronously.
        
        Args:
            index_name (str): Index name to check.
        
        Returns:
            bool: True if index exists.
        """
        query = """
        SELECT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE indexname = $1
        );
        """
        result = await self.db.execute_query(query, (index_name,), fetch_one=True)
        return result.get("exists", False) if result else False

    async def get_index_info(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an index asynchronously.
        
        Args:
            index_name (str): Index name.
        
        Returns:
            Optional[Dict[str, Any]]: Index information or None.
        """
        query = """
        SELECT
            i.indexname,
            i.tablename,
            i.indexdef,
            pg_size_pretty(pg_relation_size(i.indexname::regclass)) as index_size,
            idx.indisvalid as is_valid,
            idx.indisready as is_ready
        FROM pg_indexes i
        JOIN pg_class c ON c.relname = i.indexname
        JOIN pg_index idx ON idx.indexrelid = c.oid
        WHERE i.indexname = $1;
        """

        result = await self.db.execute_query(query, (index_name,), fetch_one=True)
        return result

    async def list_indexes(
        self, table_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all vector indexes asynchronously.
        
        Args:
            table_name (Optional[str]): Filter by table name.
        
        Returns:
            List[Dict[str, Any]]: List of index information.
        """
        if table_name:
            query = """
            SELECT
                i.indexname,
                i.tablename,
                i.indexdef,
                pg_size_pretty(pg_relation_size(i.indexname::regclass)) as index_size
            FROM pg_indexes i
            WHERE i.tablename = $1
                AND (i.indexdef LIKE '%ivfflat%' OR i.indexdef LIKE '%hnsw%')
            ORDER BY i.indexname;
            """
            results = await self.db.execute_query(query, (table_name,))
        else:
            query = """
            SELECT
                i.indexname,
                i.tablename,
                i.indexdef,
                pg_size_pretty(pg_relation_size(i.indexname::regclass)) as index_size
            FROM pg_indexes i
            WHERE i.indexdef LIKE '%ivfflat%' OR i.indexdef LIKE '%hnsw%'
            ORDER BY i.tablename, i.indexname;
            """
            results = await self.db.execute_query(query)

        return results or []

    async def reindex(self, index_name: str, concurrently: bool = False) -> bool:
        """
        Rebuild an existing index asynchronously.
        
        Args:
            index_name (str): Index name to rebuild.
            concurrently (bool): Whether to reindex concurrently.
        
        Returns:
            bool: True if reindex successful.
        
        Raises:
            VectorIndexError: If index doesn't exist or reindex fails.
        """
        if not await self.index_exists(index_name):
            error_msg = f"Index {index_name} does not exist"
            logger.error(error_msg)
            raise VectorIndexError(message=error_msg, index_name=index_name)

        try:
            if concurrently:
                # CONCURRENTLY requires separate transaction
                query = f"REINDEX INDEX CONCURRENTLY {index_name};"
            else:
                query = f"REINDEX INDEX {index_name};"

            await self.db.execute_query(query, fetch_all=False)
            logger.info(f"Reindexed {index_name} (concurrent: {concurrently})")
            return True
        except Exception as e:
            error_msg = f"Failed to reindex {index_name}: {str(e)}"
            logger.error(error_msg)
            raise VectorIndexError(message=error_msg, index_name=index_name, original_error=e) from e

    async def reindex_table(
        self, table_name: str, concurrently: bool = False
    ) -> List[str]:
        """
        Reindex all vector indexes on a table asynchronously.
        
        Args:
            table_name (str): Table name.
            concurrently (bool): Whether to reindex concurrently.
        
        Returns:
            List[str]: List of reindexed index names.
        """
        indexes = await self.list_indexes(table_name=table_name)
        reindexed = []

        for index_info in indexes:
            index_name = index_info["indexname"]
            try:
                await self.reindex(index_name, concurrently=concurrently)
                reindexed.append(index_name)
            except Exception as e:
                logger.warning(f"Failed to reindex {index_name}: {str(e)}")
                continue

        return reindexed

    async def drop_index(self, index_name: str, if_exists: bool = True) -> Optional[str]:
        """
        Drop an index asynchronously.
        
        Args:
            index_name (str): Index name to drop.
            if_exists (bool): Only drop if exists.
        
        Returns:
            Optional[str]: The name of the dropped index, or None if it didn't exist and if_exists=True.
        
        Raises:
            DatabaseError: If drop fails.
        """
        if if_exists and not await self.index_exists(index_name):
            logger.info(f"Index {index_name} does not exist, skipping drop")
            return None

        try:
            query = f"DROP INDEX IF EXISTS {index_name};"
            await self.db.execute_query(query, fetch_all=False)
            logger.info(f"Dropped index {index_name}")
            return index_name
        except Exception as e:
            error_msg = f"Failed to drop index {index_name}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(message=error_msg, operation="drop_index", original_error=e) from e

    async def auto_reindex_on_embedding_change(
        self,
        table_name: str = "embeddings",
        column_name: str = "embedding",
        index_type: Optional[IndexType] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Automatically reindex when embeddings change significantly (async).
        
        This should be called after bulk embedding updates or model changes.
        
        Args:
            table_name (str): Table name.
            column_name (str): Column name.
            index_type (Optional[IndexType]): Specific index type to reindex.
            tenant_id (Optional[str]): Tenant identifier.
        
        Returns:
            bool: True if reindex successful.
        """
        if index_type:
            index_name = self._get_index_name(table_name, column_name, index_type, tenant_id)
            if await self.index_exists(index_name):
                return await self.reindex(index_name, concurrently=True)
            else:
                logger.warning(f"Index {index_name} does not exist, skipping reindex")
                return False
        else:
            # Reindex all indexes on the table
            reindexed = await self.reindex_table(table_name, concurrently=True)
            return len(reindexed) > 0

    async def get_index_statistics(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics about an index asynchronously.
        
        Args:
            index_name (str): Index name.
        
        Returns:
            Optional[Dict[str, Any]]: Index statistics or None.
        """
        if not await self.index_exists(index_name):
            return None

        # Note: pg_stat functions require index OID, not name
        # We need to get the OID first
        oid_query = """
        SELECT oid FROM pg_class WHERE relname = $1;
        """
        oid_result = await self.db.execute_query(oid_query, (index_name,), fetch_one=True)
        
        if not oid_result or not oid_result.get("oid"):
            return None
        
        index_oid = oid_result["oid"]
        
        query = """
        SELECT
            pg_size_pretty(pg_relation_size($1)) as size,
            pg_stat_get_numscans($1) as num_scans,
            pg_stat_get_tuples_returned($1) as tuples_returned,
            pg_stat_get_tuples_fetched($1) as tuples_fetched
        """

        result = await self.db.execute_query(
            query, (index_oid,), fetch_one=True
        )
        return result

    def _get_index_name(
        self,
        table_name: str,
        column_name: str,
        index_type: IndexType,
        tenant_id: Optional[str] = None,
    ) -> str:
        """
        Generate index name.
        
        Args:
            table_name (str): Table name.
            column_name (str): Column name.
            index_type (IndexType): Index type.
            tenant_id (Optional[str]): Tenant identifier.
        
        Returns:
            str: Generated index name.
        """
        base_name = f"{table_name}_{column_name}_{index_type.value}_idx"
        if tenant_id:
            base_name = f"{base_name}_{tenant_id}"
        return base_name

    async def _get_table_row_count(self, table_name: str, tenant_id: Optional[str] = None) -> int:
        """
        Get row count for a table asynchronously.
        
        Args:
            table_name (str): Table name.
            tenant_id (Optional[str]): Tenant identifier.
        
        Returns:
            int: Row count.
        """
        if tenant_id:
            query = f"SELECT COUNT(*) as count FROM {table_name} WHERE tenant_id = $1;"
            result = await self.db.execute_query(query, (tenant_id,), fetch_one=True)
        else:
            query = f"SELECT COUNT(*) as count FROM {table_name};"
            result = await self.db.execute_query(query, fetch_one=True)

        return result.get("count", 0) if result else 0


def create_vector_index_manager(db: DatabaseConnection) -> VectorIndexManager:
    """
    Create a vector index manager instance.

    Args:
        db: Database connection

    Returns:
        VectorIndexManager instance
    """
    return VectorIndexManager(db)
