import sqlite3
from pathlib import Path

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
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    domain TEXT NOT NULL,
    content TEXT,
    source TEXT,
    source_type TEXT,
    source_url TEXT,
    publication_date TEXT,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence REAL DEFAULT 0.0,
    verification_status TEXT DEFAULT 'unverified',
    lifecycle_state TEXT DEFAULT 'discovered',
    applicable_agents TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Research items (inbox/pipeline)
CREATE TABLE IF NOT EXISTS research_items (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    topic TEXT NOT NULL,
    domain TEXT NOT NULL,
    volatility TEXT DEFAULT 'medium',
    trigger TEXT DEFAULT 'scheduled',
    status TEXT DEFAULT 'pending',
    findings TEXT,
    sources TEXT,
    scheduled_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Engineering lessons from real work
CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    problem TEXT NOT NULL,
    evidence TEXT,
    evidence_count INTEGER DEFAULT 0,
    learning TEXT NOT NULL,
    correction TEXT,
    status TEXT DEFAULT 'unverified',
    applied_to_version TEXT,
    regression_result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Benchmark suites and results
CREATE TABLE IF NOT EXISTS benchmarks (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    suite_name TEXT NOT NULL,
    task_count INTEGER,
    baseline_score REAL,
    current_score REAL,
    improvement_pct REAL,
    last_run TIMESTAMP,
    results TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                conn.executescript(SCHEMA)
                # Apply migrations conditionally
                try:
                    conn.execute("ALTER TABLE workflows ADD COLUMN worker_id TEXT")
                    conn.execute("ALTER TABLE workflows ADD COLUMN lease_expires_at TIMESTAMP")
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
        # Check_same_thread=False is needed if we use connection pools or pass connections between threads, 
        # though usually it's better to create a new connection per thread in SQLite.
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
