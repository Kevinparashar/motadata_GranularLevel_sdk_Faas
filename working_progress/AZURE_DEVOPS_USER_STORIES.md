# Azure DevOps User Stories for Python SDK

**Project:** NextGen  
**Area:** NextGen  
**Work Item Type:** User Story  
**Purpose:** Create comprehensive User Stories for PR-based development - One story per component

**Created:** 2026-01-06 15:42:21

---

## User Stories Overview

**1. Agent Framework — Complete Multi-Agent System with Orchestration**  
**2. RAG System — Complete Retrieval-Augmented Generation with Batch Processing**  
**3. LiteLLM Gateway — Complete Multi-Provider Gateway with Streaming and Function Calling**  
**4. Prompt Context Management — Complete Template, Context Window, and History Management**

---

## User Stories Structure for PR Reviews

Each User Story is designed to:
- **Cover Complete Component**: One User Story = One complete component implementation
- **PR-Ready**: Clear scope, files, and acceptance criteria for code review
- **Testable**: Comprehensive test requirements
- **Complete**: Can be merged as a single PR per component

---

## 1. Agno Agent Framework Component

### User Story 1: Complete Agent Framework Implementation

**Title:**
```
User Story: Agent Framework — Complete Multi-Agent System with Orchestration
```

**Description:**
```
As a Python developer
I want a complete agent framework with multi-agent orchestration, memory, tools, and plugins
So that I can build autonomous AI agents that can execute tasks, coordinate with each other, and maintain context

**PR Scope:**
This User Story covers the complete Agno Agent Framework implementation including:
- Base Agent class with lifecycle management
- AgentManager for multi-agent coordination
- Memory system (short-term, long-term, episodic, semantic) with persistence
- Session management for conversation tracking
- Tool registry and execution system
- Plugin system for extensibility
- Multi-agent orchestration with workflow pipelines
- Error handling and retry logic

**Files to Create/Modify:**
- src/core/agno_agent_framework/agent.py (Agent, AgentManager, models)
- src/core/agno_agent_framework/memory.py (AgentMemory, MemoryItem, persistence)
- src/core/agno_agent_framework/session.py (AgentSession, SessionManager)
- src/core/agno_agent_framework/tools.py (Tool, ToolRegistry, ToolExecutor)
- src/core/agno_agent_framework/plugins.py (AgentPlugin, PluginManager)
- src/core/agno_agent_framework/orchestration.py (WorkflowPipeline, AgentOrchestrator, coordination patterns)
- src/core/agno_agent_framework/__init__.py (update exports)
- src/tests/unit_tests/test_agent.py (comprehensive tests)
- examples/integration/multi_agent_orchestration.py (example usage)

**Dependencies:**
- Requires: LiteLLM Gateway (for agent reasoning)
- Optional: PostgreSQL Database (for persistence)
```

**Acceptance Criteria:**
```
1. Agent Class:
   - Agent can be instantiated with agent_id, name, description, gateway
   - Agent supports capabilities via add_capability()
   - Agent can execute tasks via execute_task() with retry logic
   - Agent status is tracked (IDLE, RUNNING, PAUSED, STOPPED, ERROR)
   - AgentCapability, AgentTask, AgentMessage Pydantic models are defined
   - Agent integrates with memory, session, tools, and plugins

2. AgentManager Class:
   - AgentManager can register agents via register_agent()
   - AgentManager can retrieve agents by ID via get_agent()
   - AgentManager can list all agents via list_agents()
   - AgentManager can find agents by capability via find_agents_by_capability()
   - AgentManager can broadcast messages to all agents
   - AgentManager can route messages between specific agents

3. Memory System:
   - AgentMemory class supports all memory types (SHORT_TERM, LONG_TERM, EPISODIC, SEMANTIC)
   - Memory can be stored with store(content, memory_type, importance, metadata, tags)
   - Memory can be retrieved with retrieve(query, memory_type, tags, limit)
   - Memory consolidation (short-term to long-term) works via consolidate()
   - Memory persistence to disk (JSON) works via persistence_path parameter
   - Memory loads from disk on initialization if file exists
   - Memory trimming works when max limits are exceeded
   - Memory statistics available via get_stats()

4. Session Management:
   - AgentSession class can be created with session_id, agent_id
   - Sessions can store messages via add_message()
   - Sessions track status (ACTIVE, PAUSED, CLOSED, EXPIRED)
   - SessionManager can create, retrieve, and manage sessions
   - Agent can attach to a session
   - Session history is accessible

5. Tool Registry and Execution:
   - Tool class can be defined with name, description, parameters, function
   - ToolRegistry can register and retrieve tools
   - ToolExecutor can execute tools with parameters
   - Agent can register tools via tool registry
   - Agent can execute tools during task execution
   - Tool execution errors are handled gracefully

6. Plugin System:
   - AgentPlugin base class can be extended
   - PluginManager can register, enable, disable plugins
   - Plugins can hook into agent lifecycle (before_task, after_task, on_error)
   - Agent can load plugins via PluginManager
   - Plugin execution doesn't break agent if plugin fails

7. Multi-Agent Orchestration:
   - WorkflowPipeline can be created with steps and dependencies
   - Workflow steps can have dependencies (depends_on parameter)
   - WorkflowPipeline executes steps in correct order (sequential/parallel)
   - AgentOrchestrator can create and execute workflows
   - Task delegation works via delegate_task()
   - Task chaining works via chain_tasks()
   - Coordination patterns work (leader-follower, peer-to-peer, pipeline, broadcast)

8. Error Handling and Retry Logic:
   - Agent accepts max_retries and retry_delay parameters
   - Task execution retries on failure up to max_retries
   - Retry delay is applied between retries
   - Agent status is set to ERROR on final failure
   - Task results are stored to memory if auto_persist_memory is enabled

9. Integration:
   - All components integrate seamlessly (Agent uses memory, session, tools, plugins)
   - AgentManager coordinates multiple agents
   - Orchestrator manages workflows with multiple agents
   - Example code demonstrates complete usage

10. Testing:
    - Unit tests achieve 80%+ coverage for all classes
    - Integration tests verify end-to-end workflows
    - All tests pass
    - Code follows PEP 8 with type hints and docstrings
```

