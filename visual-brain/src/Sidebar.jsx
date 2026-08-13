import { LayoutDashboard, Users, Share2, Database, Rocket, Settings, BrainCircuit, Layers, BookOpen, Activity, Cpu, Network, ListTree, ActivitySquare } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'portfolio', label: 'Portfolio', icon: Layers },
    { id: 'agents', label: 'Agent Hub', icon: Users },
    { id: 'workers', label: 'Worker Fleet', icon: ActivitySquare },
    { id: 'executors', label: 'Executors & Models', icon: Cpu },
    { id: 'routing', label: 'Routing Decisions', icon: Network },
    { id: 'learning', label: 'Learning & Skills', icon: BookOpen },
    { id: 'evolution', label: 'Evolution & Testing', icon: Rocket },
    { id: 'events', label: 'Event Stream', icon: ListTree },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <div className="glass-panel sidebar">
      <div className="sidebar-logo">
        <BrainCircuit size={28} color="#00f0ff" />
        <div>
          EvoForge
          <span>Visual Brain</span>
        </div>
      </div>
      
      <div className="sidebar-nav">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <div 
              key={tab.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={18} color={isActive ? '#00f0ff' : 'currentColor'} />
              <span>{tab.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
