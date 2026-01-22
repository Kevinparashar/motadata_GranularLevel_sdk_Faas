# Developer Integration Guide

> **For SDK Contributors and Maintainers**  
> This guide combines development guidelines, integration patterns, and practical examples to help you understand how to develop new components and how existing components integrate and work together.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [SDK Architecture Fundamentals](#sdk-architecture-fundamentals)
3. [Component Development Guide](#component-development-guide)
4. [Component Integration Patterns](#component-integration-patterns)
5. [How Components Work Together](#how-components-work-together)
6. [Development Workflows](#development-workflows)
7. [Code Examples](#code-examples)
8. [Testing Integration Points](#testing-integration-points)
9. [Best Practices](#best-practices)
10. [Troubleshooting Development Issues](#troubleshooting-development-issues)

---

## Overview

### Purpose

This guide helps you:
- **Develop new components** following SDK patterns
- **Understand how components integrate** with each other
- **Extend existing components** safely
- **Debug component interactions** effectively

### Prerequisites

- Python 3.8+ knowledge
- Understanding of async/await patterns
- Familiarity with dependency injection
- Basic knowledge of microservices architecture

### Quick Navigation

- **New to SDK?** Start with [Onboarding Guide](ONBOARDING_GUIDE.md)
- **Need architecture details?** See [SDK Architecture](../architecture/SDK_ARCHITECTURE.md)
- **Looking for usage examples?** Check [Examples](../../examples/)

---

## SDK Architecture Fundamentals

### Core Principles

1. **Modularity**: Each component is independent and swappable
2. **Dependency Injection**: Components receive dependencies through constructors
3. **Interface-Based Design**: Components implement interfaces for swappability
4. **Multi-Tenancy**: All components support tenant isolation
5. **Dual Mode**: Library mode (`src/core/`) and FaaS mode (`src/faas/`)

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                          │
│  (Your SaaS Backend or FaaS Services)                       │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  SDK Core Components                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Agents     │  │     RAG      │  │      ML      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────┴──────┐  ┌───────┴──────┐  ┌───────┴──────┐      │
│  │   Gateway   │  │   Database   │  │   Cache      │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Infrastructure Layer                            │
│  PostgreSQL | Redis | NATS | OTEL | CODEC                   │
└─────────────────────────────────────────────────────────────┘
```

### Component Communication Flow

```
Component A (e.g., Agent)
    │
    ├─→ Uses Gateway (for LLM calls)
    ├─→ Uses Cache (for response caching)
    ├─→ Uses Database (for persistence)
    └─→ Uses Observability (for tracing/logging)
```

**Key Point**: Components communicate through **dependency injection**, not direct imports.

---

## Component Development Guide

### Step 1: Component Structure

When creating a new component, follow this structure:

```
src/core/your_component/
├── __init__.py          # Component exports
├── README.md            # Component documentation
├── your_component.py    # Main implementation
├── functions.py         # Factory and convenience functions
├── interfaces.py        # Interfaces for swappability (optional)
├── exceptions.py        # Component-specific exceptions (optional)
└── utils.py             # Utility functions (optional)
```

### Step 2: Component Template

#### `__init__.py` - Component Exports

```python
"""
Your Component

Brief description of what this component does.
"""

from .your_component import YourComponent
from .functions import (
    create_your_component,
    your_component_function,
)

__all__ = [
    "YourComponent",
    "create_your_component",
    "your_component_function",
]
```

#### `your_component.py` - Main Implementation

```python
"""
Your Component Implementation

This component does X, Y, and Z.
"""

import logging
from typing import Any, Dict, Optional

from ..litellm_gateway import LiteLLMGateway
from ..cache_mechanism import CacheMechanism
from .exceptions import YourComponentError

logger = logging.getLogger(__name__)


class YourComponent:
    """
    Your Component class.
    
    This component provides functionality for...
    
    Args:
        gateway: LiteLLM Gateway instance for LLM calls
        cache: Cache mechanism instance (optional)
        tenant_id: Tenant ID for multi-tenant isolation
    """
    
    def __init__(
        self,
        gateway: LiteLLMGateway,
        cache: Optional[CacheMechanism] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize Your Component.
        
        Args:
            gateway: Gateway instance (required)
            cache: Cache instance (optional)
            tenant_id: Tenant ID for isolation
        """
        self.gateway = gateway
        self.cache = cache
        self.tenant_id = tenant_id
        logger.info(f"YourComponent initialized for tenant: {tenant_id}")
    
    async def execute(
        self,
        input_data: str,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute component operation.
        
        Args:
            input_data: Input data to process
            tenant_id: Tenant ID (uses instance tenant_id if not provided)
            
        Returns:
            Dictionary with results
            
        Raises:
            YourComponentError: If execution fails
        """
        tenant_id = tenant_id or self.tenant_id
        
        try:
            # Check cache first
            if self.cache:
                cache_key = f"{tenant_id}:your_component:{hash(input_data)}"
                cached = self.cache.get(cache_key, tenant_id=tenant_id)
                if cached:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached
            
            # Process using gateway
            result = await self.gateway.generate_async(
                prompt=input_data,
                model="gpt-4",
                tenant_id=tenant_id,
            )
            
            # Cache result
            if self.cache:
                self.cache.set(
                    cache_key,
                    {"result": result.text},
                    tenant_id=tenant_id,
                    ttl=3600,
                )
            
            return {"result": result.text}
            
        except Exception as e:
            logger.error(f"Error in YourComponent.execute: {e}", exc_info=True)
            raise YourComponentError(f"Execution failed: {e}") from e
```

#### `functions.py` - Factory Functions

```python
"""
Factory and convenience functions for Your Component.
"""

from typing import Optional

from ..litellm_gateway import create_gateway, LiteLLMGateway
from ..cache_mechanism import create_cache, CacheMechanism
from .your_component import YourComponent


def create_your_component(
    gateway: Optional[LiteLLMGateway] = None,
    cache: Optional[CacheMechanism] = None,
    tenant_id: Optional[str] = None,
    **kwargs,
) -> YourComponent:
    """
    Create a YourComponent instance.
    
    Factory function that creates and configures YourComponent.
    
    Args:
        gateway: Gateway instance (creates default if not provided)
        cache: Cache instance (optional)
        tenant_id: Tenant ID for multi-tenant isolation
        **kwargs: Additional configuration
        
    Returns:
        Configured YourComponent instance
        
    Example:
        ```python
        component = create_your_component(
            tenant_id="tenant_123",
            gateway=gateway,
            cache=cache
        )
        ```
    """
    if gateway is None:
        gateway = create_gateway(**kwargs.get("gateway_config", {}))
    
    if cache is None and kwargs.get("enable_cache", True):
        cache = create_cache(**kwargs.get("cache_config", {}))
    
    return YourComponent(
        gateway=gateway,
        cache=cache,
        tenant_id=tenant_id,
    )


async def your_component_function(
    component: YourComponent,
    input_data: str,
    tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function for component operation.
    
    Args:
        component: YourComponent instance
        input_data: Input data
        tenant_id: Tenant ID
        
    Returns:
        Operation result
    """
    return await component.execute(input_data, tenant_id=tenant_id)
```

#### `exceptions.py` - Component Exceptions

```python
"""
Exceptions for Your Component.
"""

from ...core.exceptions import SDKError


class YourComponentError(SDKError):
    """Base exception for Your Component errors."""
    pass


class YourComponentExecutionError(YourComponentError):
    """Raised when component execution fails."""
    pass


class YourComponentValidationError(YourComponentError):
    """Raised when input validation fails."""
    pass
```

### Step 3: Integration with Other Components

#### Using Gateway

```python
# In your component
from ..litellm_gateway import LiteLLMGateway

class YourComponent:
    def __init__(self, gateway: LiteLLMGateway):
        self.gateway = gateway
    
    async def process(self, prompt: str):
        # Use gateway for LLM calls
        response = await self.gateway.generate_async(
            prompt=prompt,
            model="gpt-4",
            tenant_id=self.tenant_id,
        )
        return response.text
```

#### Using Cache

```python
# In your component
from ..cache_mechanism import CacheMechanism

class YourComponent:
    def __init__(self, cache: Optional[CacheMechanism] = None):
        self.cache = cache
    
    async def process(self, key: str, data: str):
        # Check cache
        cached = self.cache.get(key, tenant_id=self.tenant_id) if self.cache else None
        if cached:
            return cached
        
        # Process and cache
        result = await self._process_data(data)
        if self.cache:
            self.cache.set(key, result, tenant_id=self.tenant_id, ttl=3600)
        
        return result
```

#### Using Database

```python
# In your component
from ..postgresql_database import DatabaseConnection

class YourComponent:
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    async def save(self, data: Dict, tenant_id: str):
        # Save with tenant isolation
        query = """
            INSERT INTO your_table (tenant_id, data)
            VALUES (%s, %s)
        """
        await self.db.execute_update(
            query,
            parameters=(tenant_id, json.dumps(data)),
            tenant_id=tenant_id,
        )
```

### Step 4: Multi-Tenancy Support

**Always include `tenant_id` parameter** in component methods:

```python
class YourComponent:
    async def execute(
        self,
        input_data: str,
        tenant_id: Optional[str] = None,  # Always include tenant_id
    ) -> Dict[str, Any]:
        # Use tenant_id for:
        # 1. Database queries: WHERE tenant_id = %s
        # 2. Cache keys: f"{tenant_id}:{key}"
        # 3. Logging: Include tenant_id in logs
        # 4. Gateway calls: Pass tenant_id to gateway
        
        tenant_id = tenant_id or self.tenant_id
        if not tenant_id:
            raise ValueError("tenant_id is required")
        
        # All operations scoped to tenant_id
        cache_key = f"{tenant_id}:your_component:{hash(input_data)}"
        # ...
```

---

## Component Integration Patterns

### Pattern 1: Agent Using Gateway

**How Agent integrates with Gateway:**

```python
# src/core/agno_agent_framework/agent.py
class Agent:
    def __init__(self, gateway: LiteLLMGateway):
        self.gateway = gateway  # Dependency injection
    
    async def execute_task(self, task: AgentTask):
        # Agent uses Gateway for LLM calls
        response = await self.gateway.generate_async(
            prompt=task.prompt,
            model=self.llm_model,
            tenant_id=task.tenant_id,
        )
        return response.text
```

**Integration Points:**
- Agent receives Gateway via constructor (dependency injection)
- Agent calls `gateway.generate_async()` for LLM operations
- Gateway handles rate limiting, retries, provider management
- Agent doesn't know about LLM providers directly

### Pattern 2: RAG Using Gateway and Database

**How RAG integrates with Gateway and Database:**

```python
# src/core/rag/rag_system.py
class RAGSystem:
    def __init__(
        self,
        db: DatabaseConnection,
        gateway: LiteLLMGateway,
        cache: Optional[CacheMechanism] = None,
    ):
        self.db = db
        self.gateway = gateway
        self.cache = cache
        self.retriever = Retriever(vector_ops, gateway)
        self.generator = RAGGenerator(gateway)
    
    async def query(self, query: str, tenant_id: str):
        # 1. Generate query embedding using Gateway
        embedding = await self.gateway.embed_async(
            texts=[query],
            model="text-embedding-3-small",
            tenant_id=tenant_id,
        )
        
        # 2. Search database for similar documents
        results = self.db.vector_ops.search_similar(
            query_embedding=embedding.embeddings[0],
            top_k=5,
            tenant_id=tenant_id,  # Tenant isolation
        )
        
        # 3. Generate response using Gateway
        context = "\n".join([r["content"] for r in results])
        response = await self.gateway.generate_async(
            prompt=f"Context: {context}\n\nQuestion: {query}",
            model="gpt-4",
            tenant_id=tenant_id,
        )
        
        return response.text
```

**Integration Points:**
- RAG uses Gateway for embeddings AND generation
- RAG uses Database for vector search
- RAG uses Cache for query result caching
- All operations are tenant-scoped

### Pattern 3: Cache Integration with All Components

**How Cache integrates with components:**

```python
# Example: Gateway using Cache
class LiteLLMGateway:
    def __init__(self, cache: Optional[CacheMechanism] = None):
        self.cache = cache
    
    async def generate_async(self, prompt: str, tenant_id: str):
        # Check cache
        cache_key = f"{tenant_id}:gateway:{hash(prompt)}"
        if self.cache:
            cached = self.cache.get(cache_key, tenant_id=tenant_id)
            if cached:
                return cached
        
        # Call LLM
        response = await self._call_llm(prompt)
        
        # Cache response
        if self.cache:
            self.cache.set(
                cache_key,
                response,
                tenant_id=tenant_id,
                ttl=3600,
            )
        
        return response
```

**Integration Points:**
- Cache is optional (components work without it)
- Cache keys include tenant_id for isolation
- Cache reduces LLM API costs significantly

### Pattern 4: Observability Integration

**How Observability integrates with all components:**

```python
# Example: Agent with Observability
from ..evaluation_observability import create_tracer

class Agent:
    def __init__(self, tracer=None):
        self.tracer = tracer or create_tracer("agent")
    
    async def execute_task(self, task: AgentTask):
        # Start trace span
        with self.tracer.start_as_current_span("agent.execute_task") as span:
            span.set_attribute("agent.id", self.agent_id)
            span.set_attribute("tenant.id", task.tenant_id)
            
            # Execute task
            result = await self._execute(task)
            
            span.set_attribute("task.completed", True)
            return result
```

**Integration Points:**
- Observability is automatic (tracer created if not provided)
- All operations are traced
- Logs include tenant_id and correlation_id

---

## How Components Work Together

### Example 1: Agent with RAG (Complete Flow)

```
User Query: "What is our refund policy?"
    ↓
Agent Framework (receives query)
    │
    ├─→ Check Cache (Agent checks if query was cached)
    │   └─→ Cache Hit: Return cached response
    │
    ├─→ RAG System (Agent calls RAG for context)
    │   │
    │   ├─→ Gateway (RAG calls Gateway for embeddings)
    │   │   └─→ LLM Provider (OpenAI/Anthropic)
    │   │
    │   ├─→ Database (RAG searches for similar documents)
    │   │   └─→ Vector Search (pgvector similarity search)
    │   │
    │   ├─→ Gateway (RAG calls Gateway for generation)
    │   │   └─→ LLM Provider (generates answer with context)
    │   │
    │   └─→ Cache (RAG caches query result)
    │
    ├─→ Gateway (Agent calls Gateway for final response)
    │   └─→ LLM Provider (generates final answer)
    │
    ├─→ Cache (Agent caches final response)
    │
    └─→ Observability (All steps traced and logged)
```

**Code Implementation:**

```python
# Complete integration example
from src.core.agno_agent_framework import create_agent
from src.core.rag import create_rag_system
from src.core.litellm_gateway import create_gateway
from src.core.cache_mechanism import create_cache
from src.core.postgresql_database import create_database

# 1. Initialize shared components
gateway = create_gateway(api_keys={"openai": "sk-..."})
cache = create_cache(backend="redis", redis_url="redis://localhost:6379")
db = create_database(connection_string="postgresql://...")

# 2. Create RAG system (uses Gateway, Database, Cache)
rag = create_rag_system(
    db=db,
    gateway=gateway,
    cache=cache,
    tenant_id="tenant_123",
)

# 3. Create Agent (uses Gateway, Cache)
agent = create_agent(
    agent_id="support_agent",
    name="Customer Support",
    gateway=gateway,
    cache=cache,
    tenant_id="tenant_123",
)

# 4. Agent uses RAG for context
async def agent_with_rag_query(query: str):
    # Agent retrieves context from RAG
    context = await rag.query(query, tenant_id="tenant_123")
    
    # Agent generates response using context
    response = await agent.execute_task(
        f"Using this context: {context}\n\nAnswer: {query}",
        tenant_id="tenant_123",
    )
    
    return response
```

### Example 2: Data Ingestion → RAG → Agent

```
File Upload
    ↓
Data Ingestion Service
    │
    ├─→ Validate File
    ├─→ Process File (extract text)
    │
    └─→ RAG System (auto-ingest)
        │
        ├─→ Document Processor (chunk document)
        ├─→ Gateway (generate embeddings)
        │   └─→ LLM Provider
        ├─→ Database (store embeddings)
        └─→ Cache (invalidate related cache)
            ↓
Agent (can now query ingested documents)
```

**Code Implementation:**

```python
from src.core.data_ingestion import create_ingestion_service
from src.core.rag import create_rag_system

# 1. Create ingestion service
ingestion = create_ingestion_service(
    db=db,
    enable_auto_ingest=True,  # Auto-ingest into RAG
    tenant_id="tenant_123",
)

# 2. Upload file (automatically ingests into RAG)
result = await ingestion.upload_and_process_async(
    file_path="document.pdf",
    title="Refund Policy",
    tenant_id="tenant_123",
)

# 3. Agent can now query the ingested document
response = await agent.execute_task(
    "What is our refund policy?",
    tenant_id="tenant_123",
)
# Agent will use RAG to retrieve the document we just ingested
```

### Example 3: Multi-Agent Orchestration

```
User Request: "Analyze incident and create change request"
    ↓
Orchestrator Agent
    │
    ├─→ Analysis Agent
    │   ├─→ Gateway (for LLM calls)
    │   └─→ Cache (for response caching)
    │
    └─→ Change Agent
        ├─→ Gateway (for LLM calls)
        └─→ Database (to save change request)
```

**Code Implementation:**

```python
from src.core.agno_agent_framework import create_agent, create_orchestrator

# Create multiple agents (all share Gateway and Cache)
analyst = create_agent("analyst", "Data Analyst", gateway, cache=cache)
writer = create_agent("writer", "Content Writer", gateway, cache=cache)
change_agent = create_agent("change", "Change Manager", gateway, cache=cache)

# Create orchestrator
orchestrator = create_orchestrator([analyst, writer, change_agent])

# Execute coordinated task
result = await orchestrator.execute(
    "Analyze this incident and create a change request",
    tenant_id="tenant_123",
)
```

---

## Development Workflows

### Workflow 1: Adding a New Component

**Step-by-Step:**

1. **Create Component Structure**
   ```bash
   mkdir -p src/core/your_component
   touch src/core/your_component/__init__.py
   touch src/core/your_component/your_component.py
   touch src/core/your_component/functions.py
   touch src/core/your_component/exceptions.py
   touch src/core/your_component/README.md
   ```

2. **Implement Core Class**
   - Follow the template in [Component Template](#step-2-component-template)
   - Include dependency injection for Gateway, Cache, Database
   - Add tenant_id support

3. **Create Factory Functions**
   - Implement `create_your_component()` in `functions.py`
   - Add convenience functions for common operations

4. **Add Integration Points**
   - Integrate with Gateway if LLM calls needed
   - Integrate with Cache if caching needed
   - Integrate with Database if persistence needed

5. **Write Tests**
   ```python
   # src/tests/unit_tests/test_your_component.py
   import pytest
   from src.core.your_component import create_your_component
   
   @pytest.mark.asyncio
   async def test_your_component_execute():
       component = create_your_component(tenant_id="test_tenant")
       result = await component.execute("test input")
       assert result is not None
   ```

6. **Write Documentation**
   - Update component README.md
   - Add usage examples
   - Document integration points

7. **Update Main Exports**
   ```python
   # src/core/__init__.py
   from .your_component import create_your_component
   ```

### Workflow 2: Extending Existing Component

**Example: Adding a new method to Agent**

1. **Understand Current Implementation**
   ```python
   # Read src/core/agno_agent_framework/agent.py
   # Understand how Agent uses Gateway, Cache, etc.
   ```

2. **Add New Method**
   ```python
   # In agent.py
   async def new_method(self, input_data: str, tenant_id: str):
       """New method that uses existing dependencies."""
       # Use self.gateway, self.cache, etc.
       result = await self.gateway.generate_async(...)
       return result
   ```

3. **Add Factory Function**
   ```python
   # In functions.py
   async def agent_new_method(agent: Agent, input_data: str, tenant_id: str):
       """Convenience function."""
       return await agent.new_method(input_data, tenant_id)
   ```

4. **Write Tests**
   ```python
   @pytest.mark.asyncio
   async def test_agent_new_method():
       agent = create_agent(...)
       result = await agent.new_method("input", "tenant_123")
       assert result is not None
   ```

5. **Update Documentation**
   - Add method to README.md
   - Add usage example

### Workflow 3: Integrating Two Components

**Example: Making Agent use RAG**

1. **Understand Both Components**
   - Read Agent implementation
   - Read RAG implementation
   - Understand their interfaces

2. **Add RAG as Dependency**
   ```python
   # In agent.py
   from ..rag import RAGSystem
   
   class Agent:
       def __init__(
           self,
           gateway: LiteLLMGateway,
           rag: Optional[RAGSystem] = None,  # New dependency
       ):
           self.gateway = gateway
           self.rag = rag  # Optional integration
   ```

3. **Use RAG in Agent Methods**
   ```python
   async def execute_task(self, task: AgentTask):
       # Use RAG if available
       if self.rag:
           context = await self.rag.query(
               task.query,
               tenant_id=task.tenant_id,
           )
           task.prompt = f"Context: {context}\n\n{task.prompt}"
       
       # Continue with normal execution
       return await self.gateway.generate_async(...)
   ```

4. **Update Factory Function**
   ```python
   # In functions.py
   def create_agent_with_rag(
       gateway: LiteLLMGateway,
       rag: RAGSystem,
       **kwargs,
   ):
       """Create agent with RAG integration."""
       return Agent(gateway=gateway, rag=rag, **kwargs)
   ```

5. **Write Integration Tests**
   ```python
   @pytest.mark.integration
   async def test_agent_with_rag():
       rag = create_rag_system(...)
       agent = create_agent_with_rag(gateway, rag)
       result = await agent.execute_task(...)
       assert result is not None
   ```

---

## Code Examples

### Example 1: Complete Component Implementation

```python
"""
Example: Sentiment Analysis Component

This component analyzes sentiment of text using LLM.
"""

import logging
from typing import Dict, Optional

from ..litellm_gateway import LiteLLMGateway
from ..cache_mechanism import CacheMechanism
from ..exceptions import SDKError

logger = logging.getLogger(__name__)


class SentimentAnalysisError(SDKError):
    """Sentiment analysis specific error."""
    pass


class SentimentAnalyzer:
    """
    Sentiment Analysis Component.
    
    Analyzes sentiment of text using LLM via Gateway.
    """
    
    def __init__(
        self,
        gateway: LiteLLMGateway,
        cache: Optional[CacheMechanism] = None,
        tenant_id: Optional[str] = None,
    ):
        self.gateway = gateway
        self.cache = cache
        self.tenant_id = tenant_id
    
    async def analyze(
        self,
        text: str,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            tenant_id: Tenant ID for isolation
            
        Returns:
            Dictionary with sentiment and score
        """
        tenant_id = tenant_id or self.tenant_id
        if not tenant_id:
            raise ValueError("tenant_id is required")
        
        # Check cache
        cache_key = f"{tenant_id}:sentiment:{hash(text)}"
        if self.cache:
            cached = self.cache.get(cache_key, tenant_id=tenant_id)
            if cached:
                logger.debug(f"Cache hit for sentiment analysis")
                return cached
        
        # Analyze using Gateway
        prompt = f"Analyze the sentiment of this text: {text}\n\nRespond with JSON: {{'sentiment': 'positive|negative|neutral', 'score': 0.0-1.0}}"
        
        try:
            response = await self.gateway.generate_async(
                prompt=prompt,
                model="gpt-4",
                tenant_id=tenant_id,
            )
            
            # Parse response (simplified)
            result = {
                "sentiment": "positive",  # Parse from response
                "score": 0.85,
            }
            
            # Cache result
            if self.cache:
                self.cache.set(
                    cache_key,
                    result,
                    tenant_id=tenant_id,
                    ttl=3600,
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
            raise SentimentAnalysisError(f"Analysis failed: {e}") from e


# Factory function
def create_sentiment_analyzer(
    gateway: LiteLLMGateway,
    cache: Optional[CacheMechanism] = None,
    tenant_id: Optional[str] = None,
) -> SentimentAnalyzer:
    """Create SentimentAnalyzer instance."""
    return SentimentAnalyzer(
        gateway=gateway,
        cache=cache,
        tenant_id=tenant_id,
    )
```

### Example 2: Component Using Multiple Dependencies

```python
"""
Example: Document Summarizer Component

Uses Gateway for LLM, Database for storage, Cache for caching.
"""

class DocumentSummarizer:
    def __init__(
        self,
        gateway: LiteLLMGateway,
        db: DatabaseConnection,
        cache: Optional[CacheMechanism] = None,
    ):
        self.gateway = gateway
        self.db = db
        self.cache = cache
    
    async def summarize(
        self,
        document_id: str,
        tenant_id: str,
    ) -> str:
        """Summarize a document."""
        # Check cache
        cache_key = f"{tenant_id}:summary:{document_id}"
        if self.cache:
            cached = self.cache.get(cache_key, tenant_id=tenant_id)
            if cached:
                return cached
        
        # Load document from database
        doc = await self.db.execute_query(
            "SELECT content FROM documents WHERE id = %s AND tenant_id = %s",
            parameters=(document_id, tenant_id),
            tenant_id=tenant_id,
        )
        
        if not doc:
            raise ValueError("Document not found")
        
        # Generate summary using Gateway
        prompt = f"Summarize this document:\n\n{doc[0]['content']}"
        response = await self.gateway.generate_async(
            prompt=prompt,
            model="gpt-4",
            tenant_id=tenant_id,
        )
        
        summary = response.text
        
        # Cache summary
        if self.cache:
            self.cache.set(cache_key, summary, tenant_id=tenant_id, ttl=86400)
        
        # Save summary to database
        await self.db.execute_update(
            "UPDATE documents SET summary = %s WHERE id = %s AND tenant_id = %s",
            parameters=(summary, document_id, tenant_id),
            tenant_id=tenant_id,
        )
        
        return summary
```

---

## Testing Integration Points

### Unit Testing Component Integration

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.core.your_component import YourComponent
from src.core.litellm_gateway import LiteLLMGateway


@pytest.fixture
def mock_gateway():
    """Mock Gateway for testing."""
    gateway = Mock(spec=LiteLLMGateway)
    gateway.generate_async = AsyncMock(
        return_value=Mock(text="Test response")
    )
    return gateway


@pytest.fixture
def mock_cache():
    """Mock Cache for testing."""
    cache = Mock()
    cache.get = Mock(return_value=None)
    cache.set = Mock()
    return cache


@pytest.mark.asyncio
async def test_your_component_with_gateway(mock_gateway):
    """Test component using Gateway."""
    component = YourComponent(gateway=mock_gateway)
    result = await component.execute("test input", tenant_id="test_tenant")
    
    assert result is not None
    mock_gateway.generate_async.assert_called_once()


@pytest.mark.asyncio
async def test_your_component_with_cache(mock_gateway, mock_cache):
    """Test component using Cache."""
    component = YourComponent(gateway=mock_gateway, cache=mock_cache)
    
    # First call (cache miss)
    result1 = await component.execute("test", tenant_id="test_tenant")
    assert mock_gateway.generate_async.called
    
    # Second call (cache hit)
    mock_cache.get.return_value = {"result": "cached"}
    result2 = await component.execute("test", tenant_id="test_tenant")
    assert result2 == {"result": "cached"}
    # Gateway should not be called again
    assert mock_gateway.generate_async.call_count == 1
```

### Integration Testing

```python
@pytest.mark.integration
async def test_agent_with_rag_integration():
    """Test Agent and RAG integration."""
    # Setup real components
    gateway = create_gateway(api_keys={"openai": "test-key"})
    db = create_database(connection_string="postgresql://test")
    cache = create_cache(backend="memory")
    
    # Create RAG
    rag = create_rag_system(db, gateway, cache, tenant_id="test_tenant")
    
    # Ingest document
    await rag.ingest_document_async(
        title="Test Doc",
        content="This is a test document",
        tenant_id="test_tenant",
    )
    
    # Create Agent with RAG
    agent = create_agent("test_agent", "Test", gateway, cache=cache)
    
    # Agent queries RAG
    context = await rag.query("test document", tenant_id="test_tenant")
    assert context is not None
    
    # Agent uses context
    response = await agent.execute_task(
        f"Context: {context}\n\nQuestion: What is in the document?",
        tenant_id="test_tenant",
    )
    assert response is not None
```

---

## Best Practices

### 1. Dependency Injection

✅ **DO:**
```python
class YourComponent:
    def __init__(self, gateway: LiteLLMGateway):
        self.gateway = gateway  # Injected dependency
```

❌ **DON'T:**
```python
class YourComponent:
    def __init__(self):
        from ..litellm_gateway import create_gateway
        self.gateway = create_gateway()  # Hard dependency
```

### 2. Tenant Isolation

✅ **DO:**
```python
async def execute(self, data: str, tenant_id: str):
    cache_key = f"{tenant_id}:component:{hash(data)}"
    query = "SELECT * FROM table WHERE tenant_id = %s"
```

❌ **DON'T:**
```python
async def execute(self, data: str):
    cache_key = f"component:{hash(data)}"  # Missing tenant_id
    query = "SELECT * FROM table"  # Missing tenant filter
```

### 3. Error Handling

✅ **DO:**
```python
try:
    result = await self.gateway.generate_async(...)
except GatewayError as e:
    logger.error(f"Gateway error: {e}")
    raise YourComponentError(f"Execution failed: {e}") from e
```

❌ **DON'T:**
```python
try:
    result = await self.gateway.generate_async(...)
except Exception as e:
    pass  # Silent failure
```

### 4. Caching

✅ **DO:**
```python
if self.cache:
    cached = self.cache.get(key, tenant_id=tenant_id)
    if cached:
        return cached
```

❌ **DON'T:**
```python
cached = self.cache.get(key)  # Missing tenant_id
```

### 5. Logging

✅ **DO:**
```python
logger.info(
    "Component operation started",
    extra={"tenant_id": tenant_id, "operation": "execute"}
)
```

❌ **DON'T:**
```python
print(f"Operation started")  # No structured logging
```

---

## Troubleshooting Development Issues

### Issue 1: Component Not Finding Dependencies

**Problem:** `ImportError: cannot import name 'LiteLLMGateway'`

**Solution:**
```python
# Use relative imports
from ..litellm_gateway import LiteLLMGateway

# Or absolute imports
from src.core.litellm_gateway import LiteLLMGateway
```

### Issue 2: Tenant Isolation Not Working

**Problem:** Data from one tenant visible to another

**Solution:**
- Always include `tenant_id` in database queries
- Always include `tenant_id` in cache keys
- Validate `tenant_id` is not None

### Issue 3: Circular Dependencies

**Problem:** `ImportError: circular import`

**Solution:**
- Use dependency injection instead of direct imports
- Move shared code to a common module
- Use lazy imports if necessary

### Issue 4: Integration Tests Failing

**Problem:** Tests fail when components interact

**Solution:**
- Mock external dependencies (Gateway, Database)
- Use test containers for integration tests
- Ensure proper cleanup between tests

---

## Additional Resources

### Documentation
- [Onboarding Guide](ONBOARDING_GUIDE.md) - For understanding SDK usage
- [SDK Architecture](../architecture/SDK_ARCHITECTURE.md) - For architecture details
- [Component READMEs](../components/) - For component-specific docs

### Code Examples
- [Basic Usage Examples](../../examples/basic_usage/) - Component usage examples
- [Integration Examples](../../examples/integration/) - Multi-component examples
- [FaaS Examples](../../examples/faas/) - FaaS service examples

### Testing
- [Unit Tests](../../src/tests/unit_tests/) - Component unit tests
- [Integration Tests](../../src/tests/integration_tests/) - Integration tests

---

## Summary

This guide provides:

1. ✅ **Component Development**: How to create new components
2. ✅ **Integration Patterns**: How components integrate
3. ✅ **Code Examples**: Real implementation examples
4. ✅ **Development Workflows**: Step-by-step guides
5. ✅ **Testing**: How to test components and integrations
6. ✅ **Best Practices**: Do's and don'ts

**Next Steps:**
- Read [Onboarding Guide](ONBOARDING_GUIDE.md) for SDK usage
- Study existing components for patterns
- Start with simple components and build up
- Write tests as you develop
- Document as you go

**Welcome to SDK development! 🚀**

