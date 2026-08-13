import sqlite3
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


SCHEMA = """
-- Core execution state
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    workflow_type TEXT NOT NULL,
    task_description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    current_step TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    git_branch TEXT,
    pr_number INTEGER,
    pr_url TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    state_snapshot TEXT,
    worker_id TEXT,
    lease_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Idempotent Operations Registry
CREATE TABLE IF NOT EXISTS workflow_operations (
    operation_key TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    task_id TEXT,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workflow_id, task_id, action)
);

-- Structured Event Log
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    run_id TEXT,
    workflow_id TEXT,
    task_id TEXT,
    agent_id TEXT,
    repository_id TEXT,
    source TEXT,
    status TEXT,
    payload TEXT
);

-- Task queue
CREATE TABLE IF NOT EXISTS tasks (

    id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    task_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    priority REAL NOT NULL DEFAULT 0.5,
    source TEXT,
    status TEXT DEFAULT 'pending',
    assigned_workflow TEXT REFERENCES workflows(id),
    estimated_complexity TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metrics
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    project TEXT,
    agent TEXT,
    tags TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent skill profiles
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    confidence REAL NOT NULL DEFAULT 0.5,
    capability_level TEXT DEFAULT 'beginner',
    last_verified TIMESTAMP,
    last_researched TIMESTAMP,
    freshness TEXT DEFAULT 'unknown',
    status TEXT DEFAULT 'active',
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_name, skill_name, version)
);

-- Versioned skill snapshots for rollback
CREATE TABLE IF NOT EXISTS skill_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id TEXT NOT NULL REFERENCES skills(id),
    version INTEGER NOT NULL,
    system_prompt_patch TEXT,
    techniques TEXT,
    tools TEXT,
    patterns TEXT,
    anti_patterns TEXT,
    benchmark_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge items with lifecycle
CREATE TABLE IF NOT EXISTS knowledge_items (
    knowledge_id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    domain TEXT NOT NULL,
    summary TEXT,
    source_ids TEXT,
    confidence REAL DEFAULT 0.0,
    verification_status TEXT DEFAULT 'UNVERIFIED',
    tags TEXT,
    related_skills TEXT,
    related_projects TEXT,
    evidence TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Research jobs (Phase 5)
CREATE TABLE IF NOT EXISTS research_jobs (
    research_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    project_id TEXT,
    task_id TEXT,
    domain TEXT NOT NULL,
    topic TEXT NOT NULL,
    query TEXT,
    reason TEXT,
    priority REAL DEFAULT 0.5,
    status TEXT DEFAULT 'QUEUED',
    source_ids TEXT,
    confidence REAL DEFAULT 0.0,
    findings TEXT,
    skill_gap_id TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skill Gaps (Phase 5)
CREATE TABLE IF NOT EXISTS skill_gaps (
    skill_gap_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    project_id TEXT,
    severity TEXT DEFAULT 'MEDIUM',
    confidence REAL DEFAULT 1.0,
    evidence_ids TEXT,
    recommended_action TEXT,
    status TEXT DEFAULT 'OPEN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Practice Plans (Phase 5)
CREATE TABLE IF NOT EXISTS practice_plans (
    practice_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    objective TEXT,
    tasks TEXT,
    difficulty TEXT,
    budget TEXT,
    deadline TIMESTAMP,
    benchmark_id TEXT,
    status TEXT DEFAULT 'DRAFT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Engineering lessons from real work
CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    problem_pattern TEXT NOT NULL,
    root_cause TEXT,
    successful_solution TEXT,
    related_skill TEXT,
    evidence_ids TEXT,
    confidence REAL DEFAULT 1.0,
    status TEXT DEFAULT 'UNVERIFIED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Benchmark suites and results
CREATE TABLE IF NOT EXISTS benchmarks (
    benchmark_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    environment TEXT,
    baseline_score REAL,
    candidate_score REAL,
    sample_count INTEGER DEFAULT 0,
    evidence TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evolution Proposals (Phase 6)
CREATE TABLE IF NOT EXISTS evolution_proposals (
    proposal_id TEXT PRIMARY KEY,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    current_version TEXT,
    candidate_version TEXT,
    description TEXT,
    hypothesis_json TEXT,
    evidence_ids TEXT,
    benchmark_id TEXT,
    experiment_id TEXT,
    risk TEXT DEFAULT 'LOW',
    status TEXT DEFAULT 'PROPOSED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    deployed_at TIMESTAMP,
    rolled_back_at TIMESTAMP,
    rollback_version TEXT
);

-- Evolution Experiments (Phase 6)
CREATE TABLE IF NOT EXISTS experiment_records (
    experiment_id TEXT PRIMARY KEY,
    proposal_id TEXT REFERENCES evolution_proposals(proposal_id),
    baseline_version TEXT,
    candidate_version TEXT,
    target TEXT,
    dataset TEXT,
    sample_count INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    baseline_score REAL,
    candidate_score REAL,
    improvement_percent REAL,
    regressions INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0,
    latency REAL DEFAULT 0.0,
    status TEXT DEFAULT 'RUNNING',
    environment TEXT
);

-- Evolution Deployments (Phase 6)
CREATE TABLE IF NOT EXISTS evolution_deployments (
    deployment_id TEXT PRIMARY KEY,
    proposal_id TEXT REFERENCES evolution_proposals(proposal_id),
    deployed_version TEXT NOT NULL,
    rollback_version TEXT NOT NULL,
    deployment_type TEXT DEFAULT 'FULL', -- CANARY, SHADOW, FULL
    status TEXT DEFAULT 'ACTIVE',
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rolled_back_at TIMESTAMP,
    rollback_reason TEXT
);

-- Failure registry
CREATE TABLE IF NOT EXISTS failures (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    task_id TEXT,
    task_description TEXT,
    context TEXT,
    attempted_solution TEXT,
    failure_reason TEXT,
    correction TEXT,
    lesson_id TEXT REFERENCES lessons(id),
    correction_worked BOOLEAN,
    regression_passed BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Execution telemetry for dynamic routing and empirical performance tracking
CREATE TABLE IF NOT EXISTS execution_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    agent_id TEXT,
    task_type TEXT,
    executor_id TEXT NOT NULL,
    provider_id TEXT,
    model_id TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms REAL,
    success BOOLEAN NOT NULL,
    retry_count INTEGER DEFAULT 0,
    fallback_used BOOLEAN DEFAULT 0,
    failure_class TEXT,
    cost_usd REAL DEFAULT 0.0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    quality_score REAL,
    tests_passed BOOLEAN,
    review_passed BOOLEAN,
    security_passed BOOLEAN,
    artifact_valid BOOLEAN,
    human_approved BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Persisted Routing Decisions
CREATE TABLE IF NOT EXISTS routing_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    agent_id TEXT,
    task_type TEXT,
    requirements_json TEXT,
    candidate_rankings_json TEXT,
    selected_executor_id TEXT NOT NULL,
    selected_provider_id TEXT,
    selected_model_id TEXT,
    selected_score REAL,
    routing_policy_version TEXT DEFAULT 'adaptive-v1',
    decision_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_telemetry_task ON execution_telemetry(task_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_executor ON execution_telemetry(executor_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_success ON execution_telemetry(success);
CREATE INDEX IF NOT EXISTS idx_routing_task ON routing_decisions(task_id);

-- Phase 4: Portfolio Intelligence Tables
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    repository_full_name TEXT UNIQUE NOT NULL,
    repository_url TEXT NOT NULL,
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    default_branch TEXT NOT NULL,
    description TEXT,
    vision TEXT,
    status TEXT DEFAULT 'MANAGED',
    importance TEXT DEFAULT 'MEDIUM',
    priority_score REAL DEFAULT 0.0,
    health TEXT DEFAULT 'UNKNOWN',
    ci_health REAL,
    security_health REAL,
    test_health REAL,
    documentation_health REAL,
    maintenance_health REAL,
    technical_debt REAL,
    recent_activity TIMESTAMP,
    last_scanned_at TIMESTAMP,
    last_worked_at TIMESTAMP,
    roadmap_version TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_health_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    overall_health TEXT,
    security_health REAL,
    test_health REAL,
    documentation_health REAL,
    maintenance_health REAL,
    activity_health REAL,
    technical_debt REAL,
    ci_health REAL,
    roadmap_health REAL,
    confidence REAL DEFAULT 1.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_roadmaps (
    roadmap_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    version TEXT NOT NULL,
    vision TEXT,
    milestones TEXT,
    objectives TEXT,
    dependencies TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio_tasks (
    task_id TEXT PRIMARY KEY,
    canonical_task_id TEXT,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    repository_full_name TEXT,
    title TEXT NOT NULL,
    description TEXT,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'unknown',
    source_id TEXT NOT NULL,
    source_url TEXT,
    priority REAL DEFAULT 0.0,
    confidence REAL DEFAULT 1.0,
    risk TEXT DEFAULT 'LOW',
    estimated_minutes INTEGER,
    dependencies TEXT,
    required_capabilities TEXT,
    status TEXT DEFAULT 'DISCOVERED',
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    item_type TEXT NOT NULL,
    rank INTEGER NOT NULL,
    score REAL NOT NULL,
    reasons TEXT,
    evidence TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_plans (
    plan_id TEXT PRIMARY KEY,
    date TEXT NOT NULL UNIQUE,
    selected_projects TEXT,
    selected_tasks TEXT,
    execution_order TEXT,
    estimated_work TEXT,
    risk TEXT,
    budget TEXT,
    reasons TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio_evidence (
    evidence_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    task_id TEXT REFERENCES portfolio_tasks(task_id),
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT,
    source_url TEXT,
    observation TEXT NOT NULL,
    severity TEXT DEFAULT 'UNKNOWN',
    confidence REAL DEFAULT 1.0,
    metadata TEXT,
    expires_at TIMESTAMP,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Phase 4 Indexes
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_priority ON projects(priority_score);
CREATE INDEX IF NOT EXISTS idx_portfolio_tasks_project ON portfolio_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_tasks_status ON portfolio_tasks(status);
CREATE INDEX IF NOT EXISTS idx_portfolio_evidence_project ON portfolio_evidence(project_id);

CREATE INDEX IF NOT EXISTS idx_telemetry_executor ON execution_telemetry(executor_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_task_type ON execution_telemetry(task_type);
CREATE INDEX IF NOT EXISTS idx_telemetry_created ON execution_telemetry(created_at);
CREATE INDEX IF NOT EXISTS idx_routing_task ON routing_decisions(task_id);
CREATE INDEX IF NOT EXISTS idx_routing_workflow ON routing_decisions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_routing_executor ON routing_decisions(selected_executor_id);
CREATE INDEX IF NOT EXISTS idx_routing_created ON routing_decisions(created_at);
"""

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self):
        """Ensure the directory for the database exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _init_db(self):
        """Initialize the database schema."""
        try:
            conn = self.get_connection()
            try:
                # Phase 5 Migration: Preserve existing learning history
                # Ensure we do not drop 'knowledge_items', 'lessons', 'benchmarks', 'failures'
                conn.executescript(SCHEMA)
                # Apply migrations conditionally
                for col_query in [
                    "ALTER TABLE workflows ADD COLUMN worker_id TEXT",
                    "ALTER TABLE workflows ADD COLUMN lease_expires_at TIMESTAMP",
                    "ALTER TABLE execution_telemetry ADD COLUMN task_type TEXT",
                    "ALTER TABLE execution_telemetry ADD COLUMN tests_passed BOOLEAN",
                    "ALTER TABLE execution_telemetry ADD COLUMN review_passed BOOLEAN",
                    "ALTER TABLE execution_telemetry ADD COLUMN security_passed BOOLEAN",
                    "ALTER TABLE execution_telemetry ADD COLUMN artifact_valid BOOLEAN",
                    "ALTER TABLE execution_telemetry ADD COLUMN human_approved BOOLEAN",
                    "ALTER TABLE portfolio_tasks ADD COLUMN canonical_task_id TEXT",
                    "ALTER TABLE portfolio_tasks ADD COLUMN repository_full_name TEXT",
                    "ALTER TABLE portfolio_tasks ADD COLUMN source_type TEXT DEFAULT 'unknown'",
                    "ALTER TABLE portfolio_tasks ADD COLUMN source_url TEXT",
                    "ALTER TABLE portfolio_tasks ADD COLUMN confidence REAL DEFAULT 1.0",
                    "ALTER TABLE portfolio_tasks ADD COLUMN estimated_minutes INTEGER",
                    "ALTER TABLE portfolio_evidence ADD COLUMN source_url TEXT",
                    "ALTER TABLE portfolio_evidence ADD COLUMN severity TEXT DEFAULT 'UNKNOWN'",
                    "ALTER TABLE portfolio_evidence ADD COLUMN expires_at TIMESTAMP",
                    # Phase 6 migrations
                    "ALTER TABLE evolution_proposals ADD COLUMN target_type TEXT",
                    "ALTER TABLE evolution_proposals ADD COLUMN target_id TEXT",
                    "ALTER TABLE evolution_proposals ADD COLUMN current_version TEXT",
                    "ALTER TABLE evolution_proposals ADD COLUMN candidate_version TEXT",
                    "ALTER TABLE evolution_proposals ADD COLUMN hypothesis_json TEXT",
                    "ALTER TABLE evolution_proposals ADD COLUMN experiment_id TEXT",
                    "ALTER TABLE evolution_proposals ADD COLUMN rolled_back_at TIMESTAMP",
                    "ALTER TABLE evolution_proposals ADD COLUMN rollback_version TEXT",
                ]:
                    try:
                        conn.execute(col_query)
                    except sqlite3.OperationalError:
                        pass # Columns already exist
                conn.commit()
            finally:
                conn.close()
            logger.info("database_initialized", path=self.db_path)
        except sqlite3.Error as e:
            logger.error("database_initialization_failed", error=str(e), path=self.db_path)
            raise

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection. Caller is responsible for closing it."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, query: str, params: tuple = ()) -> None:
        """Execute a query and commit."""
        conn = self.get_connection()
        try:
            conn.execute(query, params)
            conn.commit()
        finally:
            conn.close()

    def fetchall(self, query: str, params: tuple = ()) -> list:
        """Execute a query and fetch all results."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def record_execution_telemetry(
        self,
        task_id: str,
        workflow_id: str,
        executor_id: str,
        success: bool,
        agent_id: str | None = None,
        task_type: str | None = None,
        provider_id: str | None = None,
        model_id: str | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
        duration_ms: float = 0.0,
        retry_count: int = 0,
        fallback_used: bool = False,
        failure_class: str | None = None,
        cost_usd: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        quality_score: float | None = None,
        tests_passed: bool | None = None,
        review_passed: bool | None = None,
        security_passed: bool | None = None,
        artifact_valid: bool | None = None,
        human_approved: bool | None = None,
    ) -> None:
        """Record an execution outcome to the telemetry table."""
        query = """
            INSERT INTO execution_telemetry (
                task_id, workflow_id, agent_id, task_type, executor_id, provider_id, model_id,
                started_at, completed_at, duration_ms, success, retry_count,
                fallback_used, failure_class, cost_usd, input_tokens, output_tokens,
                quality_score, tests_passed, review_passed, security_passed,
                artifact_valid, human_approved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(
            query,
            (
                task_id,
                workflow_id,
                agent_id,
                task_type,
                executor_id,
                provider_id,
                model_id,
                started_at,
                completed_at,
                duration_ms,
                1 if success else 0,
                retry_count,
                1 if fallback_used else 0,
                failure_class,
                cost_usd,
                input_tokens,
                output_tokens,
                quality_score,
                1 if tests_passed else (0 if tests_passed is False else None),
                1 if review_passed else (0 if review_passed is False else None),
                1 if security_passed else (0 if security_passed is False else None),
                1 if artifact_valid else (0 if artifact_valid is False else None),
                1 if human_approved else (0 if human_approved is False else None),
            ),
        )

    def record_routing_decision(
        self,
        task_id: str,
        workflow_id: str,
        selected_executor_id: str,
        selected_score: float,
        decision_reason: str,
        agent_id: str | None = None,
        task_type: str | None = None,
        requirements_json: str | None = None,
        candidate_rankings_json: str | None = None,
        selected_provider_id: str | None = None,
        selected_model_id: str | None = None,
        routing_policy_version: str = "adaptive-v1",
    ) -> None:
        """Persists a routing decision for explainability and auditability."""
        query = """
            INSERT INTO routing_decisions (
                task_id, workflow_id, agent_id, task_type, requirements_json,
                candidate_rankings_json, selected_executor_id, selected_provider_id,
                selected_model_id, selected_score, routing_policy_version,
                decision_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute(
            query,
            (
                task_id,
                workflow_id,
                agent_id,
                task_type,
                requirements_json,
                candidate_rankings_json,
                selected_executor_id,
                selected_provider_id,
                selected_model_id,
                selected_score,
                routing_policy_version,
                decision_reason,
            ),
        )

    def get_routing_decisions(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """Retrieve recent routing decisions."""
        query = """
            SELECT id, task_id, workflow_id, agent_id, task_type,
                   requirements_json, candidate_rankings_json, selected_executor_id,
                   selected_provider_id, selected_model_id, selected_score,
                   routing_policy_version, decision_reason, created_at
            FROM routing_decisions
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        rows = self.fetchall(query, (limit, offset))
        return [dict(r) for r in rows]

    def get_routing_decision(self, task_id: str) -> dict[str, Any] | None:
        """Get routing decision for a specific task."""
        query = """
            SELECT * FROM routing_decisions WHERE task_id = ? ORDER BY id DESC LIMIT 1
        """
        rows = self.fetchall(query, (task_id,))
        return dict(rows[0]) if rows else None

    def get_executor_stats(self, executor_id: str | None = None) -> dict[str, dict[str, float | int]]:
        """Retrieve aggregated execution statistics per executor."""
        if executor_id:
            query = """
                SELECT executor_id,
                       COUNT(*) as total_runs,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_runs,
                       AVG(duration_ms) as avg_duration_ms,
                       AVG(cost_usd) as avg_cost_usd,
                       AVG(COALESCE(quality_score, 1.0)) as avg_quality_score,
                       SUM(CASE WHEN fallback_used = 1 THEN 1 ELSE 0 END) as fallback_count
                FROM execution_telemetry
                WHERE executor_id = ?
                GROUP BY executor_id
            """
            rows = self.fetchall(query, (executor_id,))
        else:
            query = """
                SELECT executor_id,
                       COUNT(*) as total_runs,
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_runs,
                       AVG(duration_ms) as avg_duration_ms,
                       AVG(cost_usd) as avg_cost_usd,
                       AVG(COALESCE(quality_score, 1.0)) as avg_quality_score,
                       SUM(CASE WHEN fallback_used = 1 THEN 1 ELSE 0 END) as fallback_count
                FROM execution_telemetry
                GROUP BY executor_id
            """
            rows = self.fetchall(query)

        stats: dict[str, dict[str, float | int]] = {}
        for row in rows:
            eid = row["executor_id"]
            total = int(row["total_runs"]) if row["total_runs"] is not None else 0
            successes = int(row["successful_runs"]) if row["successful_runs"] is not None else 0
            rate = (successes / total) if total > 0 else 0.0
            fallbacks = int(row["fallback_count"]) if row["fallback_count"] is not None else 0
            stats[eid] = {
                "total_runs": total,
                "successful_runs": successes,
                "success_rate": rate,
                "avg_duration_ms": float(row["avg_duration_ms"] or 0.0),
                "avg_cost_usd": float(row["avg_cost_usd"] or 0.0),
                "avg_quality_score": float(row["avg_quality_score"] or 1.0),
                "fallback_count": fallbacks,
                "fallback_rate": (fallbacks / total) if total > 0 else 0.0,
            }
        return stats

    def get_task_type_stats(
        self, task_type: str | None = None, executor_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve task-specific historical statistics."""
        conditions = []
        params: list[Any] = []
        if task_type:
            conditions.append("task_type = ?")
            params.append(task_type)
        if executor_id:
            conditions.append("executor_id = ?")
            params.append(executor_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT executor_id,
                   COALESCE(task_type, 'general') as task_type,
                   COUNT(*) as total_runs,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_runs,
                   AVG(duration_ms) as avg_duration_ms,
                   AVG(COALESCE(quality_score, 1.0)) as avg_quality_score,
                   SUM(CASE WHEN tests_passed = 1 THEN 1 ELSE 0 END) as tests_passed_count,
                   SUM(CASE WHEN review_passed = 1 THEN 1 ELSE 0 END) as review_passed_count
            FROM execution_telemetry
            {where_clause}
            GROUP BY executor_id, task_type
        """
        rows = self.fetchall(query, tuple(params))
        results = []
        for r in rows:
            total = int(r["total_runs"])
            succ = int(r["successful_runs"])
            results.append({
                "executor_id": r["executor_id"],
                "task_type": r["task_type"],
                "total_runs": total,
                "successful_runs": succ,
                "success_rate": (succ / total) if total > 0 else 0.0,
                "avg_duration_ms": float(r["avg_duration_ms"] or 0.0),
                "avg_quality_score": float(r["avg_quality_score"] or 1.0),
                "tests_passed_count": int(r["tests_passed_count"] or 0),
                "review_passed_count": int(r["review_passed_count"] or 0),
            })
        return results

    def get_recency_weighted_stats(
        self,
        executor_id: str,
        half_life_days: float = 7.0,
        task_type: str | None = None,
    ) -> dict[str, float | int]:
        """
        Calculates time-decay recency weighted statistics for an executor.
        Weight formula: w = exp(-ln(2) * delta_days / half_life_days).
        """
        import math
        from datetime import UTC, datetime

        if task_type:
            query = """
                SELECT success, quality_score, duration_ms, cost_usd, COALESCE(started_at, created_at) as created_at
                FROM execution_telemetry
                WHERE executor_id = ? AND task_type = ?
                ORDER BY COALESCE(started_at, created_at) DESC
            """
            rows = self.fetchall(query, (executor_id, task_type))
        else:
            query = """
                SELECT success, quality_score, duration_ms, cost_usd, COALESCE(started_at, created_at) as created_at
                FROM execution_telemetry
                WHERE executor_id = ?
                ORDER BY COALESCE(started_at, created_at) DESC
            """
            rows = self.fetchall(query, (executor_id,))


        if not rows:
            return {
                "total_runs": 0,
                "successful_runs": 0,
                "raw_success_rate": 0.85,
                "weighted_success_rate": 0.85,
                "weighted_quality_score": 0.90,
                "avg_duration_ms": 1000.0,
                "avg_cost_usd": 0.01,
            }

        now = datetime.now(UTC)
        decay_constant = math.log(2.0) / max(half_life_days, 0.1)

        total_weight = 0.0
        weighted_successes = 0.0
        weighted_quality = 0.0
        weighted_duration = 0.0
        weighted_cost = 0.0

        raw_successes = 0

        for r in rows:
            created_str = r["created_at"]
            try:
                created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=UTC)
            except Exception:
                created_dt = now

            delta_days = max((now - created_dt).total_seconds() / 86400.0, 0.0)
            weight = math.exp(-decay_constant * delta_days)

            total_weight += weight
            succ_val = 1.0 if r["success"] else 0.0
            if succ_val == 1.0:
                raw_successes += 1

            weighted_successes += succ_val * weight
            weighted_quality += float(r["quality_score"] or succ_val) * weight
            weighted_duration += float(r["duration_ms"] or 0.0) * weight
            weighted_cost += float(r["cost_usd"] or 0.0) * weight

        total_runs = len(rows)
        weighted_rate = (weighted_successes / total_weight) if total_weight > 0 else 0.85
        weighted_qual = (weighted_quality / total_weight) if total_weight > 0 else 0.90

        return {
            "total_runs": total_runs,
            "successful_runs": raw_successes,
            "raw_success_rate": (raw_successes / total_runs) if total_runs > 0 else 0.0,
            "weighted_success_rate": weighted_rate,
            "weighted_quality_score": weighted_qual,
            "avg_duration_ms": (weighted_duration / total_weight) if total_weight > 0 else 0.0,
            "avg_cost_usd": (weighted_cost / total_weight) if total_weight > 0 else 0.0,
        }

    def get_system_status_summary(self) -> dict[str, Any]:
        """Derives live system status from real workflow and execution state."""
        wf_rows = self.fetchall(
            "SELECT status, COUNT(*) as count FROM workflows GROUP BY status"
        )
        counts = {r["status"].lower(): int(r["count"]) for r in wf_rows}

        active_wf = counts.get("running", 0) + counts.get("pending", 0) + counts.get("initialize", 0) + counts.get("plan", 0) + counts.get("implement", 0)
        failed_wf = counts.get("failed", 0)
        paused_wf = counts.get("paused", 0)
        complete_wf = counts.get("complete", 0)

        # Recent failures
        fail_rows = self.fetchall(
            "SELECT task_id, failure_class, duration_ms, created_at FROM execution_telemetry WHERE success = 0 ORDER BY created_at DESC LIMIT 5"
        )

        return {
            "system_state": "Optimal" if failed_wf == 0 else ("Degraded" if active_wf > 0 else "Needs Attention"),
            "active_workflows": active_wf,
            "failed_workflows": failed_wf,
            "paused_workflows": paused_wf,
            "complete_workflows": complete_wf,
            "recent_failures": [dict(f) for f in fail_rows],
        }

