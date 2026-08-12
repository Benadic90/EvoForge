import sqlite3
import os
import structlog
from pathlib import Path

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
