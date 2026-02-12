"""
Unit Tests for Agent Orchestration

Tests workflow pipelines, coordination patterns, and multi-agent orchestration.
"""


import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.agno_agent_framework.agent import Agent, AgentManager, AgentTask
from src.core.agno_agent_framework.exceptions import AgentNotFoundError, WorkflowNotFoundError
from src.core.agno_agent_framework.orchestration import (
    AgentOrchestrator,
    CoordinationPattern,
    WorkflowPipeline,
    WorkflowState,
    WorkflowStatus,
    WorkflowStep,
)


class TestWorkflowStatus:
    """Test WorkflowStatus enum."""

    def test_workflow_status_values(self):
        """Test WorkflowStatus enum values."""
        assert WorkflowStatus.PENDING == "pending"
        assert WorkflowStatus.RUNNING == "running"
        assert WorkflowStatus.COMPLETED == "completed"
        assert WorkflowStatus.FAILED == "failed"
        assert WorkflowStatus.CANCELLED == "cancelled"
        assert WorkflowStatus.PAUSED == "paused"


class TestCoordinationPattern:
    """Test CoordinationPattern enum."""

    def test_coordination_pattern_values(self):
        """Test CoordinationPattern enum values."""
        assert CoordinationPattern.LEADER_FOLLOWER == "leader_follower"
        assert CoordinationPattern.PEER_TO_PEER == "peer_to_peer"
        assert CoordinationPattern.HIERARCHICAL == "hierarchical"
        assert CoordinationPattern.PIPELINE == "pipeline"
        assert CoordinationPattern.BROADCAST == "broadcast"


class TestWorkflowStep:
    """Test WorkflowStep class."""

    def test_workflow_step_init(self):
        """Test WorkflowStep initialization to cover lines 74-86."""
        step = WorkflowStep(
            step_id="step1",
            agent_id="agent1",
            task_type="test_task",
            parameters={"key": "value"},
            depends_on=["step0"],
            condition=lambda ctx: ctx.get("enabled", True),
            retry_count=3,
            timeout=30.0,
        )

        assert step.step_id == "step1"
        assert step.agent_id == "agent1"
        assert step.task_type == "test_task"
        assert step.parameters == {"key": "value"}
        assert step.depends_on == ["step0"]
        assert step.condition is not None
        assert step.retry_count == 3
        assert abs(step.timeout - 30.0) < 0.001
        assert step.status == WorkflowStatus.PENDING
        assert step.result is None
        assert step.error is None
        assert step.started_at is None
        assert step.completed_at is None

    def test_workflow_step_init_defaults(self):
        """Test WorkflowStep initialization with defaults."""
        step = WorkflowStep(
            step_id="step1",
            agent_id="agent1",
            task_type="test_task",
            parameters={},
        )

        assert step.depends_on == []
        assert step.condition is None
        assert step.retry_count == 0
        assert step.timeout is None


class TestWorkflowState:
    """Test WorkflowState dataclass."""

    def test_workflow_state_init(self):
        """Test WorkflowState initialization."""
        state = WorkflowState(workflow_id="workflow1")

        assert state.workflow_id == "workflow1"
        assert state.status == WorkflowStatus.PENDING
        assert state.current_step is None
        assert len(state.completed_steps) == 0
        assert len(state.failed_steps) == 0
        assert len(state.step_results) == 0
        assert len(state.context) == 0


