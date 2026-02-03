"""
Vector Index Management

Provides comprehensive index management for pgvector, including creation,
monitoring, and reindexing of IVFFlat and HNSW indexes.
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
        __init__.
        
        Args:
            message (str): Input parameter for this operation.
            operation (Optional[str]): Input parameter for this operation.
            original_error (Optional[Exception]): Input parameter for this operation.
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
        __init__.
        
        Args:
            message (str): Input parameter for this operation.
            index_name (Optional[str]): Input parameter for this operation.
            original_error (Optional[Exception]): Input parameter for this operation.
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
            distance (IndexDistance): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
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
            index_name (str): Input parameter for this operation.
            table_name (str): Input parameter for this operation.
            column_name (str): Input parameter for this operation.
            opclass (str): Input parameter for this operation.
            lists (int): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
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
            index_name (str): Input parameter for this operation.
            table_name (str): Input parameter for this operation.
            column_name (str): Input parameter for this operation.
            opclass (str): Input parameter for this operation.
            m (int): Input parameter for this operation.
            ef_construction (int): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        return f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON {table_name} USING hnsw ({column_name} {opclass})
        WITH (m = {m}, ef_construction = {ef_construction});
        """

    def create_index(  # noqa: S3516
        self,
        table_name: str = "embeddings",
        column_name: str = "embedding",
        index_type: IndexType = IndexType.IVFFLAT,
        distance: IndexDistance = IndexDistance.COSINE,
        lists: Optional[int] = None,  # For IVFFlat
        m: Optional[int] = None,  # For HNSW
        ef_construction: Optional[int] = None,  # For HNSW
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Create a vector index on the specified table and column.
        
        Args:
            table_name (str): Input parameter for this operation.
            column_name (str): Input parameter for this operation.
            index_type (IndexType): Input parameter for this operation.
            distance (IndexDistance): Input parameter for this operation.
            lists (Optional[int]): Input parameter for this operation.
            m (Optional[int]): Input parameter for this operation.
            ef_construction (Optional[int]): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        
        Raises:
            DatabaseError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        index_name = self._get_index_name(table_name, column_name, index_type, tenant_id)

        # Check if index already exists
        if self.index_exists(index_name):
            logger.info(f"Index {index_name} already exists")
            return True

        # Get distance operator class
        opclass = self._get_distance_opclass(distance)

        # Build index creation query based on type
        if index_type == IndexType.IVFFLAT:
            # Calculate lists parameter if not provided
            if lists is None:
                row_count = self._get_table_row_count(table_name, tenant_id)
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
            self.db.execute_query(query)
            logger.info(
                f"Created {index_type.value} index {index_name} on {table_name}.{column_name}"
            )
            return True
        except Exception as e:
            error_msg = f"Failed to create index {index_name}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(message=error_msg, operation="create_index", original_error=e)

    def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists.
        
        Args:
            index_name (str): Input parameter for this operation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        query = """
        SELECT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE indexname = %s
        );
        """
        result = self.db.execute_query(query, (index_name,), fetch_one=True)
        return result.get("exists", False) if result else False

    def get_index_info(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an index.
        
        Args:
            index_name (str): Input parameter for this operation.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary result of the operation.
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
        WHERE i.indexname = %s;
        """

        result = self.db.execute_query(query, (index_name,), fetch_one=True)
        return result

    def list_indexes(
        self, table_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all vector indexes.
        
        Args:
            table_name (Optional[str]): Input parameter for this operation.
        
        Returns:
            List[Dict[str, Any]]: Dictionary result of the operation.
        """
        if table_name:
            query = """
            SELECT
                i.indexname,
                i.tablename,
                i.indexdef,
                pg_size_pretty(pg_relation_size(i.indexname::regclass)) as index_size
            FROM pg_indexes i
            WHERE i.tablename = %s
                AND (i.indexdef LIKE '%ivfflat%' OR i.indexdef LIKE '%hnsw%')
            ORDER BY i.indexname;
            """
            results = self.db.execute_query(query, (table_name,))
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
            results = self.db.execute_query(query)

        return results or []

    def reindex(self, index_name: str, concurrently: bool = False) -> bool:
        """
        Rebuild an existing index.
        
        Args:
            index_name (str): Input parameter for this operation.
            concurrently (bool): Input parameter for this operation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        
        Raises:
            VectorIndexError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if not self.index_exists(index_name):
            error_msg = f"Index {index_name} does not exist"
            logger.error(error_msg)
            raise VectorIndexError(message=error_msg, index_name=index_name)

        try:
            if concurrently:
                # CONCURRENTLY requires separate transaction
                query = f"REINDEX INDEX CONCURRENTLY {index_name};"
            else:
                query = f"REINDEX INDEX {index_name};"

            self.db.execute_query(query)
            logger.info(f"Reindexed {index_name} (concurrent: {concurrently})")
            return True
        except Exception as e:
            error_msg = f"Failed to reindex {index_name}: {str(e)}"
            logger.error(error_msg)
            raise VectorIndexError(message=error_msg, index_name=index_name, original_error=e)

    def reindex_table(
        self, table_name: str, concurrently: bool = False
    ) -> List[str]:
        """
        Reindex all vector indexes on a table.
        
        Args:
            table_name (str): Input parameter for this operation.
            concurrently (bool): Input parameter for this operation.
        
        Returns:
            List[str]: List result of the operation.
        """
        indexes = self.list_indexes(table_name=table_name)
        reindexed = []

        for index_info in indexes:
            index_name = index_info["indexname"]
            try:
                self.reindex(index_name, concurrently=concurrently)
                reindexed.append(index_name)
            except Exception as e:
                logger.warning(f"Failed to reindex {index_name}: {str(e)}")
                continue

        return reindexed

    def drop_index(self, index_name: str, if_exists: bool = True) -> bool:  # noqa: S3516
        """
        Drop an index.
        
        Args:
            index_name (str): Input parameter for this operation.
            if_exists (bool): Input parameter for this operation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        
        Raises:
            DatabaseError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if if_exists and not self.index_exists(index_name):
            logger.info(f"Index {index_name} does not exist, skipping drop")
            return True

        try:
            query = f"DROP INDEX IF EXISTS {index_name};"
            self.db.execute_query(query)
            logger.info(f"Dropped index {index_name}")
            return True
        except Exception as e:
            error_msg = f"Failed to drop index {index_name}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(message=error_msg, operation="drop_index", original_error=e)

    def auto_reindex_on_embedding_change(
        self,
        table_name: str = "embeddings",
        column_name: str = "embedding",
        index_type: Optional[IndexType] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Automatically reindex when embeddings change significantly.
        
        This should be called after bulk embedding updates or model changes.
        
        Args:
            table_name (str): Input parameter for this operation.
            column_name (str): Input parameter for this operation.
            index_type (Optional[IndexType]): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        if index_type:
            index_name = self._get_index_name(table_name, column_name, index_type, tenant_id)
            if self.index_exists(index_name):
                return self.reindex(index_name, concurrently=True)
            else:
                logger.warning(f"Index {index_name} does not exist, skipping reindex")
                return False
        else:
            # Reindex all indexes on the table
            return len(self.reindex_table(table_name, concurrently=True)) > 0

    def get_index_statistics(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics about an index.
        
        Args:
            index_name (str): Input parameter for this operation.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary result of the operation.
        """
        if not self.index_exists(index_name):
            return None

        query = """
        SELECT
            pg_size_pretty(pg_relation_size(%s::regclass)) as size,
            pg_stat_get_numscans(%s::regclass) as num_scans,
            pg_stat_get_tuples_returned(%s::regclass) as tuples_returned,
            pg_stat_get_tuples_fetched(%s::regclass) as tuples_fetched
        """

        result = self.db.execute_query(
            query, (index_name, index_name, index_name, index_name), fetch_one=True
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
            table_name (str): Input parameter for this operation.
            column_name (str): Input parameter for this operation.
            index_type (IndexType): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            str: Returned text value.
        """
        base_name = f"{table_name}_{column_name}_{index_type.value}_idx"
        if tenant_id:
            base_name = f"{base_name}_{tenant_id}"
        return base_name

    def _get_table_row_count(self, table_name: str, tenant_id: Optional[str] = None) -> int:
        """
        Get row count for a table.
        
        Args:
            table_name (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            int: Result of the operation.
        """
        if tenant_id:
            query = f"SELECT COUNT(*) as count FROM {table_name} WHERE tenant_id = %s;"
            result = self.db.execute_query(query, (tenant_id,), fetch_one=True)
        else:
            query = f"SELECT COUNT(*) as count FROM {table_name};"
            result = self.db.execute_query(query, fetch_one=True)

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
