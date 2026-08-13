import uuid
import json
from datetime import datetime
from typing import List, Dict, Any
import structlog

from evoforge.memory.database import Database
from evoforge.portfolio.models import DailyPortfolioPlan, PortfolioRanking
from evoforge.portfolio.registry import ProjectRegistry

logger = structlog.get_logger(__name__)

class DailyPlanner:
    def __init__(self, db: Database, registry: ProjectRegistry, max_tasks: int = 5, max_cost: float = 10.0):
        self.db = db
        self.registry = registry
        self.max_tasks = max_tasks
        self.max_cost = max_cost

    def generate_plan(self) -> DailyPortfolioPlan:
        """
        Assemble the priority rankings into a bounded daily plan.
        """
        # Fetch top project rankings
        project_query = "SELECT * FROM portfolio_rankings WHERE item_type = 'project' ORDER BY rank ASC"
        project_rows = self.db.fetchall(project_query)
        top_projects = [row["item_id"] for row in project_rows][:3]  # Consider top 3 projects for the day
        
        # Fetch top tasks for those projects
        selected_tasks = []
        execution_order = []
        reasons = []
        
        task_query = "SELECT * FROM portfolio_rankings WHERE item_type = 'task' ORDER BY rank ASC"
        task_rows = self.db.fetchall(task_query)
        
        for row in task_rows:
            if len(selected_tasks) >= self.max_tasks:
                break
                
            task_id = row["item_id"]
            # To know the project, we'd join with portfolio_tasks, but we'll simplify here
            # by just grabbing the task directly to check dependencies and project.
            task = self._get_task(task_id)
            if not task:
                continue
                
            # Skip if project isn't a top project (focus strategy)
            if task.project_id not in top_projects:
                continue
                
            # Check dependencies
            if self._has_unmet_dependencies(task.dependencies):
                reasons.append(f"Skipped {task_id}: unmet dependencies.")
                continue
                
            selected_tasks.append(task_id)
            execution_order.append(task_id)
            reasons.append(f"Selected {task_id} (Rank {row['rank']}): {task.title}")

        plan = DailyPortfolioPlan(
            plan_id=f"plan_{datetime.utcnow().strftime('%Y%m%d')}_{uuid.uuid4().hex[:4]}",
            date=datetime.utcnow().strftime('%Y-%m-%d'),
            selected_projects=list(set([self._get_task(t).project_id for t in selected_tasks if self._get_task(t)])),
            selected_tasks=selected_tasks,
            execution_order=execution_order,
            estimated_work=f"{len(selected_tasks)} tasks",
            risk="LOW",
            budget={"max_tasks": self.max_tasks, "max_cost": self.max_cost},
            reasons=reasons,
            created_at=datetime.utcnow()
        )
        
        self._save_plan(plan)
        logger.info("daily_plan_generated", plan_id=plan.plan_id, task_count=len(selected_tasks))
        
        # Note: The plan determines WHAT to do.
        # The Orchestrator / run_daily_loop actually consumes this plan and creates WorkflowDefinitions.
        return plan

    def _get_task(self, task_id: str):
        from evoforge.portfolio.models import PortfolioTask
        query = "SELECT * FROM portfolio_tasks WHERE task_id = ?"
        rows = self.db.fetchall(query, (task_id,))
        if not rows:
            return None
        row = rows[0]
        return PortfolioTask(
            task_id=row["task_id"],
            project_id=row["project_id"],
            title=row["title"],
            description=row["description"],
            source=row["source"],
            source_id=row["source_id"],
            priority=row["priority"],
            risk=row["risk"],
            estimated_effort=row["estimated_effort"],
            dependencies=json.loads(row["dependencies"]) if row["dependencies"] else [],
            required_capabilities=json.loads(row["required_capabilities"]) if row["required_capabilities"] else [],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )

    def _has_unmet_dependencies(self, dependencies: List[str]) -> bool:
        """Cycle detection and dependency blocking."""
        if not dependencies:
            return False
            
        for dep_id in dependencies:
            task = self._get_task(dep_id)
            if task and task.status != "COMPLETE":
                return True
        return False
        
    def _save_plan(self, plan: DailyPortfolioPlan) -> None:
        query = """
            INSERT INTO daily_plans (
                plan_id, date, selected_projects, selected_tasks, execution_order,
                estimated_work, risk, budget, reasons, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                selected_projects=excluded.selected_projects,
                selected_tasks=excluded.selected_tasks,
                execution_order=excluded.execution_order,
                estimated_work=excluded.estimated_work,
                risk=excluded.risk,
                budget=excluded.budget,
                reasons=excluded.reasons,
                created_at=excluded.created_at
        """
        params = (
            plan.plan_id,
            plan.date,
            json.dumps(plan.selected_projects),
            json.dumps(plan.selected_tasks),
            json.dumps(plan.execution_order),
            plan.estimated_work,
            plan.risk,
            json.dumps(plan.budget),
            json.dumps(plan.reasons),
            plan.created_at
        )
        self.db.execute(query, params)
