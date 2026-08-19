from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from evoforge.agents.capabilities import AgentCapability
from evoforge.memory.state import WorkflowStage


class AgentContext(BaseModel):
    """
    Shared execution context passed to all agents.
    """
    run_id: str
    workflow_id: str
    task_id: str
    task_description: str
    project_id: str | None = None
    repository_id: str | None = None
    current_stage: WorkflowStage
    dry_run: bool = False
    permissions: list[str] = Field(default_factory=list)
    available_tools: list[str] = Field(default_factory=list)
    required_capabilities: list[AgentCapability] = Field(default_factory=list)
    memory_context: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    """
    Standardized result model for agent execution.
    """
    success: bool
    agent_id: str
    task_id: str
    workflow_id: str
    summary: str
    artifacts: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_action: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    # Real execution loop fields
    changed_files: list[str] = Field(default_factory=list)
    tests_run: list[str] = Field(default_factory=list)
    tests_passed: bool | None = None
    tests_failed: bool | None = None
    git_status: str | None = None
    workspace: str | None = None
    commit_required: bool = False
    failure_class: str | None = None


class FailurePolicy(BaseModel):
    """
    Agent-specific failure behavior.
    """
    max_attempts: int = 3
    retryable_errors: list[str] = Field(default_factory=list)
    non_retryable_errors: list[str] = Field(default_factory=list)
    fallback_allowed: bool = True
    escalation_level: str = "warning"


class ToolRequirement(BaseModel):
    name: str
    required: bool = True


class AgentContract(BaseModel):
    """
    Canonical metadata model describing an agent.
    This describes the agent but does NOT contain runtime implementation.
    """
    agent_id: str
    name: str
    display_name: str
    role: str
    description: str
    version: str
    capabilities: list[AgentCapability] = Field(default_factory=list)
    tools: list[ToolRequirement] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    skill_profile_id: str | None = None
    skill_version: str | None = None
    failure_policy: FailurePolicy = Field(default_factory=FailurePolicy)
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentExecutor(ABC):
    """
    Runtime execution interface.
    """
    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        """Executes a task using the standardized AgentContext."""

    def health_check(self) -> bool:
        """Checks if the executor backend is reachable and configured."""
        return True

    def cancel(self, task_id: str) -> None:
        """Cancels a currently running execution."""

    def get_status(self, task_id: str) -> str:
        """Gets the status of a specific execution (e.g., RUNNING, COMPLETED, FAILED, UNAVAILABLE)."""
        return "UNKNOWN"

