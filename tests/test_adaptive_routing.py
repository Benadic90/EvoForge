from datetime import UTC, datetime, timedelta

from evoforge.agents.capabilities import AgentCapability
from evoforge.agents.contracts import AgentExecutor, AgentResult
from evoforge.memory.database import Database
from evoforge.memory.manager import MemoryManager
from evoforge.memory.obsidian import ObsidianManager
from evoforge.model_router.executors import ExecutorRegistry
from evoforge.model_router.requirements import TaskClassification, TaskRequirements
from evoforge.model_router.routing import ExecutorRouter


class StubExecutor(AgentExecutor):
    def __init__(self, name: str):
        self.name = name

    def execute(self, context) -> AgentResult:
        return AgentResult(success=True, summary=f"{self.name} executed")

    def health_check(self) -> bool:
        return True


def test_recency_weighting_favors_recent_success(tmp_path):
    """Verifies that an executor with recent successes outscores one with only old successes."""
    db_path = str(tmp_path / "recency_test.db")
    db = Database(db_path)
    obsidian = ObsidianManager(str(tmp_path / "vault"))
    memory = MemoryManager(db, obsidian)

    now = datetime.now(UTC)
    old_time = (now - timedelta(days=30)).isoformat()
    recent_time = (now - timedelta(hours=1)).isoformat()

    # Executor A: 10 old successes (30 days ago) followed by 5 recent failures
    for i in range(10):
        db.record_execution_telemetry(
            task_id=f"a_old_{i}",
            workflow_id="wf",
            executor_id="executor_a",
            success=True,
            started_at=old_time,
            completed_at=old_time,
            quality_score=1.0,
        )
    for i in range(5):
        db.record_execution_telemetry(
            task_id=f"a_rec_{i}",
            workflow_id="wf",
            executor_id="executor_a",
            success=False,
            started_at=recent_time,
            completed_at=recent_time,
            quality_score=0.0,
        )

    # Executor B: 5 old failures followed by 10 recent successes
    for i in range(5):
        db.record_execution_telemetry(
            task_id=f"b_old_{i}",
            workflow_id="wf",
            executor_id="executor_b",
            success=False,
            started_at=old_time,
            completed_at=old_time,
            quality_score=0.0,
        )
    for i in range(10):
        db.record_execution_telemetry(
            task_id=f"b_rec_{i}",
            workflow_id="wf",
            executor_id="executor_b",
            success=True,
            started_at=recent_time,
            completed_at=recent_time,
            quality_score=1.0,
        )

    registry = ExecutorRegistry()
    registry.register("executor_a", StubExecutor("A"), [AgentCapability.CODING])
    registry.register("executor_b", StubExecutor("B"), [AgentCapability.CODING])
    registry.set_health("executor_a", True)
    registry.set_health("executor_b", True)

    router = ExecutorRouter(registry, memory_manager=memory)
    req = TaskRequirements(
        task_id="recency_task",
        task_type=TaskClassification.CODING,
        required_capabilities=[AgentCapability.CODING],
    )

    chain, explanation = router.get_candidate_chain(req)

    # Executor B should be selected due to high recent success rate
    assert chain[0][0] == "executor_b"
    assert explanation.candidates[0].score > explanation.candidates[1].score


def test_task_specific_slicing(tmp_path):
    """Verifies that an executor specialized in documentation is preferred for doc tasks over general coders."""
    db_path = str(tmp_path / "task_slicing_test.db")
    db = Database(db_path)
    obsidian = ObsidianManager(str(tmp_path / "vault"))
    memory = MemoryManager(db, obsidian)

    # FastDoc executor: 10 doc successes, 0 coding runs
    for i in range(10):
        db.record_execution_telemetry(
            task_id=f"doc_{i}",
            workflow_id="wf",
            executor_id="doc_specialist",
            task_type="documentation",
            success=True,
            quality_score=0.95,
        )

    # GeneralCoder: 10 coding successes, 3 doc failures
    for i in range(10):
        db.record_execution_telemetry(
            task_id=f"code_{i}",
            workflow_id="wf",
            executor_id="general_coder",
            task_type="coding",
            success=True,
            quality_score=0.95,
        )
    for i in range(3):
        db.record_execution_telemetry(
            task_id=f"code_doc_{i}",
            workflow_id="wf",
            executor_id="general_coder",
            task_type="documentation",
            success=False,
            quality_score=0.2,
        )

    registry = ExecutorRegistry()
    registry.register("doc_specialist", StubExecutor("Doc"), [AgentCapability.CODING])
    registry.register("general_coder", StubExecutor("Coder"), [AgentCapability.CODING])
    registry.set_health("doc_specialist", True)
    registry.set_health("general_coder", True)

    router = ExecutorRouter(registry, memory_manager=memory)

    doc_req = TaskRequirements(
        task_id="doc_task_01",
        task_type="documentation",
        required_capabilities=[AgentCapability.CODING],
    )

    chain, explanation = router.get_candidate_chain(doc_req)
    assert chain[0][0] == "doc_specialist"
    assert explanation.selected_executor_id == "doc_specialist"
