# PYTHON SDK QUALITY GATE RULES AND DEVELOPMENT GUIDELINE DOCUMENT

> **Audience:** Python SDK contributors, reviewers, maintainers  
> **Enforcement model:** **CI blocks merge** + **Sonar Quality Gate blocks merge**  
> **Repo alignment note:** This document is **cross-checked** against the current SDK repo structure (Makefile + pyproject + tests). Where the repo is missing enforcement/config, this doc provides **exact drop-in templates** to close the gaps.

---


### 0.1 Verified in your SDK repo (already present)
**Tooling**
- `pyproject.toml` config exists for: **black**, **isort**, **mypy**, **pytest**.
- Dev deps include: `pytest`, `pytest-asyncio`, `pytest-mock`, `pytest-cov`, `black`, `isort`, `mypy`.

**Makefile targets (usable today)**
- `format`, `format-check` → black + isort
- `type-check` → mypy
- `test`, `test-unit`, `test-integration`, `test-cov` → pytest + coverage report (HTML/term)
- `build` → `python -m build`
- `ci` → runs clean + install-dev + test + format-check + type-check

**Test structure**
- `src/tests/unit_tests`, `src/tests/integration_tests`, `src/tests/benchmarks`

### 0.2 Not present in the repo (must be added to be Sonar+CI compliant)
These are **Quality Gate must-haves** that are missing today:
- ❌ **No CI pipeline configuration** (no `.github/workflows/*`, no GitLab CI, etc.)
- ❌ **No Sonar configuration** (`sonar-project.properties` / scanner settings)
- ❌ **No enforced coverage threshold** (`--cov-fail-under=80` is not used in Makefile)
- ❌ **Lint is a placeholder** in Makefile (no ruff/flake8/pylint installed or executed)
- ❌ **No complexity enforcement**
- ❌ **No security gates** (`bandit`, `pip-audit`, `detect-secrets`) not present
- ❌ **No branch protection / PR governance documented with templates**

This document upgrades your current baseline into a **merge-blocking Quality Gate system**.

---

## 1) Mandatory Operating Model (non-negotiable)

### 1.1 Branch protection rules (mandatory)
- **No direct commits to `main`** (protected default branch).
- **All changes must be via PR**.
- **Mandatory CI pass** on PR.
- **Mandatory Sonar Quality Gate pass** on PR.
- **Mandatory approvals** (minimum 1; increase for critical components).

**Branch protection checklist (admin settings)**
- [ ] Disallow force-pushes to `main`
- [ ] Disallow direct pushes to `main`
- [ ] Require PR before merge
- [ ] Require status checks to pass (CI + Sonar gate)
- [ ] Require at least 1 approval
- [ ] Require linear history (recommended)

### 1.2 Gate waiver policy (strict)
Waivers are allowed **only** with:
- written justification in PR
- risk statement
- remediation ticket
- owner + deadline

No silent bypasses. No “we will fix later” without a tracked ticket.

---

## 2) Quality Gate Definition (Sonar + CI aligned)

### 2.1 PR Quality Gate (merge-blocking)
A PR is mergeable only if **all** pass:

**CI checks**
1. Format check (black/isort or ruff-format)
2. Lint check (ruff standardized)
3. Type check (mypy)
4. Unit tests
5. Integration tests (when component touches external dependency)
6. Coverage threshold: **≥ 80% (new code)**
7. Security scans: secrets + SAST + dependency audit
8. Build/package verification

**Sonar checks**
1. **Quality Gate = PASSED**
2. **Coverage on New Code ≥ 80%**
3. Reliability rating on New Code = **A**
4. Security rating on New Code = **A**
5. Maintainability rating on New Code = **A**
6. **0 new Blocker/Critical** issues

> **Rule:** If Sonar or CI is red → **no merge**.

### 2.2 Release Quality Gate (stricter)
All PR gates plus:
- cross-version run (e.g., 3.8–3.12)
- packaging install smoke test in clean environment
- vulnerability scan must have **0 High/Critical** (or approved waiver)

---

## 3) Mandatory Code Rules (with examples)

### 3.1 Formatting rules (mandatory)
**Rule**
- Black + isort output is the canonical style. No “pretty formatting” by hand.

**Good example**
```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
```

**Bad example (will fail format-check)**
```python
from dataclasses import dataclass
@dataclass
class User: id:int; name:str
```

**Commands**
```bash
make format
make format-check
```

---

### 3.2 Linting rules (mandatory) — Standardized on Ruff

**Standard**
- Use **Ruff** as the single linter (fast + rule-rich).
- Optional: keep flake8/pylint only if legacy demands (not recommended for greenfield).

**Must-block categories**
- unused imports/variables
- undefined names
- broad exception patterns (bare `except:`)
- swallowing exceptions without context/logging
- dangerous calls (`eval`, `exec`)
- import cycles (where detectable)
- poor practices (mutable defaults, etc.)

**Bad → Good examples**

**(A) Bare except**
```python
# BAD (blocks)
try:
    do_work()
except:
    pass
```

```python
# GOOD
import logging

logger = logging.getLogger(__name__)

try:
    do_work()
except KnownError as exc:
    logger.exception("do_work failed: %s", exc)
    raise
```

**(B) Mutable default**
```python
# BAD (blocks)
def add_item(x, items=[]):
    items.append(x)
    return items
```

```python
# GOOD
from typing import Optional

def add_item(x, items: Optional[list] = None):
    items = [] if items is None else items
    items.append(x)
    return items
```

**Ruff commands**
```bash
ruff check .
ruff format --check .
```

**Drop-in Ruff config template (add to `pyproject.toml`)**
```toml
[tool.ruff]
line-length = 100
target-version = "py38"
fix = false

[tool.ruff.lint]
select = ["E", "F", "B", "I", "UP", "SIM", "PL", "RUF"]
ignore = []
```

**Add dev dependency**
```text
ruff>=0.6.0
```

---

### 3.3 Typing rules (mandatory)
**Rules**
- All **new/modified public** functions/classes must be type-hinted.
- No `Any` in public signatures unless justified.
- `# type: ignore` requires a reason.

**Bad**
```python
def fetch_user(user_id):
    ...
```

**Good**
```python
def fetch_user(user_id: int) -> dict[str, str]:
    ...
```

**Repo current-state note**
- `mypy` exists but `disallow_untyped_defs = false` currently allows untyped defs.  
  **Gate requirement:** enforce stricter typing on **new code**.

**Recommended mypy tightening (pyproject)**
```toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true
no_implicit_optional = true
```

---

### 3.4 Project Structure & Naming Conventions (Mandatory)

#### 3.4.1 Project Structure

