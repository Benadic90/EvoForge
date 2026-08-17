import json
import uuid
from datetime import UTC, datetime

import structlog

# Phase 5 Imports
from evoforge.learning.models import ResearchJob
from evoforge.learning.research_engine import ResearchScheduler
from evoforge.learning.skill_registry import SkillRegistry
from evoforge.memory.database import Database
from evoforge.portfolio.models import DailyPortfolioPlan
from evoforge.portfolio.registry import ProjectRegistry

logger = structlog.get_logger(__name__)

class DailyPlanner:
    def __init__(self, db: Database, registry: ProjectRegistry, max_tasks: int = 5, max_cost: float = 10.0):
        self.db = db
        self.registry = registry
        self.max_tasks = max_tasks
        self.max_cost = max_cost
        
        # Phase 5 Dependencies
        # In a real DI framework these would be injected.
        self.skill_registry = SkillRegistry(db, None) # Obsidian not strictly needed for this check
        self.research_scheduler = ResearchScheduler(db)

    def generate_plan(self) -> DailyPortfolioPlan:
        """
        Assemble the priority rankings into a bounded daily plan.
        Integrates Phase 5: Checks required capabilities against actual skills, triggering gaps/research if needed.
        """
        # Fetch top project rankings
        project_query = "SELECT * FROM portfolio_rankings WHERE item_type = 'project' ORDER BY rank ASC"
        project_rows = self.db.fetchall(project_query)
        top_projects = [row["item_id"] for row in project_rows][:3]
        if not top_projects:
            # Fallback to active managed projects from registry
            top_projects = [p.project_id for p in self.registry.list() if p.status in ("MANAGED", "ACTIVE")]
        
        selected_tasks = []
        execution_order = []
        reasons = []
        
        if not top_projects:
            reasons.append("No active or managed projects registered in portfolio.")

        task_query = "SELECT * FROM portfolio_rankings WHERE item_type = 'task' ORDER BY rank ASC"
        task_rows = self.db.fetchall(task_query)
        if not task_rows:
            # If rankings haven't run, check uncompleted tasks directly
            task_rows = [{"item_id": r["task_id"], "rank": idx + 1} for idx, r in enumerate(self.db.fetchall("SELECT task_id FROM portfolio_tasks WHERE status NOT IN ('COMPLETED', 'CANCELLED') ORDER BY priority DESC LIMIT ?", (self.max_tasks * 2,)))]
            if not task_rows:
                reasons.append("Backlog is empty; no uncompleted tasks found.")
        
        for row in task_rows:
            if len(selected_tasks) >= self.max_tasks:
                break
                
            task_id = row["item_id"]
            task = self._get_task(task_id)
            if not task:
                continue
                
            if task.project_id not in top_projects:
                reasons.append(f"Skipped {task_id}: Project {task.project_id} is not in top priority projects.")
                continue
                
            if self._has_unmet_dependencies(task.dependencies):
                reasons.append(f"Skipped {task_id}: unmet dependencies.")
                continue
                
            # Phase 5 Integration: Check required capabilities
            capabilities_met = True
            for req_cap in task.required_capabilities:
                if not self._check_capability_across_agents(req_cap):
                    logger.warning("portfolio_task_missing_capability", task_id=task_id, capability=req_cap)
                    reasons.append(f"Skipped {task_id}: Missing capability {req_cap}. Triggered Phase 5 Research.")
                    
                    # Trigger Phase 5 Learning Loop
                    gap_id = str(uuid.uuid4())
                    self._create_skill_gap(gap_id, req_cap, task.project_id, task_id)
                    
                    job = ResearchJob(
                        research_id=str(uuid.uuid4()),
                        agent_id="ResearchAgent",
                        project_id=task.project_id,
                        task_id=task_id,
                        domain="portfolio_requirement",
                        topic=req_cap,
                        query=f"Research technical requirements, documentation, and best practices for: {req_cap}",
                        reason=f"Required by PortfolioTask {task_id}",
                        priority=0.9,
                        skill_gap_id=gap_id
                    )
                    self.research_scheduler.schedule_research(job)
                    capabilities_met = False
                    break
                    
            if not capabilities_met:
                continue
                
            selected_tasks.append(task_id)
            execution_order.append(task_id)
            reasons.append(f"Selected {task_id} (Rank {row['rank']}): {task.title}")

        now_utc = datetime.now(UTC)
        plan = DailyPortfolioPlan(
            plan_id=f"plan_{now_utc.strftime('%Y%m%d')}_{uuid.uuid4().hex[:4]}",
            date=now_utc.strftime('%Y-%m-%d'),
            selected_projects=list(set([self._get_task(t).project_id for t in selected_tasks if self._get_task(t)])),
            selected_tasks=selected_tasks,
            execution_order=execution_order,
            estimated_work=f"{len(selected_tasks)} tasks",
            risk="LOW",
            budget={"max_tasks": self.max_tasks, "max_cost": self.max_cost},
            reasons=reasons,
            created_at=now_utc
        )
        
        self._save_plan(plan)
        logger.info("daily_plan_generated", plan_id=plan.plan_id, task_count=len(selected_tasks))
        return plan

    def _check_capability_across_agents(self, capability: str) -> bool:
        """Checks if ANY agent has the required skill with decent confidence."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM skills WHERE skill_name LIKE ? AND status = 'active' AND confidence > 0.5",
                (f"%{capability}%",)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()
            
    def _create_skill_gap(self, gap_id: str, skill: str, project_id: str, task_id: str):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            # Simple check if one is already open
            cursor.execute("SELECT 1 FROM skill_gaps WHERE skill_id = ? AND status = 'OPEN'", (skill,))
            if cursor.fetchone():
                return
                
            cursor.execute(
                """
                INSERT INTO skill_gaps (skill_gap_id, agent_id, skill_id, project_id, severity, confidence, status)
                VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
                """,
                (gap_id, "SYSTEM", skill, project_id, "HIGH", 1.0)
            )
            conn.commit()
        finally:
            conn.close()

    def _get_task(self, task_id: str):
        from evoforge.portfolio.models import PortfolioTask
        query = "SELECT * FROM portfolio_tasks WHERE task_id = ?"
        rows = self.db.fetchall(query, (task_id,))
        if not rows:
            return None
        row = dict(rows[0])
        return PortfolioTask(
            task_id=row["task_id"],
            canonical_task_id=row.get("canonical_task_id"),
            project_id=row["project_id"],
            repository_full_name=row.get("repository_full_name"),
            title=row["title"],
            description=row["description"],
            source=row["source"],
            source_type=row.get("source_type", "unknown"),
            source_id=row["source_id"],
            source_url=row.get("source_url"),
            priority=row["priority"],
            confidence=row.get("confidence", 1.0),
            risk=row["risk"],
            estimated_minutes=row.get("estimated_minutes"),
            dependencies=json.loads(row["dependencies"]) if row["dependencies"] else [],
            required_capabilities=json.loads(row["required_capabilities"]) if row["required_capabilities"] else [],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )

    def _has_unmet_dependencies(self, dependencies: list[str]) -> bool:
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
