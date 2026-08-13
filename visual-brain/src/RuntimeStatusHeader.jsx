import React from 'react';
import { Activity, Server, Database, AlertCircle, Clock, Zap } from 'lucide-react';

export default function RuntimeStatusHeader({ isOffline, system, runtime, scheduler }) {
  if (isOffline) {
    return (
      <div className="runtime-status-header" style={{ background: 'rgba(255, 51, 102, 0.1)', borderBottom: '1px solid rgba(255, 51, 102, 0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ff3366', padding: '12px 24px' }}>
          <AlertCircle size={20} />
          <strong>OFFLINE / DISCONNECTED</strong>
          <span style={{ marginLeft: '12px', fontSize: '13px', opacity: 0.8 }}>EvoForge Control Plane is unreachable.</span>
        </div>
      </div>
    );
  }

  // Parse statuses
  const systemState = system?.status || 'UNKNOWN';
  const schedulerState = scheduler?.status || 'UNKNOWN';
  
  const workersOnline = runtime?.workers_online ?? 0;
  const workersTotal = runtime?.workers_total ?? 0;
  
  const computeMode = runtime?.compute_mode || 'UNKNOWN';

  return (
    <div className="runtime-status-header" style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      padding: '12px 24px', 
      borderBottom: '1px solid rgba(255,255,255,0.05)',
      background: 'rgba(0,0,0,0.2)',
      fontSize: '13px'
    }}>
      <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Activity size={16} color={systemState === 'ONLINE' ? '#00ffaa' : '#ffaa00'} />
          <span style={{ color: 'var(--text-muted)' }}>EvoForge:</span>
          <strong style={{ color: systemState === 'ONLINE' ? '#00ffaa' : '#ffaa00' }}>{systemState}</strong>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Clock size={16} color={schedulerState === 'RUNNING' ? '#00f0ff' : '#ffaa00'} />
          <span style={{ color: 'var(--text-muted)' }}>Scheduler:</span>
          <strong style={{ color: schedulerState === 'RUNNING' ? '#00f0ff' : '#ffaa00' }}>{schedulerState}</strong>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Server size={16} color={workersOnline > 0 ? '#00ffaa' : '#ff3366'} />
          <span style={{ color: 'var(--text-muted)' }}>Workers:</span>
          <strong>{workersOnline} ONLINE</strong> <span style={{ opacity: 0.5 }}>/ {workersTotal}</span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Zap size={16} color="#e2b714" />
          <span style={{ color: 'var(--text-muted)' }}>Mode:</span>
          <strong style={{ color: '#e2b714' }}>{computeMode}</strong>
        </div>
      </div>
    </div>
  );
}
