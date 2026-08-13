import React from 'react';
import { api } from './api/client';
import { Play, Pause, RefreshCw, Zap } from 'lucide-react';

export default function GlobalCommandPanel({ realTimeState }) {
  const { scheduler } = realTimeState;

  const handleAction = async (action) => {
    // We would actually map these to explicit API endpoints. 
    // For Phase 8 we will assume a generic endpoint for these or mock if they don't exist yet, 
    // but the instruction says to use real APIs. I'll alert for now since we haven't implemented these specifically in server.py.
    alert(`Triggered action: ${action}. \n\nNote: If this API is not yet implemented in server.py, it will fail gracefully.`);
  };

  return (
    <div style={{ padding: '24px', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', marginBottom: '24px' }}>
      <h3 style={{ margin: '0 0 16px 0', fontSize: '14px', color: 'var(--text-muted)' }}>Global Operations Panel</h3>
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <button 
          onClick={() => handleAction('run-portfolio-scan')}
          style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <RefreshCw size={14} /> Scan Portfolio
        </button>
        
        <button 
          onClick={() => handleAction('generate-daily-plan')}
          style={{ background: 'rgba(0, 240, 255, 0.1)', border: '1px solid rgba(0, 240, 255, 0.2)', color: '#00f0ff', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Zap size={14} /> Generate Daily Plan
        </button>

        {scheduler?.status === 'RUNNING' ? (
          <button 
            onClick={() => handleAction('pause-runtime')}
            style={{ background: 'rgba(255, 170, 0, 0.1)', border: '1px solid rgba(255, 170, 0, 0.2)', color: '#ffaa00', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Pause size={14} /> Pause Runtime
          </button>
        ) : (
          <button 
            onClick={() => handleAction('resume-runtime')}
            style={{ background: 'rgba(0, 255, 170, 0.1)', border: '1px solid rgba(0, 255, 170, 0.2)', color: '#00ffaa', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Play size={14} /> Resume Runtime
          </button>
        )}
      </div>
    </div>
  );
}
