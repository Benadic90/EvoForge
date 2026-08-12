# Current State Audit

**Date:** 2026-08-12
**Target:** `src/evoforge/` and supporting modules

This document provides a factual assessment of the existing EvoForge implementation based on a full codebase audit.

## 1. Existing Functionality
The repository contains a substantial foundational architecture with high modularity and clear separation of concerns.

*   **Agents**: Core (`Developer`, `QA`, `Reviewer`, `Security`) and Advanced (`Architect`, `ConflictResolver`, `DevOps`, `Documentation`, `Planner`, `Research`) agents exist, subclassing a `BaseAgent` that supports up to 10 step execution loops.
*   **Memory & Persistence**: A dual-layer memory system is implemented. `Database` manages an SQLite schema with 9 tables, while `ObsidianManager` writes markdown vault notes with YAML frontmatter.
*   **Policy Engine**: The `ActionValidator` actively enforces sandbox constraints, checking shell commands via `ShellAllowlist` (regex blocklists) and scanning for secret leaks via `SecretDetector`.
*   **Model Router**: `ModelRouter` wraps `litellm` and successfully directs requests to Gemini, Ollama, or NVIDIA models. It includes a `FallbackManager` for rate limits/errors and a `CostTracker`.
*   **Orchestration**: `OrchestratorEngine.execute_workflow()` is implemented, processing a `WorkflowDefinition` by dispatching tasks to the agent roster.
*   **Evolution & Learning**: `ExperimentFramework.run_ab_test()` runs code variants synchronously. `BenchmarkRunner`, `SkillRegistry`, and `SandboxEnvironment` are fully implemented for isolated practice.
*   **API**: A full FastAPI application exists (`server.py`) serving the visual UI endpoints.
*   **GitHub**: `GitHubClient` (PyGithub wrapper) and `LocalRepository` (GitPython wrapper) support fetching repos, creating branches, committing, and pushing.

## 2. Partial Functionality
Features that exist but are incomplete or rely on basic heuristics rather than robust logic.

*   **Agent Tool Calling**: `agents/base.py` uses rudimentary string matching (`{"tool":`) to parse tool calls instead of native LLM structured outputs or function calling.
*   **Model Selection Heuristics**: The `ModelRouter` relies on basic, hardcoded heuristics (e.g., local Ollama for trivial, Gemini for high complexity) rather than performance-measured evidence.
*   **Task Prioritization**: `orchestrator/prioritizer.py` sorts strictly by priority integer value instead of performing a full topological sort on dependencies.
*   **API Endpoints**: The endpoints currently fall back to hardcoded mock dictionaries if the SQLite tables are empty.
*   **GitHub Scanning**: `RepositoryScanner` relies on simplistic path heuristics to identify project structure and language.

## 3. Stubs
Areas containing placeholder `# TODO` code or returning mocked strings.

*   **CLI Application**: `src/evoforge/main.py` contains stubs for the `run_daily` and `status` commands.
*   **Crash Recovery**: `OrchestratorEngine.recover_crashed_workflows()` is entirely stubbed, currently just emitting a log message without actually reloading state.
*   **Evolution Proposer**: `EvolutionAgent.propose_skill_update()` returns a hardcoded mock dictionary instead of actually parsing LLM improvement proposals.

## 4. Integration Gaps
Where modules exist but lack proper connection.

*   **Memory Recording Issue**: `MemoryManager.record_workflow_checkpoint()` attempts to update non-existent database columns (`state`, `context`) instead of the actual SQLite schema columns (`status`, `state_snapshot`).
*   **Research & Source Verification**: The `ResearchEngine`, `InnovationEngine`, and `SourceVerifier` lack live web-scraping or integration with external knowledge sources, relying entirely on simulated research.

## 5. Security Weaknesses
*   While `ShellAllowlist` covers basic threats (`rm -rf`), a sufficiently capable LLM could bypass simple regex pattern matching.
*   No isolation boundary exists between the agent process and the host process other than Python-level policy checks (i.e. no Docker/container sandbox).

## 6. Reliability Weaknesses
*   No idempotent state management: If a workflow crashes mid-execution, there is no canonical way to resume exactly where it left off.
*   The system relies on synchronous, blocking loops for agent execution.
*   No structured checkpoint reloading mechanism exists.

## 7. Testing Weaknesses
*   **Coverage**: 11 test files exist in `tests/`, covering basic initialization and mock execution.
*   **Missing Suites**: There is no dedicated test file for `api` (e.g. `test_api.py`) or the `learning` package (`test_learning.py`).
*   **Lack of Integration/Recovery Tests**: There are no tests verifying crash recovery, transactional consistency, or full end-to-end task completion.

## 8. Documentation Mismatches
*   Documentation implies that EvoForge operates continuously as an autonomous organization, but the `main.py` CLI run loops are completely stubbed out.

## 9. Recommended Refactors
*   Migrate `BaseAgent` tool calling to use native provider function calling (e.g., OpenAI/Anthropic tool schemas).
*   Correct the `record_workflow_checkpoint` SQLite columns.
*   Decouple the orchestrator's state model into a dedicated `CanonicalWorkflowState` object that controls lifecycle transitions.

## 10. Exact Phase 1 Implementation Map (Runtime Integrity)

1.  **Define Canonical Workflow State**: Implement a unified Pydantic model representing a task workflow, run IDs, and explicit state enumerations (`INITIALIZE`, `PLAN`, `IMPLEMENT`, etc.).
2.  **Database Fixes**: Correct the `MemoryManager` SQL schema mismatch for checkpoint saving.
3.  **State Machine Core**: Refactor `OrchestratorEngine` to advance workflows through the explicit state machine rather than a simple sequential loop.
4.  **Crash Recovery Implementation**: Implement the stubbed `recover_crashed_workflows()` by retrieving the last durable checkpoint and injecting it back into the active `OrchestratorEngine`.
5.  **Event System Foundation**: Standardize internal event logging (`workflow.started`, `agent.completed`, etc.) using the existing structured logger.
6.  **Idempotency Checks**: Ensure git commits and side-effects check the workflow state before duplicating execution upon a crash recovery.
7.  **Phase 1 Testing**: Implement `tests/test_runtime_recovery.py` to verify the state machine and crash recovery mechanism.
