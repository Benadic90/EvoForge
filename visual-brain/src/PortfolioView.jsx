import React, { useState, useEffect } from 'react';
import { Layers, Activity, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

export default function PortfolioView() {
  const [projects, setProjects] = useState([]);
  const [health, setHealth] = useState(null);
  const [dailyPlan, setDailyPlan] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [projRes, healthRes, planRes] = await Promise.all([
          fetch('http://localhost:8000/api/projects').catch(() => null),
          fetch('http://localhost:8000/api/portfolio/health').catch(() => null),
          fetch('http://localhost:8000/api/portfolio/daily-plan').catch(() => null)
        ]);

        if (projRes?.ok) {
          const data = await projRes.json();
          setProjects(data);
        }
        if (healthRes?.ok) {
          const data = await healthRes.json();
          setHealth(data);
        }
        if (planRes?.ok) {
          const data = await planRes.json();
          setDailyPlan(data);
        }
      } catch (e) {
        console.error("Error fetching portfolio data", e);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const getHealthColor = (h) => {
    if (h === 'HEALTHY') return '#00ff9d';
    if (h === 'WARNING') return '#ffb300';
    if (h === 'CRITICAL') return '#ff3366';
    return '#8a9bb4';
  };

  const getHealthIcon = (h) => {
    if (h === 'HEALTHY') return <CheckCircle size={16} color="#00ff9d" />;
    if (h === 'WARNING') return <AlertTriangle size={16} color="#ffb300" />;
    if (h === 'CRITICAL') return <AlertTriangle size={16} color="#ff3366" />;
    return <Clock size={16} color="#8a9bb4" />;
  };

  if (loading) {
    return (
      <div className="portfolio-view" style={{ padding: '20px', color: 'var(--text-muted)' }}>
        Loading portfolio intelligence...
      </div>
    );
  }

  return (
    <div className="portfolio-view" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto', maxHeight: 'calc(100vh - 100px)' }}>
      <h1 className="dashboard-title">Portfolio Intelligence</h1>

      {/* Health Overview */}
      <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px' }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '10px' }}>Total Projects</h3>
          <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{health?.total_projects || 0}</div>
        </div>
        <div className="glass-panel" style={{ padding: '20px', borderTop: '3px solid #00ff9d' }}>
          <h3 style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '10px' }}>Healthy</h3>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#00ff9d' }}>{health?.healthy_projects || 0}</div>
        </div>
        <div className="glass-panel" style={{ padding: '20px', borderTop: '3px solid #ffb300' }}>
          <h3 style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '10px' }}>Warning</h3>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#ffb300' }}>{health?.warning_projects || 0}</div>
        </div>
        <div className="glass-panel" style={{ padding: '20px', borderTop: '3px solid #ff3366' }}>
          <h3 style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '10px' }}>Critical</h3>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#ff3366' }}>{health?.critical_projects || 0}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        {/* Project List */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={20} color="var(--primary)" /> Managed Projects
          </h2>
          
          {projects.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No projects registered. Use CLI `evoforge project-add` to register repositories.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {projects.map(p => (
                <div key={p.project_id} style={{ 
                  background: 'rgba(255,255,255,0.02)', 
                  padding: '15px', 
                  borderRadius: '8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderLeft: `3px solid ${getHealthColor(p.health)}`
                }}>
                  <div>
                    <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '4px' }}>{p.name}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{p.repository_full_name}</div>
                  </div>
                  <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', background: 'rgba(255,255,255,0.05)', padding: '4px 8px', borderRadius: '4px' }}>
                      {getHealthIcon(p.health)}
                      <span style={{ color: getHealthColor(p.health) }}>{p.health}</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Priority Score</span>
                      <span style={{ fontWeight: 'bold', color: 'var(--primary)' }}>{p.priority_score.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Daily Plan */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={20} color="var(--primary)" /> Today's Plan
          </h2>
          
          {!dailyPlan ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No daily plan generated yet.
            </div>
          ) : (
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '15px' }}>
                Plan ID: {dailyPlan.plan_id.split('_')[1]}
              </div>
              
              <div style={{ display: 'flex', gap: '15px', marginBottom: '20px' }}>
                <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--primary)' }}>{dailyPlan.selected_projects.length}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Projects</div>
                </div>
                <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px', textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#00ff9d' }}>{dailyPlan.selected_tasks.length}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Tasks</div>
                </div>
              </div>

              <h4 style={{ fontSize: '14px', marginBottom: '10px' }}>Execution Queue</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {dailyPlan.execution_order.length === 0 ? (
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No tasks scheduled.</div>
                ) : (
                  dailyPlan.execution_order.map((taskId, idx) => (
                    <div key={taskId} style={{ 
                      fontSize: '13px', 
                      padding: '8px 10px', 
                      background: 'rgba(255,255,255,0.03)', 
                      borderRadius: '4px',
                      display: 'flex',
                      gap: '10px'
                    }}>
                      <span style={{ color: 'var(--text-muted)' }}>{idx + 1}.</span>
                      <span style={{ fontFamily: 'monospace' }}>{taskId.split('_')[1]}</span>
                    </div>
                  ))
                )}
              </div>
              
              <div style={{ marginTop: '20px', paddingTop: '15px', borderTop: '1px solid rgba(255,255,255,0.1)', fontSize: '11px', color: 'var(--text-muted)' }}>
                Budget limits: {dailyPlan.budget.max_tasks} tasks maximum
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
