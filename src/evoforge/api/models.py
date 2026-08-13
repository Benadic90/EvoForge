from typing import Any

from pydantic import BaseModel, Field

# Portfolio Models


class SystemStatusResponse(BaseModel):
    system_state: str
    active_workflows: int
    failed_workflows: int
    paused_workflows: int
    complete_workflows: int
    healthy_executors: int
    unhealthy_executors: int
    recent_failures: list[dict[str, Any]] = Field(default_factory=list)
    version: str = "0.3.0"


class AgentStatusResponse(BaseModel):
    agent_id: str
    name: str
    role: str
    capabilities: list[str] = Field(default_factory=list)
    total_tasks: int = 0
    successful_tasks: int = 0
    success_rate: float | None = None
    avg_duration_ms: float | None = None


class ExecutorStatusResponse(BaseModel):
    executor_id: str
    is_healthy: bool
    is_enabled: bool
    capabilities: list[str] = Field(default_factory=list)
    total_runs: int = 0
    successful_runs: int = 0
    success_rate: float | None = None
    avg_duration_ms: float | None = None
    avg_cost_usd: float | None = None
    avg_quality_score: float | None = None
    fallback_count: int = 0
    fallback_rate: float = 0.0


class RoutingDecisionResponse(BaseModel):
    id: int
    task_id: str
    workflow_id: str
    agent_id: str | None = None
    task_type: str | None = None
    selected_executor_id: str
    selected_score: float
    routing_policy_version: str = "adaptive-v1"
    decision_reason: str | None = None
    created_at: str


class TelemetryExecutionResponse(BaseModel):
    id: int
    task_id: str
    workflow_id: str
    agent_id: str | None = None
    task_type: str | None = None
    executor_id: str
    duration_ms: float = 0.0
    success: bool
    fallback_used: bool = False
    cost_usd: float = 0.0
    quality_score: float | None = None
    created_at: str


class TelemetrySummaryResponse(BaseModel):
    total_executions: int
    total_successful: int
    overall_success_rate: float
    total_cost_usd: float
    avg_duration_ms: float
    by_executor: dict[str, dict[str, Any]] = Field(default_factory=dict)
    by_task_type: list[dict[str, Any]] = Field(default_factory=list)


class EventResponse(BaseModel):
    id: int
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class KnowledgeGraphNode(BaseModel):
    id: str
    group: int
    type: str
    title: str | None = None
    domain: str | None = None


class KnowledgeGraphLink(BaseModel):
    source: str
    target: str
    value: int = 1
    label: str = "link"


class KnowledgeGraphResponse(BaseModel):
    nodes: list[KnowledgeGraphNode] = Field(default_factory=list)
    links: list[KnowledgeGraphLink] = Field(default_factory=list)


class AntigravityStatusResponse(BaseModel):
    executor_id: str = "antigravity"
    status: str
    available: bool
    runtime_type: str | None = None
    runtime_version: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    reason_unavailable: str | None = None
    active_sessions: int = 0


class GitHubTokenUpdate(BaseModel):
    token: str


class GitHubStatusResponse(BaseModel):
    configured: bool
    username: str | None = None


class LLMKeyUpdate(BaseModel):
    provider: str
    api_key: str

class LLMKeyStatusResponse(BaseModel):
    gemini_configured: bool
    nvidia_configured: bool

