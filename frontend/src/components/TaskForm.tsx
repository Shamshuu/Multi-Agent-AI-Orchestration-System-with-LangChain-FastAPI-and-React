import React, { useState } from 'react';
import { Send, Sparkles, Terminal, CloudSun, TrendingUp, Cpu } from 'lucide-react';

interface TaskFormProps {
  onSubmit: (prompt: string) => Promise<void>;
  isLoading: boolean;
}

const SAMPLE_PROMPTS = [
  {
    title: 'Tokyo Weather & Packing',
    type: 'tokyo',
    icon: CloudSun,
    prompt: 'What is the current weather and 3-day forecast in Tokyo, Japan, and based on that and cultural norms, what should I pack for a business and leisure trip?',
  },
  {
    title: 'Financial CAGR & Growth',
    type: 'finance',
    icon: TrendingUp,
    prompt: 'Compute the 5-year future value of a $50,000 investment compounding at 9.5% annually, find industry tech benchmarks, and synthesize an executive investment summary.',
  },
  {
    title: 'AI Multi-Agent State Research',
    type: 'research',
    icon: Cpu,
    prompt: 'Search the latest architectural patterns for autonomous multi-agent state machines with LangGraph and Celery, and synthesize key design guidelines.',
  },
];

export const TaskForm: React.FC<TaskFormProps> = ({ onSubmit, isLoading }) => {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    await onSubmit(prompt.trim());
  };

  return (
    <div className="glass-card task-form-card">
      <div className="card-header-row">
        <div className="card-title-group">
          <Terminal size={16} className="card-title-icon" />
          <h2 className="card-title">Submit Complex Objective</h2>
        </div>
        <span className="card-subtitle">
          Deconstructed across Strategic Planner, Researcher with Celery Tools, and Synthesizer
        </span>
      </div>

      <form onSubmit={handleSubmit}>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the multi-step problem or objective for the agents to plan, execute with tools, and synthesize..."
          rows={3}
          disabled={isLoading}
          className="form-textarea"
        />

        <div className="template-pills-row">
          <span className="template-label">
            <Sparkles size={13} /> Quick Templates:
          </span>
          {SAMPLE_PROMPTS.map((sample, idx) => {
            const Icon = sample.icon;
            return (
              <button
                key={idx}
                type="button"
                onClick={() => setPrompt(sample.prompt)}
                disabled={isLoading}
                className={`template-pill ${sample.type}`}
              >
                <Icon size={13} />
                <span>{sample.title}</span>
              </button>
            );
          })}
        </div>

        <div className="form-action-row">
          <button
            type="submit"
            disabled={isLoading || !prompt.trim()}
            className="btn-primary"
          >
            {isLoading ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="animate-spin">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.25" />
                  <path fill="currentColor" opacity="0.75" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Orchestrating Agents...</span>
              </>
            ) : (
              <>
                <Send size={15} />
                <span>Launch Multi-Agent Workflow</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
