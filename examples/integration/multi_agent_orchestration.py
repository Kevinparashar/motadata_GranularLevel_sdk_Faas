"""
Multi-Agent Orchestration Example

Demonstrates workflow pipelines, coordination patterns, task delegation,
and chaining for complex multi-agent workflows.
"""

import asyncio

from src.core.agno_agent_framework import Agent, AgentManager, AgentOrchestrator

# Constants for error messages
DEMO_NOTE_API = "Note: These examples demonstrate the orchestration API."
DEMO_NOTE_IMPL = "Full implementation requires actual agent task handlers.\n"


async def example_workflow_pipeline():
    """Example: Sequential workflow pipeline."""
    print("=== Workflow Pipeline Example ===\n")

    # Create agents
    manager = AgentManager()

    agent1 = Agent(agent_id="researcher", name="Research Agent", description="Researches topics")
    agent1.add_capability("research", "Can research topics")

    agent2 = Agent(agent_id="writer", name="Writer Agent", description="Writes content")
    agent2.add_capability("writing", "Can write content")

    agent3 = Agent(agent_id="reviewer", name="Review Agent", description="Reviews content")
    agent3.add_capability("review", "Can review content")

    manager.register_agent(agent1)
    manager.register_agent(agent2)
    manager.register_agent(agent3)

    # Create orchestrator
    orchestrator = AgentOrchestrator(manager)
    manager.attach_orchestrator(orchestrator)

    # Create workflow
    workflow = orchestrator.create_workflow(
        name="Content Creation Pipeline", description="Research -> Write -> Review"
    )

    # Add steps with dependencies
    workflow.add_step(
        agent_id="researcher",
        task_type="research",
        parameters={"topic": "AI Agents", "depth": "detailed"},
        step_id="step1_research",
    )

    workflow.add_step(
        agent_id="writer",
        task_type="write",
        parameters={"style": "technical"},
        step_id="step2_write",
        depends_on=["step1_research"],
    )

    workflow.add_step(
        agent_id="reviewer",
        task_type="review",
        parameters={"criteria": "accuracy, clarity"},
        step_id="step3_review",
        depends_on=["step2_write"],
    )

    # Execute workflow
    result = await orchestrator.execute_workflow(workflow.pipeline_id)
    print(f"Workflow Status: {result['status']}")
    print(f"Results: {result['results']}\n")


async def example_task_delegation():
    """Example: Task delegation between agents."""
    print("=== Task Delegation Example ===\n")

    manager = AgentManager()

    coordinator = Agent(
        agent_id="coordinator", name="Coordinator Agent", description="Coordinates tasks"
    )

    worker = Agent(agent_id="worker", name="Worker Agent", description="Executes delegated tasks")

    manager.register_agent(coordinator)
    manager.register_agent(worker)

    orchestrator = AgentOrchestrator(manager)

    # Delegate task
    result = await orchestrator.delegate_task(
        from_agent_id="coordinator",
        to_agent_id="worker",
        task_type="process_data",
        parameters={"data": "sample data", "operation": "analyze"},
        priority=8,
    )

    print(f"Delegated task result: {result}\n")


async def example_task_chaining():
    """Example: Chaining tasks across multiple agents."""
    print("=== Task Chaining Example ===\n")

    manager = AgentManager()

    # Create chain of agents
    agent1 = Agent(agent_id="processor1", name="Processor 1")
    agent2 = Agent(agent_id="processor2", name="Processor 2")
    agent3 = Agent(agent_id="processor3", name="Processor 3")

    manager.register_agent(agent1)
    manager.register_agent(agent2)
    manager.register_agent(agent3)

    orchestrator = AgentOrchestrator(manager)

    # Chain tasks
    def transform_result(result: dict, step_index: int) -> dict:
        """Transform result for next step."""
        return {"input": result.get("result", ""), "step": step_index + 1}

    results = await orchestrator.chain_tasks(
        agent_chain=["processor1", "processor2", "processor3"],
        task_type="process",
        initial_parameters={"data": "initial data"},
        transform_result=transform_result,
    )

    print(f"Chain results: {results}\n")


