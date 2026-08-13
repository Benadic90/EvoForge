import React, { useState, useEffect } from 'react';
import { Activity, Server, Clock, Power, Shield } from 'lucide-react';

export default function RuntimeView() {
  const [runtimeStatus, setRuntimeStatus] = useState(null);
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [rtRes, wRes] = await Promise.all([
          fetch('http://localhost:8000/api/runtime/status'),
          fetch('http://localhost:8000/api/workers')
        ]);
        if (rtRes.ok) setRuntimeStatus(await rtRes.json());
        if (wRes.ok) {
          const data = await wRes.json();
          setWorkers(data.workers || []);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    
    fetchStatus();
    const int = setInterval(fetchStatus, 3000);
    return () => clearInterval(int);
  }, []);

  if (loading) return <div className="p-8 text-center text-[var(--text-muted)]">Loading Runtime Status...</div>;

  const isPaused = runtimeStatus?.scheduler?.status === 'PAUSED';

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', animation: 'fadeIn 0.3s ease-out' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '24px', margin: '0 0 8px 0', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={24} color="var(--primary-color)" />
            Always-On Cloud Runtime
          </h1>
          <p style={{ margin: 0, color: 'var(--text-muted)' }}>Monitor active cloud workers and persistent scheduling engine.</p>
        </div>
        
        <div style={{ display: 'flex', gap: '12px' }}>
          <div className="metric-box" style={{ padding: '12px 24px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Scheduler</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: isPaused ? '#ffaa00' : '#00ffaa' }}>
              {runtimeStatus?.scheduler?.status || 'UNKNOWN'}
            </div>
          </div>
          <div className="metric-box" style={{ padding: '12px 24px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Active Workers</div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: 'white' }}>
              {runtimeStatus?.workers_online} / {runtimeStatus?.workers_total}
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gap: '24px', gridTemplateColumns: '1fr' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '18px', margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Server size={18} />
            Worker Fleet
          </h2>
          
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>
                <th style={{ padding: '12px 8px' }}>Worker ID</th>
                <th style={{ padding: '12px 8px' }}>Type</th>
                <th style={{ padding: '12px 8px' }}>Status</th>
                <th style={{ padding: '12px 8px' }}>Active Task</th>
                <th style={{ padding: '12px 8px' }}>Last Heartbeat</th>
              </tr>
            </thead>
            <tbody>
              {workers.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No workers registered</td>
                </tr>
              ) : (
                workers.map(w => (
                  <tr key={w.worker_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '16px 8px', fontFamily: 'monospace' }}>{w.worker_id}</td>
                    <td style={{ padding: '16px 8px' }}>
                      <span style={{ 
                        padding: '4px 8px', 
                        borderRadius: '4px', 
                        fontSize: '11px', 
                        background: w.worker_type === 'CLOUD' ? 'rgba(0, 240, 255, 0.1)' : 'rgba(255, 170, 0, 0.1)',
                        color: w.worker_type === 'CLOUD' ? '#00f0ff' : '#ffaa00'
                      }}>
                        {w.worker_type}
                      </span>
                    </td>
                    <td style={{ padding: '16px 8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <div style={{ 
                          width: '8px', 
                          height: '8px', 
                          borderRadius: '50%', 
                          background: w.status === 'BUSY' ? '#00f0ff' : 
                                      w.status === 'IDLE' ? '#00ffaa' : 
                                      w.status === 'OFFLINE' ? '#ff3366' : '#ffaa00'
                        }} />
                        {w.status}
                      </div>
                    </td>
                    <td style={{ padding: '16px 8px', color: w.current_workflow_id ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                      {w.current_workflow_id || 'Waiting for work'}
                    </td>
                    <td style={{ padding: '16px 8px', fontSize: '13px', color: 'var(--text-muted)' }}>
                      {w.last_heartbeat_at ? new Date(w.last_heartbeat_at).toLocaleTimeString() : 'Never'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
