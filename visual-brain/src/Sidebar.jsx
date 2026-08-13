import { LayoutDashboard, Users, Share2, Database, Rocket, Settings, BrainCircuit, Layers, BookOpen, Activity } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'portfolio', label: 'Portfolio', icon: Layers },
    { id: 'learning', label: 'Continuous Learning', icon: BookOpen },
    { id: 'evolution', label: 'Self-Evolution', icon: Rocket },
    { id: 'runtime', label: 'Cloud Runtime', icon: Activity },
    { id: 'agents', label: 'Agent Hub', icon: Users },
    { id: 'network', label: 'Network Graph', icon: Share2 },
    { id: 'knowledge', label: 'Knowledge Base', icon: Database },
    { id: 'deployments', label: 'Deployments', icon: Rocket },
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
