from enum import Enum


class TaskComplexity(Enum):
    TRIVIAL = "trivial"      # Classification, simple formatting
    LOW = "low"              # Summarization, documentation, simple code edits
    MEDIUM = "medium"        # Bug fixes, test writing, code review
    HIGH = "high"            # Feature implementation, architecture design
    CRITICAL = "critical"    # Security analysis, complex refactoring

class TaskType(Enum):
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_EDITING = "code_editing"
    REASONING = "reasoning"
    PLANNING = "planning"
    DOCUMENTATION = "documentation"
    SECURITY_ANALYSIS = "security_analysis"
    RESEARCH = "research"
