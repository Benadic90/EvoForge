import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import { Network, CheckCircle, XCircle } from 'lucide-react';

export default function RoutingDetails() {
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDecisions = async () => {
      try {
        const data = await api.getRecentRouting();
        setDecisions(data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDecisions();
  }, []);

  if (loading) {
    return <div className="p-8 text-[var(--text-muted)] text-center">Loading Routing History...</div>;
  }

  return (
    <div className="p-8 fade-in">
      <h1 style={{ fontSize: '24px', margin: '0 0 24px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Network size={24} />
        Recent Routing Decisions
      </h1>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {decisions.map((decision) => (
          <div key={decision.task_id} className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '16px' }}>Task: {decision.task_id}</h3>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Workflow: {decision.workflow_id || 'N/A'}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#00ffaa' }}>Selected: {decision.selected_executor}</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{new Date(decision.timestamp).toLocaleString()}</div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '24px', fontSize: '13px' }}>
              <div style={{ flex: 1, background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px' }}>
                <div style={{ marginBottom: '8px', color: 'var(--text-muted)', fontWeight: 'bold' }}>Candidates Evaluated</div>
                <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {decision.candidates_evaluated.map(c => (
                    <li key={c} style={{ color: 'var(--text-primary)' }}>
                      {c === decision.selected_executor ? <strong>{c}</strong> : c}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div style={{ flex: 1, background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px' }}>
                <div style={{ marginBottom: '8px', color: 'var(--text-muted)', fontWeight: 'bold' }}>Rejections</div>
                {decision.rejection_reasons && Object.keys(decision.rejection_reasons).length > 0 ? (
                  <ul style={{ margin: 0, paddingLeft: '16px', display: 'flex', flexDirection: 'column', gap: '8px', color: '#ff3366' }}>
                    {Object.entries(decision.rejection_reasons).map(([candidate, reason]) => (
                      <li key={candidate}><strong>{candidate}:</strong> {reason}</li>
                    ))}
                  </ul>
                ) : (
                  <div style={{ color: 'var(--text-muted)' }}>No rejections.</div>
                )}
              </div>
            </div>

            {decision.explanation && (
              <div style={{ marginTop: '16px', fontSize: '13px', background: 'rgba(0,240,255,0.05)', padding: '16px', borderRadius: '8px', borderLeft: '3px solid #00f0ff' }}>
                <div style={{ marginBottom: '4px', color: '#00f0ff', fontWeight: 'bold' }}>Reasoning</div>
                <div style={{ color: 'var(--text-muted)' }}>{decision.explanation}</div>
              </div>
            )}
          </div>
        ))}
        
        {decisions.length === 0 && (
          <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No recent routing decisions.
          </div>
        )}
      </div>
    </div>
  );
}
