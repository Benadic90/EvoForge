const configuredApiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';
const trimmedApiBase = configuredApiBase.replace(/\/+$/, '');
const API_BASE = trimmedApiBase.endsWith('/api') ? trimmedApiBase : `${trimmedApiBase}/api`;

class ApiClient {
  constructor() {
    this.token = null;
  }

  setToken(token) {
    this.token = token;
  }

  async _fetch(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorData = null;
        try {
          errorData = await response.json();
        } catch (e) {
          errorData = { detail: response.statusText };
        }
        throw new Error(errorData.detail || `API Error: ${response.status}`);
      }

      // 204 No Content
      if (response.status === 204) {
        return null;
      }
      
      return await response.json();
    } catch (error) {
      console.error(`[ApiClient] Failed to fetch ${endpoint}:`, error);
      throw error;
    }
  }

  // System & Runtime
  getSystemStatus() { return this._fetch('/status'); }
  getRuntimeStatus() { return this._fetch('/runtime/status'); }
  getSchedulerStatus() { return this._fetch('/scheduler/status'); }
  
  // Workers
  getWorkers() { return this._fetch('/workers'); }
  drainWorker(workerId) { return this._fetch(`/workers/${workerId}/drain`, { method: 'POST' }); }
  
  // Agents
  getAgents() { return this._fetch('/agents'); }
  getAgentMetrics() { return this._fetch('/agents/metrics'); }
  
  // Executors & Models
  getExecutors() { return this._fetch('/executors'); }
  getModels() { return this._fetch('/models'); }
  getProviderHealth() { return this._fetch('/providers/health'); }
  
  // Routing
  getRecentRouting() { return this._fetch('/routing/recent'); }
  getRoutingStats() { return this._fetch('/routing/statistics'); }
  
  // Projects & Portfolio
  getProjects() { return this._fetch('/projects'); }
  getProject(id) { return this._fetch(`/projects/${id}`); }
  getProjectHealth(id) { return this._fetch(`/projects/${id}/health`); }
  getProjectRoadmap(id) { return this._fetch(`/projects/${id}/roadmap`); }
  getProjectTasks(id) { return this._fetch(`/projects/${id}/tasks`); }
  
  getPortfolioHealth() { return this._fetch('/portfolio/health'); }
  getPortfolioRanking() { return this._fetch('/portfolio/ranking'); }
  getDailyPlan() { return this._fetch('/portfolio/daily-plan'); }
  getPortfolioTasks() { return this._fetch('/portfolio/tasks'); }
  
  // Learning & Evolution
  getResearch() { return this._fetch('/learning/research'); }
  getSkills() { return this._fetch('/learning/skills'); }
  getSkillGaps() { return this._fetch('/learning/gaps'); }
  getBenchmarks() { return this._fetch('/learning/benchmarks'); }
  
  getProposals() { return this._fetch('/evolution/proposals'); }
  getExperiments() { return this._fetch('/evolution/experiments'); }
  approveProposal(id) { return this._fetch(`/evolution/proposals/${id}/approve`, { method: 'POST' }); }
  rejectProposal(id) { return this._fetch(`/evolution/proposals/${id}/reject`, { method: 'POST' }); }

  // Telemetry & Events
  getRecentEvents() { return this._fetch('/events/recent'); }
  getTelemetryExecutions() { return this._fetch('/telemetry/executions'); }
  getTelemetryStats() { return this._fetch('/telemetry/statistics'); }
  
  // Knowledge Graph
  getKnowledgeGraph() { return this._fetch('/graph/knowledge'); }
  
  // Settings
  getComputePolicy() { return this._fetch('/settings/compute'); }
  updateComputePolicy(policy) { return this._fetch('/settings/compute', { method: 'POST', body: JSON.stringify(policy) }); }
}

export const api = new ApiClient();
