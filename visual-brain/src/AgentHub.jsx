import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import { Users, Brain, Target, ShieldCheck } from 'lucide-react';

export default function AgentHub() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const data = await api.getAgents();
        setAgents(data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAgents();
  }, []);

  if (loading) {
    return <div className="p-8 text-[var(--text-muted)] text-center">Loading Agent Hub...</div>;
  }

  return (
    <div className="p-8 fade-in">
      <h1 style={{ fontSize: '24px', margin: '0 0 24px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Users size={24} />
        Agent Hub
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '24px' }}>
        {agents.map(agent => (
          <div key={agent.agent_id} className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {agent.agent_id}
                  {agent.status === 'IDLE' ? (
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00ffaa', display: 'inline-block' }} />
                  ) : (
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#00f0ff', display: 'inline-block' }} />
                  )}
                </h3>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{agent.role || 'General Purpose Agent'}</div>
              </div>
              <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '4px' }}>
                {agent.status}
              </span>
            </div>

            <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}><Brain size={12}/> Capabilities</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {agent.capabilities.map(cap => (
                  <span key={cap} style={{ fontSize: '10px', background: 'rgba(0, 240, 255, 0.1)', color: '#00f0ff', padding: '2px 6px', borderRadius: '4px' }}>
                    {cap}
                  </span>
                ))}
                {agent.capabilities.length === 0 && <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>None defined</span>}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '16px' }}>
               <div style={{ flex: 1, padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}><Target size={12}/> Primary</div>
                  <div style={{ fontSize: '13px' }}>{agent.primary_executor || 'Dynamic'}</div>
               </div>
            </div>
            
            {agent.current_task_id && (
              <div style={{ marginTop: '16px', fontSize: '12px', color: '#00f0ff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="pulse-dot" style={{ background: '#00f0ff', width: '6px', height: '6px', borderRadius: '50%' }}></span>
                Working on: {agent.current_task_id}
              </div>
            )}
          </div>
        ))}
        {agents.length === 0 && (
          <div className="glass-panel" style={{ gridColumn: '1 / -1', padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <Users size={32} style={{ margin: '0 auto 16px auto', opacity: 0.5 }} />
            <p>No agents active.</p>
          </div>
        )}
      </div>
    </div>
  );
}
