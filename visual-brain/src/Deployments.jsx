import { useState } from 'react';
import { CheckCircle2, AlertCircle, Clock, Server, Globe2, ArrowUpRight, X } from 'lucide-react';

export default function Deployments() {
  const [activeModal, setActiveModal] = useState(null);
  const [selectedEnv, setSelectedEnv] = useState(null);

  const environments = [
    { id: 'env-prod', name: 'Production Cluster', region: 'us-east-1', status: 'healthy', version: 'v2.4.1', uptime: '99.99%', cpu: 45 },
    { id: 'env-staging', name: 'Staging Environment', region: 'eu-west-2', status: 'deploying', version: 'v2.5.0-rc1', uptime: '99.90%', cpu: 82 },
    { id: 'env-sandbox', name: 'DevAgent Sandbox', region: 'local', status: 'degraded', version: 'v2.5.0-dev', uptime: '85.40%', cpu: 95 },
  ];

  const openModal = (type, env) => {
    setSelectedEnv(env);
    setActiveModal(type);
  };
  
  const closeModal = () => {
    setActiveModal(null);
    setSelectedEnv(null);
  };

  return (
    <div style={{ position: 'relative', padding: '0 12px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h1 className="dashboard-title" style={{ marginBottom: '24px' }}>Deployments: Infrastructure Status</h1>
      
      {/* Top Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px', marginBottom: '24px' }}>
         <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(0, 255, 170, 0.1)', color: 'var(--success)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <ArrowUpRight size={24} />
            </div>
            <div>
               <div style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-main)' }}>99.98%</div>
               <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Global Uptime</div>
            </div>
         </div>
         <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(0, 240, 255, 0.1)', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <Globe2 size={24} />
            </div>
            <div>
               <div style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-main)' }}>1.2M</div>
               <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Requests / hr</div>
            </div>
         </div>
         <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(255, 51, 102, 0.1)', color: '#ff3366', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <AlertCircle size={24} />
            </div>
            <div>
               <div style={{ fontSize: '24px', fontWeight: 600, color: 'var(--text-main)' }}>0.02%</div>
               <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Error Rate</div>
            </div>
         </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px', flex: 1, minHeight: 0, overflowY: 'auto', paddingRight: '8px' }}>
         {environments.map(env => (
           <div key={env.id} className="glass-panel env-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                 <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Server size={20} color={env.status === 'healthy' ? 'var(--success)' : env.status === 'deploying' ? 'var(--accent-cyan)' : '#ff3366'} />
                    <div>
                       <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)' }}>{env.name}</div>
                       <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Region: {env.region}</div>
                    </div>
                 </div>
                 <div className={`env-status-badge ${env.status}`}>
                    {env.status === 'healthy' ? <CheckCircle2 size={12}/> : env.status === 'deploying' ? <Clock size={12} className="animate-spin" /> : <AlertCircle size={12}/>}
                    {env.status}
                 </div>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.02)' }}>
                 <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Version</div>
                    <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-main)', fontFamily: 'monospace' }}>{env.version}</div>
                 </div>
                 <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Uptime</div>
                    <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-main)' }}>{env.uptime}</div>
                 </div>
                 <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>CPU Load</div>
                    <div className="progress-bar-bg">
                       <div className="progress-bar-fill" style={{ width: `${env.cpu}%`, background: env.cpu > 90 ? '#ff3366' : env.cpu > 70 ? 'var(--accent-cyan)' : 'var(--success)' }}></div>
                    </div>
                 </div>
              </div>
              
              <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                 <button className="agent-btn secondary" onClick={() => openModal('logs', env)} style={{ flex: 'none', padding: '8px 24px' }}>View Logs</button>
                 <button className="agent-btn secondary" onClick={() => openModal('metrics', env)} style={{ flex: 'none', padding: '8px 24px' }}>Metrics</button>
              </div>
           </div>
         ))}
      </div>
      
      {/* Modal Overlay */}
      {activeModal && (
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
          zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
           <div className="glass-panel" style={{ width: '80%', maxWidth: '600px', maxHeight: '80%', display: 'flex', flexDirection: 'column', padding: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                 <h3 style={{ margin: 0, color: 'var(--text-main)', fontSize: '18px' }}>
                   {activeModal === 'logs' ? 'System Logs' : 'Live Metrics'} - {selectedEnv?.name}
                 </h3>
                 <X size={20} color="var(--text-muted)" style={{ cursor: 'pointer' }} onClick={closeModal} />
              </div>
              
              <div style={{ flex: 1, overflowY: 'auto', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '16px', border: '1px solid rgba(255,255,255,0.05)', fontFamily: 'monospace', fontSize: '13px', color: 'var(--text-main)', lineHeight: 1.6 }}>
                 {activeModal === 'logs' ? (
                    <div style={{ color: 'var(--accent-cyan)' }}>
                      <div style={{ color: 'var(--text-muted)' }}>[2026-08-12 14:01:22] <span style={{ color: 'var(--success)' }}>INFO</span>: Cluster heartbeat received.</div>
                      <div style={{ color: 'var(--text-muted)' }}>[2026-08-12 14:01:25] <span style={{ color: 'var(--success)' }}>INFO</span>: Auto-scaling group 'worker-nodes' normalized.</div>
                      <div style={{ color: 'var(--text-muted)' }}>[2026-08-12 14:02:10] <span style={{ color: '#ffcc00' }}>WARN</span>: Memory pressure detected on node-3. Re-routing traffic...</div>
                      <div style={{ color: 'var(--text-muted)' }}>[2026-08-12 14:02:15] <span style={{ color: 'var(--success)' }}>INFO</span>: Traffic successfully re-routed. Node-3 isolated for inspection.</div>
                      <div style={{ color: 'var(--text-muted)' }}>[2026-08-12 14:05:00] <span style={{ color: 'var(--success)' }}>INFO</span>: Agent deployment sequence initiated for {selectedEnv?.version}.</div>
                    </div>
                 ) : (
                    <div>
                       <div style={{ marginBottom: '12px' }}><strong>CPU Usage:</strong> <span style={{ color: 'var(--accent-cyan)' }}>{selectedEnv?.cpu}% (Stable)</span></div>
                       <div style={{ marginBottom: '12px' }}><strong>RAM Usage:</strong> <span style={{ color: 'var(--accent-purple)' }}>4.2 GB / 16.0 GB</span></div>
                       <div style={{ marginBottom: '12px' }}><strong>Network In:</strong> <span style={{ color: 'var(--success)' }}>450 Mbps</span></div>
                       <div style={{ marginBottom: '12px' }}><strong>Network Out:</strong> <span style={{ color: 'var(--success)' }}>1.2 Gbps</span></div>
                       <div style={{ marginBottom: '12px' }}><strong>Active Connections:</strong> <span style={{ color: 'var(--accent-cyan)' }}>12,450</span></div>
                    </div>
                 )}
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
