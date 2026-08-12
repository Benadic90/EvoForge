from evoforge.agents.capabilities import AgentCapability
from evoforge.agents.contracts import AgentContext
from evoforge.memory.state import WorkflowStage
from evoforge.model_router.executors import (
    AntigravityExecutor,
    ExecutorRegistry,
    LocalModelExecutor,
)


def test_executor_registry_operations():
    registry = ExecutorRegistry()
    registry.register("local", LocalModelExecutor(), [AgentCapability.CODING])

    assert registry.is_enabled("local")
    assert AgentCapability.CODING in registry.get_capabilities("local")

    registry.set_health("local", True)
    assert registry.is_healthy("local") is True

    registry.set_health("local", False)
    assert registry.is_healthy("local") is False


def test_antigravity_executor_boundary():
    # When disabled / unconfigured
    executor_disabled = AntigravityExecutor(enabled=False)
    context = AgentContext(
        run_id="r1",
        workflow_id="w1",
        task_id="t1",
        task_description="test",
        current_stage=WorkflowStage.IMPLEMENT,
    )

    result_disabled = executor_disabled.execute(context)
    assert result_disabled.success is False
    assert result_disabled.metrics["failure_class"] == "provider_unavailable"

    # When explicitly enabled boundary
    executor_enabled = AntigravityExecutor(enabled=True)
    result_enabled = executor_enabled.execute(context)
    assert result_enabled.success is True
    assert result_enabled.agent_id == "antigravity_executor"
    assert "latency_ms" in result_enabled.metrics
