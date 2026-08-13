import time
from collections.abc import Callable
from typing import Any

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

class ExperimentResult(BaseModel):
    experiment_id: str
    variant: str
    success: bool
    score: float
    duration_ms: float
    metadata: dict[str, Any] = {}

class ExperimentFramework:
    def __init__(self, min_samples: int = 3, min_improvement_pct: float = 0.05):
        self.active_experiments = {}
        self.min_samples = min_samples
        self.min_improvement_pct = min_improvement_pct
        
    def run_ab_test(self, experiment_id: str, input_data: Any, variant_a: Callable, variant_b: Callable, evaluator: Callable) -> ExperimentResult:
        """Runs an A/B test between two variants (A=baseline, B=candidate)."""
        logger.info("experiment_started", experiment_id=experiment_id, samples=self.min_samples)
        
        scores_a = []
        scores_b = []
        durations_a = []
        durations_b = []
        
        for i in range(self.min_samples):
            # Run Variant A
            start_a = time.time()
            try:
                result_a = variant_a(input_data)
                score_a = evaluator(result_a)
                scores_a.append(score_a)
            except Exception as e:
                logger.error("variant_a_failed", error=str(e), sample=i)
                scores_a.append(0.0)
            durations_a.append((time.time() - start_a) * 1000)
                
            # Run Variant B
            start_b = time.time()
            try:
                result_b = variant_b(input_data)
                score_b = evaluator(result_b)
                scores_b.append(score_b)
            except Exception as e:
                logger.error("variant_b_failed", error=str(e), sample=i)
                scores_b.append(0.0)
            durations_b.append((time.time() - start_b) * 1000)
        
        avg_a = sum(scores_a) / len(scores_a)
        avg_b = sum(scores_b) / len(scores_b)
        
        avg_dur_a = sum(durations_a) / len(durations_a)
        avg_dur_b = sum(durations_b) / len(durations_b)
        
        # Check thresholds for B to win
        improvement = avg_b - avg_a
        regression = any(sb < sa for sa, sb in zip(scores_a, scores_b)) # strict no regression check per sample
        
        metadata = {
            "scores_a": scores_a,
            "scores_b": scores_b,
            "improvement": improvement,
            "regression_detected": regression
        }
        
        if improvement >= self.min_improvement_pct and not regression:
            winner = "B"
            final_score = avg_b
            final_duration = avg_dur_b
            final_success = True
        else:
            winner = "A"
            final_score = avg_a
            final_duration = avg_dur_a
            final_success = True if avg_a > 0 else False
            
        logger.info("experiment_completed", experiment_id=experiment_id, winner=winner, score=final_score, improvement=improvement, regression=regression)
        
        return ExperimentResult(
            experiment_id=experiment_id,
            variant=winner,
            success=final_success,
            score=final_score,
            duration_ms=final_duration,
            metadata=metadata
        )
