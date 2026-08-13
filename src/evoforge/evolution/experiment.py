import time
from collections.abc import Callable
from typing import Any
from datetime import UTC, datetime

import structlog
from pydantic import BaseModel

from evoforge.learning.models import ApprovalPolicy, ExperimentRecord
from evoforge.memory.database import Database

logger = structlog.get_logger(__name__)

class ExperimentResult(BaseModel):
    experiment_id: str
    variant: str
    success: bool
    score: float
    duration_ms: float
    metadata: dict[str, Any] = {}

class MultiMetricScore(BaseModel):
    quality: float = 0.0
    reliability: float = 0.0
    security: float = 0.0
    latency_ms: float = 0.0
    cost: float = 0.0
    test_success: float = 0.0
    review_success: float = 0.0

class MultiMetricWeights(BaseModel):
    quality: float = 1.0
    reliability: float = 1.0
    security: float = 2.0
    latency: float = -0.1
    cost: float = -0.5
    test_success: float = 1.5
    review_success: float = 1.0

class ExperimentFramework:
    def __init__(self, db: Database, policy: ApprovalPolicy, weights: MultiMetricWeights | None = None):
        self.db = db
        self.policy = policy
        self.weights = weights or MultiMetricWeights()
        self.active_experiments = {}

    def _compute_composite_score(self, metrics: MultiMetricScore) -> float:
        score = (
            metrics.quality * self.weights.quality +
            metrics.reliability * self.weights.reliability +
            metrics.security * self.weights.security +
            metrics.test_success * self.weights.test_success +
            metrics.review_success * self.weights.review_success +
            (metrics.latency_ms / 1000.0) * self.weights.latency +
            metrics.cost * self.weights.cost
        )
        return score

    def run_multi_metric_ab_test(
        self, 
        experiment_id: str, 
        proposal_id: str,
        target: str,
        dataset: str,
        input_data: list[Any], 
        variant_a: Callable, 
        variant_b: Callable, 
        evaluator: Callable[[Any], MultiMetricScore]
    ) -> ExperimentRecord:
        """Runs an A/B test enforcing multi-metric thresholds and regression limits."""
        logger.info("experiment_started", experiment_id=experiment_id, samples=self.policy.minimum_samples)
        
        sample_count = max(len(input_data), self.policy.minimum_samples)
        
        scores_a = []
        scores_b = []
        durations_a = []
        durations_b = []
        regressions = 0
        total_cost = 0.0

        for i in range(sample_count):
            data = input_data[i % len(input_data)]
            
            # Variant A (Baseline)
            start_a = time.time()
            try:
                res_a = variant_a(data)
                metric_a = evaluator(res_a)
                score_a = self._compute_composite_score(metric_a)
                scores_a.append(score_a)
            except Exception as e:
                logger.error("variant_a_failed", error=str(e), sample=i)
                scores_a.append(0.0)
                metric_a = MultiMetricScore()
            durations_a.append((time.time() - start_a) * 1000)

            # Variant B (Candidate)
            start_b = time.time()
            try:
                res_b = variant_b(data)
                metric_b = evaluator(res_b)
                score_b = self._compute_composite_score(metric_b)
                scores_b.append(score_b)
            except Exception as e:
                logger.error("variant_b_failed", error=str(e), sample=i)
                scores_b.append(0.0)
                metric_b = MultiMetricScore()
            dur_b = (time.time() - start_b) * 1000
            durations_b.append(dur_b)
            
            total_cost += metric_a.cost + metric_b.cost
            
            # Strict no-regression check for this sample
            if score_b < score_a * (1.0 - self.policy.maximum_regression):
                regressions += 1
                
        avg_a = sum(scores_a) / len(scores_a) if scores_a else 0.0
        avg_b = sum(scores_b) / len(scores_b) if scores_b else 0.0
        
        avg_dur_a = sum(durations_a) / len(durations_a) if durations_a else 0.0
        avg_dur_b = sum(durations_b) / len(durations_b) if durations_b else 0.0
        
        improvement_percent = (avg_b - avg_a) / abs(avg_a) if avg_a != 0 else (1.0 if avg_b > 0 else 0.0)

        status = "FAILED"
        if improvement_percent >= self.policy.minimum_improvement and regressions == 0:
            status = "PASSED"
        
        record = ExperimentRecord(
            experiment_id=experiment_id,
            proposal_id=proposal_id,
            baseline_version="v_current",
            candidate_version="v_candidate",
            target=target,
            dataset=dataset,
            sample_count=sample_count,
            baseline_score=avg_a,
            candidate_score=avg_b,
            improvement_percent=improvement_percent,
            regressions=regressions,
            cost=total_cost,
            latency=avg_dur_b,
            status=status,
            environment="sandbox"
        )
        record.completed_at = datetime.now(UTC)
        
        self.persist_experiment(record)
        return record

    def persist_experiment(self, record: ExperimentRecord):
        query = """
            INSERT INTO experiment_records (
                experiment_id, proposal_id, baseline_version, candidate_version, target, dataset,
                sample_count, started_at, completed_at, baseline_score, candidate_score,
                improvement_percent, regressions, cost, latency, status, environment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(query, (
            record.experiment_id, record.proposal_id, record.baseline_version, record.candidate_version,
            record.target, record.dataset, record.sample_count, record.started_at, record.completed_at,
            record.baseline_score, record.candidate_score, record.improvement_percent, record.regressions,
            record.cost, record.latency, record.status, record.environment
        ))
        logger.info("experiment_persisted", experiment_id=record.experiment_id, status=record.status)
