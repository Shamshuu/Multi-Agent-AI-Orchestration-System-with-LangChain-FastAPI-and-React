from typing import TypedDict, List, Dict, Any, Optional


class PlanStep(TypedDict):
    step_number: int
    title: str
    description: str
    tool_name: Optional[str]  # 'web_search', 'weather_search', 'calculator', or None
    tool_args: Optional[Dict[str, Any]]
    status: str  # 'pending', 'in_progress', 'completed', 'failed'


class AgentState(TypedDict):
    task_id: str
    prompt: str
    plan: List[Dict[str, Any]]
    current_step_index: int
    research_data: List[Dict[str, Any]]
    messages: List[Dict[str, str]]
    final_result: Optional[str]
    status: str
    error: Optional[str]
