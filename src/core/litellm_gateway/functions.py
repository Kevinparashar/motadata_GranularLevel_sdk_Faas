"""
LiteLLM Gateway - High-Level Functions

Factory functions, convenience functions, and utilities for LiteLLM Gateway.
"""


from typing import Any, AsyncIterator, Dict, List, Optional

from ..utils.config_validator import ConfigurationError
from ..utils.error_handler import create_error_with_suggestion
from .gateway import GatewayConfig, LiteLLMGateway

# ============================================================================
# Factory Functions
# ============================================================================


def _validate_model_format(default_model: str) -> None:
    """
    Validate model name format and provider.
    
    Args:
        default_model (str): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    
    Raises:
        create_error_with_suggestion: Raised when this function detects an invalid state or when an underlying call fails.
    """
    if not default_model:
        return

    valid_providers = ["openai", "anthropic", "google", "cohere", "azure", "bedrock"]
    model_provider = default_model.split("/")[0] if "/" in default_model else "openai"

    if model_provider not in valid_providers and not any(p in model_provider for p in valid_providers):
        suggestion = f"Valid providers: {', '.join(valid_providers)}\n"
        suggestion += "Example models: 'gpt-4', 'claude-3-opus', 'gemini-pro'\n"
        suggestion += f"Current model: '{default_model}'"
        raise create_error_with_suggestion(
            ConfigurationError,
            message=f"Invalid model format: '{default_model}'",
            suggestion=suggestion,
            config_key="default_model",
            invalid_value=default_model,
            component_name="gateway",
        )


def _validate_api_keys(api_keys: Optional[Dict[str, str]]) -> None:
    """
    Validate that API keys are provided.
    
    Args:
        api_keys (Optional[Dict[str, str]]): Input parameter for this operation.
    
    Returns:
        None: Result of the operation.
    
    Raises:
        create_error_with_suggestion: Raised when this function detects an invalid state or when an underlying call fails.
    """
    if api_keys is None or not api_keys:
        suggestion = "Provide API keys using one of these methods:\n"
        suggestion += "  1. Pass api_keys parameter: api_keys={'openai': 'sk-...'}\n"
        suggestion += "  2. Set environment variables: export OPENAI_API_KEY='sk-...'\n"
        suggestion += "  3. Use .env file: OPENAI_API_KEY=sk-..."
        raise create_error_with_suggestion(
            ConfigurationError,
            message="API keys are required for gateway initialization",
            suggestion=suggestion,
            config_key="api_keys",
            component_name="gateway",
        )


def _get_provider_api_key(provider: str, api_keys: Optional[Dict[str, str]]) -> Optional[str]:
    """
    Get API key for a provider from dict or environment.
    
    Args:
        provider (str): Input parameter for this operation.
        api_keys (Optional[Dict[str, str]]): Input parameter for this operation.
    
    Returns:
        Optional[str]: Returned text value.
    """
    import os

    # Check explicit api_keys dict first
    if api_keys and provider in api_keys:
        return api_keys[provider]

    # Fallback to environment variables
    env_key_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
    }

    env_key = env_key_map.get(provider)
    return os.getenv(env_key) if env_key else None


def _build_model_list(
    providers: Optional[List[str]],
    default_model: str,
    api_keys: Optional[Dict[str, str]],
) -> List[Dict[str, Any]]:
    """
    Build model list from providers and API keys.
    
    Args:
        providers (Optional[List[str]]): Input parameter for this operation.
        default_model (str): Input parameter for this operation.
        api_keys (Optional[Dict[str, str]]): Input parameter for this operation.
    
    Returns:
        List[Dict[str, Any]]: Dictionary result of the operation.
    """
    if not providers:
        return []

    model_list = []
    for provider in providers:
        api_key = _get_provider_api_key(provider, api_keys)
        if api_key:
            model_list.append(
                {
                    "model_name": default_model,
                    "litellm_params": {
                        "model": f"{provider}/{default_model}",
                        "api_key": api_key,
                    },
                }
            )

    return model_list


