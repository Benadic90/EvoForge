from enum import Enum
from pydantic import BaseModel, Field

from evoforge.agents.capabilities import AgentCapability

class TaskClassification(str, Enum):
    CODING = "coding"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    SECURITY = "security"
    REFACTORING = "refactoring"
    REPO_ANALYSIS = "repo_analysis"
    DEPENDENCY_UPDATE = "dependency_update"
    PERFORMANCE = "performance"
    PLANNING = "planning"
    SELF_EVOLUTION = "self_evolution"
    OTHER = "other"

class TaskRequirements(BaseModel):
    task_id: str
    task_type: TaskClassification = TaskClassification.OTHER
    required_capabilities: list[AgentCapability] = Field(default_factory=list)
    preferred_capabilities: list[AgentCapability] = Field(default_factory=list)
    
    minimum_context: int = 0
    requires_tools: bool = False
    requires_browser: bool = False
    requires_terminal: bool = False
    requires_repo_write: bool = False
    
    risk_level: str = "LOW"
    estimated_complexity: str = "LOW" # TRIVIAL, LOW, MEDIUM, HIGH, EXPERT
    
    # Preferences used for scoring
    latency_preference: float = 0.5 # 0.0 (dont care) to 1.0 (must be very fast)
    cost_preference: float = 0.5    # 0.0 (dont care) to 1.0 (must be extremely cheap)
    quality_preference: float = 0.5 # 0.0 (dont care) to 1.0 (must be highest quality)
    privacy_requirement: float = 0.0 # 0.0 (public ok) to 1.0 (must be local)
