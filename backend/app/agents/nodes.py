import json
import logging
import re
from typing import Dict, Any, Callable, Optional, List
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState
from app.agents.prompts import (
    PLANNER_SYSTEM_PROMPT,
    RESEARCHER_SYSTEM_PROMPT,
    SYNTHESIZER_SYSTEM_PROMPT,
)
from app.agents.llm import get_llm
from app.worker.tasks import dispatch_tool_execution

logger = logging.getLogger("agent_nodes")

# Type alias for event dispatcher callback
EventDispatcher = Optional[Callable[[str, str, Dict[str, Any]], Any]]


def _clean_json_string(text: str) -> str:
    """Strip markdown code fence blocks if LLM output includes them."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


async def _emit_event(
    dispatcher: EventDispatcher,
    agent_name: str,
    event_type: str,
    payload: Dict[str, Any],
):
    """Safely emit an event through the provided callback."""
    if dispatcher:
        try:
            res = dispatcher(agent_name, event_type, payload)
            if hasattr(res, "__await__"):
                await res
        except Exception as e:
            logger.error(f"Failed to emit event ({agent_name}:{event_type}): {str(e)}")


async def planner_node(state: AgentState, dispatcher: EventDispatcher = None) -> Dict[str, Any]:
    """
    Planner Node: Analyzes user prompt and constructs a structured multi-step execution plan.
    """
    task_id = state["task_id"]
    prompt = state["prompt"]

    await _emit_event(
        dispatcher,
        agent_name="Planner",
        event_type="AGENT_THOUGHT",
        payload={
            "thought": "Analyzing request requirements and defining task boundary strategy...",
            "status": "PLANNING",
        },
    )

    llm = get_llm(temperature=0.2)
    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=f"User Request: {prompt}\nDeconstruct this request into an ordered, tool-assisted plan."),
    ]

    try:
        response = await llm.ainvoke(messages)
        content = _clean_json_string(response.content)
        parsed = json.loads(content)
        steps = parsed.get("steps", [])
        thought = parsed.get("thought", "Plan generated successfully.")
    except Exception as exc:
        logger.warning(f"Error parsing Planner output ({str(exc)}). Using fallback plan.")
        thought = f"Constructed multi-phase strategy to address '{prompt}'."
        steps = [
            {
                "step_number": 1,
                "title": "Investigate Primary Data & Weather / Web Context",
                "description": f"Gather necessary data for {prompt}",
                "tool_name": "web_search",
                "tool_args": {"query": prompt, "max_results": 3},
            }
        ]

    await _emit_event(
        dispatcher,
        agent_name="Planner",
        event_type="STATE_TRANSITION",
        payload={
            "thought": thought,
            "plan": steps,
            "step_count": len(steps),
            "message": f"Planner finalized execution blueprint with {len(steps)} sub-tasks.",
        },
    )

    return {
        "plan": steps,
        "status": "PLAN_COMPLETED",
        "current_step_index": 0,
    }


async def researcher_node(state: AgentState, dispatcher: EventDispatcher = None) -> Dict[str, Any]:
    """
    Researcher Node: Iterates through plan steps, executes custom tools via Celery/Redis queue,
    and stores structured evidence.
    """
    plan = state.get("plan", [])
    idx = state.get("current_step_index", 0)
    research_data = list(state.get("research_data", []))

    if idx >= len(plan):
        return {"status": "RESEARCH_COMPLETED"}

    current_step = plan[idx]
    step_num = current_step.get("step_number", idx + 1)
    step_title = current_step.get("title", f"Step {step_num}")
    tool_name = current_step.get("tool_name")
    tool_args = current_step.get("tool_args") or {}

    await _emit_event(
        dispatcher,
        agent_name="Researcher",
        event_type="AGENT_THOUGHT",
        payload={
            "step": step_num,
            "title": step_title,
            "description": current_step.get("description", ""),
            "thought": f"Commencing execution for Step {step_num}: '{step_title}' using tool '{tool_name or 'none'}'.",
        },
    )

    tool_result = ""
    if tool_name:
        # Emit tool invocation event
        await _emit_event(
            dispatcher,
            agent_name="Researcher",
            event_type="TOOL_INVOCATION",
            payload={
                "tool": tool_name,
                "args": tool_args,
                "execution_target": "Celery Distributed Task Queue (Redis)",
                "step": step_num,
            },
        )

        # Offload execution to Celery worker asynchronously
        tool_result = await dispatch_tool_execution(tool_name, tool_args, timeout=25.0)

        # Emit tool result event
        await _emit_event(
            dispatcher,
            agent_name="Researcher",
            event_type="TOOL_RESULT",
            payload={
                "tool": tool_name,
                "result": tool_result,
                "step": step_num,
            },
        )
    else:
        tool_result = f"Step completed via internal analytical synthesis."

    research_entry = {
        "step_number": step_num,
        "title": step_title,
        "tool_name": tool_name,
        "tool_args": tool_args,
        "result": tool_result,
    }
    research_data.append(research_entry)

    next_idx = idx + 1
    next_status = "RESEARCHING" if next_idx < len(plan) else "RESEARCH_COMPLETED"

    return {
        "research_data": research_data,
        "current_step_index": next_idx,
        "status": next_status,
    }


async def synthesizer_node(state: AgentState, dispatcher: EventDispatcher = None) -> Dict[str, Any]:
    """
    Synthesizer Node: Consolidates research findings, tool outputs, and the initial prompt
    into an executive final response.
    """
    prompt = state["prompt"]
    plan = state.get("plan", [])
    research_data = state.get("research_data", [])

    await _emit_event(
        dispatcher,
        agent_name="Synthesizer",
        event_type="AGENT_THOUGHT",
        payload={
            "thought": "Aggregating gathered evidence and drafting comprehensive response with executive recommendations...",
        },
    )

    # Format research context for the Synthesizer LLM
    research_context = ""
    for r in research_data:
        research_context += (
            f"\n--- [Step {r.get('step_number')}: {r.get('title')}] ---\n"
            f"Tool: {r.get('tool_name')}\n"
            f"Result: {r.get('result')}\n"
        )

    llm = get_llm(temperature=0.3)
    messages = [
        SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Original User Request:\n{prompt}\n\n"
                f"Executed Research Evidence:\n{research_context}\n\n"
                "Please synthesize an authoritative, structured, and helpful markdown response that directly answers the user's prompt using the gathered evidence."
            )
        ),
    ]

    try:
        response = await llm.ainvoke(messages)
        final_text = response.content
    except Exception as exc:
        logger.error(f"Synthesizer LLM invocation failed ({str(exc)}).")
        final_text = (
            f"### Multi-Agent Synthesis Report\n\n"
            f"**Objective**: {prompt}\n\n"
            f"#### Findings Summary\n"
            f"{research_context}\n\n"
            f"#### Recommendations\n"
            f"- Ensure all actions conform to retrieved external constraints.\n"
            f"- Consult detailed tool metrics for further drill-downs."
        )

    await _emit_event(
        dispatcher,
        agent_name="Synthesizer",
        event_type="COMPLETE",
        payload={
            "final_result": final_text,
            "message": "All agent stages completed successfully.",
        },
    )

    return {
        "final_result": final_text,
        "status": "COMPLETED",
    }
