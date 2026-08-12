import { useState, useEffect } from 'react';
import { Search, Filter, Settings2, Bell, UserCircle2, Loader2 } from 'lucide-react';
import Sidebar from './Sidebar';
import KnowledgeGraph from './KnowledgeGraph';
import MetricsWidget from './MetricsWidget';
import WorkflowFeed from './WorkflowFeed';
import AgentHub from './AgentHub';
import NetworkView from './NetworkView';
import KnowledgeBase from './KnowledgeBase';
import Deployments from './Deployments';
import Settings from './Settings';

export default function App() {
  const [activeTab, setActiveTab] = useState('settings');
  const [graphData, setGraphData] = useState(null);
  const [metrics, setMetrics] = useState({
    developer_skill_increase: '+18%',
    developer_points: 74.2,
    security_detection_rate: '98.4%',
    total_agents: 5
  });

  const workflows = [
    { name: 'Dev Pipeline 01', time: '1 min ago', status: 'running' },
    { name: 'Security Audit', time: '5 min ago', status: 'success' },
    { name: 'Auto Deployment', time: '12 min ago', status: 'success' },
  ];

  useEffect(() => {
    fetch('http://localhost:8000/api/graph/knowledge')
      .then(res => res.json())
      .then(data => setGraphData(data))
      .catch(err => console.error("Error fetching graph data", err));

    fetch('http://localhost:8000/api/agents/metrics')
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(err => console.error("Error fetching metrics", err));
  }, []);

  const renderContent = () => {
    if (activeTab === 'dashboard') {
      return (
        <>
          <h1 className="dashboard-title">Knowledge Graph Visualization: AI Agent Memories</h1>
          <div className="dashboard-grid">
            <div className="graph-container">
              <div style={{ position: 'absolute', top: 20, left: 20, right: 20, zIndex: 10, display: 'flex', gap: '12px' }}>
                 <div className="search-bar" style={{ width: '100%', maxWidth: '300px', background: 'rgba(255,255,255,0.02)' }}>
                    <Search size={14} color="var(--text-muted)" />
                    <input type="text" placeholder="Search knowledge..." />
                 </div>
                 <div className="search-bar" style={{ width: 'auto', background: 'rgba(255,255,255,0.02)', gap: '6px', cursor: 'pointer' }}>
                    <Filter size={14} color="var(--text-muted)" />
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Filters</span>
                 </div>
                 <div className="search-bar" style={{ width: 'auto', background: 'rgba(255,255,255,0.02)', gap: '6px', cursor: 'pointer', marginLeft: 'auto' }}>
                    <Settings2 size={14} color="var(--text-muted)" />
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Display Settings</span>
                 </div>
              </div>
              <KnowledgeGraph data={graphData} />
            </div>
            
            <div className="right-panel">
              <MetricsWidget 
                title="Developer Agent Skill Level" 
                type="donut"
                value={metrics.developer_skill_increase}
                description={`Progressing +3.1 pts`}
                subtext="last commit: 3m ago"
              />
              
              <MetricsWidget 
                title="Security Agent Detection Rate" 
                type="sparkline"
                value={metrics.security_detection_rate} 
                description="0 vulnerabilities detected"
                subtext="real-time scanning"
              />
              
              <WorkflowFeed workflows={workflows} />
            </div>
          </div>
        </>
      );
    }
    
    if (activeTab === 'agents') {
      return <AgentHub />;
    }
    
    if (activeTab === 'network') {
      return <NetworkView />;
    }
    
    if (activeTab === 'knowledge') {
      return <KnowledgeBase />;
    }
    
    if (activeTab === 'deployments') {
      return <Deployments />;
    }
    
    if (activeTab === 'settings') {
      return <Settings />;
    }
    
    return null;
  };

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="main-content">
        <header className="header">
          <div className="header-left">
            <span>Project: <span className="highlight">Autonomous Dev (active)</span></span>
            <span>System Status: <span className="highlight">Optimal</span></span>
          </div>
          
          {/* Header right intentionally left empty as requested */}
        </header>
        
        {renderContent()}
      </main>
    </div>
  );
}
