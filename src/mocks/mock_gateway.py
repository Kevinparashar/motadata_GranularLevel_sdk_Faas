"""
Mock LiteLLM Gateway Implementation

Mock implementation of LiteLLMGateway for testing.

Copyright (c) 2024 Motadata. All rights reserved.
"""

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock


class MockLiteLLMGateway:
    """
    Mock implementation of LiteLLMGateway for testing.
    
    Provides a mock gateway that can be used in tests
    without requiring actual LLM API calls.
    """

    def __init__(self):
        """Initialize mock gateway."""
        self._mock = MagicMock()
        self._mock.generate = AsyncMock()
        self._mock.embed = AsyncMock()
        self._mock.embed_async = AsyncMock()

    async def generate(
        self,
        prompt: str,
        model: str = "gpt-4",
        tenant_id: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Mock generate method.
        
        Args:
            prompt: Input prompt
            model: Model name
            tenant_id: Optional tenant ID (for interface compatibility)
            messages: Optional chat messages (for interface compatibility)
            stream: Whether to stream response (for interface compatibility)
            **kwargs: Additional arguments
            
        Returns:
            Mock response dictionary with GenerateResponse-like structure
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        # Default mock response
        default_response = {
            "text": f"Mock response for: {prompt}",
            "model": model,
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            "finish_reason": "stop",
            "raw_response": {},
        }
        
        # Use mock if configured, otherwise return default
        if self._mock.generate.return_value:
            return await self._mock.generate(prompt, model=model, tenant_id=tenant_id, **kwargs)
        return default_response

    def embed(
        self, texts: List[str], model: str = "text-embedding-3-small", **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Mock embed method (synchronous).
        
        Args:
            texts: List of texts to embed
            model: Embedding model name
            **kwargs: Additional arguments
            
        Returns:
            Mock embeddings dictionary with EmbedResponse-like structure
        """
        # Default mock response
        default_response = {
            "embeddings": [[0.1] * 1536 for _ in texts],  # Mock embeddings
            "model": model,
            "usage": {"prompt_tokens": len(texts) * 10, "total_tokens": len(texts) * 10},
        }
        
        # Use mock if configured, otherwise return default
        if self._mock.embed.return_value:
            return self._mock.embed(texts, model=model, **kwargs)
        return default_response

    async def embed_async(
        self, texts: List[str], model: str = "text-embedding-3-small", **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Mock embed_async method (asynchronous).
        
        Args:
            texts: List of texts to embed
            model: Embedding model name
            **kwargs: Additional arguments
            
        Returns:
            Mock embeddings dictionary with EmbedResponse-like structure
        """
        # Minimal async operation to satisfy linter
        await asyncio.sleep(0)
        
        # Default mock response
        default_response = {
            "embeddings": [[0.1] * 1536 for _ in texts],  # Mock embeddings
            "model": model,
            "usage": {"prompt_tokens": len(texts) * 10, "total_tokens": len(texts) * 10},
        }
        
        # Use mock if configured, otherwise return default
        if self._mock.embed_async.return_value:
            return await self._mock.embed_async(texts, model=model, **kwargs)
        return default_response


__all__ = ["MockLiteLLMGateway"]

