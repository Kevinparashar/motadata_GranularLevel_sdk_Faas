# Motadata Libraries

## Comprehensive Library List

This document provides a comprehensive list of all libraries used in the SDK, their versions, and purposes.

## Core Libraries

### LLM and AI

| Library | Version | Purpose |
|---------|---------|---------|
| `litellm` | >=1.0.0 | Unified LLM interface for multiple providers |
| `openai` | >=1.0.0 | OpenAI API client (via litellm) |
| `anthropic` | >=0.18.0 | Anthropic API client (via litellm) |

### Data Validation and Configuration

| Library | Version | Purpose |
|---------|---------|---------|
| `pydantic` | >=2.0.0 | Data validation and settings management |
| `python-dotenv` | >=1.0.0 | Environment variable management |
| `pyyaml` | >=6.0 | YAML configuration file parsing |

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
| `redis` | >=5.0.0 | Redis client for distributed caching |
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
pip install redis cachetools

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
- **redis**: Distributed caching layer (optional, in-memory fallback)
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
- **Gateway Cache**: Automatic response caching using cachetools/redis
- **Memory Integration**: Agent Memory for conversation context (built-in)
- **Unified Query**: Single endpoint for Agent/RAG orchestration (FastAPI)
- **FaaS Architecture**: Services-based architecture with FastAPI, Starlette middleware, and integration placeholders

## Swappable Libraries

The SDK is designed to allow swapping of certain libraries:

### Agent Frameworks
- **agno** ↔ **langchain**: Agent framework swapping

### Caching Backends
- **redis** ↔ **memory** ↔ **database**: Cache backend swapping

### HTTP Clients
- **httpx** ↔ **aiohttp** ↔ **requests**: HTTP client swapping

### FaaS Deployment
- **mangum**: AWS Lambda deployment (optional, only for Lambda)
- **uvicorn**: Local/container deployment (default)

## License Compatibility

All libraries are compatible with the SDK's MIT license. Check individual library licenses for specific requirements.

