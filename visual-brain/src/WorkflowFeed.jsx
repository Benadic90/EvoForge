import { MoreHorizontal } from 'lucide-react';

export default function WorkflowFeed({ workflows }) {
  return (
    <div className="glass-panel widget" style={{ flex: 1, minHeight: 0 }}>
      <div className="widget-header">
         <h3>Live System Workflows</h3>
         <MoreHorizontal size={16} color="var(--text-muted)" style={{ cursor: 'pointer' }} />
      </div>
      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '-8px' }}>active pipelines</div>
      
      <div style={{ overflowY: 'hidden', flex: 1, marginTop: '8px', paddingRight: '8px' }}>
        {workflows.map((wf, idx) => (
          <div key={idx} className="workflow-item">
            <div className="timeline">
               <div className={`timeline-dot ${wf.status}`}></div>
               {idx !== workflows.length - 1 && <div className="timeline-line"></div>}
            </div>
            
            <div className="workflow-details">
              <div>
                <div className="workflow-title">{wf.name}</div>
                <div className="workflow-meta">{wf.time}</div>
              </div>
              <div className={`workflow-badge ${wf.status}`}>
                {wf.status === 'running' ? 'RUNNING' : 'SUCCESS'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
