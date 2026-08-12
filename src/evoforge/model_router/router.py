import litellm
import structlog
from typing import Optional, Dict, Any
from pydantic import BaseModel
from .classifier import TaskType, TaskComplexity
from .providers import DEFAULT_PROVIDERS, ProviderConfig

logger = structlog.get_logger(__name__)

class LLMRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    task_type: TaskType
    complexity: TaskComplexity
    max_tokens: int = 1000
    temperature: float = 0.2
    preferred_provider: Optional[str] = None
    require_json: bool = False

class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int

class ModelRouter:
    def __init__(self, providers: Dict[str, ProviderConfig] = DEFAULT_PROVIDERS):
        self.providers = providers
        # Configure litellm logging if needed
        litellm.suppress_debug_info = True

    def _select_model(self, request: LLMRequest) -> tuple[str, str]:
        """Selects provider and model based on routing table (simplified for MVP)."""
        if request.preferred_provider and request.preferred_provider in self.providers:
            provider = self.providers[request.preferred_provider]
            # Simple heuristic: pick the first model that supports the task type
            for model_key, model_config in provider.models.items():
                if request.task_type in model_config.strengths:
                    return request.preferred_provider, model_config.model_id
            
            # Fallback to first model in preferred provider
            return request.preferred_provider, list(provider.models.values())[0].model_id
            
        # Default routing logic
        if request.complexity in [TaskComplexity.TRIVIAL, TaskComplexity.LOW]:
            # Try local first
            if "ollama" in self.providers:
                return "ollama", self.providers["ollama"].models["general"].model_id
        
        # Default to Gemini for complex tasks
        return "gemini", self.providers["gemini"].models["flash"].model_id

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Route an LLM request to the optimal provider using litellm."""
        provider_name, model_id = self._select_model(request)
        provider = self.providers.get(provider_name)
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        kwargs: Dict[str, Any] = {
            "model": model_id,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        if provider and provider.base_url:
            kwargs["api_base"] = provider.base_url

        if request.require_json:
            kwargs["response_format"] = {"type": "json_object"}

        logger.debug("llm_request_started", provider=provider_name, model=model_id, task_type=request.task_type.value)

        try:
            # Note: API keys are expected to be in environment variables (e.g., GEMINI_API_KEY, NVIDIA_API_KEY)
            # litellm automatically picks them up.
            response = litellm.completion(**kwargs)
            
            usage = response.usage
            cost = litellm.completion_cost(completion_response=response) if not (provider and provider.is_local) else 0.0
            
            # litellm doesn't provide precise latency natively in standard response, just estimating or capturing if possible.
            # We'll use a placeholder for latency_ms for now.
            latency = 0 
            
            logger.info("llm_request_completed", 
                        provider=provider_name, 
                        model=model_id, 
                        input_tokens=usage.prompt_tokens,
                        output_tokens=usage.completion_tokens,
                        cost=cost)

            return LLMResponse(
                content=response.choices[0].message.content,
                provider=provider_name,
                model=model_id,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                cost_usd=cost or 0.0,
                latency_ms=latency
            )
        except Exception as e:
            logger.error("llm_request_failed", provider=provider_name, model=model_id, error=str(e))
            raise # Let a fallback manager handle this
