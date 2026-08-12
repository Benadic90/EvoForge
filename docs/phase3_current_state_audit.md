# Phase 3 Current State Audit

## 1. Existing Model Router Capabilities
The existing router (`src/evoforge/model_router/router.py`) handles basic LLM routing using `litellm`.
- It takes an `LLMRequest` containing `TaskType` and `TaskComplexity`.
- It selects a model based on hard-coded rules (e.g. `TRIVIAL` tasks go to `ollama`, complex tasks go to `gemini`).
- It has basic cost tracking (`CostTracker`).

## 2. Existing Provider Integrations
The providers are defined in `src/evoforge/model_router/providers.py` and are integrated purely at the API wrapper level via `litellm`. 
- `ollama`
- `gemini`
They are treated exclusively as LLM generation endpoints, not as executors.

## 3. What Can Be Reused
- **CostTracker**: Can be adapted for the new quota/cost policy tracking.
- **TaskType/Complexity Definitions**: Useful for deriving `TaskRequirements`.
- **litellm execution**: Can be wrapped inside a `ModelProvider` for LLM-based executors (like Gemini and Ollama).
- **AgentCapability vocabulary**: The existing `AgentCapability` enum from Phase 2 will be perfectly reused for filtering.

## 4. What Is Incomplete
- **Separation of Model vs Executor**: The current system treats the LLM as the executor. There is no concept of a runtime environment (e.g., local execution vs Antigravity).
- **No Capability-Based Filtering**: The router does not use the Phase 2 capabilities to select the executor.
- **No Performance Scoring**: It selects purely by predefined manual if-statements.
- **No Fallback / Circuit Breaker**: If litellm fails, it just raises the exception.
- **No Visual Brain/CLI Introspection**: The router's state is completely hidden.

## 5. What Must Be Refactored
- `ModelRouter` must be split into:
  - `ModelRegistry` (managing known models and their capabilities)
  - `ExecutorRegistry` (managing executor backends like `GeminiExecutor`, `AntigravityExecutor`)
  - `ExecutorRouter` (the logic that matches `TaskRequirements` to `Executor`)
- The Orchestrator's `_execute_task` must use the `ExecutorRouter` to fetch the right `AgentExecutor`, rather than reading `task.agent_type` and querying the `AgentRegistry` directly. Wait, the Orchestrator needs the Agent metadata, but the Executor will perform it. The Orchestrator should do: `Executor = ExecutorRouter.select(TaskRequirements)`.

## 6. Compatibility Risks
- The `LegacyAgentAdapter` from Phase 2 implements `AgentExecutor`. The router must seamlessly work with `AgentExecutor`. If the Orchestrator dynamically resolves the executor, how do the legacy agents fit in? A legacy agent *is* an executor. So `LocalExecutor` might just invoke the legacy python agents, or the legacy agents become specific instances of local executors. We need to define exactly how `AgentContract` (what is being done) maps to `AgentExecutor` (who does it). 
- Event Emission: We need to ensure that the new routing logic emits the requested events (`router.requested`, etc.) without breaking existing Phase 1 listeners.