class TestWorkflowPipeline:
    """Test WorkflowPipeline class."""

    def test_workflow_pipeline_init(self):
        """Test WorkflowPipeline initialization to cover lines 124-128."""
        pipeline = WorkflowPipeline(name="test_workflow", description="Test description")

        assert pipeline.name == "test_workflow"
        assert pipeline.description == "Test description"
        assert pipeline.pipeline_id is not None
        assert len(pipeline.steps) == 0
        assert pipeline.state.workflow_id == pipeline.pipeline_id

    def test_workflow_pipeline_init_with_id(self):
        """Test WorkflowPipeline initialization with custom ID."""
        pipeline = WorkflowPipeline(pipeline_id="custom_id", name="test")

        assert pipeline.pipeline_id == "custom_id"

    def test_add_step(self):
        """Test add_step method to cover lines 157-169."""
        pipeline = WorkflowPipeline()

        step_id = pipeline.add_step(
            agent_id="agent1",
            task_type="test_task",
            parameters={"key": "value"},
            step_id="step1",
            depends_on=["step0"],
            retry_count=2,
            timeout=10.0,
        )

        assert step_id == "step1"
        assert len(pipeline.steps) == 1
        step = pipeline.steps[0]
        assert step.step_id == "step1"
        assert step.agent_id == "agent1"
        assert step.task_type == "test_task"
        assert step.parameters == {"key": "value"}
        assert step.depends_on == ["step0"]
        assert step.retry_count == 2
        assert abs(step.timeout - 10.0) < 0.001

    def test_add_step_auto_id(self):
        """Test add_step with auto-generated step_id."""
        pipeline = WorkflowPipeline()

        step_id1 = pipeline.add_step("agent1", "task1", {})
        step_id2 = pipeline.add_step("agent2", "task2", {})

        assert step_id1 == "step_1"
        assert step_id2 == "step_2"
        assert len(pipeline.steps) == 2

    def test_get_ready_steps(self):
        """Test _get_ready_steps method to cover lines 178-188."""
        pipeline = WorkflowPipeline()

        # Add steps with dependencies
        step1_id = pipeline.add_step("agent1", "task1", {}, step_id="step1")
        step2_id = pipeline.add_step("agent2", "task2", {}, step_id="step2", depends_on=["step1"])

        # Initially, only step1 should be ready (no dependencies)
        ready = pipeline._get_ready_steps()
        assert len(ready) == 1
        assert ready[0].step_id == step1_id

        # Mark step1 as completed (both status and completed_steps)
        pipeline.steps[0].status = WorkflowStatus.COMPLETED
        pipeline.state.completed_steps.add(step1_id)

        # Now step2 should be ready (step1 is no longer PENDING, so it won't be in ready list)
        ready = pipeline._get_ready_steps()
        assert len(ready) == 1
        assert ready[0].step_id == step2_id

    def test_get_ready_steps_with_condition(self):
        """Test _get_ready_steps with condition."""
        pipeline = WorkflowPipeline()

        def condition(ctx):
            return ctx.get("enabled", False)

        step_id = pipeline.add_step(
            "agent1", "task1", {}, step_id="step1", condition=condition
        )

        # Step should not be ready if condition is False
        ready = pipeline._get_ready_steps()
        assert len(ready) == 0

        # Set context to enable step
        pipeline.state.context["enabled"] = True

        # Now step should be ready
        ready = pipeline._get_ready_steps()
        assert len(ready) == 1
        assert ready[0].step_id == step_id

    @pytest.mark.asyncio
    async def test_execute_simple_workflow(self):
        """Test execute method with simple workflow to cover lines 203-238."""
        pipeline = WorkflowPipeline()

        # Create mock agent
        mock_agent = MagicMock(spec=Agent)
        mock_agent.execute_task = AsyncMock(return_value={"result": "success"})

        # Create mock agent manager
        mock_manager = MagicMock(spec=AgentManager)
        mock_manager.get_agent = MagicMock(return_value=mock_agent)

        # Add a step
        pipeline.add_step("agent1", "task1", {"param": "value"})

        # Execute workflow
        result = await pipeline.execute(mock_manager, {"context": "data"})

        assert result["status"] == "completed"
        assert "results" in result
        assert "context" in result
        assert result["context"]["context"] == "data"

    @pytest.mark.asyncio
    async def test_execute_workflow_with_dependencies(self):
        """Test execute with step dependencies."""
        pipeline = WorkflowPipeline()

        mock_agent = MagicMock(spec=Agent)
        mock_agent.execute_task = AsyncMock(return_value={"result": "success"})

        mock_manager = MagicMock(spec=AgentManager)
        mock_manager.get_agent = MagicMock(return_value=mock_agent)

        # Add steps with dependency
        step1_id = pipeline.add_step("agent1", "task1", {}, step_id="step1")
        pipeline.add_step("agent2", "task2", {}, step_id="step2", depends_on=["step1"])

        result = await pipeline.execute(mock_manager)

        assert result["status"] == "completed"
        assert step1_id in pipeline.state.completed_steps

    @pytest.mark.asyncio
    async def test_execute_workflow_with_failure(self):
        """Test execute with step failure."""
        pipeline = WorkflowPipeline()

        mock_agent = MagicMock(spec=Agent)
        mock_agent.execute_task = AsyncMock(side_effect=RuntimeError("Task failed"))

        mock_manager = MagicMock(spec=AgentManager)
        mock_manager.get_agent = MagicMock(return_value=mock_agent)

        pipeline.add_step("agent1", "task1", {})

        result = await pipeline.execute(mock_manager)

        assert result["status"] == "failed"
        assert len(pipeline.state.failed_steps) > 0

    @pytest.mark.asyncio
    async def test_execute_workflow_agent_not_found(self):
        """Test execute when agent is not found."""
        pipeline = WorkflowPipeline()

        mock_manager = MagicMock(spec=AgentManager)
        mock_manager.get_agent = MagicMock(return_value=None)

        pipeline.add_step("nonexistent_agent", "task1", {})

        result = await pipeline.execute(mock_manager)

        assert result["status"] == "failed"
        assert len(pipeline.state.failed_steps) > 0

    @pytest.mark.asyncio
    async def test_execute_step_with_timeout(self):
        """Test _execute_step with timeout."""
        pipeline = WorkflowPipeline()

        mock_agent = MagicMock(spec=Agent)
        # Simulate slow task
        async def slow_task(task):
            await asyncio.sleep(2)
            return {"result": "success"}

        mock_agent.execute_task = slow_task

        mock_manager = MagicMock(spec=AgentManager)
        mock_manager.get_agent = MagicMock(return_value=mock_agent)

        step = WorkflowStep("step1", "agent1", "task1", {}, timeout=0.1)

        await pipeline._execute_step(step, mock_manager)

        assert step.status == WorkflowStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_step_with_retry(self):
        """Test _execute_step with retries."""
        pipeline = WorkflowPipeline()

        mock_agent = MagicMock(spec=Agent)
        call_count = 0

        async def failing_then_success(task):  # noqa: ARG001
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0)  # Use async feature
            if call_count < 2:
                raise RuntimeError("Temporary failure")
            return {"result": "success"}

        mock_agent.execute_task = failing_then_success

        mock_manager = MagicMock(spec=AgentManager)
        mock_manager.get_agent = MagicMock(return_value=mock_agent)

        step = WorkflowStep("step1", "agent1", "task1", {}, retry_count=2)

        await pipeline._execute_step(step, mock_manager)

        assert step.status == WorkflowStatus.COMPLETED
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_execute_step_retry_exhausted(self):
        """Test _execute_step when retries are exhausted."""
        pipeline = WorkflowPipeline()

        mock_agent = MagicMock(spec=Agent)
        mock_agent.execute_task = AsyncMock(side_effect=RuntimeError("Always fails"))

        mock_manager = MagicMock(spec=AgentManager)
        mock_manager.get_agent = MagicMock(return_value=mock_agent)

        step = WorkflowStep("step1", "agent1", "task1", {}, retry_count=2)

        await pipeline._execute_step(step, mock_manager)

        assert step.status == WorkflowStatus.FAILED
        assert step.error is not None

    def test_get_status(self):
        """Test get_status method."""
        pipeline = WorkflowPipeline(name="test_workflow")

        pipeline.add_step("agent1", "task1", {})
        pipeline.add_step("agent2", "task2", {})

        status = pipeline.get_status()

        assert status["pipeline_id"] == pipeline.pipeline_id
        assert status["name"] == "test_workflow"
        assert status["total_steps"] == 2
        assert len(status["step_details"]) == 2


