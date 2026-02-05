"""
LLMOps - LLM Operations and Monitoring

Comprehensive logging, monitoring, and operational management for LLM operations.
"""


import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class LLMOperationType(str, Enum):
    """Types of LLM operations."""

    COMPLETION = "completion"
    EMBEDDING = "embedding"
    CHAT = "chat"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"


class LLMOperationStatus(str, Enum):
    """Operation status."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    CANCELLED = "cancelled"


@dataclass
class LLMOperation:
    """LLM operation record."""

    operation_id: str
    operation_type: LLMOperationType
    model: str
    tenant_id: Optional[str] = None
    agent_id: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    status: LLMOperationStatus = LLMOperationStatus.SUCCESS
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMOps:
    """
    LLM Operations and Monitoring system.

    Tracks LLM operations, monitors performance, logs usage,
    and provides insights for optimization.
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        enable_logging: bool = True,
        enable_cost_tracking: bool = True,
    ):
        """
        Initialize LLMOps.
        
        Args:
            storage_path (Optional[str]): Input parameter for this operation.
            enable_logging (bool): Flag to enable or disable logging.
            enable_cost_tracking (bool): Flag to enable or disable cost tracking.
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.enable_logging = enable_logging
        self.enable_cost_tracking = enable_cost_tracking

        self.operations: List[LLMOperation] = []
        self.max_operations_in_memory = 10000

        # Cost tracking (per 1M tokens)
        self.model_costs: Dict[str, Dict[str, float]] = {
            "gpt-4": {"prompt": 30.0, "completion": 60.0},
            "gpt-4-turbo": {"prompt": 10.0, "completion": 30.0},
            "gpt-3.5-turbo": {"prompt": 0.5, "completion": 1.5},
            "claude-3-opus": {"prompt": 15.0, "completion": 75.0},
            "claude-3-sonnet": {"prompt": 3.0, "completion": 15.0},
            "claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
        }

    async def initialize(self) -> None:
        """
        Initialize LLMOps asynchronously (loads persisted operations).
        
        This should be called after __init__ to load operations from disk.
        
        Example:
            >>> llmops = LLMOps(storage_path="llmops.json")
            >>> await llmops.initialize()
        
        Returns:
            None: Result of the operation.
        """
        if self.storage_path and self.storage_path.exists():
            await self._load()

    async def log_operation(
        self,
        operation_type: LLMOperationType,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        status: LLMOperationStatus = LLMOperationStatus.SUCCESS,
        error_message: Optional[str] = None,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an LLM operation asynchronously.
        
        Args:
            operation_type (LLMOperationType): Input parameter for this operation.
            model (str): Model name or identifier to use.
            prompt_tokens (int): Input parameter for this operation.
            completion_tokens (int): Input parameter for this operation.
            latency_ms (float): Input parameter for this operation.
            status (LLMOperationStatus): Input parameter for this operation.
            error_message (Optional[str]): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            agent_id (Optional[str]): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            str: Returned text value.
        """
        if not self.enable_logging:
            return ""

        import uuid

        operation_id = str(uuid.uuid4())
        total_tokens = prompt_tokens + completion_tokens

        # Calculate cost
        cost_usd = 0.0
        if self.enable_cost_tracking:
            model_key = model.split("/")[-1] if "/" in model else model
            costs = self.model_costs.get(model_key, {"prompt": 0.0, "completion": 0.0})
            cost_usd = (prompt_tokens / 1_000_000) * costs.get("prompt", 0.0) + (
                completion_tokens / 1_000_000
            ) * costs.get("completion", 0.0)

        operation = LLMOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            model=model,
            tenant_id=tenant_id,
            agent_id=agent_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            status=status,
            error_message=error_message,
            metadata=metadata or {},
        )

        self.operations.append(operation)

        # Trim if exceeds max
        if len(self.operations) > self.max_operations_in_memory:
            self.operations = self.operations[-self.max_operations_in_memory :]

        await self._persist()

        return operation_id

    def get_metrics(
        self,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        time_range_hours: Optional[int] = 24,
    ) -> Dict[str, Any]:
        """
        Get LLM operation metrics.
        
        Args:
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            agent_id (Optional[str]): Input parameter for this operation.
            time_range_hours (Optional[int]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        cutoff = datetime.now()
        if time_range_hours:
            from datetime import timedelta

            cutoff = cutoff - timedelta(hours=time_range_hours)

        filtered = [
            op
            for op in self.operations
            if op.timestamp >= cutoff
            and (not tenant_id or op.tenant_id == tenant_id)
            and (not agent_id or op.agent_id == agent_id)
        ]

        if not filtered:
            return {
                "total_operations": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "average_latency_ms": 0.0,
                "success_rate": 0.0,
                "by_model": {},
                "by_type": {},
                "error_rate": 0.0,
            }

        total_operations = len(filtered)
        total_tokens = sum(op.total_tokens for op in filtered)
        total_cost = sum(op.cost_usd for op in filtered)
        avg_latency = sum(op.latency_ms for op in filtered) / total_operations
        success_count = len([op for op in filtered if op.status == LLMOperationStatus.SUCCESS])
        success_rate = success_count / total_operations if total_operations > 0 else 0.0
        error_count = len([op for op in filtered if op.status == LLMOperationStatus.ERROR])
        error_rate = error_count / total_operations if total_operations > 0 else 0.0

        # By model
        by_model = {}
        for op in filtered:
            if op.model not in by_model:
                by_model[op.model] = {
                    "count": 0,
                    "tokens": 0,
                    "cost_usd": 0.0,
                    "avg_latency_ms": 0.0,
                }
            by_model[op.model]["count"] += 1
            by_model[op.model]["tokens"] += op.total_tokens
            by_model[op.model]["cost_usd"] += op.cost_usd
            by_model[op.model]["avg_latency_ms"] += op.latency_ms

        for model in by_model:
            count = by_model[model]["count"]
            by_model[model]["avg_latency_ms"] /= count

        # By type
        by_type = {}
        for op in filtered:
            op_type = op.operation_type.value
            if op_type not in by_type:
                by_type[op_type] = {"count": 0, "tokens": 0}
            by_type[op_type]["count"] += 1
            by_type[op_type]["tokens"] += op.total_tokens

        return {
            "total_operations": total_operations,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "average_latency_ms": avg_latency,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "by_model": by_model,
            "by_type": by_type,
            "time_range_hours": time_range_hours,
        }

    def get_cost_summary(
        self, tenant_id: Optional[str] = None, time_range_hours: Optional[int] = 24
    ) -> Dict[str, Any]:
        """
        Get cost summary.
        
        Args:
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            time_range_hours (Optional[int]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        metrics = self.get_metrics(tenant_id=tenant_id, time_range_hours=time_range_hours)

        return {
            "total_cost_usd": metrics["total_cost_usd"],
            "total_tokens": metrics["total_tokens"],
            "cost_per_1k_tokens": (
                (metrics["total_cost_usd"] / metrics["total_tokens"]) * 1000
                if metrics["total_tokens"] > 0
                else 0.0
            ),
            "by_model": {
                model: {
                    "cost_usd": data["cost_usd"],
                    "tokens": data["tokens"],
                    "cost_per_1k_tokens": (
                        (data["cost_usd"] / data["tokens"]) * 1000 if data["tokens"] > 0 else 0.0
                    ),
                }
                for model, data in metrics["by_model"].items()
            },
            "time_range_hours": time_range_hours,
        }

    async def _persist(self) -> None:
        """
        Persist operations to disk asynchronously.
        
        Returns:
            None: Result of the operation.
        """
        import asyncio
        
        if not self.storage_path:
            return

        def _persist_sync() -> None:
            try:
                # Only persist recent operations
                recent_ops = self.operations[-1000:]

                data = {
                    "operations": [
                        {
                            "operation_id": op.operation_id,
                            "operation_type": op.operation_type.value,
                            "model": op.model,
                            "tenant_id": op.tenant_id,
                            "agent_id": op.agent_id,
                            "prompt_tokens": op.prompt_tokens,
                            "completion_tokens": op.completion_tokens,
                            "total_tokens": op.total_tokens,
                            "latency_ms": op.latency_ms,
                            "cost_usd": op.cost_usd,
                            "status": op.status.value,
                            "error_message": op.error_message,
                            "timestamp": op.timestamp.isoformat(),
                            "metadata": op.metadata,
                        }
                        for op in recent_ops
                    ]
                }

                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                with self.storage_path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, default=str, indent=2)
            except Exception:
                # Silently fail persistence
                pass
        
        # Run file I/O in thread pool to avoid blocking
        await asyncio.to_thread(_persist_sync)

    async def _load(self) -> None:
        """
        Load operations from disk asynchronously.
        
        Returns:
            None: Result of the operation.
        """
        import asyncio
        
        if not self.storage_path or not self.storage_path.exists():
            return

        def _load_sync() -> List[LLMOperation]:
            try:
                with self.storage_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                def _parse_operation(item: Dict[str, Any]) -> LLMOperation:
                    return LLMOperation(
                        operation_id=item["operation_id"],
                        operation_type=LLMOperationType(item["operation_type"]),
                        model=item["model"],
                        tenant_id=item.get("tenant_id"),
                        agent_id=item.get("agent_id"),
                        prompt_tokens=item["prompt_tokens"],
                        completion_tokens=item["completion_tokens"],
                        total_tokens=item["total_tokens"],
                        latency_ms=item["latency_ms"],
                        cost_usd=item["cost_usd"],
                        status=LLMOperationStatus(item["status"]),
                        error_message=item.get("error_message"),
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                        metadata=item.get("metadata", {}),
                    )

                return [_parse_operation(item) for item in data.get("operations", [])]
            except Exception:
                # Silently fail loading
                return []
        
        # Run file I/O in thread pool to avoid blocking
        self.operations = await asyncio.to_thread(_load_sync)