async def example_leader_follower():
    """Example: Leader-follower coordination pattern."""
    print("=== Leader-Follower Pattern Example ===\n")

    manager = AgentManager()

    leader = Agent(agent_id="leader", name="Leader Agent", description="Leads the coordination")

    follower1 = Agent(agent_id="follower1", name="Follower 1")
    follower2 = Agent(agent_id="follower2", name="Follower 2")
    follower3 = Agent(agent_id="follower3", name="Follower 3")

    manager.register_agent(leader)
    manager.register_agent(follower1)
    manager.register_agent(follower2)
    manager.register_agent(follower3)

    orchestrator = AgentOrchestrator(manager)

    # Coordinate using leader-follower pattern
    result = await orchestrator.coordinate_leader_follower(
        leader_id="leader",
        follower_ids=["follower1", "follower2", "follower3"],
        leader_task={"task_type": "plan", "parameters": {"objective": "Complete project"}},
        follower_task_template={"task_type": "execute", "parameters": {"task": "assigned_task"}},
        aggregation_func=lambda results: {
            "total": len(results),
            "successful": sum(1 for r in results if not isinstance(r, Exception)),
        },
    )

    print(f"Leader-Follower Result: {result}\n")


async def example_peer_to_peer():
    """Example: Peer-to-peer coordination pattern."""
    print("=== Peer-to-Peer Pattern Example ===\n")

    manager = AgentManager()

    peer1 = Agent(agent_id="peer1", name="Peer 1")
    peer2 = Agent(agent_id="peer2", name="Peer 2")
    peer3 = Agent(agent_id="peer3", name="Peer 3")

    manager.register_agent(peer1)
    manager.register_agent(peer2)
    manager.register_agent(peer3)

    orchestrator = AgentOrchestrator(manager)

    # Coordinate using peer-to-peer pattern
    result = await orchestrator.coordinate_peer_to_peer(
        agent_ids=["peer1", "peer2", "peer3"],
        task_template={"task_type": "collaborate", "parameters": {"shared_goal": "solve problem"}},
        coordination_func=lambda results: {
            "consensus": "achieved" if len({str(r) for r in results}) == 1 else "pending"
        },
    )

    print(f"Peer-to-Peer Result: {result}\n")


async def example_parallel_workflow():
    """Example: Parallel workflow execution."""
    print("=== Parallel Workflow Example ===\n")

    manager = AgentManager()

    agent1 = Agent(agent_id="agent1", name="Agent 1")
    agent2 = Agent(agent_id="agent2", name="Agent 2")
    agent3 = Agent(agent_id="agent3", name="Agent 3")

    manager.register_agent(agent1)
    manager.register_agent(agent2)
    manager.register_agent(agent3)

    orchestrator = AgentOrchestrator(manager)

    # Create workflow with parallel steps
    workflow = orchestrator.create_workflow(name="Parallel Tasks")

    # All steps depend on nothing (run in parallel)
    workflow.add_step(
        agent_id="agent1",
        task_type="task1",
        parameters={"param": "value1"},
        step_id="parallel_step1",
    )

    workflow.add_step(
        agent_id="agent2",
        task_type="task2",
        parameters={"param": "value2"},
        step_id="parallel_step2",
    )

    workflow.add_step(
        agent_id="agent3",
        task_type="task3",
        parameters={"param": "value3"},
        step_id="parallel_step3",
    )

    # Final step depends on all parallel steps
    workflow.add_step(
        agent_id="agent1",
        task_type="aggregate",
        parameters={"operation": "merge"},
        step_id="final_step",
        depends_on=["parallel_step1", "parallel_step2", "parallel_step3"],
    )

    result = await orchestrator.execute_workflow(workflow.pipeline_id)
    print(f"Parallel Workflow Status: {result['status']}")
    print(f"Step Results: {result['results']}\n")


async def main():
    """Run all examples."""
    print("Multi-Agent Orchestration Examples\n")
    print("=" * 50 + "\n")

    try:
        await example_workflow_pipeline()
        await example_task_delegation()
        await example_task_chaining()
        await example_leader_follower()
        await example_peer_to_peer()
        await example_parallel_workflow()
    except (ConnectionError, TimeoutError) as e:
        print(f"Network error (expected in demo): {e}\n")
        print(DEMO_NOTE_API)
        print(DEMO_NOTE_IMPL)
    except ValueError as e:
        print(f"Validation error (expected in demo): {e}\n")
        print(DEMO_NOTE_API)
        print(DEMO_NOTE_IMPL)
    except Exception as e:
        print(f"Example error (expected in demo): {e}\n")
        print(DEMO_NOTE_API)
        print(DEMO_NOTE_IMPL)


if __name__ == "__main__":
    asyncio.run(main())