**Tags:** `Agent Framework`, `Multi-Agent`, `Orchestration`, `Python`, `SDK`, `PR-Ready`

**Story Points:** 21

**Priority:** 1

---

## 2. RAG System Component

### User Story 2: Complete RAG System Implementation

**Title:**
```
User Story: RAG System — Complete Retrieval-Augmented Generation with Batch Processing
```

**Description:**
```
As a Python developer
I want a complete RAG system that ingests documents, retrieves relevant context, and generates context-aware responses
So that I can build document Q&A applications with efficient batch processing

**PR Scope:**
This User Story covers the complete RAG System implementation including:
- Document processor with multiple chunking strategies
- Retriever with vector similarity search
- Generator for context-aware response generation
- Complete RAG system integration
- Batch processing for document ingestion and embeddings

**Files to Create/Modify:**
- src/core/rag/document_processor.py (DocumentProcessor, DocumentChunk, chunking strategies)
- src/core/rag/retriever.py (Retriever, vector similarity search)
- src/core/rag/generator.py (RAGGenerator, context building)
- src/core/rag/rag_system.py (RAGSystem, complete integration, batch methods)
- src/core/rag/__init__.py (update exports)
- src/tests/unit_tests/test_rag.py (comprehensive tests)
- examples/integration/rag_example.py (example usage)

**Dependencies:**
- Requires: LiteLLM Gateway (for embeddings and generation)
- Requires: PostgreSQL Database with VectorOperations (for vector storage)
```

**Acceptance Criteria:**
```
1. Document Processor:
   - DocumentProcessor can be instantiated with chunk_size, chunk_overlap, strategy
   - chunk_document() method splits documents into chunks
   - Fixed-size chunking works correctly
   - Sentence-based chunking works correctly
   - Paragraph-based chunking works correctly
   - Chunks maintain metadata and document_id
   - Chunk IDs are generated uniquely

2. Retriever:
   - Retriever can be instantiated with vector_ops, gateway, embedding_model
   - retrieve() method converts query to embedding
   - retrieve() performs similarity search via VectorOperations
   - retrieve() filters results by threshold
   - retrieve() returns top_k documents
   - Retrieved documents include similarity scores
   - retrieve_async() works asynchronously

3. Generator:
   - RAGGenerator can be instantiated with gateway and model
   - generate() method builds context from retrieved documents
   - generate() creates prompt with query and context
   - generate() calls gateway.generate() with prompt
   - generate_async() works asynchronously
   - Context is properly formatted for LLM

4. RAG System Integration:
   - RAGSystem integrates DocumentProcessor, Retriever, Generator
   - ingest_document() processes document and chunks it
   - ingest_document() generates embeddings in batch (all chunks at once)
   - ingest_document() batch inserts embeddings to database
   - ingest_document() handles embedding failures gracefully (skip failed chunks)
   - query() retrieves documents and generates answer
   - query_async() works asynchronously
   - Error handling returns structured error responses

5. Batch Processing:
   - ingest_document_async() processes documents asynchronously
   - ingest_documents_batch() processes multiple documents synchronously
   - ingest_documents_batch_async() processes multiple documents concurrently
   - Batch methods use batch embedding generation (optimized)
   - Batch methods handle errors gracefully (continue on failure)
   - Batch methods return list of document IDs
   - Batch processing is 50%+ faster than individual processing

6. Integration:
   - All components integrate seamlessly
   - RAG system works with PostgreSQL vector database
   - RAG system works with LiteLLM Gateway
   - Example code demonstrates complete usage

8. Testing:
   - Unit tests achieve 80%+ coverage for all classes
   - Integration tests verify end-to-end RAG workflow
   - Performance tests verify batch processing improvements
   - All tests pass
   - Code follows PEP 8 with type hints and docstrings
```

