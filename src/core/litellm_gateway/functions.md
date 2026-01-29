# Motadata LiteLLM Gateway Functions Documentation

## Overview

The `functions.py` file provides high-level factory functions, convenience functions, and utilities for the LiteLLM Gateway. These functions simplify gateway creation, configuration, and common operations, making it easier for developers to work with the gateway without directly instantiating the `LiteLLMGateway` class or managing complex configurations.

**Primary Functionality:**
- Factory functions for creating gateways with different configurations
- Convenience functions for common LLM operations (text generation, embeddings)
- Configuration helpers for setting up multi-provider gateways
- Batch processing utilities for handling multiple requests
- Streaming text generation helpers

## Code Explanation

### Function Categories

The file is organized into several categories:

#### 1. Factory Functions
Factory functions create and configure gateways:

- **`create_gateway()`**: Create gateway with simplified configuration
- **`configure_gateway()`**: Create GatewayConfig with specified settings

#### 2. Text Generation Functions
High-level functions for text generation:

- **`generate_text()`**: Synchronous text generation
- **`generate_text_async()`**: Asynchronous text generation
- **`stream_text()`**: Streaming text generation

#### 3. Embedding Functions
Functions for generating embeddings:

- **`generate_embeddings()`**: Synchronous embedding generation
- **`generate_embeddings_async()`**: Asynchronous embedding generation

#### 4. Batch Processing Functions
Utilities for batch operations:

- **`batch_generate()`**: Batch text generation

### Key Functions

#### `create_gateway(providers, default_model, api_keys, **kwargs) -> LiteLLMGateway`
Creates a LiteLLM Gateway instance with validation and helpful error messages.

**Parameters:**
- `providers`: List of provider names (e.g., ['openai', 'anthropic'])
- `default_model`: Default model to use (e.g., 'gpt-4', 'claude-3-opus')
- `api_keys`: Dictionary mapping provider names to API keys
- `fallbacks`: List of fallback models to try if primary fails
- `timeout`: Request timeout in seconds (default: 60.0)
- `max_retries`: Maximum number of retries (default: 3)
- `retry_delay`: Delay between retries in seconds (default: 1.0)
- `**kwargs`: Additional configuration options

**Returns:** Configured `LiteLLMGateway` instance

**Raises:**
- `ConfigurationError`: If configuration is invalid with helpful suggestions

**Example:**
```python
gateway = create_gateway(
    providers=['openai'],
    default_model='gpt-4',
    api_keys={'openai': 'sk-...'}
)
```

**Validation:**
- Validates timeout, max_retries, retry_delay ranges
- Validates model name format
- Checks for API keys with helpful suggestions
- Provides clear error messages

#### `configure_gateway(model_list, fallbacks, timeout, max_retries, retry_delay) -> GatewayConfig`
Creates a GatewayConfig with specified settings.

**Parameters:**
- `model_list`: List of model configurations
- `fallbacks`: List of fallback models
- `timeout`: Request timeout (default: 60.0)
- `max_retries`: Maximum retries (default: 3)
- `retry_delay`: Retry delay (default: 1.0)

**Returns:** `GatewayConfig` instance

**Example:**
```python
config = configure_gateway(
    model_list=[...],
    fallbacks=['gpt-3.5-turbo'],
    timeout=120.0
)
gateway = LiteLLMGateway(config=config)
```

#### `generate_text(gateway, prompt, model=None, **kwargs) -> str`
Synchronous text generation convenience function.

**Parameters:**
- `gateway`: LiteLLMGateway instance
- `prompt`: Input prompt text
- `model`: Optional model name
- `**kwargs`: Additional generation parameters

**Returns:** Generated text string

**Example:**
```python
text = generate_text(gateway, "Hello, world!", model="gpt-4")
```

#### `async def generate_text_async(gateway, prompt, model=None, **kwargs) -> str`
Asynchronous text generation convenience function.

**Parameters:** Same as `generate_text()`

**Returns:** Generated text string

**Example:**
```python
text = await generate_text_async(gateway, "Hello, world!")
```

#### `stream_text(gateway, prompt, model=None, **kwargs) -> Iterator[str]`
Streaming text generation convenience function.

**Parameters:** Same as `generate_text()`

**Returns:** Iterator yielding text chunks

**Example:**
```python
for chunk in stream_text(gateway, "Tell me a story"):
    print(chunk, end="", flush=True)
```

#### `generate_embeddings(gateway, text, model=None, **kwargs) -> List[List[float]]`
Synchronous embedding generation convenience function.

