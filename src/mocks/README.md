# Mock Implementations

This directory contains **mock implementations** of SDK components for use in testing.

## Purpose

- **Mock objects**: Standalone mock implementations of SDK components
- **Test utilities**: Reusable mock classes for integration and unit tests
- **Service mocks**: Mock implementations of external services (LLM providers, databases, etc.)

## Coverage Exclusion

This directory is **excluded from code coverage** calculations:
- Pattern: `**/mock_*.py`, `**/mocks/**`
- Reason: Mock implementations are test utilities, not production code

## Structure

```
mocks/
├── __init__.py
├── mock_database.py      # Mock database implementations
├── mock_gateway.py       # Mock LLM gateway implementations
├── mock_cache.py         # Mock cache implementations
├── mock_rag.py           # Mock RAG system implementations
└── README.md
```

## Usage

### In Tests

```python
from src.mocks.mock_gateway import MockLiteLLMGateway
from src.mocks.mock_database import MockDatabaseConnection

# Use mock in tests
mock_gateway = MockLiteLLMGateway()
mock_db = MockDatabaseConnection()
```

### Current Status

- **Status**: Structure created for alignment with Go SDK
- **Usage**: Tests currently use inline mocks with `unittest.mock` and `pytest-mock`
- **Future**: Mock files can be added here for reusable mock implementations

## Notes

- Mock files follow naming convention: `mock_*.py`
- Mock implementations are automatically excluded from SonarQube coverage
- Prefer inline mocks for simple cases, use mock files for complex reusable mocks

---

**Last Updated**: Created for Go/Python SDK alignment

