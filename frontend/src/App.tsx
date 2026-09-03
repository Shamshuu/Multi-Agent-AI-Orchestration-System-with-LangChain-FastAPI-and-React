import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { TaskForm } from './components/TaskForm';
import { StateGraphVisualizer } from './components/StateGraphVisualizer';
import { TaskTimeline } from './components/TaskTimeline';
import { FinalResultView } from './components/FinalResultView';
import { TaskHistoryModal } from './components/TaskHistoryModal';
import { useAgentWebSocket } from './hooks/useAgentWebSocket';
import { createTask, getTaskEvents, checkHealth } from './services/api';
import { TaskRun } from './types';

export function App() {
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [activePrompt, setActivePrompt] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [historyOpen, setHistoryOpen] = useState<boolean>(false);
  const [hasGroq, setHasGroq] = useState<boolean>(false);

  const {
    events,
    connectionStatus,
    finalResult,
    activeAgent,
    plan,
    isCompleted,
    error,
    loadHistoricalEvents,
  } = useAgentWebSocket(currentTaskId);

  useEffect(() => {
    checkHealth()
      .then((data) => {
        if (data.has_groq_key) {
          setHasGroq(true);
        }
      })
      .catch((err) => console.warn('Health check warning:', err));
  }, []);

  const handleLaunchTask = async (prompt: string) => {
    setIsSubmitting(true);
    setActivePrompt(prompt);
    try {
      const resp = await createTask(prompt);
      setCurrentTaskId(resp.task_id);
    } catch (err: any) {
      alert(`Failed to launch task: ${err.message || err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectHistoricalTask = async (task: TaskRun) => {
    setHistoryOpen(false);
    setCurrentTaskId(task.id);
    setActivePrompt(task.prompt);

    try {
      const historicalEvents = await getTaskEvents(task.id);
      loadHistoricalEvents(historicalEvents, task.final_result);
    } catch (e) {
      console.error('Failed to load past task events:', e);
    }
  };

  useEffect(() => {
    if (finalResult) {
      setTimeout(() => {
        const el = document.getElementById('final-deliverable-section');
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 150);
    }
  }, [finalResult]);

  return (
    <div className="app-wrapper">
      <Navbar
        connectionStatus={connectionStatus}
        activeAgent={activeAgent}
        onOpenHistory={() => setHistoryOpen(true)}
        hasGroq={hasGroq}
      />

      <main className="main-content">
        {/* Task Form */}
        <TaskForm
          onSubmit={handleLaunchTask}
          isLoading={isSubmitting || (connectionStatus === 'connected' && !isCompleted)}
        />

        {/* State Graph Visualizer */}
        <StateGraphVisualizer activeAgent={activeAgent} isCompleted={isCompleted} plan={plan} />

        {/* Main Workspace: Timeline & Result Card */}
        <div className={`workspace-grid ${finalResult ? 'with-result' : ''}`}>
          <TaskTimeline
            events={events}
            isLoading={connectionStatus === 'connected' && !isCompleted}
          />

          {finalResult && (
            <div id="final-deliverable-section">
              <FinalResultView result={finalResult} prompt={activePrompt} />
            </div>
          )}
        </div>
      </main>

      {/* Task History Modal */}
      <TaskHistoryModal
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        onSelectTask={handleSelectHistoricalTask}
      />
    </div>
  );
}

export default App;