**Standard SDK Structure:**
```
motadata-python-ai-sdk/
├── src/
│   ├── core/                    # Core AI components
│   │   ├── agno_agent_framework/
│   │   ├── rag/
│   │   ├── litellm_gateway/
│   │   ├── cache_mechanism/
│   │   ├── machine_learning/
│   │   └── ...
│   ├── faas/                    # FaaS Services
│   │   ├── services/
│   │   │   ├── agent_service/
│   │   │   ├── rag_service/
│   │   │   └── ...
│   │   └── shared/
│   ├── integrations/           # Integration components
│   └── tests/                   # Test suite
│       ├── unit_tests/
│       ├── integration_tests/
│       └── benchmarks/
├── examples/                    # Usage examples
├── docs/                        # Documentation
└── pyproject.toml              # Project configuration
```

#### 3.4.2 Naming Conventions

**File Naming:**
- Use `snake_case` for all Python files: `rag_system.py`, `agent_framework.py`
- Test files must start with `test_`: `test_agent.py`, `test_rag_system.py`
- Module files: `__init__.py` (always lowercase)

**Class Naming:**
- Use `PascalCase`: `RAGSystem`, `LiteLLMGateway`, `AgentMemory`
- Exception classes must end with `Error`: `AgentError`, `GatewayError`, `RAGError`

**Function/Method Naming:**
- Use `snake_case`: `create_agent()`, `query_async()`, `ingest_document()`
- Async functions should end with `_async`: `query_async()`, `generate_async()`
- Factory functions should start with `create_`: `create_agent()`, `create_rag_system()`

**Variable Naming:**
- Use `snake_case`: `tenant_id`, `query_text`, `cache_key`
- Constants use `UPPER_SNAKE_CASE`: `DEFAULT_TTL`, `MAX_RETRIES`

**Module/Package Naming:**
- Use `snake_case`: `agno_agent_framework`, `litellm_gateway`, `cache_mechanism`

**Examples:**
```python
# GOOD (follows conventions)
class RAGSystem:
    async def query_async(self, query_text: str, tenant_id: str) -> dict:
        cache_key = f"rag:{tenant_id}:{hash(query_text)}"
        return await self._execute_query(query_text, tenant_id)

def create_rag_system(db, gateway, **kwargs) -> RAGSystem:
    return RAGSystem(db=db, gateway=gateway, **kwargs)

# BAD (violates conventions)
class ragSystem:  # Should be PascalCase
    async def Query(self, queryText: str, tenantId: str):  # Should be snake_case
        CacheKey = f"rag:{tenantId}"  # Should be snake_case
```

---

### 3.5 Docstring Standards (Mandatory)

#### 3.5.1 Docstring Format

**Rule:** All public classes, functions, and methods must have docstrings using Google-style format.

**Required Elements:**
- One-line summary
- Detailed description (if needed)
- Args section (for functions/methods)
- Returns section (for functions/methods)
- Raises section (if exceptions are raised)
- Examples section (for complex functions)

#### 3.5.2 Docstring Examples

**Class Docstring:**
```python
class RAGSystem:
    """
    Complete RAG system integrating document processing, retrieval, and generation.
    
    Handles document ingestion, vector search, and LLM-based answer generation
    with tenant isolation and caching support.
    
    Attributes:
        db: Database connection for vector storage
        gateway: LiteLLM Gateway for LLM operations
        embedding_model: Model name for embeddings
        generation_model: Model name for text generation
        cache: Optional cache mechanism for performance
    """
```

**Function Docstring:**
```python
async def query_async(
    self,
    query_text: str,
    top_k: int = 5,
    tenant_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Query RAG system asynchronously with tenant isolation.
    
    Processes a natural language query by:
    1. Generating embeddings for the query
    2. Performing vector similarity search
    3. Generating answer using retrieved context
    
    Args:
        query_text: Natural language query string
        top_k: Number of top documents to retrieve (default: 5)
        tenant_id: Tenant identifier for multi-tenant isolation (required)
        **kwargs: Additional parameters passed to gateway
    
    Returns:
        Dictionary containing:
            - answer: Generated answer text
            - sources: List of retrieved document chunks
            - metadata: Query metadata (model, tokens, etc.)
    
    Raises:
        ValueError: If tenant_id is not provided
        GatewayError: If LLM gateway call fails
        DatabaseError: If vector search fails
    
    Example:
        ```python
        result = await rag.query_async(
            query_text="What is machine learning?",
            top_k=5,
            tenant_id="tenant_123"
        )
        print(result["answer"])
        ```
    """
```

**Factory Function Docstring:**
```python
def create_rag_system(
    db: DatabaseConnection,
    gateway: LiteLLMGateway,
    embedding_model: str = "text-embedding-3-small",
    **kwargs: Any
) -> RAGSystem:
    """
    Factory function to create a RAG system instance.
    
    Creates and configures a RAG system with sensible defaults.
    All components are initialized and ready for use.
    
    Args:
        db: Database connection (required)
        gateway: LiteLLM Gateway instance (required)
        embedding_model: Model for embedding generation (default: "text-embedding-3-small")
        **kwargs: Additional configuration options:
            - generation_model: Model for text generation (default: "gpt-4")
            - cache: Optional cache mechanism
            - chunk_size: Document chunk size (default: 1000)
            - chunk_overlap: Chunk overlap size (default: 200)
    
    Returns:
        Configured RAGSystem instance
    
    Raises:
        ValueError: If required parameters are missing
        ConfigurationError: If configuration is invalid
    
    Example:
        ```python
        rag = create_rag_system(
            db=db_connection,
            gateway=gateway_instance,
            embedding_model="text-embedding-3-small",
            chunk_size=1000
        )
        ```
    """
```

**Bad Docstring Examples:**
```python
# BAD (no docstring)
class RAGSystem:
    def query(self, q):
        pass

# BAD (incomplete docstring)
def query(self, q):
    """Query RAG system."""
    pass

# BAD (wrong format)
def query(self, q):
    """
    @param q: query
    @return: result
    """
    pass
```

#### 3.5.3 Docstring Enforcement

**CI Enforcement:**
- Missing docstrings on public APIs → **FAILS CI**
- Incomplete docstrings (missing Args/Returns) → **WARNING** (for now, will become FAIL in future)
- Private methods (`_method`) → **WARNING** (recommended but not required)

**Tools:**
- Use `pydocstyle` for docstring checking:
```bash
pydocstyle src --convention=google
```

---

### 3.6 CI Failure vs Warnings (Mandatory)

#### 3.6.1 What FAILS CI (Merge-Blocking)

**These checks MUST pass or PR cannot be merged:**

1. **Format Check (FAILS CI)**
   - Black formatting violations
   - isort import ordering violations
   - **Action:** PR is blocked, must fix

2. **Lint Check (FAILS CI)**
   - Unused imports/variables
   - Undefined names
   - Syntax errors
   - Dangerous patterns (`eval`, `exec`, bare `except`)
   - **Action:** PR is blocked, must fix

