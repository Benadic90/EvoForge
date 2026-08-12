from datetime import datetime

import structlog

from .database import Database
from .events import SQLiteEventStore, emitter
from .idempotency import IdempotencyManager
from .obsidian import ObsidianManager
from .state import WorkflowState

logger = structlog.get_logger(__name__)

class MemoryManager:
    def __init__(self, db: Database, obsidian: ObsidianManager):
        self.db = db
        self.obsidian = obsidian
        self.idempotency = IdempotencyManager(db)

    def init_memory_systems(self):
        """Initializes both SQLite and Obsidian systems."""
        self.obsidian.init_vault()
        # Initialize the global event store now that we have a database
        emitter.store = SQLiteEventStore(self.db)
        logger.info("memory_systems_initialized")

    def register_project(self, repo_name: str, url: str, tech_stack: str):
        """Registers a new project across both memory layers."""
        # 1. SQLite: Insert into projects table (assuming we added one, extending schema)
        # For MVP, we'll just log it. In a real scenario, we'd execute a SQL insert here.
        # 2. Obsidian: Create semantic project note
        safe_repo_name = repo_name.replace("/", "_")
        frontmatter = {
            "type": "project",
            "repo": repo_name,
            "url": url,
            "stack": tech_stack,
            "last_scanned": datetime.now().isoformat()
        }
        content = f"# {repo_name}\n\n## Overview\nAuto-discovered project.\n\n## Current Status\nTracking active."
        self.obsidian.write_project_note(safe_repo_name, content, frontmatter)
        
        logger.info("project_registered", repo=repo_name)

    def log_daily_summary(self, summary_md: str):
        """Saves a daily summary to Obsidian."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.obsidian.write_daily_note(today, summary_md)
        logger.info("daily_summary_logged", date=today)

    def record_workflow_checkpoint(self, workflow_state: WorkflowState):
        """Records a hard state checkpoint in SQLite."""
        try:
            state_str = workflow_state.current_stage.value
            context_dict = workflow_state.model_dump()
            
            conn = self.db.get_connection()
            try:
                # Ensure date objects are serialized properly
                # We use model_dump_json for proper datetimes
                context_json = workflow_state.model_dump_json()
                
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE workflows SET status = ?, state_snapshot = ? WHERE id = ?",
                    (state_str, context_json, workflow_state.workflow_id)
                )
                conn.commit()
                logger.debug("checkpoint_saved", workflow_id=workflow_state.workflow_id, state=state_str)
            finally:
                conn.close()
        except Exception as e:
            logger.error("checkpoint_save_failed", workflow_id=workflow_state.workflow_id, error=str(e))
            raise
