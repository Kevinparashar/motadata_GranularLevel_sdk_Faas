"""
Hallucination Detection Example

Demonstrates how to detect hallucinations in RAG-generated responses
to ensure answers are grounded in retrieved context.
"""

from src.core.litellm_gateway import create_gateway
from src.core.postgresql_database import DatabaseConfig, DatabaseConnection
from src.core.rag import HallucinationDetector, create_rag_system


def main():
    # Initialize components
    db_config = DatabaseConfig.from_env()
    db = DatabaseConnection(db_config)

    gateway = create_gateway(api_keys={"openai": "sk-..."})

    # Create RAG system
    rag = create_rag_system(
        db=db, gateway=gateway, embedding_model="text-embedding-3-small", generation_model="gpt-4"
    )

    # Ingest some documents
    print("Ingesting documents...")
    doc_id1 = rag.ingest_document(
        title="AI Overview",
        content="Artificial Intelligence (AI) is the simulation of human intelligence by machines. "
        "Machine Learning is a subset of AI that enables systems to learn from data.",
    )
    doc_id2 = rag.ingest_document(
        title="Quantum Computing",
        content="Quantum computing uses quantum mechanical phenomena to perform computations. "
        "Qubits can exist in superposition, allowing parallel processing.",
    )
    print(f"Ingested documents: {doc_id1}, {doc_id2}")

    # Example 1: Query and then check for hallucinations manually
    print("\nQuerying and checking for hallucinations...")
    result = rag.query(query="What is artificial intelligence?", top_k=3)

    print(f"Answer: {result['answer'][:200]}...")

    # Check for hallucinations using the detector
    detector = HallucinationDetector(gateway=gateway, enable_llm_verification=True)

    hallucination_result = detector.detect(
        response=result["answer"],
        context_documents=result.get("retrieved_documents", []),
        query="What is artificial intelligence?",
    )

    print("\nHallucination Detection:")
    print(f"  Is hallucination: {hallucination_result.is_hallucination}")
    print(f"  Confidence: {hallucination_result.confidence:.2f}")
    print(f"  Grounded ratio: {hallucination_result.metadata['grounded_ratio']:.2%}")
    print(f"  Reasons: {hallucination_result.reasons}")

    # Example 2: Manual hallucination detection
    print("\nManual hallucination detection...")
    detector = HallucinationDetector(
        gateway=gateway,
        enable_llm_verification=True,
        similarity_threshold=0.7,
        min_grounded_ratio=0.6,
    )

    # Generate a response
    query_result = rag.query(query="Explain quantum computing", top_k=2)

    # Check for hallucinations
    hallucination_result = detector.detect(
        response=query_result["answer"],
        context_documents=query_result.get("retrieved_documents", []),
        query="Explain quantum computing",
    )

    print("\nHallucination Analysis:")
    print(f"  Is hallucination: {hallucination_result.is_hallucination}")
    print(f"  Confidence: {hallucination_result.confidence:.2f}")
    print(f"  Grounded sentences: {len(hallucination_result.grounded_sentences)}")
    print(f"  Ungrounded sentences: {len(hallucination_result.ungrounded_sentences)}")

    if hallucination_result.ungrounded_sentences:
        print("\nUngrounded sentences:")
        for sentence in hallucination_result.ungrounded_sentences[:3]:
            print(f"  - {sentence[:100]}...")

    # Example 3: RAG Generator with hallucination detection
    print("\nUsing RAG Generator with hallucination detection...")
    from src.core.rag import RAGGenerator

    generator = RAGGenerator(gateway=gateway, model="gpt-4", enable_hallucination_detection=True)

    # Retrieve documents
    retrieved = rag.retriever.retrieve(query="What is AI?", top_k=2)

    # Generate with hallucination check
    gen_result = generator.generate(
        query="What is AI?", context_documents=retrieved, check_hallucination=True
    )

    print(f"Generated response: {gen_result['response'][:200]}...")
    if "hallucination_result" in gen_result:
        print(f"Hallucination detected: {gen_result.get('is_hallucination', False)}")
        print(f"Confidence: {gen_result['hallucination_result']['confidence']:.2f}")


if __name__ == "__main__":
    main()
