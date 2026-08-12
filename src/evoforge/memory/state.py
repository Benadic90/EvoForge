from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStage(str, Enum):
    INITIALIZE = "INITIALIZE"
    SCAN = "SCAN"
    ANALYZE = "ANALYZE"
    PRIORITIZE = "PRIORITIZE"
    PLAN = "PLAN"
    ARCHITECT = "ARCHITECT"
    IMPLEMENT = "IMPLEMENT"
    TEST = "TEST"
    SECURITY = "SECURITY"
    REVIEW = "REVIEW"
    FIX = "FIX"
    COMMIT = "COMMIT"
    PUSH = "PUSH"
    CREATE_PR = "CREATE_PR"
    UPDATE_MEMORY = "UPDATE_MEMORY"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class WorkflowState(BaseModel):
    workflow_id: str
    run_id: str
    repository_id: str
    project_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    
    current_stage: WorkflowStage = WorkflowStage.INITIALIZE
    substate: str | None = None
    
    attempt_count: int = 0
    max_attempts: int = 3
    
    worker_id: str | None = None
    lease_expires_at: datetime | None = None
    deadline_at: datetime | None = None
    dry_run: bool = False
    
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    
    error: str | None = None
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def advance_to(self, stage: WorkflowStage, substate: str | None = None):
        """Advances the workflow to a new stage."""
        self.current_stage = stage
        self.substate = substate
        self.updated_at = datetime.now(UTC)
        self.attempt_count = 0  # Reset attempts on successful stage transition

    def record_attempt(self):
        """Records an attempt for the current stage."""
        self.attempt_count += 1
        self.updated_at = datetime.now(UTC)

    def has_exceeded_attempts(self) -> bool:
        """Checks if the current stage has exceeded max attempts."""
        return self.attempt_count >= self.max_attempts
        
    def has_exceeded_deadline(self) -> bool:
        """Checks if the workflow has exceeded its overall deadline."""
        if not self.deadline_at:
            return False
        return datetime.now(UTC) > self.deadline_at

    def mark_completed(self):
        """Marks the workflow as successfully completed."""
        self.current_stage = WorkflowStage.COMPLETE
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def mark_failed(self, error_message: str):
        """Marks the workflow as failed."""
        self.current_stage = WorkflowStage.FAILED
        self.error = error_message
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def get_next_stage(self) -> WorkflowStage | None:
        """Determines the next deterministic stage in the state machine."""
        transitions = {
            WorkflowStage.INITIALIZE: WorkflowStage.PLAN, # Simplified sequence for now
            WorkflowStage.PLAN: WorkflowStage.IMPLEMENT,
            WorkflowStage.IMPLEMENT: WorkflowStage.COMPLETE,
        }
        return transitions.get(self.current_stage)
