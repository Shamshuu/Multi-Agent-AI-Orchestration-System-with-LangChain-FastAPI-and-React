import React, { useState } from 'react';
import {
  Brain,
  Wrench,
  CheckCircle,
  AlertTriangle,
  ArrowRightCircle,
  ChevronDown,
  ChevronUp,
  Clock,
  Code2,
  Sparkles,
} from 'lucide-react';
import { AgentEvent, EventType } from '../types';

interface EventCardProps {
  event: AgentEvent;
}

export const EventCard: React.FC<EventCardProps> = ({ event }) => {
  const [showPayload, setShowPayload] = useState(false);

  const rawAgent = (event.agent || event.agent_name || 'System').toString();
  const agentClass = rawAgent.toLowerCase();
  const payload = event.payload || {};

  const renderIcon = (type: EventType) => {
    switch (type) {
      case 'AGENT_THOUGHT':
        return <Brain size={15} color="#818cf8" />;
      case 'TOOL_INVOCATION':
        return <Wrench size={15} color="#fbbf24" />;
      case 'TOOL_RESULT':
        return <CheckCircle size={15} color="#34d399" />;
      case 'STATE_TRANSITION':
        return <ArrowRightCircle size={15} color="#60a5fa" />;
      case 'COMPLETE':
        return <Sparkles size={15} color="#c084fc" />;
      case 'ERROR':
        return <AlertTriangle size={15} color="#f87171" />;
      default:
        return <Brain size={15} color="#94a3b8" />;
    }
  };

  const formatTimestamp = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div className={`event-item ${agentClass}`}>
      <div className="event-header">
        <div className="event-badges-group">
          <span className={`agent-name-tag ${agentClass}`}>
            {rawAgent}
          </span>
          <span className="event-type-label">
            {renderIcon(event.event_type)}
            <span>{event.event_type.replace('_', ' ')}</span>
          </span>
          {payload.tool && (
            <span className="tool-name-badge">
              Tool: {payload.tool}
            </span>
          )}
        </div>
        <span className="event-time">
          <Clock size={12} />
          <span>{formatTimestamp(event.timestamp)}</span>
        </span>
      </div>

      <div className="event-body">
        {payload.thought && <p className="event-thought-text">{payload.thought}</p>}
        {payload.message && <p>{payload.message}</p>}

        {/* Formulated Plan display */}
        {payload.plan && Array.isArray(payload.plan) && (
          <div className="plan-steps-container">
            <span style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', color: '#818cf8' }}>
              Execution Plan Steps:
            </span>
            {payload.plan.map((step: any, sIdx: number) => (
              <div key={sIdx} className="plan-step-row">
                <span className="plan-step-num">{step.step_number}.</span>
                <div>
                  <strong style={{ color: '#ffffff' }}>{step.title}</strong>
                  {step.tool_name && (
                    <span className="tool-name-badge" style={{ marginLeft: 6 }}>
                      [{step.tool_name}]
                    </span>
                  )}
                  <p style={{ color: '#94a3b8', fontSize: '0.74rem', marginTop: 2 }}>{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Dispatched Tool Args */}
        {payload.args && (
          <div className="tool-args-block">
            <span style={{ color: '#fbbf24', fontWeight: 600, display: 'block', marginBottom: 4 }}>
              Dispatched to Celery Worker:
            </span>
            <pre style={{ whiteSpace: 'pre-wrap', color: '#cbd5e1' }}>
              {JSON.stringify(payload.args, null, 2)}
            </pre>
          </div>
        )}

        {/* Tool Result Output */}
        {payload.result && (
          <div className="tool-output-block">
            <span style={{ color: '#34d399', fontWeight: 600, display: 'block' }}>
              Worker Result Output:
            </span>
            <pre>{payload.result}</pre>
          </div>
        )}

        {/* Error Notification */}
        {payload.error && (
          <div style={{ marginTop: 8, padding: 10, borderRadius: 6, background: 'rgba(244,63,94,0.15)', border: '1px solid rgba(244,63,94,0.3)', color: '#fda4af', fontSize: '0.8rem' }}>
            <strong>Error:</strong> {payload.error}
          </div>
        )}
      </div>

      <button onClick={() => setShowPayload(!showPayload)} className="raw-payload-btn">
        <Code2 size={12} />
        <span>{showPayload ? 'Hide Audit Payload' : 'View Audit Payload'}</span>
        {showPayload ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {showPayload && (
        <pre className="raw-payload-box">
          {JSON.stringify(payload, null, 2)}
        </pre>
      )}
    </div>
  );
};
