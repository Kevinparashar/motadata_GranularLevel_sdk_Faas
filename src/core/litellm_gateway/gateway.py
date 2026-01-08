"""
LiteLLM Gateway Implementation

Provides a unified interface for interacting with multiple LLM providers
through LiteLLM, with support for streaming, function calling, and embeddings.
"""

import os
from typing import Any, Dict, List, Optional, AsyncIterator
from litellm import completion, acompletion, embedding, aembedding
from litellm import Router
from pydantic import BaseModel, Field


class GatewayConfig(BaseModel):
    """Configuration for LiteLLM Gateway."""
    model_list: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of model configurations"
    )
    fallbacks: Optional[List[str]] = None
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0


class GenerateResponse(BaseModel):
    """Response from text generation."""
    text: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class EmbedResponse(BaseModel):
    """Response from embedding generation."""
    embeddings: List[List[float]]
    model: str
    usage: Optional[Dict[str, Any]] = None


class LiteLLMGateway:
    """
    LiteLLM Gateway for unified LLM access.

    Provides a single interface to interact with multiple LLM providers
    including OpenAI, Anthropic, Google, Cohere, and more.
    """

    def __init__(
        self,
        config: Optional[GatewayConfig] = None,
        router: Optional[Router] = None
    ):
        """
        Initialize LiteLLM Gateway.

        Args:
            config: Gateway configuration
            router: Optional pre-configured LiteLLM Router
        """
        self.config = config or GatewayConfig()
        self.router = router

        if router is None and self.config.model_list:
            self.router = Router(
                model_list=self.config.model_list,
                fallbacks=self.config.fallbacks,
                timeout=self.config.timeout,
                num_retries=self.config.max_retries,
            )

    def generate(
        self,
        prompt: str,
        model: str = "gpt-4",
        tenant_id: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> GenerateResponse:
        """
        Generate text completion.

        Args:
            prompt: Input prompt
            model: Model identifier
            messages: Optional list of messages
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            GenerateResponse with generated text
        """
        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        if self.router:
            response = self.router.completion(
                model=model,
                messages=messages,
                stream=stream,
                **kwargs
            )
        else:
            response = completion(
                model=model,
                messages=messages,
                stream=stream,
                **kwargs
            )

        if stream:
            # For streaming, return an async iterator
            return response

        # Extract text from response
        if hasattr(response, 'choices') and len(response.choices) > 0:
            text = response.choices[0].message.content
            model_name = response.model if hasattr(response, 'model') else model
            usage = response.usage.__dict__ if hasattr(response, 'usage') else None
            finish_reason = response.choices[0].finish_reason if hasattr(response.choices[0], 'finish_reason') else None
        elif isinstance(response, dict):
            text = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            model_name = response.get('model', model)
            usage = response.get('usage')
            finish_reason = response.get('choices', [{}])[0].get('finish_reason')
        else:
            text = str(response)
            model_name = model
            usage = None
            finish_reason = None

        return GenerateResponse(
            text=text,
            model=model_name,
            usage=usage,
            finish_reason=finish_reason,
            raw_response=response.__dict__ if hasattr(response, '__dict__') else response
        )

    async def generate_async(
        self,
        prompt: str,
        model: str = "gpt-4",
        tenant_id: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs: Any
    ) -> GenerateResponse:
        """
        Generate text completion asynchronously.

        Args:
            prompt: Input prompt
            model: Model identifier
            messages: Optional list of messages
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            GenerateResponse with generated text
        """
        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        if self.router:
            response = await self.router.acompletion(
                model=model,
                messages=messages,
                stream=stream,
                **kwargs
            )
        else:
            response = await acompletion(
                model=model,
                messages=messages,
                stream=stream,
                **kwargs
            )

        if stream:
            return response

        # Extract text from response
        if hasattr(response, 'choices') and len(response.choices) > 0:
            text = response.choices[0].message.content
            model_name = response.model if hasattr(response, 'model') else model
            usage = response.usage.__dict__ if hasattr(response, 'usage') else None
            finish_reason = response.choices[0].finish_reason if hasattr(response.choices[0], 'finish_reason') else None
        elif isinstance(response, dict):
            text = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            model_name = response.get('model', model)
            usage = response.get('usage')
            finish_reason = response.get('choices', [{}])[0].get('finish_reason')
        else:
            text = str(response)
            model_name = model
            usage = None
            finish_reason = None

        return GenerateResponse(
            text=text,
            model=model_name,
            usage=usage,
            finish_reason=finish_reason,
            raw_response=response.__dict__ if hasattr(response, '__dict__') else response
        )

    def embed(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small",
        **kwargs: Any
    ) -> EmbedResponse:
        """
        Generate embeddings.

        Args:
            texts: List of texts to embed
            model: Embedding model identifier
            **kwargs: Additional parameters

        Returns:
            EmbedResponse with embeddings
        """
        if self.router:
            response = self.router.embedding(
                model=model,
                input=texts,
                **kwargs
            )
        else:
            response = embedding(
                model=model,
                input=texts,
                **kwargs
            )

        # Extract embeddings
        if hasattr(response, 'data'):
            embeddings = [item.embedding for item in response.data]
            model_name = response.model if hasattr(response, 'model') else model
            usage = response.usage.__dict__ if hasattr(response, 'usage') else None
        elif isinstance(response, dict):
            embeddings = [item.get('embedding', []) for item in response.get('data', [])]
            model_name = response.get('model', model)
            usage = response.get('usage')
        else:
            embeddings = []
            model_name = model
            usage = None

        return EmbedResponse(
            embeddings=embeddings,
            model=model_name,
            usage=usage
        )

    async def embed_async(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small",
        **kwargs: Any
    ) -> EmbedResponse:
        """
        Generate embeddings asynchronously.

        Args:
            texts: List of texts to embed
            model: Embedding model identifier
            **kwargs: Additional parameters

        Returns:
            EmbedResponse with embeddings
        """
        if self.router:
            response = await self.router.aembedding(
                model=model,
                input=texts,
                **kwargs
            )
        else:
            response = await aembedding(
                model=model,
                input=texts,
                **kwargs
            )

        # Extract embeddings
        if hasattr(response, 'data'):
            embeddings = [item.embedding for item in response.data]
            model_name = response.model if hasattr(response, 'model') else model
            usage = response.usage.__dict__ if hasattr(response, 'usage') else None
        elif isinstance(response, dict):
            embeddings = [item.get('embedding', []) for item in response.get('data', [])]
            model_name = response.get('model', model)
            usage = response.get('usage')
        else:
            embeddings = []
            model_name = model
            usage = None

        return EmbedResponse(
            embeddings=embeddings,
            model=model_name,
            usage=usage
        )

