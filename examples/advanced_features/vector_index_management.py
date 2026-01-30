"""
Vector Index Management Example

Demonstrates how to create, manage, and reindex vector indexes
for optimal RAG search performance.
"""

from src.core.litellm_gateway import create_gateway
from src.core.postgresql_database import (
    DatabaseConfig,
    DatabaseConnection,
    IndexDistance,
    IndexType,
    VectorIndexManager,
)
from src.core.rag import create_rag_system


def main():
    # Initialize database
    db_config = DatabaseConfig.from_env()
    db = DatabaseConnection(db_config)

    # Initialize gateway
    gateway = create_gateway(api_keys={"openai": "sk-..."})

    # Create RAG system
    rag = create_rag_system(
        db=db, gateway=gateway, embedding_model="text-embedding-3-small", generation_model="gpt-4"
    )

    # Example 1: Create IVFFlat index (good for large datasets)
    print("Creating IVFFlat index...")
    success = rag.create_index(
        index_type=IndexType.IVFFLAT,
        distance=IndexDistance.COSINE,
        lists=100,  # Number of lists (auto-calculated if not provided)
    )
    print(f"Index creation: {'Success' if success else 'Failed'}")

    # Example 2: Create HNSW index (better for high-dimensional vectors)
    print("\nCreating HNSW index...")
    success = rag.create_index(
        index_type=IndexType.HNSW,
        distance=IndexDistance.COSINE,
        m=16,  # M parameter
        ef_construction=64,  # ef_construction parameter
    )
    print(f"Index creation: {'Success' if success else 'Failed'}")

    # Example 3: Get index information
    print("\nIndex Information:")
    indexes = rag.get_index_info()
    for idx in indexes:
        print(f"  - {idx['indexname']}: {idx.get('index_size', 'N/A')}")

    # Example 4: Reindex after embedding model change
    print("\nReindexing indexes (after model change)...")
    reindexed = rag.reindex(concurrently=True)  # Non-blocking
    print(f"Reindexed {len(reindexed)} indexes: {reindexed}")

    # Example 5: Direct index manager usage
    print("\nUsing index manager directly...")
    index_manager = VectorIndexManager(db)

    # Check if index exists
    index_name = "embeddings_embedding_ivfflat_idx"
    exists = index_manager.index_exists(index_name)
    print(f"Index {index_name} exists: {exists}")

    # Get index statistics
    if exists:
        stats = index_manager.get_index_statistics(index_name)
        if stats:
            print(f"Index statistics: {stats}")


if __name__ == "__main__":
    main()
