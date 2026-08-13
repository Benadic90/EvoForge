import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import { Layers, Shield, Activity, ListTodo, AlertTriangle } from 'lucide-react';

export default function PortfolioView() {
  const [projects, setProjects] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPortfolio = async () => {
      try {
        const [projRes, healthRes] = await Promise.all([
          api.getProjects(),
          api.getPortfolioHealth()
        ]);
        setProjects(projRes || []);
        setHealth(healthRes || null);
      } catch (err) {
        console.error("Failed to load portfolio:", err);
      } finally {
        setLoading(false);
      }
    };
    
    loadPortfolio();
  }, []);

  if (loading) {
    return <div className="p-8 text-[var(--text-muted)] text-center">Loading Portfolio...</div>;
  }

  return (
    <div className="p-8 fade-in">
      <h1 style={{ fontSize: '24px', margin: '0 0 24px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Layers size={24} />
        Project Portfolio Intelligence
      </h1>

      {health && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}><Activity size={14}/> Health Score</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: health.score > 80 ? '#00ffaa' : '#ffaa00' }}>
              {health.score}/100
            </div>
          </div>
          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}><Shield size={14}/> Security Posture</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
              {health.security_posture}
            </div>
          </div>
          <div className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '13px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}><ListTodo size={14}/> Critical Tasks</div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: health.critical_tasks > 0 ? '#ff3366' : '#00ffaa' }}>
              {health.critical_tasks}
            </div>
          </div>
        </div>
      )}

      <h2 style={{ fontSize: '18px', margin: '0 0 16px 0' }}>Managed Projects</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
        {projects.map(proj => (
          <div key={proj.project_id} className="glass-panel" style={{ padding: '24px', cursor: 'pointer', transition: 'all 0.2s' }} 
               onClick={() => alert(`Project details for ${proj.project_id} would open here.`)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <h3 style={{ margin: 0, fontSize: '18px' }}>{proj.project_id}</h3>
              <span style={{ 
                fontSize: '11px', padding: '2px 8px', borderRadius: '4px',
                background: proj.status === 'MANAGED' ? 'rgba(0, 240, 255, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                color: proj.status === 'MANAGED' ? '#00f0ff' : 'var(--text-muted)'
              }}>
                {proj.status}
              </span>
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              {proj.vision || 'No vision defined.'}
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <div><strong>Priority:</strong> {proj.priority}</div>
              <div><strong>Confidence:</strong> {(proj.confidence_score * 100).toFixed(0)}%</div>
            </div>
          </div>
        ))}
        {projects.length === 0 && (
          <div className="glass-panel" style={{ gridColumn: '1 / -1', padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No projects registered in the portfolio.
          </div>
        )}
      </div>
    </div>
  );
}
