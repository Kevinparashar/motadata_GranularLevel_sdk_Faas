# MOTADATA - QUICK REFERENCE GUIDE

**Fast lookup for common tasks, APIs, imports, and code snippets.**

---

## 🚀 Quick Start

```python
# 1. Install
pip install -r requirements.txt

# 2. Set API key
export OPENAI_API_KEY='your-key'

# 3. Create gateway
from src.core.litellm_gateway import create_gateway
gateway = create_gateway(api_keys={"openai": "sk-..."})

# 4. Create agent
from src.core.agno_agent_framework import create_agent
agent = create_agent("agent1", "My Agent", gateway)
```

---

## 📦 Common Imports

```python
# Gateway
from src.core.litellm_gateway import create_gateway, LiteLLMGateway

# Agents
from src.core.agno_agent_framework import (
    create_agent,
    create_agent_with_memory,
    create_agent_from_prompt,
    execute_task
)

# Prompt-Based Generation
from src.core.prompt_based_generator import (
    create_agent_from_prompt,
    create_tool_from_prompt
)

# Data Ingestion
from src.core.data_ingestion import (
    upload_and_process,
    upload_and_process_async,
    create_ingestion_service
)

# RAG
from src.core.rag import create_rag_system

# Utilities
from src.core.utils import (
    print_config_options,
    discover_config,
    create_error_with_suggestion
)
```

---

## 🤖 Agent Operations

### Create Agent
```python
# Basic agent
agent = create_agent("agent1", "My Agent", gateway)

# With memory
agent = create_agent_with_memory(
    "agent1", "My Agent", gateway,
    memory_config={"persistence_path": "/tmp/memory.json"}
)

# From prompt
agent = await create_agent_from_prompt(
    "Create a customer support agent",
    gateway=gateway
)
```

### Execute Task
```python
result = await execute_task(
    agent,
    task_type="analyze",
    parameters={"text": "Analyze this document"}
)
```

### Chat with Agent
```python
from src.core.agno_agent_framework import chat_with_agent

response = await chat_with_agent(
    agent,
    message="Hello, how can you help?",
    tenant_id="tenant_123"
)
```

---

## 🔧 Configuration

### Discover Options
```python
from src.core.utils import print_config_options

# Print all options for a component
print_config_options('agent')
print_config_options('gateway')
print_config_options('rag')
```

### Validate Configuration
```python
from src.core.utils import discover_config

result = discover_config('gateway', {
    'api_key': 'sk-...',
    'default_model': 'gpt-4'
})
```

### Configuration Builders
```python
from src.core.utils import create_agent_config

config = (create_agent_config()
    .with_name("My Agent")
    .with_description("Agent description")
    .with_capability("customer_support")
    .with_tool("tool_123")
    .build())
```

---

## 🔌 Gateway Operations

### Create Gateway
```python
gateway = create_gateway(
    providers=['openai'],
    default_model='gpt-4',
    api_keys={'openai': 'sk-...'}
)
```

### Generate Text
```python
response = gateway.generate(
    prompt="Explain quantum computing",
    model="gpt-4"
)
print(response.text)
```

### Async Generation
```python
response = await gateway.generate_async(
    prompt="Explain quantum computing",
    model="gpt-4"
)
```

---

## 📚 RAG Operations

### Create RAG System
```python
from src.core.rag import create_rag_system

rag = create_rag_system(
    db=db,
    gateway=gateway,
    tenant_id="tenant_123"
)
```

### Add Documents
```python
await rag.add_document(
    content="Document content here",
    metadata={"title": "My Document"}
)
```

### Query
```python
result = await rag.query(
    query="What is this about?",
    top_k=5
)
print(result["answer"])
```

---

## 🛠️ Prompt-Based Generation

### Create Agent from Prompt
```python
from src.core.prompt_based_generator import create_agent_from_prompt

agent = await create_agent_from_prompt(
    prompt="Create a customer support agent that categorizes tickets",
    gateway=gateway,
    tenant_id="tenant_123"
)
```

### Create Tool from Prompt
```python
from src.core.prompt_based_generator import create_tool_from_prompt

tool = await create_tool_from_prompt(
    prompt="Create a tool that calculates priority based on urgency and impact",
    gateway=gateway,
    tenant_id="tenant_123"
)
```

---

## ⚠️ Error Handling

### Catch Specific Errors
```python
from src.core.agno_agent_framework.exceptions import AgentExecutionError
from src.core.rag.exceptions import RetrievalError

try:
    result = await agent.execute_task(task)
except AgentExecutionError as e:
    print(f"Agent error: {e.message}")
    print(f"Suggestion: {e.suggestion}")  # If available
except RetrievalError as e:
    print(f"Retrieval error: {e.message}")
```

### Catch All SDK Errors
```python
from src.core.exceptions import SDKError

try:
    # Any SDK operation
    result = await agent.execute_task(task)
except SDKError as e:
    print(f"SDK error: {e.message}")
```

---

## 🔍 Configuration Discovery

### Get Config Options
```python
from src.core.utils import (
    get_agent_config_options,
    get_gateway_config_options,
    get_rag_config_options
)

# Get all options
agent_options = get_agent_config_options()
gateway_options = get_gateway_config_options()
rag_options = get_rag_config_options()

# Access required/optional options
required = agent_options['required']
optional = agent_options['optional']
example = agent_options['example']
```

---

## 📊 Common Patterns

