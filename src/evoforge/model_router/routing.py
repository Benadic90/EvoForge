import time
from typing import Optional
from pydantic import BaseModel

import structlog

from evoforge.agents.capabilities import match_capabilities
from evoforge.agents.contracts import AgentExecutor
from evoforge.model_router.executors import ExecutorRegistry
from evoforge.model_router.requirements import TaskRequirements

logger = structlog.get_logger(__name__)


class RoutingExplanation(BaseModel):
    selected_executor_id: str
    score: float
    reasons: list[str]
    rejected: dict[str, list[str]]


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, cooldown_seconds: int = 300):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        
        self.failures: dict[str, int] = {}
        self.cooldown_until: dict[str, float] = {}

    def record_success(self, executor_id: str):
        self.failures[executor_id] = 0
        if executor_id in self.cooldown_until:
            del self.cooldown_until[executor_id]

    def record_failure(self, executor_id: str):
        count = self.failures.get(executor_id, 0) + 1
        self.failures[executor_id] = count
        if count >= self.failure_threshold:
            self.cooldown_until[executor_id] = time.time() + self.cooldown_seconds
            logger.warning("circuit_breaker_tripped", executor_id=executor_id, cooldown=self.cooldown_seconds)

    def is_available(self, executor_id: str) -> bool:
        if executor_id in self.cooldown_until:
            if time.time() > self.cooldown_until[executor_id]:
                # Cooldown expired
                del self.cooldown_until[executor_id]
                self.failures[executor_id] = 0
                return True
            return False
        return True


class ExecutorRouter:
    """Routes a task to the most appropriate Executor."""
    def __init__(self, executor_registry: ExecutorRegistry):
        self.registry = executor_registry
        self.circuit_breaker = CircuitBreaker()
        # In a real system, these weights could come from a config or policy engine
        self.weights = {
            "capability_match": 0.40,
            "quality_score": 0.25,
            "historical_success": 0.15,
            "reliability": 0.10,
            "cost_penalty": 0.05,
            "latency_penalty": 0.05
        }

    def select_executor(self, req: TaskRequirements) -> tuple[AgentExecutor, RoutingExplanation]:
        candidates = self.registry.list_all()
        scored_candidates = []
        rejected = {}
        
        for exc_id in candidates:
            # 1. Check Circuit Breaker & Health
            if not self.registry.is_healthy(exc_id):
                rejected[exc_id] = ["Executor marked unhealthy."]
                continue
            if not self.registry.is_enabled(exc_id):
                rejected[exc_id] = ["Executor is administratively disabled."]
                continue
            if not self.circuit_breaker.is_available(exc_id):
                rejected[exc_id] = ["Circuit breaker is open (cooling down after failures)."]
                continue

            # 2. Capability Matching
            caps = self.registry.get_capabilities(exc_id)
            match_res = match_capabilities(set(req.required_capabilities), set(caps))
            
            if not match_res.matched:
                missing_str = [c.value for c in match_res.missing]
                rejected[exc_id] = [f"Missing required capabilities: {missing_str}"]
                continue
                
            # 3. Privacy Policy Filter (stubbed for now)
            # If req.privacy_requirement is high, and this is a cloud provider, we reject.
            is_cloud = "gemini" in exc_id or "nvidia" in exc_id # Simple heuristic for now
            if req.privacy_requirement > 0.8 and is_cloud:
                rejected[exc_id] = ["Violates privacy requirements (requires local)."]
                continue

            # 4. Scoring
            # Score base is capability match score. We will enrich it with historical data later.
            base_score = match_res.score * self.weights["capability_match"]
            
            # Historical success/reliability (mocked to 0.9 for now)
            hist_score = 0.9 * (self.weights["quality_score"] + self.weights["historical_success"] + self.weights["reliability"])
            
            # Cost/Latency penalties (mocked)
            cost_pen = 0.1 * self.weights["cost_penalty"] * req.cost_preference
            lat_pen = 0.1 * self.weights["latency_penalty"] * req.latency_preference
            
            final_score = base_score + hist_score - cost_pen - lat_pen
            
            reasons = [f"Capability match score: {match_res.score:.2f}"]
            if req.privacy_requirement < 0.8:
                reasons.append("Passes privacy/policy checks.")
                
            scored_candidates.append((exc_id, final_score, reasons))

        if not scored_candidates:
            raise RuntimeError(f"No available executors for task {req.task_id}. Rejections: {rejected}")

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_id, best_score, best_reasons = scored_candidates[0]

        explanation = RoutingExplanation(
            selected_executor_id=best_id,
            score=best_score,
            reasons=best_reasons,
            rejected=rejected
        )

        logger.info("executor_selected", executor_id=best_id, score=best_score, task_id=req.task_id)
        
        return self.registry.get(best_id), explanation
