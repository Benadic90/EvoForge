import React, { useState } from 'react';
import { api } from './api/client';
import { Play, Pause, RefreshCw, Zap, Flame, CheckCircle, AlertCircle, Loader } from 'lucide-react';

export default function GlobalCommandPanel({ realTimeState }) {
  const { scheduler } = realTimeState;
  const [loadingAction, setLoadingAction] = useState(null);
  const [feedback, setFeedback] = useState(null);

  const executeAction = async (actionName, apiCall, successMessage) => {
    setLoadingAction(actionName);
    setFeedback(null);
    try {
      const res = await apiCall();
      setFeedback({ success: true, message: successMessage || res?.message || 'Operation executed successfully!' });
    } catch (err) {
      setFeedback({ success: false, message: err.message || `Failed to execute ${actionName}` });
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div style={{ padding: '24px', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', marginBottom: '24px', border: '1px solid rgba(255,255,255,0.06)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, fontSize: '14px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Autonomous Command & Operations
        </h3>
        {scheduler?.status && (
          <span style={{ 
            fontSize: '12px', 
            padding: '3px 8px', 
            borderRadius: '4px', 
            background: scheduler.status === 'RUNNING' ? 'rgba(0, 255, 170, 0.15)' : 'rgba(255, 170, 0, 0.15)',
            color: scheduler.status === 'RUNNING' ? '#00ffaa' : '#ffaa00',
            fontWeight: 'bold'
          }}>
            Scheduler: {scheduler.status}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        {/* Trigger Daily Loop */}
        <button 
          onClick={() => executeAction('daily-run', () => api.forceRunDaily(), 'AI Agent awoken! Autonomous daily run is now executing in background.')}
          disabled={loadingAction !== null}
          style={{ 
            background: 'linear-gradient(135deg, rgba(0, 240, 255, 0.25), rgba(112, 0, 255, 0.25))', 
            border: '1px solid rgba(0, 240, 255, 0.4)', 
            color: '#fff', 
            padding: '10px 18px', 
            borderRadius: '8px', 
            cursor: 'pointer', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            fontWeight: 'bold',
            opacity: loadingAction ? 0.6 : 1
          }}
        >
          {loadingAction === 'daily-run' ? <Loader size={16} className="spin" /> : <Flame size={16} color="#00f0ff" />}
          Trigger Autonomous Daily Run
        </button>

        {/* Scan Portfolio */}
        <button 
          onClick={() => executeAction('scan', () => api.scanPortfolio(), 'Portfolio scanned! Discovered autonomous engineering upgrades & updated backlog.')}
          disabled={loadingAction !== null}
          style={{ 
            background: 'rgba(255,255,255,0.05)', 
            border: '1px solid rgba(255,255,255,0.1)', 
            color: 'white', 
            padding: '10px 16px', 
            borderRadius: '8px', 
            cursor: 'pointer', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            opacity: loadingAction ? 0.6 : 1
          }}
        >
          {loadingAction === 'scan' ? <Loader size={16} className="spin" /> : <RefreshCw size={16} />}
          Scan Portfolio
        </button>
        
        {/* Generate Plan */}
        <button 
          onClick={() => executeAction('plan', () => api.generateDailyPlan(), 'Generated prioritized daily upgrade plan from portfolio backlog.')}
          disabled={loadingAction !== null}
          style={{ 
            background: 'rgba(0, 240, 255, 0.1)', 
            border: '1px solid rgba(0, 240, 255, 0.2)', 
            color: '#00f0ff', 
            padding: '10px 16px', 
            borderRadius: '8px', 
            cursor: 'pointer', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px',
            opacity: loadingAction ? 0.6 : 1
          }}
        >
          {loadingAction === 'plan' ? <Loader size={16} className="spin" /> : <Zap size={16} />}
          Generate Daily Plan
        </button>

        {/* Resume / Pause Runtime */}
        {scheduler?.status === 'RUNNING' ? (
          <button 
            onClick={() => executeAction('pause', () => api.pauseRuntime(), 'Scheduler paused.')}
            disabled={loadingAction !== null}
            style={{ 
              background: 'rgba(255, 170, 0, 0.1)', 
              border: '1px solid rgba(255, 170, 0, 0.2)', 
              color: '#ffaa00', 
              padding: '10px 16px', 
              borderRadius: '8px', 
              cursor: 'pointer', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              opacity: loadingAction ? 0.6 : 1
            }}
          >
            {loadingAction === 'pause' ? <Loader size={16} className="spin" /> : <Pause size={16} />}
            Pause 24/7 Runtime
          </button>
        ) : (
          <button 
            onClick={() => executeAction('resume', () => api.resumeRuntime(), '24/7 autonomous background runtime resumed!')}
            disabled={loadingAction !== null}
            style={{ 
              background: 'rgba(0, 255, 170, 0.1)', 
              border: '1px solid rgba(0, 255, 170, 0.2)', 
              color: '#00ffaa', 
              padding: '10px 16px', 
              borderRadius: '8px', 
              cursor: 'pointer', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              opacity: loadingAction ? 0.6 : 1
            }}
          >
            {loadingAction === 'resume' ? <Loader size={16} className="spin" /> : <Play size={16} />}
            Resume 24/7 Runtime
          </button>
        )}
      </div>

      {feedback && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '13px',
          background: feedback.success ? 'rgba(0, 255, 170, 0.1)' : 'rgba(255, 68, 68, 0.1)',
          color: feedback.success ? '#00ffaa' : '#ff4444',
          border: `1px solid ${feedback.success ? 'rgba(0, 255, 170, 0.25)' : 'rgba(255, 68, 68, 0.25)'}`
        }}>
          {feedback.success ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          <span>{feedback.message}</span>
        </div>
      )}
    </div>
  );
}
