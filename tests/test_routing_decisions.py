from evoforge.agents.capabilities import AgentCapability
from evoforge.agents.contracts import AgentExecutor, AgentResult
from evoforge.memory.database import Database
from evoforge.memory.manager import MemoryManager
from evoforge.memory.obsidian import ObsidianManager
from evoforge.model_router.executors import ExecutorRegistry
from evoforge.model_router.requirements import TaskClassification, TaskRequirements
from evoforge.model_router.routing import ExecutorRouter


class SimpleExecutor(AgentExecutor):
    def execute(self, context) -> AgentResult:
        return AgentResult(success=True, summary="Done")

    def health_check(self) -> bool:
        return True


def test_routing_decision_persisted_to_database(tmp_path):
    """Verifies that every routing decision is saved with full rankings and explanation in SQLite."""
    db_path = str(tmp_path / "routing_decisions_test.db")
    db = Database(db_path)
    obsidian = ObsidianManager(str(tmp_path / "vault"))
    memory = MemoryManager(db, obsidian)

    registry = ExecutorRegistry()
    registry.register("exec_1", SimpleExecutor(), [AgentCapability.CODING])
    registry.register("exec_2", SimpleExecutor(), [AgentCapability.CODING])
    registry.set_health("exec_1", True)
    registry.set_health("exec_2", True)

    router = ExecutorRouter(registry, memory_manager=memory)

    req = TaskRequirements(
        task_id="task_audit_99",
        task_type=TaskClassification.CODING,
        required_capabilities=[AgentCapability.CODING],
    )

    chain, explanation = router.get_candidate_chain(req, workflow_id="wf_123", agent_id="developer")

    # Verify decision stored in database
    decision = db.get_routing_decision("task_audit_99")
    assert decision is not None
    assert decision["task_id"] == "task_audit_99"
    assert decision["workflow_id"] == "wf_123"
    assert decision["agent_id"] == "developer"
    assert decision["selected_executor_id"] in ["exec_1", "exec_2"]
    assert decision["routing_policy_version"] == "adaptive-v1"
    assert "Capability match" in decision["decision_reason"]