3. **Type Check (FAILS CI)**
   - Missing type hints on public APIs
   - Type errors (incompatible types)
   - `Any` usage without justification
   - **Action:** PR is blocked, must fix

4. **Unit Tests (FAILS CI)**
   - Any test failure
   - Test timeouts
   - **Action:** PR is blocked, must fix

5. **Coverage Threshold (FAILS CI)**
   - New code coverage < 80%
   - Overall coverage drops below threshold
   - **Action:** PR is blocked, must add tests

6. **Security Scans (FAILS CI)**
   - Secrets detected in code
   - High/Critical vulnerabilities
   - Unsafe patterns (`eval`, `exec`, `shell=True`)
   - **Action:** PR is blocked, must fix

7. **Build Verification (FAILS CI)**
   - Package build fails
   - Import errors
   - **Action:** PR is blocked, must fix

8. **Sonar Quality Gate (FAILS CI)**
   - Quality Gate = FAILED
   - New Blocker/Critical issues
   - Coverage on new code < 80%
   - Security rating < A
   - **Action:** PR is blocked, must fix

#### 3.6.2 What are WARNINGS (Non-Blocking)

**These checks generate warnings but do NOT block merge:**

1. **Code Complexity (WARNING)**
   - Cyclomatic complexity > 10 (but ≤ 15)
   - Function length > 80 LOC (but ≤ 120 LOC)
   - **Action:** Warning in PR, review recommended

2. **Docstring Completeness (WARNING)**
   - Missing docstrings on private methods
   - Incomplete docstrings (missing optional sections)
   - **Action:** Warning in PR, fix recommended

3. **Type Hints (WARNING)**
   - Missing type hints on private methods
   - `Any` usage with justification comment
   - **Action:** Warning in PR, improve recommended

4. **Sonar Code Smells (WARNING)**
   - Minor code smells (not bugs/vulnerabilities)
   - Maintainability issues (non-critical)
   - **Action:** Warning in PR, technical debt

5. **Dependency Vulnerabilities (WARNING)**
   - Low/Medium severity vulnerabilities
   - Outdated dependencies (non-critical)
   - **Action:** Warning in PR, update recommended

#### 3.6.3 CI Status Summary

| Check | Status | Action |
|-------|--------|--------|
| Format check fails | ❌ **FAILS CI** | Block merge, must fix |
| Lint errors | ❌ **FAILS CI** | Block merge, must fix |
| Type errors | ❌ **FAILS CI** | Block merge, must fix |
| Test failures | ❌ **FAILS CI** | Block merge, must fix |
| Coverage < 80% | ❌ **FAILS CI** | Block merge, must add tests |
| Secrets detected | ❌ **FAILS CI** | Block merge, must remove |
| Sonar gate failed | ❌ **FAILS CI** | Block merge, must fix |
| Complexity > 15 | ⚠️ **WARNING** | Review recommended |
| Missing private docstrings | ⚠️ **WARNING** | Improve recommended |
| Code smells (minor) | ⚠️ **WARNING** | Technical debt |

#### 3.6.4 Example CI Output

**FAILING CI (Blocked):**
```
❌ Format check: FAILED
   - src/core/rag/rag_system.py:15:1 - Line too long
   - src/core/agent/agent.py:42:3 - Import not sorted

❌ Lint check: FAILED
   - src/core/gateway/gateway.py:23 - Unused import 'os'
   - src/core/cache/cache.py:45 - Undefined name 'dragonfly_client'

❌ Type check: FAILED
   - src/core/rag/rag_system.py:67 - Missing return type annotation

❌ Coverage: FAILED
   - New code coverage: 65% (required: 80%)
   - Missing coverage in: src/core/rag/retriever.py

→ PR BLOCKED: Must fix all failures before merge
```

**PASSING CI (with warnings):**
```
✅ Format check: PASSED
✅ Lint check: PASSED
✅ Type check: PASSED
✅ Tests: PASSED (120 tests, 0 failures)
✅ Coverage: PASSED (85% new code coverage)
✅ Security: PASSED (no secrets, no high vulnerabilities)
✅ Sonar: PASSED (Quality Gate: PASSED)

⚠️ Warnings:
   - src/core/agent/agent.py:234 - Function complexity: 12 (recommended: ≤10)
   - src/core/rag/rag_system.py:156 - Missing docstring on private method
   - Sonar: 3 minor code smells detected

→ PR APPROVED: Can merge (warnings are non-blocking)
```

---

## 4) Coverage Gate (≥ 80%) — Mandatory with examples

### 4.1 Coverage threshold (mandatory)
- **Coverage on New Code ≥ 80%** (Sonar gate)
- CI must enforce `--cov-fail-under=80` for immediate feedback.

**Repo current-state note**
- `pytest-cov` exists, but `test-cov` does not enforce threshold today.

### 4.2 Update Makefile (drop-in replacement)
Replace `test-cov` with:

```make
test-cov: ## Run tests with coverage report + enforce threshold
	$(PYTHON) -m pytest $(TESTS_DIR) \
		--cov=$(SRC_DIR) --cov-report=term-missing --cov-report=xml \
		--cov-fail-under=80
```

### 4.3 Example: what “good coverage” means
If you add a new helper `normalize_headers()` you must add a test that covers:
- normal input
- empty input
- mixed-case headers
- invalid types (raises)

**Implementation**
```python
def normalize_headers(headers: dict[str, str]) -> dict[str, str]:
    return {k.lower(): v.strip() for k, v in headers.items()}
```

**Tests**
```python
def test_normalize_headers_lowercases_and_strips():
    assert normalize_headers({"X-Token": " abc "}) == {"x-token": "abc"}
```

---

## 5) Complexity Limits (mandatory)

### 5.1 Limits (enforced)
- **Cyclomatic complexity per function: ≤ 10**
- **Cognitive complexity per function: ≤ 15** (Sonar)
- **Function length soft limit: ≤ 80 LOC** (review gate; make hard later if needed)

### 5.2 Enforcement options (choose 1 path, but enforce consistently)
**Primary (recommended): Sonar**
- Enforce cognitive complexity via Sonar rules.
- Fail Quality Gate on new violations.

**Secondary (CI local enforcement): Radon**
Add dev dependency:
```text
radon>=6.0.0
```

CI command:
```bash
radon cc -s -n B src
# "B" or better only; adjust if needed
```

### 5.3 Example: reducing complexity
**Bad (complex, nested, fragile)**
```python
def build_payload(data):
    if data:
        if "user" in data:
            if "id" in data["user"]:
                ...
```

**Good (early returns + helpers)**
```python
def build_payload(data: dict) -> dict:
    user = data.get("user") or {}
    user_id = user.get("id")
    if not user_id:
        raise ValueError("user.id is required")
    return {"userId": user_id}
```

