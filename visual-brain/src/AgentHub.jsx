import { useState } from 'react';
import { Cpu, ShieldCheck, TerminalSquare, BrainCircuit, Activity, MoreVertical, X } from 'lucide-react';

export default function AgentHub() {
  const [activeModal, setActiveModal] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);

  const agents = [
    {
      id: 1,
      name: 'Evolution Engine',
      role: 'System Orchestrator',
      status: 'active',
      level: 42,
      memory: '2.4k',
      load: 78,
      icon: BrainCircuit,
      color: '#b026ff'
    },
    {
      id: 2,
      name: 'DevAgent Alpha',
      role: 'Code Synthesis',
      status: 'active',
      level: 28,
      memory: '1.1k',
      load: 64,
      icon: TerminalSquare,
      color: '#00f0ff'
    },
    {
      id: 3,
      name: 'Security Sentinel',
      role: 'Vulnerability Scanning',
      status: 'monitoring',
      level: 35,
      memory: '850',
      load: 12,
      icon: ShieldCheck,
      color: '#00ffaa'
    },
    {
      id: 4,
      name: 'Data Processor',
      role: 'Log Analysis',
      status: 'idle',
      level: 14,
      memory: '4.2k',
      load: 2,
      icon: Cpu,
      color: '#8b949e'
    }
  ];

  const openModal = (type, agent) => {
    setSelectedAgent(agent);
    setActiveModal(type);
  };
  
  const closeModal = () => {
    setActiveModal(null);
    setSelectedAgent(null);
  };

  return (
    <div style={{ position: 'relative', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h1 className="dashboard-title" style={{ marginBottom: '24px' }}>Agent Hub: System Entities</h1>
      
      <div className="agents-grid">
        {agents.map(agent => {
          const Icon = agent.icon;
          return (
            <div key={agent.id} className="glass-panel agent-card" style={{ borderColor: `rgba(255,255,255,0.05)` }}>
              <div className="agent-card-header">
                <div className="agent-icon-wrapper" style={{ background: `${agent.color}20`, color: agent.color }}>
                  <Icon size={24} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div className="agent-name">{agent.name}</div>
                    <MoreVertical size={16} color="var(--text-muted)" style={{ cursor: 'pointer' }} />
                  </div>
                  <div className="agent-role">{agent.role}</div>
                </div>
              </div>
              
              <div className="agent-stats">
                <div className="stat-box">
                  <div className="stat-label">Level</div>
                  <div className="stat-value">{agent.level}</div>
                </div>
                <div className="stat-box">
                  <div className="stat-label">Memories</div>
                  <div className="stat-value">{agent.memory}</div>
                </div>
                <div className="stat-box">
                  <div className="stat-label">Status</div>
                  <div className="stat-value" style={{ 
                    color: agent.status === 'active' ? 'var(--accent-cyan)' : agent.status === 'monitoring' ? 'var(--success)' : 'var(--text-muted)',
                    textTransform: 'capitalize'
                  }}>
                    {agent.status}
                  </div>
                </div>
              </div>
              
              <div className="agent-load">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Activity size={12}/> Compute Load</span>
                  <span>{agent.load}%</span>
                </div>
                <div className="progress-bar-bg">
                  <div className="progress-bar-fill" style={{ width: `${agent.load}%`, background: agent.color, boxShadow: `0 0 10px ${agent.color}` }}></div>
                </div>
              </div>
              
              <div className="agent-actions">
                <button className="agent-btn primary" onClick={() => openModal('configure', agent)}>Configure</button>
                <button className="agent-btn secondary" onClick={() => openModal('logs', agent)}>Logs</button>
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Modal Overlay */}
      {activeModal && (
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
          zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
           <div className="glass-panel" style={{ width: '80%', maxWidth: '600px', maxHeight: '80%', display: 'flex', flexDirection: 'column', padding: '24px', border: `1px solid ${selectedAgent?.color}40`, boxShadow: `0 0 30px ${selectedAgent?.color}20` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                 <h3 style={{ margin: 0, color: 'var(--text-main)', fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                   {activeModal === 'logs' ? 'Agent Stream Logs' : 'Configure Agent'} - <span style={{ color: selectedAgent?.color }}>{selectedAgent?.name}</span>
                 </h3>
                 <X size={20} color="var(--text-muted)" style={{ cursor: 'pointer' }} onClick={closeModal} />
              </div>
              
              <div style={{ flex: 1, overflowY: 'auto', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
                 {activeModal === 'logs' ? (
                    <div style={{ fontFamily: 'monospace', fontSize: '13px', lineHeight: 1.6 }}>
                      <div style={{ color: 'var(--text-muted)' }}>[00:00.01] <span style={{ color: selectedAgent?.color }}>[SYSTEM]</span> Agent {selectedAgent?.name} initialized.</div>
                      <div style={{ color: 'var(--text-muted)' }}>[00:00.45] <span style={{ color: selectedAgent?.color }}>[MEMORY]</span> Loaded {selectedAgent?.memory} vector embeddings.</div>
                      <div style={{ color: 'var(--text-muted)' }}>[00:01.12] <span style={{ color: selectedAgent?.color }}>[TASK]</span> Awaiting instructions from Orchestrator...</div>
                      <div style={{ color: 'var(--text-muted)' }}>[00:05.33] <span style={{ color: selectedAgent?.color }}>[EXECUTE]</span> Processing background queue payload.</div>
                      <div style={{ color: 'var(--text-muted)' }}>[00:05.89] <span style={{ color: 'var(--success)' }}>[SUCCESS]</span> Payload resolved. Return code 0.</div>
                    </div>
                 ) : (
                    <div style={{ color: 'var(--text-main)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                       <div>
                          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>Agent Capability Profile</div>
                          <select className="setting-select" style={{ width: '100%', background: 'rgba(0,0,0,0.4)' }}>
                             <option>Default (Balanced)</option>
                             <option>High Performance (Max Compute)</option>
                             <option>Eco Mode (Low Priority)</option>
                          </select>
                       </div>
                       <div>
                          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>Memory Access Level</div>
                          <select className="setting-select" style={{ width: '100%', background: 'rgba(0,0,0,0.4)' }}>
                             <option>Read/Write (Full Access)</option>
                             <option>Read Only</option>
                             <option>Isolated Sandbox</option>
                          </select>
                       </div>
                       <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '8px' }}>
                          <label className="toggle-switch">
                             <input type="checkbox" defaultChecked />
                             <span className="toggle-slider"></span>
                          </label>
                          <span style={{ fontSize: '13px' }}>Allow Inter-Agent Communication</span>
                       </div>
                       <div style={{ marginTop: '16px' }}>
                          <button className="agent-btn primary" onClick={closeModal} style={{ width: '100%', background: `${selectedAgent?.color}20`, color: selectedAgent?.color }}>Save Configuration</button>
                       </div>
                    </div>
                 )}
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
