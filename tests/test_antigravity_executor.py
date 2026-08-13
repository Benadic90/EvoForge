
from evoforge.agents.contracts import AgentContext
from evoforge.memory.state import WorkflowStage
from evoforge.model_router.antigravity_runtime import AntigravityRuntimeDetector
from evoforge.model_router.executors import AntigravityExecutor


def test_antigravity_executor_unavailable():
    """Verify the executor handles an unavailable runtime by returning a structured failure."""
    executor = AntigravityExecutor(enabled=True)
    # The detector should say it's unavailable locally
    assert not executor.health_check()
    assert AntigravityRuntimeDetector.health_check() is False

    ctx = AgentContext(
        run_id="run-1",
        workflow_id="wf-1",
        task_id="task-1",
        task_description="Test task",
        current_stage=WorkflowStage.IMPLEMENT
    )

    res = executor.execute(ctx)
    
    # It must not fake success
    assert not res.success
    assert "antigravity" in res.summary.lower()
    assert res.metrics["failure_class"] == "provider_unavailable"
    assert res.metrics["retryable"] is False
    assert res.metrics["provider"] == "antigravity"


def test_antigravity_cancel_unavailable(capsys):
    """Verify cancellation gracefully logs and returns when unavailable."""
    executor = AntigravityExecutor(enabled=True)
    executor.cancel("task-1")
    captured = capsys.readouterr()
    assert "antigravity_cancel_unavailable" in captured.out or "antigravity_cancel_unavailable" in captured.err


def test_antigravity_status_unavailable():
    """Verify status is UNAVAILABLE when runtime is absent."""
    executor = AntigravityExecutor(enabled=True)
    assert executor.get_status("task-1") == "UNAVAILABLE"

