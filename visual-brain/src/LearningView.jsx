import React, { useEffect, useState } from 'react';
import { api } from './api/client';
import { BookOpen, Search, Target, CheckCircle, Database } from 'lucide-react';

export default function LearningView() {
  const [research, setResearch] = useState([]);
  const [skills, setSkills] = useState([]);
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLearning = async () => {
      try {
        const [rRes, sRes, gRes] = await Promise.all([
          api.getResearch(),
          api.getSkills(),
          api.getSkillGaps()
        ]);
        setResearch(rRes || []);
        setSkills(sRes || []);
        setGaps(gRes || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchLearning();
  }, []);

  if (loading) {
    return <div className="p-8 text-[var(--text-muted)] text-center">Loading Learning & Skills...</div>;
  }

  return (
    <div className="p-8 fade-in">
      <h1 style={{ fontSize: '24px', margin: '0 0 24px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <BookOpen size={24} />
        Continuous Learning & Skills
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '18px', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}><CheckCircle size={18} /> Acquired Skills</h2>
          {skills.length === 0 ? (
            <div style={{ color: 'var(--text-muted)' }}>No skills documented yet.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {skills.map(s => (
                <div key={s.skill_id} style={{ background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <strong style={{ fontSize: '15px' }}>{s.skill_id}</strong>
                    <span style={{ fontSize: '11px', color: '#00ffaa' }}>{(s.confidence * 100).toFixed(0)}% Confidence</span>
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{s.description}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '8px' }}>Based on {s.evidence_count} evidence points.</div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '18px', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}><Target size={18} /> Identified Gaps</h2>
            {gaps.length === 0 ? (
              <div style={{ color: 'var(--text-muted)' }}>No skill gaps identified.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {gaps.map(g => (
                  <div key={g.gap_id} style={{ background: 'rgba(255,170,0,0.1)', border: '1px solid rgba(255,170,0,0.2)', padding: '12px', borderRadius: '8px' }}>
                    <strong style={{ color: '#ffaa00', fontSize: '14px', display: 'block', marginBottom: '4px' }}>{g.topic}</strong>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{g.reason}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="glass-panel" style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '18px', margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}><Search size={18} /> Active Research</h2>
            {research.length === 0 ? (
              <div style={{ color: 'var(--text-muted)' }}>No active research jobs.</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {research.map(r => (
                  <div key={r.job_id} style={{ background: 'rgba(0,240,255,0.05)', border: '1px solid rgba(0,240,255,0.1)', padding: '12px', borderRadius: '8px' }}>
                    <strong style={{ color: '#00f0ff', fontSize: '14px', display: 'block', marginBottom: '4px' }}>{r.topic}</strong>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Status: {r.status}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
