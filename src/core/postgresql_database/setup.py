"""
Database Setup and Initialization

Provides functions for initializing the database with pgvector extension,
creating necessary tables, and setting up vector indexes.
"""


import logging
from typing import Any, Dict, Optional

from .connection import DatabaseConnection

logger = logging.getLogger(__name__)


async def create_pgvector_extension(db: DatabaseConnection) -> bool:
    """
    Create pgvector extension in the database.
    
    Args:
        db: Database connection instance.
    
    Returns:
        bool: True if extension was created or already exists, False otherwise.
    """
    # OTEL Integration (optional)
    tracer = None
    try:
        from ..otel_integration import create_otel_tracer
        tracer = create_otel_tracer(service_name="database-setup")
    except (ImportError, Exception):
        tracer = None
    
    if tracer:
        with tracer.start_trace("setup.create_pgvector_extension") as trace:
            trace.set_attribute("operation", "create_pgvector_extension")
            
            try:
                result = await db.create_pgvector_extension()
                trace.set_attribute("extension.created", str(result))
                return result
            except Exception as e:
                trace.record_exception(e)
                logger.error(f"Failed to create pgvector extension: {e}")
                return False
    else:
        # No OTEL - execute without tracing
        try:
            return await db.create_pgvector_extension()
        except Exception as e:
            logger.error(f"Failed to create pgvector extension: {e}")
            return False


async def verify_pgvector_extension(db: DatabaseConnection) -> bool:
    """
    Verify if pgvector extension is installed.
    
    Args:
        db: Database connection instance.
    
    Returns:
        bool: True if extension exists, False otherwise.
    """
    # OTEL Integration (optional)
    tracer = None
    try:
        from ..otel_integration import create_otel_tracer
        tracer = create_otel_tracer(service_name="database-setup")
    except (ImportError, Exception):
        tracer = None
    
    if tracer:
        with tracer.start_trace("setup.verify_pgvector_extension") as trace:
            trace.set_attribute("operation", "verify_pgvector_extension")
            
            try:
                result = await db.verify_pgvector_extension()
                trace.set_attribute("extension.exists", str(result))
                return result
            except Exception as e:
                trace.record_exception(e)
                logger.error(f"Failed to verify pgvector extension: {e}")
                return False
    else:
        # No OTEL - execute without tracing
        try:
            return await db.verify_pgvector_extension()
        except Exception as e:
            logger.error(f"Failed to verify pgvector extension: {e}")
            return False


async def create_embeddings_table(db: DatabaseConnection, dimension: int = 1536) -> bool:
    """
    Create embeddings table with pgvector support.
    
    Args:
        db: Database connection instance.
        dimension: Embedding vector dimension (default: 1536).
    
    Returns:
        bool: True if table was created or already exists, False otherwise.
    """
    # OTEL Integration (optional)
    tracer = None
    try:
        from ..otel_integration import create_otel_tracer
        tracer = create_otel_tracer(service_name="database-setup")
    except (ImportError, Exception):
        tracer = None
    
    if tracer:
        with tracer.start_trace("setup.create_embeddings_table") as trace:
            trace.set_attribute("operation", "create_embeddings_table")
            trace.set_attribute("dimension", dimension)
            
            try:
                query = f"""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER NOT NULL,
                    embedding vector({dimension}) NOT NULL,
                    model TEXT NOT NULL,
                    metadata JSONB,
                    tenant_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_embeddings_document_id ON embeddings(document_id);
                CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model);
                CREATE INDEX IF NOT EXISTS idx_embeddings_tenant_id ON embeddings(tenant_id) WHERE tenant_id IS NOT NULL;
                """
                
                await db.execute_query(query, fetch_all=False)
                trace.set_attribute("table.created", "true")
                return True
            except Exception as e:
                trace.record_exception(e)
                logger.error(f"Failed to create embeddings table: {e}")
                return False
    else:
        # No OTEL - execute without tracing
        try:
            query = f"""
            CREATE TABLE IF NOT EXISTS embeddings (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL,
                embedding vector({dimension}) NOT NULL,
                model TEXT NOT NULL,
                metadata JSONB,
                tenant_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_embeddings_document_id ON embeddings(document_id);
            CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model);
            CREATE INDEX IF NOT EXISTS idx_embeddings_tenant_id ON embeddings(tenant_id) WHERE tenant_id IS NOT NULL;
            """
            
            await db.execute_query(query, fetch_all=False)
            return True
        except Exception as e:
            logger.error(f"Failed to create embeddings table: {e}")
            return False


