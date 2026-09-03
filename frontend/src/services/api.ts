import { TaskRun, AgentEvent } from '../types';

const API_BASE = '/api';

export async function createTask(prompt: string): Promise<{ task_id: string; status: string; prompt: string }> {
  const response = await fetch(`${API_BASE}/tasks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to create task' }));
    throw new Error(err.detail || `HTTP Error ${response.status}`);
  }

  return response.json();
}

export async function listTasks(): Promise<TaskRun[]> {
  const response = await fetch(`${API_BASE}/tasks`);
  if (!response.ok) {
    throw new Error(`Failed to list tasks: ${response.statusText}`);
  }
  return response.json();
}

export async function getTask(taskId: string): Promise<TaskRun> {
  const response = await fetch(`${API_BASE}/tasks/${taskId}`);
  if (!response.ok) {
    throw new Error(`Failed to get task ${taskId}`);
  }
  return response.json();
}

export async function getTaskEvents(taskId: string): Promise<AgentEvent[]> {
  const response = await fetch(`${API_BASE}/tasks/${taskId}/events`);
  if (!response.ok) {
    throw new Error(`Failed to fetch events for task ${taskId}`);
  }
  return response.json();
}

export async function checkHealth(): Promise<{ status: string; has_groq_key: boolean; has_openai_key: boolean }> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  return response.json();
}
