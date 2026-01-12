"""
LiteLLM Gateway Implementation

Provides a unified interface for interacting with multiple LLM providers
through LiteLLM, with support for streaming, function calling, and embeddings.
"""

# Standard library imports
import asyncio
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

# Third-party imports
from litellm import acompletion, aembedding, completion, embedding
from pydantic import BaseModel, Field

try:
    from litellm.router import Router  # type: ignore
except ImportError:
    from litellm import Router  # type: ignore  # Fallback for older versions

# Local application/library specific imports
from ..cache_mechanism import CacheConfig, CacheMechanism
from ..feedback_loop import FeedbackLoop, FeedbackType
from ..llmops import LLMOps, LLMOperationStatus, LLMOperationType
from ..utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from ..utils.health_check import HealthCheck, HealthCheckResult, HealthStatus
from ..validation import ValidationLevel, ValidationManager
from .rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    RequestBatcher,
    RequestDeduplicator,
)


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
    # Advanced features
    enable_circuit_breaker: bool = True
    enable_rate_limiting: bool = True
    enable_request_deduplication: bool = True
    enable_request_batching: bool = False
    enable_health_monitoring: bool = True
    enable_llmops: bool = True
    enable_validation: bool = True
    enable_feedback_loop: bool = True
    enable_caching: bool = True
    cache_ttl: int = 3600  # Default cache TTL in seconds (1 hour)
    rate_limit_config: Optional[RateLimitConfig] = None
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    validation_level: ValidationLevel = ValidationLevel.MODERATE
    cache: Optional[CacheMechanism] = None
    cache_config: Optional[CacheConfig] = None


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
            router_kwargs = {
                "model_list": self.config.model_list,
                "timeout": self.config.timeout,
                "num_retries": self.config.max_retries,
            }
            if self.config.fallbacks is not None:
                router_kwargs["fallbacks"] = self.config.fallbacks
            self.router = Router(**router_kwargs)

        # Initialize circuit breaker
        self.circuit_breaker: Optional[CircuitBreaker] = None
        if self.config.enable_circuit_breaker:
            self.circuit_breaker = CircuitBreaker(
                name="litellm_gateway",
                config=self.config.circuit_breaker_config or CircuitBreakerConfig(
                    failure_threshold=5,
                    success_threshold=2,
                    timeout=60.0
                )
            )

        # Initialize rate limiter (per-tenant)
        self.rate_limiters: Dict[str, RateLimiter] = {}

        # Initialize request deduplicator
        self.deduplicator: Optional[RequestDeduplicator] = None
        if self.config.enable_request_deduplication:
            self.deduplicator = RequestDeduplicator(ttl=300.0)

        # Initialize request batcher
        self.batcher: Optional[RequestBatcher] = None
        if self.config.enable_request_batching:
            self.batcher = RequestBatcher(batch_size=10, batch_timeout=0.5)

        # Initialize health check
        self.health_check: Optional[HealthCheck] = None
        if self.config.enable_health_monitoring:
            self.health_check = HealthCheck(name="litellm_gateway")
            self._setup_health_checks()

        # Provider health tracking
        self.provider_health: Dict[str, Dict[str, Any]] = {}

        # Storage path for LLMOps and Feedback
        self.storage_path = Path("./llmops_data")

        # Initialize LLMOps
        self.llmops: Optional[LLMOps] = None
        if self.config.enable_llmops:
            self.llmops = LLMOps(
                storage_path=str(self.storage_path / "llmops.json"),
                enable_logging=True,
                enable_cost_tracking=True
            )

        # Initialize validation manager
        self.validation_manager: Optional[ValidationManager] = None
        if self.config.enable_validation:
            self.validation_manager = ValidationManager(default_level=self.config.validation_level)

        # Initialize feedback loop
        self.feedback_loop: Optional[FeedbackLoop] = None
        if self.config.enable_feedback_loop:
            self.feedback_loop = FeedbackLoop(
                storage_path=str(self.storage_path / "feedback.json"),
                auto_process=True
            )

        # Initialize cache mechanism
        self.cache: Optional[CacheMechanism] = None
        if self.config.enable_caching:
            self.cache = self.config.cache or CacheMechanism(
                self.config.cache_config or CacheConfig()
            )

    def _setup_health_checks(self) -> None:
        """Setup health check functions."""
        if not self.health_check:
            return

        async def check_router_health() -> HealthCheckResult:
            """Check router health."""
            if not self.router:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message="Router not configured"
                )
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Router available"
            )

        async def check_circuit_breaker_health() -> HealthCheckResult:
            """Check circuit breaker health."""
            if not self.circuit_breaker:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message="Circuit breaker not enabled"
                )
            stats = self.circuit_breaker.get_stats()
            if stats["state"] == CircuitState.OPEN.value:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message="Circuit breaker is OPEN",
                    details=stats
                )
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Circuit breaker healthy",
                details=stats
            )

        async def check_provider_health() -> HealthCheckResult:
            """Check provider health."""
            if not self.provider_health:
                return HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    message="No provider health data"
                )

            # Check if any provider is unhealthy
            unhealthy_providers = [
                name for name, health in self.provider_health.items()
                if health.get("status") == "unhealthy"
            ]

            if unhealthy_providers:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message=f"Unhealthy providers: {', '.join(unhealthy_providers)}",
                    details={"provider_health": self.provider_health}
                )

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="All providers healthy",
                details={"provider_health": self.provider_health}
            )

        self.health_check.add_check(check_router_health)
        self.health_check.add_check(check_circuit_breaker_health)
        self.health_check.add_check(check_provider_health)

    def _get_rate_limiter(self, tenant_id: Optional[str] = None) -> Optional[RateLimiter]:
        """Get or create rate limiter for tenant."""
        if not self.config.enable_rate_limiting:
            return None

        key = tenant_id or "global"
        if key not in self.rate_limiters:
            self.rate_limiters[key] = RateLimiter(
                config=self.config.rate_limit_config or RateLimitConfig(),
                tenant_id=tenant_id
            )
        return self.rate_limiters[key]

    def _classify_error(self, error: Exception) -> Dict[str, Any]:
        """
        Classify error for advanced error handling.

        Args:
            error: Exception to classify

        Returns:
            Dictionary with error classification
        """
        error_type = type(error).__name__
        error_message = str(error)

        classification = {
            "type": error_type,
            "message": error_message,
            "category": "unknown",
            "retryable": False,
            "provider_error": False,
            "rate_limit_error": False,
            "timeout_error": False,
            "authentication_error": False
        }

        # Classify error
        if "rate limit" in error_message.lower() or "429" in error_message:
            classification.update({
                "category": "rate_limit",
                "retryable": True,
                "rate_limit_error": True
            })
        elif "timeout" in error_message.lower() or "timed out" in error_message.lower():
            classification.update({
                "category": "timeout",
                "retryable": True,
                "timeout_error": True
            })
        elif "authentication" in error_message.lower() or "401" in error_message or "403" in error_message:
            classification.update({
                "category": "authentication",
                "retryable": False,
                "authentication_error": True
            })
        elif "api" in error_type.lower() or "provider" in error_type.lower():
            classification.update({
                "category": "provider",
                "retryable": True,
                "provider_error": True
            })
        else:
            # Check for retryable patterns
            retryable_patterns = ["connection", "network", "temporary", "503", "502", "500"]
            if any(pattern in error_message.lower() for pattern in retryable_patterns):
                classification["retryable"] = True
                classification["category"] = "network"

        return classification

    async def get_health(self) -> Dict[str, Any]:
        """Get gateway health status."""
        if not self.health_check:
            return {"status": "health_monitoring_disabled"}

        result = await self.health_check.check()
        health_info = self.health_check.get_health()

        # Add gateway-specific metrics
        health_info.update({
            "circuit_breaker": self.circuit_breaker.get_stats() if self.circuit_breaker else None,
            "rate_limiters": {
                tenant: limiter.get_stats()
                for tenant, limiter in self.rate_limiters.items()
            },
            "provider_health": self.provider_health,
            "llmops": self.llmops.get_metrics() if self.llmops else None,
            "feedback_stats": self.feedback_loop.get_feedback_stats() if self.feedback_loop else None
        })

        return health_info

    def _generate_cache_key(
        self,
        prompt: str,
        model: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        tenant_id: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """
        Generate cache key for LLM request.

        This creates a deterministic cache key based on request parameters.
        Identical requests (same prompt, model, tenant) will have the same key,
        enabling cache hits and cost savings.

        Args:
            prompt: Input prompt
            model: Model identifier
            messages: Optional messages list
            tenant_id: Optional tenant ID (ensures tenant isolation in cache)
            **kwargs: Additional parameters

        Returns:
            Cache key string (format: "gateway:generate:{model}:{hash}")
        """
        # Create deterministic key from request parameters
        # All parameters are included to ensure cache key uniqueness
        key_data = {
            "prompt": prompt,
            "model": model,
            "messages": messages,
            "tenant_id": tenant_id,  # Tenant isolation: same prompt for different tenants = different cache keys
            **{k: v for k, v in kwargs.items() if k not in ["stream"]}  # Exclude stream (streaming can't be cached)
        }

        # Create hash for consistent key (SHA256, truncated to 16 chars for efficiency)
        key_string = json.dumps(key_data, sort_keys=True)  # Sort keys for deterministic hashing
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        return f"gateway:generate:{model}:{key_hash}"

    def record_feedback(
        self,
        query: str,
        response: str,
        feedback_type: FeedbackType,
        content: str,
        tenant_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Record feedback for continuous learning.

        Args:
            query: Original query
            response: System response
            feedback_type: Type of feedback
            content: Feedback content
            tenant_id: Optional tenant ID

        Returns:
            Feedback ID or None if feedback loop not enabled
        """
        if not self.feedback_loop:
            return None

        return self.feedback_loop.record_feedback(
            query=query,
            response=response,
            feedback_type=feedback_type,
            content=content,
            tenant_id=tenant_id
        )

    def get_llmops_metrics(
        self,
        tenant_id: Optional[str] = None,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get LLM operations metrics.

        Args:
            tenant_id: Optional tenant ID filter
            time_range_hours: Time range in hours

        Returns:
            Dictionary with metrics
        """
        if not self.llmops:
            return {"error": "LLMOps not enabled"}

        return self.llmops.get_metrics(tenant_id=tenant_id, time_range_hours=time_range_hours)

    def get_cost_summary(
        self,
        tenant_id: Optional[str] = None,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get cost summary.

        Args:
            tenant_id: Optional tenant ID filter
            time_range_hours: Time range in hours

        Returns:
            Dictionary with cost summary
        """
        if not self.llmops:
            return {"error": "LLMOps not enabled"}

        return self.llmops.get_cost_summary(tenant_id=tenant_id, time_range_hours=time_range_hours)

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
            return response  # type: ignore[return-value]

        # Extract text from response (litellm types are incomplete, using runtime checks)
        text: str = ""
        model_name: str = model
        usage: Optional[Dict[str, Any]] = None
        finish_reason: Optional[str] = None
        raw_response: Optional[Dict[str, Any]] = None

        if hasattr(response, 'choices') and response.choices:  # type: ignore[attr-defined]
            choices = response.choices  # type: ignore[attr-defined]
            if len(choices) > 0:
                choice = choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):  # type: ignore[attr-defined]
                    text = choice.message.content or ""  # type: ignore[attr-defined]
                if hasattr(choice, 'finish_reason'):  # type: ignore[attr-defined]
                    finish_reason = choice.finish_reason  # type: ignore[attr-defined]
            if hasattr(response, 'model'):  # type: ignore[attr-defined]
                model_name = response.model or model  # type: ignore[attr-defined]
            if hasattr(response, 'usage') and response.usage:  # type: ignore[attr-defined]
                usage = response.usage.__dict__ if hasattr(response.usage, '__dict__') else None  # type: ignore[attr-defined]
            raw_response = response.__dict__ if hasattr(response, '__dict__') else None
        elif isinstance(response, dict):
            choices = response.get('choices', [])
            if choices and len(choices) > 0:
                message = choices[0].get('message', {})
                text = message.get('content', '') or ""
                finish_reason = choices[0].get('finish_reason')
            model_name = response.get('model', model) or model
            usage = response.get('usage')
            raw_response = response
        else:
            text = str(response) if response else ""
            raw_response = {"response": str(response)} if response else None

        return GenerateResponse(
            text=text or "",
            model=model_name or model,
            usage=usage,
            finish_reason=finish_reason,
            raw_response=raw_response
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
        Generate text completion asynchronously with advanced features.

        Args:
            prompt: Input prompt
            model: Model identifier
            tenant_id: Optional tenant ID for rate limiting and tracking
            messages: Optional list of messages
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            GenerateResponse with generated text
        """
        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        # COST OPTIMIZATION: Check cache first (if caching enabled and not streaming)
        # Cache hits avoid expensive LLM API calls, reducing costs by 50-90% for repeated queries
        # Example: Without cache: $0.01 per call. With 50% cache hit rate: $0.005 average cost
        if self.cache and not stream and self.config.enable_caching:
            cache_key = self._generate_cache_key(
                prompt=prompt,
                model=model,
                messages=messages,
                tenant_id=tenant_id,
                **kwargs
            )
            cached_response = self.cache.get(cache_key, tenant_id=tenant_id)
            if cached_response:
                # Cache hit: Return immediately without API call (saves cost and latency)
                # Cost saved: ~$0.001-0.01 per cached response (depends on model)
                if isinstance(cached_response, dict):
                    return GenerateResponse(
                        text=cached_response.get("text", ""),
                        model=cached_response.get("model", model),
                        usage=cached_response.get("usage"),
                        finish_reason=cached_response.get("finish_reason"),
                        raw_response=cached_response.get("raw_response")
                    )
                return cached_response

        # Rate limiting
        rate_limiter = self._get_rate_limiter(tenant_id)
        if rate_limiter:
            await rate_limiter.acquire()

        # Track operation metrics
        start_time = time.time()
        prompt_tokens = 0
        completion_tokens = 0
        error_message: Optional[str] = None
        status = LLMOperationStatus.SUCCESS

        # Define the actual generation function
        async def _generate() -> Any:
            """Internal generation function."""
            nonlocal prompt_tokens, completion_tokens, error_message, status

            try:
                if self.router:
                    response = await self.router.acompletion(  # type: ignore
                        model=model,
                        messages=messages,  # type: ignore
                        stream=stream,
                        **kwargs
                    )
                else:
                    response = await acompletion(  # type: ignore
                        model=model,
                        messages=messages,  # type: ignore
                        stream=stream,
                        **kwargs
                    )

                # Extract token usage
                if hasattr(response, 'usage') and response.usage:  # type: ignore[attr-defined]
                    prompt_tokens = getattr(response.usage, 'prompt_tokens', 0) or 0  # type: ignore[attr-defined]
                    completion_tokens = getattr(response.usage, 'completion_tokens', 0) or 0  # type: ignore[attr-defined]

                # Update provider health
                provider_name = model.split("/")[0] if "/" in model else "default"
                self.provider_health[provider_name] = {
                    "status": "healthy",
                    "last_success": datetime.now().isoformat(),
                    "last_check": datetime.now().isoformat()
                }

                return response

            except Exception as e:
                # Classify error
                error_classification = self._classify_error(e)
                error_message = str(e)

                # Determine status
                if "rate limit" in error_message.lower() or "429" in error_message:
                    status = LLMOperationStatus.RATE_LIMITED
                elif "timeout" in error_message.lower():
                    status = LLMOperationStatus.TIMEOUT
                else:
                    status = LLMOperationStatus.ERROR

                # Update provider health
                provider_name = model.split("/")[0] if "/" in model else "default"
                self.provider_health[provider_name] = {
                    "status": "unhealthy" if not error_classification["retryable"] else "degraded",
                    "last_error": error_message,
                    "error_classification": error_classification,
                    "last_check": datetime.now().isoformat()
                }

                raise

        # Use deduplication if enabled
        if self.deduplicator and not stream:
            response = await self.deduplicator.get_or_execute(
                _generate,
                prompt=prompt,
                model=model,
                messages=messages,
                stream=stream,
                **kwargs
            )
        # Use batching if enabled
        elif self.batcher and not stream:
            batch_key = f"{model}_{tenant_id or 'global'}"
            response = await self.batcher.batch_execute(
                batch_key,
                _generate,
                prompt=prompt,
                model=model,
                messages=messages,
                stream=stream,
                **kwargs
            )
        # Use circuit breaker if enabled
        elif self.circuit_breaker:
            response = await self.circuit_breaker.call(_generate)
        else:
            response = await _generate()

        if stream:
            return response

        # Log operation
        if self.llmops:
            latency_ms = (time.time() - start_time) * 1000
            self.llmops.log_operation(
                operation_type=LLMOperationType.COMPLETION,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                status=status,
                error_message=error_message,
                tenant_id=tenant_id,
                metadata={"stream": stream}
            )

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

        generate_response = GenerateResponse(
            text=text,
            model=model_name,
            usage=usage,
            finish_reason=finish_reason,
            raw_response=response.__dict__ if hasattr(response, '__dict__') else response
        )

        # COST OPTIMIZATION: Store successful response in cache for future requests
        # This enables future identical requests to be served from cache, avoiding API costs
        # Cache TTL: Default 3600 seconds (1 hour). Adjust based on your data freshness needs
        if self.cache and not stream and self.config.enable_caching and status == LLMOperationStatus.SUCCESS:
            cache_key = self._generate_cache_key(
                prompt=prompt,
                model=model,
                messages=messages,
                tenant_id=tenant_id,
                **kwargs
            )
            # Store response data for caching
            # Future identical requests will use this cached response, saving API costs
            cache_data = {
                "text": text,
                "model": model_name,
                "usage": usage,
                "finish_reason": finish_reason,
                "raw_response": generate_response.raw_response
            }
            self.cache.set(
                cache_key,
                cache_data,
                tenant_id=tenant_id,
                ttl=self.config.cache_ttl  # Cache duration in seconds
            )

        return generate_response

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
            model=model_name or model,
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

        # Extract embeddings (litellm types are incomplete, using runtime checks)
        embeddings: List[List[float]] = []
        model_name: str = model
        usage: Optional[Dict[str, Any]] = None

        if hasattr(response, 'data') and response.data:  # type: ignore[attr-defined]
            data_list = response.data if isinstance(response.data, list) else []  # type: ignore[attr-defined]
            embeddings = [item.embedding for item in data_list if hasattr(item, 'embedding')]  # type: ignore[attr-defined]
            if hasattr(response, 'model'):  # type: ignore[attr-defined]
                model_name = response.model or model  # type: ignore[attr-defined]
            if hasattr(response, 'usage') and response.usage:  # type: ignore[attr-defined]
                usage = response.usage.__dict__ if hasattr(response.usage, '__dict__') else None  # type: ignore[attr-defined]
        elif isinstance(response, dict):
            data = response.get('data', [])
            if data and isinstance(data, list):
                embeddings = [item.get('embedding', []) for item in data if isinstance(item, dict)]
            model_name = response.get('model', model) or model
            usage = response.get('usage')
        else:
            embeddings = []

        return EmbedResponse(
            embeddings=embeddings,
            model=model_name or model,
            usage=usage
        )

