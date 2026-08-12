import { MoreHorizontal } from 'lucide-react';

export default function MetricsWidget({ title, type, value, description, subtext }) {
  return (
    <div className="glass-panel widget">
      <div className="widget-header">
         <h3>{title}</h3>
         <MoreHorizontal size={16} color="var(--text-muted)" style={{ cursor: 'pointer' }} />
      </div>
      
      {type === 'donut' && (
        <div style={{ textAlign: 'center', marginTop: '8px' }}>
          <div className="donut-container">
            <div className="donut-inner">{value}</div>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-main)', marginTop: '8px' }}>{description}</div>
          {subtext && <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{subtext}</div>}
        </div>
      )}
      
      {type === 'sparkline' && (
        <div style={{ marginTop: '8px' }}>
          <div className="metric-value">{value}</div>
          <svg style={{ width: '100%', height: '35px', marginTop: '8px', overflow: 'visible' }} viewBox="0 0 280 60" preserveAspectRatio="none">
             <defs>
               <linearGradient id="sparklineGrad" x1="0" x2="0" y1="0" y2="1">
                 <stop offset="0%" stopColor="var(--accent-cyan-glow)" />
                 <stop offset="100%" stopColor="transparent" />
               </linearGradient>
             </defs>
             {/* Mock sparkline path */}
             <path d="M0 40 Q 20 20 40 30 T 80 10 T 120 40 T 160 20 T 200 35 T 240 10 T 280 15" 
                   fill="none" stroke="var(--accent-cyan)" strokeWidth="4" 
                   style={{ filter: 'drop-shadow(0 0 4px var(--accent-cyan))' }} />
             <path d="M0 40 Q 20 20 40 30 T 80 10 T 120 40 T 160 20 T 200 35 T 240 10 T 280 15 L 280 60 L 0 60 Z" 
                   fill="url(#sparklineGrad)" />
          </svg>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>{description}</div>
          {subtext && <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{subtext}</div>}
        </div>
      )}
      
      {!type && (
        <>
          <div className="metric-value">
            {value}
          </div>
          {description && <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{description}</div>}
          {subtext && <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{subtext}</div>}
        </>
      )}
    </div>
  );
}
