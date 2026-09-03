import logging
from typing import Dict, Any, Callable, Optional
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.nodes import (
    planner_node,
    researcher_node,
    synthesizer_node,
    _emit_event,
    EventDispatcher,
)
from app.db.session import AsyncSessionLocal
from app.db.repository import update_task_run, create_agent_event

logger = logging.getLogger("agent_graph")


def build_agent_graph(dispatcher: EventDispatcher = None):
    """
    Construct the LangGraph StateGraph connecting the Planner, Researcher,
    and Synthesizer agents with conditional looping.
    """
    workflow = StateGraph(AgentState)

    # Node wrappers passing the event dispatcher
    async def _planner_step(state: AgentState) -> Dict[str, Any]:
        return await planner_node(state, dispatcher=dispatcher)

    async def _researcher_step(state: AgentState) -> Dict[str, Any]:
        return await researcher_node(state, dispatcher=dispatcher)

    async def _synthesizer_step(state: AgentState) -> Dict[str, Any]:
        return await synthesizer_node(state, dispatcher=dispatcher)

    # Register nodes
    workflow.add_node("planner", _planner_step)
    workflow.add_node("researcher", _researcher_step)
    workflow.add_node("synthesizer", _synthesizer_step)

    # Define edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")

    # Conditional edge: continue researcher loop if more steps remain in plan
    def should_continue_research(state: AgentState) -> str:
        idx = state.get("current_step_index", 0)
        plan = state.get("plan", [])
        if idx < len(plan):
            return "researcher"
        return "synthesizer"

    workflow.add_conditional_edges(
        "researcher",
        should_continue_research,
        {
            "researcher": "researcher",
            "synthesizer": "synthesizer",
        },
    )

    workflow.add_edge("synthesizer", END)

    return workflow.compile()


async def execute_agent_workflow(
    task_id: str,
    prompt: str,
    event_callback: Optional[Callable[[str, str, Dict[str, Any]], Any]] = None,
) -> Dict[str, Any]:
    """
    Execute the entire multi-agent LangGraph workflow for a given task_id.
    Persists all intermediate states to PostgreSQL and forwards real-time events.
    """
    logger.info(f"Starting agent workflow for task {task_id}")

    # Helper to persist events to DB while notifying WebSocket subscribers
    async def dispatcher(agent_name: str, event_type: str, payload: Dict[str, Any]):
        # 1. Persist to PostgreSQL
        try:
            async with AsyncSessionLocal() as session:
                await create_agent_event(
                    session=session,
                    task_run_id=task_id,
                    agent_name=agent_name,
                    event_type=event_type,
                    payload=payload,
                )
        except Exception as e:
            logger.error(f"Error persisting AgentEvent to DB: {str(e)}")

        # 2. Notify WebSocket listener
        if event_callback:
            try:
                res = event_callback(agent_name, event_type, payload)
                if hasattr(res, "__await__"):
                    await res
            except Exception as e:
                logger.error(f"Error calling event_callback: {str(e)}")

    # Mark task as RUNNING in DB
    try:
        async with AsyncSessionLocal() as session:
            await update_task_run(session, task_id=task_id, status="RUNNING")
    except Exception as e:
        logger.error(f"Error updating task status to RUNNING: {str(e)}")

    # Initial state
    initial_state: AgentState = {
        "task_id": task_id,
        "prompt": prompt,
        "plan": [],
        "current_step_index": 0,
        "research_data": [],
        "messages": [],
        "final_result": None,
        "status": "RUNNING",
        "error": None,
    }

    try:
        graph = build_agent_graph(dispatcher=dispatcher)
        final_state = await graph.ainvoke(initial_state)

        final_result = final_state.get("final_result", "Workflow completed without text output.")

        # Update DB to COMPLETED
        async with AsyncSessionLocal() as session:
            await update_task_run(
                session,
                task_id=task_id,
                status="COMPLETED",
                final_result=final_result,
            )

        # Explicitly broadcast completion with final_result to all listeners
        await dispatcher(
            agent_name="Synthesizer",
            event_type="COMPLETE",
            payload={
                "final_result": final_result,
                "status": "COMPLETED",
                "message": "All agent stages completed successfully.",
            },
        )

        return final_state

    except Exception as exc:
        logger.exception(f"Fatal error during agent workflow execution for {task_id}: {str(exc)}")
        error_msg = f"Workflow Execution Error: {str(exc)}"

        await _emit_event(
            dispatcher,
            agent_name="System",
            event_type="ERROR",
            payload={"error": error_msg},
        )

        async with AsyncSessionLocal() as session:
            await update_task_run(
                session,
                task_id=task_id,
                status="FAILED",
                final_result=error_msg,
            )

        return {**initial_state, "status": "FAILED", "error": error_msg}
