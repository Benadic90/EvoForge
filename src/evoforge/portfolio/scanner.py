import json
import uuid
from datetime import datetime

import structlog

from evoforge.github_integration.client import GitHubClient
from evoforge.memory.database import Database
from evoforge.portfolio.models import PortfolioEvidence, ProjectHealthReport
from evoforge.portfolio.registry import ProjectRegistry

logger = structlog.get_logger(__name__)

class ProjectScanner:
    def __init__(self, db: Database, gh_client: GitHubClient, registry: ProjectRegistry):
        self.db = db
        self.gh_client = gh_client
        self.registry = registry

    def scan_project(self, project_id: str, force_rescan: bool = False) -> tuple[ProjectHealthReport | None, list[dict] | None]:
        profile = self.registry.get(project_id)
        if not profile:
            logger.error("scan_project_not_found", project_id=project_id)
            return None, None

        # Cache check: if not forced and scanned in last 4 hours, skip
        if not force_rescan and profile.last_scanned_at:
            from datetime import timedelta
            if datetime.utcnow() - profile.last_scanned_at < timedelta(hours=4):
                logger.info("scan_skipped_cached", project_id=project_id)
                return None, None

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
        if issues is None:
            # Partial failure from GitHub
            warnings.append("Failed to fetch open issues from GitHub API.")
            unknown_fields.append("maintenance_health")
            issues = [] # Default to empty for loop below, but health remains None
        elif len(issues) > 20:
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

        # Local Analysis (Security/Tests/Docs/Debt)
        test_health = None
        documentation_health = None
        technical_debt = None
        
        # Try to find a local workspace to scan
        import os

        from evoforge.github_integration.scanner import RepositoryScanner
        
        # Check standard workspace location or current directory if it's the root project
        possible_paths = [
            os.path.join(os.getcwd(), profile.name),
            os.path.join(os.getcwd(), "workspaces", profile.name),
            os.getcwd() if profile.name.lower() in os.getcwd().lower() else ""
        ]
        
        local_path = None
        for p in possible_paths:
            if p and os.path.exists(p) and os.path.isdir(p):
                local_path = p
                break
                
        if local_path:
            local_scanner = RepositoryScanner(local_path)
            local_results = local_scanner.scan()
            
            if "error" not in local_results:
                # Test Health
                if local_results.get("has_tests"):
                    test_health = 1.0
                    evidence_list.append(self._make_evidence(project_id, "local_scan", "tests_found", "Test directory discovered.", 0.9))
                else:
                    test_health = 0.2
                    evidence_list.append(self._make_evidence(project_id, "local_scan", "tests_missing", "No test directory discovered.", 0.8))
                    
                # Documentation Health
                if local_results.get("has_docs"):
                    documentation_health = 1.0
                else:
                    documentation_health = 0.3
                    evidence_list.append(self._make_evidence(project_id, "local_scan", "docs_missing", "No primary documentation found.", 0.8))
                    
                # Technical Debt (based on TODOs)
                todos = local_results.get("todo_count", 0)
                if todos > 50:
                    technical_debt = 0.3
                    evidence_list.append(self._make_evidence(project_id, "local_scan", "high_debt", f"Found {todos} TODO/FIXME markers.", 0.7))
                elif todos > 0:
                    technical_debt = 0.7
                else:
                    technical_debt = 1.0
                    
        if test_health is None:
            unknown_fields.append("test_health")
        if documentation_health is None:
            unknown_fields.append("documentation_health")
        if technical_debt is None:
            unknown_fields.append("technical_debt")
            
        unknown_fields.extend(["security_health", "roadmap_health"])

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

        # 3. Generate raw items for backlog (GitHub Issues + Autonomous Engineering Upgrades)
        raw_items = []
        for issue in issues:
            raw_items.append({
                "source": "github_issue",
                "source_type": "github_issue",
                "source_id": issue["id"],
                "source_url": issue.get("html_url"),
                "title": issue["title"],
                "description": issue["body"],
                "priority_hint": 0.5,
                "risk_hint": "LOW",
                "metadata": {"labels": issue.get("labels", [])}
            })

        # 4. Proactive Autonomous Engineering Upgrades (Continuous 24/7 Lead Engineer Roadmap)
        autonomous_upgrades = [
            {
                "source": "autonomous_engine",
                "source_type": "architecture_evolution",
                "source_id": f"auto_arch_{profile.name.lower()}",
                "source_url": None,
                "title": f"Architecture Evolution: Modularize and modernize core components for {profile.name}",
                "description": f"Perform automated architectural inspection of {repo}, enforce clean module separation, reduce coupling, and modernize asynchronous execution patterns.",
                "priority_hint": 0.85,
                "risk_hint": "LOW",
                "metadata": {"category": "architecture", "autonomous": True}
            },
            {
                "source": "autonomous_engine",
                "source_type": "test_hardening",
                "source_id": f"auto_test_{profile.name.lower()}",
                "source_url": None,
                "title": f"Test Hardening: Generate automated unit & regression test suites for {profile.name}",
                "description": f"Audit test coverage across {repo}, generate edge-case unit tests, mock external boundaries, and ensure CI test verification passes.",
                "priority_hint": 0.80,
                "risk_hint": "LOW",
                "metadata": {"category": "testing", "autonomous": True}
            },
            {
                "source": "autonomous_engine",
                "source_type": "security_audit",
                "source_id": f"auto_sec_{profile.name.lower()}",
                "source_url": None,
                "title": f"Security & Dependency Hardening: Update dependencies and sanitize inputs for {profile.name}",
                "description": f"Scan {repo} dependencies for CVE vulnerabilities, pin secure versions, sanitize external data flows, and enforce strict typing.",
                "priority_hint": 0.75,
                "risk_hint": "LOW",
                "metadata": {"category": "security", "autonomous": True}
            },
            {
                "source": "autonomous_engine",
                "source_type": "documentation_evolution",
                "source_id": f"auto_doc_{profile.name.lower()}",
                "source_url": None,
                "title": f"Documentation Evolution: Generate comprehensive API specs & developer guides for {profile.name}",
                "description": f"Analyze codebase interfaces in {repo} and generate high-clarity docstrings, architecture diagrams, and complete README developer guides.",
                "priority_hint": 0.60,
                "risk_hint": "LOW",
                "metadata": {"category": "documentation", "autonomous": True}
            },
            {
                "source": "autonomous_engine",
                "source_type": "user_requested_task",
                "source_id": f"live_test_{profile.name.lower()}_v16",
                "source_url": None,
                "title": f"Live Tool Loop Test v16: Create test file in {profile.name}",
                "description": f"CLONE {repo}. CREATE a new file named 'hello_autonomous.py' in the root directory containing exactly 'print(1)'. Use the write_file tool. Do not do anything else. This must be a real file change to succeed.",
                "priority_hint": 0.99,
                "risk_hint": "LOW",
                "estimated_minutes": 5,
                "metadata": {"category": "testing", "autonomous": True}
            }
        ]

        existing_task_sources = set()
        if self.db:
            rows = self.db.fetchall("SELECT source_id FROM portfolio_tasks WHERE project_id = ?", (project_id,))
            existing_task_sources = {r["source_id"] for r in rows}

        for upg in autonomous_upgrades:
            if upg["source_id"] not in existing_task_sources:
                raw_items.append(upg)

        # Update ProjectProfile
        profile.health = overall_health
        profile.maintenance_health = maintenance_health
        profile.ci_health = ci_health
        profile.last_scanned_at = datetime.utcnow()
        self.registry.register(profile)

        # Store Evidence and Health History
        self._store_evidence(evidence_list)
        self._save_health_history(report)

        logger.info("project_scanned", project_id=project_id, overall_health=overall_health)
        return report, raw_items

    def _make_evidence(self, project_id: str, src_type: str, src_id: str, observation: str, confidence: float, source_url: str | None = None, severity: str = "UNKNOWN", task_id: str | None = None, expires_at: datetime | None = None) -> PortfolioEvidence:
        return PortfolioEvidence(
            evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            task_id=task_id,
            source="ProjectScanner",
            source_type=src_type,
            source_id=src_id,
            source_url=source_url,
            observation=observation,
            severity=severity,
            confidence=confidence,
            expires_at=expires_at,
            timestamp=datetime.utcnow()
        )

    def _store_evidence(self, evidence_list: list[PortfolioEvidence]) -> None:
        if not evidence_list:
            return
        
        query = """
            INSERT INTO portfolio_evidence (
                evidence_id, project_id, task_id, source, source_type, source_id, source_url,
                observation, severity, confidence, metadata, expires_at, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        for ev in evidence_list:
            params = (
                ev.evidence_id,
                ev.project_id,
                ev.task_id,
                ev.source,
                ev.source_type,
                ev.source_id,
                ev.source_url,
                ev.observation,
                ev.severity,
                ev.confidence,
                json.dumps(ev.metadata),
                ev.expires_at,
                ev.timestamp
            )
            self.db.execute(query, params)

    def _save_health_history(self, report: ProjectHealthReport) -> None:
        query = """
            INSERT INTO project_health_history (
                project_id, overall_health, security_health, test_health,
                documentation_health, maintenance_health, activity_health,
                technical_debt, ci_health, roadmap_health, confidence, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            report.project_id,
            report.overall_health,
            report.security_health,
            report.test_health,
            report.documentation_health,
            report.maintenance_health,
            report.activity_health,
            report.technical_debt,
            report.ci_health,
            report.roadmap_health,
            1.0, # default confidence
            report.timestamp
        )
        self.db.execute(query, params)
