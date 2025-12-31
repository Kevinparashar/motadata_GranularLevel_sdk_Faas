# Component Dependencies and Build Order

## Overview

This document outlines the dependencies between SDK components and provides a recommended build order for development. Understanding component dependencies is crucial for parallel development and integration planning.

## Dependency Visualization

### Layer-Based Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌──────────────────┐          ┌──────────────────┐        │
│  │   API Backend    │          │       RAG        │        │
│  └────────┬─────────┘          └────────┬─────────┘        │
│           │                              │                  │
└───────────┼──────────────────────────────┼──────────────────┘
            │                              │
┌───────────┼──────────────────────────────┼──────────────────┐
│           │      Core Layer              │                  │
│  ┌────────▼─────────┐  ┌──────────────┐ │  ┌──────────────┐│
│  │      Agent       │  │    Cache     │ │  │   Prompt     ││
│  └────────┬─────────┘  └──────┬───────┘ │  │  Context    ││
│           │                    │         │  └──────┬───────┘│
└───────────┼────────────────────┼─────────┼─────────┼────────┘
            │                    │         │         │
┌───────────┼────────────────────┼─────────┼─────────┼────────┐
│           │  Infrastructure   │         │         │        │
│  ┌────────▼─────────┐  ┌──────▼───────┐ │  ┌─────▼──────┐│
│  │ LiteLLM Gateway  │  │ Connectivity │ │  │ PostgreSQL ││
│  └────────┬─────────┘  └──────┬───────┘ │  │  Database   ││
│           │                    │         │  └─────┬──────┘│
└───────────┼────────────────────┼─────────┼─────────┼────────┘
            │                    │         │         │
┌───────────┼────────────────────┼─────────┼─────────┼────────┐
│           │   Foundation Layer  │         │         │        │
│  ┌────────▼─────────┐  ┌────────▼───────┐ │         │        │
│  │  Observability   │  │ Pool Impl.     │ │         │        │
│  └──────────────────┘  └────────────────┘ │         │        │
└──────────────────────────────────────────────────────────────┘
```

## Dependency Matrix

| Component | Direct Dependencies | Indirect Dependencies | Required By |
|-----------|-------------------|---------------------|-------------|
| **Evaluation & Observability** | None | None | All components |
| **Pool Implementation** | None | None | Connectivity, PostgreSQL Database |
| **Connectivity** | Pool Implementation, Observability | None | API Backend |
| **PostgreSQL Database** | Observability | None | RAG, Pool Implementation |
| **LiteLLM Gateway** | Observability, Cache | None | Agent, RAG, API Backend |
| **Cache** | Gateway, RAG | Observability | LiteLLM Gateway |
| **Agent** | LiteLLM Gateway, Observability | Cache | API Backend, Prompt Context Management |
| **Prompt Context Management** | Agent, Observability | LiteLLM Gateway, Cache | API Backend |
| **RAG** | PostgreSQL Database, LiteLLM Gateway | Observability, Cache | API Backend, Cache |
| **API Backend** | Agent, Gateway, RAG | All other components | None |

## Build 


These components have no dependencies and can be developed in parallel:

1. **Evaluation & Observability** (src/core/evaluation_observability/)
   - Priority: **HIGH** - Required by all other components
   - Can start: Immediately
   - Blocking: All other components

2. **Pool Implementation** (pool_implementation/)
   - Priority: **MEDIUM** - Required by Connectivity and Database
   - Can start: Immediately
   - Blocking: Connectivity, Database connection pooling

### Infrastructure Components

These components depend only on foundation components:

3. **PostgreSQL Database** (src/core/postgresql_database/)
   - Dependencies: Observability
   - Priority: **HIGH** - Required by RAG
   - Can start: After Observability
   - Blocking: RAG

4. **Connectivity** (connectivity_clients/)
   - Dependencies: Pool Implementation, Observability
   - Priority: **MEDIUM** - Required by API Backend
   - Can start: After Pool Implementation and Observability
   - Blocking: API Backend

5. **LiteLLM Gateway** (src/core/litellm_gateway/)
   - Dependencies: Observability, Cache (optional)
   - Priority: **HIGH** - Required by Agent, RAG, API Backend
   - Can start: After Observability (Cache can be added later)
   - Blocking: Agent, RAG, API Backend

### Core Components

These components depend on infrastructure components:

6. **Cache** (src/core/cache_mechanism/)
   - Dependencies: Gateway, RAG
   - Priority: **MEDIUM** - Enhances Gateway performance
   - Can start: After Gateway (can work without RAG initially)
   - Blocking: Gateway optimization

7. **Agent** (src/core/agno_agent_framework/)
   - Dependencies: LiteLLM Gateway, Observability
   - Priority: **HIGH** - Core functionality
   - Can start: After Gateway and Observability
   - Blocking: API Backend, Prompt Context Management

8. **Prompt Context Management** (src/core/prompt_context_management/)
   - Dependencies: Agent, Observability
   - Priority: **MEDIUM** - Enhances Agent functionality
   - Can start: After Agent and Observability
   - Blocking: API Backend

### Application Layer Components

These components depend on multiple core and infrastructure components:

9. **RAG** (src/core/rag/)
   - Dependencies: PostgreSQL Database, LiteLLM Gateway
   - Priority: **HIGH** - Core functionality
   - Can start: After Database and Gateway
   - Blocking: API Backend, Cache

10. **API Backend** (src/core/api_backend_services/)
    - Dependencies: Agent, Gateway, RAG
    - Priority: **HIGH** - User-facing interface
    - Can start: After Agent, Gateway, and RAG
    - Blocking: None (final component)


## Dependency Notes

### Circular Dependencies
- **Cache ↔ Gateway**: Cache depends on Gateway for response caching, Gateway can optionally use Cache for optimization. This is a soft dependency - Gateway can work without Cache initially.

### Optional Dependencies
- **Gateway → Cache**: Gateway can function without Cache, but Cache enhances performance
- **Pool Implementation → Database**: Database can work without Pool Implementation, but Pool enhances connection management

### Interface Dependencies
- All components that implement interfaces (Agent, Database, Cache) depend on `interfaces.py` being defined first
- Interface definitions should be completed before any component implementation begins

## Integration Points

- **Observability**: Integrates with ALL components
- **API Backend**: Integrates with Agent, Gateway, and RAG
- **Gateway**: Integrates with Agent, RAG, and API Backend

- **Agent**: Integrates with Gateway, Observability, and Prompt Context Management
- **RAG**: Integrates with Database, Gateway, and Cache
- **Cache**: Integrates with Gateway and RAG

- **Connectivity**: Integrates with Pool Implementation and Observability
- **Pool Implementation**: Integrates with Database and Connectivity
- **PostgreSQL Database**: Integrates with RAG and Observability
- **Prompt Context Management**: Integrates with Agent and Observability

 ### Dependencies
- **API Backend**: Depends on 3 major components (Agent, Gateway, RAG)
- **Agent**: Depends on Gateway (critical path)
- **RAG**: Depends on Database and Gateway (critical path)
- **Cache**: Depends on Gateway and RAG
- **Prompt Context Management**: Depends on Agent
- **Connectivity**: Depends on Pool Implementation
- **Evaluation & Observability**: No dependencies
- **Pool Implementation**: No dependencies
- **PostgreSQL Database**: Only depends on Observability
- **LiteLLM Gateway**: Only depends on Observability


