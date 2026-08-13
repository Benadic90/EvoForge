
import structlog

from evoforge.memory.database import Database
from evoforge.portfolio.models import ProjectProfile

logger = structlog.get_logger(__name__)

class ProjectRegistry:
    def __init__(self, db: Database):
        self.db = db

    def register(self, profile: ProjectProfile) -> None:
        """Register a new project or update an existing one."""
        query = """
            INSERT INTO projects (
                project_id, repository_full_name, repository_url, owner, name, default_branch,
                description, vision, status, importance, priority_score, health, ci_health,
                metadata, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(project_id) DO UPDATE SET
                repository_full_name=excluded.repository_full_name,
                repository_url=excluded.repository_url,
                owner=excluded.owner,
                name=excluded.name,
                default_branch=excluded.default_branch,
                description=excluded.description,
                vision=excluded.vision,
                status=excluded.status,
                importance=excluded.importance,
                priority_score=excluded.priority_score,
                health=excluded.health,
                ci_health=excluded.ci_health,
                metadata=excluded.metadata,
                updated_at=CURRENT_TIMESTAMP
        """
        import json
        params = (
            profile.project_id,
            profile.repository_full_name,
            profile.repository_url,
            profile.owner,
            profile.name,
            profile.default_branch,
            profile.description,
            profile.vision,
            profile.status,
            profile.importance,
            profile.priority_score,
            profile.health,
            profile.ci_health,
            json.dumps(profile.metadata) if profile.metadata else "{}"
        )
        self.db.execute(query, params)
        logger.info("project_registered", project_id=profile.project_id, repo=profile.repository_full_name)

    def get(self, project_id: str) -> ProjectProfile | None:
        query = "SELECT * FROM projects WHERE project_id = ?"
        rows = self.db.fetchall(query, (project_id,))
        if not rows:
            return None
        return self._row_to_profile(rows[0])

    def get_by_repo(self, repository_full_name: str) -> ProjectProfile | None:
        query = "SELECT * FROM projects WHERE repository_full_name = ?"
        rows = self.db.fetchall(query, (repository_full_name,))
        if not rows:
            return None
        return self._row_to_profile(rows[0])

    def list(self) -> list[ProjectProfile]:
        query = "SELECT * FROM projects"
        rows = self.db.fetchall(query)
        return [self._row_to_profile(row) for row in rows]

    def remove(self, project_id: str) -> None:
        query = "DELETE FROM projects WHERE project_id = ?"
        self.db.execute(query, (project_id,))
        logger.info("project_removed", project_id=project_id)

    def enable(self, project_id: str) -> None:
        query = "UPDATE projects SET status = 'MANAGED', updated_at = CURRENT_TIMESTAMP WHERE project_id = ?"
        self.db.execute(query, (project_id,))
        logger.info("project_enabled", project_id=project_id)

    def disable(self, project_id: str) -> None:
        query = "UPDATE projects SET status = 'PAUSED', updated_at = CURRENT_TIMESTAMP WHERE project_id = ?"
        self.db.execute(query, (project_id,))
        logger.info("project_disabled", project_id=project_id)

    def get_health_trend(self, project_id: str) -> str:
        """Calculate the project health trend based on historical snapshots."""
        query = "SELECT overall_health FROM project_health_history WHERE project_id = ? ORDER BY timestamp DESC LIMIT 3"
        rows = self.db.fetchall(query, (project_id,))
        if len(rows) < 2:
            return "UNKNOWN"
            
        health_scores = {"CRITICAL": 0, "WARNING": 1, "HEALTHY": 2, "UNKNOWN": 1}
        current_score = health_scores.get(rows[0]["overall_health"], 1)
        prev_score = health_scores.get(rows[1]["overall_health"], 1)
        
        if current_score > prev_score:
            return "IMPROVING"
        elif current_score < prev_score:
            return "DECLINING"
        else:
            return "STABLE"

    def _row_to_profile(self, row: dict) -> ProjectProfile:
        import json
        metadata_str = row["metadata"]
        metadata = json.loads(metadata_str) if metadata_str else {}
        
        project_id = row["project_id"]
        health_trend = self.get_health_trend(project_id)
        
        return ProjectProfile(
            project_id=project_id,
            repository_full_name=row["repository_full_name"],
            repository_url=row["repository_url"],
            owner=row["owner"],
            name=row["name"],
            default_branch=row["default_branch"],
            description=row["description"],
            vision=row["vision"],
            status=row["status"],
            importance=str(row["importance"]),
            priority_score=row["priority_score"],
            health=row["health"],
            health_trend=health_trend,
            ci_health=row["ci_health"],
            security_health=row["security_health"],
            test_health=row["test_health"],
            documentation_health=row["documentation_health"],
            maintenance_health=row["maintenance_health"],
            technical_debt=row["technical_debt"],
            recent_activity=row["recent_activity"],
            last_scanned_at=row["last_scanned_at"],
            last_worked_at=row["last_worked_at"],
            roadmap_version=row["roadmap_version"],
            metadata=metadata
        )
