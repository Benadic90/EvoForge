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


            rows = self.db.fetchall("SELECT * FROM portfolio_tasks WHERE task_id = ?", (task_id,))
            if not rows:
                continue

            row = dict(rows[0])
            ptask = self.priority_engine._row_to_task(row)

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

    def execute_pending_workflows(self):
        """Processes pending workflows using the embedded OrchestratorEngine."""
        from evoforge.agents.factory import build_agent_registry
        from evoforge.github_integration.git_workflow import AutonomousGitWorkflow
        from evoforge.memory.manager import MemoryManager
        from evoforge.model_router.executors import create_default_executor_registry
        from evoforge.model_router.routing import ExecutorRouter
        from evoforge.orchestrator.engine import OrchestratorEngine
        from evoforge.orchestrator.workflows import TaskPriority, WorkflowDefinition, WorkflowTask
        from evoforge.utils.config import load_config
        
        cfg = load_config()
        executor_registry = create_default_executor_registry(cfg, db=self.db)
        router = ExecutorRouter(executor_registry)
        agent_registry = build_agent_registry(None, None)
        orchestrator = OrchestratorEngine(MemoryManager(self.db, ""), agent_registry, router)
        
        pending_rows = self.db.fetchall("SELECT * FROM workflows WHERE status = 'pending' ORDER BY created_at ASC LIMIT 5")
        if not pending_rows:
            return
            
        logger.info("scheduler_executing_pending_workflows", count=len(pending_rows))
        for row in pending_rows:
            wf_id = row["id"]
            project_id = row["project"]
            task_desc = row["task_description"] or "Automated Workflow Task"
            
            task_id = "ptask_" + wf_id.split("_ptask_")[-1] if "_ptask_" in wf_id else wf_id
            
            ptask_rows = self.db.fetchall("SELECT * FROM portfolio_tasks WHERE task_id = ?", (task_id,))
            repo_name = "unknown/repo"
            task_title = task_desc
            if ptask_rows:
                pt_row = dict(ptask_rows[0])
                repo_name = pt_row.get("repository_full_name") or repo_name
                task_title = pt_row.get("title") or task_title
                
            wtask = WorkflowTask(
                id=task_id,
                name=task_title,
                description=task_desc,
                priority=TaskPriority.MEDIUM,
                agent_type="developer",
            )
            
            wdef = WorkflowDefinition(
                id=wf_id,
                repo_name=repo_name,
                tasks=[wtask],
                dry_run=False
            )
            
            try:
                self.db.execute("UPDATE workflows SET status = 'running' WHERE id = ?", (wf_id,))
                self.db.execute("UPDATE portfolio_tasks SET status = 'RUNNING' WHERE task_id = ?", (task_id,))
                
                orchestrator.execute_workflow(wdef)
                
                self.db.execute("UPDATE workflows SET status = 'completed' WHERE id = ?", (wf_id,))
                self.db.execute("UPDATE portfolio_tasks SET status = 'COMPLETED' WHERE task_id = ?", (task_id,))
                
                # Publish Git PR if changes produced
                git_flow = AutonomousGitWorkflow(db=self.db)
                solution = wtask.context.get("result", task_desc)
                pr_url = git_flow.publish_task_solution(
                    repo_full_name=repo_name,
                    task_id=task_id,
                    task_title=task_title,
                    task_description=task_desc,
                    solution_summary=solution,
                )
                if pr_url:
                    logger.info("scheduler_pr_published", url=pr_url)
            except Exception as e:
                logger.error("scheduler_workflow_execution_failed", workflow_id=wf_id, error=str(e))
                self.db.execute("UPDATE workflows SET status = 'failed' WHERE id = ?", (wf_id,))
                self.db.execute("UPDATE portfolio_tasks SET status = 'FAILED' WHERE task_id = ?", (task_id,))

    def trigger_research(self):
        if self.learning and hasattr(self.learning, 'run_scheduled_research'):
            self.learning.run_scheduled_research()

    def run_once(self):
        self._ensure_state_record()
        
        if self.is_paused():
            logger.info("scheduler_is_paused_skipping_tick")
            return

        now_iso = datetime.now(UTC).isoformat()
        self._update_state(status="RUNNING", last_tick=now_iso)

        if not self.gh_client or getattr(self.gh_client, 'token', None) is None:
            logger.warning("GITHUB_UNAVAILABLE")
            self._update_state(status="RUNNING", last_failure=now_iso)
            return

        try:
            self.enqueue_portfolio_tasks()
            self.execute_pending_workflows()
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