---

## 6) Security Rules (mandatory) — secrets, unsafe eval, dependency risk

### 6.1 Mandatory block rules
CI must fail if:
- **Secrets** exist in repo (keys, tokens, passwords, private keys)
- **Unsafe eval/exec** used
- **Pickle loads on untrusted input** exists
- `subprocess` uses `shell=True` without strict justification
- HTTP clients lack timeouts
- retries are unbounded

### 6.2 Examples (bad → good)

**(A) `eval`**
```python
# BAD (blocks)
result = eval(user_input)
```

```python
# GOOD (safe alternative)
import json
result = json.loads(user_input)
```

**(B) No HTTP timeout**
```python
# BAD (blocks)
requests.get(url)
```

```python
# GOOD
requests.get(url, timeout=10)
```

**(C) Secrets in code**
```python
# BAD (blocks)
API_KEY = "sk_live_..."
```

```python
# GOOD (env + secrets manager)
import os
API_KEY = os.environ["API_KEY"]
```

### 6.3 Mandatory security tools (CI)
Add dev deps:
```text
bandit>=1.7.0
pip-audit>=2.7.0
detect-secrets>=1.5.0
```

Commands:
```bash
detect-secrets scan --baseline .secrets.baseline
bandit -r src -q
pip-audit
```

**detect-secrets baseline template**
```bash
detect-secrets scan > .secrets.baseline
```

---

## 7) PR Rules (mandatory) — templates and checkpoints

### 7.1 PR requirements (merge-blocking)
- [ ] No direct commits to `main`
- [ ] PR has description + risk assessment
- [ ] CI green
- [ ] Sonar gate green
- [ ] Coverage ≥ 80% new code
- [ ] Lint passes (ruff)
- [ ] Type-check passes (mypy)
- [ ] Security scans pass
- [ ] Component docs updated (if public behavior changes)

### 7.2 PR description template (copy/paste)
```markdown
## What changed
- 

## Why
- 

## Risk & blast radius
- Low / Medium / High
- Affected components:
- Rollback plan:

## Validation evidence
- [ ] ruff check .
- [ ] mypy src
- [ ] pytest unit
- [ ] pytest integration (if applicable)
- [ ] coverage >= 80%
- [ ] security scans (bandit/pip-audit/detect-secrets)

## Sonar
- Quality Gate: PASSED
- New Code Coverage: __%
- New issues: 0 critical/blocker
```

### 7.3 Review checklist (for reviewers)
- [ ] Tests cover critical paths
- [ ] Exceptions are actionable (context + remediation)
- [ ] No hidden breaking change
- [ ] Complexity within limits
- [ ] No secrets / security smells
- [ ] Public API changes documented

---

## 7.5 SDK-Specific Coding Patterns (Mandatory)

### 7.5.1 Async-First Pattern

**Rule:** All I/O operations (database, HTTP, LLM calls) must use async/await.

**Bad (synchronous blocking):**
```python
# BAD (blocks event loop)
def query_rag(self, query: str) -> dict:
    result = self.db.execute_query(query)  # Blocks
    return result
```

**Good (async):**
```python
# GOOD (non-blocking)
async def query_rag_async(self, query: str) -> dict[str, Any]:
    result = await self.db.execute_query_async(query)
    return result
```

**Example from SDK (RAG System):**
```python
# src/core/rag/rag_system.py
async def query_async(
    self,
    query_text: str,
    top_k: int = 5,
    tenant_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Async query method - required for production."""
    # All I/O is async
    embeddings = await self.gateway.embed_async(query_text, model=self.embedding_model)
    results = await self.vector_ops.search_async(embeddings[0], top_k=top_k, tenant_id=tenant_id)
    # ...
```

### 7.5.2 Tenant Isolation Pattern

**Rule:** All components must support `tenant_id` parameter for multi-tenant isolation.

**Bad (no tenant isolation):**
```python
# BAD (no tenant context)
def get_cache(self, key: str) -> Any:
    return self.cache.get(key)  # No tenant isolation
```

**Good (tenant-scoped):**
```python
# GOOD (tenant isolation)
def get_cache(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
    if not tenant_id:
        raise ValueError("tenant_id is required for multi-tenant operations")
    return self.cache.get(key, tenant_id=tenant_id)
```

**Example from SDK (Cache Mechanism):**
```python
# src/core/cache_mechanism/cache.py
def _namespaced_key(self, key: str, tenant_id: Optional[str] = None) -> str:
    """Create namespaced cache key with optional tenant isolation."""
    if tenant_id:
        return f"{self.config.namespace}:{tenant_id}:{key}"
    return f"{self.config.namespace}:{key}"

def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
    namespaced = self._namespaced_key(key, tenant_id=tenant_id)
    # ...
```

### 7.5.3 Dependency Injection Pattern

**Rule:** Components receive dependencies via constructor injection, not global imports.

**Bad (tight coupling):**
```python
# BAD (hard dependency)
from src.core.litellm_gateway import LiteLLMGateway

class Agent:
    def __init__(self):
        self.gateway = LiteLLMGateway()  # Hard dependency
```

**Good (dependency injection):**
```python
# GOOD (injected dependency)
class Agent:
    def __init__(self, gateway: LiteLLMGateway, tenant_id: Optional[str] = None):
        self.gateway = gateway  # Injected
        self.tenant_id = tenant_id
```

**Example from SDK (Agent Framework):**
```python
# src/core/agno_agent_framework/agent.py
class Agent(BaseModel):
    gateway: Optional[Any] = None  # LiteLLM Gateway instance (injected)
    tenant_id: Optional[str] = None  # Tenant context for multi-tenant SaaS
    
    async def execute_task(self, task: AgentTask) -> Any:
        # Uses injected gateway
        response = await self.gateway.generate_async(
            prompt=task.prompt,
            model=self.llm_model,
            tenant_id=self.tenant_id or task.tenant_id,
        )
```

### 7.5.4 Factory Function Pattern

**Rule:** Use factory functions for component creation (not direct class instantiation).

**Bad (direct instantiation):**
```python
# BAD (complex initialization)
gateway = LiteLLMGateway(
    api_key=os.getenv("API_KEY"),
    provider="openai",
    default_model="gpt-4",
    enable_caching=True,
    cache_ttl=3600,
    # ... many parameters
)
```

**Good (factory function):**
```python
# GOOD (simplified creation)
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(
    api_key=os.getenv("API_KEY"),
    provider="openai",
    default_model="gpt-4"
)
```

