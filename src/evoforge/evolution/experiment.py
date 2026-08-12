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
    def __init__(self):
        self.active_experiments = {}
        
    def run_ab_test(self, experiment_id: str, input_data: Any, variant_a: Callable, variant_b: Callable, evaluator: Callable) -> ExperimentResult:
        """Runs an A/B test between two variants of an agent, prompt, or tool."""
        logger.info("experiment_started", experiment_id=experiment_id)
        
        # Run Variant A
        start_a = time.time()
        try:
            result_a = variant_a(input_data)
            score_a = evaluator(result_a)
            success_a = True
        except Exception as e:
            logger.error("variant_a_failed", error=str(e))
            score_a = 0.0
            success_a = False
        duration_a = (time.time() - start_a) * 1000
            
        # Run Variant B
        start_b = time.time()
        try:
            result_b = variant_b(input_data)
            score_b = evaluator(result_b)
            success_b = True
        except Exception as e:
            logger.error("variant_b_failed", error=str(e))
            score_b = 0.0
            success_b = False
        duration_b = (time.time() - start_b) * 1000
        
        # Determine winner
        if score_a >= score_b:
            winner = "A"
            final_score = score_a
            final_duration = duration_a
            final_success = success_a
        else:
            winner = "B"
            final_score = score_b
            final_duration = duration_b
            final_success = success_b
            
        logger.info("experiment_completed", experiment_id=experiment_id, winner=winner, score=final_score)
        
        return ExperimentResult(
            experiment_id=experiment_id,
            variant=winner,
            success=final_success,
            score=final_score,
            duration_ms=final_duration
        )
