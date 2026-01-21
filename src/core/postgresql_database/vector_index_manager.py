"""
Vector Index Management

Provides comprehensive index management for pgvector, including creation,
monitoring, and reindexing of IVFFlat and HNSW indexes.
"""

# Standard library imports
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Local application/library specific imports
from .connection import DatabaseConnection


class DatabaseError(Exception):
    """Database operation error."""
    def __init__(self, message: str, operation: Optional[str] = None, original_error: Optional[Exception] = None):
        self.message = message
        self.operation = operation
        self.original_error = original_error
        super().__init__(self.message)


class IndexError_(Exception):
    """Index operation error."""
    def __init__(self, message: str, index_name: Optional[str] = None, original_error: Optional[Exception] = None):
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
            db: Database connection
        """
        self.db = db
    
    def create_index(
        self,
        table_name: str = "embeddings",
        column_name: str = "embedding",
        index_type: IndexType = IndexType.IVFFLAT,
        distance: IndexDistance = IndexDistance.COSINE,
        lists: Optional[int] = None,  # For IVFFlat
        m: Optional[int] = None,  # For HNSW
        ef_construction: Optional[int] = None,  # For HNSW
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Create a vector index on the specified table and column.
        
        Args:
            table_name: Name of the table containing vectors
            column_name: Name of the vector column
            index_type: Type of index (IVFFlat or HNSW)
            distance: Distance metric (cosine, l2, inner_product)
            lists: Number of lists for IVFFlat (default: sqrt(rows))
            m: M parameter for HNSW (default: 16)
            ef_construction: ef_construction for HNSW (default: 64)
            tenant_id: Optional tenant ID for multi-tenancy
        
        Returns:
            True if index created successfully
        
        Raises:
            DatabaseError: If index creation fails
        """
        index_name = self._get_index_name(table_name, column_name, index_type, tenant_id)
        
        # Check if index already exists
        if self.index_exists(index_name):
            logger.info(f"Index {index_name} already exists")
            return True
        
        # Get table row count for IVFFlat lists calculation
        if index_type == IndexType.IVFFLAT and lists is None:
            row_count = self._get_table_row_count(table_name, tenant_id)
            lists = max(100, int(row_count ** 0.5)) if row_count > 0 else 100
            logger.info(f"Calculated IVFFlat lists: {lists} (based on {row_count} rows)")
        
        # Set HNSW defaults
        if index_type == IndexType.HNSW:
            m = m or 16
            ef_construction = ef_construction or 64
        
        # Build index creation query
        if index_type == IndexType.IVFFLAT:
            if distance == IndexDistance.COSINE:
                opclass = "vector_cosine_ops"
            elif distance == IndexDistance.L2:
                opclass = "vector_l2_ops"
            else:  # inner_product
                opclass = "vector_ip_ops"
            
            query = f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON {table_name} USING ivfflat ({column_name} {opclass})
            WITH (lists = {lists});
            """
        else:  # HNSW
            if distance == IndexDistance.COSINE:
                opclass = "vector_cosine_ops"
            elif distance == IndexDistance.L2:
                opclass = "vector_l2_ops"
            else:  # inner_product
                opclass = "vector_ip_ops"
            
            query = f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON {table_name} USING hnsw ({column_name} {opclass})
            WITH (m = {m}, ef_construction = {ef_construction});
            """
        
        # Add tenant filter if provided
        if tenant_id:
            # Note: PostgreSQL doesn't support filtered indexes directly,
            # but we can create a partial index if needed
            pass
        
        try:
            self.db.execute_query(query)
            logger.info(f"Created {index_type.value} index {index_name} on {table_name}.{column_name}")
            return True
        except Exception as e:
            error_msg = f"Failed to create index {index_name}: {str(e)}"
            logger.error(error_msg)
            raise DatabaseError(message=error_msg, operation="create_index", original_error=e)
    
    def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists.
        
        Args:
            index_name: Name of the index
        
        Returns:
            True if index exists
        """
        query = """
        SELECT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE indexname = %s
        );
        """
        result = self.db.execute_query(query, (index_name,), fetch_one=True)
        return result.get('exists', False) if result else False
    
    def get_index_info(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an index.
        
        Args:
            index_name: Name of the index
        
        Returns:
            Dictionary with index information or None if not found
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
        self,
        table_name: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all vector indexes.
        
        Args:
            table_name: Optional table name filter
            tenant_id: Optional tenant ID filter
        
        Returns:
            List of index information dictionaries
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
    
    def reindex(
        self,
        index_name: str,
        concurrently: bool = False
    ) -> bool:
        """
        Rebuild an existing index.
        
        Args:
            index_name: Name of the index to rebuild
            concurrently: Whether to rebuild concurrently (non-blocking)
        
        Returns:
            True if reindexing successful
        
        Raises:
            IndexError_: If index doesn't exist or reindexing fails
        """
        if not self.index_exists(index_name):
            error_msg = f"Index {index_name} does not exist"
            logger.error(error_msg)
            raise IndexError_(message=error_msg, index_name=index_name)
        
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
            raise IndexError_(message=error_msg, index_name=index_name, original_error=e)
    
    def reindex_table(
        self,
        table_name: str,
        concurrently: bool = False,
        tenant_id: Optional[str] = None
    ) -> List[str]:
        """
        Reindex all vector indexes on a table.
        
        Args:
            table_name: Name of the table
            concurrently: Whether to rebuild concurrently
            tenant_id: Optional tenant ID
        
        Returns:
            List of reindexed index names
        """
        indexes = self.list_indexes(table_name=table_name, tenant_id=tenant_id)
        reindexed = []
        
        for index_info in indexes:
            index_name = index_info['indexname']
            try:
                self.reindex(index_name, concurrently=concurrently)
                reindexed.append(index_name)
            except Exception as e:
                logger.warning(f"Failed to reindex {index_name}: {str(e)}")
                continue
        
        return reindexed
    
    def drop_index(self, index_name: str, if_exists: bool = True) -> bool:
        """
        Drop an index.
        
        Args:
            index_name: Name of the index to drop
            if_exists: Whether to ignore error if index doesn't exist
        
        Returns:
            True if index dropped successfully
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
        tenant_id: Optional[str] = None
    ) -> bool:
        """
        Automatically reindex when embeddings change significantly.
        
        This should be called after bulk embedding updates or model changes.
        
        Args:
            table_name: Name of the embeddings table
            column_name: Name of the embedding column
            index_type: Optional specific index type to reindex
            tenant_id: Optional tenant ID
        
        Returns:
            True if reindexing completed
        """
        if index_type:
            index_name = self._get_index_name(table_name, column_name, index_type, tenant_id)
            if self.index_exists(index_name):
                return self.reindex(index_name, concurrently=True)
        else:
            # Reindex all indexes on the table
            return len(self.reindex_table(table_name, concurrently=True, tenant_id=tenant_id)) > 0
    
    def get_index_statistics(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics about an index.
        
        Args:
            index_name: Name of the index
        
        Returns:
            Dictionary with index statistics
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
        
        result = self.db.execute_query(query, (index_name, index_name, index_name, index_name), fetch_one=True)
        return result
    
    def _get_index_name(
        self,
        table_name: str,
        column_name: str,
        index_type: IndexType,
        tenant_id: Optional[str] = None
    ) -> str:
        """
        Generate index name.
        
        Args:
            table_name: Table name
            column_name: Column name
            index_type: Index type
            tenant_id: Optional tenant ID
        
        Returns:
            Index name
        """
        base_name = f"{table_name}_{column_name}_{index_type.value}_idx"
        if tenant_id:
            base_name = f"{base_name}_{tenant_id}"
        return base_name
    
    def _get_table_row_count(self, table_name: str, tenant_id: Optional[str] = None) -> int:
        """
        Get row count for a table.
        
        Args:
            table_name: Table name
            tenant_id: Optional tenant ID filter
        
        Returns:
            Row count
        """
        if tenant_id:
            query = f"SELECT COUNT(*) as count FROM {table_name} WHERE tenant_id = %s;"
            result = self.db.execute_query(query, (tenant_id,), fetch_one=True)
        else:
            query = f"SELECT COUNT(*) as count FROM {table_name};"
            result = self.db.execute_query(query, fetch_one=True)
        
        return result.get('count', 0) if result else 0


def create_vector_index_manager(db: DatabaseConnection) -> VectorIndexManager:
    """
    Create a vector index manager instance.
    
    Args:
        db: Database connection
    
    Returns:
        VectorIndexManager instance
    """
    return VectorIndexManager(db)

