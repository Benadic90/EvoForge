import pytest
from evoforge.model_router.executors import ExecutorRegistry, LocalModelExecutor, GeminiExecutor, AntigravityExecutor
from evoforge.agents.capabilities import AgentCapability
from evoforge.agents.contracts import AgentContext
from evoforge.memory.state import WorkflowStage

def test_executor_registry_operations():
    registry = ExecutorRegistry()
    registry.register("local", LocalModelExecutor(), [AgentCapability.CODING])
    
    assert registry.is_healthy("local")
    assert registry.is_enabled("local")
    assert AgentCapability.CODING in registry.get_capabilities("local")
    
    registry.set_health("local", False)
    assert not registry.is_healthy("local")
    
def test_antigravity_executor_boundary():
    executor = AntigravityExecutor()
    context = AgentContext(
        run_id="r1",
        workflow_id="w1",
        task_id="t1",
        task_description="test",
        current_stage=WorkflowStage.IMPLEMENT
    )
    
    result = executor.execute(context)
    assert result.success is True
    assert result.agent_id == "antigravity_executor"
    assert "latency_ms" in result.metrics
