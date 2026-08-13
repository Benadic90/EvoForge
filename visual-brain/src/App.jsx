import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Dashboard from './Dashboard';
import PortfolioView from './PortfolioView';
import LearningView from './LearningView';
import EvolutionView from './EvolutionView';
import Settings from './Settings';
import WorkerFleetView from './WorkerFleetView';
import AgentHub from './AgentHub';
import ExecutorsView from './ExecutorsView';
import EventStream from './EventStream';
import RoutingDetails from './RoutingDetails';
import RuntimeStatusHeader from './RuntimeStatusHeader';
import { useRealTime } from './hooks/useRealTime';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Connect to backend real-time state
  const realTimeState = useRealTime(3000);

  const renderContent = () => {
    if (activeTab === 'dashboard') return <Dashboard realTimeState={realTimeState} />;
    if (activeTab === 'portfolio') return <PortfolioView />;
    if (activeTab === 'agents') return <AgentHub />;
    if (activeTab === 'executors') return <ExecutorsView />;
    if (activeTab === 'routing') return <RoutingDetails />;
    if (activeTab === 'learning') return <LearningView />;
    if (activeTab === 'evolution') return <EvolutionView />;
    if (activeTab === 'events') return <EventStream realTimeState={realTimeState} />;
    if (activeTab === 'workers') return <WorkerFleetView realTimeState={realTimeState} />;
    if (activeTab === 'settings') return <Settings />;
    
    // Fallbacks
    if (activeTab === 'network' || activeTab === 'knowledge' || activeTab === 'deployments') {
      return <div className="p-8 text-[var(--text-muted)]">This view is currently under construction for Phase 8.</div>;
    }

    return <Dashboard realTimeState={realTimeState} />;
  };

  return (
    <div className="app-layout" style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content" style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
        <RuntimeStatusHeader 
          isOffline={realTimeState.isOffline}
          system={realTimeState.system}
          runtime={realTimeState.runtime}
          scheduler={realTimeState.scheduler}
        />
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {renderContent()}
        </div>
      </main>
    </div>
  );
}
