import React from 'react';
import { Network, CheckCircle2, Search, CloudRain, Calculator } from 'lucide-react';
import { AgentName, PlanStep } from '../types';

interface StateGraphVisualizerProps {
  activeAgent: AgentName | null;
  isCompleted: boolean;
  plan: PlanStep[];
}

export const StateGraphVisualizer: React.FC<StateGraphVisualizerProps> = ({
  activeAgent,
  isCompleted,
  plan,
}) => {
  const isPlannerDone = isCompleted || activeAgent === 'Researcher' || activeAgent === 'Synthesizer';
  const isResearcherDone = isCompleted || activeAgent === 'Synthesizer';
  const isSynthesizerDone = isCompleted;

  return (
    <div className="glass-card state-graph-card">
      <div className="card-header-row">
        <div className="card-title-group">
          <Network size={16} className="card-title-icon" />
          <h3 className="card-title">LangGraph Agent State Machine</h3>
        </div>
        <span className="state-status-tag">
          State: {isCompleted ? 'COMPLETED' : activeAgent ? `EXEC_${activeAgent.toUpperCase()}` : 'IDLE'}
        </span>
      </div>

      <div className="graph-nodes-grid">
        {/* 1. Planner Node */}
        <div
          className={`node-card ${
            activeAgent === 'Planner'
              ? 'active'
              : isPlannerDone
              ? 'completed'
              : 'idle'
          }`}
        >
          <div className="node-top">
            <span className="node-id">Node 01</span>
            {isPlannerDone ? (
              <CheckCircle2 size={16} color="#10b981" />
            ) : activeAgent === 'Planner' ? (
              <span className="active-agent-dot" />
            ) : null}
          </div>
          <h4 className="node-title">Strategic Planner</h4>
          <p className="node-desc">
            Deconstructs objective into {plan.length ? `${plan.length} structured` : 'ordered'} tool-assisted phases.
          </p>
        </div>

        {/* 2. Researcher & Celery Node */}
        <div
          className={`node-card researcher ${
            activeAgent === 'Researcher'
              ? 'active researcher'
              : isResearcherDone
              ? 'completed'
              : 'idle'
          }`}
        >
          <div className="node-top">
            <span className="node-id">Node 02</span>
            {isResearcherDone ? (
              <CheckCircle2 size={16} color="#10b981" />
            ) : activeAgent === 'Researcher' ? (
              <span className="active-agent-dot" />
            ) : null}
          </div>
          <h4 className="node-title">Researcher & Tools</h4>
          <p className="node-desc">
            Dispatches tools asynchronously to Celery distributed worker via Redis.
          </p>
          <div className="node-tools-list">
            <span className="micro-tool-pill">
              <Search size={11} /> Web
            </span>
            <span className="micro-tool-pill">
              <CloudRain size={11} /> Weather
            </span>
            <span className="micro-tool-pill">
              <Calculator size={11} /> Math
            </span>
          </div>
        </div>

        {/* 3. Synthesizer Node */}
        <div
          className={`node-card synthesizer ${
            activeAgent === 'Synthesizer'
              ? 'active synthesizer'
              : isSynthesizerDone
              ? 'completed'
              : 'idle'
          }`}
        >
          <div className="node-top">
            <span className="node-id">Node 03</span>
            {isSynthesizerDone ? (
              <CheckCircle2 size={16} color="#10b981" />
            ) : activeAgent === 'Synthesizer' ? (
              <span className="active-agent-dot" />
            ) : null}
          </div>
          <h4 className="node-title">Executive Synthesizer</h4>
          <p className="node-desc">
            Consolidates accumulated evidence into a polished Markdown deliverable.
          </p>
        </div>
      </div>
    </div>
  );
};
