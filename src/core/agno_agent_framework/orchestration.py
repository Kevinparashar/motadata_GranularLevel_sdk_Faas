"""
Multi-Agent Orchestration System

Provides workflow pipelines, coordination patterns, task delegation, and chaining
for complex multi-agent workflows.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set
from datetime import datetime

from .agent import Agent, AgentTask, AgentStatus

if TYPE_CHECKING:
    from .agent import AgentManager


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class CoordinationPattern(str, Enum):
    """Coordination pattern types."""
    LEADER_FOLLOWER = "leader_follower"
    PEER_TO_PEER = "peer_to_peer"
    HIERARCHICAL = "hierarchical"
    PIPELINE = "pipeline"
    BROADCAST = "broadcast"


class WorkflowStep:
    """A single step in a workflow pipeline."""
    
    def __init__(
        self,
        step_id: str,
        agent_id: str,
        task_type: str,
        parameters: Dict[str, Any],
        depends_on: Optional[List[str]] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        retry_count: int = 0,
        timeout: Optional[float] = None
    ):
        self.step_id = step_id
        self.agent_id = agent_id
        self.task_type = task_type
        self.parameters = parameters
        self.depends_on = depends_on or []
        self.condition = condition
        self.retry_count = retry_count
        self.timeout = timeout
        self.status = WorkflowStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None


@dataclass
class WorkflowState:
    """State of a workflow execution."""
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[str] = None
    completed_steps: Set[str] = field(default_factory=set)
    failed_steps: Set[str] = field(default_factory=set)
    step_results: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class WorkflowPipeline:
    """
    Workflow pipeline for orchestrating multi-step agent tasks.
    
    Supports sequential, parallel, and conditional execution patterns.
    """
    
    def __init__(
        self,
        pipeline_id: Optional[str] = None,
        name: str = "workflow",
        description: str = ""
    ):
        self.pipeline_id = pipeline_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        self.state = WorkflowState(workflow_id=self.pipeline_id)
    
    def add_step(
        self,
        agent_id: str,
        task_type: str,
        parameters: Dict[str, Any],
        step_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None,
        retry_count: int = 0,
        timeout: Optional[float] = None
    ) -> str:
        """
        Add a step to the workflow.
        
        Args:
            agent_id: Agent to execute the step
            task_type: Type of task
            parameters: Task parameters
            step_id: Optional step ID (auto-generated if not provided)
            depends_on: List of step IDs this step depends on
            condition: Optional condition function to check before execution
            retry_count: Number of retries on failure
            timeout: Optional timeout in seconds
        
        Returns:
            Step ID
        """
        step_id = step_id or f"step_{len(self.steps) + 1}"
        step = WorkflowStep(
            step_id=step_id,
            agent_id=agent_id,
            task_type=task_type,
            parameters=parameters,
            depends_on=depends_on or [],
            condition=condition,
            retry_count=retry_count,
            timeout=timeout
        )
        self.steps.append(step)
        return step_id
    
    def _get_ready_steps(self) -> List[WorkflowStep]:
        """Get steps that are ready to execute (dependencies satisfied)."""
        ready = []
        for step in self.steps:
            if step.status != WorkflowStatus.PENDING:
                continue
            # Check if all dependencies are completed
            if all(
                dep_id in self.state.completed_steps
                for dep_id in step.depends_on
            ):
                # Check condition if present
                if step.condition:
                    if not step.condition(self.state.context):
                        continue
                ready.append(step)
        return ready
    
    async def execute(
        self,
        agent_manager: "AgentManager",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the workflow pipeline.
        
        Args:
            agent_manager: AgentManager instance
            context: Optional initial context
        
        Returns:
            Final workflow result
        """
        self.state.status = WorkflowStatus.RUNNING
        self.state.started_at = datetime.now()
        self.state.context.update(context or {})
        
        try:
            while True:
                ready_steps = self._get_ready_steps()
                if not ready_steps:
                    # Check if all steps are done
                    if all(
                        step.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
                        for step in self.steps
                    ):
                        break
                    # Wait a bit for dependencies
                    await asyncio.sleep(0.1)
                    continue
                
                # Execute ready steps (can be parallel)
                tasks = [
                    self._execute_step(step, agent_manager)
                    for step in ready_steps
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if workflow succeeded
            if self.state.failed_steps:
                self.state.status = WorkflowStatus.FAILED
                self.state.error = f"Failed steps: {', '.join(self.state.failed_steps)}"
            else:
                self.state.status = WorkflowStatus.COMPLETED
                self.state.completed_at = datetime.now()
        
        except Exception as e:
            self.state.status = WorkflowStatus.FAILED
            self.state.error = str(e)
            self.state.completed_at = datetime.now()
        
        return {
            "workflow_id": self.pipeline_id,
            "status": self.state.status.value,
            "results": self.state.step_results,
            "context": self.state.context,
            "error": self.state.error
        }
    
    async def _execute_step(
        self,
        step: WorkflowStep,
        agent_manager: "AgentManager"
    ) -> None:
        """Execute a single workflow step."""
        agent = agent_manager.get_agent(step.agent_id)
        if not agent:
            step.status = WorkflowStatus.FAILED
            step.error = f"Agent {step.agent_id} not found"
            self.state.failed_steps.add(step.step_id)
            return
        
        step.status = WorkflowStatus.RUNNING
        step.started_at = datetime.now()
        self.state.current_step = step.step_id
        
        # Merge context into parameters
        params = {**step.parameters, **self.state.context}
        
        attempt = 0
        while attempt <= step.retry_count:
            try:
                # Create task
                task = AgentTask(
                    task_id=f"{step.step_id}_{attempt}",
                    task_type=step.task_type,
                    parameters=params,
                    priority=10
                )
                
                # Execute with timeout if specified
                if step.timeout:
                    result = await asyncio.wait_for(
                        agent.execute_task(task),
                        timeout=step.timeout
                    )
                else:
                    result = await agent.execute_task(task)
                
                step.status = WorkflowStatus.COMPLETED
                step.result = result
                step.completed_at = datetime.now()
                self.state.completed_steps.add(step.step_id)
                self.state.step_results[step.step_id] = result
                
                # Update context with result
                if isinstance(result, dict):
                    self.state.context.update(result)
                
                return
            
            except Exception as e:
                attempt += 1
                if attempt > step.retry_count:
                    step.status = WorkflowStatus.FAILED
                    step.error = str(e)
                    step.completed_at = datetime.now()
                    self.state.failed_steps.add(step.step_id)
                    return
                await asyncio.sleep(0.1 * attempt)  # Exponential backoff
    
    def get_status(self) -> Dict[str, Any]:
        """Get workflow status."""
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "status": self.state.status.value,
            "current_step": self.state.current_step,
            "total_steps": len(self.steps),
            "completed_steps": len(self.state.completed_steps),
            "failed_steps": len(self.state.failed_steps),
            "step_details": [
                {
                    "step_id": step.step_id,
                    "status": step.status.value,
                    "agent_id": step.agent_id,
                    "error": step.error
                }
                for step in self.steps
            ]
        }


