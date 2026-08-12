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

    def record_execution_telemetry(
        self,
        task_id: str,
        workflow_id: str,
        executor_id: str,
        success: bool,
        **kwargs,
    ) -> None:
        """Records execution telemetry for router scoring."""
        self.db.record_execution_telemetry(
            task_id=task_id,
            workflow_id=workflow_id,
            executor_id=executor_id,
            success=success,
            **kwargs,
        )

    def record_routing_decision(
        self,
        task_id: str,
        workflow_id: str,
        selected_executor_id: str,
        selected_score: float,
        decision_reason: str,
        **kwargs,
    ) -> None:
        """Persists a routing decision for explainability and auditability."""
        self.db.record_routing_decision(
            task_id=task_id,
            workflow_id=workflow_id,
            selected_executor_id=selected_executor_id,
            selected_score=selected_score,
            decision_reason=decision_reason,
            **kwargs,
        )

    def get_routing_decisions(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """Retrieves recent routing decisions."""
        return self.db.get_routing_decisions(limit=limit, offset=offset)

    def get_routing_decision(self, task_id: str) -> dict | None:
        """Gets routing decision by task id."""
        return self.db.get_routing_decision(task_id)

    def get_executor_stats(self, executor_id: str | None = None) -> dict[str, dict[str, float | int]]:
        """Returns empirical stats per executor."""
        return self.db.get_executor_stats(executor_id)

    def get_task_type_stats(
        self, task_type: str | None = None, executor_id: str | None = None
    ) -> list[dict]:
        """Returns task-type specific performance statistics."""
        return self.db.get_task_type_stats(task_type=task_type, executor_id=executor_id)

    def get_recency_weighted_stats(
        self,
        executor_id: str,
        half_life_days: float = 7.0,
        task_type: str | None = None,
    ) -> dict[str, float | int]:
        """Returns recency-decay weighted statistics for an executor."""
        return self.db.get_recency_weighted_stats(
            executor_id=executor_id,
            half_life_days=half_life_days,
            task_type=task_type,
        )


