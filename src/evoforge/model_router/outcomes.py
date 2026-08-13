from typing import Any

from pydantic import BaseModel, Field


class ExecutionOutcome(BaseModel):
    """Structured representation of task execution outcomes and engineering verification."""
    success: bool
    quality_score: float | None = None
    tests_passed: bool | None = None
    review_passed: bool | None = None
    security_passed: bool | None = None
    artifact_valid: bool | None = None
    human_approved: bool | None = None
    duration_ms: float = 0.0
    fallback_used: bool = False
    retry_count: int = 0
    failure_class: str | None = None
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
