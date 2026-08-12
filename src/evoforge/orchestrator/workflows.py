from enum import Enum
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class WorkflowState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CRASHED = "crashed"

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
    dependencies: List[str] = []
    agent_type: str  # "developer", "qa", etc.
    status: WorkflowState = WorkflowState.PENDING
    context: Dict[str, Any] = {}
    
class WorkflowDefinition(BaseModel):
    id: str
    repo_name: str
    tasks: List[WorkflowTask]
    created_at: str = datetime.now().isoformat()
    state: WorkflowState = WorkflowState.PENDING
