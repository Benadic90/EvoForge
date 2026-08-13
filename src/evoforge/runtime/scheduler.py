import time
from datetime import UTC, datetime
from typing import Any

import structlog

from evoforge.memory.database import Database
from evoforge.orchestrator.workflows import WorkflowDefinition, WorkflowTask
from evoforge.portfolio.daily_planner import DailyPlanner
from evoforge.portfolio.priority_engine import PortfolioPriorityEngine
from evoforge.portfolio.registry import ProjectRegistry
from evoforge.portfolio.scanner import ProjectScanner
from evoforge.portfolio.task_builder import PortfolioTaskRequirementsBuilder

logger = structlog.get_logger(__name__)

class SchedulerEngine:
    """
    Persistent Cloud Scheduler that delegates bounded work to the queue (SQLite workflows table).
    It does not execute workflows directly; it schedules them.
    """

    def __init__(self, db: Database, gh_client: Any, learning_system: Any = None):
        self.db = db
        self.gh_client = gh_client
        self.learning = learning_system
        self.scheduler_id = "primary_scheduler"
        self._running = False
        
        self.project_registry = ProjectRegistry(db)
        self.scanner = ProjectScanner(db, gh_client, self.project_registry)
        self.priority_engine = PortfolioPriorityEngine(db, self.project_registry)
        self.planner = DailyPlanner(db, self.project_registry)

    def _ensure_state_record(self):
        query = """
        INSERT INTO scheduler_state (scheduler_id, status, version) 
        VALUES (?, 'STOPPED', '1.0')
        ON CONFLICT(scheduler_id) DO NOTHING
        """
        self.db.execute(query, (self.scheduler_id,))

    def _update_state(self, status: str, last_tick: str = None, last_success: str = None, last_failure: str = None, next_run: str = None):
        fields = ["status = ?"]
        params = [status]

        if last_tick:
            fields.append("last_tick = ?")
            params.append(last_tick)
        if last_success:
            fields.append("last_success = ?")
            params.append(last_success)
        if last_failure:
            fields.append("last_failure = ?")
            params.append(last_failure)
        if next_run:
            fields.append("next_run = ?")
            params.append(next_run)

        params.append(self.scheduler_id)
        query = f"UPDATE scheduler_state SET {', '.join(fields)} WHERE scheduler_id = ?"
        self.db.execute(query, tuple(params))

    def get_status(self) -> dict:
        self._ensure_state_record()
        rows = self.db.fetchall("SELECT * FROM scheduler_state WHERE scheduler_id = ?", (self.scheduler_id,))
        return dict(rows[0]) if rows else {}

    def is_paused(self) -> bool:
        status = self.get_status().get("status", "STOPPED")
        return status == "PAUSED"

    def pause(self):
        self._ensure_state_record()
        self._update_state(status="PAUSED")
        logger.warning("scheduler_paused_emergency")

    def resume(self):
        self._ensure_state_record()
        self._update_state(status="RUNNING")
        logger.info("scheduler_resumed")

    def enqueue_portfolio_tasks(self):
        """Scans portfolio, generates plan, and writes workflows to DB for workers."""
        logger.info("scheduler_enqueuing_portfolio_tasks")
        for p in self.project_registry.list():
            if p.status == "MANAGED":
                report, raw_items = self.scanner.scan_project(p.project_id)
                if raw_items:
                    self.priority_engine.generate_backlog(p.project_id, raw_items)

        self.priority_engine.rank_projects()
        self.priority_engine.rank_tasks()

        plan = self.planner.generate_plan()
        if not plan.selected_tasks:
            logger.info("no_portfolio_tasks_to_schedule")
            return

        enqueued_count = 0
        for task_id in plan.execution_order:
            import json

            from evoforge.portfolio.models import PortfolioTask

            rows = self.db.fetchall("SELECT * FROM portfolio_tasks WHERE task_id = ?", (task_id,))
            if not rows:
                continue

            row = dict(rows[0])
            ptask = PortfolioTask(
                task_id=row["task_id"],
                project_id=row["project_id"],
                title=row["title"],
                description=row["description"],
                source=row["source"],
                source_id=row["source_id"],
                priority=row["priority"],
                risk=row["risk"],
                dependencies=json.loads(row["dependencies"]) if row["dependencies"] else [],
                required_capabilities=json.loads(row["required_capabilities"]) if row["required_capabilities"] else [],
                status=row["status"],
            )

            req = PortfolioTaskRequirementsBuilder.build(ptask)
            
            from evoforge.orchestrator.workflows import TaskPriority
            wtask = WorkflowTask(
                id=req.task_id,
                name=ptask.title,
                description=ptask.description,
                priority=TaskPriority.MEDIUM,
                agent_type="developer",
            )
            
            repo_name = ptask.repository_full_name or "unknown/repo"
            wdef = WorkflowDefinition(
                id=f"wf_{plan.plan_id}_{task_id}",
                repo_name=repo_name,
                tasks=[wtask],
                dry_run=False
            )
            
            # Write to workflows table where status='pending'
            # Workers will pick this up.
            try:
                # Need to use the Orchestrator Engine's state initialization logic conceptually here,
                # but we just insert the raw DB record.
                state_snapshot = f'{{"workflow_id": "{wdef.id}", "run_id": "scheduled_{plan.plan_id}", "repository_id": "{repo_name}", "current_stage": "INITIALIZE", "dry_run": false, "attempt_count": 0, "history": []}}'
                
                self.db.execute(
                    """INSERT INTO workflows (id, project, workflow_type, task_description, status, state_snapshot) 
                       VALUES (?, ?, ?, ?, 'pending', ?)
                       ON CONFLICT(id) DO NOTHING""",
                    (wdef.id, ptask.project_id, "portfolio_task", ptask.title, state_snapshot)
                )
                self.db.execute("UPDATE portfolio_tasks SET status = 'QUEUED' WHERE task_id = ?", (task_id,))
                enqueued_count += 1
            except Exception as e:
                logger.error("failed_to_enqueue_task", task_id=task_id, error=str(e))

        logger.info("portfolio_tasks_enqueued", count=enqueued_count)

    def trigger_research(self):
        if self.learning and hasattr(self.learning, 'run_scheduled_research'):
            # The learning system handles creating jobs. We may need to adapt it to create workflows instead.
            # For now, just trigger it to queue research jobs.
            self.learning.run_scheduled_research()

    def run_once(self):
        self._ensure_state_record()
        
        if self.is_paused():
            logger.info("scheduler_is_paused_skipping_tick")
            return

        now_iso = datetime.now(UTC).isoformat()
        self._update_state(status="RUNNING", last_tick=now_iso)

        try:
            self.enqueue_portfolio_tasks()
            self.trigger_research()
            
            self._update_state(status="RUNNING", last_success=datetime.now(UTC).isoformat())
        except Exception as e:
            logger.exception("scheduler_tick_failed", error=str(e))
            self._update_state(status="RUNNING", last_failure=datetime.now(UTC).isoformat())

    def start(self, interval_seconds: int = 3600):
        """Starts the persistent scheduler loop."""
        self._running = True
        logger.info("scheduler_started", interval=interval_seconds)
        
        while self._running:
            self.run_once()
            
            # Wait for next tick, check for pause/stop frequently
            end_time = time.time() + interval_seconds
            while time.time() < end_time and self._running:
                time.sleep(5)
                
    def stop(self):
        self._running = False
        self._update_state(status="STOPPED")
        logger.info("scheduler_stopped")
