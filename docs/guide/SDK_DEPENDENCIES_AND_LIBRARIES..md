# MOTADATA - SDK DEPENDENCIES AND LIBRARIES

**Comprehensive list of all libraries used in the SDK, their versions, purposes, and upgrade guidance.**

---

## 📖 How to Read This Document

### Dependency Types

| Type | Meaning | Example |
|------|---------|---------|
| **Direct** | SDK directly imports and uses | `litellm`, `pydantic` |
| **Transitive** | Required by direct dependencies | `certifi` (via `httpx`) |
| **Optional** | Needed only for specific features | `dragonfly` (caching backend) |

### Upgrade Risk Levels

| Risk | Meaning | Action |
|------|---------|--------|
| 🟢 **Low** | Patch updates safe, minor updates usually safe | Update freely |
| 🟡 **Medium** | Minor updates may need testing | Test before production |
| 🔴 **High** | Breaking changes likely | Read changelog, test thoroughly |

### Version Notation

- `>=1.0.0` - Minimum version required
- `^2.0.0` - Compatible with 2.x.x (SemVer)
- `~1.5.0` - Compatible with 1.5.x only

---

## Core Libraries

### LLM and AI

| Library | Version | Type | Purpose | Why We Need It | Upgrade Risk |
|---------|---------|------|---------|----------------|--------------|
| `litellm` | >=1.0.0 | **Direct** | Unified LLM interface for multiple providers | Core abstraction for all LLM operations; enables provider switching | 🟡 **Medium** - API changes affect all components |
| `openai` | >=1.0.0 | **Transitive** | OpenAI API client (via litellm) | Accessed through litellm; enables OpenAI provider | 🟢 **Low** - Managed by litellm |
| `anthropic` | >=0.18.0 | **Transitive** | Anthropic API client (via litellm) | Accessed through litellm; enables Anthropic/Claude provider | 🟢 **Low** - Managed by litellm |

### Data Validation and Configuration

| Library | Version | Type | Purpose | Why We Need It | Upgrade Risk |
|---------|---------|------|---------|----------------|--------------|
| `pydantic` | >=2.0.0 | **Direct** | Data validation and settings management | Core data modeling; ensures type safety across SDK | 🔴 **High** - v1 to v2 migration required careful testing |
| `python-dotenv` | >=1.0.0 | **Direct** | Environment variable management | Loads `.env` files; simplifies configuration | 🟢 **Low** - Stable API |
| `pyyaml` | >=6.0 | **Direct** | YAML configuration file parsing | Config file support; optional feature | 🟢 **Low** - Stable API |

### Database

| Library | Version | Purpose |
|---------|---------|---------|
| `psycopg2-binary` | >=2.9.9 | PostgreSQL adapter for Python |
| `sqlalchemy` | >=2.0.0 | SQL toolkit and ORM (optional) |
| `alembic` | >=1.12.0 | Database migration tool (optional) |

### HTTP and Networking

| Library | Version | Purpose |
|---------|---------|---------|
| `httpx` | >=0.24.0 | Modern HTTP client with async support |
| `aiohttp` | >=3.8.0 | Async HTTP client/server framework |
| `requests` | >=2.31.0 | HTTP library (legacy support) |

### Caching

| Library | Version | Purpose |
|---------|---------|---------|
| `dragonfly` | >=5.0.0 | Dragonfly client for distributed caching |
| `cachetools` | >=5.3.0 | In-memory caching utilities |
| `diskcache` | >=5.6.0 | Disk-based caching |

### Async and Concurrency

| Library | Version | Purpose |
|---------|---------|---------|
| `asyncio` | Built-in | Async I/O support |
| `aiofiles` | >=23.0.0 | Async file operations |

### Observability and Logging

| Library | Version | Purpose |
|---------|---------|---------|
| `opentelemetry-api` | >=1.20.0 | Distributed tracing API |
| `opentelemetry-sdk` | >=1.20.0 | Tracing SDK implementation |
| `structlog` | >=23.0.0 | Structured logging |
| `prometheus-client` | >=0.18.0 | Metrics collection |

### Testing

| Library | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=7.0.0 | Testing framework |
| `pytest-asyncio` | >=0.21.0 | Async test support |
| `pytest-mock` | >=3.10.0 | Mocking utilities |
| `pytest-cov` | >=4.0.0 | Coverage reporting |

### API Framework

| Library | Version | Purpose |
|---------|---------|---------|
| `fastapi` | >=0.100.0 | Modern web framework for APIs |
| `starlette` | >=0.27.0 | ASGI framework (FastAPI dependency, used for middleware) |
| `uvicorn` | >=0.23.0 | ASGI server |
| `pydantic` | >=2.0.0 | Request/response validation |
| `mangum` | >=0.17.0 | AWS Lambda adapter for ASGI applications (optional, for Lambda deployment) |

### Utilities

| Library | Version | Purpose |
|---------|---------|---------|
| `numpy` | >=1.24.0 | Numerical operations for vectors |
| `python-dateutil` | >=2.8.2 | Date/time utilities |
| `typing-extensions` | >=4.5.0 | Extended type hints |

