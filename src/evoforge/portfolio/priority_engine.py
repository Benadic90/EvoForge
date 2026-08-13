import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import structlog

from evoforge.memory.database import Database
from evoforge.portfolio.models import (
    ProjectProfile, PortfolioTask, PortfolioRanking, PortfolioEvidence
)
from evoforge.portfolio.registry import ProjectRegistry

logger = structlog.get_logger(__name__)

class PortfolioPriorityEngine:
    def __init__(self, db: Database, registry: ProjectRegistry):
        self.db = db
        self.registry = registry
        # Configurable weights (in a real system, these would come from config)
        self.weights = {
            "security_severity": 0.4,
            "roadmap_importance": 0.3,
            "technical_debt": 0.15,
            "inactivity": 0.05,
            "user_impact": 0.1
        }

    def generate_backlog(self, project_id: str, raw_items: List[Dict[str, Any]]) -> List[PortfolioTask]:
        """
        Normalize diverse items (GH issues, CI failures) into PortfolioTasks.
        raw_items is a list of dicts with keys: source, source_id, title, description,
        priority_hint, risk_hint, etc.
        """
        tasks = []
        for item in raw_items:
            task = PortfolioTask(
                task_id=f"ptask_{uuid.uuid4().hex[:8]}",
                project_id=project_id,
                title=item.get("title", "Untitled Task"),
                description=item.get("description", ""),
                source=item.get("source", "unknown"),
                source_id=str(item.get("source_id", uuid.uuid4())),
                priority=float(item.get("priority_hint", 0.0)),
                risk=item.get("risk_hint", "LOW"),
                estimated_effort=item.get("effort_hint", "UNKNOWN"),
                dependencies=item.get("dependencies", []),
                required_capabilities=item.get("required_capabilities", []),
                status="NOT_STARTED",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata=item.get("metadata", {})
            )
            self._save_task(task)
            tasks.append(task)
            
        logger.info("backlog_generated", project_id=project_id, task_count=len(tasks))
        return tasks

    def rank_projects(self) -> List[PortfolioRanking]:
        """Rank all active projects based on priority scoring model."""
        projects = [p for p in self.registry.list() if p.status == "ACTIVE"]
        rankings = []
        
        for p in projects:
            score, reasons, evidence = self._calculate_project_score(p)
            # Update project score in registry
            p.priority_score = score
            self.registry.register(p)
            
            rankings.append({
                "project": p,
                "score": score,
                "reasons": reasons,
                "evidence": evidence
            })
            
        # Sort descending by score
        rankings.sort(key=lambda x: x["score"], reverse=True)
        
        final_rankings = []
        for idx, r in enumerate(rankings):
            ranking = PortfolioRanking(
                item_id=r["project"].project_id,
                item_type="project",
                rank=idx + 1,
                score=r["score"],
                reasons=r["reasons"],
                evidence=r["evidence"],
                created_at=datetime.utcnow()
            )
            self._save_ranking(ranking)
            final_rankings.append(ranking)
            
        logger.info("projects_ranked", count=len(final_rankings))
        return final_rankings

    def rank_tasks(self, project_id: Optional[str] = None) -> List[PortfolioRanking]:
        """Rank open tasks across the portfolio or for a specific project."""
        query = "SELECT * FROM portfolio_tasks WHERE status NOT IN ('COMPLETE', 'CANCELLED')"
        params = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
            
        rows = self.db.fetchall(query, tuple(params))
        tasks = [self._row_to_task(row) for row in rows]
        
        rankings = []
        for t in tasks:
            score, reasons, evidence = self._calculate_task_score(t)
            t.priority = score
            self._save_task(t)
            
            rankings.append({
                "task": t,
                "score": score,
                "reasons": reasons,
                "evidence": evidence
            })
            
        rankings.sort(key=lambda x: x["score"], reverse=True)
        
        final_rankings = []
        for idx, r in enumerate(rankings):
            ranking = PortfolioRanking(
                item_id=r["task"].task_id,
                item_type="task",
                rank=idx + 1,
                score=r["score"],
                reasons=r["reasons"],
                evidence=r["evidence"],
                created_at=datetime.utcnow()
            )
            self._save_ranking(ranking)
            final_rankings.append(ranking)
            
        logger.info("tasks_ranked", count=len(final_rankings))
        return final_rankings

    def _calculate_project_score(self, project: ProjectProfile) -> tuple[float, List[str], List[PortfolioEvidence]]:
        score = project.importance * 0.5
        reasons = [f"Base importance weight (+{score:.2f})"]
        evidence = []
        
        if project.health == "CRITICAL":
            score += 0.3
            reasons.append("Critical project health detected (+0.30)")
            
        if project.ci_health == 0.0:
            score += 0.2
            reasons.append("Active CI pipeline failure (+0.20)")
            
        return min(1.0, score), reasons, evidence

    def _calculate_task_score(self, task: PortfolioTask) -> tuple[float, List[str], List[PortfolioEvidence]]:
        # In a real system, this evaluates dependencies and urgency
        score = task.priority
        reasons = [f"Base task priority (+{score:.2f})"]
        evidence = []
        
        if task.risk == "HIGH":
            score += 0.2
            reasons.append("High risk task (+0.20)")
            
        if "security" in task.source.lower() or "security" in task.title.lower():
            score += 0.4
            reasons.append("Security related task (+0.40)")
            
        return min(1.0, score), reasons, evidence

    def _save_task(self, task: PortfolioTask) -> None:
        query = """
            INSERT INTO portfolio_tasks (
                task_id, project_id, title, description, source, source_id,
                priority, risk, estimated_effort, dependencies, required_capabilities,
                status, metadata, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                title=excluded.title,
                description=excluded.description,
                priority=excluded.priority,
                risk=excluded.risk,
                estimated_effort=excluded.estimated_effort,
                dependencies=excluded.dependencies,
                required_capabilities=excluded.required_capabilities,
                status=excluded.status,
                metadata=excluded.metadata,
                updated_at=CURRENT_TIMESTAMP
        """
        params = (
            task.task_id,
            task.project_id,
            task.title,
            task.description,
            task.source,
            task.source_id,
            task.priority,
            task.risk,
            task.estimated_effort,
            json.dumps(task.dependencies),
            json.dumps(task.required_capabilities),
            task.status,
            json.dumps(task.metadata),
            task.created_at,
            datetime.utcnow()
        )
        self.db.execute(query, params)

    def _save_ranking(self, ranking: PortfolioRanking) -> None:
        query = """
            INSERT INTO portfolio_rankings (
                item_id, item_type, rank, score, reasons, evidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            ranking.item_id,
            ranking.item_type,
            ranking.rank,
            ranking.score,
            json.dumps(ranking.reasons),
            json.dumps([e.dict() for e in ranking.evidence]),
            ranking.created_at
        )
        self.db.execute(query, params)

    def _row_to_task(self, row: dict) -> PortfolioTask:
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
