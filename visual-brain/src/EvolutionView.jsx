import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import { Rocket, GitMerge, XCircle, CheckCircle, Search } from 'lucide-react';

export default function EvolutionView() {
  const [proposals, setProposals] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [pRes, eRes] = await Promise.all([
        api.getProposals(),
        api.getExperiments()
      ]);
      setProposals(pRes || []);
      setExperiments(eRes || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleApprove = async (id) => {
    try {
      await api.approveProposal(id);
      fetchData();
    } catch (err) {
      alert("Failed to approve: " + err.message);
    }
  };

  const handleReject = async (id) => {
    try {
      await api.rejectProposal(id);
      fetchData();
    } catch (err) {
      alert("Failed to reject: " + err.message);
    }
  };

  if (loading) {
    return <div className="p-8 text-[var(--text-muted)] text-center">Loading Evolution & Testing...</div>;
  }

  return (
    <div className="p-8 fade-in">
      <h1 style={{ fontSize: '24px', margin: '0 0 24px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Rocket size={24} />
        Evolution & Testing
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '18px', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <GitMerge size={18} /> Pending Proposals
          </h2>
          {proposals.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No evolution proposals pending.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {proposals.map(p => (
                <div key={p.proposal_id} style={{ padding: '20px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', borderLeft: '3px solid #00f0ff' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <h3 style={{ margin: 0, fontSize: '16px' }}>{p.title}</h3>
                    <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '4px' }}>{p.status}</span>
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>{p.description}</div>
                  
                  {p.status === 'PENDING_APPROVAL' && (
                    <div style={{ display: 'flex', gap: '12px' }}>
                      <button onClick={() => handleApprove(p.proposal_id)} style={{ background: 'rgba(0, 255, 170, 0.1)', border: '1px solid rgba(0, 255, 170, 0.2)', color: '#00ffaa', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <CheckCircle size={14} /> Approve
                      </button>
                      <button onClick={() => handleReject(p.proposal_id)} style={{ background: 'rgba(255, 51, 102, 0.1)', border: '1px solid rgba(255, 51, 102, 0.2)', color: '#ff3366', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <XCircle size={14} /> Reject
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '18px', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Search size={18} /> Recent Experiments
          </h2>
          {experiments.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>No recent experiments.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {experiments.map(e => (
                <div key={e.experiment_id} style={{ padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
                  <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '4px', color: e.passed ? '#00ffaa' : '#ff3366' }}>
                    {e.name}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Score: {e.score}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