## FaaS-Specific Libraries

### Service Integration

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| `nats-py` | >=2.0.0 | NATS message bus client | ⏳ Planned (placeholder ready) |
| `msgpack` | >=1.0.0 | MessagePack serialization | ⏳ Planned (placeholder ready) |
| `protobuf` | >=4.0.0 | Protocol Buffers serialization | ⏳ Planned (placeholder ready) |

**Note**: FaaS services currently use JSON for serialization. NATS, MessagePack, and Protobuf integrations are placeholders ready for implementation.

## Component-Specific Libraries

### Agent Framework

| Library | Version | Purpose |
|---------|---------|---------|
| `agno` | Latest | Agent framework (swappable) |
| `langchain` | >=0.1.0 | Alternative agent framework |

### Vector Operations

| Library | Version | Purpose |
|---------|---------|---------|
| `pgvector` | Extension | PostgreSQL vector extension |
| `numpy` | >=1.24.0 | Vector operations |

### Document Processing

| Library | Version | Purpose |
|---------|---------|---------|
| `nltk` | >=3.8.0 | Natural language processing |
| `pdfplumber` | >=0.9.0 | PDF parsing (optional) |
| `PyPDF2` | >=3.0.0 | PDF processing (optional) |
| `html.parser` | Built-in | HTML text extraction |
| `json` | Built-in | JSON parsing and conversion |
| `unicodedata` | Built-in | Unicode normalization |
| `re` | Built-in | Regular expressions for text processing |

## Development Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `black` | >=23.0.0 | Code formatting |
| `isort` | >=5.12.0 | Import sorting |
| `mypy` | >=1.0.0 | Type checking |
| `ruff` | >=0.1.0 | Fast linter |

## Version Management

### Minimum Versions

All libraries specify minimum versions to ensure compatibility:
- Python 3.8+ required
- Most libraries support Python 3.8-3.12

### Version Pinning

For production deployments, consider pinning exact versions:
```txt
litellm==1.0.0
pydantic==2.0.0
psycopg2-binary==2.9.9
```

## Installation

### Complete Installation

```bash
pip install -r requirements.txt
```

### Component-Specific Installation

```bash
# Core dependencies only
pip install litellm pydantic httpx

# With database support
pip install psycopg2-binary sqlalchemy

# With caching
pip install dragonfly cachetools

# With observability
pip install opentelemetry-api opentelemetry-sdk structlog

# For AWS Lambda deployment
pip install mangum

# For FaaS integrations (when implemented)
pip install nats-py msgpack protobuf
```

## Library Purposes Summary

### Core Functionality
- **litellm**: Primary LLM interface with multi-provider support
- **pydantic**: Data validation and settings management
- **httpx**: HTTP operations with async support

### Data Storage
- **psycopg2-binary**: PostgreSQL database connectivity
- **dragonfly**: Distributed caching layer (optional, in-memory fallback)
- **cachetools**: In-memory caching utilities

### Development
- **pytest**: Testing framework
- **black/isort**: Code quality and PEP 8 compliance
- **mypy**: Type checking
- **ruff**: Fast linter

### Observability
- **opentelemetry**: Distributed tracing
- **structlog**: Structured logging
- **prometheus-client**: Metrics collection

### Recent Enhancements
- **Gateway Cache**: Automatic response caching using cachetools/dragonfly
- **Memory Integration**: Agent Memory for conversation context (built-in)
- **Unified Query**: Single endpoint for Agent/RAG orchestration (FastAPI)
- **FaaS Architecture**: Services-based architecture with FastAPI, Starlette middleware, and integration placeholders

## Swappable Libraries

The SDK is designed to allow swapping of certain libraries:

### Agent Frameworks
- **agno** ↔ **langchain**: Agent framework swapping

### Caching Backends
- **dragonfly** ↔ **memory** ↔ **database**: Cache backend swapping

### HTTP Clients
- **httpx** ↔ **aiohttp** ↔ **requests**: HTTP client swapping

### FaaS Deployment
- **mangum**: AWS Lambda deployment (optional, only for Lambda)
- **uvicorn**: Local/container deployment (default)

---

## Dependency Management Best Practices

### Understanding Transitive Dependencies

**What are transitive dependencies?**
- Dependencies required by your direct dependencies
- Example: `litellm` requires `openai`, so `openai` is a transitive dependency

**Why care about transitive dependencies?**
- Security vulnerabilities can exist in transitive deps
- Version conflicts can occur between transitive deps
- Upgrade one direct dep can force upgrades of many transitive deps

**View your transitive dependencies:**
```bash
# List all dependencies (direct + transitive)
pip list

# See dependency tree
pip install pipdeptree
pipdeptree

# Check for vulnerabilities
pip-audit
```

### Upgrade Strategy by Risk Level

#### 🟢 Low Risk Libraries (Update Freely)

**Examples:** `python-dotenv`, `cachetools`, `pyyaml`

**Strategy:**
1. Update to latest: `pip install --upgrade {library}`
2. Run tests: `pytest`
3. Deploy if tests pass

