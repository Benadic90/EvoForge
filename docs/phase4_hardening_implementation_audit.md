# Phase 4 Hardening Implementation Audit

Based on the baseline audit findings, this document details exactly what will be changed to transform the Phase 4 skeleton into a reliable, autonomous portfolio management pipeline. The implementation is ordered by priority.

## 1. Security / Untrusted GitHub Text
**Target Files**: `src/evoforge/portfolio/models.py`, `src/evoforge/portfolio/scanner.py`, `src/evoforge/portfolio/priority_engine.py`
- **Changes**: 
  - Remove logic in `priority_engine.py` that modifies priority based on raw string matches (`if "security" in title`).
  - Modify `ProjectScanner` to extract and validate structured `PortfolioEvidence` (severity, type, observation) rather than passing raw untrusted GitHub issue descriptions directly to decision engines.
  - Establish a strict boundary: GitHub text remains untrusted context, not instruction.

## 2. Real Priority Mathematics
**Target Files**: `src/evoforge/portfolio/priority_engine.py`, `src/evoforge/portfolio/models.py`
- **Changes**: 
  - Implement a configurable scoring formula leveraging `self.weights`.
  - Normalize inputs to `0.0 - 1.0` (e.g., `security_score`, `impact_score`).
  - Introduce `confidence_factor` into calculations (`effective_signal = score * confidence`).
  - Enforce explainability by storing inputs, weights, and confidence in rankings so `evoforge portfolio-explain` can output human-readable reasoning.

## 3. PortfolioTask → TaskRequirements → ExecutorRouter
**Target Files**: `src/evoforge/portfolio/models.py`, `src/evoforge/portfolio/task_builder.py` (NEW)
- **Changes**: 
  - Build `PortfolioTaskRequirementsBuilder`.
  - Map `PortfolioTask` attributes to Phase 3 `TaskRequirements` using Phase 2 capability vocabularies (e.g., `requires_repo_write`, `requires_browser`).

## 4. DailyPlan → Bounded Workflow
**Target Files**: `src/evoforge/portfolio/daily_planner.py`, `src/evoforge/cli/main.py`
- **Changes**: 
  - Update `evoforge run-daily` to generate a `DailyPortfolioPlan`.
  - For each selected `PortfolioTask`, use `PortfolioTaskRequirementsBuilder` to feed `ExecutorRouter` and output a bounded `WorkflowDefinition`.
  - Submit the bounded workflows to the Phase 1 `OrchestratorEngine`.

## 5. Health History + Trends
**Target Files**: `src/evoforge/memory/database.py`, `src/evoforge/portfolio/registry.py`
- **Changes**: 
  - Create the `project_health_history` SQLite table.
  - Implement snapshotting logic when saving project states.
  - Add trend calculation (IMPROVING, DECLINING, STABLE) based on historical deltas.

## 6. Real Repository Analysis
**Target Files**: `src/evoforge/portfolio/scanner.py`
- **Changes**: 
  - Enhance `ProjectScanner` with safe local heuristics (e.g., test discovery, TODO counting, CI config detection) to replace mocked `unknown_fields`.

## 7. Roadmap Synchronization
**Target Files**: `src/evoforge/portfolio/roadmap.py`
- **Changes**: 
  - Compare actual GitHub state with Obsidian roadmaps without silently overwriting.
  - Mark low-confidence updates as `NEEDS_REVIEW` using explicit synchronization proposals.

## 8. API Pagination/Error Handling
**Target Files**: `src/evoforge/api/server.py`
- **Changes**: 
  - Add `page` and `page_size` query params to `GET /api/portfolio/tasks`, `GET /api/projects`, and `GET /api/portfolio/ranking`.
  - Wrap API endpoints in robust try/except blocks to return `503 Service Unavailable` instead of raw `500`s for GitHub timeouts.

## 9. GitHub Caching/Rate-Limit Handling
**Target Files**: `src/evoforge/github_integration/client.py`, `src/evoforge/portfolio/scanner.py`
- **Changes**: 
  - Support `last_scan` timestamps.
  - Handle partial successes (`scan_status = FAILED` for single repos without failing the entire portfolio scan).

## 10. Visual Brain Integration
**Target Files**: `visual-brain/src/App.jsx`, `visual-brain/src/components/PortfolioView.jsx`
- **Changes**: 
  - Fetch paginated API data.
  - Display project health trends, confidence, and open tasks without fabricating data.
