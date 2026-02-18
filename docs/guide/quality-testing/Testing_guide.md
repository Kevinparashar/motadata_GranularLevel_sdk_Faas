# AI Components – Testing Guide
## Comprehensive Unit and Integration Testing Framework for AI-Powered Systems

---

## Table of Contents

1. [Introduction](#introduction)
2. [Objectives](#objectives)
3. [Scope and Coverage](#scope-and-coverage)
4. [Testing Libraries and Tools](#testing-libraries-and-tools)
5. [Methodology](#methodology)
6. [Core Testing Principles](#core-testing-principles)
7. [Quality Metrics and Standards](#quality-metrics-and-standards)
8. [Mocking Strategy](#mocking-strategy)
9. [Unit Testing Framework](#unit-testing-framework)
10. [Integration Testing Framework](#integration-testing-framework)
11. [Test Execution and Validation](#test-execution-and-validation)
12. [Best Practices and Guidelines](#best-practices-and-guidelines)
13. [Code Examples - Testing Libraries Usage](#code-examples---testing-libraries-usage)
14. [Code Examples - Component-Specific Unit Tests](#code-examples---component-specific-unit-tests)
15. [Code Examples - Integration Test Scenarios](#code-examples---integration-test-scenarios)
16. [Code Examples - Error Scenarios and Edge Cases](#code-examples---error-scenarios-and-edge-cases)
17. [Code Examples - Benchmark Testing](#code-examples---benchmark-testing)
18. [Conclusion](#conclusion)
19. [References](#references)

---

## Introduction

### Background

Modern AI-powered applications built on Large Language Models (LLMs) and autonomous agents present unique testing challenges due to their **non-deterministic nature**. Traditional software testing approaches that rely on exact output matching are insufficient for validating GenAI systems, where the same input can produce different (yet equally valid) outputs.

This testing guide addresses these challenges by establishing a comprehensive framework that:
- Validates **deterministic contracts** and **behavioral invariants** rather than exact outputs
- Ensures **reliability and correctness** while accommodating non-deterministic behavior
- Provides **practical, actionable testing strategies** with complete code examples
- Establishes **measurable quality gates** for production readiness

### Purpose

This document serves as the **authoritative testing specification** for all GenAI components in the Motadata AI SDK. It defines:

✅ **What to test** - Complete coverage of all AI components
✅ **How to test** - Mocking strategies, assertion patterns, validation rules
✅ **When to test** - Unit vs integration testing boundaries
✅ **Success criteria** - Quality metrics, performance boundaries, blocking gates

**Target Audience:**
- QA Engineers and Test Automation Specialists
- Backend Developers implementing AI components
- DevOps Engineers setting up CI/CD pipelines
- Technical Leads reviewing code quality

---

## Objectives

### Primary Objectives

1. **Ensure Correctness**
   - Validate that each GenAI component behaves according to its contract
   - Verify correct interactions between multiple components
   - Confirm error handling and edge case management

2. **Maintain Reliability**
   - Achieve ≥80% code coverage for all core AI components
   - Test all critical workflows end-to-end
   - Validate performance boundaries and resource limits

3. **Enable Continuous Integration**
   - Establish blocking quality gates for merge protection
   - Maintain fast test execution (unit tests < 5 min, integration < 15 min)
   - Provide clear pass/fail criteria for automated testing

4. **Support Development Velocity**
   - Provide reusable mock fixtures and test utilities
   - Document testing patterns with complete code examples
   - Enable confident refactoring through comprehensive test coverage

### Secondary Objectives

- **Documentation**: Serve as living documentation of expected component behavior
- **Regression Prevention**: Catch breaking changes before production deployment
- **Knowledge Transfer**: Enable new team members to understand system behavior through tests
- **Quality Culture**: Establish testing best practices across the engineering organization

---

## Scope and Coverage

### Components in Scope

This guide applies to the following **8 core GenAI components**:

| # | Component | Category | Testing Priority |
|---|-----------|----------|------------------|
| 1 | **LiteLLM Gateway** | Infrastructure | 🔴 Critical |
| 2 | **Agno Agent Framework** | Core AI | 🔴 Critical |
| 3 | **RAG System** | Core AI | 🔴 Critical |
| 4 | **Prompt Context Management** | Core AI | 🟡 High |
| 5 | **Prompt-Based Generator** | Core AI | 🟡 High |
| 6 | **Data Ingestion Service** | Infrastructure | 🟡 High |
| 7 | **Cache Mechanism** | Infrastructure | 🟢 Medium |
| 8 | **LLMOps** | Observability | 🟢 Medium |

### Testing Levels Covered

| Test Level | Scope | Coverage Target | Execution Time |
|------------|-------|-----------------|----------------|
| **Unit Testing** | Isolated component logic | ≥ 80% code coverage | < 5 minutes |
| **Integration Testing** | Multi-component workflows | All critical paths | < 15 minutes |

---

## Testing Libraries and Tools

### Overview

This section details all libraries, frameworks, and tools used for testing GenAI components in the SDK. Each tool serves a specific purpose in the testing ecosystem.

### Core Testing Framework

#### pytest (≥ 7.0.0)

**Purpose:** Primary testing framework for all unit and integration tests

**What it does:**
- Discovers and executes test files and functions automatically
- Provides powerful assertion introspection for clear failure messages
- Supports fixtures for test data and dependency injection
- Enables parametrized testing for multiple input scenarios
- Offers rich plugin ecosystem for extended functionality

**Why we use it:**
- Industry-standard Python testing framework
- Excellent developer experience with minimal boilerplate
- Built-in fixture management for dependency injection
- Comprehensive plugin ecosystem

---

### Async Testing Support

#### pytest-asyncio (≥ 0.21.0)

**Purpose:** Enable testing of asynchronous Python code

**What it does:**
- Provides `@pytest.mark.asyncio` decorator for async test functions
- Manages event loop creation and cleanup automatically
- Supports async fixtures for asynchronous test setup/teardown
- Handles coroutine execution within pytest framework

**Why we use it:**
- SDK components use async/await extensively
- Ensures proper async context management in tests
- Prevents event loop-related test failures

---

### Mocking and Stubbing

#### pytest-mock (≥ 3.10.0)

**Purpose:** Simplified mocking with pytest integration

**What it does:**
- Provides `mocker` fixture for creating mocks and patches
- Integrates `unittest.mock` with pytest's fixture system
- Automatic cleanup of mocks after each test
- Spy functionality to track calls without replacing implementation

**Why we use it:**
- Cleaner syntax than raw unittest.mock
- Automatic mock cleanup prevents test pollution
- Better integration with pytest fixtures

#### unittest.mock (Built-in)

**Purpose:** Python standard library mocking functionality

**What it does:**
- Creates mock objects that mimic real objects
- Patches modules, classes, and functions during tests
- Records method calls, arguments, and return values
- Supports MagicMock for mocking magic methods

**Usage Example:**
```python
from unittest.mock import Mock, patch, MagicMock

@patch('litellm.completion')
def test_with_patch(mock_completion):
    """Test with patched external dependency."""
    mock_completion.return_value = Mock(
        choices=[Mock(message=Mock(content="Response"))]
    )
    
    gateway = LiteLLMGateway()
    result = gateway.generate("Hello", model="gpt-4")
    assert result["text"] == "Response"
```

**Why we use it:**
- Standard library - no additional dependencies
- Powerful patching capabilities for external services
- Industry-standard mocking patterns

---

### Code Coverage

#### pytest-cov (≥ 4.0.0)

**Purpose:** Code coverage measurement and reporting

**What it does:**
- Measures line and branch coverage during test execution
- Generates coverage reports in multiple formats (HTML, XML, terminal)
- Identifies untested code paths
- Enforces minimum coverage thresholds
- Integrates with CI/CD for coverage tracking

**Usage Example:**
```bash
# Run tests with coverage
pytest --cov=src --cov-report=html

# Enforce minimum coverage threshold
pytest --cov=src --cov-fail-under=80

# Show missing lines
pytest --cov=src --cov-report=term-missing
```

**Coverage Report Output:**
```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
src/core/litellm_gateway.py     150      8    95%   45-52
src/core/rag_system.py          200     25    87%   120-145
-----------------------------------------------------------
TOTAL                          2000    150    92%
```

**Why we use it:**
- Enforces quality standards with measurable metrics
- Identifies untested code requiring attention
- Tracks coverage trends over time
- Integrates with CI/CD pipelines

---

### Performance and Benchmarking

#### pytest-benchmark (≥ 4.0.0)

**Purpose:** Performance testing and benchmarking

**What it does:**
- Measures execution time of test functions
- Provides statistical analysis (mean, median, stddev)
- Compares performance across test runs
- Generates performance reports and charts
- Detects performance regressions

**Usage Example:**
```python
def test_cache_performance(benchmark):
    """Benchmark cache lookup performance."""
    cache = CacheManager()
    cache.set("key1", "value1")
    
    # Benchmark cache get operation
    result = benchmark(cache.get, "key1")
    
    assert result == "value1"
    # Benchmark will report: mean, median, stddev
```

**Why we use it:**
- Validates performance boundaries (e.g., cache < 10ms)
- Detects performance regressions early
- Provides statistical confidence in performance metrics

---

### Time and Timeout Management

#### pytest-timeout (≥ 2.1.0)

**Purpose:** Enforce test execution time limits

**What it does:**
- Sets maximum execution time for individual tests
- Terminates tests that exceed time limits
- Prevents infinite loops and hanging tests
- Configurable per-test or globally

**Usage Example:**
```python
import pytest

@pytest.mark.timeout(30)
def test_agent_execution():
    """Test must complete within 30 seconds."""
    agent = Agent(gateway=mock_gateway)
    result = agent.execute_task("Long-running task")
    assert result["status"] == "completed"
```

**Why we use it:**
- Prevents CI/CD pipeline hangs
- Enforces performance boundaries
- Catches infinite loops and deadlocks

---

### Data Generation and Fixtures

#### Faker (≥ 18.0.0)

**Purpose:** Generate realistic fake data for testing

**What it does:**
- Creates realistic test data (names, emails, addresses, text)
- Supports multiple locales and data types
- Generates reproducible data with seeds
- Reduces test data maintenance overhead

**Usage Example:**
```python
from faker import Faker

def test_with_fake_data():
    """Test with generated fake data."""
    fake = Faker()
    
    # Generate test data
    user_name = fake.name()
    user_email = fake.email()
    document_text = fake.text(max_nb_chars=500)
    
    # Use in test
    result = process_user(name=user_name, email=user_email)
    assert result["email"] == user_email
```

**Why we use it:**
- Realistic test data improves test quality
- Reduces hardcoded test data maintenance
- Supports varied test scenarios

---

### HTTP Testing

#### responses (≥ 0.23.0)

**Purpose:** Mock HTTP requests and responses

**What it does:**
- Intercepts HTTP requests made by code under test
- Returns predefined responses without network calls
- Validates request parameters and headers
- Supports multiple HTTP methods (GET, POST, PUT, DELETE)

**Usage Example:**
```python
import responses

@responses.activate
def test_http_client():
    """Test HTTP client with mocked responses."""
    # Mock HTTP endpoint
    responses.add(
        responses.POST,
        "https://api.openai.com/v1/chat/completions",
        json={"choices": [{"message": {"content": "Response"}}]},
        status=200
    )
    
    # Make request (will be intercepted)
    gateway = LiteLLMGateway()
    result = gateway.generate("Hello", model="gpt-4")
    
    # Validate mock was called
    assert len(responses.calls) == 1
    assert result["text"] == "Response"
```

**Why we use it:**
- Tests HTTP clients without network dependencies
- Validates request construction
- Fast test execution (no network latency)

---

### Test Data and Snapshots

#### pytest-snapshot (≥ 0.9.0)

**Purpose:** Snapshot testing for deterministic outputs

**What it does:**
- Captures output of test runs as "snapshots"
- Compares future test runs against saved snapshots
- Detects unexpected changes in deterministic outputs
- Useful for testing prompt templates, configuration

**Usage Example:**
```python
def test_prompt_template(snapshot):
    """Test prompt template generates consistent output."""
    template = PromptTemplate("Analyze: {text}")
    result = template.render(text="Sample text")
    
    # Compare against saved snapshot
    snapshot.assert_match(result)
```

**Why we use it:**
- Perfect for deterministic components (templates, config)
- Catches unintended output changes
- Reduces manual assertion writing

---

### Assertion Libraries

#### assertpy (≥ 1.1)

**Purpose:** Fluent assertion library for readable tests

**What it does:**
- Provides chainable assertion methods
- Improves test readability with natural language syntax
- Better error messages than standard assertions
- Type-specific assertions (strings, lists, dicts)

**Usage Example:**
```python
from assertpy import assert_that

def test_with_assertpy():
    """Test using fluent assertions."""
    result = gateway.generate("Hello", model="gpt-4")
    
    # Fluent assertions
    assert_that(result).contains_key("text")
    assert_that(result["text"]).is_not_empty()
    assert_that(result["tokens"]).is_greater_than(0)
    assert_that(result["model"]).is_equal_to("gpt-4")
```

**Why we use it:**
- More readable test code
- Better error messages on failure
- Chainable assertions reduce boilerplate

---

### Database Testing

#### pytest-postgresql (≥ 5.0.0)

**Purpose:** PostgreSQL fixtures for testing

**What it does:**
- Provides isolated PostgreSQL instances for tests
- Automatic database creation and cleanup
- Supports multiple concurrent test databases
- Fast test execution with transaction rollback

**Usage Example:**
```python
def test_with_postgres(postgresql):
    """Test with real PostgreSQL database."""
    # Get connection
    conn = postgresql
    cursor = conn.cursor()
    
    # Run test
    cursor.execute("CREATE TABLE test (id INT, data TEXT)")
    cursor.execute("INSERT INTO test VALUES (1, 'data')")
    conn.commit()
    
    # Verify
    cursor.execute("SELECT * FROM test")
    assert cursor.fetchone() == (1, 'data')
```

**Why we use it:**
- Tests database logic with real PostgreSQL
- Faster than Docker-based solutions
- Automatic cleanup prevents test pollution

---

### Logging and Output Capture

#### pytest-logging (Built-in with pytest)

**Purpose:** Capture and assert on log output

**What it does:**
- Captures log messages during test execution
- Allows assertions on log content and levels
- Displays logs for failed tests
- Configurable log levels per test

**Usage Example:**
```python
import logging

def test_logging(caplog):
    """Test that component logs correctly."""
    with caplog.at_level(logging.INFO):
        gateway = LiteLLMGateway()
        gateway.generate("Hello", model="gpt-4")
    
    # Assert on log messages
    assert "Generating text with model gpt-4" in caplog.text
    assert any(record.levelname == "INFO" for record in caplog.records)
```

**Why we use it:**
- Validates observability and logging behavior
- Ensures proper log levels are used
- Catches missing or incorrect log messages

---

### Test Organization

#### pytest-testmon (≥ 2.0.0)

**Purpose:** Run only tests affected by code changes

**What it does:**
- Tracks dependencies between tests and code
- Runs only tests affected by recent changes
- Speeds up development by skipping unchanged tests
- Integrates with version control

**Usage Example:**
```bash
# First run - all tests execute
pytest --testmon

# Subsequent runs - only affected tests
pytest --testmon
```

**Why we use it:**
- Faster feedback during development
- Reduces CI/CD execution time
- Maintains confidence in test coverage

---

### Library Summary Table

| Library | Version | Purpose | Test Type |
|---------|---------|---------|-----------|
| **pytest** | ≥ 7.0.0 | Core testing framework | All |
| **pytest-asyncio** | ≥ 0.21.0 | Async test support | Unit, Integration |
| **pytest-mock** | ≥ 3.10.0 | Mocking utilities | Unit |
| **unittest.mock** | Built-in | Standard mocking | Unit |
| **pytest-cov** | ≥ 4.0.0 | Code coverage | All |
| **pytest-benchmark** | ≥ 4.0.0 | Performance testing | Unit |
| **pytest-timeout** | ≥ 2.1.0 | Timeout enforcement | All |
| **responses** | ≥ 0.23.0 | HTTP mocking | Unit |
| **Faker** | ≥ 18.0.0 | Test data generation | All |
| **assertpy** | ≥ 1.1 | Fluent assertions | All |
| **pytest-snapshot** | ≥ 0.9.0 | Snapshot testing | Unit |
| **pytest-postgresql** | ≥ 5.0.0 | Database testing | Integration |
| **pytest-testmon** | ≥ 2.0.0 | Selective test execution | All |

---

### Installation

**Install all testing dependencies from `requirements-test.txt` or install individually as needed.**

---

## Methodology

### Testing Approach

Our testing methodology follows a **contract-based validation** approach optimized for non-deterministic AI systems:

```
┌─────────────────────────────────────────────────────────────┐
│                  TESTING METHODOLOGY                         │
└─────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │ Deterministic│
    │  Components  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────┐
    │ Exact Assertions │──> Test output values directly
    │  (What + How)    │
    └──────────────────┘

    ┌──────────────┐
    │Non-Determistic│
    │  Components  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────┐
    │Contract Assertions│──> Test structure, schema, behavior
    │  (What, not How) │
    └──────────────────┘
```

### Validation Strategy

We employ **three layers of validation** for comprehensive coverage:

#### 1. Structural Contract Validation
- ✅ Output type correctness (dict, list, string, etc.)
- ✅ Required fields presence
- ✅ Schema conformance (Pydantic models, JSON schemas)

#### 2. Behavioral Contract Validation
- ✅ Correct function/tool selected for given input
- ✅ Arguments passed with correct types and values
- ✅ Termination conditions met (no infinite loops)
- ✅ Side effects applied correctly (database writes, API calls)

#### 3. Invariant Validation
- ✅ Resource limits respected (context size, token count, memory)
- ✅ Ordering rules preserved (message history, retrieval ranking)
- ✅ Tenant isolation maintained (multi-tenancy guarantees)
- ✅ Performance boundaries not violated (timeouts, latency)

### Tools and Frameworks

| Tool | Version | Purpose |
|------|---------|---------|
| **pytest** | ≥ 7.0.0 | Primary testing framework |
| **pytest-asyncio** | ≥ 0.21.0 | Async test support |
| **pytest-mock** | ≥ 3.10.0 | Mocking utilities |
| **pytest-cov** | ≥ 4.0.0 | Coverage reporting |
| **unittest.mock** | Built-in | Standard library mocking |

---

## Core Testing Principles

### Principle 1: Non-Determinism Accommodation

**LLM and agent-based systems are non-deterministic by nature.**

**Rule:** Tests must validate **deterministic contracts and invariants**, not exact textual output, unless the LLM response is explicitly mocked or stubbed.

**Allowed:** Tests should validate structure and behavior (output type, required fields, schema conformance).

**Not Allowed:** Testing exact textual output from non-mocked LLM calls (will fail randomly).

**Exception:** Exact output matching is **only permitted** when:
1. ✅ The LLM call is mocked/stubbed
2. ✅ The component is deterministic by design (e.g., template rendering, cache key generation)

### Principle 2: Isolation and Repeatability

**Unit tests must be:**
- 🔒 **Isolated** - No dependencies on external services
- 🔁 **Repeatable** - Same input = same result, every time
- ⚡ **Fast** - Each test completes in < 1 second

**Implementation:** All external dependencies must be mocked. Tests should not depend on real databases, APIs, or external services.

### Principle 3: Error Path Coverage

**Every error path must be tested.**

**Rule:** For every `try/except` block, there must be a corresponding test that triggers the exception.

**Example:** For every `try/except` block in component code, there must be a corresponding test that triggers the exception and validates the error handling.

### Principle 4: Mock at Service Boundaries

**Mock external services, not internal methods.**

**Guidelines:**
- ✅ Mock: LLM API calls, database connections, external HTTP APIs
- ❌ Don't mock: Internal helper functions, business logic, validators

**Example:** Mock external service calls (LLM APIs, databases, HTTP APIs) at service boundaries. Do not mock internal helper functions or business logic.

---

## Quality Metrics and Standards

### Code Coverage Requirements

| Component Type | Unit Test Coverage | Integration Coverage | Error Path Coverage |
|----------------|-------------------|---------------------|---------------------|
| **Core AI Components** | ≥ 80% | All critical workflows | 100% |
| **Utility Functions** | ≥ 90% | N/A | 100% |
| **API Endpoints** | ≥ 85% | All endpoints | 100% |
| **Error Handlers** | 100% | All error paths | 100% |
| **Configuration** | ≥ 75% | N/A | 100% |

### Quality Gates (Blocking)

All gates must pass before code can be merged:

- ✅ **All tests pass** - Zero failures in unit + integration suites
- ✅ **Coverage thresholds met** - Component-specific minimums achieved
- ✅ **No new linting errors** - Code quality maintained
- ✅ **All error paths tested** - 100% error handler coverage
- ✅ **Performance boundaries respected** - No regressions in timing
- ✅ **Documentation updated** - README and docstrings current

---

## Mocking Strategy

### Recommended Libraries

**Primary:** `pytest-mock` (preferred for pytest ecosystem)
**Secondary:** `unittest.mock` (Python standard library)

**Import Pattern:** Use `from unittest.mock import Mock, patch, MagicMock, AsyncMock` and `import pytest`.

### Mocking Principles

1. **Mock at service boundaries**, not internal methods
2. **Use fixtures** for common mocks to promote reusability
3. **Mock external services** (LLM providers, databases, APIs)
4. **Never mock the component under test** - test real implementation
5. **Configure mocks completely** - specify all expected method calls

### Standard Mock Fixtures

Create reusable fixtures in `conftest.py` for common mocks: `mock_llm_gateway`, `mock_database`, `mock_cache`, `mock_vector_db`, and `mock_async_llm`. These fixtures provide standard responses and can be reused across multiple tests.

### Component-Specific Mocking Patterns

**Pattern 1: Mocking LLM Providers** - Use `@patch('litellm.completion')` to mock LLM API calls and validate request/response structure.

**Pattern 2: Mocking Database Operations** - Mock database and vector DB connections, configure return values for search/query operations.

**Pattern 3: Mocking Agent Tools** - Create mock tools with `Mock()` objects, configure `execute()` return values, and validate tool invocation.

---

## Unit Testing Framework

### Overview

**Objective:** Ensure each GenAI component behaves correctly in isolation, with predictable behavior and well-defined contracts.

### General Unit Testing Rules

✅ **No live LLM or external service calls** - All external dependencies mocked
✅ **All dependencies must be mocked or stubbed** - Complete isolation
✅ **Tests must be repeatable** - Same result every execution
✅ **Error paths are mandatory** - 100% error handler coverage
✅ **Validation focuses on contracts** - Structure, behavior, invariants

### Unit Testing Validation Types

#### 1. Structural Contract Validation
Validate output type and schema (dict, list, string), required fields presence, and schema conformance.

#### 2. Behavioral Contract Validation
Validate correct behavior and side effects: correct function/tool selection, arguments passed correctly, termination conditions met.

#### 3. Invariant Validation
Validate system invariants: resource limits respected, ordering rules preserved, tenant isolation maintained, performance boundaries not violated.

---

## Component-Specific Unit Tests

### 1. LiteLLM Gateway

**Test Focus:**
- Request payload construction
- Provider configuration resolution
- Error normalization logic
- Cache integration
- Rate limiting per tenant

**Testing Requirements:** Validate request structure, error handling, tenant isolation, and cache integration. See code examples section for implementation details.

```python
import pytest
from unittest.mock import Mock, patch
from src.core.litellm_gateway import LiteLLMGateway, GatewayConfig

def test_gateway_request_structure():
    """Test that gateway constructs correct request payload."""
    gateway = LiteLLMGateway(config=GatewayConfig(provider="openai"))
    
    with patch('litellm.completion') as mock_completion:
        mock_completion.return_value = Mock(
            choices=[Mock(message=Mock(content="Response"))],
            usage=Mock(total_tokens=10)
        )
        
        gateway.generate("Hello", model="gpt-4", temperature=0.7)
        
        # Validate request structure
        call_args = mock_completion.call_args
        assert call_args[1]["model"] == "gpt-4"
        assert call_args[1]["messages"][0]["content"] == "Hello"
        assert call_args[1]["temperature"] == 0.7

def test_gateway_error_normalization():
    """Test that provider errors are normalized to SDK errors."""
    gateway = LiteLLMGateway()
    
    with patch('litellm.completion') as mock_completion:
        # Simulate provider rate limit error
        mock_completion.side_effect = Exception("Rate limit exceeded")
        
        with pytest.raises(GatewayError) as exc_info:
            gateway.generate("Hello", model="gpt-4")
        
        # Validate error is normalized
        assert "rate limit" in str(exc_info.value).lower()
        assert exc_info.value.error_type == "rate_limit"

def test_gateway_tenant_isolation():
    """Test that cache keys include tenant_id for isolation."""
    gateway = LiteLLMGateway()
    
    key1 = gateway._generate_cache_key(
        prompt="Hello",
        model="gpt-4",
        tenant_id="tenant_1"
    )
    key2 = gateway._generate_cache_key(
        prompt="Hello",
        model="gpt-4",
        tenant_id="tenant_2"
    )
    
    # Same prompt, different tenants = different cache keys
    assert key1 != key2
    assert "tenant_1" in key1
    assert "tenant_2" in key2

def test_gateway_cache_integration():
    """Test gateway uses cache correctly."""
    mock_cache = Mock()
    mock_cache.get.return_value = None  # Cache miss
    
    gateway = LiteLLMGateway(cache=mock_cache)
    
    with patch('litellm.completion') as mock_llm:
        mock_llm.return_value = Mock(
            choices=[Mock(message=Mock(content="Response"))],
            usage=Mock(total_tokens=50)
        )
        
        gateway.generate("Hello", model="gpt-4", tenant_id="t1")
    
    # Validate cache operations
    assert mock_cache.get.called  # Checked cache first
    assert mock_cache.set.called  # Stored result in cache
```

### 2. Agno Agent Framework

**Test Focus:**
- Agent decision logic
- Tool selection rules
- Termination conditions
- Memory context management

**Testing Requirements:** Validate tool selection, termination bounds, tool failure handling, and memory context. See code examples section for implementation details.

---

### 3. RAG System

**Test Focus:**
- Retrieval query formation
- Filtering and ranking logic
- Context assembly behavior
- Token limit enforcement

**Testing Requirements:** Validate document retrieval, empty result handling, context size limits, and query optimization. See code examples section for implementation details.

---

### 4. Prompt Context Management

**Test Focus:**
- Context ordering
- Token limit enforcement
- Truncation strategy
- Priority preservation

**Testing Requirements:** Validate context ordering, token limits, priority preservation, and deterministic assembly. See code examples section for implementation details.

---

### 5. Prompt-Based Generator

**Test Focus:**
- Prompt template rendering
- Variable substitution
- Formatting and escaping
- Error handling for missing variables

**Testing Requirements:** Validate template rendering, missing variable handling, variable escaping, and snapshot matching. See code examples section for implementation details.

---

### 6. Data Ingestion Service

**Test Focus:**
- Input validation
- Parsing logic
- Deduplication behavior
- Metadata preservation

**Testing Requirements:** Validate input validation, file size limits, deduplication, and metadata preservation. See code examples section for implementation details.

---

### 7. Cache Mechanism

**Test Focus:**
- Cache key generation
- TTL logic
- Read/write behavior
- Tenant isolation

**Testing Requirements:** Validate basic operations, TTL expiration, tenant isolation, and key collision prevention. See code examples section for implementation details.

---

### 8. LLMOps

**Test Focus:**
- Log generation
- Metric emission
- Trace context propagation
- Sensitive data filtering

**Testing Requirements:** Validate log structure, correlation ID propagation, sensitive data filtering, and metric emission. See code examples section for implementation details.

---

## Integration Testing Framework

### Overview

**Objective:** Validate that multiple GenAI components work together correctly under controlled, realistic scenarios.

### General Integration Testing Rules

✅ **External services must be stubbed or simulated** - No real LLM/DB calls
✅ **Tests validate data flow and orchestration** - Not internal implementation
✅ **Both success and failure paths must be covered** - Happy + error scenarios
✅ **Performance boundaries validated** - Timeouts, resource limits

### Integration Testing Validation Strategy

Integration tests must validate:

1. **Correct component interaction** - Components communicate properly
2. **Correct data passed between components** - Data format/structure maintained
3. **Stable system behavior** - Works despite non-deterministic outputs

**Assertions focus on:**
- Schema validity
- Required fields
- Tool usage
- Workflow completion
- Error propagation

---

## Required Integration Test Scenarios

### Scenario 1: Prompt Generator → LiteLLM Gateway

**Validate:**
- ✅ Prompt generated and passed correctly
- ✅ Gateway response parsed correctly
- ✅ Errors propagate in standardized form

**Testing Requirements:** See code examples section for implementation details.

### Scenario 2: Agent → Tools

**Validate:**
- ✅ Agent invokes correct tools
- ✅ Tools invoked in correct order
- ✅ Agent completes without infinite loops

**Testing Requirements:** See code examples section for implementation details.

### Scenario 3: RAG Pipeline (Ingestion → Retrieval → Generation)

**Validate:**
- ✅ Ingested data is retrievable
- ✅ Retrieved context included in prompt
- ✅ Output adheres to expected response structure

**Testing Requirements:** See code examples section for implementation details.

### Scenario 4: Cache Integration

**Validate:**
- ✅ Cache hit avoids recomputation
- ✅ Cache miss triggers fresh execution
- ✅ Cached data scoped correctly by tenant

**Testing Requirements:** See code examples section for implementation details.

### Scenario 5: LLMOps Integration

**Validate:**
- ✅ Logs, metrics, and traces generated for full workflow
- ✅ Correlation ID preserved across components
- ✅ Failures still emit telemetry

**Testing Requirements:** See code examples section for implementation details.

---

## Error Scenarios and Edge Cases

### Overview

**All components must test comprehensive error scenarios** to ensure graceful failure handling and proper error propagation.

### Network Errors

**Testing Requirements:** Validate timeout handling, connection refused errors. See code examples section for implementation details.

### LLM Provider Errors

**Testing Requirements:** Validate rate limit errors, invalid API key errors, model not found errors. See code examples section for implementation details.

### Malformed Input Errors

**Testing Requirements:** Validate empty query handling, missing tenant ID validation, invalid tool arguments. See code examples section for implementation details.

### Edge Cases

**Testing Requirements:** Validate null value handling, max retrieval limits, empty context handling. See code examples section for implementation details.

---

## Test Execution and Validation

### Running Tests

#### Unit Tests

**Commands:** Use `pytest src/tests/unit_tests/` with various flags for coverage, verbosity, and filtering. See code examples section for detailed command examples.

#### Integration Tests

**Commands:** Use `pytest src/tests/integration_tests/` with integration markers and timeout flags. See code examples section for detailed command examples.

#### Coverage Reports

**Commands:** Use `pytest --cov=src` with various report formats. See code examples section for detailed command examples.

### Pre-Merge Validation Checklist

Before merging any pull request, verify:

- ✅ **All tests pass** - Zero failures in unit + integration suites
- ✅ **Coverage thresholds met** - ≥80% for modified components
- ✅ **No new linting errors** - Run `ruff check src/`
- ✅ **All error paths tested** - 100% coverage of error handlers
- ✅ **Performance boundaries respected** - No timeout violations
- ✅ **Assertions contract-based** - No exact text matching (unless mocked)
- ✅ **Mocks properly configured** - All external services mocked
- ✅ **Documentation updated** - README and docstrings current

### Continuous Integration

**Required CI Checks:** Configure CI/CD pipeline with unit tests, integration tests, coverage checks, and coverage upload. See code examples section for CI configuration example.

---

## Best Practices and Guidelines

### 1. Test Naming Conventions

**Format:** `test_<component>_<scenario>_<expected_behavior>`

**Examples:** Use descriptive names like `test_gateway_rate_limit_raises_error()`. Avoid vague names like `test_gateway()`.

### 2. Test Organization

**Structure:** Group related tests in classes. Organize by happy path, error path, and edge cases.

### 3. Assertion Messages

**Provide context in assertions:** Include clear failure messages with expected vs actual values.

### 4. Test Data Management

**Use fixtures for test data:** Create reusable fixtures for common test data patterns.

### 5. Async Test Patterns

**Use pytest-asyncio for async tests:** Decorate async test functions with `@pytest.mark.asyncio`.

---

## Code Examples - Testing Libraries Usage

### pytest Usage Examples

```python
# Run all tests
pytest src/tests/

# Run with verbose output
pytest src/tests/ -v

# Run specific test file
pytest src/tests/unit_tests/test_gateway.py
```

### pytest-asyncio Usage Examples

```python
import pytest

@pytest.mark.asyncio
async def test_async_llm_call():
    """Test asynchronous LLM generation."""
    gateway = LiteLLMGateway()
    result = await gateway.generate_async("Hello", model="gpt-4")
    assert result["text"] is not None
```

### pytest-mock Usage Examples

```python
def test_with_mocker(mocker):
    """Test using pytest-mock fixture."""
    # Create mock
    mock_llm = mocker.Mock()
    mock_llm.generate.return_value = {"text": "Response"}
    
    # Use mock in test
    gateway = LiteLLMGateway(llm_client=mock_llm)
    result = gateway.generate("Hello")
    
    # Verify mock was called
    mock_llm.generate.assert_called_once()
```

### unittest.mock Usage Examples

```python
from unittest.mock import Mock, patch, MagicMock

@patch('litellm.completion')
def test_with_patch(mock_completion):
    """Test with patched external dependency."""
    mock_completion.return_value = Mock(
        choices=[Mock(message=Mock(content="Response"))]
    )
    
    gateway = LiteLLMGateway()
    result = gateway.generate("Hello", model="gpt-4")
    assert result["text"] == "Response"
```

### pytest-cov Usage Examples

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html

# Enforce minimum coverage threshold
pytest --cov=src --cov-fail-under=80

# Show missing lines
pytest --cov=src --cov-report=term-missing
```

### pytest-benchmark Usage Examples

```python
def test_cache_performance(benchmark):
    """Benchmark cache lookup performance."""
    cache = CacheManager()
    cache.set("key1", "value1")
    
    # Benchmark cache get operation
    result = benchmark(cache.get, "key1")
    
    assert result == "value1"
    # Benchmark will report: mean, median, stddev
```

### pytest-timeout Usage Examples

```python
import pytest

@pytest.mark.timeout(30)
def test_agent_execution():
    """Test must complete within 30 seconds."""
    agent = Agent(gateway=mock_gateway)
    result = agent.execute_task("Long-running task")
    assert result["status"] == "completed"
```

### Faker Usage Examples

```python
from faker import Faker

def test_with_fake_data():
    """Test with generated fake data."""
    fake = Faker()
    
    # Generate test data
    user_name = fake.name()
    user_email = fake.email()
    document_text = fake.text(max_nb_chars=500)
    
    # Use in test
    result = process_user(name=user_name, email=user_email)
    assert result["email"] == user_email
```

### responses Usage Examples

```python
import responses

@responses.activate
def test_http_client():
    """Test HTTP client with mocked responses."""
    # Mock HTTP endpoint
    responses.add(
        responses.POST,
        "https://api.openai.com/v1/chat/completions",
        json={"choices": [{"message": {"content": "Response"}}]},
        status=200
    )
    
    # Make request (will be intercepted)
    gateway = LiteLLMGateway()
    result = gateway.generate("Hello", model="gpt-4")
    
    # Validate mock was called
    assert len(responses.calls) == 1
    assert result["text"] == "Response"
```

### pytest-snapshot Usage Examples

```python
def test_prompt_template(snapshot):
    """Test prompt template generates consistent output."""
    template = PromptTemplate("Analyze: {text}")
    result = template.render(text="Sample text")
    
    # Compare against saved snapshot
    snapshot.assert_match(result)
```

### assertpy Usage Examples

```python
from assertpy import assert_that

def test_with_assertpy():
    """Test using fluent assertions."""
    result = gateway.generate("Hello", model="gpt-4")
    
    # Fluent assertions
    assert_that(result).contains_key("text")
    assert_that(result["text"]).is_not_empty()
    assert_that(result["tokens"]).is_greater_than(0)
    assert_that(result["model"]).is_equal_to("gpt-4")
```

### pytest-postgresql Usage Examples

```python
def test_with_postgres(postgresql):
    """Test with real PostgreSQL database."""
    # Get connection
    conn = postgresql
    cursor = conn.cursor()
    
    # Run test
    cursor.execute("CREATE TABLE test (id INT, data TEXT)")
    cursor.execute("INSERT INTO test VALUES (1, 'data')")
    conn.commit()
    
    # Verify
    cursor.execute("SELECT * FROM test")
    assert cursor.fetchone() == (1, 'data')
```

### pytest-logging Usage Examples

```python
import logging

def test_logging(caplog):
    """Test that component logs correctly."""
    with caplog.at_level(logging.INFO):
        gateway = LiteLLMGateway()
        gateway.generate("Hello", model="gpt-4")
    
    # Assert on log messages
    assert "Generating text with model gpt-4" in caplog.text
    assert any(record.levelname == "INFO" for record in caplog.records)
```

### Installation Examples

```bash
# Install from requirements-test.txt
pip install -r requirements-test.txt

# Or install individually
pip install pytest>=7.0.0 \
            pytest-asyncio>=0.21.0 \
            pytest-mock>=3.10.0 \
            pytest-cov>=4.0.0 \
            pytest-benchmark>=4.0.0 \
            pytest-timeout>=2.1.0 \
            responses>=0.23.0 \
            Faker>=18.0.0 \
            assertpy>=1.1 \
            pytest-snapshot>=0.9.0 \
            pytest-postgresql>=5.0.0 \
            pytest-testmon>=2.0.0
```

**requirements-test.txt example:**
```txt
# Core Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0
pytest-cov>=4.0.0

# Performance & Utilities
pytest-benchmark>=4.0.0
pytest-timeout>=2.1.0
pytest-testmon>=2.0.0

# Mocking & Test Data
responses>=0.23.0
Faker>=18.0.0

# Assertions & Snapshots
assertpy>=1.1
pytest-snapshot>=0.9.0

# Database Testing
pytest-postgresql>=5.0.0
```

---

## Code Examples - Component-Specific Unit Tests

### 1. LiteLLM Gateway Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from src.core.litellm_gateway import LiteLLMGateway, GatewayConfig

def test_gateway_request_structure():
    """Test that gateway constructs correct request payload."""
    gateway = LiteLLMGateway(config=GatewayConfig(provider="openai"))
    
    with patch('litellm.completion') as mock_completion:
        mock_completion.return_value = Mock(
            choices=[Mock(message=Mock(content="Response"))],
            usage=Mock(total_tokens=10)
        )
        
        gateway.generate("Hello", model="gpt-4", temperature=0.7)
        
        # Validate request structure
        call_args = mock_completion.call_args
        assert call_args[1]["model"] == "gpt-4"
        assert call_args[1]["messages"][0]["content"] == "Hello"
        assert call_args[1]["temperature"] == 0.7

def test_gateway_error_normalization():
    """Test that provider errors are normalized to SDK errors."""
    gateway = LiteLLMGateway()
    
    with patch('litellm.completion') as mock_completion:
        # Simulate provider rate limit error
        mock_completion.side_effect = Exception("Rate limit exceeded")
        
        with pytest.raises(GatewayError) as exc_info:
            gateway.generate("Hello", model="gpt-4")
        
        # Validate error is normalized
        assert "rate limit" in str(exc_info.value).lower()
        assert exc_info.value.error_type == "rate_limit"

def test_gateway_tenant_isolation():
    """Test that cache keys include tenant_id for isolation."""
    gateway = LiteLLMGateway()
    
    key1 = gateway._generate_cache_key(
        prompt="Hello",
        model="gpt-4",
        tenant_id="tenant_1"
    )
    key2 = gateway._generate_cache_key(
        prompt="Hello",
        model="gpt-4",
        tenant_id="tenant_2"
    )
    
    # Same prompt, different tenants = different cache keys
    assert key1 != key2
    assert "tenant_1" in key1
    assert "tenant_2" in key2

def test_gateway_cache_integration():
    """Test gateway uses cache correctly."""
    mock_cache = Mock()
    mock_cache.get.return_value = None  # Cache miss
    
    gateway = LiteLLMGateway(cache=mock_cache)
    
    with patch('litellm.completion') as mock_llm:
        mock_llm.return_value = Mock(
            choices=[Mock(message=Mock(content="Response"))],
            usage=Mock(total_tokens=50)
        )
        
        gateway.generate("Hello", model="gpt-4", tenant_id="t1")
    
    # Validate cache operations
    assert mock_cache.get.called  # Checked cache first
    assert mock_cache.set.called  # Stored result in cache
```

### 2. Agno Agent Framework Unit Tests

```python
import pytest
from unittest.mock import Mock
from src.core.agno_agent_framework import Agent, Tool

def test_agent_tool_selection(mock_llm_gateway):
    """Test that agent selects correct tool based on task."""
    # Create mock tools
    search_tool = Mock(spec=Tool)
    search_tool.name = "search"
    search_tool.description = "Search for information"
    
    calculator_tool = Mock(spec=Tool)
    calculator_tool.name = "calculator"
    calculator_tool.description = "Perform calculations"
    
    # Create agent with tools
    agent = Agent(gateway=mock_llm_gateway)
    agent.add_tool(search_tool)
    agent.add_tool(calculator_tool)
    
    # Mock LLM to select search tool
    mock_llm_gateway.generate.return_value = {
        "tool_calls": [{
            "name": "search",
            "arguments": {"query": "Python tutorials"}
        }],
        "finish_reason": "tool_calls"
    }
    
    result = agent.execute_task("Find Python tutorials")
    
    # Validate correct tool selected
    assert search_tool.execute.called
    assert not calculator_tool.execute.called
    assert search_tool.execute.call_args[1]["query"] == "Python tutorials"

def test_agent_termination_bounds(mock_llm_gateway):
    """Test that agent terminates within max iterations."""
    agent = Agent(gateway=mock_llm_gateway, max_iterations=5)
    
    # Mock LLM to never finish (infinite loop scenario)
    mock_llm_gateway.generate.return_value = {
        "tool_calls": [{"name": "search", "arguments": {}}],
        "finish_reason": "tool_calls"
    }
    
    with pytest.raises(AgentExecutionError) as exc_info:
        agent.execute_task("Task that never completes")
    
    # Validate termination
    assert "max iterations" in str(exc_info.value).lower()
    assert mock_llm_gateway.generate.call_count <= 5

def test_agent_tool_failure_handling(mock_llm_gateway):
    """Test that agent handles tool failures gracefully."""
    # Create tool that fails
    failing_tool = Mock(spec=Tool)
    failing_tool.name = "search"
    failing_tool.execute.side_effect = Exception("Tool error")
    
    agent = Agent(gateway=mock_llm_gateway)
    agent.add_tool(failing_tool)
    
    # Mock LLM to call the failing tool
    mock_llm_gateway.generate.return_value = {
        "tool_calls": [{"name": "search", "arguments": {}}],
        "finish_reason": "tool_calls"
    }
    
    # Agent should not crash
    result = agent.execute_task("Task with failing tool")
    
    # Validate error was handled
    assert result["status"] == "failed" or "error" in result
    assert "tool error" in str(result).lower()

def test_agent_memory_context():
    """Test that agent maintains conversation memory."""
    mock_gateway = Mock()
    mock_gateway.generate.return_value = {"text": "Response", "finish_reason": "stop"}
    
    agent = Agent(gateway=mock_gateway, enable_memory=True)
    
    # First interaction
    agent.chat("Hello", session_id="session_1")
    
    # Second interaction
    agent.chat("Remember my previous message?", session_id="session_1")
    
    # Validate memory was passed to LLM
    second_call_args = mock_gateway.generate.call_args_list[1]
    messages = second_call_args[1]["messages"]
    
    # Should include previous conversation
    assert len(messages) >= 3  # system + user1 + assistant1 + user2
    assert any("Hello" in str(msg) for msg in messages)
```

### 3. RAG System

**Test Focus:**
- Retrieval query formation
- Filtering and ranking logic
- Context assembly behavior
- Token limit enforcement

**Example Tests:**

```python
import pytest
from unittest.mock import Mock
from src.core.rag import RAGSystem, DocumentProcessor

def test_rag_document_retrieval(mock_vector_db, mock_llm_gateway):
    """Test RAG retrieves relevant documents."""
    # Setup mock vector DB
    mock_vector_db.search.return_value = [
        {"doc_id": "1", "score": 0.95, "content": "Python is a programming language"},
        {"doc_id": "2", "score": 0.85, "content": "Python has great libraries"},
        {"doc_id": "3", "score": 0.75, "content": "Python is easy to learn"}
    ]
    
    rag = RAGSystem(vector_db=mock_vector_db, gateway=mock_llm_gateway)
    results = rag.retrieve("What is Python?", top_k=5)
    
    # Validate structure
    assert isinstance(results, list)
    assert len(results) <= 5
    assert all("doc_id" in r for r in results)
    assert all("score" in r for r in results)
    assert all(0 <= r["score"] <= 1 for r in results)
    
    # Validate ordering (descending by score)
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)

def test_rag_empty_retrieval_handling(mock_vector_db, mock_llm_gateway):
    """Test RAG handles empty retrieval results."""
    # Mock empty results
    mock_vector_db.search.return_value = []
    
    rag = RAGSystem(vector_db=mock_vector_db, gateway=mock_llm_gateway)
    results = rag.retrieve("Unknown query", top_k=5)
    
    # Should return empty list, not error
    assert isinstance(results, list)
    assert len(results) == 0

def test_rag_context_size_limits(mock_vector_db, mock_llm_gateway):
    """Test RAG respects context size limits."""
    # Mock documents with large content
    large_docs = [
        {"doc_id": str(i), "score": 0.9, "content": "x" * 5000}
        for i in range(10)
    ]
    mock_vector_db.search.return_value = large_docs
    
    rag = RAGSystem(
        vector_db=mock_vector_db,
        gateway=mock_llm_gateway,
        max_context_tokens=8000
    )
    
    context = rag._assemble_context(large_docs)
    
    # Validate context size
    token_count = len(context) // 4  # Rough token estimate
    assert token_count <= 8000

def test_rag_query_rewriting():
    """Test RAG query optimization (deterministic)."""
    mock_gateway = Mock()
    mock_vector_db = Mock()
    
    rag = RAGSystem(vector_db=mock_vector_db, gateway=mock_gateway)
    
    # Test query expansion
    original_query = "python"
    expanded_query = rag._expand_query(original_query)
    
    # Validate expansion (deterministic rules)
    assert len(expanded_query) >= len(original_query)
    assert original_query.lower() in expanded_query.lower()
```

### 4. Prompt Context Management

**Test Focus:**
- Context ordering
- Token limit enforcement
- Truncation strategy
- Priority preservation

**Example Tests:**

```python
import pytest
from src.core.prompt_context_management import PromptManager

def test_prompt_context_ordering():
    """Test that context maintains correct order."""
    manager = PromptManager(max_tokens=1000)
    
    manager.add_context("system", "You are a helpful assistant", priority=1)
    manager.add_context("user", "Hello", priority=2)
    manager.add_context("assistant", "Hi there", priority=3)
    
    context = manager.build_context()
    
    # Validate order
    assert context[0]["role"] == "system"
    assert context[1]["role"] == "user"
    assert context[2]["role"] == "assistant"

def test_prompt_token_limit_enforcement():
    """Test that context respects token limits."""
    manager = PromptManager(max_tokens=100)
    
    # Add content that exceeds limit
    for i in range(20):
        manager.add_context("user", "Message " * 50, priority=i)
    
    context = manager.build_context()
    
    # Validate token limit
    total_tokens = sum(len(msg["content"]) // 4 for msg in context)
    assert total_tokens <= 100

def test_prompt_high_priority_preserved():
    """Test that high-priority context is preserved during truncation."""
    manager = PromptManager(max_tokens=200)
    
    # Add high-priority system prompt
    manager.add_context("system", "IMPORTANT INSTRUCTION", priority=100)
    
    # Add many low-priority messages
    for i in range(50):
        manager.add_context("user", "Low priority message", priority=i)
    
    context = manager.build_context()
    
    # High-priority system prompt must be present
    assert any(msg["role"] == "system" and "IMPORTANT" in msg["content"] 
               for msg in context)

def test_prompt_deterministic_assembly():
    """Test that same inputs produce same output."""
    manager1 = PromptManager(max_tokens=500)
    manager1.add_context("system", "Test", priority=1)
    manager1.add_context("user", "Hello", priority=2)
    
    manager2 = PromptManager(max_tokens=500)
    manager2.add_context("system", "Test", priority=1)
    manager2.add_context("user", "Hello", priority=2)
    
    # Same inputs = same output
    assert manager1.build_context() == manager2.build_context()
```

### 5. Prompt-Based Generator

**Test Focus:**
- Prompt template rendering
- Variable substitution
- Formatting and escaping
- Error handling for missing variables

**Example Tests:**

```python
import pytest
from src.core.prompt_based_generator import PromptGenerator

def test_prompt_template_rendering():
    """Test basic template rendering."""
    generator = PromptGenerator()
    
    template = "Hello {name}, your age is {age}"
    variables = {"name": "Alice", "age": 30}
    
    result = generator.render(template, variables)
    
    # Validate rendering
    assert result == "Hello Alice, your age is 30"
    assert "{" not in result  # No unreplaced variables

def test_prompt_missing_variables():
    """Test that missing variables cause explicit failure."""
    generator = PromptGenerator()
    
    template = "Hello {name}, your age is {age}"
    variables = {"name": "Alice"}  # Missing 'age'
    
    with pytest.raises(PromptGeneratorError) as exc_info:
        generator.render(template, variables)
    
    # Validate error message
    assert "age" in str(exc_info.value)
    assert "missing" in str(exc_info.value).lower()

def test_prompt_variable_escaping():
    """Test that special characters are escaped properly."""
    generator = PromptGenerator()
    
    template = "User input: {user_input}"
    variables = {"user_input": "Hello <script>alert('xss')</script>"}
    
    result = generator.render(template, variables, escape=True)
    
    # Validate escaping
    assert "<script>" not in result
    assert "&lt;script&gt;" in result or "script" not in result.lower()

def test_prompt_snapshot_matching():
    """Test that prompt generation is deterministic."""
    generator = PromptGenerator()
    
    template = "Analyze: {text}\nTone: {tone}\nLength: {length}"
    variables = {"text": "Sample text", "tone": "professional", "length": "brief"}
    
    result = generator.render(template, variables)
    
    # Expected output (snapshot)
    expected = "Analyze: Sample text\nTone: professional\nLength: brief"
    assert result == expected
```

### 6. Data Ingestion Service

**Test Focus:**
- Input validation
- Parsing logic
- Deduplication behavior
- Metadata preservation

**Example Tests:**

```python
import pytest
from src.core.data_ingestion import DataIngestionService

def test_data_ingestion_validation():
    """Test input validation rejects invalid data."""
    service = DataIngestionService()
    
    # Invalid file (empty content)
    with pytest.raises(ValidationError) as exc_info:
        service.ingest_file(
            file_path="test.txt",
            content="",
            tenant_id="tenant_1"
        )
    
    assert "empty" in str(exc_info.value).lower()

def test_data_ingestion_file_size_limit():
    """Test that oversized files are rejected."""
    service = DataIngestionService(max_file_size_mb=10)
    
    # Create large content (11 MB)
    large_content = "x" * (11 * 1024 * 1024)
    
    with pytest.raises(ValidationError) as exc_info:
        service.ingest_file(
            file_path="large.txt",
            content=large_content,
            tenant_id="tenant_1"
        )
    
    assert "size" in str(exc_info.value).lower()

def test_data_ingestion_deduplication():
    """Test that duplicate files are detected."""
    service = DataIngestionService()
    
    # Ingest same file twice
    file_data = {
        "file_path": "doc.txt",
        "content": "Sample content",
        "tenant_id": "tenant_1"
    }
    
    result1 = service.ingest_file(**file_data)
    result2 = service.ingest_file(**file_data)
    
    # Second ingestion should detect duplicate
    assert result2["status"] == "duplicate" or result2["doc_id"] == result1["doc_id"]

def test_data_ingestion_metadata_preservation():
    """Test that metadata is preserved accurately."""
    service = DataIngestionService()
    
    metadata = {
        "author": "John Doe",
        "created_at": "2024-01-01",
        "tags": ["python", "tutorial"]
    }
    
    result = service.ingest_file(
        file_path="doc.txt",
        content="Content",
        tenant_id="tenant_1",
        metadata=metadata
    )
    
    # Validate metadata preserved
    assert result["metadata"]["author"] == "John Doe"
    assert result["metadata"]["tags"] == ["python", "tutorial"]
```

### 7. Cache Mechanism

**Test Focus:**
- Cache key generation
- TTL logic
- Read/write behavior
- Tenant isolation

**Example Tests:**

```python
import pytest
import time
from src.core.cache_mechanism import CacheManager

def test_cache_basic_operations():
    """Test basic cache get/set/delete."""
    cache = CacheManager()
    
    # Set value
    cache.set("key1", {"data": "value1"}, ttl=60)
    
    # Get value (hit)
    result = cache.get("key1")
    assert result == {"data": "value1"}
    
    # Delete value
    cache.delete("key1")
    
    # Get after delete (miss)
    result = cache.get("key1")
    assert result is None

def test_cache_ttl_expiration():
    """Test that cache entries expire after TTL."""
    cache = CacheManager()
    
    # Set with short TTL
    cache.set("key1", "value1", ttl=1)  # 1 second
    
    # Immediate get (hit)
    assert cache.get("key1") == "value1"
    
    # Wait for expiration
    time.sleep(1.1)
    
    # Get after expiration (miss)
    assert cache.get("key1") is None

def test_cache_tenant_isolation():
    """Test that cache keys are isolated by tenant."""
    cache = CacheManager()
    
    # Set same key for different tenants
    cache.set("key1", "tenant1_value", tenant_id="tenant_1")
    cache.set("key1", "tenant2_value", tenant_id="tenant_2")
    
    # Validate isolation
    assert cache.get("key1", tenant_id="tenant_1") == "tenant1_value"
    assert cache.get("key1", tenant_id="tenant_2") == "tenant2_value"
    
    # Keys should be different
    key1 = cache._generate_key("key1", tenant_id="tenant_1")
    key2 = cache._generate_key("key1", tenant_id="tenant_2")
    assert key1 != key2

def test_cache_key_collision_prevention():
    """Test that similar inputs generate different keys."""
    cache = CacheManager()
    
    key1 = cache._generate_key("prompt1", model="gpt-4", tenant_id="t1")
    key2 = cache._generate_key("prompt1", model="gpt-3.5", tenant_id="t1")
    key3 = cache._generate_key("prompt2", model="gpt-4", tenant_id="t1")
    
    # All keys should be unique
    assert key1 != key2
    assert key1 != key3
    assert key2 != key3
```

### 8. LLMOps

**Test Focus:**
- Log generation
- Metric emission
- Trace context propagation
- Sensitive data filtering

**Example Tests:**

```python
import pytest
from unittest.mock import Mock
from src.core.llmops import LLMOpsLogger

def test_llmops_log_structure():
    """Test that LLMOps logs contain required fields."""
    logger = LLMOpsLogger()
    
    log_entry = logger.log_llm_call(
        model="gpt-4",
        prompt="Hello",
        response="Hi there",
        tokens=50,
        cost=0.001,
        tenant_id="tenant_1"
    )
    
    # Validate required fields
    assert "timestamp" in log_entry
    assert "model" in log_entry
    assert "tokens" in log_entry
    assert "cost" in log_entry
    assert "tenant_id" in log_entry
    assert "correlation_id" in log_entry

def test_llmops_correlation_id_propagation():
    """Test that correlation IDs are propagated."""
    logger = LLMOpsLogger()
    
    correlation_id = "corr_12345"
    
    log1 = logger.log_llm_call(
        model="gpt-4",
        prompt="Step 1",
        response="Response 1",
        correlation_id=correlation_id
    )
    
    log2 = logger.log_llm_call(
        model="gpt-4",
        prompt="Step 2",
        response="Response 2",
        correlation_id=correlation_id
    )
    
    # Same correlation ID
    assert log1["correlation_id"] == correlation_id
    assert log2["correlation_id"] == correlation_id

def test_llmops_sensitive_data_filtering():
    """Test that sensitive data is not logged."""
    logger = LLMOpsLogger()
    
    log_entry = logger.log_llm_call(
        model="gpt-4",
        prompt="My API key is sk-1234567890abcdef",
        response="Response",
        api_key="sk-1234567890abcdef"
    )
    
    # Sensitive data should be redacted
    assert "sk-1234567890abcdef" not in str(log_entry)
    assert "api_key" not in log_entry or log_entry["api_key"] == "[REDACTED]"

def test_llmops_metric_emission():
    """Test that metrics are emitted correctly."""
    logger = LLMOpsLogger()
    mock_metrics = Mock()
    logger.metrics_client = mock_metrics
    
    logger.log_llm_call(
        model="gpt-4",
        prompt="Hello",
        response="Hi",
        tokens=50,
        cost=0.001,
        latency=1.5
    )
    
    # Validate metrics emitted
    assert mock_metrics.record_metric.called
    calls = mock_metrics.record_metric.call_args_list
    
    # Should record tokens, cost, and latency
    metric_names = [call[0][0] for call in calls]
    assert "llm.tokens" in metric_names
    assert "llm.cost" in metric_names
    assert "llm.latency" in metric_names
```

---

## Integration Testing Framework

### Overview

**Objective:** Validate that multiple GenAI components work together correctly under controlled, realistic scenarios.

### General Integration Testing Rules

✅ **External services must be stubbed or simulated** - No real LLM/DB calls
✅ **Tests validate data flow and orchestration** - Not internal implementation
✅ **Both success and failure paths must be covered** - Happy + error scenarios
✅ **Performance boundaries validated** - Timeouts, resource limits

### Integration Testing Validation Strategy

Integration tests must validate:

1. **Correct component interaction** - Components communicate properly
2. **Correct data passed between components** - Data format/structure maintained
3. **Stable system behavior** - Works despite non-deterministic outputs

**Assertions focus on:**
- Schema validity
- Required fields
- Tool usage
- Workflow completion
- Error propagation

---

## Required Integration Test Scenarios

### Scenario 1: Prompt Generator → LiteLLM Gateway

**Validate:**
- ✅ Prompt generated and passed correctly
- ✅ Gateway response parsed correctly
- ✅ Errors propagate in standardized form

**Example:**

```python
import pytest
from unittest.mock import Mock, patch

def test_prompt_generator_gateway_integration():
    """Test prompt generator sends correct request to gateway."""
    generator = PromptGenerator()
    gateway = LiteLLMGateway()
    
    with patch('litellm.completion') as mock_completion:
        mock_completion.return_value = Mock(
            choices=[Mock(message=Mock(content="Generated agent"))],
            usage=Mock(total_tokens=100)
        )
        
        # Generate agent from prompt
        result = generator.generate_agent(
            description="Create a customer support agent",
            gateway=gateway
        )
        
        # Validate integration
        assert "agent" in result
        assert result["agent"]["name"]
        assert result["agent"]["system_prompt"]
        
        # Validate gateway was called correctly
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args[1]
        assert "customer support" in str(call_args["messages"])
```

### Scenario 2: Agent → Tools

**Validate:**
- ✅ Agent invokes correct tools
- ✅ Tools invoked in correct order
- ✅ Agent completes without infinite loops

**Example:**

```python
import pytest
from unittest.mock import Mock

def test_agent_tool_orchestration():
    """Test agent orchestrates multiple tools correctly."""
    # Setup mock tools
    search_tool = Mock()
    search_tool.name = "search"
    search_tool.execute.return_value = {"results": ["Result 1", "Result 2"]}
    
    summarize_tool = Mock()
    summarize_tool.name = "summarize"
    summarize_tool.execute.return_value = {"summary": "Summary of results"}
    
    # Setup mock gateway
    mock_gateway = Mock()
    call_count = [0]
    
    def mock_generate(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call: use search tool
            return {
                "tool_calls": [{"name": "search", "arguments": {"query": "Python"}}],
                "finish_reason": "tool_calls"
            }
        elif call_count[0] == 2:
            # Second call: use summarize tool
            return {
                "tool_calls": [{"name": "summarize", "arguments": {"text": "..."}}],
                "finish_reason": "tool_calls"
            }
        else:
            # Final call: complete
            return {
                "text": "Task completed",
                "finish_reason": "stop"
            }
    
    mock_gateway.generate = mock_generate
    
    # Create agent with tools
    agent = Agent(gateway=mock_gateway, max_iterations=10)
    agent.add_tool(search_tool)
    agent.add_tool(summarize_tool)
    
    # Execute task
    result = agent.execute_task("Search for Python and summarize results")
    
    # Validate orchestration
    assert search_tool.execute.called
    assert summarize_tool.execute.called
    
    # Validate order (search before summarize)
    assert search_tool.execute.call_count == 1
    assert summarize_tool.execute.call_count == 1
    
    # Validate completion
    assert result["status"] == "completed"
    assert "text" in result or "output" in result
```

### Scenario 3: RAG Pipeline (Ingestion → Retrieval → Generation)

**Validate:**
- ✅ Ingested data is retrievable
- ✅ Retrieved context included in prompt
- ✅ Output adheres to expected response structure

**Example:**

```python
import pytest
from unittest.mock import Mock, patch

def test_rag_end_to_end_workflow():
    """Test complete RAG pipeline from ingestion to generation."""
    # Setup components
    mock_db = Mock()
    mock_vector_db = Mock()
    mock_gateway = Mock()
    
    # Create RAG system
    rag = RAGSystem(
        db=mock_db,
        vector_db=mock_vector_db,
        gateway=mock_gateway
    )
    
    # Step 1: Ingest document
    mock_vector_db.insert.return_value = "doc_1"
    
    doc_id = rag.ingest_document(
        title="Python Guide",
        content="Python is a programming language. It is easy to learn.",
        tenant_id="tenant_1"
    )
    
    assert doc_id == "doc_1"
    assert mock_vector_db.insert.called
    
    # Step 2: Retrieve documents
    mock_vector_db.search.return_value = [
        {"doc_id": "doc_1", "score": 0.95, "content": "Python is a programming language"}
    ]
    
    retrieved = rag.retrieve("What is Python?", tenant_id="tenant_1")
    
    assert len(retrieved) > 0
    assert retrieved[0]["doc_id"] == "doc_1"
    
    # Step 3: Generate response with context
    mock_gateway.generate.return_value = {
        "text": "Python is a programming language that is easy to learn.",
        "finish_reason": "stop"
    }
    
    response = rag.query(
        "What is Python?",
        tenant_id="tenant_1"
    )
    
    # Validate response structure
    assert "answer" in response
    assert "sources" in response
    assert len(response["sources"]) > 0
    assert response["sources"][0]["doc_id"] == "doc_1"
    
    # Validate context was passed to gateway
    gateway_call = mock_gateway.generate.call_args
    prompt = str(gateway_call[1]["messages"])
    assert "Python is a programming language" in prompt  # Context included
```

### Scenario 4: Cache Integration

**Validate:**
- ✅ Cache hit avoids recomputation
- ✅ Cache miss triggers fresh execution
- ✅ Cached data scoped correctly by tenant

**Example:**

```python
import pytest
from unittest.mock import Mock

def test_cache_integration_with_gateway():
    """Test that cache integration works with gateway."""
    mock_cache = Mock()
    mock_llm = Mock()
    
    gateway = LiteLLMGateway(cache=mock_cache)
    
    # First call: cache miss
    mock_cache.get.return_value = None
    mock_llm.completion.return_value = Mock(
        choices=[Mock(message=Mock(content="Fresh response"))],
        usage=Mock(total_tokens=50)
    )
    
    with patch('litellm.completion', mock_llm.completion):
        response1 = gateway.generate("Hello", model="gpt-4", tenant_id="t1")
    
    # Validate cache miss behavior
    assert mock_cache.get.called
    assert mock_cache.set.called  # Cache should be updated
    assert response1["text"] == "Fresh response"
    
    # Second call: cache hit
    mock_cache.get.return_value = {
        "text": "Cached response",
        "model": "gpt-4",
        "tokens": 50
    }
    
    response2 = gateway.generate("Hello", model="gpt-4", tenant_id="t1")
    
    # Validate cache hit behavior
    assert response2["text"] == "Cached response"
    assert mock_llm.completion.call_count == 1  # LLM not called again
```

### Scenario 5: LLMOps Integration

**Validate:**
- ✅ Logs, metrics, and traces generated for full workflow
- ✅ Correlation ID preserved across components
- ✅ Failures still emit telemetry

**Example:**

```python
import pytest
from unittest.mock import Mock

def test_llmops_cross_component_tracing():
    """Test that correlation ID flows through multiple components."""
    mock_llmops = Mock()
    correlation_id = "corr_12345"
    
    # Create components with LLMOps
    gateway = LiteLLMGateway(llmops=mock_llmops)
    rag = RAGSystem(gateway=gateway, llmops=mock_llmops)
    
    # Execute RAG query
    with patch('litellm.completion') as mock_completion:
        mock_completion.return_value = Mock(
            choices=[Mock(message=Mock(content="Response"))],
            usage=Mock(total_tokens=50)
        )
        
        rag.query(
            "What is Python?",
            tenant_id="tenant_1",
            correlation_id=correlation_id
        )
    
    # Validate LLMOps captured all operations
    assert mock_llmops.log_operation.called
    
    # All logged operations should have same correlation_id
    logged_calls = mock_llmops.log_operation.call_args_list
    for call in logged_calls:
        assert call[1]["correlation_id"] == correlation_id

def test_llmops_error_tracking():
    """Test that errors are logged with full context."""
    mock_llmops = Mock()
    
    gateway = LiteLLMGateway(llmops=mock_llmops)
    
    with patch('litellm.completion') as mock_completion:
        mock_completion.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            gateway.generate("Hello", model="gpt-4")
    
    # Validate error was logged
    assert mock_llmops.log_error.called
    error_log = mock_llmops.log_error.call_args[1]
    assert "error_message" in error_log
    assert "API Error" in error_log["error_message"]
```

---

## Error Scenarios and Edge Cases

### Overview

**All components must test comprehensive error scenarios** to ensure graceful failure handling and proper error propagation.

### Network Errors

```python
def test_gateway_network_timeout():
    """Test gateway handles network timeout."""
    gateway = LiteLLMGateway(timeout=5)
    
    with patch('litellm.completion') as mock_completion:
        mock_completion.side_effect = TimeoutError("Request timeout")
        
        with pytest.raises(GatewayError) as exc_info:
            gateway.generate("Hello", model="gpt-4")
        
        assert exc_info.value.error_type == "timeout"

def test_gateway_connection_refused():
    """Test gateway handles connection failures."""
    gateway = LiteLLMGateway()
    
    with patch('litellm.completion') as mock_completion:
        mock_completion.side_effect = ConnectionError("Connection refused")
        
        with pytest.raises(GatewayError) as exc_info:
            gateway.generate("Hello", model="gpt-4")
        
        assert exc_info.value.error_type == "connection_error"
```

### LLM Provider Errors

```python
def test_gateway_rate_limit_error():
    """Test gateway handles rate limit errors."""
    gateway = LiteLLMGateway()
    
    with patch('litellm.completion') as mock_completion:
        mock_completion.side_effect = Exception("Rate limit exceeded")
        
        with pytest.raises(GatewayError) as exc_info:
            gateway.generate("Hello", model="gpt-4")
        
        assert exc_info.value.error_type == "rate_limit"

def test_gateway_invalid_api_key():
    """Test gateway handles authentication errors."""
    gateway = LiteLLMGateway()
    
    with patch('litellm.completion') as mock_completion:
        mock_completion.side_effect = Exception("Invalid API key")
        
        with pytest.raises(GatewayError) as exc_info:
            gateway.generate("Hello", model="gpt-4")
        
        assert exc_info.value.error_type == "authentication_error"

def test_gateway_model_not_found():
    """Test gateway handles invalid model errors."""
    gateway = LiteLLMGateway()
    
    with patch('litellm.completion') as mock_completion:
        mock_completion.side_effect = Exception("Model not found")
        
        with pytest.raises(GatewayError) as exc_info:
            gateway.generate("Hello", model="invalid-model")
        
        assert exc_info.value.error_type == "model_not_found"
```

### Malformed Input Errors

```python
def test_rag_empty_query():
    """Test RAG handles empty queries."""
    rag = RAGSystem(db=Mock(), gateway=Mock())
    
    with pytest.raises(ValidationError) as exc_info:
        rag.query("", tenant_id="tenant_1")
    
    assert "empty" in str(exc_info.value).lower()

def test_rag_missing_tenant_id():
    """Test RAG enforces tenant_id requirement."""
    rag = RAGSystem(db=Mock(), gateway=Mock())
    
    with pytest.raises(ValidationError) as exc_info:
        rag.query("What is Python?", tenant_id=None)
    
    assert "tenant" in str(exc_info.value).lower()

def test_agent_invalid_tool_arguments():
    """Test agent handles invalid tool arguments."""
    mock_tool = Mock()
    mock_tool.name = "calculator"
    mock_tool.execute.side_effect = TypeError("Invalid argument type")
    
    agent = Agent(gateway=Mock())
    agent.add_tool(mock_tool)
    
    result = agent.execute_task("Calculate invalid input")
    
    # Should handle gracefully, not crash
    assert result["status"] == "failed" or "error" in result
```

### Edge Cases

```python
def test_cache_null_value_handling():
    """Test cache handles null values correctly."""
    cache = CacheManager()
    
    # Setting None should work
    cache.set("key1", None, ttl=60)
    
    # Getting None should return None, not indicate cache miss
    result = cache.get("key1")
    assert result is None
    
    # But key should exist in cache
    assert cache.exists("key1")

def test_rag_max_retrieval_limit():
    """Test RAG respects max retrieval limits."""
    mock_vector_db = Mock()
    mock_vector_db.search.return_value = [
        {"doc_id": str(i), "score": 0.9, "content": f"Doc {i}"}
        for i in range(1000)  # Return 1000 documents
    ]
    
    rag = RAGSystem(vector_db=mock_vector_db, gateway=Mock())
    
    results = rag.retrieve("query", top_k=5)
    
    # Should limit to top_k
    assert len(results) <= 5

def test_prompt_manager_empty_context():
    """Test prompt manager handles empty context."""
    manager = PromptManager()
    
    # No context added
    context = manager.build_context()
    
    # Should return empty list, not error
    assert isinstance(context, list)
    assert len(context) == 0
```

---

## Test Execution and Validation

### Running Tests

#### Unit Tests

```bash
# Run all unit tests
pytest src/tests/unit_tests/ -v

# Run specific component tests
pytest src/tests/unit_tests/test_litellm_gateway.py -v

# Run with coverage
pytest src/tests/unit_tests/ --cov=src/core --cov-report=html

# Run fast tests only (< 1 second)
pytest src/tests/unit_tests/ -m "not slow"

# Run with detailed output
pytest src/tests/unit_tests/ -vv --tb=short
```

#### Integration Tests

```bash
# Run all integration tests
pytest src/tests/integration_tests/ -m integration -v

# Run specific workflow tests
pytest src/tests/integration_tests/test_rag_integration.py -v

# Run with external service stubs
pytest src/tests/integration_tests/ --use-stubs

# Run with timeout
pytest src/tests/integration_tests/ --timeout=30
```

#### Coverage Reports

```bash
# Generate HTML coverage report
pytest src/tests/ --cov=src --cov-report=html

# View coverage summary
pytest src/tests/ --cov=src --cov-report=term-missing

# Check coverage thresholds
pytest src/tests/ --cov=src --cov-fail-under=80
```

### Pre-Merge Validation Checklist

Before merging any pull request, verify:

- ✅ **All tests pass** - Zero failures in unit + integration suites
- ✅ **Coverage thresholds met** - ≥80% for modified components
- ✅ **No new linting errors** - Run `ruff check src/`
- ✅ **All error paths tested** - 100% coverage of error handlers
- ✅ **Performance boundaries respected** - No timeout violations
- ✅ **Assertions contract-based** - No exact text matching (unless mocked)
- ✅ **Mocks properly configured** - All external services mocked
- ✅ **Documentation updated** - README and docstrings current

### Continuous Integration

**Required CI Checks:**

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run Unit Tests
        run: pytest src/tests/unit_tests/ --cov=src --cov-fail-under=80
      
      - name: Run Integration Tests
        run: pytest src/tests/integration_tests/ -m integration --timeout=900
      
      - name: Check Coverage
        run: pytest --cov=src --cov-report=xml
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
```

---

## Best Practices and Guidelines

### 1. Test Naming Conventions

**Format:** `test_<component>_<scenario>_<expected_behavior>`

**Examples:**
```python
✅ test_gateway_rate_limit_raises_error()
✅ test_agent_tool_selection_chooses_correct_tool()
✅ test_rag_empty_query_validation_fails()

❌ test_gateway()  # Too vague
❌ test_1()  # Non-descriptive
❌ testGatewayRateLimit()  # Wrong naming convention
```

### 2. Test Organization

**Structure:**
```python
class TestComponent:
    """Group related tests for a component."""
    
    def test_happy_path(self):
        """Test normal operation."""
        pass
    
    def test_error_path(self):
        """Test error handling."""
        pass
    
    def test_edge_case(self):
        """Test boundary conditions."""
        pass
```

### 3. Assertion Messages

**Provide context in assertions:**

```python
# ✅ GOOD: Clear failure message
assert result["status"] == "completed", \
    f"Expected status 'completed', got '{result['status']}'"

# ❌ BAD: No context
assert result["status"] == "completed"
```

### 4. Test Data Management

**Use fixtures for test data:**

```python
@pytest.fixture
def sample_document():
    return {
        "title": "Test Document",
        "content": "Test content",
        "metadata": {"author": "Test Author"}
    }

def test_with_sample_data(sample_document):
    result = process_document(sample_document)
    assert result["title"] == sample_document["title"]
```

### 5. Async Test Patterns

**Use pytest-asyncio for async tests:**

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

---

## Conclusion

### Summary of Key Points

This comprehensive testing guide establishes a **robust, production-ready framework** for validating GenAI components in the Motadata AI SDK:

1. **Non-Determinism Accommodation** - Tests validate contracts and invariants, not exact outputs
2. **Comprehensive Coverage** - 8 core components with 80%+ code coverage
3. **Practical Implementation** - 40+ complete, runnable code examples
4. **Quality Assurance** - Clear metrics, boundaries, and blocking gates
5. **Error Resilience** - Extensive error scenarios and edge case coverage

### Testing Maturity Model

| Level | Description | Status |
|-------|-------------|--------|
| **Level 1** | Basic unit tests exist | ✅ Complete |
| **Level 2** | Integration tests cover workflows | ✅ Complete |
| **Level 3** | Comprehensive error coverage | ✅ Complete |
| **Level 4** | Performance boundaries validated | ✅ Complete |
| **Level 5** | Automated quality gates | 🟡 In Progress |

### Next Steps

**For QA Engineers:**
1. Review component-specific test examples
2. Set up local test environment using fixtures
3. Begin implementing missing test cases
4. Integrate tests into CI/CD pipeline

**For Developers:**
1. Write tests before implementing features (TDD)
2. Ensure all new code meets coverage thresholds
3. Add error path tests for all exception handling
4. Update tests when modifying component behavior

**For Technical Leads:**
1. Enforce quality gates in code review process
2. Monitor coverage trends over time
3. Schedule quarterly test suite maintenance
4. Ensure team training on testing best practices

### Continuous Improvement

This guide is a **living document** and should be updated as:
- New components are added to the SDK
- Testing patterns evolve and improve
- New edge cases are discovered
- Tools and frameworks are upgraded

**Review Schedule:** Quarterly review and update of testing strategies

---

## References

### Documentation

- [SDK Architecture](docs/architecture/SDK_ARCHITECTURE.md) - System design and component structure
- [Component Documentation](docs/components/) - Detailed component specifications
- [Developer Integration Guide](docs/guide/DEVELOPER_INTEGRATION_GUIDE.md) - Development patterns
- [Unit Test Examples](src/tests/unit_tests/) - Reference implementations
- [Integration Test Examples](src/tests/integration_tests/) - Workflow tests

### Testing Frameworks

- **pytest Documentation**: https://docs.pytest.org/
- **pytest-mock Documentation**: https://pytest-mock.readthedocs.io/
- **Python unittest.mock**: https://docs.python.org/3/library/unittest.mock.html
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/

---
