"""
LiteLLM Gateway Implementation

Provides a unified interface for interacting with multiple LLM providers
through LiteLLM, with support for streaming, function calling, and embeddings.
"""


# Standard library imports
import hashlib
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party imports
from litellm import acompletion, aembedding, completion, embedding
from pydantic import BaseModel, ConfigDict, Field

try:
    from litellm.router import Router
except ImportError:
    from litellm import Router  # Fallback for older versions

# Local application/library specific imports
from ..cache_mechanism import CacheConfig, CacheMechanism
from ..feedback_loop import FeedbackLoop, FeedbackType
from ..llmops import LLMOperationStatus, LLMOperationType, LLMOps

# Set up logger
logger = logging.getLogger(__name__)
from ..utils.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from ..utils.health_check import HealthCheck, HealthCheckResult, HealthStatus
from ..validation import ValidationLevel, ValidationManager
from .kv_cache import create_kv_cache_manager
from .rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    RequestBatcher,
    RequestDeduplicator,
)


class GatewayConfig(BaseModel):
    """Configuration for LiteLLM Gateway."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    model_list: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of model configurations"
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
    enable_kv_cache: bool = True  # Enable KV cache for attention optimization
    kv_cache_ttl: int = 3600  # KV cache TTL in seconds
    rate_limit_config: Optional[RateLimitConfig] = None
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    validation_level: ValidationLevel = ValidationLevel.MODERATE
    cache: Optional[CacheMechanism] = Field(default=None, description="Cache mechanism instance", validate_default=False)
    cache_config: Optional[CacheConfig] = None
    batch_size: Optional[int] = None
    batch_timeout: Optional[float] = None


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

    def _initialize_router(self, router: Optional[Router]) -> None:
        """
        Initialize LiteLLM router.
        
        Args:
            router (Optional[Router]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        if router is not None:
            self.router = router
            return
        
        if self.config.model_list:
            router_kwargs = {
                "model_list": self.config.model_list,
                "timeout": self.config.timeout,
                "num_retries": self.config.max_retries,
            }
            if self.config.fallbacks is not None:
                router_kwargs["fallbacks"] = self.config.fallbacks
            self.router = Router(**router_kwargs)

    def _initialize_circuit_breaker(self) -> None:
        """
        Initialize circuit breaker if enabled.
        
        Returns:
            None: Result of the operation.
        """
        if not self.config.enable_circuit_breaker:
            self.circuit_breaker = None
            return
        
        self.circuit_breaker = CircuitBreaker(
            name="litellm_gateway",
            config=self.config.circuit_breaker_config
            or CircuitBreakerConfig(failure_threshold=5, success_threshold=2, timeout=60.0),
        )

    def _initialize_rate_limiter(self) -> None:
        """
        Initialize rate limiter (per-tenant).
        
        Returns:
            None: Result of the operation.
        """
        self.rate_limiters: Dict[str, RateLimiter] = {}

    def _initialize_deduplicator(self) -> None:
        """
        Initialize request deduplicator if enabled.
        
        Returns:
            None: Result of the operation.
        """
        if self.config.enable_request_deduplication:
            self.deduplicator = RequestDeduplicator(ttl=300.0)
        else:
            self.deduplicator = None

    def _initialize_batcher(self) -> None:
        """
        Initialize request batcher if enabled.
        
        Returns:
            None: Result of the operation.
        """
        if self.config.enable_request_batching:
            self.batcher = RequestBatcher(
                batch_size=self.config.batch_size or 10,
                batch_timeout=self.config.batch_timeout or 0.5,
            )
        else:
            self.batcher = None

    def _initialize_kv_cache(self) -> None:
        """
        Initialize KV cache manager if enabled.
        
        Returns:
            None: Result of the operation.
        """
        if self.config.enable_kv_cache:
            self.kv_cache = create_kv_cache_manager(
                cache=self.cache,
                enable_kv_cache=self.config.enable_kv_cache,
                kv_cache_ttl=self.config.kv_cache_ttl or 3600,
            )
        else:
            self.kv_cache = None

    def _initialize_health_check(self) -> None:
        """
        Initialize health check if enabled.
        
        Returns:
            None: Result of the operation.
        """
        if self.config.enable_health_monitoring:
            self.health_check = HealthCheck(name="litellm_gateway")
            self._setup_health_checks()
        else:
            self.health_check = None

    def _initialize_llmops(self) -> None:
        """
        Initialize LLMOps if enabled.
        
        Returns:
            None: Result of the operation.
        """
        if self.config.enable_llmops:
            self.llmops = LLMOps(
                storage_path=str(self.storage_path / "llmops.json"),
                enable_logging=True,
                enable_cost_tracking=True,
            )
        else:
            self.llmops = None

    def _initialize_validation_manager(self) -> None:
        """
        Initialize validation manager if enabled.
        
        Returns:
            None: Result of the operation.
        """
        if self.config.enable_validation:
            self.validation_manager = ValidationManager(default_level=self.config.validation_level)
        else:
            self.validation_manager = None

    def _initialize_feedback_loop(self) -> None:
        """
        Initialize feedback loop if enabled.
        
        Returns:
            None: Result of the operation.
        """
        if self.config.enable_feedback_loop:
            self.feedback_loop = FeedbackLoop(
                storage_path=str(self.storage_path / "feedback.json"), auto_process=True
            )
        else:
            self.feedback_loop = None

    def _initialize_cache(self) -> None:
        """
        Initialize cache mechanism if enabled.
        
        Returns:
            None: Result of the operation.
        """
        if self.config.enable_caching:
            self.cache = self.config.cache or CacheMechanism(
                self.config.cache_config or CacheConfig()
            )
        else:
            self.cache = None

    def __init__(self, config: Optional[GatewayConfig] = None, router: Optional[Router] = None):
        """
        Initialize LiteLLM Gateway.
        
        Args:
            config (Optional[GatewayConfig]): Configuration object or settings.
            router (Optional[Router]): Input parameter for this operation.
        """
        self.config = config or GatewayConfig()
        self.provider_health: Dict[str, Dict[str, Any]] = {}
        self.storage_path = Path("./llmops_data")

        self._initialize_router(router)
        self._initialize_circuit_breaker()
        self._initialize_rate_limiter()
        self._initialize_deduplicator()
        self._initialize_batcher()
        self._initialize_cache()  # Initialize cache before KV cache (KV cache depends on cache)
        self._initialize_kv_cache()
        self._initialize_health_check()
        self._initialize_llmops()
        self._initialize_validation_manager()
        self._initialize_feedback_loop()
        
        # CODEC Integration (optional)
        self.codec_serializer: Optional[Any] = None  # CodecSerializer instance for request/response encoding

        # OTEL Integration (optional)
        self.otel_tracer: Optional[Any] = None  # OTELTracer instance for distributed tracing
        self.otel_metrics: Optional[Any] = None  # OTELMetrics instance for metrics collection

    def _setup_health_checks(self) -> None:
        """
        Setup health check functions.
        
        Returns:
            None: Result of the operation.
        """
        if not self.health_check:
            return

        def check_router_health() -> HealthCheckResult:
            """Check router health."""
            if not self.router:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED, message="Router not configured"
                )
            return HealthCheckResult(status=HealthStatus.HEALTHY, message="Router available")

        def check_circuit_breaker_health() -> HealthCheckResult:
            """Check circuit breaker health."""
            if not self.circuit_breaker:
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY, message="Circuit breaker not enabled"
                )
            stats = self.circuit_breaker.get_stats()
            if stats["state"] == CircuitState.OPEN.value:
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY, message="Circuit breaker is OPEN", details=stats
                )
            return HealthCheckResult(
                status=HealthStatus.HEALTHY, message="Circuit breaker healthy", details=stats
            )

        def check_provider_health() -> HealthCheckResult:
            """Check provider health."""
            if not self.provider_health:
                return HealthCheckResult(
                    status=HealthStatus.UNKNOWN, message="No provider health data"
                )

            # Check if any provider is unhealthy
            unhealthy_providers = [
                name
                for name, health in self.provider_health.items()
                if health.get("status") == "unhealthy"
            ]

            if unhealthy_providers:
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message=f"Unhealthy providers: {', '.join(unhealthy_providers)}",
                    details={"provider_health": self.provider_health},
                )

            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="All providers healthy",
                details={"provider_health": self.provider_health},
            )

        self.health_check.add_check(check_router_health)
        self.health_check.add_check(check_circuit_breaker_health)
        self.health_check.add_check(check_provider_health)

    def _get_rate_limiter(self, tenant_id: Optional[str] = None) -> Optional[RateLimiter]:
        """
        Get or create rate limiter for tenant.
        
        Args:
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Optional[RateLimiter]: Result if available, else None.
        """
        if not self.config.enable_rate_limiting:
            return None

        key = tenant_id or "global"
        if key not in self.rate_limiters:
            self.rate_limiters[key] = RateLimiter(
                config=self.config.rate_limit_config or RateLimitConfig(), tenant_id=tenant_id
            )
        return self.rate_limiters[key]

    def _classify_error(self, error: Exception) -> Dict[str, Any]:
        """
        Classify error for advanced error handling.
        
        Args:
            error (Exception): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
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
            "authentication_error": False,
        }

        # Classify error
        if "rate limit" in error_message.lower() or "429" in error_message:
            classification.update(
                {"category": "rate_limit", "retryable": True, "rate_limit_error": True}
            )
        elif "timeout" in error_message.lower() or "timed out" in error_message.lower():
            classification.update({"category": "timeout", "retryable": True, "timeout_error": True})
        elif (
            "authentication" in error_message.lower()
            or "401" in error_message
            or "403" in error_message
        ):
            classification.update(
                {"category": "authentication", "retryable": False, "authentication_error": True}
            )
        elif "api" in error_type.lower() or "provider" in error_type.lower():
            classification.update(
                {"category": "provider", "retryable": True, "provider_error": True}
            )
        else:
            # Check for retryable patterns
            retryable_patterns = ["connection", "network", "temporary", "503", "502", "500"]
            if any(pattern in error_message.lower() for pattern in retryable_patterns):
                classification["retryable"] = True
                classification["category"] = "network"

        return classification

    async def get_health(self) -> Dict[str, Any]:
        """
        Get gateway health status.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        if not self.health_check:
            return {"status": "health_monitoring_disabled"}

        await self.health_check.check()
        health_info = self.health_check.get_health()

        # Add gateway-specific metrics
        health_info.update(
            {
                "circuit_breaker": (
                    self.circuit_breaker.get_stats() if self.circuit_breaker else None
                ),
                "rate_limiters": {
                    tenant: limiter.get_stats() for tenant, limiter in self.rate_limiters.items()
                },
                "provider_health": self.provider_health,
                "llmops": self.llmops.get_metrics() if self.llmops else None,
                "feedback_stats": (
                    self.feedback_loop.get_feedback_stats() if self.feedback_loop else None
                ),
            }
        )

        return health_info

    def _generate_cache_key(
        self,
        prompt: str,
        model: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        tenant_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate cache key for LLM request.
        
        This creates a deterministic cache key based on request parameters.
                                Identical requests (same prompt, model, tenant) will have the same key,
                                enabling cache hits and cost savings.
        
        Args:
            prompt (str): Prompt text sent to the model.
            model (str): Model name or identifier to use.
            messages (Optional[List[Dict[str, Any]]]): Chat messages in role/content format.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        # Create deterministic key from request parameters
        # All parameters are included to ensure cache key uniqueness
        key_data = {
            "prompt": prompt,
            "model": model,
            "messages": messages,
            "tenant_id": tenant_id,  # Tenant isolation: same prompt for different tenants = different cache keys
            **{
                k: v for k, v in kwargs.items() if k not in ["stream"]
            },  # Exclude stream (streaming can't be cached)
        }

        # Create hash for consistent key (SHA256, truncated to 16 chars for efficiency)
        key_string = json.dumps(key_data, sort_keys=True)  # Sort keys for deterministic hashing
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        return f"gateway:generate:{model}:{key_hash}"

    async def record_feedback(
        self,
        query: str,
        response: str,
        feedback_type: FeedbackType,
        content: str,
        tenant_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Record feedback for continuous learning asynchronously.
        
        Args:
            query (str): Input parameter for this operation.
            response (str): Input parameter for this operation.
            feedback_type (FeedbackType): Input parameter for this operation.
            content (str): Content text.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Optional[str]: Returned text value.
        """
        if not self.feedback_loop:
            return None

        return await self.feedback_loop.record_feedback(
            query=query,
            response=response,
            feedback_type=feedback_type,
            content=content,
            tenant_id=tenant_id,
        )

    def get_llmops_metrics(
        self, tenant_id: Optional[str] = None, time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get LLM operations metrics.
        
        Args:
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            time_range_hours (int): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        if not self.llmops:
            return {"error": "LLMOps not enabled"}

        return self.llmops.get_metrics(tenant_id=tenant_id, time_range_hours=time_range_hours)

    def get_cost_summary(
        self, tenant_id: Optional[str] = None, time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get cost summary.
        
        Args:
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            time_range_hours (int): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        if not self.llmops:
            return {"error": "LLMOps not enabled"}

        return self.llmops.get_cost_summary(tenant_id=tenant_id, time_range_hours=time_range_hours)

    def _execute_sync_generation(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool,
        **kwargs: Any,
    ) -> Any:
        """
        Execute synchronous LLM generation call.
        
        Args:
            model (str): Model name or identifier to use.
            messages (List[Dict[str, Any]]): Chat messages in role/content format.
            stream (bool): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        if self.router:
            return self.router.completion(
                model=model, messages=messages, stream=stream, **kwargs
            )
        else:
            return completion(model=model, messages=messages, stream=stream, **kwargs)

    async def generate(
        self,
        prompt: str,
        model: str = "gpt-4",
        tenant_id: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> GenerateResponse:
        """
        Generate text completion asynchronously.
        
        Args:
            prompt (str): Prompt text sent to the model.
            model (str): Model name or identifier to use.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            messages (Optional[List[Dict[str, Any]]]): Chat messages in role/content format.
            stream (bool): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            GenerateResponse: Result of the operation.
        """
        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        # Check KV cache
        kv_cache_key = await self._check_kv_cache(prompt, model, messages, tenant_id)

        # Execute generation
        response = self._execute_sync_generation(
            model=model, messages=messages, stream=stream, **kwargs
        )

        if stream:
            return response

        # Extract response data
        text, model_name, usage, finish_reason, raw_response = self._extract_response_data(
            response, model
        )

        result = GenerateResponse(
            text=text or "",
            model=model_name or model,
            usage=usage,
            finish_reason=finish_reason,
            raw_response=raw_response,
        )

        # Store KV cache
        if kv_cache_key:
            await self._store_kv_cache(kv_cache_key, prompt, model, tenant_id)

        return result

    async def _check_kv_cache(
        self, prompt: str, model: str, messages: List[Dict[str, Any]], tenant_id: Optional[str]
    ) -> Optional[str]:
        """
        Check KV cache for prompt context asynchronously.
        
        Args:
            prompt (str): Prompt text sent to the model.
            model (str): Model name or identifier to use.
            messages (List[Dict[str, Any]]): Chat messages in role/content format.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Optional[str]: Returned text value.
        """
        if not self.kv_cache:
            return None
        
        kv_cache_key = self.kv_cache.generate_cache_key(
            prompt=prompt, model=model, messages=messages
        )
        cached_kv = await self.kv_cache.get_kv_cache(kv_cache_key, tenant_id=tenant_id)
        if cached_kv:
            logger.debug(f"KV cache hit for prompt context: {kv_cache_key[:50]}...")
        return kv_cache_key

    async def _check_response_cache(
        self,
        prompt: str,
        model: str,
        messages: List[Dict[str, Any]],
        tenant_id: Optional[str],
        stream: bool,
        **kwargs: Any,
    ) -> Optional[GenerateResponse]:
        """
        Check cache for existing response asynchronously.
        
        Args:
            prompt (str): Prompt text sent to the model.
            model (str): Model name or identifier to use.
            messages (List[Dict[str, Any]]): Chat messages in role/content format.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            stream (bool): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Optional[GenerateResponse]: Result if available, else None.
        """
        if not self.cache or stream or not self.config.enable_caching:
            return None
        
        cache_key = self._generate_cache_key(
            prompt=prompt, model=model, messages=messages, tenant_id=tenant_id, **kwargs
        )
        cached_response = await self.cache.get(cache_key, tenant_id=tenant_id)
        if not cached_response:
            return None
        
        if isinstance(cached_response, dict):
            return GenerateResponse(
                text=cached_response.get("text", ""),
                model=cached_response.get("model", model),
                usage=cached_response.get("usage"),
                finish_reason=cached_response.get("finish_reason"),
                raw_response=cached_response.get("raw_response"),
            )
        return cached_response

    def _extract_token_usage(self, response: Any, prompt_tokens: List[int], completion_tokens: List[int]) -> None:
        """
        Extract token usage from response.
        
        Args:
            response (Any): Input parameter for this operation.
            prompt_tokens (List[int]): Input parameter for this operation.
            completion_tokens (List[int]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        if hasattr(response, "usage") and response.usage:
            prompt_tokens[0] = getattr(response.usage, "prompt_tokens", 0) or 0
            completion_tokens[0] = getattr(response.usage, "completion_tokens", 0) or 0

    def _update_provider_health_success(self, model: str) -> None:
        """
        Update provider health after successful generation.
        
        Args:
            model (str): Model name or identifier to use.
        
        Returns:
            None: Result of the operation.
        """
        provider_name = model.split("/")[0] if "/" in model else "default"
        self.provider_health[provider_name] = {
            "status": "healthy",
            "last_success": datetime.now().isoformat(),
            "last_check": datetime.now().isoformat(),
        }

    def _update_provider_health_error(
        self, model: str, error_msg: str, error_classification: Dict[str, Any]
    ) -> None:
        """
        Update provider health after error.
        
        Args:
            model (str): Model name or identifier to use.
            error_msg (str): Input parameter for this operation.
            error_classification (Dict[str, Any]): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        provider_name = model.split("/")[0] if "/" in model else "default"
        self.provider_health[provider_name] = {
            "status": "unhealthy" if not error_classification["retryable"] else "degraded",
            "last_error": error_msg,
            "error_classification": error_classification,
            "last_check": datetime.now().isoformat(),
        }

    def _determine_error_status(self, error_msg: str) -> LLMOperationStatus:
        """
        Determine operation status from error message.
        
        Args:
            error_msg (str): Input parameter for this operation.
        
        Returns:
            LLMOperationStatus: Result of the operation.
        """
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            return LLMOperationStatus.RATE_LIMITED
        elif "timeout" in error_msg.lower():
            return LLMOperationStatus.TIMEOUT
        else:
            return LLMOperationStatus.ERROR

    async def _execute_generation(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool,
        prompt_tokens: List[int],
        completion_tokens: List[int],
        error_message: List[Optional[str]],
        status: List[LLMOperationStatus],
        **kwargs: Any,
    ) -> Any:
        """
        Execute the actual LLM generation call.
        
        Args:
            model (str): Model name or identifier to use.
            messages (List[Dict[str, Any]]): Chat messages in role/content format.
            stream (bool): Input parameter for this operation.
            prompt_tokens (List[int]): Input parameter for this operation.
            completion_tokens (List[int]): Input parameter for this operation.
            error_message (List[Optional[str]]): Input parameter for this operation.
            status (List[LLMOperationStatus]): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        """
        try:
            if self.router:
                # Type ignore needed because litellm's router type stubs are incomplete
                response = await self.router.acompletion(
                    model=model, messages=messages, stream=stream, **kwargs  # type: ignore[arg-type]
                )
            else:
                response = await acompletion(
                    model=model, messages=messages, stream=stream, **kwargs
                )

            self._extract_token_usage(response, prompt_tokens, completion_tokens)
            self._update_provider_health_success(model)
            return response

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Handle validation/parsing errors specifically
            error_classification = self._classify_error(e)
            error_message[0] = str(e)
            status[0] = self._determine_error_status(error_message[0])
            self._update_provider_health_error(model, error_message[0], error_classification)
            raise
        except Exception as e:
            # Catch-all for other exceptions (network, API errors, etc.)
            error_classification = self._classify_error(e)
            error_message[0] = str(e)
            status[0] = self._determine_error_status(error_message[0])
            self._update_provider_health_error(model, error_message[0], error_classification)
            raise

    def _extract_response_data(
        self, response: Any, model: str
    ) -> tuple[str, str, Optional[Dict[str, Any]], Optional[str], Any]:
        """
        Extract text, model, usage, finish_reason, and raw_response from response.
        
        Args:
            response (Any): Input parameter for this operation.
            model (str): Model name or identifier to use.
        
        Returns:
            tuple[str, str, Optional[Dict[str, Any]], Optional[str], Any]: Dictionary result of the operation.
        """
        if hasattr(response, "choices") and len(response.choices) > 0:
            text = response.choices[0].message.content
            model_name = response.model if hasattr(response, "model") else model
            usage = response.usage.__dict__ if hasattr(response, "usage") else None
            finish_reason = (
                response.choices[0].finish_reason
                if hasattr(response.choices[0], "finish_reason")
                else None
            )
            raw_response = response.__dict__ if hasattr(response, "__dict__") else response
        elif isinstance(response, dict):
            text = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            model_name = response.get("model", model)
            usage = response.get("usage")
            finish_reason = response.get("choices", [{}])[0].get("finish_reason")
            raw_response = response
        else:
            text = str(response)
            model_name = model
            usage = None
            finish_reason = None
            raw_response = response.__dict__ if hasattr(response, "__dict__") else response
        
        return text, model_name, usage, finish_reason, raw_response

    async def _store_kv_cache(
        self, kv_cache_key: str, prompt: str, model: str, tenant_id: Optional[str]
    ) -> None:
        """
        Store KV cache entry asynchronously.
        
        Args:
            kv_cache_key (str): Input parameter for this operation.
            prompt (str): Prompt text sent to the model.
            model (str): Model name or identifier to use.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            None: Result of the operation.
        """
        if not self.kv_cache:
            return
        
        try:
            from .kv_cache import KVCacheEntry

            kv_entry = KVCacheEntry(
                cache_key=kv_cache_key,
                keys=[],  # Would contain attention keys in production
                values=[],  # Would contain attention values in production
                metadata={
                    "prompt": prompt[:100],
                    "model": model,
                    "timestamp": datetime.now().isoformat(),
                },
            )
            await self.kv_cache.set_kv_cache(kv_entry, tenant_id=tenant_id)
        except (AttributeError, ValueError, TypeError) as e:
            # Handle cache-related errors specifically
            logger.debug(f"Failed to store KV cache entry: {e}")
        except Exception as e:
            # Catch-all for unexpected errors (should not happen, but log for debugging)
            logger.warning(f"Unexpected error storing KV cache entry: {e}", exc_info=True)

    async def _store_response_cache(
        self,
        prompt: str,
        model: str,
        messages: List[Dict[str, Any]],
        tenant_id: Optional[str],
        text: str,
        model_name: str,
        usage: Optional[Dict[str, Any]],
        finish_reason: Optional[str],
        raw_response: Any,
        status: LLMOperationStatus,
        **kwargs: Any,
    ) -> None:
        """
        Store response in cache asynchronously.
        
        Args:
            prompt (str): Prompt text sent to the model.
            model (str): Model name or identifier to use.
            messages (List[Dict[str, Any]]): Chat messages in role/content format.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            text (str): Input parameter for this operation.
            model_name (str): Input parameter for this operation.
            usage (Optional[Dict[str, Any]]): Input parameter for this operation.
            finish_reason (Optional[str]): Input parameter for this operation.
            raw_response (Any): Input parameter for this operation.
            status (LLMOperationStatus): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        if (
            not self.cache
            or not self.config.enable_caching
            or status != LLMOperationStatus.SUCCESS
        ):
            return
        
        cache_key = self._generate_cache_key(
            prompt=prompt, model=model, messages=messages, tenant_id=tenant_id, **kwargs
        )
        cache_data = {
            "text": text,
            "model": model_name,
            "usage": usage,
            "finish_reason": finish_reason,
            "raw_response": raw_response,
        }
        await self.cache.set(
            cache_key,
            cache_data,
            tenant_id=tenant_id,
            ttl=self.config.cache_ttl,
        )

    async def generate_async(
        self,
        prompt: str,
        model: str = "gpt-4",
        tenant_id: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> GenerateResponse:
        """
        Generate text completion asynchronously with advanced features.
        
        Args:
            prompt (str): Prompt text sent to the model.
            model (str): Model name or identifier to use.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            messages (Optional[List[Dict[str, Any]]]): Chat messages in role/content format.
            stream (bool): Input parameter for this operation.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            GenerateResponse: Result of the operation.
        """
        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        # OTEL Integration: Start trace for LLM generation
        tracer = self.otel_tracer
        if tracer is None:
            try:
                from ..otel_integration import create_otel_tracer
                tracer = create_otel_tracer()
            except (ImportError, Exception):
                tracer = None

        # Track operation metrics
        start_time = time.time()

        if tracer:
            with tracer.start_trace("gateway.generate") as trace:
                trace.set_attribute("gateway.model", model)
                trace.set_attribute("gateway.prompt.length", len(prompt))
                from ..utils.tenant_utils import add_tenant_attributes_to_span
                add_tenant_attributes_to_span(trace, tenant_id, attribute_prefix="gateway")

                # Check KV cache span
                with tracer.start_span("gateway.cache.kv.check", parent=trace) as cache_span:
                    kv_cache_key = await self._check_kv_cache(prompt, model, messages, tenant_id)
                    cache_span.set_attribute("cache.kv.hit", kv_cache_key is not None)

                # Check response cache span
                with tracer.start_span("gateway.cache.response.check", parent=trace) as cache_span:
                    cached_response = await self._check_response_cache(
                        prompt, model, messages, tenant_id, stream, **kwargs
                    )
                    cache_span.set_attribute("cache.response.hit", cached_response is not None)
                    if cached_response:
                        # Record cache hit metrics
                        metrics = self.otel_metrics
                        if metrics is None:
                            try:
                                from ..otel_integration import create_otel_metrics
                                metrics = create_otel_metrics()
                            except (ImportError, Exception):
                                metrics = None
                        if metrics:
                            metrics.increment_counter("gateway.cache.hits", amount=1.0, attributes={
                                "model": model,
                            })
                        return cached_response

                # Rate limiting span
                rate_limiter = self._get_rate_limiter(tenant_id)
                if rate_limiter:
                    with tracer.start_span("gateway.rate_limit", parent=trace):
                        await rate_limiter.acquire()

                # Provider call span
                with tracer.start_span("gateway.provider.call", parent=trace) as provider_span:
                    provider_span.set_attribute("provider.model", model)
                    
                    try:
                        # Execute generation
                        otel_prompt_tokens: List[int] = [0]
                        otel_completion_tokens: List[int] = [0]
                        otel_error_message: List[Optional[str]] = [None]
                        otel_status_list: List[LLMOperationStatus] = [LLMOperationStatus.SUCCESS]

                        # Create generation function
                        async def _generate() -> Any:
                            return await self._execute_generation(
                                model=model,
                                messages=messages,
                                stream=stream,
                                prompt_tokens=otel_prompt_tokens,
                                completion_tokens=otel_completion_tokens,
                                error_message=otel_error_message,
                                status=otel_status_list,
                                **kwargs,
                            )

                        # Execute with appropriate strategy
                        if self.deduplicator and not stream:
                            response = await self.deduplicator.get_or_execute(
                                _generate, prompt=prompt, model=model, messages=messages, stream=stream, **kwargs
                            )
                        elif self.batcher and not stream:
                            batch_key = f"{model}_{tenant_id or 'global'}"
                            response = await self.batcher.batch_execute(
                                batch_key,
                                _generate,
                                prompt=prompt,
                                model=model,
                                messages=messages,
                                stream=stream,
                                **kwargs,
                            )
                        elif self.circuit_breaker:
                            response = await self.circuit_breaker.call(_generate)
                        else:
                            response = await _generate()

                        if stream:
                            return response

                        # Extract response data
                        text, model_name, usage, finish_reason, raw_response = self._extract_response_data(
                            response, model
                        )

                        # Set span attributes with response data
                        if usage:
                            prompt_tokens = usage.get("prompt_tokens", 0)
                            completion_tokens = usage.get("completion_tokens", 0)
                            total_tokens = usage.get("total_tokens", 0)
                            provider_span.set_attribute("tokens.prompt", prompt_tokens)
                            provider_span.set_attribute("tokens.completion", completion_tokens)
                            provider_span.set_attribute("tokens.total", total_tokens)

                        generate_response = GenerateResponse(
                            text=text,
                            model=model_name,
                            usage=usage,
                            finish_reason=finish_reason,
                            raw_response=raw_response,
                        )

                        # Record metrics
                        duration = time.time() - start_time
                        metrics = self.otel_metrics
                        if metrics is None:
                            try:
                                from ..otel_integration import create_otel_metrics
                                metrics = create_otel_metrics()
                            except (ImportError, Exception):
                                metrics = None

                        if metrics and usage:
                            total_tokens = usage.get("total_tokens", 0)
                            metrics.record_histogram("gateway.tokens.used", total_tokens, {
                                "model": model_name,
                            })
                            metrics.record_histogram("gateway.request.duration", duration, {
                                "model": model_name,
                            })
                            metrics.increment_counter("gateway.provider.calls", amount=1.0, attributes={
                                "model": model_name,
                                "status": "success",
                            })

                        # Store KV cache
                        if kv_cache_key:
                            await self._store_kv_cache(kv_cache_key, prompt, model, tenant_id)

                        # Store response cache
                        await self._store_response_cache(
                            prompt=prompt,
                            model=model,
                            messages=messages,
                            tenant_id=tenant_id,
                            text=text,
                            model_name=model_name,
                            usage=usage,
                            finish_reason=finish_reason,
                            raw_response=raw_response,
                            status=LLMOperationStatus.SUCCESS,
                            **kwargs,
                        )

                        # Log operation to LLMOps
                        if self.llmops:
                            latency_ms = (time.time() - start_time) * 1000
                            prompt_tokens = usage.get("prompt_tokens", 0) if usage else 0
                            completion_tokens = usage.get("completion_tokens", 0) if usage else 0
                            await self.llmops.log_operation(
                                operation_type=LLMOperationType.COMPLETION,
                                model=model_name,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                latency_ms=latency_ms,
                                status=LLMOperationStatus.SUCCESS,
                                error_message=None,
                                tenant_id=tenant_id,
                                metadata={"stream": stream},
                            )

                        return generate_response

                    except Exception as e:
                        provider_span.record_exception(e)
                        duration = time.time() - start_time

                        # Record error metrics
                        metrics = self.otel_metrics
                        if metrics is None:
                            try:
                                from ..otel_integration import create_otel_metrics
                                metrics = create_otel_metrics()
                            except (ImportError, Exception):
                                metrics = None

                        if metrics:
                            metrics.record_histogram("gateway.request.duration", duration, {
                                "model": model,
                            })
                            metrics.increment_counter("gateway.provider.calls", amount=1.0, attributes={
                                "model": model,
                                "status": "error",
                                "error_type": type(e).__name__,
                            })
                        raise
        else:
            # No OTEL - execute without tracing
            # Check KV cache
            kv_cache_key = await self._check_kv_cache(prompt, model, messages, tenant_id)

            # Check response cache
            cached_response = await self._check_response_cache(
                prompt, model, messages, tenant_id, stream, **kwargs
            )
            if cached_response:
                return cached_response

            # Rate limiting
            rate_limiter = self._get_rate_limiter(tenant_id)
            if rate_limiter:
                await rate_limiter.acquire()

            no_otel_prompt_tokens: List[int] = [0]
            no_otel_completion_tokens: List[int] = [0]
            no_otel_error_message: List[Optional[str]] = [None]
            no_otel_status_list: List[LLMOperationStatus] = [LLMOperationStatus.SUCCESS]

            # Create generation function
            async def _generate() -> Any:
                return await self._execute_generation(
                    model=model,
                    messages=messages,
                    stream=stream,
                    prompt_tokens=no_otel_prompt_tokens,
                    completion_tokens=no_otel_completion_tokens,
                    error_message=no_otel_error_message,
                    status=no_otel_status_list,
                    **kwargs,
                )

            # Execute with appropriate strategy
            if self.deduplicator and not stream:
                response = await self.deduplicator.get_or_execute(
                    _generate, prompt=prompt, model=model, messages=messages, stream=stream, **kwargs
                )
            elif self.batcher and not stream:
                batch_key = f"{model}_{tenant_id or 'global'}"
                response = await self.batcher.batch_execute(
                    batch_key,
                    _generate,
                    prompt=prompt,
                    model=model,
                    messages=messages,
                    stream=stream,
                    **kwargs,
                )
            elif self.circuit_breaker:
                response = await self.circuit_breaker.call(_generate)
            else:
                response = await _generate()

            if stream:
                return response

            # Log operation
            status = no_otel_status_list[0]
            if self.llmops:
                latency_ms = (time.time() - start_time) * 1000
                await self.llmops.log_operation(
                    operation_type=LLMOperationType.COMPLETION,
                    model=model,
                    prompt_tokens=no_otel_prompt_tokens[0],
                    completion_tokens=no_otel_completion_tokens[0],
                    latency_ms=latency_ms,
                    status=status,
                    error_message=no_otel_error_message[0],
                    tenant_id=tenant_id,
                    metadata={"stream": stream},
                )

            # Extract response data
            text, model_name, usage, finish_reason, raw_response = self._extract_response_data(
                response, model
            )

            generate_response = GenerateResponse(
                text=text,
                model=model_name,
                usage=usage,
                finish_reason=finish_reason,
                raw_response=raw_response,
            )

            # Store KV cache
            if kv_cache_key:
                await self._store_kv_cache(kv_cache_key, prompt, model, tenant_id)

            # Store response cache
            await self._store_response_cache(
                prompt=prompt,
                model=model,
                messages=messages,
                tenant_id=tenant_id,
                text=text,
                model_name=model_name,
                usage=usage,
                finish_reason=finish_reason,
                raw_response=raw_response,
                status=status,
                **kwargs,
            )

            return generate_response

    def embed(
        self, texts: List[str], model: str = "text-embedding-3-small", **kwargs: Any
    ) -> EmbedResponse:
        """
        Generate embeddings.
        
        Args:
            texts (List[str]): Input parameter for this operation.
            model (str): Model name or identifier to use.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            EmbedResponse: Result of the operation.
        """
        if self.router:
            response = self.router.embedding(model=model, input=texts, **kwargs)
        else:
            response = embedding(model=model, input=texts, **kwargs)

        # Extract embeddings
        if hasattr(response, "data"):
            embeddings = [item.embedding for item in response.data]
            model_name = response.model if hasattr(response, "model") else model
            usage = response.usage.__dict__ if hasattr(response, "usage") else None
        elif isinstance(response, dict):
            embeddings = [item.get("embedding", []) for item in response.get("data", [])]
            model_name = response.get("model", model)
            usage = response.get("usage")
        else:
            embeddings = []
            model_name = model
            usage = None

        return EmbedResponse(embeddings=embeddings, model=model_name or model, usage=usage)

    def _extract_embeddings_from_object(
        self, response: Any, model: str
    ) -> tuple[List[List[float]], str, Optional[Dict[str, Any]]]:
        """
        Extract embeddings from response object with attributes.
        
        Args:
            response (Any): Input parameter for this operation.
            model (str): Model name or identifier to use.
        
        Returns:
            tuple[List[List[float]], str, Optional[Dict[str, Any]]]: Dictionary result of the operation.
        """
        embeddings: List[List[float]] = []
        model_name: str = model
        usage: Optional[Dict[str, Any]] = None

        if hasattr(response, "data") and response.data:
            data_list = response.data if isinstance(response.data, list) else []
            embeddings = [item.embedding for item in data_list if hasattr(item, "embedding")]
            if hasattr(response, "model"):
                model_name = response.model or model
            if hasattr(response, "usage") and response.usage:
                usage = response.usage.__dict__ if hasattr(response.usage, "__dict__") else None

        return embeddings, model_name, usage

    def _extract_embeddings_from_dict(
        self, response: dict, model: str
    ) -> tuple[List[List[float]], str, Optional[Dict[str, Any]]]:
        """
        Extract embeddings from dict response.
        
        Args:
            response (dict): Input parameter for this operation.
            model (str): Model name or identifier to use.
        
        Returns:
            tuple[List[List[float]], str, Optional[Dict[str, Any]]]: Dictionary result of the operation.
        """
        embeddings: List[List[float]] = []
        data = response.get("data", [])
        if data and isinstance(data, list):
            embeddings = [item.get("embedding", []) for item in data if isinstance(item, dict)]
        model_name = response.get("model", model) or model
        usage = response.get("usage")
        return embeddings, model_name, usage

    async def embed_async(
        self, texts: List[str], model: str = "text-embedding-3-small", **kwargs: Any
    ) -> EmbedResponse:
        """
        Generate embeddings asynchronously.
        
        Args:
            texts (List[str]): Input parameter for this operation.
            model (str): Model name or identifier to use.
            **kwargs (Any): Input parameter for this operation.
        
        Returns:
            EmbedResponse: Result of the operation.
        """
        if self.router:
            response = await self.router.aembedding(model=model, input=texts, **kwargs)
        else:
            response = await aembedding(model=model, input=texts, **kwargs)

        # Extract embeddings (litellm types are incomplete, using runtime checks)
        if isinstance(response, dict):
            embeddings, model_name, usage = self._extract_embeddings_from_dict(response, model)
        else:
            embeddings, model_name, usage = self._extract_embeddings_from_object(response, model)

        return EmbedResponse(embeddings=embeddings, model=model_name or model, usage=usage)

    async def encode_llm_request(
        self,
        request_id: str,
        prompt: str,
        model: str,
        tenant_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Encode an LLM request to bytes using codec serializer.
        
        Args:
            request_id: Unique request identifier
            prompt: Prompt text
            model: Model name
            tenant_id: Tenant identifier
            parameters: Optional request parameters
        
        Returns:
            Encoded bytes
        
        Raises:
            ValueError: If codec serializer is not configured
        """
        if not self.codec_serializer:
            # Try to import and use default codec serializer
            try:
                from ..codec_integration import encode_llm_request
                return await encode_llm_request(
                    request_id=request_id,
                    prompt=prompt,
                    model=model,
                    tenant_id=tenant_id or "",
                    parameters=parameters,
                    codec=None,  # Use default codec
                )
            except ImportError:
                raise ValueError("Codec serializer not configured and codec_integration not available")
        
        from ..codec_integration import encode_llm_request
        return await encode_llm_request(
            request_id=request_id,
            prompt=prompt,
            model=model,
            tenant_id=tenant_id or "",
            parameters=parameters,
            codec=self.codec_serializer,
        )

    async def decode_llm_response(self, payload: bytes) -> Dict[str, Any]:
        """
        Decode bytes to LLM response dictionary using codec serializer.
        
        Args:
            payload: Encoded bytes to decode
        
        Returns:
            Decoded response dictionary
        
        Raises:
            ValueError: If codec serializer is not configured
        """
        if not self.codec_serializer:
            # Try to import and use default codec serializer
            try:
                from ..codec_integration import decode_llm_response
                return await decode_llm_response(payload, codec=None)  # Use default codec
            except ImportError:
                raise ValueError("Codec serializer not configured and codec_integration not available")
        
        from ..codec_integration import decode_llm_response
        return await decode_llm_response(payload, codec=self.codec_serializer)