**Example from SDK (Gateway Factory):**
```python
# src/core/litellm_gateway/functions.py
def create_gateway(
    api_key: str,
    provider: str = "openai",
    default_model: str = "gpt-4",
    **kwargs: Any
) -> LiteLLMGateway:
    """Factory function to create a LiteLLM Gateway instance."""
    config = GatewayConfig(
        enable_caching=kwargs.get("enable_caching", True),
        cache_ttl=kwargs.get("cache_ttl", 3600),
        # ... sensible defaults
    )
    return LiteLLMGateway(api_key=api_key, provider=provider, default_model=default_model, config=config)
```

### 7.5.5 Error Handling Pattern

**Rule:** Use custom exception hierarchy, never bare `except:`.

**Bad (bare except):**
```python
# BAD (swallows all errors)
try:
    result = await gateway.generate_async(prompt)
except:
    return None  # Lost error context
```

**Good (specific exceptions):**
```python
# GOOD (specific error handling)
from src.core.exceptions import GatewayError, RateLimitError

try:
    result = await gateway.generate_async(prompt, tenant_id=tenant_id)
except RateLimitError as e:
    logger.warning(f"Rate limit exceeded for tenant {tenant_id}: {e}")
    raise  # Re-raise with context
except GatewayError as e:
    logger.error(f"Gateway error for tenant {tenant_id}: {e}")
    raise
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    raise GatewayError(f"Unexpected error: {e}") from e
```

**Example from SDK (Exception Hierarchy):**
```python
# src/core/agno_agent_framework/exceptions.py
class AgentError(Exception):
    """Base exception for agent errors."""
    pass

class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""
    pass

class AgentConfigurationError(AgentError):
    """Raised when agent configuration is invalid."""
    pass
```

### 7.5.6 Type Hints for Public APIs

**Rule:** All public methods must have complete type hints (no `Any` unless justified).

**Bad (missing types):**
```python
# BAD (no type hints)
def query(self, query, top_k=5, **kwargs):
    # ...
```

**Good (complete types):**
```python
# GOOD (complete type hints)
from typing import Dict, Any, Optional, List

async def query_async(
    self,
    query_text: str,
    top_k: int = 5,
    tenant_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Query RAG system with type hints."""
    # ...
```

**Example from SDK (RAG System):**
```python
# src/core/rag/rag_system.py
async def query_async(
    self,
    query_text: str,
    top_k: int = 5,
    tenant_id: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Query RAG system asynchronously."""
    # All parameters and return types are explicit
```

### 7.5.7 Logging Pattern

**Rule:** Use structured logging with context (tenant_id, request_id, etc.).

**Bad (unstructured logging):**
```python
# BAD (no context)
print(f"Processing request: {request}")
```

**Good (structured logging):**
```python
# GOOD (structured with context)
import logging

logger = logging.getLogger(__name__)

logger.info(
    "Processing RAG query",
    extra={
        "tenant_id": tenant_id,
        "query": query_text,
        "top_k": top_k,
        "component": "rag_system"
    }
)
```

**Example from SDK:**
```python
# src/core/rag/rag_system.py
logger = logging.getLogger(__name__)

async def query_async(self, query_text: str, tenant_id: Optional[str] = None, **kwargs):
    logger.info(
        "RAG query initiated",
        extra={"tenant_id": tenant_id, "query_length": len(query_text)}
    )
    # ...
```

---

## 8) Component-Specific Quality Gates (Mandatory)

Each component in the SDK has specific rules and patterns that must be followed.

### 8.1 Agent Framework Component Rules

**Location:** `src/core/agno_agent_framework/`

#### 8.1.1 Mandatory Rules

1. **Agent State Management:**
   - All agents must track status (`idle`, `running`, `paused`, `stopped`, `error`)
   - State transitions must be thread-safe (use `asyncio.Lock`)

2. **Memory Management:**
   - Agents must support optional memory (episodic, semantic, short-term, long-term)
   - Memory must be tenant-scoped
   - Memory persistence must be optional (in-memory or database-backed)

3. **Tool Execution:**
   - All tools must be registered via `ToolRegistry`
   - Tool execution must be async
   - Tool errors must not crash the agent

4. **Gateway Dependency:**
   - Agents must receive `LiteLLMGateway` via dependency injection
   - All LLM calls must go through the gateway (never direct provider calls)

#### 8.1.2 Code Examples

**Good Agent Implementation:**
```python
# src/core/agno_agent_framework/agent.py
from typing import Optional, Dict, Any
from pydantic import BaseModel
from ..litellm_gateway import LiteLLMGateway
from .exceptions import AgentExecutionError, AgentStateError

class Agent(BaseModel):
    agent_id: str
    tenant_id: Optional[str] = None
    name: str
    gateway: Optional[LiteLLMGateway] = None  # Injected dependency
    status: AgentStatus = AgentStatus.IDLE
    memory: Optional[AgentMemory] = None
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute agent task with proper error handling."""
        if self.status != AgentStatus.IDLE:
            raise AgentStateError(f"Agent {self.agent_id} is not idle")
        
        if not self.gateway:
            raise AgentConfigurationError("Gateway is required")
        
        try:
            self.status = AgentStatus.RUNNING
            # Use gateway for LLM calls
            response = await self.gateway.generate_async(
                prompt=task.prompt,
                model=self.llm_model,
                tenant_id=self.tenant_id,
            )
            # Store in memory if configured
            if self.memory:
                await self.memory.add_episodic(
                    content=response.text,
                    metadata={"task_id": task.task_id}
                )
            return {"result": response.text, "task_id": task.task_id}
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.exception(f"Agent {self.agent_id} execution failed: {e}")
            raise AgentExecutionError(f"Task execution failed: {e}") from e
        finally:
            self.status = AgentStatus.IDLE
```

**Bad Agent Implementation:**
```python
# BAD (violates multiple rules)
class Agent:
    def __init__(self):
        self.gateway = LiteLLMGateway()  # Hard dependency, no injection
        self.status = "idle"  # String, not enum
    
    def execute_task(self, task):  # Not async
        try:
            result = self.gateway.generate(task.prompt)  # Sync call, no tenant_id
            return result
        except:  # Bare except
            return None  # Swallows errors
```

#### 8.1.3 Testing Requirements

**Unit Tests Must Cover:**
- Agent state transitions
- Task execution with success/failure paths
- Memory operations (add, retrieve, clear)
- Tool execution and error handling
- Gateway integration (mocked)

**Example Test:**
```python
# src/tests/unit_tests/test_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.agno_agent_framework import create_agent, AgentStatus

@pytest.mark.asyncio
async def test_agent_execute_task_success():
    """Test successful task execution."""
    gateway = MagicMock()
    gateway.generate_async = AsyncMock(return_value=MagicMock(text="Result"))
    
    agent = create_agent(
        agent_id="test_agent",
        name="Test Agent",
        gateway=gateway,
        tenant_id="tenant_123"
    )
    
    task = AgentTask(task_id="task_1", task_type="test", parameters={"prompt": "Hello"})
    result = await agent.execute_task(task)
    
    assert result["result"] == "Result"
    assert agent.status == AgentStatus.IDLE
    gateway.generate_async.assert_called_once()
```