def create_gateway(
    providers: Optional[List[str]] = None,
    default_model: str = "gpt-4",
    api_keys: Optional[Dict[str, str]] = None,
    fallbacks: Optional[List[str]] = None,
    timeout: float = 60.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    **kwargs: Any,
) -> LiteLLMGateway:
    """
    Create a LiteLLM Gateway instance with validation and helpful error messages.

    Args:
        providers: List of provider names (e.g., ['openai', 'anthropic'])
        default_model: Default model to use (e.g., 'gpt-4', 'claude-3-opus')
        api_keys: Dictionary mapping provider names to API keys
        fallbacks: List of fallback models to try if primary fails
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        **kwargs: Additional configuration options

    Returns:
        Configured LiteLLMGateway instance

    Raises:
        ConfigurationError: If configuration is invalid with helpful suggestions

    Example:
        >>> gateway = create_gateway(
        ...     providers=['openai'],
        ...     default_model='gpt-4',
        ...     api_keys={'openai': 'sk-...'}
        ... )
    """
    from ..utils.config_validator import ConfigValidator

    validator = ConfigValidator()

    # Validate configuration
    config_dict = {
        "default_model": default_model,
        "timeout": timeout,
        "max_retries": max_retries,
        "retry_delay": retry_delay,
        **kwargs,
    }

    # Validate types
    validator.validate_type(config_dict, "timeout", float, "gateway")
    validator.validate_type(config_dict, "max_retries", int, "gateway")
    validator.validate_type(config_dict, "retry_delay", float, "gateway")

    # Validate ranges
    validator.validate_range(
        config_dict, "timeout", min_value=1.0, max_value=300.0, component_name="gateway"
    )
    validator.validate_range(
        config_dict, "max_retries", min_value=0, max_value=10, component_name="gateway"
    )
    validator.validate_range(
        config_dict, "retry_delay", min_value=0.1, max_value=60.0, component_name="gateway"
    )

    # Validate model name format
    _validate_model_format(default_model)

    # Check for API keys
    _validate_api_keys(api_keys)

    # Build model list
    model_list = _build_model_list(providers, default_model, api_keys)

    config = GatewayConfig(
        model_list=model_list if model_list else [],
        fallbacks=fallbacks,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )

    return LiteLLMGateway(config=config, **kwargs)