### Multi-Tenant Setup
```python
# All components support tenant_id
agent = create_agent(
    "agent1", "My Agent", gateway,
    tenant_id="tenant_123"
)

rag = create_rag_system(
    db, gateway,
    tenant_id="tenant_123"
)
```

### Error Handling with Suggestions
```python
from src.core.utils import create_error_with_suggestion
from src.core.exceptions import ConfigurationError

try:
    # Your code
    pass
except Exception as e:
    raise create_error_with_suggestion(
        ConfigurationError,
        message=f"Configuration error: {str(e)}",
        suggestion="Check that all required fields are provided. See print_config_options('component') for available options."
    )
```

### Configuration Validation
```python
from src.core.utils import ConfigValidator

validator = ConfigValidator()

# Validate required fields
validator.validate_required(
    config,
    required_keys=['api_key', 'model'],
    component_name='gateway'
)

# Validate type
validator.validate_type(
    config,
    key='timeout',
    expected_type=float,
    component_name='gateway'
)

# Validate range
validator.validate_range(
    config,
    key='timeout',
    min_value=1.0,
    max_value=300.0,
    component_name='gateway'
)
```

---

## 🚀 Advanced Features

### Vector Index Management
```python
from src.core.rag import create_rag_system, IndexType, IndexDistance

rag = create_rag_system(db, gateway)

# Create IVFFlat index
rag.index_manager.create_index(
    table_name="embeddings",
    column_name="embedding",
    index_type=IndexType.IVFFLAT,
    index_params={"lists": 100}
)

# Reindex after model change
rag.reindex_vector_index(
    table_name="embeddings",
    column_name="embedding",
    concurrently=True
)
```

### KV Cache for LLM Generation
```python
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(
    api_keys={"openai": "sk-..."},
    enable_kv_caching=True,
    kv_cache_default_ttl=3600
)

# Generation automatically uses KV cache
response = await gateway.generate_async(
    prompt="Long context...",
    model="gpt-4"
)
```

### Hallucination Detection
```python
from src.core.rag import create_rag_system, create_hallucination_detector

rag = create_rag_system(db, gateway, enable_hallucination_detection=True)

# Query with automatic hallucination detection
result = await rag.query("What is our refund policy?")

if 'hallucination_result' in result:
    hallucination = result['hallucination_result']
    if hallucination['is_hallucination']:
        print(f"Warning: Potential hallucination (confidence: {hallucination['confidence']})")
```

---

## ☁️ FaaS Services

### Using Agent Service
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8083/api/v1/agents",
        json={"name": "My Agent", "llm_model": "gpt-4"},
        headers={"X-Tenant-ID": "tenant_123"}
    )
    agent = response.json()
```

### Using RAG Service
```python
async with httpx.AsyncClient() as client:
    # Ingest document
    await client.post(
        "http://localhost:8082/api/v1/rag/documents",
        json={"title": "Doc", "content": "..."},
        headers={"X-Tenant-ID": "tenant_123"}
    )
    
    # Query
    response = await client.post(
        "http://localhost:8082/api/v1/rag/query",
        json={"query": "What is AI?", "top_k": 5},
        headers={"X-Tenant-ID": "tenant_123"}
    )
```

### Using Gateway Service
```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8080/api/v1/gateway/generate",
        json={"prompt": "Hello", "model": "gpt-4"},
        headers={"X-Tenant-ID": "tenant_123"}
    )
    result = response.json()
```

📖 **[FaaS Examples](../../examples/faas/)** | **[FaaS Documentation](../src/faas/README.md)**

---

## 🔗 Quick Links

- **[Full Documentation Index](DOCUMENTATION_INDEX.md)** - Complete documentation navigation
- **[Main README](../../README.md)** - Project overview
- **[Examples](../../examples/)** - Code examples
- **[FaaS Examples](../../examples/faas/)** - FaaS service examples
- **[Troubleshooting](../troubleshooting/README.md)** - Common issues

---

## 📝 Common Tasks Cheat Sheet

| Task | Code |
|------|------|
| Create agent | `create_agent("id", "name", gateway)` |
| Create from prompt | `await create_agent_from_prompt("prompt", gateway)` |
| Execute task | `await execute_task(agent, "type", params)` |
| Create gateway | `create_gateway(api_keys={"openai": "sk-..."})` |
| Generate text | `gateway.generate("prompt", "gpt-4")` |
| Create RAG | `create_rag_system(db, gateway)` |
| Query RAG | `await rag.query("question")` |
| Create vector index | `rag.index_manager.create_index(...)` |
| Reindex | `rag.reindex_vector_index(...)` |
| Enable KV cache | `create_gateway(..., enable_kv_caching=True)` |
| Enable hallucination detection | `create_rag_system(..., enable_hallucination_detection=True)` |
| Discover config | `print_config_options('agent')` |
| Validate config | `discover_config('gateway', config)` |
| Use Agent Service | `POST http://agent-service:8083/api/v1/agents` |
| Use RAG Service | `POST http://rag-service:8082/api/v1/rag/query` |
| Use Gateway Service | `POST http://gateway-service:8080/api/v1/gateway/generate` |
| Use Prompt Generator Service | `POST http://prompt-generator-service:8087/api/v1/prompt/agents` |
| Use LLMOps Service | `POST http://llmops-service:8088/api/v1/llmops/operations` |

---

**Last Updated:** 2025-01-XX

