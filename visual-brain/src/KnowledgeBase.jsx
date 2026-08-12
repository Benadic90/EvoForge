import { Search, Database, HardDrive, Share2, Eye, Server } from 'lucide-react';

export default function KnowledgeBase() {
  const memories = [
    { id: 'vec_8x4a', type: 'Code Context', source: 'DevAgent', content: 'Parsed authentication flow architecture from src/auth/', time: '2m ago' },
    { id: 'vec_9m21', type: 'Security Sig', source: 'Security Sentinel', content: 'Identified potential race condition in threaded execution block', time: '15m ago' },
    { id: 'vec_1p0x', type: 'System Log', source: 'Orchestrator', content: 'User requested visual dashboard layout generation', time: '1h ago' },
    { id: 'vec_4c99', type: 'Code Context', source: 'DevAgent', content: 'Cached state management component structures in React', time: '2h ago' },
    { id: 'vec_7j3k', type: 'System Log', source: 'Orchestrator', content: 'Evolution Agent leveled up code synthesis capabilities', time: '4h ago' },
  ];

  return (
    <div style={{ padding: '0 12px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h1 className="dashboard-title" style={{ marginBottom: '24px' }}>Knowledge Base: Semantic Memory</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '24px', flex: 1, minHeight: 0 }}>
        
        {/* Left Column - Memory Stream */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
           <div style={{ padding: '20px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 500, color: 'var(--text-main)' }}>Vector Embeddings Stream</h3>
              <div className="search-bar" style={{ width: '200px' }}>
                <Search size={14} color="var(--text-muted)" />
                <input type="text" placeholder="Query memories..." />
              </div>
           </div>
           
           <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {memories.map((mem) => (
                <div key={mem.id} className="memory-card">
                  <div className="memory-header">
                     <span className="memory-id">{mem.id}</span>
                     <span className="memory-time">{mem.time}</span>
                  </div>
                  <div className="memory-content">{mem.content}</div>
                  <div className="memory-footer">
                     <span className={`memory-badge ${mem.type === 'Security Sig' ? 'security' : mem.type === 'Code Context' ? 'dev' : 'system'}`}>
                        {mem.type}
                     </span>
                     <span className="memory-source"><Share2 size={10} style={{ marginRight: 4 }}/> {mem.source}</span>
                  </div>
                </div>
              ))}
           </div>
        </div>

        {/* Right Column - Stats */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
           <div className="glass-panel widget" style={{ flex: 1 }}>
              <div className="widget-header" style={{ marginBottom: '16px' }}>
                 <h3>Storage Status</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                 <div className="storage-stat">
                    <Database size={18} color="var(--accent-cyan)" />
                    <div>
                       <div className="storage-val">14,204</div>
                       <div className="storage-label">Total Vectors</div>
                    </div>
                 </div>
                 <div className="storage-stat">
                    <HardDrive size={18} color="var(--accent-purple)" />
                    <div>
                       <div className="storage-val">1.2 GB</div>
                       <div className="storage-label">SQLite Size</div>
                    </div>
                 </div>
                 <div className="storage-stat">
                    <Server size={18} color="var(--success)" />
                    <div>
                       <div className="storage-val">99.8%</div>
                       <div className="storage-label">Index Health</div>
                    </div>
                 </div>
              </div>
           </div>
           
           <div className="glass-panel widget" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', inset: 0, opacity: 0.1, backgroundImage: 'radial-gradient(circle at center, var(--accent-cyan) 0%, transparent 70%)' }}></div>
              <div style={{ textAlign: 'center', zIndex: 1 }}>
                 <Eye size={32} color="var(--accent-cyan)" style={{ marginBottom: '12px', filter: 'drop-shadow(0 0 10px var(--accent-cyan))', margin: '0 auto' }}/>
                 <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-main)', marginTop: '12px' }}>Live Observation</div>
                 <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>Agents are currently indexing<br/>the workspace.</div>
              </div>
           </div>
        </div>

      </div>
    </div>
  );
}
