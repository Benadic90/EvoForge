import json
import time
from typing import Any

import structlog
from pydantic import BaseModel, Field

from evoforge.agents.capabilities import match_capabilities
from evoforge.agents.contracts import AgentExecutor
from evoforge.model_router.executors import ExecutorRegistry
from evoforge.model_router.requirements import TaskRequirements

logger = structlog.get_logger(__name__)


class CandidateScore(BaseModel):
    executor_id: str
    score: float
    reasons: list[str] = Field(default_factory=list)


class RoutingExplanation(BaseModel):
    selected_executor_id: str
    score: float
    policy_version: str = "adaptive-v1"
    reasons: list[str] = Field(default_factory=list)
    candidates: list[CandidateScore] = Field(default_factory=list)
    rejected: dict[str, list[str]] = Field(default_factory=dict)


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
    """Adaptive Model & Executor Router (Policy: adaptive-v1).
    
    Dynamically scores execution backends using:
    - Capability matching & policy constraints
    - Historical success with Bayesian Laplace smoothing
    - Recency-decay weighted performance (7-day half-life)
    - Task-specific historical performance slicing
    - Multi-factor engineering quality outcomes (tests, reviews, quality scores)
    - Latency, cost, and fallback penalty factors
    - Durable routing decision persistence for full auditability
    """

    POLICY_VERSION = "adaptive-v1"

    def __init__(self, executor_registry: ExecutorRegistry, memory_manager: Any = None):
        self.registry = executor_registry
        self.memory = memory_manager
        self.circuit_breaker = CircuitBreaker()
        self.weights = {
            "capability_match": 0.35,
            "historical_success": 0.15,
            "recency_performance": 0.15,
            "task_specific_success": 0.15,
            "quality_score": 0.10,
            "reliability": 0.05,
            "cost_penalty": 0.025,
            "latency_penalty": 0.025,
        }

    def _get_empirical_stats(self, executor_id: str) -> dict[str, float | int]:
        """Fetch empirical performance metrics from SQLite if memory system is connected."""
        if self.memory and hasattr(self.memory, "get_executor_stats"):
            try:
                stats_dict = self.memory.get_executor_stats(executor_id)
                if executor_id in stats_dict:
                    return stats_dict[executor_id]
            except Exception as e:
                logger.warning("stats_lookup_failed", executor_id=executor_id, error=str(e))

        # Default prior for unobserved executors
        return {
            "total_runs": 0,
            "successful_runs": 0,
            "success_rate": 0.85,
            "avg_duration_ms": 1000.0,
            "avg_cost_usd": 0.01,
            "avg_quality_score": 0.90,
            "fallback_rate": 0.0,
        }

    def _get_recency_stats(self, executor_id: str, task_type: str | None = None) -> dict[str, float | int]:
        """Fetch recency-decay weighted statistics (half-life 7 days)."""
        if self.memory and hasattr(self.memory, "get_recency_weighted_stats"):
            try:
                return self.memory.get_recency_weighted_stats(executor_id, half_life_days=7.0, task_type=task_type)
            except Exception as e:
                logger.warning("recency_stats_lookup_failed", executor_id=executor_id, error=str(e))

        return {
            "total_runs": 0,
            "successful_runs": 0,
            "raw_success_rate": 0.85,
            "weighted_success_rate": 0.85,
            "weighted_quality_score": 0.90,
            "avg_duration_ms": 1000.0,
            "avg_cost_usd": 0.01,
        }

    def _get_task_specific_stats(self, executor_id: str, task_type: str) -> dict[str, float | int] | None:
        """Fetch task-specific historical statistics."""
        if self.memory and hasattr(self.memory, "get_task_type_stats"):
            try:
                rows = self.memory.get_task_type_stats(task_type=task_type, executor_id=executor_id)
                if rows:
                    return rows[0]
            except Exception as e:
                logger.warning("task_type_stats_lookup_failed", executor_id=executor_id, error=str(e))
        return None

    def get_candidate_chain(
        self, req: TaskRequirements, workflow_id: str = "workflow_standalone", agent_id: str | None = None
    ) -> tuple[list[tuple[str, AgentExecutor]], RoutingExplanation]:
        """Returns all eligible executors ranked by adaptive empirical score and persists the decision."""
        candidates = self.registry.list_all()
        scored_candidates: list[tuple[str, float, list[str]]] = []
        rejected: dict[str, list[str]] = {}

        task_type_str = req.task_type.value if hasattr(req.task_type, "value") else str(req.task_type)

        for exc_id in candidates:
            # 1. Check Circuit Breaker & Health
            if not self.registry.is_enabled(exc_id):
                rejected[exc_id] = ["Executor is administratively disabled."]
                continue
            if not self.registry.is_healthy(exc_id):
                rejected[exc_id] = ["Executor health check failed / provider unavailable."]
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

            # 3. Privacy Policy Filter
            is_cloud = "gemini" in exc_id or "nvidia" in exc_id
            if req.privacy_requirement > 0.8 and is_cloud:
                rejected[exc_id] = ["Violates privacy requirements (requires local executor)."]
                continue

            # 4. Global Historical Stats + Bayesian Smoothing
            stats = self._get_empirical_stats(exc_id)
            total_runs = int(stats.get("total_runs", 0))
            succ_runs = int(stats.get("successful_runs", 0))

            if total_runs > 0:
                smoothed_success_rate = (succ_runs + 4.0) / (total_runs + 5.0)
            else:
                smoothed_success_rate = 0.85

            # 5. Recency-Decay Performance
            recency_stats = self._get_recency_stats(exc_id)
            recency_success = float(recency_stats.get("weighted_success_rate", smoothed_success_rate))
            recency_quality = float(recency_stats.get("weighted_quality_score", 0.90))

            # 6. Task-Specific Performance
            task_stats = self._get_task_specific_stats(exc_id, task_type_str)
            if task_stats and int(task_stats.get("total_runs", 0)) >= 3:
                t_total = int(task_stats["total_runs"])
                t_succ = int(task_stats["successful_runs"])
                task_success_rate = (t_succ + 4.0) / (t_total + 5.0)
                task_reason = f"Task-type '{task_type_str}' empirical success: {task_stats['success_rate']*100:.1f}% ({t_total} runs)"
            else:
                task_success_rate = smoothed_success_rate
                task_reason = f"Task-type '{task_type_str}' using smoothed baseline: {smoothed_success_rate*100:.1f}%"

            # 7. Quality & Verification Outcomes
            hist_quality = float(stats.get("avg_quality_score", 0.90))
            blended_quality = 0.5 * hist_quality + 0.5 * recency_quality
            avg_duration_ms = float(stats.get("avg_duration_ms", 1000.0))
            avg_cost_usd = float(stats.get("avg_cost_usd", 0.01))
            fallback_rate = float(stats.get("fallback_rate", 0.0))

            # Weighted Scoring Formula (adaptive-v1)
            base_cap_score = match_res.score * self.weights["capability_match"]
            hist_succ_part = smoothed_success_rate * self.weights["historical_success"]
            recency_part = recency_success * self.weights["recency_performance"]
            task_succ_part = task_success_rate * self.weights["task_specific_success"]
            quality_part = blended_quality * self.weights["quality_score"]
            reliability_part = 0.95 * self.weights["reliability"]

            # Normalized Penalties
            cost_penalty = min(avg_cost_usd / 0.10, 1.0) * self.weights["cost_penalty"] * req.cost_preference
            latency_penalty = min(avg_duration_ms / 10000.0, 1.0) * self.weights["latency_penalty"] * req.latency_preference
            fallback_penalty = fallback_rate * 0.05

            final_score = (
                base_cap_score
                + hist_succ_part
                + recency_part
                + task_succ_part
                + quality_part
                + reliability_part
                - cost_penalty
                - latency_penalty
                - fallback_penalty
            )

            raw_rate = float(stats.get("success_rate", 0.85))
            reasons = [
                f"Capability match: {match_res.score:.2f}",
                f"Empirical success: {raw_rate * 100:.1f}% ({total_runs} runs, smoothed: {smoothed_success_rate * 100:.1f}%)",
                f"Recent 7-day weighted success: {recency_success * 100:.1f}%",
                task_reason,
                f"Blended quality rating: {blended_quality:.2f}",
            ]

            if req.privacy_requirement <= 0.8:
                reasons.append("Passes privacy policy check.")

            scored_candidates.append((exc_id, final_score, reasons))

        if not scored_candidates:
            raise RuntimeError(f"No available executors for task {req.task_id}. Rejections: {rejected}")

        # Sort descending by adaptive empirical score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        candidate_chain = [(eid, self.registry.get(eid)) for eid, _, _ in scored_candidates]
        candidate_scores = [
            CandidateScore(executor_id=eid, score=score, reasons=reasons)
            for eid, score, reasons in scored_candidates
        ]

        best_id, best_score, best_reasons = scored_candidates[0]

        explanation = RoutingExplanation(
            selected_executor_id=best_id,
            score=best_score,
            policy_version=self.POLICY_VERSION,
            reasons=best_reasons,
            candidates=candidate_scores,
            rejected=rejected,
        )

        # Persist the routing decision to database if memory manager is active
        if self.memory and hasattr(self.memory, "record_routing_decision"):
            try:
                self.memory.record_routing_decision(
                    task_id=req.task_id,
                    workflow_id=workflow_id,
                    selected_executor_id=best_id,
                    selected_score=best_score,
                    decision_reason="; ".join(best_reasons),
                    agent_id=agent_id,
                    task_type=task_type_str,
                    requirements_json=req.model_dump_json(),
                    candidate_rankings_json=json.dumps([c.model_dump() for c in candidate_scores]),
                    routing_policy_version=self.POLICY_VERSION,
                )
            except Exception as e:
                logger.warning("routing_decision_persist_failed", error=str(e), task_id=req.task_id)

        logger.info(
            "adaptive_executor_ranked_chain",
            policy=self.POLICY_VERSION,
            top_executor=best_id,
            top_score=best_score,
            candidate_count=len(candidate_chain),
            task_id=req.task_id,
        )

        return candidate_chain, explanation

    def select_executor(
        self, req: TaskRequirements, workflow_id: str = "workflow_standalone", agent_id: str | None = None
    ) -> tuple[AgentExecutor, RoutingExplanation]:
        """Selects the top-ranked executor."""
        chain, explanation = self.get_candidate_chain(req, workflow_id=workflow_id, agent_id=agent_id)
        return chain[0][1], explanation

