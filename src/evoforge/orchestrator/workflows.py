from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from evoforge.memory.state import WorkflowStage


class TaskPriority(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

class WorkflowTask(BaseModel):
    id: str
    name: str
    description: str
    priority: TaskPriority
    dependencies: list[str] = []
    agent_type: str  # "developer", "qa", etc.
    status: WorkflowStage = WorkflowStage.INITIALIZE
    context: dict[str, Any] = {}
    
class WorkflowDefinition(BaseModel):
    id: str
    repo_name: str
    tasks: list[WorkflowTask]
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    state: WorkflowStage = WorkflowStage.INITIALIZE
    dry_run: bool = False
