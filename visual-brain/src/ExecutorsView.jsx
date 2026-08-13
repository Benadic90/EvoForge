import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import { Cpu, Zap, Activity, AlertCircle } from 'lucide-react';

export default function ExecutorsView() {
  const [executors, setExecutors] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchExecutors = async () => {
    try {
      const data = await api.getExecutors();
      setExecutors(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutors();
    const interval = setInterval(fetchExecutors, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="p-8 text-[var(--text-muted)] text-center">Loading Executors & Models...</div>;
  }

  return (
    <div className="p-8 fade-in">
      <h1 style={{ fontSize: '24px', margin: '0 0 24px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Cpu size={24} />
        Executors & Models
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
        {executors.map((exec) => (
          <div key={exec.executor_id} className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {exec.executor_id}
                  {exec.is_available ? (
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00ffaa', display: 'inline-block' }} />
                  ) : (
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ff3366', display: 'inline-block' }} />
                  )}
                </h3>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{exec.provider} - {exec.model_name}</div>
              </div>
              <div style={{ fontSize: '11px', background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                {exec.executor_type}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
              <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Activity size={12} /> Success Rate
                </div>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{(exec.success_rate * 100).toFixed(1)}%</div>
              </div>
              <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Zap size={12} /> Avg Latency
                </div>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{exec.avg_latency_ms}ms</div>
              </div>
            </div>

            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              <strong>Capabilities:</strong> {exec.capabilities.join(', ') || 'Unknown'}
            </div>

            {!exec.is_available && (
              <div style={{ marginTop: '16px', padding: '12px', background: 'rgba(255, 51, 102, 0.1)', color: '#ff3366', borderRadius: '6px', fontSize: '12px', display: 'flex', gap: '8px' }}>
                <AlertCircle size={14} style={{ flexShrink: 0 }} />
                <span>{exec.unavailability_reason || 'Currently unavailable'}</span>
              </div>
            )}
          </div>
        ))}

        {executors.length === 0 && (
          <div style={{ gridColumn: '1 / -1', padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }} className="glass-panel">
            <Cpu size={32} style={{ margin: '0 auto 16px auto', opacity: 0.5 }} />
            <p>No executors registered.</p>
          </div>
        )}
      </div>
    </div>
  );
}
