from pydantic import BaseModel
from typing import List, Dict, Optional
from .classifier import TaskType

class ModelConfig(BaseModel):
    model_id: str
    max_context: int
    strengths: List[TaskType]
    cost_tier: str  # "free", "cheap", "moderate", "expensive"
    reliability_score: float = 1.0  # 0.0 to 1.0

class RateLimit(BaseModel):
    rpm: int  # Requests per minute
    tpm: int  # Tokens per minute

class ProviderConfig(BaseModel):
    name: str
    api_type: str  # "openai", "google", "nvidia", "ollama"
    base_url: Optional[str] = None
    models: Dict[str, ModelConfig]
    rate_limit: RateLimit
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_context_tokens: int
    is_local: bool

# Default provider configurations
DEFAULT_PROVIDERS = {
    "ollama": ProviderConfig(
        name="ollama",
        api_type="ollama",
        base_url="http://localhost:11434",
        models={
            "coder": ModelConfig(
                model_id="qwen2.5-coder:7b-instruct-q4_K_M",
                max_context=32768,
                strengths=[TaskType.CODE_EDITING, TaskType.SUMMARIZATION],
                cost_tier="free"
            ),
            "general": ModelConfig(
                model_id="llama3.1:8b-instruct-q4_K_M",
                max_context=8192,
                strengths=[TaskType.CLASSIFICATION, TaskType.DOCUMENTATION],
                cost_tier="free"
            )
        },
        rate_limit=RateLimit(rpm=9999, tpm=9999999),
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        max_context_tokens=32768,
        is_local=True
    ),
    "gemini": ProviderConfig(
        name="gemini",
        api_type="google",
        models={
            "pro": ModelConfig(
                model_id="gemini/gemini-3.1-pro",
                max_context=1000000,
                strengths=[TaskType.REASONING, TaskType.PLANNING, TaskType.CODE_REVIEW],
                cost_tier="expensive"
            ),
            "flash": ModelConfig(
                model_id="gemini/gemini-3.6-flash",
                max_context=1000000,
                strengths=[TaskType.CODE_GENERATION, TaskType.RESEARCH],
                cost_tier="moderate"
            )
        },
        rate_limit=RateLimit(rpm=15, tpm=1000000), # Assuming free tier for defaults
        cost_per_1k_input=0.0015,
        cost_per_1k_output=0.0075,
        max_context_tokens=1000000,
        is_local=False
    ),
    "nvidia": ProviderConfig(
        name="nvidia",
        api_type="openai",
        base_url="https://integrate.api.nvidia.com/v1",
        models={
            "deepseek": ModelConfig(
                model_id="deepseek-ai/deepseek-coder-33b-instruct",
                max_context=16384,
                strengths=[TaskType.CODE_GENERATION, TaskType.SECURITY_ANALYSIS],
                cost_tier="moderate"
            )
        },
        rate_limit=RateLimit(rpm=40, tpm=100000),
        cost_per_1k_input=0.001,  # Approximate costs
        cost_per_1k_output=0.002,
        max_context_tokens=16384,
        is_local=False
    )
}
