"""
Unit Tests for Agent OTEL Integration

Tests for OpenTelemetry integration within the Agent Framework.
"""

import pytest

from src.core.agno_agent_framework.agent import Agent, AgentTask
from src.core.otel_integration import OTELMetrics, OTELTracer


class TestAgentOTELIntegration:
    """Tests for Agent OTEL integration."""

    def test_agent_with_otel_tracer(self):
        """Test agent initialization with OTEL tracer."""
        tracer = OTELTracer(service_name="test-agent")
        agent = Agent(
            agent_id="test_agent",
            name="Test Agent",
            otel_tracer=tracer,
        )
        
        assert agent.otel_tracer is not None
        assert agent.otel_tracer.service_name == "test-agent"

    def test_agent_with_otel_metrics(self):
        """Test agent initialization with OTEL metrics."""
        metrics = OTELMetrics(service_name="test-agent")
        agent = Agent(
            agent_id="test_agent",
            name="Test Agent",
            otel_metrics=metrics,
        )
        
        assert agent.otel_metrics is not None
        assert agent.otel_metrics.service_name == "test-agent"

    def test_agent_without_otel(self):
        """Test agent works without OTEL configured."""
        agent = Agent(
            agent_id="test_agent",
            name="Test Agent",
        )
        
        assert agent.otel_tracer is None
        assert agent.otel_metrics is None

    @pytest.mark.asyncio
    async def test_execute_task_with_otel(self):
        """Test task execution with OTEL tracing."""
        tracer = OTELTracer(service_name="test-agent")
        metrics = OTELMetrics(service_name="test-agent")
        
        agent = Agent(
            agent_id="test_agent",
            name="Test Agent",
            otel_tracer=tracer,
            otel_metrics=metrics,
        )
        
        task = AgentTask(
            task_id="test_task",
            task_type="test",
            parameters={},
        )
        
        # Execute task - should not raise exception
        result = await agent.execute_task(task)
        
        assert result is not None
        assert "status" in result or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_execute_task_without_otel(self):
        """Test task execution without OTEL."""
        agent = Agent(
            agent_id="test_agent",
            name="Test Agent",
        )
        
        task = AgentTask(
            task_id="test_task",
            task_type="test",
            parameters={},
        )
        
        # Execute task - should work without OTEL
        result = await agent.execute_task(task)
        
        assert result is not None

