# Phase 8: Current State Audit
## Visual Brain & API Integration

### Existing Pages (Visual Brain)
- **App.jsx**: Main entry point; currently handles manual routing/tabs.
- **Sidebar.jsx**: Navigation menu connecting to tabs.
- **Dashboard (App.jsx core views)**: Currently includes `WorkflowFeed`, `MetricsWidget`, and static displays.
- **AgentHub.jsx**: Shows list of agents (currently some hardcoded / mocked logic may remain).
- **Deployments.jsx**: Deployment operations.
- **EvolutionView.jsx**: Phase 6 interface showing proposals and experiments.
- **KnowledgeBase.jsx**: Phase 5 knowledge search interface.
- **KnowledgeGraph.jsx / NetworkView.jsx**: Node/edge visualizations.
- **LearningView.jsx**: Phase 5 continuous learning interface.
- **PortfolioView.jsx**: Phase 4 project portfolio.
- **RuntimeView.jsx**: Phase 7 worker/scheduler interface.
- **Settings.jsx**: Configuration interface.

### Existing API Endpoints (Control Plane)
The API at `src/evoforge/api/server.py` exposes a robust typed interface:
- **System/Runtime**: `/api/status`, `/api/runtime/status`, `/api/scheduler/status`
- **Agents**: `/api/agents`, `/api/agents/{id}`, `/api/agents/{id}/capabilities`
- **Workers**: `/api/workers`, `/api/workers/register`, `/api/workers/{id}/heartbeat`, `/api/workers/{id}/request-work`, `/api/workers/{id}/release-work`, `/api/workers/{id}/drain`
- **Executors/Routing**: `/api/executors`, `/api/models`, `/api/routing/recent`, `/api/routing/statistics`, `/api/routing/{id}`
- **Portfolio/Projects**: `/api/projects`, `/api/projects/{id}`, `/api/projects/{id}/health`, `/api/projects/{id}/roadmap`, `/api/portfolio/ranking`, `/api/portfolio/daily-plan`
- **Learning/Evolution**: `/api/learning/research`, `/api/learning/skills`, `/api/evolution/proposals`, `/api/evolution/experiments`
- **Telemetry/Events**: `/api/events/recent`, `/api/telemetry/executions`, `/api/telemetry/statistics`
- **Settings**: `/api/settings/compute`

### Shortcomings & Gaps
1. **Scattered Logic**: Many components execute their own `fetch()` calls or rely on `setInterval()` polling independently. There is no centralized API client (`src/api/`).
2. **Mock Data**: Earlier phases left behind static placeholder numbers in React (e.g. `98.4%`, fake agent counts) instead of strictly consuming the backend JSON.
3. **No Event Streaming**: Polling is used instead of a unified real-time event stream.
4. **Error Handling**: Offline states or API connection failures are not uniformly handled; the UI does not clearly show when the backend drops offline.
5. **No Unified Command Panel**: The UI lacks a central, safe operations panel to trigger scheduler operations, runtime pauses, or daily plan generation.

### Missing Real-Time Functionality
- `Server-Sent Events (SSE)` or centralized efficient polling is needed to deliver live `events/recent` updates directly to a global state or hook.
- A "System Timeline" component merging workflow, routing, and learning events into one view.
- Real-time updates to worker/executor/portfolio states instead of page reloads.