### 8.2 RAG System Component Rules

**Location:** `src/core/rag/`

#### 8.2.1 Mandatory Rules

1. **Document Processing:**
   - All document ingestion must be async
   - Documents must be chunked with configurable strategy
   - Metadata extraction must be optional but recommended

2. **Vector Operations:**
   - All vector searches must be tenant-scoped
   - Embeddings must be cached (via CacheMechanism)
   - Vector index management must be handled by `VectorIndexManager`

3. **Gateway Integration:**
   - Embedding generation must use gateway
   - Text generation must use gateway
   - All gateway calls must include `tenant_id`

4. **Error Handling:**
   - Document processing errors must not crash the system
   - Invalid queries must return empty results, not exceptions

#### 8.2.2 Code Examples

**Good RAG Implementation:**
```python
# src/core/rag/rag_system.py
from typing import Optional, Dict, Any, List
from ..litellm_gateway import LiteLLMGateway
from ..postgresql_database.connection import DatabaseConnection
from ..cache_mechanism import CacheMechanism

class RAGSystem:
    def __init__(
        self,
        db: DatabaseConnection,
        gateway: LiteLLMGateway,  # Required dependency
        embedding_model: str = "text-embedding-3-small",
        cache: Optional[CacheMechanism] = None,
        **kwargs: Any
    ):
        self.db = db
        self.gateway = gateway
        self.embedding_model = embedding_model
        self.cache = cache or CacheMechanism()
    
    async def query_async(
        self,
        query_text: str,
        top_k: int = 5,
        tenant_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Query RAG system with proper tenant isolation."""
        if not tenant_id:
            raise ValueError("tenant_id is required for multi-tenant operations")
        
        # Check cache first
        cache_key = f"rag_query:{hash(query_text)}"
        cached = self.cache.get(cache_key, tenant_id=tenant_id)
        if cached:
            logger.info("RAG query cache hit", extra={"tenant_id": tenant_id})
            return cached
        
        try:
            # Generate embeddings via gateway
            embeddings = await self.gateway.embed_async(
                query_text,
                model=self.embedding_model,
                tenant_id=tenant_id
            )
            
            # Vector search (tenant-scoped)
            results = await self.vector_ops.search_async(
                embeddings[0],
                top_k=top_k,
                tenant_id=tenant_id
            )
            
            # Generate response via gateway
            context = "\n".join([r["content"] for r in results])
            response = await self.gateway.generate_async(
                prompt=f"Context: {context}\n\nQuestion: {query_text}",
                tenant_id=tenant_id
            )
            
            result = {
                "answer": response.text,
                "sources": results,
                "metadata": {"top_k": top_k, "model": self.embedding_model}
            }
            
            # Cache result
            self.cache.set(cache_key, result, tenant_id=tenant_id, ttl=3600)
            return result
            
        except Exception as e:
            logger.exception(f"RAG query failed for tenant {tenant_id}: {e}")
            return {"answer": "", "sources": [], "error": str(e)}
```

**Bad RAG Implementation:**
```python
# BAD (violates multiple rules)
class RAGSystem:
    def query(self, query):  # Not async, no tenant_id
        # Direct API call (bypasses gateway)
        embeddings = openai.Embedding.create(input=query)
        # No tenant isolation
        results = db.search(embeddings)
        return results  # No error handling
```

#### 8.2.3 Testing Requirements

**Unit Tests Must Cover:**
- Document ingestion (sync and async)
- Query processing with cache hits/misses
- Vector search operations
- Gateway integration (mocked)
- Tenant isolation
- Error handling (invalid queries, gateway failures)

### 8.3 Gateway Component Rules

**Location:** `src/core/litellm_gateway/`

#### 8.3.1 Mandatory Rules

1. **Provider Abstraction:**
   - Never use provider SDKs directly (always via LiteLLM)
   - Support multiple providers (OpenAI, Anthropic, Google, etc.)
   - Provider selection must be configurable

2. **Caching:**
   - Response caching must be enabled by default
   - Cache keys must include tenant_id
   - Cache TTL must be configurable

3. **Rate Limiting:**
   - Rate limiting must be per-tenant
   - Rate limit configuration must be flexible
   - Rate limit errors must be specific exceptions

4. **Circuit Breaker:**
   - Circuit breaker must be enabled for external calls
   - Circuit breaker state must be logged
   - Fallback providers must be supported

5. **LLMOps Tracking:**
   - All LLM calls must be logged for cost tracking
   - Token usage must be recorded
   - Response times must be measured

#### 8.3.2 Code Examples

**Good Gateway Implementation:**
```python
# src/core/litellm_gateway/gateway.py
from typing import Optional, Dict, Any
from ..cache_mechanism import CacheMechanism
from ..utils.circuit_breaker import CircuitBreaker
from .rate_limiter import RateLimiter

class LiteLLMGateway:
    def __init__(
        self,
        api_key: str,
        provider: str = "openai",
        default_model: str = "gpt-4",
        cache: Optional[CacheMechanism] = None,
        enable_rate_limiting: bool = True,
        **kwargs: Any
    ):
        self.api_key = api_key
        self.provider = provider
        self.default_model = default_model
        self.cache = cache or CacheMechanism()
        self.circuit_breaker = CircuitBreaker(name=f"gateway_{provider}")
        self.rate_limiter = RateLimiter() if enable_rate_limiting else None
    
    async def generate_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs: Any
    ) -> GenerateResponse:
        """Generate text with caching, rate limiting, and circuit breaker."""
        if not tenant_id:
            raise ValueError("tenant_id is required")
        
        model = model or self.default_model
        
        # Check cache
        cache_key = f"gateway:{model}:{hash(prompt)}"
        cached = self.cache.get(cache_key, tenant_id=tenant_id)
        if cached:
            return GenerateResponse(**cached)
        
        # Rate limiting
        if self.rate_limiter:
            await self.rate_limiter.acquire(tenant_id=tenant_id)
        
        # Circuit breaker protection
        async def _call_llm():
            from litellm import acompletion
            response = await acompletion(
                model=f"{self.provider}/{model}",
                messages=[{"role": "user", "content": prompt}],
                api_key=self.api_key,
                **kwargs
            )
            return response
        
        try:
            response = await self.circuit_breaker.call(_call_llm)
            
            result = GenerateResponse(
                text=response.choices[0].message.content,
                model=model,
                usage=response.usage.dict() if hasattr(response, 'usage') else None
            )
            
            # Cache result
            self.cache.set(
                cache_key,
                result.dict(),
                tenant_id=tenant_id,
                ttl=3600
            )
            
            # LLMOps tracking
            self._track_llm_operation(tenant_id, model, response.usage)
            
            return result
            
        except Exception as e:
            logger.exception(f"Gateway generation failed for tenant {tenant_id}: {e}")
            raise GatewayError(f"Generation failed: {e}") from e
```

