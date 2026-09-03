export type AgentName = 'Planner' | 'Researcher' | 'Synthesizer' | 'System' | 'Tool';

export type EventType =
  | 'AGENT_THOUGHT'
  | 'STATE_TRANSITION'
  | 'TOOL_INVOCATION'
  | 'TOOL_RESULT'
  | 'COMPLETE'
  | 'ERROR'
  | 'INITIAL_STATE';

export interface PlanStep {
  step_number: number;
  title: string;
  description: string;
  tool_name?: string | null;
  tool_args?: Record<string, any> | null;
}

export interface AgentEvent {
  id?: string;
  task_id?: string;
  task_run_id?: string;
  agent: AgentName | string;
  agent_name?: string;
  event_type: EventType;
  payload: Record<string, any>;
  timestamp: string;
}

export interface TaskRun {
  id: string;
  prompt: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  final_result?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}
