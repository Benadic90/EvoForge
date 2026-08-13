from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PortfolioEvidence(BaseModel):
    """Evidence used to explain a portfolio decision or health score."""
    evidence_id: str
    project_id: str
    task_id: Optional[str] = None
    source: str
    source_type: str  # github_issue, github_pr, github_commit, github_ci, security_finding, test_result, roadmap, dependency_scan, project_memory
    source_id: Optional[str] = None
    observation: str
    timestamp: datetime
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProjectHealthReport(BaseModel):
    """The current health state of a project."""
    project_id: str
    overall_health: str  # HEALTHY, WARNING, CRITICAL, UNKNOWN
    security_health: Optional[float] = None
    test_health: Optional[float] = None
    documentation_health: Optional[float] = None
    maintenance_health: Optional[float] = None
    activity_health: Optional[float] = None
    technical_debt: Optional[float] = None
    ci_health: Optional[float] = None
    roadmap_health: Optional[float] = None
    evidence: List[PortfolioEvidence] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    unknown_fields: List[str] = Field(default_factory=list)
    timestamp: datetime

class ProjectProfile(BaseModel):
    """Canonical representation of a managed project in the portfolio."""
    project_id: str
    repository_full_name: str
    repository_url: str
    owner: str
    name: str
    default_branch: str
    description: Optional[str] = None
    vision: Optional[str] = None
    status: str = "ACTIVE"
    importance: float = 0.5  # 0.0 to 1.0
    priority_score: float = 0.0
    health: str = "UNKNOWN"
    ci_health: Optional[float] = None
    security_health: Optional[float] = None
    test_health: Optional[float] = None
    documentation_health: Optional[float] = None
    maintenance_health: Optional[float] = None
    technical_debt: Optional[float] = None
    recent_activity: Optional[datetime] = None
    last_scanned_at: Optional[datetime] = None
    last_worked_at: Optional[datetime] = None
    roadmap_version: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Milestone(BaseModel):
    milestone_id: str
    title: str
    description: str
    priority: str
    status: str
    dependencies: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    target_date: Optional[str] = None

class ProjectRoadmap(BaseModel):
    """Canonical planning state."""
    roadmap_id: str
    project_id: str
    version: str
    vision: str
    milestones: List[Milestone] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    status: str
    created_at: datetime
    updated_at: datetime

class PortfolioTask(BaseModel):
    """Normalized work item in the portfolio backlog."""
    task_id: str
    project_id: str
    title: str
    description: str
    source: str
    source_id: str
    priority: float = 0.0
    risk: str = "LOW"
    estimated_effort: str = "UNKNOWN"
    dependencies: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    status: str = "NOT_STARTED"
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PortfolioRanking(BaseModel):
    """Explanation of why a project or task is ranked where it is."""
    item_id: str
    item_type: str = "project"  # project or task
    rank: int
    score: float
    reasons: List[str] = Field(default_factory=list)
    evidence: List[PortfolioEvidence] = Field(default_factory=list)
    created_at: datetime

class DailyPortfolioPlan(BaseModel):
    """The daily plan containing the bounded work EvoForge should execute."""
    plan_id: str
    date: str
    selected_projects: List[str] = Field(default_factory=list)
    selected_tasks: List[str] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    estimated_work: str
    risk: str
    budget: Dict[str, Any] = Field(default_factory=dict)
    reasons: List[str] = Field(default_factory=list)
    created_at: datetime

class PortfolioHealth(BaseModel):
    """Aggregated portfolio health overview."""
    total_projects: int = 0
    healthy_projects: int = 0
    warning_projects: int = 0
    critical_projects: int = 0
    unknown_projects: int = 0
    overall_health: str = "UNKNOWN"
    critical_findings: List[str] = Field(default_factory=list)
