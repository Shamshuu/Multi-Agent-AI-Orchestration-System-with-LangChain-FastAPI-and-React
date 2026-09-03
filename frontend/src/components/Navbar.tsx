import React from 'react';
import { Layers, Sparkles, History } from 'lucide-react';
import { AgentName } from '../types';

interface NavbarProps {
  connectionStatus: 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error';
  activeAgent: AgentName | null;
  onOpenHistory: () => void;
  hasGroq: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  connectionStatus,
  activeAgent,
  onOpenHistory,
  hasGroq,
}) => {
  return (
    <header className="navbar">
      <div className="navbar-left">
        <div className="logo-badge">
          <Layers size={22} />
        </div>
        <div className="brand-details">
          <div className="brand-title-row">
            <span className="brand-title">AgentMesh</span>
            <span className="tech-badge">LangGraph + Celery</span>
            {hasGroq && (
              <span className="groq-badge">
                <Sparkles size={12} /> Groq Powered
              </span>
            )}
          </div>
          <span className="brand-subtitle">
            Autonomous Multi-Agent State Machine & Distributed Tool Orchestrator
          </span>
        </div>
      </div>

      <div className="navbar-right">
        {activeAgent && (
          <div className="active-agent-badge">
            <span className="active-agent-dot" />
            <span>Active: <strong>{activeAgent}</strong></span>
          </div>
        )}

        <div className="connection-badge">
          <span className={`status-dot ${connectionStatus}`} />
          <span>
            {connectionStatus === 'connected'
              ? 'Live Stream'
              : connectionStatus === 'connecting'
              ? 'Connecting...'
              : 'Standby'}
          </span>
        </div>

        <button onClick={onOpenHistory} className="nav-button">
          <History size={14} />
          <span>Audit Log</span>
        </button>
      </div>
    </header>
  );
};
