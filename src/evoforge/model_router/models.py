from abc import ABC, abstractmethod
from typing import Any

import structlog
from pydantic import BaseModel, Field

from evoforge.agents.capabilities import AgentCapability

logger = structlog.get_logger(__name__)

class ModelMetadata(BaseModel):
    model_id: str
    provider_id: str
    display_name: str
    context_window: int
    capabilities: list[AgentCapability] = Field(default_factory=list)
    supports_tools: bool = False
    supports_structured_output: bool = False
    supports_vision: bool = False
    supports_parallel_tools: bool = False
    estimated_latency_ms: int = 1000
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    availability: bool = True
    version: str = "1.0"


class ModelProvider(ABC):
    """Abstract base class for a model provider (inference engine)."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for the provider (e.g. 'gemini', 'ollama')."""

    @abstractmethod
    def list_models(self) -> list[ModelMetadata]:
        """List all models currently provided by this provider."""

    @abstractmethod
    def get_model_metadata(self, model_id: str) -> ModelMetadata | None:
        """Get metadata for a specific model."""

    @abstractmethod
    def generate(self, model_id: str, prompt: str, **kwargs) -> Any:
        """
        Generate a completion using the specified model.
        Providers wrap litellm, google-genai, etc. inside here.
        """

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the provider is currently accessible."""


class ModelRegistry:
    """Registry tracking all known models across all providers."""
    def __init__(self):
        self._providers: dict[str, ModelProvider] = {}
        self._models: dict[str, ModelMetadata] = {}

    def register_provider(self, provider: ModelProvider):
        """Registers a model provider and caches its models."""
        if provider.provider_id in self._providers:
            raise ValueError(f"Provider '{provider.provider_id}' is already registered.")
            
        self._providers[provider.provider_id] = provider
        
        # Discover and register its models
        models = provider.list_models()
        for m in models:
            self._models[f"{provider.provider_id}/{m.model_id}"] = m
            
        logger.info("provider_registered", provider_id=provider.provider_id, model_count=len(models))

    def get_model(self, provider_id: str, model_id: str) -> ModelMetadata | None:
        """Get a specific model's metadata."""
        return self._models.get(f"{provider_id}/{model_id}")

    def get_provider(self, provider_id: str) -> ModelProvider:
        """Get a registered provider."""
        if provider_id not in self._providers:
            raise KeyError(f"Provider '{provider_id}' not found.")
        return self._providers[provider_id]

    def list_all_models(self) -> list[ModelMetadata]:
        """List all models from all registered providers."""
        return list(self._models.values())


class AntigravityExecutionRequest(BaseModel):
    task_id: str
    workflow_id: str
    agent_id: str | None = None
    repository_path: str | None = None
    branch: str | None = None
    task_description: str
    requirements: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    dry_run: bool = False
    timeout_seconds: int = 300
    working_directory: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AntigravityExecutionResult(BaseModel):
    success: bool
    status: str
    summary: str
    duration_ms: float = 0.0
    error_type: str | None = None
    error_message_sanitized: str | None = None
    exit_code: int | None = None
    session_id: str | None = None
    executor_id: str
    provider_id: str = "antigravity"
    model_id: str | None = None
    artifacts: list[str] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
