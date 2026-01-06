# Unit Tests

## Instructions for Running Unit Tests

### Setup

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Install the SDK in development mode
pip install -e .
```

### Running Tests

```bash
# Run all unit tests
pytest src/tests/unit_tests/

# Run specific test file
pytest src/tests/unit_tests/test_litellm_gateway.py

# Run function-driven API tests
pytest src/tests/unit_tests/test_agent_functions.py
pytest src/tests/unit_tests/test_rag_functions.py
pytest src/tests/unit_tests/test_cache_functions.py
pytest src/tests/unit_tests/test_api_functions.py

# Run all function-driven API tests
pytest src/tests/unit_tests/ -k "functions"

# Run with coverage
pytest src/tests/unit_tests/ --cov=src --cov-report=html

# Run in verbose mode
pytest src/tests/unit_tests/ -v
```

### Test Structure

Tests are organized by component:

```
unit_tests/
├── Component Tests (Class-based)
│   ├── test_agent.py                    # Agent framework class tests
│   ├── test_cache.py                    # Cache mechanism class tests
│   ├── test_litellm_gateway.py          # LiteLLM Gateway class tests
│   ├── test_rag.py                      # RAG system class tests
│   ├── test_postgresql_database.py      # Database tests
│   ├── test_pool_implementation.py      # Pool implementation tests
│   └── test_observability.py           # Observability tests
│
└── Function-Driven API Tests
    ├── test_agent_functions.py          # Agent framework functions tests
    ├── test_rag_functions.py           # RAG system functions tests
    ├── test_cache_functions.py         # Cache mechanism functions tests
    ├── test_api_functions.py            # API backend functions tests
    ├── test_litellm_gateway_functions.py # LiteLLM Gateway functions tests
    └── test_prompt_context_functions.py # Prompt context functions tests
```

### Function-Driven API Tests

The SDK provides comprehensive test coverage for the function-driven API:

- **Factory Functions**: Test component creation with various configurations
- **Convenience Functions**: Test high-level operations and integrations
- **Utility Functions**: Test batch operations, retries, and common patterns

Each function test file includes:
- Factory function tests (create_*, configure_*)
- Convenience function tests (high-level operations)
- Utility function tests (batch processing, retries, etc.)
- Edge case and error handling tests

## Testing Framework Used

- **pytest**: Primary testing framework
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **pytest-cov**: Coverage reporting

## Structure of Test Cases

### Basic Test Structure

```python
import pytest
from src.core.litellm_gateway import LiteLLMGateway

class TestGateway:
    def test_generate_text(self):
        """Test text generation."""
        gateway = LiteLLMGateway()
        response = gateway.generate(
            prompt="Hello",
            model="gpt-4"
        )
        assert response.text is not None
        assert len(response.text) > 0
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_generation():
    """Test async text generation."""
    gateway = LiteLLMGateway()
    response = await gateway.generate_async(
        prompt="Hello",
        model="gpt-4"
    )
    assert response.text is not None
```

### Mocked Tests

```python
from unittest.mock import Mock, patch

def test_gateway_with_mock():
    """Test gateway with mocked LLM."""
    with patch('litellm.completion') as mock_completion:
        mock_completion.return_value = Mock(
            choices=[Mock(message=Mock(content="Test response"))]
        )
        
        gateway = LiteLLMGateway()
        response = gateway.generate("Hello", "gpt-4")
        
        assert response.text == "Test response"
```

### Fixtures

```python
import pytest

@pytest.fixture
def gateway():
    """Gateway fixture."""
    return LiteLLMGateway()

@pytest.fixture
def sample_document():
    """Sample document fixture."""
    return {
        "title": "Test Document",
        "content": "Test content..."
    }

def test_with_fixtures(gateway, sample_document):
    """Test using fixtures."""
    result = gateway.process(sample_document)
    assert result is not None
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Use Fixtures**: Reuse common test setup
3. **Mock External Dependencies**: Mock API calls and external services
4. **Test Edge Cases**: Test error conditions and edge cases
5. **Maintain Coverage**: Aim for >80% code coverage

