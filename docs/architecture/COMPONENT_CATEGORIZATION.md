# MOTADATA - COMPONENT CATEGORIZATION

This document explains how SDK components are grouped, so you can quickly pick the right module for your use case.

## Categories

### 1) Core AI components (`src/core/`)

- **LiteLLM Gateway**: all model calls (generate, embed, streaming)
- **Agent Framework**: orchestration, tools, workflows, memory
- **RAG System**: ingest docs, retrieve context, generate answers
- **Prompt Context Management**: templates and context window
- **Cache Mechanism**: caching for cost and latency reduction
- **PostgreSQL Database**: DB + vector ops + index management
- **Machine Learning**: ML framework, MLOps, serving

### 2) FaaS services (`src/faas/`)

Optional REST services that wrap the core components for deployment.

### 3) Docs and examples

- `docs/`: architecture, components, troubleshooting
- `examples/`: runnable examples and use cases

## How to decide quickly

- Need a single LLM call → use **Gateway**
- Need multi-step orchestration → use **Agents**
- Need document Q&A → use **RAG**
- Need stable, repeated outputs → enable **Cache**


