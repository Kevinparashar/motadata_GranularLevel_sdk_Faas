"""
Feedback Loop System

Implements feedback mechanisms for continuous learning and improvement in AI systems.
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import json
from pathlib import Path


class FeedbackType(str, Enum):
    """Types of feedback."""
    CORRECTION = "correction"  # User corrected the output
    RATING = "rating"  # User rated the output
    USEFUL = "useful"  # User marked as useful/not useful
    IMPROVEMENT = "improvement"  # User suggested improvement
    ERROR = "error"  # System error was reported


class FeedbackStatus(str, Enum):
    """Feedback processing status."""
    PENDING = "pending"
    PROCESSED = "processed"
    APPLIED = "applied"
    IGNORED = "ignored"


@dataclass
class FeedbackItem:
    """Individual feedback item."""
    feedback_id: str
    query: str
    response: str
    feedback_type: FeedbackType
    content: str  # Correction text, rating value, or improvement suggestion
    timestamp: datetime = field(default_factory=datetime.now)
    status: FeedbackStatus = FeedbackStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    tenant_id: Optional[str] = None
    agent_id: Optional[str] = None
    tool_id: Optional[str] = None  # Added for tool feedback support


class FeedbackLoop:
    """
    Feedback loop system for continuous learning and improvement.
    
    Collects user feedback, learns from corrections, and updates
    knowledge bases and models accordingly.
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        auto_process: bool = True
    ):
        """
        Initialize feedback loop.
        
        Args:
            storage_path: Optional path for persistent storage
            auto_process: Whether to automatically process feedback
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.auto_process = auto_process
        self.feedback_queue: List[FeedbackItem] = []
        self.processed_feedback: List[FeedbackItem] = []
        self.callbacks: Dict[FeedbackType, List[Callable]] = {
            FeedbackType.CORRECTION: [],
            FeedbackType.RATING: [],
            FeedbackType.USEFUL: [],
            FeedbackType.IMPROVEMENT: [],
            FeedbackType.ERROR: []
        }
        
        if self.storage_path and self.storage_path.exists():
            self._load()
    
    def record_feedback(
        self,
        query: str,
        response: str,
        feedback_type: FeedbackType,
        content: str,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Record user feedback.
        
        Args:
            query: Original query
            response: System response
            feedback_type: Type of feedback
            content: Feedback content (correction, rating, etc.)
            tenant_id: Optional tenant ID
            agent_id: Optional agent ID
            metadata: Optional metadata
        
        Returns:
            Feedback ID
        """
        import uuid
        
        feedback_id = str(uuid.uuid4())
        feedback = FeedbackItem(
            feedback_id=feedback_id,
            query=query,
            response=response,
            feedback_type=feedback_type,
            content=content,
            tenant_id=tenant_id,
            agent_id=agent_id,
            metadata=metadata or {}
        )
        
        self.feedback_queue.append(feedback)
        
        if self.auto_process:
            self.process_feedback(feedback_id)
        
        self._persist()
        
        return feedback_id
    
    def process_feedback(self, feedback_id: str) -> bool:
        """
        Process a feedback item.
        
        Args:
            feedback_id: Feedback ID to process
        
        Returns:
            True if processed successfully
        """
        feedback = next(
            (f for f in self.feedback_queue if f.feedback_id == feedback_id),
            None
        )
        
        if not feedback:
            return False
        
        # Call registered callbacks
        callbacks = self.callbacks.get(feedback.feedback_type, [])
        for callback in callbacks:
            try:
                callback(feedback)
            except Exception as e:
                # Log error but continue
                pass
        
        feedback.status = FeedbackStatus.PROCESSED
        self.feedback_queue.remove(feedback)
        self.processed_feedback.append(feedback)
        
        self._persist()
        
        return True
    
    def register_callback(
        self,
        feedback_type: FeedbackType,
        callback: Callable[[FeedbackItem], None]
    ) -> None:
        """
        Register a callback for specific feedback type.
        
        Args:
            feedback_type: Type of feedback
            callback: Callback function
        """
        if feedback_type not in self.callbacks:
            self.callbacks[feedback_type] = []
        self.callbacks[feedback_type].append(callback)
    
    def get_feedback_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get feedback statistics.
        
        Args:
            tenant_id: Optional tenant ID filter
        
        Returns:
            Dictionary with feedback statistics
        """
        all_feedback = self.feedback_queue + self.processed_feedback
        
        if tenant_id:
            all_feedback = [f for f in all_feedback if f.tenant_id == tenant_id]
        
        stats = {
            "total": len(all_feedback),
            "pending": len([f for f in self.feedback_queue if not tenant_id or f.tenant_id == tenant_id]),
            "processed": len([f for f in self.processed_feedback if not tenant_id or f.tenant_id == tenant_id]),
            "by_type": {}
        }
        
        for feedback_type in FeedbackType:
            count = len([f for f in all_feedback if f.feedback_type == feedback_type])
            stats["by_type"][feedback_type.value] = count
        
        return stats
    
    def get_learning_insights(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract learning insights from feedback.
        
        Args:
            tenant_id: Optional tenant ID filter
        
        Returns:
            Dictionary with learning insights
        """
        processed = self.processed_feedback
        
        if tenant_id:
            processed = [f for f in processed if f.tenant_id == tenant_id]
        
        corrections = [f for f in processed if f.feedback_type == FeedbackType.CORRECTION]
        ratings = [f for f in processed if f.feedback_type == FeedbackType.RATING]
        errors = [f for f in processed if f.feedback_type == FeedbackType.ERROR]
        
        insights = {
            "total_corrections": len(corrections),
            "total_ratings": len(ratings),
            "total_errors": len(errors),
            "common_corrections": {},
            "error_patterns": [],
            "average_rating": 0.0
        }
        
        # Analyze corrections
        correction_patterns = {}
        for correction in corrections:
            pattern = correction.query[:50]  # First 50 chars as pattern
            correction_patterns[pattern] = correction_patterns.get(pattern, 0) + 1
        
        insights["common_corrections"] = dict(
            sorted(correction_patterns.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # Analyze ratings
        if ratings:
            rating_values = []
            for rating in ratings:
                try:
                    value = float(rating.content)
                    rating_values.append(value)
                except ValueError:
                    pass
            if rating_values:
                insights["average_rating"] = sum(rating_values) / len(rating_values)
        
        # Analyze errors
        error_patterns = {}
        for error in errors:
            error_type = error.metadata.get("error_type", "unknown")
            error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
        
        insights["error_patterns"] = [
            {"type": k, "count": v}
            for k, v in sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return insights
    
    def _persist(self) -> None:
        """Persist feedback to disk."""
        if not self.storage_path:
            return
        
        try:
            data = {
                "feedback_queue": [
                    {
                        "feedback_id": f.feedback_id,
                        "query": f.query,
                        "response": f.response,
                        "feedback_type": f.feedback_type.value,
                        "content": f.content,
                        "timestamp": f.timestamp.isoformat(),
                        "status": f.status.value,
                        "metadata": f.metadata,
                        "tenant_id": f.tenant_id,
                        "agent_id": f.agent_id
                    }
                    for f in self.feedback_queue
                ],
                "processed_feedback": [
                    {
                        "feedback_id": f.feedback_id,
                        "query": f.query,
                        "response": f.response,
                        "feedback_type": f.feedback_type.value,
                        "content": f.content,
                        "timestamp": f.timestamp.isoformat(),
                        "status": f.status.value,
                        "metadata": f.metadata,
                        "tenant_id": f.tenant_id,
                        "agent_id": f.agent_id
                    }
                    for f in self.processed_feedback[-1000:]  # Keep last 1000
                ]
            }
            
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with self.storage_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, default=str, indent=2)
        except Exception:
            # Silently fail persistence
            pass
    
    def _load(self) -> None:
        """Load feedback from disk."""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        try:
            with self.storage_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            def _parse_feedback(item: Dict[str, Any]) -> FeedbackItem:
                return FeedbackItem(
                    feedback_id=item["feedback_id"],
                    query=item["query"],
                    response=item["response"],
                    feedback_type=FeedbackType(item["feedback_type"]),
                    content=item["content"],
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    status=FeedbackStatus(item["status"]),
                    metadata=item.get("metadata", {}),
                    tenant_id=item.get("tenant_id"),
                    agent_id=item.get("agent_id")
                )
            
            self.feedback_queue = [
                _parse_feedback(item) for item in data.get("feedback_queue", [])
            ]
            self.processed_feedback = [
                _parse_feedback(item) for item in data.get("processed_feedback", [])
            ]
        except Exception:
            # Silently fail loading
            pass


