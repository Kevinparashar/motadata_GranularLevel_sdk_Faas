# Python SDK Developer Guidelines
## Multi-Tenant AI SDK Platform

**Golden Rule: You build it. You test it. You own it.**

Every developer is also the QA owner of their feature.

## Purpose

This document defines mandatory engineering standards for our Python AI SDK to ensure:

- Strong tenant isolation
- High performance
- Operational reliability
- Clean architecture
- QA ownership by developers

These rules are **NOT optional**.

---

## 1. Multi-Tenancy (MANDATORY)

- Every operation MUST accept `tenant_id` parameter
- Tenant context must be validated at function boundary
- No global/shared state across tenants
- All DB and cache access MUST be tenant scoped
- Use `tenant_id` in all cache keys
- Never store tenant info in module-level variables

**Rule:**

If `tenant_id` is missing for multi-tenant operations, raise `ValueError` immediately.

**Example:**
```python
# GOOD
async def query_rag(self, query: str, tenant_id: str) -> dict:
    if not tenant_id:
        raise ValueError("tenant_id is required")
    cache_key = f"tenant:{tenant_id}:rag:{query}"
    # ...

# BAD
cache_key = f"rag:{query}"  # No tenant isolation
```

---

## 2. SDK Architecture

- One module per business domain
- Functions must be stateless
- No cross-module global state
- Inter-service communication via HTTP client (async)

**Component Structure:**
```
src/
├── core/              # Core SDK components
├── faas/              # FaaS service integrations
└── integrations/      # Third-party integrations
```

**Graceful Shutdown:**
- Close async connections
- Cancel pending tasks
- Clean up resources

---

## 3. Resilience

**Mandatory for all external calls:**

- Timeouts on ALL external calls
- Maximum retries = 3
- Circuit breakers for dependencies
- Idempotency for state-changing operations

**Example:**
```python
async def call_external_api(self, url: str, timeout: int = 30):
    async with asyncio.timeout(timeout):
        # ... make request
```

---

## 4. File and Function Limits

**Files:**
- Max 1000 lines (except generated code)

**Functions:**
- Max 80 lines
- Max 5 parameters
- No empty functions
- No duplicated logic

---

## 5. Error Handling and Logging

**Errors:**

- Never ignore errors
- Always use specific exception types
- Use domain errors for business logic
- Wrap external errors with context

**Logging:**

Every log MUST include:

- `tenant_id`
- `request_id` (if available)
- Structured logging only

**Rules:**

- Never log secrets or PII
- Use correct log levels (DEBUG, INFO, WARNING, ERROR)
- Use structured logging (dict format)

**Example:**
```python
logger.info(
    "RAG query executed",
    extra={
        "tenant_id": tenant_id,
        "request_id": request_id,
        "query_length": len(query)
    }
)
```

---

## 6. Concurrency

- All I/O operations MUST be async
- Use `asyncio` for concurrent operations
- Tasks must be cancellable via context
- No fire-and-forget tasks
- Always bound parallelism
- Use `asyncio.gather()` or `asyncio.create_task()` with proper error handling

**Example:**
```python
# GOOD
async def process_multiple(self, items: list):
    tasks = [self.process_item(item) for item in items[:10]]  # Bound
    results = await asyncio.gather(*tasks, return_exceptions=True)

# BAD
for item in items:  # No bound, no error handling
    asyncio.create_task(self.process_item(item))
```

---

## 7. Configuration

- Environment-based config only
- No hardcoded secrets
- Validate config at initialization
- Fail fast if config missing
- Use Pydantic for config validation

**Example:**
```python
class Config(BaseModel):
    database_url: str
    dragonfly_url: Optional[str] = None
    
    @validator('database_url')
    def validate_db_url(cls, v):
        if not v:
            raise ValueError("database_url is required")
        return v
```

---

## 8. Database Rules

- Queries must be tenant scoped
- Never use `SELECT *`
- Pagination mandatory for large datasets
- Use parameterized queries (prevent SQL injection)
- Use async database operations
- Connection pooling required

**Example:**
```python
# GOOD
async def get_documents(
    self, 
    tenant_id: str, 
    limit: int = 100, 
    offset: int = 0
):
    query = """
        SELECT id, content, metadata 
        FROM documents 
        WHERE tenant_id = $1 
        LIMIT $2 OFFSET $3
    """
    return await self.db.fetch(query, tenant_id, limit, offset)
```

---

## 9. Cache (Dragonfly)

- Cache keys MUST include `tenant_id`
- TTL mandatory for all cache entries
- Cache-aside pattern
- Graceful fallback to DB on cache miss

**Example:**

```
tenant:{tenant_id}:rag:query:{hash}
tenant:{tenant_id}:agent:{agent_id}
tenant:{tenant_id}:cache:{key}
```

