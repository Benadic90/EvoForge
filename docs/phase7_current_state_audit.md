# Phase 7 Baseline Audit: Current State of EvoForge

## Current Runtime Assumptions
- **Single Process Monolith**: `evoforge run_daily` acts as the single execution engine. It initializes the database, the agent registry, the executor router, the project scanner, and the orchestrator all in one synchronous loop.
- **Laptop as Core**: Since the `run_daily` loop runs on the user's local machine, when the laptop is off, EvoForge stops entirely.
- **Worker/Lease Logic**: The `OrchestratorEngine` uses a UUID `worker_id` generated per instantiation and uses an atomic SQLite `UPDATE` to acquire a lease for a workflow. However, this is largely a safety mechanism in a local multi-process scenario; there is no distributed worker pooling yet.

## What Requires the Laptop?
- The entire control plane (scheduling, database connections, API server).
- Local models (Ollama execution).
- GitHub syncing (currently tied to the `run_daily` loop execution on the host machine).

## What Can Run Headlessly?
- The existing SQLite database and FastAPI server (`server.py`) can run headlessly.
- The `ExecutorRouter` and remote cloud models (Gemini, NVIDIA) require no GUI or local state beyond the API keys.
- The `OrchestratorEngine` and its state machine (`WorkflowState`) are completely decoupled from UI or specific local hardware constraints, designed to run bounded segments and checkpoint to SQLite.

## What Must Move to the Cloud (Control Plane)
- The persistent `evoforge.db` SQLite database.
- `ProjectRegistry`, `ProjectScanner`, and `DailyPlanner` logic.
- `AgentRegistry` and `ExecutorRegistry` initialization.
- The workflow lease manager and scheduler loop.

## Existing Worker/Lease Semantics
- Workflows have a `worker_id` and `lease_expires_at` column in SQLite.
- `OrchestratorEngine._acquire_lease()` updates `lease_expires_at` (15 min default).
- `_renew_lease()` extends the lease during execution.
- If a worker dies, `recover_crashed_workflows()` finds workflows where `lease_expires_at` is past due and re-acquires them.
- **Limitation**: There is no overarching `workers` table, meaning the system knows a workflow has a lease, but it doesn't know the status/health of the workers themselves or what capabilities they offer.

## Existing Database Limitations
- No `workers` or `worker_heartbeats` table.
- No `scheduler_state` table to persist scheduler runs.
- Relying on SQLite is fine for single-node deployments, but restricts scaling to multiple concurrent cloud nodes unless a distributed filesystem (like Litestream/LiteFS) or Postgres is used in the future. The abstraction should remain DB-agnostic.

## Current Scheduler Limitations
- There is no long-running scheduler. `run_daily` is a CLI command that runs once and exits.
- No abstraction exists for recurring background tasks (research scanning, evolution benchmarking).

## Security Concerns
- A headless control plane will require authentication. Worker nodes asking for tasks must prove identity to avoid malicious nodes stealing workflows.
- Secrets (API keys) are currently loaded from the host environment variables. The worker nodes must have these securely injected, and the laptop worker shouldn't need cloud API keys if it only serves local models.

## Deployment Constraints
- Target: A single-node persistent Control Plane deployment using the existing SQLite database.
- Target: Minimal Python worker processes that poll for tasks.
- No Kafka/Redis/K8s to keep complexity low for now.
