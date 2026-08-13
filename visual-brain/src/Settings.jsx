import { Sliders, Shield, Zap, Key, Save, RotateCcw, Cpu } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function Settings() {
  const [computePolicy, setComputePolicy] = useState({
    mode: 'HYBRID',
    allow_local: true,
    allow_cloud: true,
    prefer_local: false,
    ollama_enabled: true,
    ollama_status: 'UNKNOWN'
  });

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch('/api/settings/compute')
      .then(res => res.json())
      .then(data => setComputePolicy(data))
      .catch(err => console.error('Failed to load compute policy:', err));
  }, []);

  const saveSettings = async () => {
    setSaving(true);
    try {
      const res = await fetch('/api/settings/compute', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(computePolicy)
      });
      const updated = await res.json();
      setComputePolicy(updated);
    } catch (err) {
      console.error('Failed to save settings:', err);
    }
    setSaving(false);
  };

  return (
    <div style={{ padding: '0 12px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
         <h1 className="dashboard-title" style={{ margin: 0 }}>System Settings: Core Configuration</h1>
         <div style={{ display: 'flex', gap: '12px' }}>
            <button className="agent-btn secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', flex: 'none' }}><RotateCcw size={14}/> Reset Defaults</button>
            <button onClick={saveSettings} disabled={saving} className="agent-btn primary" style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', background: 'rgba(0, 240, 255, 0.15)', color: 'var(--accent-cyan)', flex: 'none', opacity: saving ? 0.5 : 1 }}>
               <Save size={14}/> {saving ? 'Saving...' : 'Save Changes'}
            </button>
         </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', flex: 1, overflowY: 'auto', paddingRight: '8px', minHeight: 0 }}>
         
         {/* Column 1 */}
         <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            <div className="glass-panel" style={{ padding: '24px' }}>
               <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 0, marginBottom: '20px', color: 'var(--text-main)', fontSize: '15px' }}><Cpu size={18} color="var(--accent-cyan)"/> Execution Mode (Compute)</h3>
               
               <div className="setting-row">
                  <div className="setting-info">
                     <div className="setting-name">Compute Mode</div>
                     <div className="setting-desc">LOCAL excludes cloud. CLOUD excludes local. HYBRID uses both.</div>
                  </div>
                  <select 
                     className="setting-select"
                     value={computePolicy.mode}
                     onChange={(e) => setComputePolicy({ ...computePolicy, mode: e.target.value })}
                  >
                     <option value="LOCAL">Local</option>
                     <option value="CLOUD">Cloud</option>
                     <option value="HYBRID">Hybrid</option>
                  </select>
               </div>
               
               <div className="setting-row">
                  <div className="setting-info">
                     <div className="setting-name">Prefer Local Models</div>
                     <div className="setting-desc">Prioritize local Ollama execution over Cloud if available.</div>
                  </div>
                  <label className="toggle-switch">
                     <input 
                       type="checkbox" 
                       checked={computePolicy.prefer_local} 
                       onChange={(e) => setComputePolicy({ ...computePolicy, prefer_local: e.target.checked })} 
                     />
                     <span className="toggle-slider"></span>
                  </label>
               </div>
               
               <div className="setting-row" style={{ borderBottom: 'none', paddingBottom: 0 }}>
                  <div className="setting-info">
                     <div className="setting-name">Allow Cloud Fallback</div>
                     <div className="setting-desc">If HYBRID/CLOUD is active, allows failover to cloud.</div>
                  </div>
                  <label className="toggle-switch">
                     <input 
                        type="checkbox" 
                        checked={computePolicy.allow_cloud}
                        onChange={(e) => setComputePolicy({ ...computePolicy, allow_cloud: e.target.checked })}
                     />
                     <span className="toggle-slider"></span>
                  </label>
               </div>
            </div>

            <div className="glass-panel" style={{ padding: '24px' }}>
               <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 0, marginBottom: '20px', color: 'var(--text-main)', fontSize: '15px' }}><Zap size={18} color="var(--accent-cyan)"/> Orchestrator Engine</h3>
               
               <div className="setting-row">
                  <div className="setting-info">
                     <div className="setting-name">Ollama Status</div>
                     <div className="setting-desc">Live health check of local execution layer.</div>
                  </div>
                  <div style={{ color: computePolicy.ollama_status === 'AVAILABLE' ? 'var(--success)' : 'var(--danger)', fontWeight: 'bold' }}>
                     {computePolicy.ollama_status}
                  </div>
               </div>
               
               <div className="setting-row">
                  <div className="setting-info">
                     <div className="setting-name">Max Concurrency</div>
                     <div className="setting-desc">Number of agents allowed to run simultaneously.</div>
                  </div>
                  <input type="number" className="setting-input" defaultValue={5} min={1} max={20} style={{ width: '80px' }} />
               </div>
               
               <div className="setting-row" style={{ borderBottom: 'none', paddingBottom: 0 }}>
                  <div className="setting-info">
                     <div className="setting-name">Context Window (Tokens)</div>
                     <div className="setting-desc">Maximum context size passed to the agents.</div>
                  </div>
                  <select className="setting-select">
                     <option>128,000</option>
                     <option>200,000</option>
                     <option>1,000,000</option>
                  </select>
               </div>
            </div>

         </div>

         {/* Column 2 */}
         <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            <div className="glass-panel" style={{ padding: '24px' }}>
               <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 0, marginBottom: '20px', color: 'var(--text-main)', fontSize: '15px' }}><Shield size={18} color="var(--success)"/> Security & Policies</h3>
               
               <div className="setting-row">
                  <div className="setting-info">
                     <div className="setting-name">Require Human Approval</div>
                     <div className="setting-desc">Block destructive actions (e.g. DELETE) without review.</div>
                  </div>
                  <label className="toggle-switch">
                     <input type="checkbox" defaultChecked />
                     <span className="toggle-slider"></span>
                  </label>
               </div>
               
               <div className="setting-row" style={{ borderBottom: 'none', paddingBottom: 0 }}>
                  <div className="setting-info">
                     <div className="setting-name">Strict Mode Scanning</div>
                     <div className="setting-desc">Security Sentinel analyzes all dependencies on install.</div>
                  </div>
                  <label className="toggle-switch">
                     <input type="checkbox" />
                     <span className="toggle-slider"></span>
                  </label>
               </div>
            </div>

            <div className="glass-panel" style={{ padding: '24px' }}>
               <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 0, marginBottom: '20px', color: 'var(--text-main)', fontSize: '15px' }}><Key size={18} color="var(--accent-purple)"/> API Credentials</h3>
               
               <div className="setting-row">
                  <div className="setting-info">
                     <div className="setting-name">NVIDIA API Key</div>
                  </div>
                  <input type="password" className="setting-input" placeholder="nvapi-..." style={{ width: '200px' }} />
               </div>
               
               <div className="setting-row" style={{ borderBottom: 'none', paddingBottom: 0 }}>
                  <div className="setting-info">
                     <div className="setting-name">Gemini API Key</div>
                  </div>
                  <input type="password" className="setting-input" placeholder="AIza..." style={{ width: '200px' }} />
               </div>
            </div>

         </div>

      </div>
    </div>
  );
}
