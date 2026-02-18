"""
Feedback Integration

Integration with feedback loop system for agent and tool feedback collection.
"""


from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from ..feedback_loop import FeedbackLoop, FeedbackType
from ..utils.type_helpers import MetadataDict


class AgentFeedback(BaseModel):
    """Feedback for an agent."""

    agent_id: str
    rating: int = Field(ge=1, le=5)  # 1-5 stars
    feedback_text: Optional[str] = None
    effectiveness_score: float = Field(ge=0.0, le=1.0, default=0.0)
    user_id: str
    tenant_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: MetadataDict = Field(default_factory=dict)


class ToolFeedback(BaseModel):
    """Feedback for a tool."""

    tool_id: str
    rating: int = Field(ge=1, le=5)  # 1-5 stars
    feedback_text: Optional[str] = None
    performance_score: float = Field(ge=0.0, le=1.0, default=0.0)
    user_id: str
    tenant_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: MetadataDict = Field(default_factory=dict)


class FeedbackCollector:
    """
    Collects and processes feedback for agents and tools.

    Integrates with FeedbackLoop system to track effectiveness
    and enable continuous improvement.
    """

    def __init__(self, feedback_loop: Optional[FeedbackLoop] = None):
        """
        Initialize feedback collector.
        
        Args:
            feedback_loop (Optional[FeedbackLoop]): Input parameter for this operation.
        """
        self.feedback_loop = feedback_loop
        self._agent_feedback: Dict[str, list] = {}  # {agent_id: [feedback]}
        self._tool_feedback: Dict[str, list] = {}  # {tool_id: [feedback]}

    async def collect_agent_feedback(
        self,
        agent_id: str,
        rating: int,
        user_id: str,
        tenant_id: str,
        feedback_text: Optional[str] = None,
        effectiveness_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Collect feedback for an agent asynchronously.
        
        Args:
            agent_id (str): Input parameter for this operation.
            rating (int): Input parameter for this operation.
            user_id (str): User identifier (used for auditing or personalization).
            tenant_id (str): Tenant identifier used for tenant isolation.
            feedback_text (Optional[str]): Input parameter for this operation.
            effectiveness_score (Optional[float]): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            str: Returned text value.
        """
        feedback = AgentFeedback(
            agent_id=agent_id,
            rating=rating,
            feedback_text=feedback_text,
            effectiveness_score=effectiveness_score or (rating / 5.0),
            user_id=user_id,
            tenant_id=tenant_id,
            metadata=metadata or {},
        )

        if agent_id not in self._agent_feedback:
            self._agent_feedback[agent_id] = []

        self._agent_feedback[agent_id].append(feedback)

        # Also record in feedback loop if available
        if self.feedback_loop:
            await self.feedback_loop.record_feedback(
                query=f"Agent {agent_id} feedback",
                response=f"Rating: {rating}, Effectiveness: {feedback.effectiveness_score}",
                feedback_type=FeedbackType.RATING,
                content=str(rating),
                tenant_id=tenant_id,
                agent_id=agent_id,
                metadata={
                    "feedback_text": feedback_text,
                    "effectiveness_score": feedback.effectiveness_score,
                    **(metadata or {}),
                },
            )

        return feedback.agent_id

    async def collect_tool_feedback(
        self,
        tool_id: str,
        rating: int,
        user_id: str,
        tenant_id: str,
        feedback_text: Optional[str] = None,
        performance_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Collect feedback for a tool asynchronously.
        
        Args:
            tool_id (str): Tool identifier.
            rating (int): Input parameter for this operation.
            user_id (str): User identifier (used for auditing or personalization).
            tenant_id (str): Tenant identifier used for tenant isolation.
            feedback_text (Optional[str]): Input parameter for this operation.
            performance_score (Optional[float]): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            str: Returned text value.
        """
        feedback = ToolFeedback(
            tool_id=tool_id,
            rating=rating,
            feedback_text=feedback_text,
            performance_score=performance_score or (rating / 5.0),
            user_id=user_id,
            tenant_id=tenant_id,
            metadata=metadata or {},
        )

        if tool_id not in self._tool_feedback:
            self._tool_feedback[tool_id] = []

        self._tool_feedback[tool_id].append(feedback)

        # Also record in feedback loop if available
        if self.feedback_loop:
            await self.feedback_loop.record_feedback(
                query=f"Tool {tool_id} feedback",
                response=f"Rating: {rating}, Performance: {feedback.performance_score}",
                feedback_type=FeedbackType.RATING,
                content=str(rating),
                tenant_id=tenant_id,
                metadata={
                    "tool_id": tool_id,
                    "feedback_text": feedback_text,
                    "performance_score": feedback.performance_score,
                    **(metadata or {}),
                },
            )

        return feedback.tool_id

    def get_agent_feedback_stats(
        self, agent_id: str, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get feedback statistics for an agent.
        
        Args:
            agent_id (str): Input parameter for this operation.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        if agent_id not in self._agent_feedback:
            return {"total_feedback": 0, "average_rating": 0.0, "average_effectiveness": 0.0}

        feedback_list = self._agent_feedback[agent_id]

        if tenant_id:
            feedback_list = [f for f in feedback_list if f.tenant_id == tenant_id]

        if not feedback_list:
            return {"total_feedback": 0, "average_rating": 0.0, "average_effectiveness": 0.0}

        total = len(feedback_list)
        avg_rating = sum(f.rating for f in feedback_list) / total
        avg_effectiveness = sum(f.effectiveness_score for f in feedback_list) / total

        return {
            "total_feedback": total,
            "average_rating": round(avg_rating, 2),
            "average_effectiveness": round(avg_effectiveness, 2),
            "ratings_distribution": {
                "1": len([f for f in feedback_list if f.rating == 1]),
                "2": len([f for f in feedback_list if f.rating == 2]),
                "3": len([f for f in feedback_list if f.rating == 3]),
                "4": len([f for f in feedback_list if f.rating == 4]),
                "5": len([f for f in feedback_list if f.rating == 5]),
            },
        }

    def get_tool_feedback_stats(
        self, tool_id: str, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get feedback statistics for a tool.
        
        Args:
            tool_id (str): Tool identifier.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        if tool_id not in self._tool_feedback:
            return {"total_feedback": 0, "average_rating": 0.0, "average_performance": 0.0}

        feedback_list = self._tool_feedback[tool_id]

        if tenant_id:
            feedback_list = [f for f in feedback_list if f.tenant_id == tenant_id]

        if not feedback_list:
            return {"total_feedback": 0, "average_rating": 0.0, "average_performance": 0.0}

        total = len(feedback_list)
        avg_rating = sum(f.rating for f in feedback_list) / total
        avg_performance = sum(f.performance_score for f in feedback_list) / total

        return {
            "total_feedback": total,
            "average_rating": round(avg_rating, 2),
            "average_performance": round(avg_performance, 2),
            "ratings_distribution": {
                "1": len([f for f in feedback_list if f.rating == 1]),
                "2": len([f for f in feedback_list if f.rating == 2]),
                "3": len([f for f in feedback_list if f.rating == 3]),
                "4": len([f for f in feedback_list if f.rating == 4]),
                "5": len([f for f in feedback_list if f.rating == 5]),
            },
        }
