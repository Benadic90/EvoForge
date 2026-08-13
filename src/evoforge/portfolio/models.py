from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PortfolioEvidence(BaseModel):
    """Evidence used to explain a portfolio decision or health score."""
    evidence_id: str
    project_id: str
    task_id: str | None = None
    source: str
    source_type: str  # github_issue, github_pr, github_commit, github_ci, security_finding, test_result, roadmap, dependency_scan, project_memory
    source_id: str | None = None
    source_url: str | None = None
    observation: str
    severity: str = "UNKNOWN" # CRITICAL, HIGH, MEDIUM, LOW
    timestamp: datetime
    expires_at: datetime | None = None
    confidence: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)

class ProjectHealthReport(BaseModel):
    """The current health state of a project."""
    project_id: str
    overall_health: str  # HEALTHY, WARNING, CRITICAL, UNKNOWN
    security_health: float | None = None
    test_health: float | None = None
    documentation_health: float | None = None
    maintenance_health: float | None = None
    activity_health: float | None = None
    technical_debt: float | None = None
    ci_health: float | None = None
    roadmap_health: float | None = None
    evidence: list[PortfolioEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    unknown_fields: list[str] = Field(default_factory=list)
    timestamp: datetime

class ProjectProfile(BaseModel):
    """Canonical representation of a managed project in the portfolio."""
    project_id: str
    repository_full_name: str
    repository_url: str
    owner: str
    name: str
    default_branch: str
    description: str | None = None
    vision: str | None = None
    status: str = "MANAGED" # MANAGED, PAUSED, ARCHIVED, IGNORED
    importance: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
    priority_score: float = 0.0
    health: str = "UNKNOWN"
    health_trend: str = "STABLE"
    ci_health: float | None = None
    security_health: float | None = None
    test_health: float | None = None
    documentation_health: float | None = None
    maintenance_health: float | None = None
    technical_debt: float | None = None
    recent_activity: datetime | None = None
    last_scanned_at: datetime | None = None
    last_worked_at: datetime | None = None
    roadmap_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class Milestone(BaseModel):
    milestone_id: str
    title: str
    description: str
    priority: str
    status: str
    dependencies: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    target_date: str | None = None

class ProjectRoadmap(BaseModel):
    """Canonical planning state."""
    roadmap_id: str
    project_id: str
    version: str
    vision: str
    milestones: list[Milestone] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    status: str
    created_at: datetime
    updated_at: datetime

class PortfolioTask(BaseModel):
    """Normalized work item in the portfolio backlog."""
    task_id: str
    canonical_task_id: str | None = None
    project_id: str
    repository_full_name: str | None = None
    title: str
    description: str
    source: str
    source_type: str = "unknown"
    source_id: str
    source_url: str | None = None
    priority: float = 0.0
    confidence: float = 1.0
    risk: str = "LOW"
    estimated_minutes: int | None = None
    dependencies: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    status: str = "DISCOVERED" # DISCOVERED, ANALYZED, READY, BLOCKED, PLANNED, RUNNING, COMPLETED, FAILED, CANCELLED, DEFERRED
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

class PortfolioRanking(BaseModel):
    """Explanation of why a project or task is ranked where it is."""
    item_id: str
    item_type: str = "project"  # project or task
    rank: int
    score: float
    reasons: list[str] = Field(default_factory=list)
    evidence: list[PortfolioEvidence] = Field(default_factory=list)
    created_at: datetime

class DailyPortfolioPlan(BaseModel):
    """The daily plan containing the bounded work EvoForge should execute."""
    plan_id: str
    date: str
    selected_projects: list[str] = Field(default_factory=list)
    selected_tasks: list[str] = Field(default_factory=list)
    execution_order: list[str] = Field(default_factory=list)
    estimated_work: str
    risk: str
    budget: dict[str, Any] = Field(default_factory=dict)
    reasons: list[str] = Field(default_factory=list)
    created_at: datetime

class PortfolioHealth(BaseModel):
    """Aggregated portfolio health overview."""
    total_projects: int = 0
    healthy_projects: int = 0
    warning_projects: int = 0
    critical_projects: int = 0
    unknown_projects: int = 0
    overall_health: str = "UNKNOWN"
    critical_findings: list[str] = Field(default_factory=list)
