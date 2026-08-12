# EvoForge Model Providers & Executors Guide

## 1. Architectural Overview

EvoForge separates **Models** (inference engines, tokenizer specs, context windows) from **Executors** (runtime environments, tool access, permissions).

```
┌─────────────────────────────────────────────────────────────┐
│                      Task Requirements                       │
│    (Capabilities, Complexity, Latency/Cost Preferences)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       Executor Router                       │
│  1. Health & Circuit Breaker Check                          │
│  2. Capability Matching                                     │
│  3. Privacy & Security Policy Filtering                     │
│  4. Empirical Historical Scoring (from SQLite Telemetry)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Ranked Candidate Chain                   │
│   [Primary Executor] ─── (on failure) ───► [Fallback]       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Provider Implementation Status

| Provider / Backend | Runtime Status | Health Check Mechanism | Supported Capabilities | Configuration Keys |
| :--- | :--- | :--- | :--- | :--- |
| **Local / Ollama** | `IMPLEMENTED` | Live HTTP ping to `endpoint/api/tags` | `CODING`, `REFACTORING`, `MULTI_FILE_EDITING` | `providers.ollama.endpoint`, `providers.ollama.default_model` |
| **Google Gemini** | `IMPLEMENTED` | Environment key verification (`GEMINI_API_KEY`, `GOOGLE_API_KEY`) | `CODING`, `REASONING`, `REFACTORING`, `REPO_NAVIGATION`, `MULTI_FILE_EDITING` | `GEMINI_API_KEY`, `providers.gemini.default_model` |
| **NVIDIA Cloud** | `IMPLEMENTED` | Environment key verification (`NVIDIA_API_KEY`) | `CODING`, `REASONING`, `REFACTORING`, `MULTI_FILE_EDITING` | `NVIDIA_API_KEY`, `providers.nvidia.endpoint` |
| **Antigravity Boundary** | `STUB/BOUNDARY` | Disabled by default (`ANTIGRAVITY_ENABLED=1`) | `BROWSER`, `TERMINAL`, `REPO_NAVIGATION`, `TESTING`, `CODING` | `ANTIGRAVITY_ENABLED`, `ANTIGRAVITY_ENDPOINT` |

---

## 3. Telemetry & Empirical Scoring

Execution telemetry is automatically persisted to SQLite in the `execution_telemetry` table upon every execution attempt:

- **Metrics recorded**: `task_id`, `workflow_id`, `agent_id`, `executor_id`, `provider_id`, `model_id`, `started_at`, `completed_at`, `duration_ms`, `success`, `retry_count`, `fallback_used`, `failure_class`, `cost_usd`, `input_tokens`, `output_tokens`, `quality_score`.
- **Scoring formula**:
  $$\text{Score} = w_{\text{cap}} \cdot S_{\text{cap}} + w_{\text{qual}} \cdot Q_{\text{emp}} + w_{\text{succ}} \cdot R_{\text{succ}} + w_{\text{rel}} \cdot 0.95 - P_{\text{cost}} - P_{\text{lat}}$$
  Where:
  - $S_{\text{cap}}$: Capability match score (Phase 2 formula)
  - $Q_{\text{emp}}$: Average historical quality score
  - $R_{\text{succ}}$: Empirical success rate ($\frac{\text{successes}}{\text{total runs}}$)
  - $P_{\text{cost}}$, $P_{\text{lat}}$: Penalties weighted by task preferences.

---

## 4. Fallback Architecture

When a primary executor encounters a transient failure (such as rate limits or timeouts):
1. Telemetry records the failed attempt with its `failure_class`.
2. The Circuit Breaker increments consecutive failure counts.
3. The Orchestrator emits `router.fallback` event and transparently executes the next candidate in the ranked chain.
4. If a fallback executor succeeds, the task completes and telemetry marks `fallback_used=1`.
5. Policy and capability constraints are never relaxed during fallback.

---

## 5. Security & Secret Isolation

- **API Keys**: All cloud credentials (`GEMINI_API_KEY`, `NVIDIA_API_KEY`, `GITHUB_TOKEN`) are accessed exclusively from memory/environment variables at call time and are never logged, formatted into event payloads, or stored in SQLite.
- **Dry-run Mode**: Full simulation without making outbound API requests or incurring cost.
