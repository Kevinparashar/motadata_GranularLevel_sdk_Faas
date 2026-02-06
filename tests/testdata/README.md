# Test Data Directory

This directory contains **test fixtures, sample data, and test resources** used by unit and integration tests.

## Purpose

- **Test fixtures**: Sample files, JSON data, mock responses
- **Test resources**: Configuration files, sample documents, test databases
- **Test data files**: CSV, JSON, XML, or other data formats for testing

## Coverage Exclusion

This directory is **excluded from code coverage** calculations:
- Pattern: `**/testdata/**`
- Reason: Test data files are not production code and don't need coverage

## Structure

```
testdata/
├── fixtures/          # Test fixtures and sample data
├── documents/         # Sample documents for RAG testing
├── configs/           # Test configuration files
├── responses/         # Mock API responses
└── databases/         # Test database dumps or schemas
```

## Usage Examples

### Loading Test Data in Tests

```python
import json
from pathlib import Path

# Load test fixture
testdata_dir = Path(__file__).parent.parent / "testdata"
fixture_path = testdata_dir / "fixtures" / "sample_data.json"

with open(fixture_path) as f:
    test_data = json.load(f)
```

### Using Test Documents

```python
from pathlib import Path

# Load test document for RAG testing
test_doc = Path(__file__).parent.parent / "testdata" / "documents" / "sample.pdf"
```

## Best Practices

1. **Keep files small**: Test data should be minimal and focused
2. **Version control**: Commit test data files to Git
3. **Naming**: Use descriptive names (e.g., `sample_user_data.json`, `mock_api_response_200.json`)
4. **Organization**: Group related test data in subdirectories
5. **Cleanup**: Remove unused test data files periodically

## Current Status

- **Status**: Empty (reserved for future test data)
- **Usage**: Tests currently use inline fixtures or mocks

## Notes

- Test data files are automatically excluded from SonarQube coverage
- Keep test data files in version control for reproducibility
- Don't commit sensitive data (use `.gitignore` if needed)

---

**Last Updated**: Reserved for future test data needs