**Tags:** `RAG`, `Document Processing`, `Vector Search`, `Batch Processing`, `Python`, `SDK`, `PR-Ready`

**Story Points:** 21

**Priority:** 1

---

## 3. LiteLLM Gateway Component

### User Story 3: Complete LiteLLM Gateway Implementation

**Title:**
```
User Story: LiteLLM Gateway — Complete Multi-Provider Gateway with Streaming and Function Calling
```

**Description:**
```
As a Python developer
I want a unified gateway for multiple LLM providers with streaming, embeddings, and function calling
So that I can switch between providers and use advanced LLM features without changing code

**PR Scope:**
This User Story covers the complete LiteLLM Gateway implementation including:
- Base gateway with multi-provider support (OpenAI, Anthropic, Google, etc.)
- Text generation (synchronous and asynchronous)
- Streaming text generation
- Embeddings generation with batch support
- Function calling support
- Error handling and retry logic
- Model routing and fallback mechanisms

**Files to Create/Modify:**
- src/core/litellm_gateway/gateway.py (LiteLLMGateway, GatewayConfig, all methods)
- src/core/litellm_gateway/__init__.py (update exports)
- src/tests/unit_tests/test_litellm_gateway.py (comprehensive tests)
- examples/integration/gateway_example.py (example usage)

**Dependencies:**
- Requires: litellm library
- Optional: Evaluation & Observability (for metrics tracking)
```

**Acceptance Criteria:**
```
1. Base Gateway:
   - LiteLLMGateway can be instantiated with optional router/config
   - Gateway supports OpenAI provider
   - Gateway supports Anthropic provider
   - Gateway supports Google provider
   - Gateway can switch between providers
   - Gateway handles provider-specific configurations
   - GatewayConfig model is properly defined

2. Text Generation (Sync & Async):
   - generate() method accepts prompt, model, and optional parameters
   - generate() returns GenerateResponse with text, model, usage, finish_reason
   - generate_async() works asynchronously with same interface
   - Both methods support all configured providers
   - Both methods support messages parameter (chat format)
   - Error handling returns structured errors

3. Streaming Generation:
   - stream() method accepts prompt, model, and returns generator
   - stream() yields text chunks as they're generated
   - stream_async() works asynchronously with async generator
   - Streaming works with all supported providers
   - Stream can be consumed iteratively
   - Streaming handles errors gracefully

4. Embeddings Generation:
   - embed() method accepts texts (list), model, and returns EmbedResponse
   - embed() supports batch processing (multiple texts in one call)
   - embed() returns list of embeddings matching input texts
   - embed_async() works asynchronously
   - EmbedResponse includes embeddings, model, usage
   - Batch embedding is more efficient than individual calls

5. Function Calling:
   - generate() accepts functions parameter (list of function definitions)
   - generate() returns function calls in response
   - Function calls include function name and arguments
   - generate() can accept function results for subsequent calls
   - Function calling works with supported providers
   - Function calling supports async operations

6. Error Handling and Retries:
   - Gateway retries on transient failures (network errors, rate limits)
   - Gateway handles provider-specific errors correctly
   - Gateway returns structured error responses
   - Retry logic is configurable via GatewayConfig
   - Gateway doesn't retry on permanent failures
   - Timeout handling works correctly

7. Model Routing and Fallback:
   - Gateway supports model routing via LiteLLM Router
   - Fallback mechanisms work when primary model fails
   - Model selection based on availability, cost, latency
   - Router configuration is properly handled

8. Response Models:
   - GenerateResponse model includes all necessary fields
   - EmbedResponse model includes all necessary fields
   - Response models are properly validated
   - Raw responses are accessible when needed

9. Integration:
   - Gateway integrates with other SDK components
   - Gateway can be used by Agent Framework
   - Gateway can be used by RAG System
   - Example code demonstrates complete usage

10. Testing:
    - Unit tests achieve 80%+ coverage for all methods
    - Integration tests verify provider connectivity (mocked)
    - Streaming tests verify chunk generation
    - Function calling tests verify tool integration
    - Error handling tests verify retry logic
    - All tests pass
    - Code follows PEP 8 with type hints and docstrings
```

