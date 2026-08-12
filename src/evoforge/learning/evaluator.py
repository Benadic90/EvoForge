from typing import Any

import structlog
from pydantic import BaseModel

from evoforge.learning.benchmark_runner import BenchmarkResult, BenchmarkRunner, BenchmarkSuite
from evoforge.learning.evolution_proposer import EvolutionProposal
from evoforge.utils.config import LearningConfig

logger = structlog.get_logger(__name__)

class EvaluationResult(BaseModel):
    proposal: EvolutionProposal
    approved: bool
    benchmark_result: BenchmarkResult
    reasoning: str

class SkillEvaluator:
    def __init__(self, runner: BenchmarkRunner, config: LearningConfig):
        self.runner = runner
        self.config = config

    def evaluate_proposal(self, proposal: EvolutionProposal, agent_instance: Any, suite: BenchmarkSuite) -> EvaluationResult:
        """Evaluates a proposed skill update against the agent's benchmark suite."""
        logger.info("evaluating_proposal", agent=proposal.agent_name, skill=proposal.skill_name)
        
        # 1. Apply the proposal changes to the agent_instance temporarily
        # In MVP we assume agent_instance is a mocked copy inside the sandbox
        # and has its skill_profile loaded.
        
        # 2. Run the benchmark suite
        benchmark_result = self.runner.run_suite(suite, agent_instance)
        
        # 3. Compare to baseline & apply auto-deploy policy
        approved, reasoning = self._approve_or_reject(benchmark_result)
        
        logger.info("evaluation_completed", approved=approved, improvement=benchmark_result.improvement_pct)
        
        return EvaluationResult(
            proposal=proposal,
            approved=approved,
            benchmark_result=benchmark_result,
            reasoning=reasoning
        )

    def _approve_or_reject(self, result: BenchmarkResult) -> tuple[bool, str]:
        """Determines if the benchmark result meets the threshold for automatic deployment."""
        if not result.success:
            return False, "Benchmark failed (Regression detected)."
            
        if result.improvement_pct >= self.config.auto_deploy_threshold:
            # We assume confidence was evaluated during proposal/research phase
            # For MVP, we check just the threshold.
            return True, f"Improvement {result.improvement_pct:.2f} meets threshold {self.config.auto_deploy_threshold}."
            
        return False, f"Improvement {result.improvement_pct:.2f} is below threshold {self.config.auto_deploy_threshold}. Requires human PR review."

    def run_regression(self, agent_instance: Any, full_suite: BenchmarkSuite) -> bool:
        """Runs a full regression suite to ensure no existing capabilities broke."""
        result = self.runner.run_suite(full_suite, agent_instance)
        return result.success