**Parameters:**
- `gateway`: LiteLLMGateway instance
- `text`: Text to embed (string or list of strings)
- `model`: Optional embedding model name
- `**kwargs`: Additional parameters

**Returns:** List of embedding vectors

**Example:**
```python
embeddings = generate_embeddings(
    gateway,
    "This is a sample text",
    model="text-embedding-ada-002"
)
```

#### `async def generate_embeddings_async(gateway, text, model=None, **kwargs) -> List[List[float]]`
Asynchronous embedding generation convenience function.

**Parameters:** Same as `generate_embeddings()`

**Returns:** List of embedding vectors

#### `batch_generate(gateway, prompts, model=None, **kwargs) -> List[str]`
Batch text generation for multiple prompts.

**Parameters:**
- `gateway`: LiteLLMGateway instance
- `prompts`: List of prompt strings
- `model`: Optional model name
- `**kwargs`: Additional generation parameters

**Returns:** List of generated texts

**Example:**
```python
prompts = ["What is AI?", "What is ML?", "What is NLP?"]
results = batch_generate(gateway, prompts, model="gpt-4")
```

## Usage Instructions

### Basic Gateway Creation

```python
from src.core.litellm_gateway import create_gateway

# Simple creation with API key
gateway = create_gateway(
    providers=['openai'],
    default_model='gpt-4',
    api_keys={'openai': 'your-api-key'}
)
```

### Multi-Provider Gateway

```python
# Create gateway with multiple providers
gateway = create_gateway(
    providers=['openai', 'anthropic'],
    default_model='gpt-4',
    api_keys={
        'openai': 'sk-openai-key',
        'anthropic': 'sk-anthropic-key'
    },
    fallbacks=['gpt-3.5-turbo']
)
```

### Text Generation

```python
from src.core.litellm_gateway import create_gateway, generate_text_async

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

# Async generation (recommended)
text = await generate_text_async(
    gateway,
    prompt="Explain quantum computing",
    model="gpt-4",
    temperature=0.7
)
print(text)
```

### Streaming Generation

```python
from src.core.litellm_gateway import create_gateway, stream_text

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

# Streaming for real-time responses
for chunk in stream_text(gateway, "Tell me a story"):
    print(chunk, end="", flush=True)
```

### Embedding Generation

```python
from src.core.litellm_gateway import create_gateway, generate_embeddings_async

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

# Single text embedding
embeddings = await generate_embeddings_async(
    gateway,
    "This is a sample text",
    model="text-embedding-ada-002"
)

# Batch embeddings
texts = ["Text 1", "Text 2", "Text 3"]
all_embeddings = await generate_embeddings_async(
    gateway,
    texts,
    model="text-embedding-ada-002"
)
```

### Batch Processing

```python
from src.core.litellm_gateway import create_gateway, batch_generate

gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

# Generate multiple texts at once
prompts = [
    "What is artificial intelligence?",
    "What is machine learning?",
    "What is deep learning?"
]
results = batch_generate(gateway, prompts, model="gpt-4")
for prompt, result in zip(prompts, results):
    print(f"Q: {prompt}\nA: {result}\n")
```

### Advanced Configuration

```python
from src.core.litellm_gateway import create_gateway, configure_gateway
from src.core.litellm_gateway.gateway import LiteLLMGateway

# Create custom configuration
config = configure_gateway(
    model_list=[
        {
            "model_name": "gpt-4",
            "litellm_params": {
                "model": "openai/gpt-4",
                "api_key": "sk-..."
            }
        }
    ],
    fallbacks=['gpt-3.5-turbo'],
    timeout=120.0,
    max_retries=5
)

# Create gateway with custom config
gateway = LiteLLMGateway(config=config)
```

### Prerequisites

1. **Python 3.10+**: Required for type hints and async/await
2. **Dependencies**: Install via `pip install -r requirements.txt`
   - `litellm`: Core LLM library
   - `pydantic`: For data validation
3. **API Keys**: Configure provider API keys:
   - Pass via `api_keys` parameter, or
   - Set environment variables: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.

## Connection to Other Components

### LiteLLM Gateway Class
These functions create and use `LiteLLMGateway` instances from `gateway.py`:
- All factory functions return `LiteLLMGateway` instances
- Convenience functions use gateway methods internally

**Integration Point:** Functions wrap `LiteLLMGateway` class instantiation and methods

### Config Validator
Uses `ConfigValidator` from `src/core/utils/config_validator.py`:
- Validates gateway configuration
- Provides helpful error messages
- Ensures configuration correctness

