# Agent Contracts Architecture

EvoForge Phase 2 standardizes how the orchestrator and external systems interact with agents and executors through an explicit Contract Architecture.

## Core Abstractions

We separate metadata from implementation to allow routing work to different execution environments (local Python, remote microservices, LLM endpoints) without changing the Orchestrator logic.

### 1. Agent Contract (`AgentContract`)
The canonical metadata describing an agent. It contains no runtime code.
- `agent_id`: Unique identifier (e.g., `"developer"`).
- `name` / `role` / `description`: Human-readable context.
- `version`: Version of the agent definition.
- `capabilities`: List of `AgentCapability` enum values the agent possesses.
- `tools`: Required and optional tools for this agent.
- `permissions`: Required system permissions (evaluated by Policy Engine).

### 2. Agent Executor (`AgentExecutor`)
The runtime interface that actually performs the work.
```python
def execute(self, context: AgentContext) -> AgentResult:
```
This is an abstract class. Implementations can be native Python classes, HTTP clients calling remote services, or wrappers around legacy agent classes.

### 3. Agent Context (`AgentContext`)
The standardized payload passed to an executor.
Includes `run_id`, `task_id`, `workflow_id`, `task_description`, and available context (`project_id`, `dry_run`, `available_tools`).

### 4. Agent Result (`AgentResult`)
The standardized response returned by an executor.
Includes `success` boolean, `summary`, `metrics`, `errors`, and generated `artifacts`.

## Legacy Agent Adapter

For backwards compatibility with Phase 1 agents (`DeveloperAgent`, `QAAgent`, etc.), EvoForge uses the `LegacyAgentAdapter`. This adapter implements `AgentExecutor`, wraps the legacy agent instance, and maps the standard `AgentContext` to the older ad-hoc method calls (e.g., `implement_feature()`, `write_tests()`).

## Agent Registry

The `AgentRegistry` is the authoritative source for all available agents. It registers pairs of `(AgentContract, AgentExecutor)` and is injected into the OrchestratorEngine.

## Future: Phase 3 Routing

In Phase 3, the Orchestrator will match task requirements against `AgentContract.capabilities`. It will then use a Model Router to select the best `AgentExecutor` backend (e.g., a local model, Gemini, or Antigravity) capable of fulfilling those capabilities, creating a fully dynamic and distributed agent ecosystem.
