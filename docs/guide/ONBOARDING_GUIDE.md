# Motadata SDK Onboarding Guide

**Welcome to the Motadata Python AI SDK!** This guide will help you understand the SDK architecture, components, and how everything works together.

---

## 🎯 Who This Guide Is For

- **New team members** joining the project
- **Developers** who need to understand the SDK structure
- **Architects** evaluating the SDK design
- **Anyone** who wants a comprehensive overview

---

## 📋 Table of Contents

1. [What Is This SDK?](#what-is-this-sdk)
2. [Architecture Overview](#architecture-overview)
3. [Core Components](#core-components)
4. [How Components Work Together](#how-components-work-together)
5. [Learning Path](#learning-path)
6. [Common Workflows](#common-workflows)
7. [Integration Patterns](#integration-patterns)
8. [Next Steps](#next-steps)

---

## What Is This SDK?

The **Motadata Python AI SDK** is a comprehensive, modular framework for building AI-powered applications. It provides:

- **Unified LLM Interface**: Access multiple AI providers (OpenAI, Anthropic, Google) through one gateway
- **Autonomous Agents**: Create intelligent agents that can execute tasks, use tools, and manage memory
- **RAG System**: Build document Q&A systems with vector search and retrieval
- **Prompt-Based Creation**: Generate agents and tools from natural language descriptions
- **Production Features**: Caching, observability, multi-tenancy, error handling

### Key Principles

1. **Modularity**: Each component is independent and swappable
2. **Multi-Tenancy**: Full tenant isolation across all components
3. **Dual Mode**: Can be used as a library (`src/core/`) or as services (`src/faas/`)
4. **Function-Driven API**: Simple factory functions for component creation
5. **Observability-First**: Built-in tracing, logging, and metrics

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  SaaS Platform Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    AWS API Gateway (Routing, Auth, Rate Limiting)     │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                       │
│                        ▼                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │      SaaS Backend Services (Business Logic)          │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                       │
│                        ▼                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Motadata AI SDK (This Framework)            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │   Agents     │  │     RAG      │  │      ML      │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │   Gateway    │  │   Database   │  │ Observability│   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                       │
│                        ▼                                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Infrastructure Layer                           │   │
│  │  - PostgreSQL (with pgvector)  - Dragonfly (Cache)    │   │
│  │  - NATS (Messaging)            - OTEL (Observability)  │   │
│  │  - CODEC (Serialization)                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Layers

1. **SaaS Platform Layer**: Your business logic and API gateway
2. **AI SDK Layer**: Core AI components (Agents, RAG, Gateway, etc.)
3. **Infrastructure Layer**: Databases, messaging, observability tools

### Data Flow

```
User Request
    ↓
AWS API Gateway (Auth, Rate Limiting)
    ↓
SaaS Backend (Business Logic)
    ↓
AI SDK Components (Agents/RAG/ML)
    ↓
LiteLLM Gateway (provides model access, handles API calls, rate limiting, caching)
    ↓
LLM Providers (OpenAI, Anthropic, Google, etc. - actual model execution)
```

For detailed architecture information, see:
- **[SDK Architecture](architecture/SDK_ARCHITECTURE.md)** - Overall architecture
- **[AI Architecture Design](architecture/AI_ARCHITECTURE_DESIGN.md)** - Detailed AI architecture

---

## Core Components

The SDK consists of several core components, each serving a specific purpose:

### 1. Data Ingestion Service
**Purpose**: Simple, unified interface for uploading and processing data files

**What it does**:
- **One-Line Upload**: Simply provide a file path, everything else is automatic
- **Automatic Processing**: Detects format, extracts content, processes data
- **Automatic Integration**: Automatically ingests into RAG, caches content, makes available to agents
- **Multi-Modal Support**: Handles text, PDF, DOC/DOCX, audio, video, and images
- **Data Validation**: Validates file format, size, and content
- **Data Cleansing**: Normalizes and cleanses data for quality

**Supported Data Formats**:
- **Text**: `.txt`, `.md`, `.markdown`, `.html`, `.json`
- **Documents**: `.pdf`, `.doc`, `.docx`, `.rtf`
- **Audio**: `.mp3`, `.wav`, `.m4a`, `.ogg` (with automatic transcription)
- **Video**: `.mp4`, `.avi`, `.mov`, `.mkv` (with transcription and frame extraction)
- **Images**: `.jpg`, `.png`, `.gif`, `.bmp` (with OCR and description)
- **Structured**: `.csv`, `.json`, `.xml`, `.xlsx`, `.xls`

**When to use**: When you want to upload files and have them automatically work with all AI components

📖 **[Full Documentation](../src/core/data_ingestion/README.md)** | **[Multi-Modal Processing](components/multimodal_data_processing.md)**

---

### 2. LiteLLM Gateway
**Purpose**: Unified interface for multiple LLM providers

**What it does**:
- Abstracts differences between LLM providers (OpenAI, Anthropic, Google)
- Handles authentication, rate limiting, circuit breakers
- Caches responses to reduce costs
- Tracks usage and costs (LLMOps)

**When to use**: Always - this is the foundation for all AI operations

📖 **[Full Documentation](components/litellm_gateway_explanation.md)** | **[Component README](../src/core/litellm_gateway/README.md)**

---

### 3. Agent Framework
**Purpose**: Create autonomous AI agents that can execute tasks

**What it does**:
- Creates agents with memory, tools, and session management
- Executes tasks using LLM assistance
- Manages agent-to-agent communication
- Supports tool calling and function execution

**When to use**: Building chatbots, assistants, or task automation systems

📖 **[Full Documentation](components/agno_agent_framework_explanation.md)** | **[Component README](../src/core/agno_agent_framework/README.md)**

---

### 4. RAG System
**Purpose**: Answer questions from documents using retrieval-augmented generation

**What it does**:
- Processes and chunks documents from multiple formats
- **Multi-Modal Data Support**: Handles text, PDF, DOC/DOCX, audio, video, and images
- Creates embeddings and stores in vector database
- Retrieves relevant context for queries
- Generates answers using retrieved context

**Supported Data Formats**:
- **Text**: `.txt`, `.md`, `.markdown`, `.html`, `.json`
- **Documents**: `.pdf`, `.doc`, `.docx`, `.rtf`
- **Audio**: `.mp3`, `.wav`, `.m4a`, `.ogg` (with automatic transcription)
- **Video**: `.mp4`, `.avi`, `.mov`, `.mkv` (with transcription and frame extraction)
- **Images**: `.jpg`, `.png`, `.gif`, `.bmp` (with OCR and description)

**When to use**: Document Q&A, knowledge base systems, semantic search, multi-modal content analysis

📖 **[Full Documentation](components/rag_system_explanation.md)** | **[Component README](../src/core/rag/README.md)**

---

### 5. Prompt-Based Generator
**Purpose**: Create agents and tools from natural language prompts

**What it does**:
- Interprets natural language descriptions
- Generates fully configured agents and tools
- Validates generated code
- Integrates with feedback loop for improvement

**When to use**: Rapid prototyping, dynamic agent creation, user-defined tools

📖 **[Full Documentation](components/prompt_based_generator_explanation.md)** | **[User Guide](prompt_based_creation_guide.md)**

---

### 6. Cache Mechanism
**Purpose**: Reduce API costs by caching LLM responses

**What it does**:
- Caches LLM responses with TTL
- Supports multiple backends (memory, Dragonfly)
- Automatic cache invalidation
- Tenant-isolated caching

**When to use**: Always - reduces costs significantly (50-90% savings)

📖 **[Full Documentation](components/cache_mechanism_explanation.md)** | **[Component README](../src/core/cache_mechanism/README.md)**

---

### 7. PostgreSQL Database
**Purpose**: Vector database for embeddings and structured data

**What it does**:
- Stores embeddings with pgvector extension
- Provides similarity search
- Manages structured data
- Supports multi-tenancy

**When to use**: RAG systems, embedding storage, structured data

📖 **[Full Documentation](components/postgresql_database_explanation.md)** | **[Component README](../src/core/postgresql_database/README.md)**

---

### 8. Evaluation & Observability
**Purpose**: Monitor, trace, and debug SDK operations

**What it does**:
- Distributed tracing with OpenTelemetry
- Structured logging
- Metrics collection
- Performance monitoring

**When to use**: Always - essential for production debugging

📖 **[Full Documentation](components/evaluation_observability_explanation.md)** | **[Component README](../src/core/evaluation_observability/README.md)**

---

### 9. Other Components

- **Prompt Context Management**: Template-based prompts with versioning
- **API Backend Services**: RESTful API endpoints
- **Machine Learning Framework**: ML training, inference, MLOps
- **Integration Components**: NATS, OTEL, CODEC

📖 **[All Components](components/README.md)**

---

## How Components Work Together

### Example 1: Agent with RAG

```
User Query: "What is our refund policy?"
    ↓
Agent Framework (receives query)
    ↓
RAG System (retrieves relevant documents)
    ↓
LiteLLM Gateway (provides LLM model, handles API calls to providers)
    ↓
LLM Provider (OpenAI/Anthropic/Google - generates answer using context)
    ↓
LiteLLM Gateway (returns response)
    ↓
Cache Mechanism (stores response for future use)
    ↓
Response to User
```

**Code Example**:
```python
from src.core.agno_agent_framework import create_agent
from src.core.rag import create_rag_system
from src.core.litellm_gateway import create_gateway

# Setup
gateway = create_gateway(api_keys={"openai": "sk-..."})
rag = create_rag_system(db, gateway, tenant_id="tenant_123")
agent = create_agent("support_agent", "Customer Support", gateway)

# Use RAG in agent
context = await rag.retrieve("refund policy", limit=5)
response = await agent.execute_task(
    f"Answer this question using context: {context}\n\nQuestion: What is our refund policy?"
)
```

---

### Example 3: Multi-Agent System

```
User Request: "Analyze this incident and create a change request"
    ↓
Orchestrator Agent (coordinates)
    ↓
    ├─→ Analysis Agent (analyzes incident)
    │   └─→ LiteLLM Gateway (provides model access)
    │       └─→ LLM Provider (generates analysis)
    │
    └─→ Change Agent (creates change request)
        └─→ LiteLLM Gateway (provides model access)
            └─→ LLM Provider (generates change request)
    ↓
Response to User
```

**Integration Points**:
- Agents communicate through shared memory or messaging
- All agents use the same LiteLLM Gateway
- Observability tracks all agent operations
- Cache reduces redundant LLM calls

---

### Example 4: Prompt-Based Agent Creation

```
User Prompt: "Create a customer support agent that can handle refunds"
    ↓
Prompt-Based Generator (interprets prompt)
    ↓
Agent Generator (creates agent configuration)
    ↓
Agent Framework (instantiates agent)
    ↓
Ready-to-use Agent
```

**Code Example**:
```python
from src.core.prompt_based_generator import create_agent_from_prompt

agent = await create_agent_from_prompt(
    "Create a customer support agent that can handle refunds and returns",
    gateway=gateway,
    tenant_id="tenant_123"
)
```

---

## Learning Path

### Foundation
- Read [Main README](../README.md) for the quick start
- Run the [Hello World example](../examples/hello_world.py)
- Understand [LiteLLM Gateway](components/litellm_gateway_explanation.md)
- Study [Agent Framework](components/agno_agent_framework_explanation.md)
- Try [Basic Agent Example](../examples/basic_usage/05_agent_basic.py)
- Understand [Cache Mechanism](components/cache_mechanism_explanation.md)
- Review [RAG System](components/rag_system_explanation.md)
- Run [RAG Example](../examples/basic_usage/07_rag_basic.py)
- Try [Agent with RAG](../examples/integration/agent_with_rag.py)

### Advanced Features

The SDK includes production-grade advanced features for optimization and quality assurance:

- **Vector Index Management**: Automatic creation and reindexing of IVFFlat and HNSW indexes for optimal RAG search performance
- **KV Cache**: Attention key-value caching for LLM generation, reducing latency by 20-50% for repeated contexts
- **Hallucination Detection**: Automatic detection of ungrounded responses in RAG systems, ensuring answers are supported by retrieved documents

📖 **[Advanced Features Documentation](components/advanced_features.md)**

### Advanced Capabilities
- Study [Prompt-Based Generator](components/prompt_based_generator_explanation.md)
- Try [Prompt-Based Examples](../examples/prompt_based/)
- Understand [Observability](components/evaluation_observability_explanation.md)
- Read [SDK Architecture](architecture/SDK_ARCHITECTURE.md)
- Study [AI Architecture Design](architecture/AI_ARCHITECTURE_DESIGN.md)
- Review [REST/FastAPI Architecture](architecture/REST_FASTAPI_ARCHITECTURE.md)
- Review [Integration Guides](integration_guides/README.md)
- Study NATS, OTEL, and CODEC integrations
- Build a complete use case

### Production Readiness
- Study error handling patterns
- Review [Troubleshooting Guides](troubleshooting/README.md)
- Write tests for your components
- Understand tenant isolation and security best practices
- Test multi-tenant scenarios
- Study caching strategies
- Review performance metrics
- Optimize implementations

---

## Common Workflows

### Workflow 1: Creating a Simple Agent

```python
from src.core.agno_agent_framework import create_agent
from src.core.litellm_gateway import create_gateway

# 1. Create gateway
gateway = create_gateway(api_keys={"openai": "sk-..."})

# 2. Create agent
agent = create_agent(
    agent_id="my_agent",
    name="My Agent",
    gateway=gateway,
    tenant_id="tenant_123"
)

# 3. Execute task
result = await agent.execute_task("What is 2+2?")
print(result)
```

📖 **[Full Guide](../src/core/agno_agent_framework/README.md)**

---

### Workflow 3: Setting Up RAG System

```python
from src.core.rag import create_rag_system
from src.core.litellm_gateway import create_gateway
from src.core.postgresql_database import create_database

# 1. Setup database
db = create_database(connection_string="postgresql://...")

# 2. Create gateway
gateway = create_gateway(api_keys={"openai": "sk-..."})

# 3. Create RAG system
rag = create_rag_system(db, gateway, tenant_id="tenant_123")

# 4. Add documents
await rag.add_documents([
    {"content": "Document 1 content...", "metadata": {"title": "Doc 1"}},
    {"content": "Document 2 content...", "metadata": {"title": "Doc 2"}},
])

# 5. Query
results = await rag.query("What is the main topic?", limit=5)
```

📖 **[Full Guide](../src/core/rag/README.md)**

---

### Workflow 4: Creating Agent from Prompt

```python
from src.core.prompt_based_generator import create_agent_from_prompt
from src.core.litellm_gateway import create_gateway

# 1. Create gateway
gateway = create_gateway(api_keys={"openai": "sk-..."})

# 2. Create agent from prompt
agent = await create_agent_from_prompt(
    prompt="Create a customer support agent that can handle refunds, returns, and product questions",
    gateway=gateway,
    tenant_id="tenant_123"
)

# 3. Use agent
response = await agent.execute_task("A customer wants a refund for order #12345")
```

📖 **[Full Guide](prompt_based_creation_guide.md)**

---

### Workflow 5: Multi-Agent Orchestration

```python
from src.core.agno_agent_framework import create_agent, create_orchestrator

# 1. Create multiple agents
analyst = create_agent("analyst", "Data Analyst", gateway)
writer = create_agent("writer", "Content Writer", gateway)

# 2. Create orchestrator
orchestrator = create_orchestrator([analyst, writer])

# 3. Execute coordinated task
result = await orchestrator.execute(
    "Analyze sales data and write a summary report"
)
```

📖 **[Agent Framework](../src/core/agno_agent_framework/README.md)**

---

## Integration Patterns

### Pattern 1: SDK in SaaS Platform

```
SaaS Backend Service
    ↓
Import AI SDK
    ↓
Initialize Components (Gateway, Agents, RAG)
    ↓
Handle Business Logic
    ↓
Use SDK Components for AI Operations
```

**Key Points**:
- SDK is imported as a library
- Components are initialized per tenant
- All operations are tenant-isolated

---

### Pattern 2: Observability Integration

```
SDK Component Operation
    ↓
OpenTelemetry Tracer (automatic)
    ↓
OTEL Collector
    ↓
Observability Backend (Jaeger, Prometheus, etc.)
```

**Key Points**:
- Tracing is automatic for all SDK operations
- Metrics are collected automatically
- Logs are structured and searchable

---

### Pattern 3: Caching Strategy

```
LLM Request
    ↓
Check Cache (by prompt hash + tenant)
    ↓
    ├─→ Cache Hit: Return cached response ($0 cost)
    └─→ Cache Miss: Call LLM API → Cache response → Return
```

**Key Points**:
- Cache keys include tenant ID for isolation
- TTL-based expiration
- Automatic cache invalidation

---

## Next Steps

### Immediate Next Steps

1. **Read the Architecture Docs**:
   - [SDK Architecture](architecture/SDK_ARCHITECTURE.md)
   - [AI Architecture Design](architecture/AI_ARCHITECTURE_DESIGN.md)

2. **Try the Examples**:
   - [Basic Usage Examples](../examples/basic_usage/)
   - [Integration Examples](../examples/integration/)

3. **Explore Components**:
   - [Component Documentation](components/README.md)
   - [Component Explanations](components/)

### When You Need Specific Information

- **Quick Reference**: [Quick Reference Guide](guide/QUICK_REFERENCE.md)
- **Navigation**: [Documentation Index](guide/DOCUMENTATION_INDEX.md)
- **Troubleshooting**: [Troubleshooting Index](troubleshooting/README.md)
- **Search**: Use [search_docs.py](guide/search_docs.py) tool

### Deep Dives

- **Development**: [Developer Integration Guide](guide/DEVELOPER_INTEGRATION_GUIDE.md) - Component development and integration
- **Architecture**: [Architecture Documentation](architecture/)
- **Integration**: [Integration Guides](integration_guides/)
- **Components**: [Component Explanations](components/)

---

## 📚 Documentation Quick Links

### Getting Started
- **[Main README](../README.md)** - Project overview and quick start
- **[Hello World Example](../examples/hello_world.py)** - Simplest example

### Architecture
- **[SDK Architecture](architecture/SDK_ARCHITECTURE.md)** - Overall architecture
- **[AI Architecture Design](architecture/AI_ARCHITECTURE_DESIGN.md)** - Detailed AI architecture
- **[REST/FastAPI Architecture](architecture/REST_FASTAPI_ARCHITECTURE.md)** - API layer design
- **[FaaS Architecture](architecture/FAAS_IMPLEMENTATION_GUIDE.md)** - FaaS services-based architecture

### Components
- **[All Components](components/README.md)** - Component overview
- **[Component Explanations](components/)** - Detailed component docs

### Integration
- **[Integration Guides](integration_guides/README.md)** - Integration overview
- **[NATS Integration](integration_guides/nats_integration_guide.md)**
- **[OTEL Integration](integration_guides/otel_integration_guide.md)**
- **[CODEC Integration](integration_guides/codec_integration_guide.md)**
- **[FaaS Integrations](../src/faas/integrations/README.md)** - NATS, OTEL, CODEC for FaaS services

### FaaS Services
- **[FaaS Overview](../src/faas/README.md)** - FaaS architecture and services
- **[FaaS Implementation Guide](architecture/FAAS_IMPLEMENTATION_GUIDE.md)** - Complete implementation guide
- **[FaaS Examples](../../examples/faas/)** - FaaS service usage examples
- **[FaaS Deployment](../deployment/)** - Docker, Kubernetes, AWS Lambda guides
- **[Prompt Generator Service](../src/faas/services/prompt_generator_service/README.md)** - Prompt-based creation service
- **[LLMOps Service](../src/faas/services/llmops_service/README.md)** - LLM operations monitoring service

### Guides & Tools
- **[Documentation Index](guide/DOCUMENTATION_INDEX.md)** - Complete navigation
- **[Developer Integration Guide](guide/DEVELOPER_INTEGRATION_GUIDE.md)** - **FOR DEVELOPERS** - Component development and integration patterns
- **[Quick Reference](guide/QUICK_REFERENCE.md)** - Common tasks
- **[Navigation Helper](guide/NAVIGATION_HELPER.md)** - Find information fast
- **[Prompt-Based Creation](prompt_based_creation_guide.md)** - Create agents from prompts
- **[Advanced Features](components/advanced_features.md)** - Vector indexes, KV cache, hallucination detection

### Troubleshooting
- **[Troubleshooting Index](troubleshooting/README.md)** - All troubleshooting guides

---

## 🆘 Need Help?

1. **Start Here**: This onboarding guide
2. **Quick Start**: [README Quick Start](../README.md#quick-start-5-minutes)
3. **Examples**: [Examples Directory](../examples/)
4. **Troubleshooting**: [Troubleshooting Index](troubleshooting/README.md)
5. **Search**: [Documentation Index](guide/DOCUMENTATION_INDEX.md)

---

**Welcome to the team! 🚀**

**SDK Version:** 0.1.0

