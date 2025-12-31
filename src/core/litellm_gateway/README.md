# LiteLLM Gateway

## Overview

The LiteLLM Gateway serves as the central AI operations hub for the entire SDK. It provides a unified interface for interacting with multiple Large Language Model (LLM) providers, abstracting away provider-specific complexities and enabling seamless integration across all AI components.

## Purpose and Functionality

The gateway acts as a critical middleware layer that standardizes how the SDK interacts with various LLM providers including OpenAI, Anthropic, Google, Cohere, and others. It handles provider-specific API differences, manages authentication, implements retry logic and fallback mechanisms, and provides consistent response formatting across all providers.

The gateway supports both synchronous and asynchronous operations, enabling efficient handling of concurrent requests. It also provides streaming capabilities for real-time response generation, which is essential for interactive applications.

## Connection to Other Components

### Integration with Agno Agent Framework

The **Agno Agent Framework** (`src/core/agno_agent_framework/`) depends directly on the LiteLLM Gateway for all LLM operations. When agents need to perform reasoning, generate responses, or analyze data, they call the gateway's `generate()` or `generate_async()` methods. The gateway instance is injected into each agent during initialization, creating a clear dependency relationship.

### Integration with RAG System

The **RAG System** (`src/core/rag/`) uses the gateway in two critical ways:
1. **Embedding Generation**: The RAG system's retriever component uses the gateway's `embed()` method to generate vector embeddings for both documents during ingestion and queries during retrieval.
2. **Response Generation**: After retrieving relevant documents, the RAG generator uses the gateway's `generate()` method to create context-aware responses using the retrieved information.

### Integration with Prompt Context Management

The **Prompt Context Management** component (`src/core/prompt_context_management/`) works closely with the gateway by providing formatted prompts and context. The gateway receives these prepared prompts and executes them against the configured LLM providers, returning structured responses that can be further processed.

### Integration with Evaluation & Observability

The **Evaluation & Observability** component (`src/core/evaluation_observability/`) monitors all gateway operations. It tracks metrics such as token usage, response times, error rates, and costs. The gateway emits events that the observability system captures for logging, tracing, and performance analysis.

### Integration with API Backend Services

The **API Backend Services** (`src/core/api_backend_services/`) expose the gateway's functionality through RESTful endpoints. When API requests come in for text generation or embeddings, the backend services route them to the gateway, which handles the actual LLM interactions.

## Libraries Utilized

- **litellm**: The core library that provides unified access to multiple LLM providers. It handles provider-specific API calls, authentication, and response formatting.
- **pydantic**: Used for data validation and configuration management, ensuring type safety and proper validation of gateway configurations and responses.
- **httpx**: Provides async HTTP client capabilities for efficient concurrent API requests to LLM providers.

## Key Methods and Their Roles

### `generate()` and `generate_async()`

These methods handle text generation requests. They accept prompts, model specifications, and various generation parameters. The methods abstract away provider differences, automatically handle retries and fallbacks, and return standardized response objects that other components can consume.

### `embed()` and `embed_async()`

These methods generate vector embeddings for text inputs. They are primarily used by the RAG system for document indexing and query processing. The methods support batch processing and return normalized embedding vectors.

### `generate_stream()` and `generate_stream_async()`

These methods provide streaming capabilities, allowing real-time token generation. They return async iterators that yield text chunks as they're generated, enabling interactive user experiences.

## Error Handling

The gateway implements comprehensive error handling for various failure scenarios:

- **Provider Failures**: When a primary provider fails, the gateway automatically attempts fallback providers if configured.
- **Rate Limiting**: The gateway handles rate limit errors by implementing exponential backoff and retry logic.
- **Network Errors**: Transient network issues trigger automatic retries with configurable retry counts and delays.
- **Invalid Responses**: Malformed or invalid responses from providers are caught and converted to standardized error responses.

All errors are logged and can be monitored through the Evaluation & Observability component.

## Configuration and Setup

The gateway is configured through the `GatewayConfig` class, which allows specification of:
- Model lists and routing rules
- Fallback provider chains
- Timeout and retry configurations
- Provider-specific API keys and endpoints

Configuration can be provided programmatically or loaded from environment variables, enabling flexible deployment scenarios.

## Best Practices

1. **Connection Reuse**: The gateway maintains persistent connections to providers when possible, reducing latency and overhead.
2. **Caching**: Responses can be cached through the Cache Mechanism component to reduce costs and improve response times.
3. **Monitoring**: All gateway operations should be monitored through the observability system to track usage, costs, and performance.
4. **Error Handling**: Components using the gateway should implement appropriate error handling for gateway failures.
5. **Resource Management**: The gateway should be properly initialized and closed to ensure clean resource management.
