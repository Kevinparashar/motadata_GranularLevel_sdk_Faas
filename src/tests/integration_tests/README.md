# Integration Tests

## Overview

Integration tests verify that multiple components work together correctly. They test the interaction between different parts of the SDK, including external services like databases and LLM providers.

## Purpose

Integration tests ensure:
- **Component Integration**: Components work together correctly
- **End-to-End Workflows**: Complete workflows function as expected
- **External Service Integration**: Integration with databases, APIs, etc.
- **Error Propagation**: Errors are handled correctly across components

## Test Structure

### Component Integration Tests

```python
import pytest
from src.core.litellm_gateway import LiteLLMGateway
from src.core.litellm_gateway.components.rag import RAGSystem
from src.core.litellm_gateway.components.postgresql_database import DatabaseManager

@pytest.mark.integration
def test_rag_with_database():
    """Test RAG system with database integration."""
    db = DatabaseManager()
    gateway = LiteLLMGateway()
    rag = RAGSystem(gateway=gateway, database=db)
    
    # Ingest document
    doc_id = rag.ingest_document(
        title="Test",
        content="Test content"
    )
    
    # Query
    result = rag.query("Test query")
    assert result["answer"] is not None
```

### End-to-End Tests

```python
@pytest.mark.integration
def test_complete_workflow():
    """Test complete workflow from query to response."""
    # Setup
    gateway = LiteLLMGateway()
    rag = RAGSystem(gateway=gateway)
    
    # Execute workflow
    result = rag.query("What is Python?")
    
    # Verify
    assert "answer" in result
    assert "sources" in result
    assert len(result["sources"]) > 0
```

## Running Integration Tests

```bash
# Run all integration tests
pytest src/tests/integration_tests/ -m integration

# Run with external services
pytest src/tests/integration_tests/ --external-services

# Run specific integration test
pytest src/tests/integration_tests/test_rag_integration.py
```

## Test Environment

Integration tests may require:
- **Database**: PostgreSQL with pgvector
- **API Keys**: LLM provider API keys
- **External Services**: Redis, message queues, etc.

## Best Practices

1. **Use Test Containers**: Use Docker for external services
2. **Clean Up**: Clean up test data after tests
3. **Isolate Tests**: Each test should be independent
4. **Mock When Possible**: Mock expensive external calls when appropriate
5. **Test Real Scenarios**: Test realistic use cases