**Bad Gateway Implementation:**
```python
# BAD (violates multiple rules)
import openai

class Gateway:
    def generate(self, prompt):  # Not async, no tenant_id
        # Direct provider call (no abstraction)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content  # No caching, no error handling
```

#### 8.3.3 Testing Requirements

**Unit Tests Must Cover:**
- Provider abstraction (multiple providers)
- Caching (hit/miss scenarios)
- Rate limiting (per-tenant)
- Circuit breaker (open/closed/half-open states)
- LLMOps tracking (token counts, costs)
- Error handling (provider failures, rate limits)

### 8.4 Cache Mechanism Component Rules

**Location:** `src/core/cache_mechanism/`

#### 8.4.1 Mandatory Rules

1. **Backend Abstraction:**
   - Support multiple backends (memory, Dragonfly)
   - Backend selection must be configurable
   - Backend failures must not crash the application

2. **Tenant Isolation:**
   - All cache keys must be tenant-scoped
   - Cache operations must include tenant_id parameter
   - Pattern invalidation must respect tenant boundaries

3. **TTL Management:**
   - TTL must be configurable per operation
   - Default TTL must be set
   - Expired entries must be automatically removed

4. **Memory Backend:**
   - LRU eviction must be implemented
   - Max size must be configurable
   - Memory usage must be monitored

#### 8.4.2 Code Examples

**Good Cache Implementation:**
```python
# src/core/cache_mechanism/cache.py
from typing import Optional, Any
from dataclasses import dataclass

@dataclass
class CacheConfig:
    backend: str = "memory"  # "memory" or "dragonfly"
    default_ttl: int = 300
    max_size: int = 1024
    dragonfly_url: Optional[str] = None
    namespace: str = "sdk_cache"

class CacheMechanism:
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.backend = self.config.backend
        # Initialize backend...
    
    def _namespaced_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """Create tenant-scoped cache key."""
        if tenant_id:
            return f"{self.config.namespace}:{tenant_id}:{key}"
        return f"{self.config.namespace}:{key}"
    
    def set(
        self,
        key: str,
        value: Any,
        tenant_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> None:
        """Set cache value with tenant isolation."""
        if not tenant_id:
            raise ValueError("tenant_id is required for multi-tenant operations")
        
        ttl = ttl or self.config.default_ttl
        namespaced_key = self._namespaced_key(key, tenant_id=tenant_id)
        
        if self.backend == "dragonfly":
            self._dragonfly_client.set(namespaced_key, value, ex=ttl)
        else:
            # Memory backend with LRU
            self._store[namespaced_key] = (value, time.time() + ttl)
            self._store.move_to_end(namespaced_key)
            self._evict_if_needed()
    
    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        """Get cache value with tenant isolation."""
        if not tenant_id:
            raise ValueError("tenant_id is required")
        
        namespaced_key = self._namespaced_key(key, tenant_id=tenant_id)
        # Implementation...
```

#### 8.4.3 Testing Requirements

