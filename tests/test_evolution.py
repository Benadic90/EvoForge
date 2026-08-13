import os
import tempfile
from unittest.mock import MagicMock

from evoforge.agents.registry import ToolRegistry
from evoforge.evolution.agent import EvolutionAgent
from evoforge.evolution.experiment import ExperimentFramework
from evoforge.evolution.metrics import PerformanceMonitor
from evoforge.memory.database import Database
from evoforge.model_router.router import ModelRouter


def test_evolution_agent():
    router = MagicMock(spec=ModelRouter)
    tools = ToolRegistry()
    db = MagicMock(spec=Database)
    
    agent = EvolutionAgent(router, tools, db=db)
    assert agent.name == "EvolutionAgent"

def test_experiment_framework():
    from evoforge.learning.models import ApprovalPolicy
    db = MagicMock(spec=Database)
    policy = ApprovalPolicy(risk_level="LOW", requires_human=True, minimum_samples=1, minimum_improvement=0.05, maximum_regression=0.0)
    framework = ExperimentFramework(db, policy)
    
    def variant_a(data): return data + 1
    def variant_b(data): return data + 2
    from evoforge.evolution.experiment import MultiMetricScore
    def evaluator(result): return MultiMetricScore(quality=float(result)) # Higher is better
    
    result = framework.run_multi_metric_ab_test(
        "test-exp-1", "prop1", "tgt", "ds", [1, 1, 1, 1, 1], variant_a, variant_b, evaluator
    )
    
    assert result.experiment_id == "test-exp-1"
    assert result.status == "PASSED" # 1+2 = 3 > 1+1 = 2
    assert result.candidate_score > result.baseline_score

def test_performance_monitor():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(db_path)
        
        monitor = PerformanceMonitor(db)
        
        # Record some metrics
        monitor.record_metric("llm_latency", 150.0)
        monitor.record_metric("llm_latency", 250.0)
        
        baseline = monitor.get_baseline("llm_latency")
        assert baseline == 200.0 # Average
