import { useState, useEffect } from 'react';
import { Search, Filter, Settings2 } from 'lucide-react';
import Sidebar from './Sidebar';
import KnowledgeGraph from './KnowledgeGraph';
import MetricsWidget from './MetricsWidget';
import WorkflowFeed from './WorkflowFeed';
import AgentHub from './AgentHub';
import NetworkView from './NetworkView';
import KnowledgeBase from './KnowledgeBase';
import Deployments from './Deployments';
import PortfolioView from './PortfolioView';
import Settings from './Settings';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [graphData, setGraphData] = useState(null);
  const [systemStatus, setSystemStatus] = useState({
    system_state: 'Optimal',
    active_workflows: 0,
    failed_workflows: 0,
    healthy_executors: 3,
    unhealthy_executors: 0
  });
  const [metrics, setMetrics] = useState({
    developer_skill_increase: '0 runs',
    developer_points: 0.0,
    security_detection_rate: 'N/A',
    router_accuracy: 'N/A',
    total_agents: 11
  });
  const [recentEvents, setRecentEvents] = useState([]);

  useEffect(() => {
    const fetchAllData = () => {
      // 1. System Status
      fetch('http://localhost:8000/api/status')
        .then(res => res.json())
        .then(data => setSystemStatus(data))
        .catch(err => console.error("Error fetching status", err));

      // 2. Knowledge Graph
      fetch('http://localhost:8000/api/graph/knowledge')
        .then(res => res.json())
        .then(data => setGraphData(data))
        .catch(err => console.error("Error fetching graph data", err));

      // 3. Agent Metrics
      fetch('http://localhost:8000/api/agents/metrics')
        .then(res => res.json())
        .then(data => setMetrics(data))
        .catch(err => console.error("Error fetching metrics", err));

      // 4. Events & Telemetry
      fetch('http://localhost:8000/api/events/recent?limit=10')
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data) && data.length > 0) {
            setRecentEvents(data.map(evt => ({
              name: evt.event_type,
              time: evt.created_at ? new Date(evt.created_at).toLocaleTimeString() : 'just now',
              status: evt.event_type.includes('failed') ? 'failed' : (evt.event_type.includes('started') ? 'running' : 'success')
            })));
          }
        })
        .catch(err => console.error("Error fetching events", err));
    };

    fetchAllData();
    const interval = setInterval(fetchAllData, 5000);
    return () => clearInterval(interval);
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
                title="Router Accuracy & Empirical Score" 
                type="donut"
                value={metrics.router_accuracy}
                description={`${metrics.developer_skill_increase} total`}
                subtext="adaptive routing active"
              />
              
              <MetricsWidget 
                title="Developer Quality Rating" 
                type="sparkline"
                value={`${metrics.developer_points} pts`} 
                description={`Executors: ${systemStatus.healthy_executors} online`}
                subtext="real-time telemetry"
              />
              
              <WorkflowFeed workflows={recentEvents} />
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
    
    if (activeTab === 'portfolio') {
      return <PortfolioView />;
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
            <span>Active Workflows: <span className="highlight">{systemStatus.active_workflows}</span></span>
            <span>System Status: <span className="highlight">{systemStatus.system_state}</span></span>
            <span>Healthy Backends: <span className="highlight">{systemStatus.healthy_executors}</span></span>
          </div>
        </header>
        
        {renderContent()}
      </main>
    </div>
  );
}