class TestAgentOrchestrator:
    """Test AgentOrchestrator class."""

    @pytest.fixture
    def mock_agent_manager(self):
        """Create a mock agent manager."""
        manager = MagicMock(spec=AgentManager)
        return manager

    @pytest.fixture
    def orchestrator(self, mock_agent_manager):
        """Create an AgentOrchestrator instance."""
        return AgentOrchestrator(mock_agent_manager)

    def test_init(self, mock_agent_manager):
        """Test AgentOrchestrator initialization."""
        orchestrator = AgentOrchestrator(mock_agent_manager)

        assert orchestrator.agent_manager == mock_agent_manager
        assert len(orchestrator.workflows) == 0
        assert len(orchestrator.active_workflows) == 0

    def test_create_workflow(self, orchestrator):
        """Test create_workflow method."""
        workflow = orchestrator.create_workflow(name="test_workflow", description="Test")

        assert isinstance(workflow, WorkflowPipeline)
        assert workflow.name == "test_workflow"
        assert workflow.description == "Test"
        assert workflow.pipeline_id in orchestrator.workflows

    @pytest.mark.asyncio
    async def test_execute_workflow(self, orchestrator, mock_agent_manager):
        """Test execute_workflow method."""
        # Create workflow
        workflow = orchestrator.create_workflow()

        # Mock agent
        mock_agent = MagicMock(spec=Agent)
        mock_agent.execute_task = AsyncMock(return_value={"result": "success"})
        mock_agent_manager.get_agent = MagicMock(return_value=mock_agent)

        # Add step
        workflow.add_step("agent1", "task1", {})

        # Execute
        result = await orchestrator.execute_workflow(workflow.pipeline_id, {"key": "value"})

        assert result["status"] == "completed"
        assert workflow.pipeline_id not in orchestrator.active_workflows

    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self, orchestrator):
        """Test execute_workflow with non-existent workflow."""
        with pytest.raises(WorkflowNotFoundError):
            await orchestrator.execute_workflow("nonexistent_id")

    @pytest.mark.asyncio
    async def test_delegate_task(self, orchestrator, mock_agent_manager):
        """Test delegate_task method."""
        # Create mock agents
        source_agent = MagicMock(spec=Agent)
        target_agent = MagicMock(spec=Agent)

        task = AgentTask(task_id="task1", task_type="test", parameters={})
        target_agent.task_queue = [task]
        target_agent.add_task = MagicMock(return_value="task1")
        target_agent.execute_task = AsyncMock(return_value={"result": "delegated"})
        source_agent.send_message = AsyncMock()

        mock_agent_manager.get_agent = MagicMock(
            side_effect=lambda agent_id: source_agent if agent_id == "agent1" else target_agent
        )

        result = await orchestrator.delegate_task(
            "agent1", "agent2", "test_task", {"param": "value"}, priority=10
        )

        assert result == {"result": "delegated"}
        target_agent.add_task.assert_called_once()
        source_agent.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_delegate_task_agent_not_found(self, orchestrator, mock_agent_manager):
        """Test delegate_task when target agent not found."""
        mock_agent_manager.get_agent = MagicMock(return_value=None)

        with pytest.raises(AgentNotFoundError):
            await orchestrator.delegate_task("agent1", "agent2", "task", {})

    @pytest.mark.asyncio
    async def test_chain_tasks(self, orchestrator, mock_agent_manager):
        """Test chain_tasks method."""
        # Create mock agents
        agents = {}
        for agent_id in ["agent1", "agent2", "agent3"]:
            agent = MagicMock(spec=Agent)
            agent.execute_task = AsyncMock(return_value={"result": f"from_{agent_id}"})
            agents[agent_id] = agent

        mock_agent_manager.get_agent = MagicMock(side_effect=lambda agent_id: agents[agent_id])

        results = await orchestrator.chain_tasks(
            ["agent1", "agent2", "agent3"], "test_task", {"initial": "param"}
        )

        assert len(results) == 3
        assert all("result" in r for r in results)

    @pytest.mark.asyncio
    async def test_chain_tasks_with_transform(self, orchestrator, mock_agent_manager):
        """Test chain_tasks with transform_result function."""
        agents = {}
        for agent_id in ["agent1", "agent2"]:
            agent = MagicMock(spec=Agent)
            agent.execute_task = AsyncMock(return_value={"value": agent_id})
            agents[agent_id] = agent

        mock_agent_manager.get_agent = MagicMock(side_effect=lambda agent_id: agents[agent_id])

        def transform(result, index):
            return {"transformed": result["value"], "index": index}

        results = await orchestrator.chain_tasks(
            ["agent1", "agent2"], "test_task", {"initial": "param"}, transform_result=transform
        )

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_chain_tasks_agent_not_found(self, orchestrator, mock_agent_manager):
        """Test chain_tasks when agent not found."""
        mock_agent_manager.get_agent = MagicMock(return_value=None)

        with pytest.raises(AgentNotFoundError):
            await orchestrator.chain_tasks(["agent1"], "task", {})

    @pytest.mark.asyncio
    async def test_coordinate_leader_follower(self, orchestrator, mock_agent_manager):
        """Test coordinate_leader_follower method."""
        # Create leader and followers
        leader = MagicMock(spec=Agent)
        leader.execute_task = AsyncMock(return_value={"leader_result": "data"})

        followers = []
        for follower_id in ["follower1", "follower2"]:
            follower = MagicMock(spec=Agent)
            follower.execute_task = AsyncMock(return_value={"follower_result": follower_id})
            followers.append((follower_id, follower))

        def get_agent(agent_id):
            if agent_id == "leader1":
                return leader
            for fid, fagent in followers:
                if agent_id == fid:
                    return fagent
            return None

        mock_agent_manager.get_agent = MagicMock(side_effect=get_agent)

        result = await orchestrator.coordinate_leader_follower(
            leader_id="leader1",
            follower_ids=["follower1", "follower2"],
            leader_task={"task_type": "lead", "parameters": {}},
            follower_task_template={"task_type": "follow", "parameters": {}},
        )

        assert "leader_result" in result
        assert "follower_results" in result
        assert len(result["follower_results"]) == 2

    @pytest.mark.asyncio
    async def test_coordinate_leader_follower_with_aggregation(self, orchestrator, mock_agent_manager):
        """Test coordinate_leader_follower with aggregation function."""
        leader = MagicMock(spec=Agent)
        leader.execute_task = AsyncMock(return_value={"result": "leader"})

        follower = MagicMock(spec=Agent)
        follower.execute_task = AsyncMock(return_value={"result": "follower"})

        mock_agent_manager.get_agent = MagicMock(
            side_effect=lambda agent_id: leader if agent_id == "leader1" else follower
        )

        def aggregate(results):
            return {"aggregated": sum(1 for r in results if "result" in r)}

        result = await orchestrator.coordinate_leader_follower(
            leader_id="leader1",
            follower_ids=["follower1"],
            leader_task={"task_type": "lead", "parameters": {}},
            follower_task_template={"task_type": "follow", "parameters": {}},
            aggregation_func=aggregate,
        )

        assert "aggregated" in result

    @pytest.mark.asyncio
    async def test_coordinate_leader_follower_leader_not_found(self, orchestrator, mock_agent_manager):
        """Test coordinate_leader_follower when leader not found."""
        mock_agent_manager.get_agent = MagicMock(return_value=None)

        with pytest.raises(AgentNotFoundError):
            await orchestrator.coordinate_leader_follower(
                leader_id="leader1",
                follower_ids=[],
                leader_task={"task_type": "lead", "parameters": {}},
                follower_task_template={"task_type": "follow", "parameters": {}},
            )

    @pytest.mark.asyncio
    async def test_coordinate_peer_to_peer(self, orchestrator, mock_agent_manager):
        """Test coordinate_peer_to_peer method."""
        agents = {}
        for agent_id in ["agent1", "agent2", "agent3"]:
            agent = MagicMock(spec=Agent)
            agent.execute_task = AsyncMock(return_value={"result": agent_id})
            agents[agent_id] = agent

        mock_agent_manager.get_agent = MagicMock(side_effect=lambda agent_id: agents.get(agent_id))

        result = await orchestrator.coordinate_peer_to_peer(
            agent_ids=["agent1", "agent2", "agent3"],
            task_template={"task_type": "peer_task", "parameters": {}},
        )

        assert "agent_results" in result
        assert "coordinated" in result
        assert len(result["agent_results"]) == 3

    @pytest.mark.asyncio
    async def test_coordinate_peer_to_peer_with_coordination_func(self, orchestrator, mock_agent_manager):
        """Test coordinate_peer_to_peer with coordination function."""
        agent = MagicMock(spec=Agent)
        agent.execute_task = AsyncMock(return_value={"result": "peer"})

        mock_agent_manager.get_agent = MagicMock(return_value=agent)

        def coordinate(results):
            return {"coordinated_result": len(results)}

        result = await orchestrator.coordinate_peer_to_peer(
            agent_ids=["agent1", "agent2"],
            task_template={"task_type": "task", "parameters": {}},
            coordination_func=coordinate,
        )

        assert "coordinated" in result
        assert result["coordinated"]["coordinated_result"] == 2

    def test_get_workflow(self, orchestrator):
        """Test get_workflow method."""
        workflow = orchestrator.create_workflow()

        retrieved = orchestrator.get_workflow(workflow.pipeline_id)

        assert retrieved == workflow
        assert orchestrator.get_workflow("nonexistent") is None

    def test_list_workflows(self, orchestrator):
        """Test list_workflows method."""
        workflow1 = orchestrator.create_workflow()
        workflow2 = orchestrator.create_workflow()

        workflow_ids = orchestrator.list_workflows()

        assert len(workflow_ids) == 2
        assert workflow1.pipeline_id in workflow_ids
        assert workflow2.pipeline_id in workflow_ids

    def test_get_orchestration_status(self, orchestrator):
        """Test get_orchestration_status method."""
        workflow = orchestrator.create_workflow()

        status = orchestrator.get_orchestration_status()

        assert status["total_workflows"] == 1
        assert status["active_workflows"] == 0
        assert workflow.pipeline_id in status["workflow_ids"]

