import React from 'react';
import { ActivitySquare, CheckCircle, XCircle, Clock } from 'lucide-react';
import { api } from './api/client';
import GlobalCommandPanel from './GlobalCommandPanel';

export default function Dashboard({ realTimeState }) {
  const { system, runtime, scheduler, events, loading } = realTimeState;

  if (loading) {
    return <div className="p-8 text-[var(--text-muted)] text-center">Loading Mission Control...</div>;
  }

  // Filter out recent workflow activity
  const workflowEvents = events.filter(e => e.event_type.startsWith('workflow.'));
  const recentWorkflows = workflowEvents.slice(0, 5);

  return (
    <div className="dashboard-content p-8 fade-in">
      <div className="header-section" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '28px', margin: '0 0 8px 0' }}>Mission Control</h1>
          <p style={{ margin: 0, color: 'var(--text-muted)' }}>Unified Command & Telemetry</p>
        </div>
      </div>

      <GlobalCommandPanel realTimeState={realTimeState} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
        <div className="metric-box" style={{ background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '12px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '8px' }}>EvoForge</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: system?.status === 'ONLINE' ? '#00ffaa' : '#ffaa00' }}>
            {system?.status || 'UNKNOWN'}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Core Platform State</div>
        </div>
        
        <div className="metric-box" style={{ background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '12px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '8px' }}>Active Workers</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {runtime?.workers_online ?? 'NO DATA'} <span style={{ fontSize: '14px', opacity: 0.5 }}>/ {runtime?.workers_total ?? 0}</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Fleet Capacity</div>
        </div>

        <div className="metric-box" style={{ background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '12px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '8px' }}>Scheduler</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: scheduler?.status === 'RUNNING' ? '#00f0ff' : '#ffaa00' }}>
            {scheduler?.status || 'UNKNOWN'}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Background Loop</div>
        </div>

        <div className="metric-box" style={{ background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '12px' }}>
          <div style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '8px' }}>Compute Policy</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#e2b714' }}>
            {runtime?.compute_mode || 'UNKNOWN'}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>Routing Tier</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '18px', margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ActivitySquare size={18} />
            Recent Workflow Activity
          </h2>
          {recentWorkflows.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No recent workflows</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {recentWorkflows.map((event, idx) => (
                <div key={idx} style={{ 
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', borderLeft: `3px solid ${event.severity === 'ERROR' ? '#ff3366' : '#00f0ff'}`
                }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: 'bold' }}>{event.event_type}</span>
                      {event.project_id && <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px' }}>{event.project_id}</span>}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{event.details}</div>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '18px', margin: '0 0 20px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={18} />
            System Events
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', height: '400px', overflowY: 'auto' }}>
            {events.slice(0, 15).map((e, idx) => (
              <div key={idx} style={{ padding: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{new Date(e.timestamp).toLocaleTimeString()}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-primary)' }}>{e.event_type}</div>
              </div>
            ))}
            {events.length === 0 && <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No recent events.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
