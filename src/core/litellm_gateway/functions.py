"""
LiteLLM Gateway - High-Level Functions

Factory functions, convenience functions, and utilities for LiteLLM Gateway.
"""

from typing import Any, Dict, List, Optional, AsyncIterator
from .gateway import LiteLLMGateway, GatewayConfig, GenerateResponse, EmbedResponse


# ============================================================================
# Factory Functions
# ============================================================================

def create_gateway(
    providers: Optional[List[str]] = None,
    default_model: str = "gpt-4",
    api_keys: Optional[Dict[str, str]] = None,
    fallbacks: Optional[List[str]] = None,
    timeout: float = 60.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    **kwargs: Any
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
    from ..utils.config_validator import ConfigValidator, ConfigHelper
    
    validator = ConfigValidator()
    
    # Validate configuration
    config_dict = {
        "default_model": default_model,
        "timeout": timeout,
        "max_retries": max_retries,
        "retry_delay": retry_delay,
        **kwargs
    }
    
    # Validate types
    validator.validate_type(config_dict, "timeout", float, "gateway")
    validator.validate_type(config_dict, "max_retries", int, "gateway")
    validator.validate_type(config_dict, "retry_delay", float, "gateway")
    
    # Validate ranges
    validator.validate_range(config_dict, "timeout", min_value=1.0, max_value=300.0, component_name="gateway")
    validator.validate_range(config_dict, "max_retries", min_value=0, max_value=10, component_name="gateway")
    validator.validate_range(config_dict, "retry_delay", min_value=0.1, max_value=60.0, component_name="gateway")
    
    # Validate model name format
    if default_model:
        valid_providers = ["openai", "anthropic", "google", "cohere", "azure", "bedrock"]
        model_provider = default_model.split("/")[0] if "/" in default_model else "openai"
        if model_provider not in valid_providers and not any(p in model_provider for p in valid_providers):
            suggestion = f"Valid providers: {', '.join(valid_providers)}\n"
            suggestion += f"Example models: 'gpt-4', 'claude-3-opus', 'gemini-pro'\n"
            suggestion += f"Current model: '{default_model}'"
            raise create_error_with_suggestion(
                ConfigurationError,
                message=f"Invalid model format: '{default_model}'",
                suggestion=suggestion,
                config_key="default_model",
                invalid_value=default_model,
                component_name="gateway"
            )
    
    # Check for API keys
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
            component_name="gateway"
        )
    """
    Create and configure a LiteLLM Gateway with default settings.
    
    Args:
        providers: List of provider names (e.g., ["openai", "anthropic"])
        default_model: Default model to use
        api_keys: Dictionary mapping provider names to API keys
        fallbacks: List of fallback models
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        retry_delay: Delay between retries
        **kwargs: Additional gateway configuration
    
    Returns:
        Configured LiteLLMGateway instance
    
    Example:
        >>> gateway = create_gateway(
        ...     providers=["openai", "anthropic"],
        ...     default_model="gpt-4",
        ...     api_keys={"openai": "sk-...", "anthropic": "sk-..."}
        ... )
    """
    import os
    
    model_list = []
    
    if providers:
        for provider in providers:
            api_key = None
            if api_keys and provider in api_keys:
                api_key = api_keys[provider]
            elif provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            elif provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
            elif provider == "google":
                api_key = os.getenv("GOOGLE_API_KEY")
            
            if api_key:
                model_list.append({
                    "model_name": default_model,
                    "litellm_params": {
                        "model": f"{provider}/{default_model}",
                        "api_key": api_key
                    }
                })
    
    config = GatewayConfig(
        model_list=model_list if model_list else [],
        fallbacks=fallbacks,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay
    )
    
    return LiteLLMGateway(config=config, **kwargs)


def configure_gateway(
    model_list: Optional[List[Dict[str, Any]]] = None,
    fallbacks: Optional[List[str]] = None,
    timeout: float = 60.0,
    max_retries: int = 3,
    retry_delay: float = 1.0
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
        retry_delay=retry_delay
    )


# ============================================================================
# High-Level Convenience Functions
# ============================================================================

def generate_text(
    gateway: LiteLLMGateway,
    prompt: str,
    model: str = "gpt-4",
    **kwargs: Any
) -> str:
    """
    Generate text with simplified interface (high-level convenience).
    
    Args:
        gateway: LiteLLMGateway instance
        prompt: Input prompt
        model: Model to use
        **kwargs: Additional generation parameters
    
    Returns:
        Generated text
    
    Example:
        >>> text = generate_text(gateway, "What is AI?", model="gpt-4")
        >>> print(text)
    """
    response = gateway.generate(
        prompt=prompt,
        model=model,
        **kwargs
    )
    return response.text


async def generate_text_async(
    gateway: LiteLLMGateway,
    prompt: str,
    model: str = "gpt-4",
    **kwargs: Any
) -> str:
    """
    Generate text asynchronously with simplified interface.
    
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
    response = await gateway.generate_async(
        prompt=prompt,
        model=model,
        **kwargs
    )
    return response.text


def stream_text(
    gateway: LiteLLMGateway,
    prompt: str,
    model: str = "gpt-4",
    **kwargs: Any
) -> AsyncIterator[str]:
    """
    Stream text generation (high-level convenience).
    
    Args:
        gateway: LiteLLMGateway instance
        prompt: Input prompt
        model: Model to use
        **kwargs: Additional generation parameters
    
    Yields:
        Text chunks as they're generated
    
    Example:
        >>> async for chunk in stream_text(gateway, "Tell me a story"):
        ...     print(chunk, end="", flush=True)
    """
    response = gateway.generate(
        prompt=prompt,
        model=model,
        stream=True,
        **kwargs
    )
    
    # Handle streaming response
    if hasattr(response, '__aiter__'):
        async for chunk in response:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0].get('delta', {})
                content = delta.get('content', '')
                if content:
                    yield content
    else:
        # Fallback for non-async iterators
        for chunk in response:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0].get('delta', {})
                content = delta.get('content', '')
                if content:
                    yield content


def generate_embeddings(
    gateway: LiteLLMGateway,
    texts: List[str],
    model: str = "text-embedding-3-small",
    **kwargs: Any
) -> List[List[float]]:
    """
    Generate embeddings with simplified interface (high-level convenience).
    
    Args:
        gateway: LiteLLMGateway instance
        texts: List of texts to embed
        model: Embedding model to use
        **kwargs: Additional embedding parameters
    
    Returns:
        List of embedding vectors
    
    Example:
        >>> embeddings = generate_embeddings(
        ...     gateway,
        ...     ["Hello", "World"],
        ...     model="text-embedding-3-small"
        ... )
    """
    response = gateway.embed(
        texts=texts,
        model=model,
        **kwargs
    )
    return response.embeddings


async def generate_embeddings_async(
    gateway: LiteLLMGateway,
    texts: List[str],
    model: str = "text-embedding-3-small",
    **kwargs: Any
) -> List[List[float]]:
    """
    Generate embeddings asynchronously with simplified interface.
    
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
    response = await gateway.embed_async(
        texts=texts,
        model=model,
        **kwargs
    )
    return response.embeddings


# ============================================================================
# Utility Functions
# ============================================================================

def batch_generate(
    gateway: LiteLLMGateway,
    prompts: List[str],
    model: str = "gpt-4",
    max_concurrent: int = 5,
    **kwargs: Any
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
        tasks = [
            generate_text_async(gateway, prompt, model, **kwargs)
            for prompt in prompts
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    results = asyncio.run(_generate_all())
    return [
        str(r) if isinstance(r, Exception) else r
        for r in results
    ]


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

