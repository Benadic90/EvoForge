import pytest
import tempfile
import os
from unittest.mock import MagicMock
from evoforge.evolution.agent import EvolutionAgent
from evoforge.evolution.experiment import ExperimentFramework, ExperimentResult
from evoforge.evolution.metrics import PerformanceMonitor
from evoforge.model_router.router import ModelRouter, LLMResponse
from evoforge.agents.registry import ToolRegistry
from evoforge.memory.database import Database

def test_evolution_agent():
    router = MagicMock(spec=ModelRouter)
    tools = ToolRegistry()
    
    agent = EvolutionAgent(router, tools)
    assert agent.name == "EvolutionAgent"

def test_experiment_framework():
    framework = ExperimentFramework()
    
    def variant_a(data): return data + 1
    def variant_b(data): return data + 2
    def evaluator(result): return float(result) # Higher is better
    
    result = framework.run_ab_test("test-exp-1", 5, variant_a, variant_b, evaluator)
    
    assert result.experiment_id == "test-exp-1"
    assert result.variant == "B" # 5+2 = 7 > 6
    assert result.success is True
    assert result.score == 7.0

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