**Frequency:** Monthly or quarterly

#### 🟡 Medium Risk Libraries (Test Before Production)

**Examples:** `litellm`, `fastapi`, `httpx`

**Strategy:**
1. Check changelog for breaking changes
2. Update in development: `pip install --upgrade {library}`
3. Run full test suite: `pytest src/tests/`
4. Test in staging environment
5. Deploy to production after validation

**Frequency:** Quarterly or when security fixes released

#### 🔴 High Risk Libraries (Careful Migration Required)

**Examples:** `pydantic` (v1→v2), `sqlalchemy` (v1→v2)

**Strategy:**
1. Read migration guide thoroughly
2. Create dedicated branch for upgrade
3. Update code to new API patterns
4. Run comprehensive tests
5. Performance test in staging
6. Plan rollback strategy
7. Deploy with monitoring

**Frequency:** Only when necessary (major features/security)

### Common Upgrade Scenarios

#### Scenario 1: Security Vulnerability in Direct Dependency

```bash
# Example: Critical vulnerability in httpx
pip install --upgrade httpx==0.24.1  # Specific safe version
pytest src/tests/  # Run tests
pip-audit  # Verify fix
```

**Checklist:**
- [ ] Check if vulnerability affects SDK usage
- [ ] Update to patched version
- [ ] Run full test suite
- [ ] Deploy as hotfix if critical

#### Scenario 2: Security Vulnerability in Transitive Dependency

```bash
# Example: Vulnerability in certifi (via httpx)
pip install --upgrade certifi  # Update transitive dep
pip check  # Verify no conflicts
pytest  # Run tests
```

**Checklist:**
- [ ] Identify which direct dep pulls it in
- [ ] Check if updating direct dep fixes it
- [ ] Otherwise, constrain transitive dep version
- [ ] Add note in requirements.txt

#### Scenario 3: Major Version Upgrade (Breaking Changes)

```bash
# Example: Upgrading pydantic 1.x → 2.x
pip install pydantic>=2.0.0  # Upgrade
# Fix breaking changes in code
pytest src/tests/  # Will likely fail
# Iterate until all tests pass
```

**Checklist:**
- [ ] Read migration guide
- [ ] Create feature branch
- [ ] Update code incrementally
- [ ] Add compatibility shims if needed
- [ ] Update documentation
- [ ] Test thoroughly in staging

### Version Pinning Strategies

#### Development (Flexible)
```txt
# requirements.txt
litellm>=1.0.0
pydantic>=2.0.0
```
**Pros:** Get latest features and fixes
**Cons:** May break unexpectedly

#### Production (Strict)
```txt
# requirements-prod.txt
litellm==1.0.5
pydantic==2.0.3
```
**Pros:** Reproducible builds
**Cons:** Miss security fixes

#### Recommended (Balanced)
```txt
# requirements.txt
litellm>=1.0.0,<2.0.0  # Allow minor updates, block majors
pydantic>=2.0.0,<3.0.0
```
**Pros:** Security fixes + stability
**Cons:** Requires periodic testing

### Monitoring Dependency Health

**Tools to use:**

1. **Security Scanning**
   ```bash
   pip-audit  # Check for known vulnerabilities
   safety check  # Alternative security scanner
   ```

2. **Dependency Updates**
   ```bash
   pip list --outdated  # See what's available
   pip-review --auto  # Interactive updater
   ```

3. **Compatibility Checking**
   ```bash
   pip check  # Verify dependency compatibility
   pipdeptree  # Visualize dependency tree
   ```

**Frequency:**
- 🔴 **Security scans:** Weekly (automated in CI)
- 🟡 **Dependency updates:** Monthly review
- 🟢 **Major upgrades:** Quarterly planning

### Direct vs Transitive Dependency Summary

**All SDK Dependencies (Categorized):**

#### Direct Dependencies (SDK imports directly)
```
Core:
- litellm, pydantic, httpx, psycopg2-binary
- fastapi, uvicorn, asyncio, aiofiles

Optional:
- dragonfly, opentelemetry-api, structlog
```

#### Transitive Dependencies (Required by direct deps)
```
Via litellm:
- openai, anthropic, google-generativeai

Via httpx:
- certifi, httpcore, h11, sniffio

Via pydantic:
- typing-extensions, annotated-types

Via fastapi:
- starlette, anyio
```

**To see your current dependency tree:**
```bash
pip install pipdeptree
pipdeptree -p litellm  # Show litellm's dependencies
pipdeptree --reverse  # Show what depends on what
```

---

## License Compatibility

All libraries are compatible with the SDK's MIT license. Check individual library licenses for specific requirements.

**License Summary:**
- **MIT:** Most dependencies (litellm, pydantic, httpx, etc.)
- **Apache 2.0:** OpenTelemetry libraries
- **BSD:** PostgreSQL-related libraries
- **PSF:** Python standard library modules

**For production use:** Run `pip-licenses` to generate complete license report.

---

**Last Updated:** 2026-02-02
**Next Review:** 2026-05-02