async def create_documents_table(db: DatabaseConnection) -> bool:
    """
    Create documents table.
    
    Args:
        db: Database connection instance.
    
    Returns:
        bool: True if table was created or already exists, False otherwise.
    """
    # OTEL Integration (optional)
    tracer = None
    try:
        from ..otel_integration import create_otel_tracer
        tracer = create_otel_tracer(service_name="database-setup")
    except (ImportError, Exception):
        tracer = None
    
    if tracer:
        with tracer.start_trace("setup.create_documents_table") as trace:
            trace.set_attribute("operation", "create_documents_table")
            
            try:
                query = """
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    source TEXT,
                    tenant_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_documents_tenant_id ON documents(tenant_id) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source) WHERE source IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
                """
                
                await db.execute_query(query, fetch_all=False)
                trace.set_attribute("table.created", "true")
                return True
            except Exception as e:
                trace.record_exception(e)
                logger.error(f"Failed to create documents table: {e}")
                return False
    else:
        # No OTEL - execute without tracing
        try:
            query = """
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata JSONB,
                source TEXT,
                tenant_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_documents_tenant_id ON documents(tenant_id) WHERE tenant_id IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source) WHERE source IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
            """
            
            await db.execute_query(query, fetch_all=False)
            return True
        except Exception as e:
            logger.error(f"Failed to create documents table: {e}")
            return False


async def verify_tables_exist(db: DatabaseConnection) -> Dict[str, Any]:
    """
    Verify that required tables exist.
    
    Args:
        db: Database connection instance.
    
    Returns:
        Dict[str, bool]: Dictionary mapping table names to existence status.
    """
    # OTEL Integration (optional)
    tracer = None
    try:
        from ..otel_integration import create_otel_tracer
        tracer = create_otel_tracer(service_name="database-setup")
    except (ImportError, Exception):
        tracer = None
    
    if tracer:
        with tracer.start_trace("setup.verify_tables_exist") as trace:
            trace.set_attribute("operation", "verify_tables_exist")
            
            try:
                query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                    AND table_name IN ('embeddings', 'documents');
                """
                
                results = await db.execute_query(query, fetch_all=True)
                
                existing_tables = {row["table_name"] for row in results} if results else set()
                
                status = {
                    "embeddings": "embeddings" in existing_tables,
                    "documents": "documents" in existing_tables,
                }
                
                trace.set_attribute("embeddings.exists", str(status["embeddings"]))
                trace.set_attribute("documents.exists", str(status["documents"]))
                
                return status
            except Exception as e:
                trace.record_exception(e)
                logger.error(f"Failed to verify tables: {e}")
                return {"embeddings": False, "documents": False}
    else:
        # No OTEL - execute without tracing
        try:
            query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
                AND table_name IN ('embeddings', 'documents');
            """
            
            results = await db.execute_query(query, fetch_all=True)
            
            existing_tables = {row["table_name"] for row in results} if results else set()
            
            return {
                "embeddings": "embeddings" in existing_tables,
                "documents": "documents" in existing_tables,
            }
        except Exception as e:
            logger.error(f"Failed to verify tables: {e}")
            return {"embeddings": False, "documents": False}


async def setup_vector_indexes(
    db: DatabaseConnection,
    index_type: str = "ivfflat",
    dimension: int = 1536,
) -> bool:
    """
    Setup vector indexes on embeddings table.
    
    Args:
        db: Database connection instance.
        index_type: Index type ('ivfflat' or 'hnsw', default: 'ivfflat').
        dimension: Embedding vector dimension (default: 1536).
    
    Returns:
        bool: True if indexes were created or already exist, False otherwise.
    """
    # OTEL Integration (optional)
    tracer = None
    try:
        from ..otel_integration import create_otel_tracer
        tracer = create_otel_tracer(service_name="database-setup")
    except (ImportError, Exception):
        tracer = None
    
    if tracer:
        with tracer.start_trace("setup.setup_vector_indexes") as trace:
            trace.set_attribute("operation", "setup_vector_indexes")
            trace.set_attribute("index_type", index_type)
            trace.set_attribute("dimension", dimension)
            
            try:
                # Use VectorIndexManager for index creation
                from .vector_index_manager import VectorIndexManager, IndexType, IndexDistance
                
                index_manager = VectorIndexManager(db)
                
                # Determine index type
                if index_type.lower() == "hnsw":
                    idx_type = IndexType.HNSW
                else:
                    idx_type = IndexType.IVFFLAT
                
                # Create index on embeddings table
                result = await index_manager.create_index(
                    table_name="embeddings",
                    column_name="embedding",
                    index_type=idx_type,
                    distance=IndexDistance.COSINE,
                )
                
                trace.set_attribute("index.created", "true" if result else "false")
                return result is not None
            except Exception as e:
                trace.record_exception(e)
                logger.error(f"Failed to setup vector indexes: {e}")
                return False
    else:
        # No OTEL - execute without tracing
        try:
            # Use VectorIndexManager for index creation
            from .vector_index_manager import VectorIndexManager, IndexType, IndexDistance
            
            index_manager = VectorIndexManager(db)
            
            # Determine index type
            if index_type.lower() == "hnsw":
                idx_type = IndexType.HNSW
            else:
                idx_type = IndexType.IVFFLAT
            
            # Create index on embeddings table
            result = await index_manager.create_index(
                table_name="embeddings",
                column_name="embedding",
                index_type=idx_type,
                distance=IndexDistance.COSINE,
            )
            
            return result is not None
        except Exception as e:
            logger.error(f"Failed to setup vector indexes: {e}")
            return False


