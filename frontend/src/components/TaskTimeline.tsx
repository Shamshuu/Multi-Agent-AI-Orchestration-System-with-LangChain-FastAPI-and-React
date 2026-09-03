import React, { useState, useRef, useEffect } from 'react';
import { Activity } from 'lucide-react';
import { AgentEvent } from '../types';
import { EventCard } from './EventCard';

interface TaskTimelineProps {
  events: AgentEvent[];
  isLoading: boolean;
}

export const TaskTimeline: React.FC<TaskTimelineProps> = ({ events, isLoading }) => {
  const [filter, setFilter] = useState<string>('ALL');
  const scrollRef = useRef<HTMLDivElement>(null);

  const filteredEvents = events.filter((ev) => {
    const agent = (ev.agent || ev.agent_name || 'System').toString().toUpperCase();
    if (filter === 'ALL') return true;
    if (filter === 'PLANNER') return agent === 'PLANNER';
    if (filter === 'RESEARCHER') return agent === 'RESEARCHER';
    if (filter === 'SYNTHESIZER') return agent === 'SYNTHESIZER';
    if (filter === 'TOOLS') return ev.event_type === 'TOOL_INVOCATION' || ev.event_type === 'TOOL_RESULT';
    return true;
  });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <div className="glass-card timeline-card">
      <div className="timeline-header-row">
        <div className="card-title-group">
          <Activity size={16} className="card-title-icon" />
          <h3 className="card-title">Real-Time Audit Timeline</h3>
          <span className="timeline-count-badge">
            {events.length} events
          </span>
        </div>

        <div className="timeline-filter-group">
          {['ALL', 'PLANNER', 'RESEARCHER', 'TOOLS', 'SYNTHESIZER'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`filter-btn ${filter === f ? 'active' : ''}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div ref={scrollRef} className="timeline-scroll-area">
        {filteredEvents.length === 0 ? (
          <div className="timeline-empty">
            <Activity size={32} className="timeline-empty-icon" />
            <p style={{ fontSize: '0.86rem', color: '#cbd5e1' }}>Awaiting task submission...</p>
            <p style={{ fontSize: '0.74rem', color: '#64748b' }}>
              Events will stream here in real-time as agents transition and execute Celery tools.
            </p>
          </div>
        ) : (
          filteredEvents.map((ev, idx) => <EventCard key={ev.id || idx} event={ev} />)
        )}

        {isLoading && (
          <div style={{ padding: '12px 16px', borderRadius: 8, background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.3)', color: '#c7d2fe', fontSize: '0.78rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="active-agent-dot" />
            <span>Agent workflow in progress...</span>
          </div>
        )}
      </div>
    </div>
  );
};