**Code:**
```python
def _get_cache_key(self, key: str, tenant_id: str) -> str:
    return f"tenant:{tenant_id}:{self.namespace}:{key}"
```

---

## 10. Rate Limiting and Fairness

- Per-tenant rate limits
- Return appropriate errors (HTTP 429 equivalent)
- Tier-based quotas
- Prevent noisy neighbors

---

## 11. API Standards

- Backward compatible changes only
- Major breaking changes via versioning
- Validate inputs at boundaries (reject invalid requests early)
- Consistent error format
- Type hints mandatory for all public APIs

**Example:**
```python
async def query(
    self,
    query_text: str,
    tenant_id: str,
    top_k: int = 5,
    **kwargs: Any
) -> Dict[str, Any]:
    """Query RAG system.
    
    Args:
        query_text: The query string
        tenant_id: Tenant identifier (required)
        top_k: Number of results to return
        
    Returns:
        Dict containing query results
        
    Raises:
        ValueError: If tenant_id is missing
    """
```

---

## 12. Async/Await Patterns

- All I/O operations MUST be async
- Use `async def` for functions that perform I/O
- Use `await` for async operations
- Never use `asyncio.run()` inside async functions
- Use `asyncio.to_thread()` for CPU-bound operations

**Example:**
```python
# GOOD
async def process_file(self, file_path: str):
    content = await asyncio.to_thread(self._read_file, file_path)
    result = await self._process_async(content)
    return result

# BAD
async def process_file(self, file_path: str):
    content = open(file_path).read()  # Blocking I/O
    result = self._process(content)  # Not async
```

---

## 13. QA OWNERSHIP (MANDATORY)

**Every Developer is QA.**

There is NO separate QA dependency.

A feature is NOT DONE until the developer fully tests it.

### Developer QA Responsibilities:

**Functional Testing:**
- Happy path
- Edge cases
- Negative scenarios
- Tenant isolation

**Unit Tests:**
- All business logic
- Tenant-aware tests
- External dependencies mocked
- Minimum **85% coverage** on new code

**Integration Testing:**
- Multi-tenant flows
- Database interaction
- Cache behavior
- Data integrity and validation

**Manual Testing:**
- SDK functions work end-to-end
- Logs contain `tenant_id` and `request_id`
- Errors handled correctly
- Rate limits respected

**Performance Validation:**
- If code touches cache, DB, serialization, or concurrency, benchmarks are REQUIRED
- No regressions allowed

**PR will be rejected if:**
- Feature not manually tested
- Unit tests missing
- Tenant isolation not verified
- Benchmarks missing (if applicable)
- QA checklist incomplete
- Coverage below 85%

---

## 14. Benchmarking

- All new or modified performance-sensitive code must include benchmarks
- Use `pytest-benchmark`
- Benchmarks must not show performance regression
- PRs with performance degradation must not be approved
- Include memory allocation benchmarks

**Example:**
```python
def benchmark_rag_query(benchmark):
    rag = create_rag_system(...)
    query = "test query"
    tenant_id = "test_tenant"
    
    result = benchmark(rag.query_async, query, tenant_id=tenant_id)
    assert result is not None
```

---

## 15. Testing Requirements

**Unit Tests:**
- Use `pytest` and `pytest-asyncio`
- Mock external dependencies
- Test tenant isolation
- Minimum 85% coverage

**Integration Tests:**
- Test with real database (test DB)
- Test with real cache (test instance)
- Clean up after tests

**Test Structure:**
```
tests/
├── unit_tests/          # Unit tests
├── integration_tests/    # Integration tests
└── benchmarks/          # Performance benchmarks
```

---

## 16. Code Quality

- Follow PEP 8 style guide
- Use type hints for all functions
- Use `mypy` for type checking
- Use `black` for code formatting
- Use `ruff` or `pylint` for linting
- SonarQube Quality Gate must pass

**SonarQube Requirements:**
- New Bugs: **0**
- New Vulnerabilities: **0**
- New Security Hotspots: **0**
- New Critical Code Smells: **0**
- New Major Code Smells: **0**
- Reliability Rating: **A**
- Security Rating: **A**
- Maintainability Rating: **A or B**
- Code Coverage: **≥ 85%**

---

## 17. Ownership and Reviews

- Every module has an owner
- Minimum 1 PR approval
- Sonar Quality Gate must pass
- Large changes require architecture review

---

## PR Self-QA Checklist

- [ ] Feature manually tested
- [ ] Unit tests added (≥ 85% coverage)
- [ ] Tenant isolation verified
- [ ] Logs validated (include tenant_id)
- [ ] Benchmarks added (if applicable)
- [ ] No linter errors
- [ ] No ignored errors
- [ ] Cache keys tenant scoped
- [ ] Timeouts configured
- [ ] Async/await patterns correct
- [ ] Type hints added
- [ ] Documentation updated

---

## Final Rule

**You build it. You test it. You own it.**