async def verify_setup(db: DatabaseConnection) -> Dict[str, Any]:
    """
    Verify complete database setup including extension, tables, and indexes.
    
    Args:
        db: Database connection instance.
    
    Returns:
        Dict[str, Any]: Complete setup verification status.
    """
    # OTEL Integration (optional)
    tracer = None
    try:
        from ..otel_integration import create_otel_tracer
        tracer = create_otel_tracer(service_name="database-setup")
    except (ImportError, Exception):
        tracer = None
    
    if tracer:
        with tracer.start_trace("setup.verify_setup") as trace:
            trace.set_attribute("operation", "verify_setup")
            
            try:
                status = {
                    "connection": False,
                    "pgvector_extension": False,
                    "tables": {},
                    "indexes": {},
                }
                
                # Check connection
                status["connection"] = await db.check_connection()
                
                if not status["connection"]:
                    trace.set_attribute("setup.status", "connection_failed")
                    return status
                
                # Check pgvector extension
                status["pgvector_extension"] = await verify_pgvector_extension(db)
                
                # Check tables
                status["tables"] = await verify_tables_exist(db)
                
                # Check indexes
                try:
                    query = """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = 'embeddings'
                        AND indexname LIKE '%embedding%';
                    """
                    results = await db.execute_query(query, fetch_all=True)
                    existing_indexes = {row["indexname"] for row in results} if results else set()
                    status["indexes"] = {
                        "embeddings_embedding": len(existing_indexes) > 0,
                        "indexes_list": list(existing_indexes),
                    }
                except Exception as e:
                    logger.warning(f"Failed to check indexes: {e}")
                    status["indexes"] = {"error": str(e)}
                
                trace.set_attribute("setup.status", "complete")
                trace.set_attribute("extension.available", str(status["pgvector_extension"]))
                
                return status
            except Exception as e:
                trace.record_exception(e)
                logger.error(f"Failed to verify setup: {e}")
                return {"error": str(e)}
    else:
        # No OTEL - execute without tracing
        try:
            status = {
                "connection": False,
                "pgvector_extension": False,
                "tables": {},
                "indexes": {},
            }
            
            # Check connection
            status["connection"] = await db.check_connection()
            
            if not status["connection"]:
                return status
            
            # Check pgvector extension
            status["pgvector_extension"] = await verify_pgvector_extension(db)
            
            # Check tables
            status["tables"] = await verify_tables_exist(db)
            
            # Check indexes
            try:
                query = """
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'embeddings'
                    AND indexname LIKE '%embedding%';
                """
                results = await db.execute_query(query, fetch_all=True)
                existing_indexes = {row["indexname"] for row in results} if results else set()
                status["indexes"] = {
                    "embeddings_embedding": len(existing_indexes) > 0,
                    "indexes_list": list(existing_indexes),
                }
            except Exception as e:
                logger.warning(f"Failed to check indexes: {e}")
                status["indexes"] = {"error": str(e)}
            
            return status
        except Exception as e:
            logger.error(f"Failed to verify setup: {e}")
            return {"error": str(e)}


