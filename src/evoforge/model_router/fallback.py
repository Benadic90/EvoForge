import time
from collections.abc import Callable

import litellm
import structlog

from .router import LLMRequest, LLMResponse, ModelRouter

logger = structlog.get_logger(__name__)

class FallbackManager:
    def __init__(self, router: ModelRouter, max_retries: int = 3):
        self.router = router
        self.max_retries = max_retries
        self.fallback_chain = ["gemini", "nvidia", "ollama"] # Simple static chain for MVP

    def complete_with_fallback(self, request: LLMRequest) -> LLMResponse:
        """Executes an LLM request with retry and fallback logic."""
        
        # Try the router's primary selection first
        try:
            return self._execute_with_retry(self.router.complete, request)
        except Exception as e:
            logger.warning("primary_model_failed", error=str(e), fallback_chain=self.fallback_chain)
            
        # If primary fails, try fallbacks
        for provider in self.fallback_chain:
            if provider == request.preferred_provider:
                continue # Already tried
                
            logger.info("attempting_fallback", provider=provider)
            fallback_request = request.model_copy(update={"preferred_provider": provider})
            
            try:
                return self._execute_with_retry(self.router.complete, fallback_request)
            except Exception as e:
                logger.warning("fallback_model_failed", provider=provider, error=str(e))
                
        logger.error("all_models_failed")
        raise RuntimeError("All LLM providers failed to complete the request.")

    def _execute_with_retry(self, func: Callable, request: LLMRequest) -> LLMResponse:
        """Executes a function with exponential backoff on transient errors."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return func(request)
            except litellm.exceptions.RateLimitError as e:
                last_error = e
                sleep_time = 2 ** attempt
                logger.warning("rate_limit_hit", attempt=attempt+1, sleep=sleep_time)
                time.sleep(sleep_time)
            except litellm.exceptions.APIConnectionError as e:
                last_error = e
                sleep_time = 2 ** attempt
                logger.warning("connection_error", attempt=attempt+1, sleep=sleep_time)
                time.sleep(sleep_time)
            except Exception as e:
                # For non-transient errors (like invalid auth or bad request), fail fast
                raise e
                
        raise last_error or Exception("Max retries exceeded")