**Tags:** `Gateway`, `LiteLLM`, `Multi-Provider`, `Streaming`, `Function Calling`, `Python`, `SDK`, `PR-Ready`

**Story Points:** 21

**Priority:** 1

---

## 4. Prompt Context Management Component

### User Story 4: Complete Prompt Context Management Implementation

**Title:**
```
User Story: Prompt Context Management — Complete Template, Context Window, and History Management
```

**Description:**
```
As a Python developer
I want a complete prompt management system with templates, context window handling, and history tracking
So that I can manage prompts effectively and ensure they fit within LLM token limits

**PR Scope:**
This User Story covers the complete Prompt Context Management implementation including:
- Prompt template system with versioning
- Context window handling and token estimation
- Prompt history tracking
- PII redaction utilities
- Context building from multiple sources

**Files to Create/Modify:**
- src/core/prompt_context_management/prompt_manager.py (all classes: PromptTemplate, PromptStore, ContextWindowManager, PromptContextManager)
- src/core/prompt_context_management/__init__.py (update exports)
- src/tests/unit_tests/test_prompt_context.py (comprehensive tests)
- examples/integration/prompt_example.py (example usage)

**Dependencies:**
- None (standalone component, used by other components)
```

**Acceptance Criteria:**
```
1. Prompt Template System:
   - PromptTemplate can be created with name, version, content, metadata
   - PromptStore can store multiple versions of same template
   - PromptStore can retrieve template by name and version
   - PromptStore returns latest version if version not specified
   - Template rendering supports variable substitution (Python format-style)
   - Templates can be updated and versioned
   - Template metadata is preserved

2. Context Window Handling:
   - ContextWindowManager can be instantiated with max_tokens, safety_margin
   - estimate_tokens() estimates token count for text (simple heuristic)
   - truncate() truncates text to fit within token limit
   - build_context() builds context from messages within token limit
   - Safety margin is applied correctly
   - Context prioritization works (most recent messages prioritized)
   - Context formatting is optimized for LLM consumption

3. Prompt History Management:
   - PromptContextManager tracks prompt history
   - record_history() adds prompts to history
   - build_context_with_history() builds context from recent history
   - History respects context window limits
   - History can be used to build conversation context
   - History can be cleared or limited

4. PII Redaction:
   - strip_sensitive() method redacts patterns from text
   - Default patterns include API keys and emails
   - Custom patterns can be provided
   - Redacted text replaces sensitive data with [REDACTED]
   - Redaction doesn't break text structure

5. Context Building:
   - build_context_with_history() combines history with new message
   - Context is properly formatted for LLM
   - Context respects token limits
   - Context prioritization works correctly

6. Integration:
   - PromptContextManager integrates all features
   - render() method combines template rendering with context building
   - add_template() and record_history() work together
   - truncate_prompt() ensures prompts fit within limits
   - Example code demonstrates complete usage

7. Testing:
   - Unit tests achieve 80%+ coverage for all classes
   - Template versioning tests verify multiple versions
   - Context window tests verify token limits
   - History tests verify context building
   - PII redaction tests verify pattern matching
   - All tests pass
   - Code follows PEP 8 with type hints and docstrings
```

**Tags:** `Prompt Management`, `Templates`, `Context Window`, `History`, `PII`, `Python`, `SDK`, `PR-Ready`

**Story Points:** 13

**Priority:** 1

---

## Summary: User Stories for PR Reviews

### Total User Stories: 4 (One per Component)

**1. Agno Agent Framework:** Complete multi-agent system with orchestration  
**2. RAG System:** Complete retrieval-augmented generation with batch processing  
**3. LiteLLM Gateway:** Complete multi-provider gateway with streaming and function calling  
**4. Prompt Context Management:** Complete template, context window, and history management

### PR Workflow for Each User Story:

1. **Create Branch:** `git checkout -b feature/user-story-1-agent-framework`
2. **Implement:** Complete component implementation per User Story
3. **Test:** Write comprehensive tests, ensure 80%+ coverage
4. **Commit:** `git commit -m "feat: implement complete agent framework (User Story 1)"`
5. **Create PR:** Link PR to User Story in Azure DevOps
6. **Review:** Code review against all Acceptance Criteria
7. **Merge:** After approval and all tests pass

### Benefits:
- ✅ Each User Story = One complete component = One focused PR
- ✅ Clear scope for reviewers (entire component)
- ✅ Easy to track progress (component-level)
- ✅ Independent merges (each component is complete)
- ✅ Comprehensive acceptance criteria for thorough testing
- ✅ Production-ready components from the start

---

**Document Created:** Current  
**Use:** Copy each User Story to Azure DevOps as a separate work item
