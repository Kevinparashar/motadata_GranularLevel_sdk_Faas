## Coverage Exclusions

The following are **excluded from coverage calculations**:

| Exclusion Pattern | Reason |
|-------------------|--------|
| `**/*_gen.py` | Generated code |
| `**/*_pb2.py` | Protocol buffer generated code |
| `**/mock_*.py` | Mock implementations |
| `**/mocks/**` | Mock packages |
| `**/setup.py` | Application bootstrap code |
| `**/testdata/**` | Test fixtures |
| `**/test_*.py` | Test files themselves |
| `**/*_test.py` | Test files (alternative naming) |

### SonarQube Configuration
```properties
sonar.coverage.exclusions=**/test_*.py,**/*_test.py,**/tests/**,**/__pycache__/**,**/*.pyc,**/*.pyo,**/venv/**,**/env/**,**/.venv/**,**/build/**,**/dist/**,**/*.egg-info/**,**/testdata/**,**/*_pb2.py,**/mock_*.py,**/mocks/**,**/conftest.py,**/setup.py,**/examples/**
```

