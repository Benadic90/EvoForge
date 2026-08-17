import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import { Server, Zap, RefreshCw, PowerOff } from 'lucide-react';

export default function WorkerFleetView({ realTimeState }) {
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchWorkers = async () => {
    try {
      const data = await api.getWorkers();
      setWorkers(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkers();
    const interval = setInterval(fetchWorkers, 5000); // Polling for precise worker state
    return () => clearInterval(interval);
  }, []);

  const handleDrain = async (workerId) => {
    if (window.confirm(`Are you sure you want to drain worker ${workerId}? It will stop accepting new tasks.`)) {
      try {
        await api.drainWorker(workerId);
        fetchWorkers();
      } catch (err) {
        alert("Failed to drain worker: " + err.message);
      }
    }
  };

  if (loading) {
    return <div className="p-8 text-[var(--text-muted)] text-center">Loading Worker Fleet...</div>;
  }

  return (
    <div className="p-8 fade-in">
      <h1 style={{ fontSize: '24px', margin: '0 0 24px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Server size={24} />
        Worker Fleet
      </h1>

      <div style={{ display: 'grid', gap: '16px' }}>
        {workers.map((worker) => {
          const heartbeat = worker.last_heartbeat_at || worker.last_heartbeat || worker.last_seen_at;
          return (
          <div key={worker.worker_id} className="glass-panel" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                <h3 style={{ margin: 0, fontSize: '18px' }}>{worker.worker_id}</h3>
                <span style={{ 
                  fontSize: '11px', 
                  padding: '2px 8px', 
                  borderRadius: '12px',
                  background: worker.status === 'IDLE' ? 'rgba(0, 255, 170, 0.1)' 
                            : worker.status === 'RUNNING' ? 'rgba(0, 240, 255, 0.1)' 
                            : 'rgba(255, 51, 102, 0.1)',
                  color: worker.status === 'IDLE' ? '#00ffaa' : worker.status === 'RUNNING' ? '#00f0ff' : '#ff3366'
                }}>
                  {worker.status}
                </span>
                <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                  {worker.worker_type}
                </span>
              </div>
              
              <div style={{ fontSize: '13px', color: 'var(--text-muted)', display: 'flex', gap: '24px' }}>
                <div><strong>Capabilities:</strong> {(worker.capabilities || []).join(', ') || 'None'}</div>
                <div><strong>Last Heartbeat:</strong> {heartbeat ? new Date(heartbeat).toLocaleTimeString() : 'Never'}</div>
              </div>
              
              {worker.current_workflow_id && (
                <div style={{ marginTop: '12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', color: '#00f0ff' }}>
                  <RefreshCw size={14} className="spin" />
                  Running Workflow: {worker.current_workflow_id}
                </div>
              )}
            </div>
            
            <div style={{ display: 'flex', gap: '12px' }}>
              <button 
                onClick={() => handleDrain(worker.worker_id)}
                style={{
                  background: 'rgba(255, 51, 102, 0.1)',
                  border: '1px solid rgba(255, 51, 102, 0.2)',
                  color: '#ff3366',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <PowerOff size={14} /> Drain
              </button>
            </div>
          </div>
          );
        })}

        {workers.length === 0 && (
          <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Server size={32} style={{ margin: '0 auto 16px auto', opacity: 0.5 }} />
            <p>No workers connected.</p>
          </div>
        )}
      </div>
    </div>
  );
}
