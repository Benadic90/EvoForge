from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

SkillLevel = Literal["NOVICE", "DEVELOPING", "COMPETENT", "ADVANCED", "EXPERT"]
KnowledgeFreshness = Literal["FRESH", "STALE", "EXPIRED", "UNKNOWN"]
KnowledgeVerificationStatus = Literal["VERIFIED", "LIKELY_VALID", "LOW_CONFIDENCE", "UNVERIFIED", "CONFLICTED", "EXPIRED", "REJECTED"]
ResearchStatus = Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "NEEDS_REVIEW"]
PracticeStatus = Literal["DRAFT", "ACTIVE", "COMPLETED", "FAILED", "EVALUATING"]
EvolutionStatus = Literal["PROPOSED", "QUEUED", "TESTING", "PASSED", "FAILED", "REJECTED", "APPROVED", "DEPLOYED", "ROLLED_BACK", "PAUSED"]
EvolutionTarget = Literal["PROMPT", "SKILL", "ROUTING_POLICY", "AGENT_CONFIG", "WORKFLOW_STRATEGY", "TOOL_STRATEGY", "RESEARCH_STRATEGY", "PLANNING_STRATEGY", "EVALUATION_STRATEGY"]
SkillGapSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
SkillGapStatus = Literal["OPEN", "IN_PRACTICE", "RESOLVED", "IGNORED"]
class ResearchJob(BaseModel):
    research_id: str
    agent_id: str
    project_id: str | None = None
    task_id: str | None = None
    domain: str
    topic: str
    query: str
    reason: str
    priority: float = 0.5
    status: ResearchStatus = "QUEUED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    findings: str | None = None
    skill_gap_id: str | None = None

class KnowledgeItem(BaseModel):
    knowledge_id: str
    topic: str
    domain: str
    summary: str
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    verification_status: KnowledgeVerificationStatus = "UNVERIFIED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    related_skills: list[str] = Field(default_factory=list)
    related_projects: list[str] = Field(default_factory=list)
    evidence: str | None = None
    
    @property
    def freshness(self) -> KnowledgeFreshness:
        if not self.expires_at:
            return "UNKNOWN"
        now = datetime.now(UTC)
        # Handle naive datetime from db
        expires = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=UTC)
        if now > expires:
            return "EXPIRED"
        # If it expires in less than 7 days, call it stale
        if (expires - now).days < 7:
            return "STALE"
        return "FRESH"

class Skill(BaseModel):
    name: str
    version: int
    confidence: float
    skill_level: SkillLevel
    last_verified: datetime | None = None
    freshness: KnowledgeFreshness = "UNKNOWN"
    techniques: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)

class SkillGap(BaseModel):
    skill_gap_id: str
    agent_id: str
    skill_id: str
    project_id: str | None = None
    severity: SkillGapSeverity = "MEDIUM"
    confidence: float = 1.0
    evidence_ids: list[str] = Field(default_factory=list)
    recommended_action: str | None = None
    status: SkillGapStatus = "OPEN"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class PracticePlan(BaseModel):
    practice_id: str
    agent_id: str
    skill_id: str
    objective: str
    tasks: list[str] = Field(default_factory=list)
    difficulty: str = "medium"
    budget: dict[str, Any] = Field(default_factory=dict)
    deadline: datetime | None = None
    benchmark_id: str | None = None
    status: PracticeStatus = "DRAFT"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class BenchmarkResult(BaseModel):
    benchmark_id: str
    agent_id: str
    skill_id: str
    environment: str
    baseline_score: float
    candidate_score: float
    sample_count: int = 1
    evidence: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

class Hypothesis(BaseModel):
    current_behavior: str
    observed_weakness: str
    proposed_change: str
    expected_improvement: str
    risk: str
    benchmark: str
    acceptance_threshold: str

class EvolutionProposal(BaseModel):
    proposal_id: str
    target_type: EvolutionTarget
    target_id: str
    current_version: str | int | None = None
    candidate_version: str | int | None = None
    description: str
    hypothesis: Hypothesis
    evidence_ids: list[str] = Field(default_factory=list)
    benchmark_id: str | None = None
    experiment_id: str | None = None
    status: EvolutionStatus = "PROPOSED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    approved_at: datetime | None = None
    deployed_at: datetime | None = None
    rolled_back_at: datetime | None = None
    rollback_version: str | int | None = None

class ExperimentRecord(BaseModel):
    experiment_id: str
    proposal_id: str
    baseline_version: str | int
    candidate_version: str | int
    target: str
    dataset: str
    sample_count: int
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    baseline_score: float | None = None
    candidate_score: float | None = None
    improvement_percent: float | None = None
    regressions: int = 0
    cost: float = 0.0
    latency: float = 0.0
    status: str = "RUNNING"
    environment: str

class ApprovalPolicy(BaseModel):
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    requires_human: bool
    minimum_samples: int
    minimum_improvement: float
    maximum_regression: float

class EngineeringLesson(BaseModel):
    id: str
    agent_name: str
    problem_pattern: str
    root_cause: str | None = None
    successful_solution: str | None = None
    related_skill: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    status: str = "UNVERIFIED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
