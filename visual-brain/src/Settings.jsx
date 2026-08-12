import { Sliders, Shield, Zap, Key, Save, RotateCcw } from 'lucide-react';

export default function Settings() {
  return (
    <div style={{ padding: '0 12px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
         <h1 className="dashboard-title" style={{ margin: 0 }}>System Settings: Core Configuration</h1>
         <div style={{ display: 'flex', gap: '12px' }}>
            <button className="agent-btn secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', flex: 'none' }}><RotateCcw size={14}/> Reset Defaults</button>
            <button className="agent-btn primary" style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', background: 'rgba(0, 240, 255, 0.15)', color: 'var(--accent-cyan)', flex: 'none' }}><Save size={14}/> Save Changes</button>
         </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', flex: 1, overflowY: 'auto', paddingRight: '8px', minHeight: 0 }}>
         
         {/* Column 1 */}
         <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            <div className="glass-panel" style={{ padding: '24px' }}>
               <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 0, marginBottom: '20px', color: 'var(--text-main)', fontSize: '15px' }}><Zap size={18} color="var(--accent-cyan)"/> Orchestrator Engine</h3>
               
               <div className="setting-row">
                  <div className="setting-info">
                     <div className="setting-name">Primary LLM Provider</div>
                     <div className="setting-desc">The model used for reasoning and code synthesis.</div>
                  </div>
                  <select className="setting-select">
                     <option>NVIDIA NIM (Free)</option>
                     <option>Google Gemini 3.1 Pro</option>
                     <option>Ollama (Local LLM)</option>
                  </select>
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

            <div className="glass-panel" style={{ padding: '24px' }}>
               <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 0, marginBottom: '20px', color: 'var(--text-main)', fontSize: '15px' }}><Key size={18} color="var(--accent-purple)"/> API Credentials</h3>
               
               <div className="setting-row">
                  <div className="setting-info">
                     <div className="setting-name">NVIDIA API Key</div>
                  </div>
                  <input type="password" className="setting-input" placeholder="nvapi-..." style={{ width: '200px' }} />
               </div>
               
               <div className="setting-row">
                  <div className="setting-info">
                     <div className="setting-name">Gemini API Key</div>
                  </div>
                  <input type="password" className="setting-input" placeholder="AIza..." style={{ width: '200px' }} />
               </div>
               
               <div className="setting-row" style={{ borderBottom: 'none', paddingBottom: 0 }}>
                  <div className="setting-info">
                     <div className="setting-name">Ollama Base URL</div>
                  </div>
                  <input type="text" className="setting-input" defaultValue="http://localhost:11434" style={{ width: '200px' }} />
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
               
               <div className="setting-row">
                  <div className="setting-info">
                     <div className="setting-name">Auto-Resolve Lints</div>
                     <div className="setting-desc">Allow DevAgent to automatically fix linter errors.</div>
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
               <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 0, marginBottom: '20px', color: 'var(--text-main)', fontSize: '15px' }}><Sliders size={18} color="#ff3366"/> Dashboard Preferences</h3>
               
               <div className="setting-row">
                  <div className="setting-info">
                     <div className="setting-name">Live Animations</div>
                     <div className="setting-desc">Enable particle effects and glowing pulses.</div>
                  </div>
                  <label className="toggle-switch">
                     <input type="checkbox" defaultChecked />
                     <span className="toggle-slider"></span>
                  </label>
               </div>
               
               <div className="setting-row" style={{ borderBottom: 'none', paddingBottom: 0 }}>
                  <div className="setting-info">
                     <div className="setting-name">Refresh Rate</div>
                     <div className="setting-desc">How often the dashboard polls for API updates.</div>
                  </div>
                  <select className="setting-select">
                     <option>Real-time (WebSocket)</option>
                     <option>Every 5 seconds</option>
                     <option>Every 30 seconds</option>
                  </select>
               </div>
            </div>

         </div>

      </div>
    </div>
  );
}
