# Phase 4 Audit: EvoForge Repository Current State Analysis

## 1. GitHub Integration (`src/evoforge/github_integration/`)
* **Implemented**: 
  * Repository discovery (`get_user_repositories`) for the authenticated user.
  * Local cloning, branching, and committing via GitPython (`LocalRepository`).
  * PR creation and template management (`PullRequestManager`).
  * Basic file-based static scanning (checking for `pyproject.toml`, `.github`, etc.) and language detection (`RepositoryScanner`).
* **Missing/Not Implemented**: 
  * Issue discovery, scanning, and reading/writing.
  * Dependency graph and remote GitHub API repository metadata (like CI health/test states from GitHub Actions) beyond static file checks.
  * Security finding access (Dependabot/CodeQL API integration).

## 2. Project Memory (`src/evoforge/memory/`)
* **SQLite Database (`database.py`)**:
  * Contains 14 tables including `workflows`, `tasks`, `metrics`, `events`, `execution_telemetry`, etc.
  * The `tasks` table currently models individual workflow tasks but doesn't have normalized representations for GitHub issues vs security findings across a whole portfolio context.
  * The `workflows` table tracks execution but lacks a multi-repo portfolio-level scheduling loop.
* **Obsidian Manager (`obsidian.py`)**:
  * Manages the markdown knowledge vault.
  * Projects directory exists (`Projects/`), but there's no structured synchronization mechanism that turns repository facts into Obsidian roadmaps.

## 3. Workflow Execution & Planning (`src/evoforge/orchestrator/`, `src/evoforge/agents/`)
* **Planning Infrastructure**:
  * Uses `WorkflowDefinition` and `WorkflowTask`.
  * `TaskPrioritizer` sorts tasks simply by an enum (`CRITICAL`, `HIGH`, etc.).
  * `PlannerAgent` exists to convert high-level goals into implementation plans.
  * `OrchestratorEngine` runs the workflow state machine with worker leases, atomic execution, and crash recovery.
* **Daily Loop**:
  * `run_daily_loop` exists in the engine to recover workflows, run input workflows, and trigger learning.
  * **Missing**: The CLI `evoforge daily-plan` / `run_daily` is currently a stub. There is no automated portfolio scanner that generates the input for `run_daily_loop` based on portfolio health and prioritization.

## 4. Visual Brain Frontend (`visual-brain/`)
* Located at the root (`visual-brain/`). Built with React/Vite.
* Features a dashboard with metrics, agent hub, network view, and a real-time event feed.
* **Missing**: No "Portfolio" view displaying all projects, health, open tasks, roadmaps, etc.

## 5. Existing Models for Reuse
* `WorkflowDefinition` and `WorkflowTask` (can be extended for `PortfolioTask`).
* `RepositoryPolicy` for security boundaries.
* `KnowledgeItem`, `ResearchTopic` for learning.
* `AgentContract` for bounding execution context.
* `EventRecord` for the `EventEmitter` system.

## Risks and Compatibility Concerns
* **Concurrency**: We must use Phase 1 workflow leases for multi-repository concurrency to avoid stepping on existing workflows.
* **Memory Sync**: Roadmaps must be properly synced between GitHub and Obsidian. We must not let AI blindly rewrite a human-curated Obsidian roadmap without GitHub evidence.
* **Policy Integrity**: We must not bypass the `PolicyEngine` or Agent Contracts when generating automated daily plans. Everything must funnel through the existing secure execution pipeline.
