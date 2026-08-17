
function getApiBase() {
  const custom = typeof window !== 'undefined' ? localStorage.getItem('evoforge_api_base') : null;
  const raw = custom || import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';
  const trimmed = raw.replace(/\/+$/, '');
  return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
}

class ApiClient {
  constructor() {
    this.token = typeof window !== 'undefined' ? localStorage.getItem('evoforge_auth_token') : null;
  }

  setToken(token) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) localStorage.setItem('evoforge_auth_token', token);
      else localStorage.removeItem('evoforge_auth_token');
    }
  }

  setBaseUrl(url) {
    if (typeof window !== 'undefined') {
      if (url) localStorage.setItem('evoforge_api_base', url);
      else localStorage.removeItem('evoforge_api_base');
    }
  }

  async _fetch(endpoint, options = {}) {
    const base = getApiBase();
    const url = `${base}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
      headers['X-Worker-Token'] = this.token;
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
  
  // Settings & Operations
  getComputePolicy() { return this._fetch('/settings/compute'); }
  updateComputePolicy(policy) { return this._fetch('/settings/compute', { method: 'PUT', body: JSON.stringify(policy) }); }
  updateGitHubToken(token) { return this._fetch('/github/token', { method: 'PUT', body: JSON.stringify({ token }) }); }
  updateLLMKey(provider, apiKey) { return this._fetch('/llm/keys', { method: 'PUT', body: JSON.stringify({ provider, api_key: apiKey }) }); }

  // Control Plane Global Operations
  scanPortfolio() { return this._fetch('/portfolio/scan', { method: 'POST' }); }
  generateDailyPlan() { return this._fetch('/portfolio/daily-plan', { method: 'POST' }); }
  resumeRuntime() { return this._fetch('/scheduler/resume', { method: 'POST' }); }
  pauseRuntime() { return this._fetch('/scheduler/pause', { method: 'POST' }); }
  forceRunDaily() { return this._fetch('/force-run-daily'); }
  triggerEvolution() { return this._fetch('/learning/evolve', { method: 'POST' }); }
}

export const api = new ApiClient();
