import uuid
import json
from datetime import datetime
from typing import List, Optional
import structlog

from evoforge.memory.database import Database
from evoforge.github_integration.client import GitHubClient
from evoforge.portfolio.models import ProjectProfile, ProjectHealthReport, PortfolioEvidence
from evoforge.portfolio.registry import ProjectRegistry

logger = structlog.get_logger(__name__)

class ProjectScanner:
    def __init__(self, db: Database, gh_client: GitHubClient, registry: ProjectRegistry):
        self.db = db
        self.gh_client = gh_client
        self.registry = registry

    def scan_project(self, project_id: str) -> Optional[ProjectHealthReport]:
        profile = self.registry.get(project_id)
        if not profile:
            logger.error("scan_project_not_found", project_id=project_id)
            return None

        repo = profile.repository_full_name
        
        # 1. Gather data from GitHub API
        issues = self.gh_client.get_open_issues(repo)
        prs = self.gh_client.get_open_prs(repo)
        commits = self.gh_client.get_recent_commits(repo)
        ci_state = self.gh_client.get_ci_state(repo, profile.default_branch)
        
        # 2. Compute Health Scores
        evidence_list = []
        warnings = []
        unknown_fields = []
        
        # Maintenance Health (Issue/PR counts, freshness)
        maintenance_health = None
        if len(issues) > 20:
            maintenance_health = 0.4
            evidence_list.append(self._make_evidence(project_id, "github_issue", "issues_high", "Project has over 20 open issues.", 0.9))
        elif len(issues) == 0:
            maintenance_health = 1.0
            evidence_list.append(self._make_evidence(project_id, "github_issue", "issues_low", "Project has 0 open issues.", 0.9))
        else:
            maintenance_health = 0.8
            evidence_list.append(self._make_evidence(project_id, "github_issue", "issues_moderate", f"Project has {len(issues)} open issues.", 0.9))

        # Activity Health (Recent commits)
        activity_health = None
        if commits:
            activity_health = 1.0
            evidence_list.append(self._make_evidence(project_id, "github_commit", "commits_active", f"Project has {len(commits)} recent commits.", 1.0))
        else:
            activity_health = 0.1
            evidence_list.append(self._make_evidence(project_id, "github_commit", "commits_stale", "No recent commits found.", 0.8))

        # CI Health
        ci_health = None
        if ci_state == "success":
            ci_health = 1.0
            evidence_list.append(self._make_evidence(project_id, "github_ci", "ci_success", "CI pipeline is passing.", 1.0))
        elif ci_state == "failure":
            ci_health = 0.0
            evidence_list.append(self._make_evidence(project_id, "github_ci", "ci_failure", "CI pipeline is failing.", 1.0))
        else:
            unknown_fields.append("ci_health")
            evidence_list.append(self._make_evidence(project_id, "github_ci", "ci_unknown", "CI state is unknown.", 0.5))

        # Security/Tests/Docs (mocking static analysis for now since we're just reading GitHub API)
        # Ideally, we would clone the repo and run `RepositoryScanner` locally here.
        unknown_fields.extend(["security_health", "test_health", "documentation_health", "technical_debt", "roadmap_health"])

        # Overall health logic
        overall_health = "UNKNOWN"
        scores = [h for h in [maintenance_health, activity_health, ci_health] if h is not None]
        if not scores:
            overall_health = "UNKNOWN"
        else:
            avg_score = sum(scores) / len(scores)
            if ci_health == 0.0:
                overall_health = "CRITICAL"
            elif avg_score >= 0.8:
                overall_health = "HEALTHY"
            elif avg_score >= 0.5:
                overall_health = "WARNING"
            else:
                overall_health = "CRITICAL"

        report = ProjectHealthReport(
            project_id=project_id,
            overall_health=overall_health,
            maintenance_health=maintenance_health,
            activity_health=activity_health,
            ci_health=ci_health,
            evidence=evidence_list,
            warnings=warnings,
            unknown_fields=unknown_fields,
            timestamp=datetime.utcnow()
        )

        # Update ProjectProfile
        profile.health = overall_health
        profile.maintenance_health = maintenance_health
        profile.ci_health = ci_health
        profile.last_scanned_at = datetime.utcnow()
        self.registry.register(profile)

        # Store Evidence
        self._store_evidence(evidence_list)

        logger.info("project_scanned", project_id=project_id, overall_health=overall_health)
        return report

    def _make_evidence(self, project_id: str, src_type: str, src_id: str, observation: str, confidence: float) -> PortfolioEvidence:
        return PortfolioEvidence(
            evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            source="ProjectScanner",
            source_type=src_type,
            source_id=src_id,
            observation=observation,
            confidence=confidence,
            timestamp=datetime.utcnow()
        )

    def _store_evidence(self, evidence_list: List[PortfolioEvidence]) -> None:
        if not evidence_list:
            return
        
        query = """
            INSERT INTO portfolio_evidence (
                evidence_id, project_id, task_id, source, source_type, source_id,
                observation, confidence, metadata, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        for ev in evidence_list:
            params = (
                ev.evidence_id,
                ev.project_id,
                ev.task_id,
                ev.source,
                ev.source_type,
                ev.source_id,
                ev.observation,
                ev.confidence,
                json.dumps(ev.metadata),
                ev.timestamp
            )
            self.db.execute(query, params)