class AgentOrchestrator:
    """
    Advanced orchestrator for multi-agent coordination.
    
    Supports multiple coordination patterns and workflow management.
    """
    
    def __init__(self, agent_manager: "AgentManager"):
        self.agent_manager = agent_manager
        self.workflows: Dict[str, WorkflowPipeline] = {}
        self.active_workflows: Set[str] = set()
    
    def create_workflow(
        self,
        name: str = "workflow",
        description: str = ""
    ) -> WorkflowPipeline:
        """
        Create a new workflow pipeline.
        
        Args:
            name: Workflow name
            description: Workflow description
        
        Returns:
            WorkflowPipeline instance
        """
        pipeline = WorkflowPipeline(name=name, description=description)
        self.workflows[pipeline.pipeline_id] = pipeline
        return pipeline
    
    async def execute_workflow(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow_id: Workflow ID
            context: Optional initial context
        
        Returns:
            Workflow result
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found")
        
        self.active_workflows.add(workflow_id)
        try:
            result = await workflow.execute(self.agent_manager, context)
            return result
        finally:
            self.active_workflows.discard(workflow_id)
    
    async def delegate_task(
        self,
        from_agent_id: str,
        to_agent_id: str,
        task_type: str,
        parameters: Dict[str, Any],
        priority: int = 5
    ) -> Any:
        """
        Delegate a task from one agent to another.
        
        Args:
            from_agent_id: Source agent ID
            to_agent_id: Target agent ID
            task_type: Type of task
            parameters: Task parameters
            priority: Task priority
        
        Returns:
            Task result
        """
        target_agent = self.agent_manager.get_agent(to_agent_id)
        if not target_agent:
            raise ValueError(f"Agent '{to_agent_id}' not found")
        
        task_id = target_agent.add_task(task_type, parameters, priority)
        task = next(t for t in target_agent.task_queue if t.task_id == task_id)
        
        # Notify source agent
        source_agent = self.agent_manager.get_agent(from_agent_id)
        if source_agent:
            source_agent.send_message(
                to_agent_id,
                {"action": "task_delegated", "task_id": task_id},
                "delegation"
            )
        
        return await target_agent.execute_task(task)
    
    async def chain_tasks(
        self,
        agent_chain: List[str],
        task_type: str,
        initial_parameters: Dict[str, Any],
        transform_result: Optional[Callable[[Any, int], Dict[str, Any]]] = None
    ) -> List[Any]:
        """
        Chain tasks across multiple agents sequentially.
        
        Args:
            agent_chain: List of agent IDs in execution order
            task_type: Type of task
            initial_parameters: Initial task parameters
            transform_result: Optional function to transform result for next agent
        
        Returns:
            List of results from each agent
        """
        results = []
        current_params = initial_parameters
        
        for i, agent_id in enumerate(agent_chain):
            agent = self.agent_manager.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent '{agent_id}' not found")
            
            task = AgentTask(
                task_id=f"chain_{i}_{agent_id}",
                task_type=task_type,
                parameters=current_params,
                priority=10
            )
            
            result = await agent.execute_task(task)
            results.append(result)
            
            # Transform result for next agent
            if transform_result and i < len(agent_chain) - 1:
                current_params = transform_result(result, i)
            elif isinstance(result, dict):
                current_params = result
        
        return results
    
    async def coordinate_leader_follower(
        self,
        leader_id: str,
        follower_ids: List[str],
        leader_task: Dict[str, Any],
        follower_task_template: Dict[str, Any],
        aggregation_func: Optional[Callable[[List[Any]], Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate agents using leader-follower pattern.
        
        Leader executes first, then followers execute in parallel,
        results are aggregated.
        
        Args:
            leader_id: Leader agent ID
            follower_ids: List of follower agent IDs
            leader_task: Leader task definition
            follower_task_template: Template for follower tasks
            aggregation_func: Optional function to aggregate follower results
        
        Returns:
            Coordination result
        """
        leader = self.agent_manager.get_agent(leader_id)
        if not leader:
            raise ValueError(f"Agent '{leader_id}' not found")
        
        # Execute leader task
        leader_task_obj = AgentTask(
            task_id=f"leader_{leader_id}",
            task_type=leader_task["task_type"],
            parameters=leader_task["parameters"],
            priority=10
        )
        leader_result = await leader.execute_task(leader_task_obj)
        
        # Prepare follower tasks with leader result
        follower_params = {
            **follower_task_template["parameters"],
            "leader_result": leader_result
        }
        
        # Execute followers in parallel
        follower_tasks = []
        for follower_id in follower_ids:
            follower = self.agent_manager.get_agent(follower_id)
            if not follower:
                continue
            task = AgentTask(
                task_id=f"follower_{follower_id}",
                task_type=follower_task_template["task_type"],
                parameters=follower_params,
                priority=5
            )
            follower_tasks.append(follower.execute_task(task))
        
        follower_results = await asyncio.gather(*follower_tasks, return_exceptions=True)
        
        # Aggregate results
        if aggregation_func:
            aggregated = aggregation_func(follower_results)
        else:
            aggregated = follower_results
        
        return {
            "leader_result": leader_result,
            "follower_results": follower_results,
            "aggregated": aggregated
        }
    
    async def coordinate_peer_to_peer(
        self,
        agent_ids: List[str],
        task_template: Dict[str, Any],
        coordination_func: Optional[Callable[[List[Any]], Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate agents using peer-to-peer pattern.
        
        All agents execute in parallel, results are coordinated.
        
        Args:
            agent_ids: List of agent IDs
            task_template: Task template for all agents
            coordination_func: Optional function to coordinate results
        
        Returns:
            Coordination result
        """
        tasks = []
        for agent_id in agent_ids:
            agent = self.agent_manager.get_agent(agent_id)
            if not agent:
                continue
            task = AgentTask(
                task_id=f"peer_{agent_id}",
                task_type=task_template["task_type"],
                parameters=task_template["parameters"],
                priority=5
            )
            tasks.append(agent.execute_task(task))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        if coordination_func:
            coordinated = coordination_func(results)
        else:
            coordinated = results
        
        return {
            "agent_results": dict(zip(agent_ids, results)),
            "coordinated": coordinated
        }
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowPipeline]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[str]:
        """List all workflow IDs."""
        return list(self.workflows.keys())
    
    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "total_workflows": len(self.workflows),
            "active_workflows": len(self.active_workflows),
            "workflow_ids": list(self.workflows.keys()),
            "active_workflow_ids": list(self.active_workflows)
        }

