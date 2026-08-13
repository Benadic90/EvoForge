import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000/api';

const LearningView = () => {
  const [research, setResearch] = useState([]);
  const [skills, setSkills] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [benchmarks, setBenchmarks] = useState([]);
  const [proposals, setProposals] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/learning/research`).then(res => res.json()).then(setResearch).catch(console.error);
    fetch(`${API_BASE}/learning/skills`).then(res => res.json()).then(setSkills).catch(console.error);
    fetch(`${API_BASE}/learning/gaps`).then(res => res.json()).then(setGaps).catch(console.error);
    fetch(`${API_BASE}/learning/benchmarks`).then(res => res.json()).then(setBenchmarks).catch(console.error);
    fetch(`${API_BASE}/evolution/proposals`).then(res => res.json()).then(setProposals).catch(console.error);
  }, []);

  return (
    <div style={{ padding: '2rem', color: '#e5e7eb' }}>
      <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '1.5rem', borderBottom: '1px solid #374151', paddingBottom: '0.5rem' }}>Continuous Learning & Skill Evolution</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        
        {/* Research Jobs */}
        <div style={{ backgroundColor: '#1f2937', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #374151' }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#60a5fa' }}>Research Jobs</h2>
          {research.length === 0 ? <p>No active research jobs.</p> : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {research.map(r => (
                <li key={r.research_id} style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#374151', borderRadius: '0.25rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <strong>{r.topic}</strong>
                    <span style={{ padding: '0.25rem 0.5rem', backgroundColor: r.status === 'COMPLETED' ? '#065f46' : '#b45309', borderRadius: '0.25rem', fontSize: '0.8rem' }}>{r.status}</span>
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#9ca3af' }}>Agent: {r.agent_id} | Priority: {r.priority}</div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Skill Gaps */}
        <div style={{ backgroundColor: '#1f2937', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #374151' }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#f87171' }}>Identified Skill Gaps</h2>
          {gaps.length === 0 ? <p>No active skill gaps.</p> : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {gaps.map(g => (
                <li key={g.skill_gap_id} style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#374151', borderRadius: '0.25rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <strong>{g.skill_id}</strong>
                    <span style={{ padding: '0.25rem 0.5rem', backgroundColor: '#7f1d1d', borderRadius: '0.25rem', fontSize: '0.8rem' }}>{g.severity}</span>
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#9ca3af' }}>Status: {g.status} | Confidence: {g.confidence.toFixed(2)}</div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Benchmarks */}
        <div style={{ backgroundColor: '#1f2937', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #374151' }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#34d399' }}>Benchmark Runs</h2>
          {benchmarks.length === 0 ? <p>No benchmarks recorded.</p> : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {benchmarks.map(b => (
                <li key={b.benchmark_id} style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#374151', borderRadius: '0.25rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <strong>{b.skill_id}</strong>
                    <span style={{ color: b.candidate_score >= b.baseline_score ? '#34d399' : '#f87171' }}>
                      {b.candidate_score.toFixed(2)} (Base: {b.baseline_score.toFixed(2)})
                    </span>
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#9ca3af' }}>Agent: {b.agent_id} | Env: {b.environment}</div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Proposals */}
        <div style={{ backgroundColor: '#1f2937', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #374151' }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem', color: '#c084fc' }}>Evolution Proposals</h2>
          {proposals.length === 0 ? <p>No proposals available.</p> : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {proposals.map(p => (
                <li key={p.proposal_id} style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#374151', borderRadius: '0.25rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <strong>{p.target}</strong>
                    <span style={{ padding: '0.25rem 0.5rem', backgroundColor: '#4c1d95', borderRadius: '0.25rem', fontSize: '0.8rem' }}>{p.status}</span>
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#9ca3af' }}>Type: {p.change_type} | Risk: {p.risk}</div>
                  <p style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>{p.description}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default LearningView;