def configure_gateway(
    model_list: Optional[List[Dict[str, Any]]] = None,
    fallbacks: Optional[List[str]] = None,
    timeout: float = 60.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> GatewayConfig:
    """
    Create a GatewayConfig with specified settings.

    Args:
        model_list: List of model configurations
        fallbacks: List of fallback models
        timeout: Request timeout
        max_retries: Maximum retries
        retry_delay: Retry delay

    Returns:
        GatewayConfig instance

    Example:
        >>> config = configure_gateway(
        ...     model_list=[{"model_name": "gpt-4", ...}],
        ...     timeout=120.0
        ... )
        >>> gateway = LiteLLMGateway(config=config)
    """
    return GatewayConfig(
        model_list=model_list or [],
        fallbacks=fallbacks,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )


# ============================================================================
# High-Level Convenience Functions
# ============================================================================


async def generate_text(gateway: LiteLLMGateway, prompt: str, model: str = "gpt-4", **kwargs: Any) -> str:
    """
    Generate text asynchronously with simplified interface (high-level convenience).

    Args:
        gateway: LiteLLMGateway instance
        prompt: Input prompt
        model: Model to use
        **kwargs: Additional generation parameters

    Returns:
        Generated text

    Example:
        >>> text = await generate_text(gateway, "What is AI?", model="gpt-4")
        >>> print(text)
    """
    response = await gateway.generate_async(prompt=prompt, model=model, **kwargs)
    return response.text


async def generate_text_async(
    gateway: LiteLLMGateway, prompt: str, model: str = "gpt-4", **kwargs: Any
) -> str:
    """
    Generate text asynchronously with simplified interface (alias for generate_text).

    Args:
        gateway: LiteLLMGateway instance
        prompt: Input prompt
        model: Model to use
        **kwargs: Additional generation parameters

    Returns:
        Generated text

    Example:
        >>> text = await generate_text_async(gateway, "What is AI?")
    """
    # Delegate to the main async function
    return await generate_text(gateway, prompt, model, **kwargs)


async def stream_text(
    gateway: LiteLLMGateway, prompt: str, model: str = "gpt-4", **kwargs: Any
) -> AsyncIterator[str]:
    """
    Stream text generation (high-level convenience).
    
    Yields:
                            Text chunks as they're generated
    
                        Example:
                            >>> async for chunk in stream_text(gateway, "Tell me a story"):
                            ...     print(chunk, end="", flush=True)
    
    Args:
        gateway (LiteLLMGateway): Gateway client used for LLM calls.
        prompt (str): Prompt text sent to the model.
        model (str): Model name or identifier to use.
        **kwargs (Any): Input parameter for this operation.
    
    Returns:
        AsyncIterator[str]: Result of the operation.
    """
    # Use the gateway's generate with streaming enabled
    # When stream=True, acompletion returns an async iterator
    import litellm

    messages = kwargs.pop("messages", None) or [{"role": "user", "content": prompt}]

    response = await litellm.acompletion(
        model=model, messages=messages, stream=True, **kwargs
    )

    # Response is a CustomStreamWrapper that implements async iteration
    async for chunk in response:  # type: ignore[attr-defined]
        if hasattr(chunk, "choices") and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                yield delta.content


async def generate_embeddings(
    gateway: LiteLLMGateway, texts: List[str], model: str = "text-embedding-3-small", **kwargs: Any
) -> List[List[float]]:
    """
    Generate embeddings asynchronously with simplified interface (high-level convenience).

    Args:
        gateway: LiteLLMGateway instance
        texts: List of texts to embed
        model: Embedding model to use
        **kwargs: Additional embedding parameters

    Returns:
        List of embedding vectors

    Example:
        >>> embeddings = await generate_embeddings(
        ...     gateway,
        ...     ["Hello", "World"],
        ...     model="text-embedding-3-small"
        ... )
    """
    response = await gateway.embed_async(texts=texts, model=model, **kwargs)
    return response.embeddings


async def generate_embeddings_async(
    gateway: LiteLLMGateway, texts: List[str], model: str = "text-embedding-3-small", **kwargs: Any
) -> List[List[float]]:
    """
    Generate embeddings asynchronously with simplified interface (alias for generate_embeddings).

    Args:
        gateway: LiteLLMGateway instance
        texts: List of texts to embed
        model: Embedding model to use
        **kwargs: Additional embedding parameters

    Returns:
        List of embedding vectors

    Example:
        >>> embeddings = await generate_embeddings_async(
        ...     gateway,
        ...     ["Hello", "World"]
        ... )
    """
    # Delegate to the main async function
    return await generate_embeddings(gateway, texts, model, **kwargs)


# ============================================================================
# Utility Functions
# ============================================================================


def batch_generate(
    gateway: LiteLLMGateway,
    prompts: List[str],
    model: str = "gpt-4",
    max_concurrent: int = 5,
    **kwargs: Any,
) -> List[str]:
    """
    Generate text for multiple prompts concurrently.

    Args:
        gateway: LiteLLMGateway instance
        prompts: List of prompts
        model: Model to use
        max_concurrent: Maximum concurrent requests
        **kwargs: Additional generation parameters

    Returns:
        List of generated texts

    Example:
        >>> prompts = ["What is AI?", "What is ML?"]
        >>> texts = batch_generate(gateway, prompts)
    """
    import asyncio

    async def _generate_all():
        # Use semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _generate_with_limit(prompt: str) -> str:
            async with semaphore:
                return await generate_text_async(gateway, prompt, model, **kwargs)

        tasks = [_generate_with_limit(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)

    results = asyncio.run(_generate_all())
    # Filter out exceptions and convert to strings
    return [str(r) if not isinstance(r, Exception) else "" for r in results]


__all__ = [
    # Factory functions
    "create_gateway",
    "configure_gateway",
    # High-level convenience functions
    "generate_text",
    "generate_text_async",
    "stream_text",
    "generate_embeddings",
    "generate_embeddings_async",
    # Utility functions
    "batch_generate",
]