**Integration Point:** `create_gateway()` uses validator for validation

### Error Handler
Uses error handling utilities from `src/core/utils/error_handler.py`:
- Creates helpful error messages
- Provides suggestions for fixing errors
- Improves developer experience

**Integration Point:** Error handling in `create_gateway()`

### Where Used
- **All AI Components**: Agent, RAG, and other components use these functions
- **Examples**: All examples use these convenience functions
- **API Backend Services**: HTTP endpoints use these functions
- **FaaS Gateway Service**: REST API wrapper uses these functions
- **User Applications**: Primary interface for creating gateways

## Best Practices

### 1. Use Factory Functions
Always use factory functions instead of directly instantiating `LiteLLMGateway`:
```python
# Good: Use factory function
gateway = create_gateway(api_keys={'openai': 'key'}, default_model='gpt-4')

# Bad: Direct instantiation (unless you need full control)
from src.core.litellm_gateway.gateway import LiteLLMGateway, GatewayConfig
config = GatewayConfig(...)
gateway = LiteLLMGateway(config=config)
```

### 2. Use Async Functions
Always prefer async functions for production:
```python
# Good: Async for better performance
text = await generate_text_async(gateway, "prompt")

# Bad: Synchronous blocks event loop
text = generate_text(gateway, "prompt")
```

### 3. Provide API Keys Explicitly
Always provide API keys explicitly for clarity:
```python
# Good: Explicit API keys
gateway = create_gateway(
    api_keys={'openai': 'sk-...'},
    default_model='gpt-4'
)

# Bad: Relying on environment variables (less explicit)
gateway = create_gateway(default_model='gpt-4')  # May fail if env var not set
```

### 4. Use Fallbacks
Configure fallback models for reliability:
```python
# Good: Fallback models
gateway = create_gateway(
    providers=['openai'],
    default_model='gpt-4',
    fallbacks=['gpt-3.5-turbo'],
    api_keys={'openai': 'key'}
)

# Bad: No fallback (single point of failure)
gateway = create_gateway(
    providers=['openai'],
    default_model='gpt-4',
    api_keys={'openai': 'key'}
)
```

### 5. Handle Errors
Always handle errors appropriately:
```python
# Good: Error handling
try:
    text = await generate_text_async(gateway, "prompt")
except Exception as e:
    logger.error(f"Generation failed: {e}")
    # Handle error

# Bad: No error handling
text = await generate_text_async(gateway, "prompt")  # May crash
```

### 6. Use Batch Processing
Use batch processing for multiple requests:
```python
# Good: Batch processing
prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
results = batch_generate(gateway, prompts)

# Bad: Sequential processing
results = []
for prompt in prompts:
    result = await generate_text_async(gateway, prompt)
    results.append(result)
```

### 7. Use Streaming for Long Responses
Use streaming for better user experience:
```python
# Good: Streaming for long responses
for chunk in stream_text(gateway, "Long prompt"):
    print(chunk, end="")

# Bad: Waiting for complete response
text = await generate_text_async(gateway, "Long prompt")  # Blocks
print(text)
```

### 8. Validate Configuration
Let the factory function validate configuration:
```python
# Good: Factory function validates
gateway = create_gateway(
    timeout=120.0,  # Validated automatically
    max_retries=5
)

# Bad: Manual validation (error-prone)
if timeout < 1.0 or timeout > 300.0:
    raise ValueError("Invalid timeout")
# ... manual validation code
```

## Additional Resources

### Documentation
- **[Gateway Class Documentation](gateway.md)** - Core LiteLLMGateway class
- **[Gateway README](README.md)** - Complete gateway guide
- **[Gateway Troubleshooting](../../../docs/troubleshooting/litellm_gateway_troubleshooting.md)** - Common issues

### Related Components
- **[Gateway Class](gateway.py)** - Core gateway implementation
- **[Rate Limiter](rate_limiter.py)** - Rate limiting
- **[KV Cache](kv_cache.py)** - Attention caching

### External Resources
- **[LiteLLM Documentation](https://docs.litellm.ai/)** - Official LiteLLM docs
- **[OpenAI API Reference](https://platform.openai.com/docs/api-reference)** - OpenAI API
- **[Async/Await in Python](https://docs.python.org/3/library/asyncio.html)** - Async programming

### Examples
- **[Basic Gateway Example](../../../../examples/basic_usage/03_litellm_gateway_basic.py)** - Simple usage
- **[Gateway with Streaming Example](../../../../examples/)** - Streaming examples
- **[Multi-Provider Example](../../../../examples/)** - Multiple providers

