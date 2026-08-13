import React, { useState } from 'react';
import { ListTree, Search, Filter } from 'lucide-react';

export default function EventStream({ realTimeState }) {
  const { events, loading } = realTimeState;
  const [filter, setFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  if (loading) {
    return <div className="p-8 text-[var(--text-muted)] text-center">Loading Event Stream...</div>;
  }

  const filteredEvents = events.filter(e => {
    if (filter !== 'ALL' && e.severity !== filter && !e.event_type.startsWith(filter.toLowerCase())) {
      return false;
    }
    if (searchTerm) {
      const s = searchTerm.toLowerCase();
      if (!e.event_type.toLowerCase().includes(s) && !e.details?.toLowerCase().includes(s)) {
        return false;
      }
    }
    return true;
  });

  return (
    <div className="p-8 fade-in" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ListTree size={24} />
          System Timeline
        </h1>
        
        <div style={{ display: 'flex', gap: '16px' }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input 
              type="text" 
              placeholder="Search events..." 
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                padding: '8px 16px 8px 36px',
                borderRadius: '6px',
                color: 'white',
                fontSize: '13px',
                width: '250px'
              }}
            />
          </div>
          
          <select 
            value={filter} 
            onChange={e => setFilter(e.target.value)}
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              padding: '8px 16px',
              borderRadius: '6px',
              color: 'white',
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Events</option>
            <option value="ERROR">Errors</option>
            <option value="WARNING">Warnings</option>
            <option value="WORKFLOW">Workflows</option>
            <option value="ROUTING">Routing</option>
          </select>
        </div>
      </div>

      <div className="glass-panel" style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
        {filteredEvents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
            No events match the current filters.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {filteredEvents.map((event, idx) => (
              <div key={idx} style={{
                display: 'flex', gap: '24px', padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px',
                borderLeft: `4px solid ${
                  event.severity === 'ERROR' ? '#ff3366' : 
                  event.severity === 'WARNING' ? '#ffaa00' : 
                  event.event_type.startsWith('workflow') ? '#00f0ff' : '#00ffaa'
                }`
              }}>
                <div style={{ width: '80px', flexShrink: 0, fontSize: '12px', color: 'var(--text-muted)', paddingTop: '2px' }}>
                  {new Date(event.timestamp).toLocaleTimeString()}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 'bold', fontSize: '14px' }}>{event.event_type}</span>
                    {event.severity !== 'INFO' && (
                      <span style={{ 
                        fontSize: '10px', padding: '2px 6px', borderRadius: '4px',
                        background: event.severity === 'ERROR' ? 'rgba(255,51,102,0.1)' : 'rgba(255,170,0,0.1)',
                        color: event.severity === 'ERROR' ? '#ff3366' : '#ffaa00'
                      }}>
                        {event.severity}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    {event.details}
                  </div>
                  {(event.project_id || event.worker_id || event.executor_id) && (
                    <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                      {event.project_id && <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.05)', padding: '4px 8px', borderRadius: '4px' }}>Project: {event.project_id}</span>}
                      {event.worker_id && <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.05)', padding: '4px 8px', borderRadius: '4px' }}>Worker: {event.worker_id}</span>}
                      {event.executor_id && <span style={{ fontSize: '11px', background: 'rgba(255,255,255,0.05)', padding: '4px 8px', borderRadius: '4px' }}>Executor: {event.executor_id}</span>}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
