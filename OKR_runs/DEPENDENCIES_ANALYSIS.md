# Dependencies Analysis for SDK Components

## For Showcase Scripts (Minimal Requirements)

### ✅ REQUIRED
1. **OPENAI_API_KEY** - Environment variable
   - Needed for: Gateway, Agent Framework
   - Set: `export OPENAI_API_KEY='your-key'`

2. **Python Dependencies** - From `requirements.txt`
   - Install: `pip install -r requirements.txt`
   - Includes: litellm, fastapi, pydantic, opentelemetry-api, etc.

3. **Virtual Environment** - Python venv
   - Create: `python3 -m venv venv`
   - Activate: `source venv/bin/activate`

### ✅ That's It for Showcases!
The showcase scripts are designed to work with **minimal dependencies**. They:
- Use in-memory cache (no Redis/Dragonfly needed)
- Verify components exist (RAG/Vector/ML don't need database)
- Use OTEL in no-op mode (no endpoint needed)
- Don't require NATS, PostgreSQL, or other external services

---

## For Full Production Use (Additional Requirements)

### 🔴 REQUIRED for Full Functionality

#### 1. PostgreSQL Database with pgvector Extension
**Required for:**
- RAG System (document storage, embeddings, retrieval)
- Vector Operations (similarity search)
- Vector Index Manager (index creation)
- Machine Learning Framework (model storage, training data)
- All DALs (Data Access Layers) for persistence

**Setup:**
```bash
# Install PostgreSQL
# Install pgvector extension
psql -U postgres -d your_database -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Environment Variables:**
```bash
# Option 1: Connection string
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Option 2: Individual variables
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=motadata_sdk
POSTGRES_USER=your-username
POSTGRES_PASSWORD=your-password
```

#### 2. Database Tables/Schema
**Required for:**
- All DAL operations (embeddings, documents, operations, context, etc.)
- Vector operations (embeddings table with vector column)
- Index management

**Note:** Tables should be created via migrations or DAL initialization.

---

### 🟡 OPTIONAL (But Recommended for Production)

#### 1. Dragonfly/Redis (Cache Backend)
**Optional for:**
- Cache Mechanism (alternative to in-memory)
- Better performance for production
- Distributed caching across instances

**Setup:**
```bash
# Install Dragonfly or Redis
# Default: Uses in-memory cache if not provided
```

**Environment Variables:**
```bash
DRAGONFLY_URL=redis://localhost:6379/0
# OR
DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379
DRAGONFLY_PASSWORD=your-password
```

#### 2. NATS (Message Bus)
**Optional for:**
- Asynchronous messaging between services
- Event publishing
- Service-to-service communication

**Environment Variables:**
```bash
NATS_URL=nats://localhost:4222
```

#### 3. OTEL Collector (Observability)
**Optional for:**
- Distributed tracing
- Metrics collection
- Observability dashboards

**Environment Variables:**
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

**Note:** Works in no-op mode if not configured (tracing still works, just not exported).

---

## Component-by-Component Requirements

### Components That Work WITHOUT External Services

✅ **Cache Mechanism**
- Works with: In-memory backend (default)
- Optional: Dragonfly/Redis for production

✅ **Codec Integration**
- Works with: No external services needed
- Pure Python serialization/deserialization

✅ **OTEL Integration**
- Works with: No-op mode (no endpoint needed)
- Optional: OTEL collector for exporting traces

✅ **Prompt Context Management**
- Works with: In-memory storage (default)
- Optional: Database DAL for persistence

✅ **LLMOps**
- Works with: In-memory logging (default)
- Optional: Database DAL for persistence

### Components That Need External Services

🔴 **RAG System** (Full Functionality)
- Requires: PostgreSQL with pgvector
- Requires: Database connection
- Optional: Cache, OTEL, NATS

🔴 **Vector Operations** (Full Functionality)
- Requires: PostgreSQL with pgvector
- Requires: Database connection
- Optional: Cache

🔴 **Vector Index Manager** (Full Functionality)
- Requires: PostgreSQL with pgvector
- Requires: Database connection

🔴 **Machine Learning Framework** (Full Functionality)
- Requires: PostgreSQL (for model storage)
- Requires: Database connection
- Optional: Storage for model artifacts

🔴 **All DALs** (Persistence)
- Requires: PostgreSQL database
- Requires: Database connection
- Requires: Tables created (via migrations)

### Components That Need API Key

🔴 **LiteLLM Gateway**
- Requires: OPENAI_API_KEY (or ANTHROPIC_API_KEY, GOOGLE_API_KEY)
- Optional: Cache, OTEL, Database

🔴 **Agent Framework**
- Requires: Gateway (which needs API key)
- Optional: Database, Cache, OTEL

---

## Summary Table

| Component | API Key | requirements.txt | venv | PostgreSQL | Redis/Dragonfly | NATS | OTEL |
|-----------|---------|------------------|------|------------|-----------------|------|------|
| **Showcase Scripts** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Gateway** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Cache (in-memory)** | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Codec** | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **OTEL (no-op)** | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Prompt Context** | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **LLMOps (in-memory)** | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **RAG (full)** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Vector Ops (full)** | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **ML Framework (full)** | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Production (all)** | ✅ | ✅ | ✅ | ✅ | 🟡 | 🟡 | 🟡 |

**Legend:**
- ✅ = Required
- ❌ = Not needed
- 🟡 = Optional but recommended

---

## Quick Reference

### For Showcase Scripts Only:
```bash
# 1. Set API key
export OPENAI_API_KEY='your-key'

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run showcases
./run_showcase.sh
```

### For Full Production:
```bash
# 1. Set API key
export OPENAI_API_KEY='your-key'

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up PostgreSQL with pgvector
# (See PostgreSQL setup instructions)

# 4. Set database URL
export DATABASE_URL='postgresql://user:pass@localhost:5432/dbname'

# 5. (Optional) Set up Redis/Dragonfly
export DRAGONFLY_URL='redis://localhost:6379/0'

# 6. (Optional) Set up NATS
export NATS_URL='nats://localhost:4222'

# 7. (Optional) Set up OTEL
export OTEL_EXPORTER_OTLP_ENDPOINT='http://localhost:4317'
```

---

## Answer to Your Question

**For the showcase scripts specifically:**
- ✅ **NO additional dependencies needed** beyond:
  1. OPENAI_API_KEY
  2. requirements.txt (Python packages)
  3. venv (virtual environment)

**For full production use:**
- ✅ **PostgreSQL with pgvector** is required for:
  - RAG System full functionality
  - Vector Operations full functionality
  - ML Framework full functionality
  - All DAL persistence

- 🟡 **Optional but recommended:**
  - Dragonfly/Redis (for production caching)
  - NATS (for async messaging)
  - OTEL Collector (for observability)