**Unit Tests Must Cover:**
- Backend abstraction (memory and Dragonfly)
- Tenant isolation (keys don't collide)
- TTL expiration
- LRU eviction (memory backend)
- Pattern invalidation
- Error handling (backend failures)

### 8.5 FaaS Services Component Rules

**Location:** `src/faas/services/`

#### 8.5.1 Mandatory Rules

1. **Stateless Design:**
   - Services must not hold client state between requests
   - All state must be in database or cache
   - Service instances must be interchangeable

2. **HTTP Client:**
   - Inter-service communication must use `ServiceHTTPClient`
   - Retry logic must be implemented
   - Circuit breakers must be used

3. **Request Validation:**
   - All requests must be validated with Pydantic models
   - Tenant ID must be extracted from headers
   - Invalid requests must return 400 errors

4. **Error Handling:**
   - All errors must return proper HTTP status codes
   - Error responses must be JSON
   - Internal errors must not expose implementation details

#### 8.5.2 Code Examples

**Good FaaS Service Implementation:**
```python
# src/faas/services/rag_service/service.py
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from ...shared.http_client import ServiceHTTPClient
from ...shared.database import get_db_connection

app = FastAPI()

class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5

class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    metadata: dict

@app.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID")
) -> RAGQueryResponse:
    """Query RAG service with tenant isolation."""
    try:
        # Get database connection (stateless)
        db = await get_db_connection()
        
        # Create RAG system (stateless)
        rag = create_rag_system(db=db, gateway=gateway_client, tenant_id=x_tenant_id)
        
        # Execute query
        result = await rag.query_async(
            query_text=request.query,
            top_k=request.top_k,
            tenant_id=x_tenant_id
        )
        
        return RAGQueryResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"RAG query failed for tenant {x_tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

**Bad FaaS Service Implementation:**
```python
# BAD (stateful, no validation)
app = FastAPI()
rag_systems = {}  # State in memory (violates stateless)

@app.post("/query")
async def query_rag(query: str):  # No validation, no tenant_id
    # Stateful (stores in memory)
    if "tenant_123" not in rag_systems:
        rag_systems["tenant_123"] = create_rag_system(...)
    
    return rag_systems["tenant_123"].query(query)  # No error handling
```

#### 8.5.3 Testing Requirements

**Unit Tests Must Cover:**
- Request validation (Pydantic models)
- Tenant ID extraction from headers
- Stateless behavior (multiple requests)
- Error handling (400, 500 responses)
- Service-to-service communication (mocked)

### 8.6 Machine Learning Component Rules

**Location:** `src/core/machine_learning/`

#### 8.6.1 Mandatory Rules

1. **Model Management:**
   - Models must be versioned
   - Model metadata must be stored in database
   - Model loading must be lazy (on-demand)

2. **Training:**
   - Training must be async
   - Training progress must be trackable
   - Training data must be tenant-scoped

3. **Inference:**
   - Inference must be async
   - Batch inference must be supported
   - Inference results must be cached

4. **MLOps Integration:**
   - Model metrics must be logged
   - Model performance must be monitored
   - Model versioning must be tracked

#### 8.6.2 Code Examples

**Good ML Component Implementation:**
```python
# src/core/machine_learning/ml_framework/model.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class MLModel(BaseModel):
    model_id: str
    tenant_id: Optional[str] = None
    version: str
    model_type: str
    model_path: Optional[str] = None
    
    async def train_async(
        self,
        training_data: List[Dict[str, Any]],
        tenant_id: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Train model asynchronously with tenant isolation."""
        if not tenant_id:
            raise ValueError("tenant_id is required")
        
        # Filter training data by tenant
        tenant_data = [d for d in training_data if d.get("tenant_id") == tenant_id]
        
        # Training logic...
        metrics = await self._train_model(tenant_data, **kwargs)
        
        # Store model metadata
        await self._save_model_metadata(tenant_id, metrics)
        
        return metrics
    
    async def predict_async(
        self,
        input_data: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Predict with tenant-scoped model."""
        if not tenant_id:
            raise ValueError("tenant_id is required")
        
        # Load model if needed (lazy loading)
        if not self._model_loaded:
            await self._load_model(tenant_id)
        
        # Prediction logic...
        result = await self._run_inference(input_data)
        
        return result
```

#### 8.6.3 Testing Requirements

**Unit Tests Must Cover:**
- Model training (async)
- Model inference (async, batch)
- Model versioning
- Tenant isolation
- MLOps tracking
- Error handling

### 8.7 Component Gate Checklist (Required Per Component Touched)

A "component" is any top-level functional module under `src/` (e.g., `src/core/agno_agent_framework`, `src/core/rag`, `src/core/litellm_gateway`, `src/faas/services/agent_service`).

For every component modified, PR must include:
- [ ] **Unit tests** for new/changed logic (≥80% coverage)
- [ ] **Integration tests** if component touches external dependency (database, HTTP, LLM)
- [ ] **Component-specific rules** followed (see sections 8.1-8.6)
- [ ] **Tenant isolation** implemented (if applicable)
- [ ] **Async methods** used for I/O operations
- [ ] **Dependency injection** used (no hard dependencies)
- [ ] **Error handling** with custom exceptions
- [ ] **Type hints** complete for all public APIs
- [ ] **Logging** with structured context (tenant_id, request_id)
- [ ] Updated **component docs** (README.md) when behavior changes
- [ ] **API contract** stability (or migration notes if breaking)
- [ ] **Observability** expectations met (logs/metrics)

### 8.8 Component Documentation Template

Every component must have a `README.md` file with the following structure:

```markdown
# Component: <Component Name> — Motadata Python AI SDK

## Purpose
Clear description of what this component does and when to use it.

## Architecture
- How it fits into the SDK
- Dependencies (what it needs)
- Dependents (what uses it)

## Public API
### Factory Functions
- `create_<component>()` - Main factory function
- Parameters and return types

### Classes
- Main classes with key methods
- Method signatures with type hints

## Configuration
- Environment variables
- Configuration options
- Default values

## Usage Examples
### Basic Usage
```python
# Copy-paste runnable example
```

### Advanced Usage
```python
# Advanced configuration example
```

## Multi-Tenancy
- How tenant isolation works
- Required parameters
- Tenant-scoped operations

## Error Handling
- What exceptions are raised
- When they occur
- How to handle them

## Performance Considerations
- Caching behavior
- Cost implications
- Best practices

## Testing
- Unit tests: `src/tests/unit_tests/test_<component>.py`
- Integration tests: `src/tests/integration_tests/test_<component>.py`

## Related Components
- Links to related components
- Integration patterns
```

### 8.9 Component-Specific Testing Examples

See sections 8.1.3, 8.2.3, 8.3.3, 8.4.3, 8.5.3, and 8.6.3 for component-specific testing requirements and examples.

---

## 9) CI + Sonar enforcement templates (drop-in)

> Your repo currently has **no CI config** and **no Sonar config**. Use the following templates.

### 9.1 `sonar-project.properties` template (root)
```properties
sonar.projectKey=motadata_python_sdk
sonar.projectName=Motadata Python SDK
sonar.sources=src
sonar.tests=src/tests
sonar.python.version=3.8

# Coverage
sonar.python.coverage.reportPaths=coverage.xml

# Optional
sonar.exclusions=**/__pycache__/**,**/*.pyc
sonar.test.inclusions=src/tests/**

# If you generate junit report:
# sonar.python.xunit.reportPath=test-results.xml
```

### 9.2 GitHub Actions CI template (merge-blocking)
Create: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [ main ]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          pip install ruff bandit pip-audit detect-secrets radon

      - name: Format check
        run: |
          ruff format --check .

      - name: Lint
        run: |
          ruff check .

      - name: Type check
        run: |
          python -m mypy src

      - name: Tests + Coverage Gate
        run: |
          pytest -q src/tests --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=80

      - name: Security - secrets
        run: |
          detect-secrets scan --baseline .secrets.baseline

      - name: Security - SAST
        run: |
          bandit -r src -q

      - name: Security - dependency audit
        run: |
          pip-audit

      - name: Complexity gate
        run: |
          radon cc -s -n B src

      - name: Build package
        run: |
          python -m build

      # Sonar scan step depends on your Sonar setup
      # - name: Sonar Scan
      #   uses: SonarSource/sonarqube-scan-action@v2
      #   env:
      #     SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
      #     SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}
```

### 9.3 GitLab CI template (if you use GitLab)
Create: `.gitlab-ci.yml`
```yaml
stages: [quality]

quality_gate:
  stage: quality
  image: python:3.11
  script:
    - pip install -e ".[dev]"
    - pip install ruff bandit pip-audit detect-secrets radon build
    - ruff format --check .
    - ruff check .
    - python -m mypy src
    - pytest -q src/tests --cov=src --cov-report=xml --cov-fail-under=80
    - detect-secrets scan --baseline .secrets.baseline
    - bandit -r src -q
    - pip-audit
    - radon cc -s -n B src
    - python -m build
  only:
    - merge_requests
```

---

## 10) Mandatory checkpoints (single-page summary)

### 10.1 Developer must run before PR
```bash
make format
ruff check .
python -m mypy src
pytest -q src/tests --cov=src --cov-report=xml --cov-fail-under=80
bandit -r src -q
pip-audit
detect-secrets scan --baseline .secrets.baseline
radon cc -s -n B src
python -m build
```

### 10.2 CI must enforce (merge-blocking)
- Format check
- Ruff lint
- Mypy
- Tests + coverage fail-under 80
- Secret scan
- Bandit
- Pip-audit
- Complexity gate
- Build + smoke import (optional but recommended)
- Sonar Quality Gate pass

---

## 11) Action plan to fully align the repo (what to change now)

**P0 (must-do to be “Quality Gate compliant”)**
1. Add **CI pipeline** (GitHub/GitLab).
2. Add **Sonar properties + scanner** integration.
3. Enforce **coverage threshold** (`--cov-fail-under=80`) in CI and Makefile.
4. Replace placeholder `lint` target with **ruff**.
5. Add **security scanners** (`detect-secrets`, `bandit`, `pip-audit`).
6. Add **complexity gate** (Sonar + radon).

**P1 (next hardening)**
- Multi-Python version matrix (3.8–3.12)
- Pre-commit hooks
- Packaging smoke test in clean venv/container
- Changelog and semantic versioning policy

---

*End of document.*
