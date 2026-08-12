from enum import Enum
from pydantic import BaseModel, Field


class CapabilityRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentCapability(str, Enum):
    """
    Stable vocabulary of capabilities.
    """
    CODING = "coding"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    PLANNING = "planning"
    REASONING = "reasoning"
    ARCHITECTURE = "architecture"
    RESEARCH = "research"
    BROWSER = "browser"
    TERMINAL = "terminal"
    REPO_NAVIGATION = "repo_navigation"
    MULTI_FILE_EDITING = "multi_file_editing"
    TESTING = "testing"
    TEST_GENERATION = "test_generation"
    SECURITY_ANALYSIS = "security_analysis"
    DOCUMENTATION = "documentation"
    GIT = "git"
    GITHUB = "github"
    LONG_CONTEXT = "long_context"
    CODE_REVIEW = "code_review"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    DATA_ANALYSIS = "data_analysis"
    SHELL_EXECUTION = "shell_execution"
    PARALLEL_EXECUTION = "parallel_execution"


class CapabilityMetadata(BaseModel):
    id: AgentCapability
    name: str
    description: str
    risk_level: CapabilityRiskLevel
    required_tools: list[str] = Field(default_factory=list)
    minimum_context: int = 4096


# Central registry to hold metadata for each capability
CAPABILITY_REGISTRY: dict[AgentCapability, CapabilityMetadata] = {
    AgentCapability.CODING: CapabilityMetadata(
        id=AgentCapability.CODING,
        name="Coding",
        description="Write and edit code.",
        risk_level=CapabilityRiskLevel.MEDIUM,
    ),
    AgentCapability.DEBUGGING: CapabilityMetadata(
        id=AgentCapability.DEBUGGING,
        name="Debugging",
        description="Identify and fix software defects.",
        risk_level=CapabilityRiskLevel.MEDIUM,
    ),
    AgentCapability.REFACTORING: CapabilityMetadata(
        id=AgentCapability.REFACTORING,
        name="Refactoring",
        description="Improve code structure without changing behavior.",
        risk_level=CapabilityRiskLevel.MEDIUM,
    ),
    AgentCapability.PLANNING: CapabilityMetadata(
        id=AgentCapability.PLANNING,
        name="Planning",
        description="Deconstruct complex tasks into actionable steps.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.REASONING: CapabilityMetadata(
        id=AgentCapability.REASONING,
        name="Reasoning",
        description="Solve complex logical problems.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.ARCHITECTURE: CapabilityMetadata(
        id=AgentCapability.ARCHITECTURE,
        name="Architecture",
        description="Design system architecture and components.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.RESEARCH: CapabilityMetadata(
        id=AgentCapability.RESEARCH,
        name="Research",
        description="Gather information to solve unknown problems.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.BROWSER: CapabilityMetadata(
        id=AgentCapability.BROWSER,
        name="Browser Interaction",
        description="Interact with the web and websites.",
        risk_level=CapabilityRiskLevel.MEDIUM,
    ),
    AgentCapability.TERMINAL: CapabilityMetadata(
        id=AgentCapability.TERMINAL,
        name="Terminal Access",
        description="Execute commands in a terminal.",
        risk_level=CapabilityRiskLevel.HIGH,
    ),
    AgentCapability.REPO_NAVIGATION: CapabilityMetadata(
        id=AgentCapability.REPO_NAVIGATION,
        name="Repository Navigation",
        description="Traverse and search codebase directories.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.MULTI_FILE_EDITING: CapabilityMetadata(
        id=AgentCapability.MULTI_FILE_EDITING,
        name="Multi-file Editing",
        description="Coordinate edits across multiple files.",
        risk_level=CapabilityRiskLevel.MEDIUM,
    ),
    AgentCapability.TESTING: CapabilityMetadata(
        id=AgentCapability.TESTING,
        name="Testing",
        description="Run software tests.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.TEST_GENERATION: CapabilityMetadata(
        id=AgentCapability.TEST_GENERATION,
        name="Test Generation",
        description="Write new automated tests.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.SECURITY_ANALYSIS: CapabilityMetadata(
        id=AgentCapability.SECURITY_ANALYSIS,
        name="Security Analysis",
        description="Analyze code for vulnerabilities.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.DOCUMENTATION: CapabilityMetadata(
        id=AgentCapability.DOCUMENTATION,
        name="Documentation",
        description="Write and generate software documentation.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.GIT: CapabilityMetadata(
        id=AgentCapability.GIT,
        name="Git Operations",
        description="Execute git source control commands.",
        risk_level=CapabilityRiskLevel.MEDIUM,
    ),
    AgentCapability.GITHUB: CapabilityMetadata(
        id=AgentCapability.GITHUB,
        name="GitHub Integration",
        description="Interact with GitHub issues and PRs.",
        risk_level=CapabilityRiskLevel.MEDIUM,
    ),
    AgentCapability.LONG_CONTEXT: CapabilityMetadata(
        id=AgentCapability.LONG_CONTEXT,
        name="Long Context",
        description="Process extremely large documents or repositories.",
        risk_level=CapabilityRiskLevel.LOW,
        minimum_context=100000,
    ),
    AgentCapability.CODE_REVIEW: CapabilityMetadata(
        id=AgentCapability.CODE_REVIEW,
        name="Code Review",
        description="Review code diffs and PRs for quality.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.DEPENDENCY_ANALYSIS: CapabilityMetadata(
        id=AgentCapability.DEPENDENCY_ANALYSIS,
        name="Dependency Analysis",
        description="Analyze package dependencies and updates.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.PERFORMANCE_ANALYSIS: CapabilityMetadata(
        id=AgentCapability.PERFORMANCE_ANALYSIS,
        name="Performance Analysis",
        description="Analyze and optimize code performance.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.DATA_ANALYSIS: CapabilityMetadata(
        id=AgentCapability.DATA_ANALYSIS,
        name="Data Analysis",
        description="Process and analyze datasets.",
        risk_level=CapabilityRiskLevel.LOW,
    ),
    AgentCapability.SHELL_EXECUTION: CapabilityMetadata(
        id=AgentCapability.SHELL_EXECUTION,
        name="Shell Execution",
        description="Execute arbitrary shell scripts.",
        risk_level=CapabilityRiskLevel.CRITICAL,
    ),
    AgentCapability.PARALLEL_EXECUTION: CapabilityMetadata(
        id=AgentCapability.PARALLEL_EXECUTION,
        name="Parallel Execution",
        description="Spawn and coordinate multiple sub-agents.",
        risk_level=CapabilityRiskLevel.MEDIUM,
    ),
}


class CapabilityMatchResult(BaseModel):
    matched: bool
    missing: list[AgentCapability]
    extra: list[AgentCapability]
    score: float


def match_capabilities(required: set[AgentCapability], provided: set[AgentCapability]) -> CapabilityMatchResult:
    """
    Check if the provided capabilities satisfy the required capabilities.
    """
    missing = list(required - provided)
    extra = list(provided - required)
    
    matched = len(missing) == 0
    score = 1.0 if matched else (len(required) - len(missing)) / len(required) if required else 1.0
    
    return CapabilityMatchResult(
        matched=matched,
        missing=missing,
        extra=extra,
        score=score
    )
