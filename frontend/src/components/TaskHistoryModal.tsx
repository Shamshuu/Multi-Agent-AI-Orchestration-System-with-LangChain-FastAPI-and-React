import React, { useEffect, useState } from 'react';
import { X, History, ArrowRight, RefreshCw, Loader2 } from 'lucide-react';
import { TaskRun } from '../types';
import { listTasks } from '../services/api';

interface TaskHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTask: (task: TaskRun) => Promise<void>;
}

export const TaskHistoryModal: React.FC<TaskHistoryModalProps> = ({
  isOpen,
  onClose,
  onSelectTask,
}) => {
  const [tasks, setTasks] = useState<TaskRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listTasks();
      setTasks(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load task history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchTasks();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">
            <History size={18} color="#818cf8" />
            <span>PostgreSQL Task Audit Log</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <button onClick={fetchTasks} disabled={loading} className="modal-close-btn" title="Refresh">
              <RefreshCw size={15} />
            </button>
            <button onClick={onClose} className="modal-close-btn">
              <X size={18} />
            </button>
          </div>
        </div>

        <div className="modal-list">
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 32, gap: 8, color: '#94a3b8' }}>
              <Loader2 size={18} className="animate-spin" />
              <span>Querying database...</span>
            </div>
          )}

          {error && (
            <div style={{ padding: 12, borderRadius: 8, background: 'rgba(244,63,94,0.15)', border: '1px solid rgba(244,63,94,0.3)', color: '#fda4af', fontSize: '0.78rem' }}>
              {error}
            </div>
          )}

          {!loading && !error && tasks.length === 0 && (
            <div style={{ textAlign: 'center', padding: 32, color: '#64748b', fontSize: '0.86rem' }}>
              No historical task runs recorded yet.
            </div>
          )}

          {!loading &&
            tasks.map((task) => (
              <div
                key={task.id}
                onClick={() => onSelectTask(task)}
                className="modal-task-item"
              >
                <div style={{ flex: 1, minWidth: 0, paddingRight: 16 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span className={`status-badge ${task.status.toLowerCase()}`}>
                      {task.status}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: '#64748b' }}>
                      ID: {task.id.slice(0, 8)}...
                    </span>
                  </div>
                  <p style={{ fontSize: '0.84rem', color: '#f1f5f9', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {task.prompt}
                  </p>
                  <span style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 4, display: 'block' }}>
                    {task.created_at ? new Date(task.created_at).toLocaleString() : ''}
                  </span>
                </div>

                <button className="action-btn" style={{ background: 'rgba(99,102,241,0.2)', color: '#c7d2fe' }}>
                  <span>View</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};
