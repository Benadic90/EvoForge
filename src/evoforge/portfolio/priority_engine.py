import json
import uuid
from datetime import datetime
from typing import Any

import structlog

from evoforge.memory.database import Database
from evoforge.portfolio.models import (
    PortfolioEvidence,
    PortfolioRanking,
    PortfolioTask,
    ProjectProfile,
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

    def generate_backlog(self, project_id: str, raw_items: list[dict[str, Any]]) -> list[PortfolioTask]:
        """
        Normalize diverse items (GH issues, CI failures, autonomous upgrades) into PortfolioTasks.
        Deduplicates by (project_id, source_id) so existing tasks are not re-inserted.
        """
        existing_rows = self.db.fetchall("SELECT source_id, task_id, status FROM portfolio_tasks WHERE project_id = ?", (project_id,))
        existing_sources = {r["source_id"] for r in existing_rows}
        
        # Get repository full name if available
        profile = self.registry.get(project_id)
        repo_name = profile.repository_full_name if profile else None

        tasks = []
        for item in raw_items:
            source_id = str(item.get("source_id", uuid.uuid4()))
            if source_id in existing_sources:
                continue

            task = PortfolioTask(
                task_id=f"ptask_{uuid.uuid4().hex[:8]}",
                project_id=project_id,
                repository_full_name=repo_name or item.get("repository_full_name"),
                title=item.get("title") or "Untitled Task",
                description=item.get("description") or "",
                source=item.get("source", "unknown"),
                source_type=item.get("source_type", "unknown"),
                source_id=source_id,
                source_url=item.get("source_url"),
                priority=float(item.get("priority_hint", 0.0)),
                risk=item.get("risk_hint", "LOW"),
                estimated_minutes=item.get("estimated_minutes", None),
                dependencies=item.get("dependencies", []),
                required_capabilities=item.get("required_capabilities", []),
                status="DISCOVERED",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata=item.get("metadata", {})
            )
            self._save_task(task)
            tasks.append(task)
            existing_sources.add(source_id)
            
        logger.info("backlog_generated", project_id=project_id, new_tasks=len(tasks))
        return tasks

    def rank_projects(self) -> list[PortfolioRanking]:
        """Rank all active projects in the portfolio."""
        self.db.execute("DELETE FROM portfolio_rankings WHERE item_type = 'project'")
        
        profiles = self.registry.list()
        active_profiles = [p for p in profiles if p.status == "MANAGED" or p.status == "ACTIVE"]
        
        rankings = []
        for p in active_profiles:
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

    def rank_tasks(self, project_id: str | None = None) -> list[PortfolioRanking]:
        """Rank open tasks across the portfolio or for a specific project."""
        if project_id:
            self.db.execute("DELETE FROM portfolio_rankings WHERE item_type = 'task' AND item_id IN (SELECT task_id FROM portfolio_tasks WHERE project_id = ?)", (project_id,))
        else:
            self.db.execute("DELETE FROM portfolio_rankings WHERE item_type = 'task'")
            
        query = "SELECT * FROM portfolio_tasks WHERE status NOT IN ('COMPLETED', 'CANCELLED', 'DEFERRED', 'COMPLETE')"
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

    def _calculate_project_score(self, project: ProjectProfile) -> tuple[float, list[str], list[PortfolioEvidence]]:
        score = 0.0
        reasons = []
        evidence = []
        
        importance_map = {"CRITICAL": 1.0, "HIGH": 0.8, "MEDIUM": 0.5, "LOW": 0.2}
        importance_val = importance_map.get(project.importance, 0.5)
        
        # We start with the importance weight
        score += importance_val * 0.4 # max 0.4 from importance
        reasons.append(f"Importance ({project.importance}) weight (+{importance_val * 0.4:.2f})")
        
        # In a real system, we fetch actual PortfolioEvidence linked to this project
        # and mathematically apply confidence and severity.
        
        return min(1.0, score), reasons, evidence

    def _calculate_task_score(self, task: PortfolioTask) -> tuple[float, list[str], list[PortfolioEvidence]]:
        # Mathematically compute task score
        score = task.priority * 0.3
        reasons = [f"Base task priority (+{score:.2f})"]
        evidence = []
        
        if task.risk == "HIGH":
            score += 0.2
            reasons.append("High risk penalty/bonus (+0.20)")
            
        # The priority logic must rely on structured evidence, NOT raw strings.
        # So we fetch evidence where task_id = task.task_id
        # and sum the severities.
        query = "SELECT * FROM portfolio_evidence WHERE task_id = ?"
        ev_rows = self.db.fetchall(query, (task.task_id,))
        for row in ev_rows:
            ev = PortfolioEvidence(**row)
            evidence.append(ev)
            if ev.severity == "CRITICAL":
                added = 0.4 * ev.confidence
                score += added
                reasons.append(f"Critical evidence: {ev.observation} (+{added:.2f})")
            elif ev.severity == "HIGH":
                added = 0.2 * ev.confidence
                score += added
                reasons.append(f"High evidence: {ev.observation} (+{added:.2f})")
            
        return min(1.0, score), reasons, evidence

    def _save_task(self, task: PortfolioTask) -> None:
        query = """
            INSERT INTO portfolio_tasks (
                task_id, canonical_task_id, project_id, repository_full_name, title, description,
                source, source_type, source_id, source_url, priority, confidence, risk, estimated_minutes,
                dependencies, required_capabilities, status, metadata, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                canonical_task_id=excluded.canonical_task_id,
                title=excluded.title,
                description=excluded.description,
                priority=excluded.priority,
                confidence=excluded.confidence,
                risk=excluded.risk,
                estimated_minutes=excluded.estimated_minutes,
                dependencies=excluded.dependencies,
                required_capabilities=excluded.required_capabilities,
                status=excluded.status,
                metadata=excluded.metadata,
                updated_at=CURRENT_TIMESTAMP
        """
        params = (
            task.task_id,
            task.canonical_task_id,
            task.project_id,
            task.repository_full_name,
            task.title,
            task.description,
            task.source,
            task.source_type,
            task.source_id,
            task.source_url,
            task.priority,
            task.confidence,
            task.risk,
            task.estimated_minutes,
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
            json.dumps([e.model_dump() for e in ranking.evidence]),
            ranking.created_at
        )
        self.db.execute(query, params)

    def _row_to_task(self, row: dict) -> PortfolioTask:
        row_dict = dict(row)
        return PortfolioTask(
            task_id=row_dict["task_id"],
            canonical_task_id=row_dict.get("canonical_task_id"),
            project_id=row_dict["project_id"],
            repository_full_name=row_dict.get("repository_full_name"),
            title=row_dict["title"],
            description=row_dict["description"],
            source=row_dict["source"],
            source_type=row_dict.get("source_type", "unknown"),
            source_id=row_dict["source_id"],
            source_url=row_dict.get("source_url"),
            priority=row_dict["priority"],
            confidence=row_dict.get("confidence", 1.0),
            risk=row_dict["risk"],
            estimated_minutes=row_dict.get("estimated_minutes"),
            dependencies=json.loads(row_dict["dependencies"]) if row_dict["dependencies"] else [],
            required_capabilities=json.loads(row_dict["required_capabilities"]) if row_dict["required_capabilities"] else [],
            status=row_dict["status"],
            created_at=row_dict["created_at"],
            updated_at=row_dict["updated_at"],
            metadata=json.loads(row_dict["metadata"]) if row_dict["metadata"] else {}
        )
