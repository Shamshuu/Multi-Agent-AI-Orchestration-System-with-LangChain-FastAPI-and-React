import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Check, Copy, Download, Sparkles } from 'lucide-react';

interface FinalResultViewProps {
  result: string;
  prompt?: string;
}

export const FinalResultView: React.FC<FinalResultViewProps> = ({ result, prompt }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy result:', err);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([result], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-synthesis-${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="glass-card result-card">
      <div className="result-header-row">
        <div className="result-title-group">
          <div className="result-icon-badge">
            <Sparkles size={18} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff' }}>
              Synthesized Executive Deliverable
            </h3>
            <span style={{ fontSize: '0.74rem', color: '#34d399', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
              <span className="status-dot connected" /> Multi-Agent Workflow Completed
            </span>
          </div>
        </div>

        <div className="result-actions">
          <button onClick={handleCopy} className="action-btn">
            {copied ? <Check size={13} color="#34d399" /> : <Copy size={13} />}
            <span>{copied ? 'Copied!' : 'Copy'}</span>
          </button>
          <button onClick={handleDownload} className="action-btn">
            <Download size={13} />
            <span>Download .md</span>
          </button>
        </div>
      </div>

      <div className="markdown-container">
        <ReactMarkdown>{result}</ReactMarkdown>
      </div>
    </div>
  );
};
