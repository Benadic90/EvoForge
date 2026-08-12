# Phase 3B Current State Audit

## 1. Executor Mocks
In `src/evoforge/model_router/executors.py`, the following executors are completely mocked:
- `LocalModelExecutor`
- `GeminiExecutor`
- `NvidiaExecutor`
- `AntigravityExecutor` (which is correctly a boundary stub, but the others should be real).
They currently return fake `AgentResult` objects with hardcoded `latency_ms` and `cost`.

## 2. Telemetry & Historical Data
In `src/evoforge/model_router/routing.py`, historical routing is mocked:
```python
hist_score = 0.9 * (self.weights["quality_score"] + self.weights["historical_success"] + self.weights["reliability"])
```
There is no database table to store execution metrics. The `Database` class in `src/evoforge/memory/database.py` only stores `workflows`, `workflow_events`, `checkpoints`, etc., but no `execution_telemetry` or equivalent.

## 3. Fallback Mechanism
The router in `src/evoforge/model_router/routing.py` currently selects the highest-scored executor and returns it. It does not actively catch execution failures and fall back to the next best candidate. The orchestrator engine calls the executor and just fails if the executor fails. Fallback needs to be integrated, perhaps at the executor or orchestrator level. The user asks to "test fallback", meaning the router or the engine needs to handle retry/fallback to the next candidate.

## 4. Provider Configuration
The actual model API logic resides in the old `src/evoforge/model_router/router.py`, which uses `litellm`. That file's logic needs to be moved into the new `LocalModelExecutor`, `GeminiExecutor`, and `NvidiaExecutor` (or into `ModelProvider` classes if we decouple model inference from agent execution). Since an `AgentExecutor` executes an `AgentContext`, these new executors must take the agent's prompt, route it via `litellm` (or direct API), and return an `AgentResult`.

## 5. Summary
To achieve Phase 3B:
1. We must create an `execution_telemetry` table in SQLite.
2. The `ExecutorRouter` must read this table for real historical scoring.
3. The `OrchestratorEngine` must loop over fallback candidates if the chosen executor fails.
4. The `AgentExecutor` implementations must use `litellm` (or real APIs) to execute the task prompt, measure actual latency, check health, handle rate limits, and return the `AgentResult`.
