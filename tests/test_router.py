import pytest

from evoforge.agents.capabilities import AgentCapability
from evoforge.model_router.executors import (
    AntigravityExecutor,
    ExecutorRegistry,
    GeminiExecutor,
    LocalModelExecutor,
)
from evoforge.model_router.requirements import TaskRequirements
from evoforge.model_router.routing import ExecutorRouter


@pytest.fixture
def mock_registry():
    registry = ExecutorRegistry()
    registry.register("local", LocalModelExecutor(), [AgentCapability.CODING])
    registry.register("gemini", GeminiExecutor(), [AgentCapability.CODING, AgentCapability.REASONING])
    registry.register("antigravity", AntigravityExecutor(), [AgentCapability.CODING, AgentCapability.REASONING, AgentCapability.BROWSER])
    registry.set_health("local", True)
    registry.set_health("gemini", True)
    registry.set_health("antigravity", True)
    return registry


def test_router_selects_most_capable(mock_registry):
    router = ExecutorRouter(mock_registry)
    req = TaskRequirements(
        task_id="t1",
        required_capabilities=[AgentCapability.BROWSER, AgentCapability.CODING]
    )
    
    _executor, explanation = router.select_executor(req)
    assert explanation.selected_executor_id == "antigravity"
    assert "local" in explanation.rejected
    assert "gemini" in explanation.rejected

def test_router_circuit_breaker(mock_registry):
    router = ExecutorRouter(mock_registry)
    
    # Simulate circuit breaker tripping for antigravity
    for _ in range(5):
        router.circuit_breaker.record_failure("antigravity")
        
    req = TaskRequirements(
        task_id="t2",
        required_capabilities=[AgentCapability.CODING]
    )
    
    # Should pick gemini because antigravity is circuit broken, local has lower score?
    # Actually, local and gemini both have CODING. Gemini has REASONING (extra), so local might have a higher capability match score (fewer extra).
    _executor, explanation = router.select_executor(req)
    assert explanation.selected_executor_id in ["local", "gemini"]
    assert "antigravity" in explanation.rejected
    assert "Circuit breaker is open" in explanation.rejected["antigravity"][0]

def test_router_privacy_policy(mock_registry):
    router = ExecutorRouter(mock_registry)
    req = TaskRequirements(
        task_id="t3",
        required_capabilities=[AgentCapability.CODING],
        privacy_requirement=1.0 # Requires local
    )
    
    _executor, explanation = router.select_executor(req)
    assert explanation.selected_executor_id == "local"
    assert "gemini" in explanation.rejected
    
def test_router_no_available_executors(mock_registry):
    router = ExecutorRouter(mock_registry)
    req = TaskRequirements(
        task_id="t4",
        required_capabilities=[AgentCapability.TERMINAL] # No one has this in the mock
    )
    
    with pytest.raises(RuntimeError) as excinfo:
        router.select_executor(req)
    
    assert "No available executors" in str(excinfo.value)