async def setup_database(
    db: DatabaseConnection,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Complete database setup including extension, tables, and indexes.
    
    Args:
        db: Database connection instance.
        config: Optional configuration dictionary with:
            - dimension: Embedding dimension (default: 1536)
            - index_type: Index type 'ivfflat' or 'hnsw' (default: 'ivfflat')
            - create_extension: Whether to create extension if missing (default: True)
            - create_tables: Whether to create tables (default: True)
            - create_indexes: Whether to create indexes (default: True)
    
    Returns:
        Dict[str, Any]: Dictionary with setup results for each step (may include error messages).
    """
    if config is None:
        config = {}
    
    dimension = config.get("dimension", 1536)
    index_type = config.get("index_type", "ivfflat")
    create_extension = config.get("create_extension", True)
    create_tables = config.get("create_tables", True)
    create_indexes = config.get("create_indexes", True)
    
    # OTEL Integration (optional)
    tracer = None
    try:
        from ..otel_integration import create_otel_tracer
        tracer = create_otel_tracer(service_name="database-setup")
    except (ImportError, Exception):
        tracer = None
    
    if tracer:
        with tracer.start_trace("setup.setup_database") as trace:
            trace.set_attribute("operation", "setup_database")
            trace.set_attribute("dimension", dimension)
            trace.set_attribute("index_type", index_type)
            
            try:
                results = {
                    "connection": False,
                    "pgvector_extension": False,
                    "embeddings_table": False,
                    "documents_table": False,
                    "vector_indexes": False,
                }
                
                # Check/establish connection
                results["connection"] = await db.check_connection()
                if not results["connection"]:
                    trace.set_attribute("setup.status", "connection_failed")
                    return results
                
                # Create/verify pgvector extension
                if create_extension:
                    results["pgvector_extension"] = await create_pgvector_extension(db)
                else:
                    results["pgvector_extension"] = await verify_pgvector_extension(db)
                
                if not results["pgvector_extension"]:
                    trace.set_attribute("setup.status", "extension_missing")
                    return results
                
                # Create tables
                if create_tables:
                    results["embeddings_table"] = await create_embeddings_table(db, dimension=dimension)
                    results["documents_table"] = await create_documents_table(db)
                else:
                    table_status = await verify_tables_exist(db)
                    results["embeddings_table"] = table_status.get("embeddings", False)
                    results["documents_table"] = table_status.get("documents", False)
                
                # Create indexes
                if create_indexes and results["embeddings_table"]:
                    results["vector_indexes"] = await setup_vector_indexes(
                        db, index_type=index_type, dimension=dimension
                    )
                else:
                    # Just verify indexes exist
                    try:
                        query = """
                        SELECT COUNT(*) as count
                        FROM pg_indexes
                        WHERE tablename = 'embeddings'
                            AND indexname LIKE '%embedding%';
                        """
                        result = await db.execute_query(query, fetch_one=True)
                        results["vector_indexes"] = result.get("count", 0) > 0 if result else False
                    except Exception:
                        results["vector_indexes"] = False
                
                trace.set_attribute("setup.status", "complete")
                trace.set_attribute("extension.created", str(results["pgvector_extension"]))
                trace.set_attribute("tables.created", str(results["embeddings_table"] and results["documents_table"]))
                trace.set_attribute("indexes.created", str(results["vector_indexes"]))
                
                return results
            except Exception as e:
                trace.record_exception(e)
                logger.error(f"Database setup failed: {e}")
                return {"error": True, "message": str(e)}
    else:
        # No OTEL - execute without tracing
        try:
            results = {
                "connection": False,
                "pgvector_extension": False,
                "embeddings_table": False,
                "documents_table": False,
                "vector_indexes": False,
            }
            
            # Check/establish connection
            results["connection"] = await db.check_connection()
            if not results["connection"]:
                return results
            
            # Create/verify pgvector extension
            if create_extension:
                results["pgvector_extension"] = await create_pgvector_extension(db)
            else:
                results["pgvector_extension"] = await verify_pgvector_extension(db)
            
            if not results["pgvector_extension"]:
                return results
            
            # Create tables
            if create_tables:
                results["embeddings_table"] = await create_embeddings_table(db, dimension=dimension)
                results["documents_table"] = await create_documents_table(db)
            else:
                table_status = await verify_tables_exist(db)
                results["embeddings_table"] = table_status.get("embeddings", False)
                results["documents_table"] = table_status.get("documents", False)
            
            # Create indexes
            if create_indexes and results["embeddings_table"]:
                results["vector_indexes"] = await setup_vector_indexes(
                    db, index_type=index_type, dimension=dimension
                )
            else:
                # Just verify indexes exist
                try:
                    query = """
                    SELECT COUNT(*) as count
                    FROM pg_indexes
                    WHERE tablename = 'embeddings'
                        AND indexname LIKE '%embedding%';
                    """
                    result = await db.execute_query(query, fetch_one=True)
                    results["vector_indexes"] = result.get("count", 0) > 0 if result else False
                except Exception:
                    results["vector_indexes"] = False
            
            return results
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            return {"error": True, "message": str(e)}  

