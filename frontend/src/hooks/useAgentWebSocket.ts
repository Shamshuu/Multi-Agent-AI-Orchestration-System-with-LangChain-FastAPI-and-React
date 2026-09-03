import { useState, useEffect, useRef, useCallback } from 'react';
import { AgentEvent, AgentName, PlanStep } from '../types';
import { getTask, getTaskEvents } from '../services/api';

export interface UseAgentWebSocketReturn {
  events: AgentEvent[];
  connectionStatus: 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error';
  finalResult: string | null;
  activeAgent: AgentName | null;
  plan: PlanStep[];
  isCompleted: boolean;
  error: string | null;
  clearEvents: () => void;
  loadHistoricalEvents: (historical: AgentEvent[], finalRes?: string | null) => void;
}

export function useAgentWebSocket(taskId: string | null): UseAgentWebSocketReturn {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'disconnected' | 'error'>('idle');
  const [finalResult, setFinalResult] = useState<string | null>(null);
  const [activeAgent, setActiveAgent] = useState<AgentName | null>(null);
  const [plan, setPlan] = useState<PlanStep[]>([]);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<number | null>(null);
  const pollIntervalRef = useRef<number | null>(null);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setFinalResult(null);
    setActiveAgent(null);
    setPlan([]);
    setIsCompleted(false);
    setError(null);
  }, []);

  const loadHistoricalEvents = useCallback((historical: AgentEvent[], finalRes?: string | null) => {
    setEvents(historical);
    if (finalRes) {
      setFinalResult(finalRes);
      setIsCompleted(true);
      setActiveAgent(null);
    }
    // Extract plan if available
    for (const ev of historical) {
      if (ev.payload?.plan && Array.isArray(ev.payload.plan)) {
        setPlan(ev.payload.plan);
      }
      const res = ev.payload?.final_result || ev.payload?.finalResult || ev.payload?.result;
      if (ev.event_type === 'COMPLETE' && res) {
        setFinalResult(res);
        setIsCompleted(true);
        setActiveAgent(null);
      }
    }
  }, []);

  useEffect(() => {
    if (!taskId) {
      setConnectionStatus('idle');
      return;
    }

    clearEvents();
    setConnectionStatus('connecting');

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/ws/${taskId}`;

    console.log(`[WebSocket] Connecting to ${wsUrl}`);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`[WebSocket] Connected for task: ${taskId}`);
      setConnectionStatus('connected');
      setError(null);

      // Periodic client ping
      pingIntervalRef.current = window.setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 10000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Ignore heartbeat/pong frames
        if (data.type === 'heartbeat' || data.type === 'pong') {
          return;
        }

        const agentName = (data.agent || data.agent_name || 'System') as AgentName;
        const eventType = data.event_type;
        let payload = data.payload || {};

        if (typeof payload === 'string') {
          try {
            payload = JSON.parse(payload);
          } catch {
            // Keep as string if plain text
          }
        }

        const possibleResult =
          payload.final_result ||
          payload.finalResult ||
          payload.result ||
          data.final_result ||
          data.result;

        if (data.event_type === 'INITIAL_STATE') {
          if ((payload.status === 'COMPLETED' || possibleResult) && possibleResult) {
            setFinalResult(possibleResult);
            setIsCompleted(true);
            setActiveAgent(null);
          }
          return;
        }

        const newEvent: AgentEvent = {
          id: data.id || `${Date.now()}-${Math.random()}`,
          agent: agentName,
          event_type: eventType,
          payload,
          timestamp: data.timestamp || new Date().toISOString(),
        };

        setEvents((prev) => {
          const exists = prev.some((e) => e.id === newEvent.id && e.timestamp === newEvent.timestamp);
          if (exists) return prev;
          return [...prev, newEvent];
        });

        // Update active agent badge
        if (agentName && agentName !== 'System') {
          setActiveAgent(agentName);
        }

        // Update plan state if formulated
        if (payload.plan && Array.isArray(payload.plan)) {
          setPlan(payload.plan);
        }

        // Handle completion
        if (eventType === 'COMPLETE' || payload.status === 'COMPLETED') {
          setIsCompleted(true);
          setActiveAgent(null);
          if (possibleResult) {
            setFinalResult(possibleResult);
          }
        }

        // Handle error
        if (eventType === 'ERROR') {
          setError(payload.error || 'An error occurred during execution');
          setActiveAgent(null);
        }
      } catch (err) {
        console.error('[WebSocket] Failed to parse message:', err);
      }
    };

    ws.onerror = (e) => {
      console.error('[WebSocket] Error:', e);
      setConnectionStatus('error');
      setError('WebSocket connection encountered an error.');
    };

    ws.onclose = (e) => {
      console.log(`[WebSocket] Closed: code=${e.code} reason=${e.reason}`);
      setConnectionStatus('disconnected');
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
    };

    // ACTIVE POLLING BACKUP:
    // Every 1.5 seconds, poll the task status to ensure the final deliverable
    // automatically displays even if WebSocket disconnected or completed ahead of time!
    pollIntervalRef.current = window.setInterval(async () => {
      try {
        const taskInfo = await getTask(taskId);
        if (taskInfo && taskInfo.status === 'COMPLETED' && taskInfo.final_result) {
          console.log('[Task Poller] Task completed! Automatically setting result.');
          setFinalResult(taskInfo.final_result);
          setIsCompleted(true);
          setActiveAgent(null);

          // If events list is empty, backfill events
          setEvents((currentEvents) => {
            if (currentEvents.length === 0) {
              getTaskEvents(taskId).then((evts) => {
                if (evts && evts.length > 0) setEvents(evts);
              }).catch(() => {});
            }
            return currentEvents;
          });

          // Stop polling once completed
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }
        }
      } catch {
        // Ignore transient poll errors
      }
    }, 1500);

    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [taskId, clearEvents]);

  return {
    events,
    connectionStatus,
    finalResult,
    activeAgent,
    plan,
    isCompleted,
    error,
    clearEvents,
    loadHistoricalEvents,
  };
}
