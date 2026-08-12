from evoforge.agents.capabilities import AgentCapability
from evoforge.agents.contracts import (
    AgentContext,
    AgentContract,
    AgentExecutor,
    AgentResult,
)
from evoforge.agents.registry import AgentRegistry
from evoforge.memory.database import Database
from evoforge.memory.events import emitter
from evoforge.memory.manager import MemoryManager
from evoforge.memory.obsidian import ObsidianManager
from evoforge.memory.state import WorkflowStage
from evoforge.model_router.executors import ExecutorRegistry
from evoforge.model_router.requirements import TaskClassification, TaskRequirements
from evoforge.model_router.routing import ExecutorRouter
from evoforge.orchestrator.engine import OrchestratorEngine
from evoforge.orchestrator.workflows import TaskPriority, WorkflowDefinition, WorkflowTask


class ReliableExecutor(AgentExecutor):
    def execute(self, context: AgentContext) -> AgentResult:
        return AgentResult(
            success=True,
            agent_id="reliable_executor",
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            summary="Reliable execution completed.",
            metrics={"latency_ms": 100, "cost": 0.001, "provider": "gemini"},
        )


class FlakyExecutor(AgentExecutor):
    def __init__(self, should_succeed: bool = False):
        self.should_succeed = should_succeed

    def execute(self, context: AgentContext) -> AgentResult:
        if self.should_succeed:
            return AgentResult(
                success=True,
                agent_id="flaky_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary="Flaky execution succeeded.",
                metrics={"latency_ms": 200, "cost": 0.0, "provider": "local"},
            )
        return AgentResult(
            success=False,
            agent_id="flaky_executor",
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            summary="Flaky execution failed due to timeout.",
            errors=["Timeout contacting backend"],
            metrics={"latency_ms": 5000, "cost": 0.0, "failure_class": "timeout", "provider": "local"},
        )


def test_router_empirical_scoring_prefers_reliable_executor(tmp_path):
    db_path = str(tmp_path / "test_routing_db.db")
    db = Database(db_path)
    obsidian = ObsidianManager(str(tmp_path / "vault"))
    memory = MemoryManager(db, obsidian)

    # Seed empirical history:
    # 'gemini': 10 runs, 10 successes (100%)
    for i in range(10):
        db.record_execution_telemetry(
            task_id=f"t_gem_{i}",
            workflow_id="wf",
            executor_id="gemini",
            success=True,
            duration_ms=400.0,
            cost_usd=0.001,
            quality_score=0.98,
        )

    # 'local': 10 runs, 4 successes (40%)
    for i in range(10):
        db.record_execution_telemetry(
            task_id=f"t_loc_{i}",
            workflow_id="wf",
            executor_id="local",
            success=(i < 4),
            duration_ms=2500.0,
            cost_usd=0.0,
            quality_score=0.4,
        )

    registry = ExecutorRegistry()
    registry.register("gemini", ReliableExecutor(), [AgentCapability.CODING])
    registry.register("local", FlakyExecutor(should_succeed=True), [AgentCapability.CODING])

    # Mark healthy for scoring test
    registry.set_health("gemini", True)
    registry.set_health("local", True)

    router = ExecutorRouter(registry, memory_manager=memory)

    req = TaskRequirements(
        task_id="task_test_score",
        task_type=TaskClassification.CODING,
        required_capabilities=[AgentCapability.CODING],
    )

    chain, explanation = router.get_candidate_chain(req)

    # Gemini should be ranked higher due to 100% success rate vs 40%
    assert chain[0][0] == "gemini"
    assert chain[1][0] == "local"
    assert explanation.candidates[0].score > explanation.candidates[1].score


def test_router_cold_start_smoothing_prevents_untested_domination(tmp_path):
    db_path = str(tmp_path / "test_cold_start_db.db")
    db = Database(db_path)
    obsidian = ObsidianManager(str(tmp_path / "vault"))
    memory = MemoryManager(db, obsidian)

    # Veteran: 500 tasks, 455 successes (91% raw success)
    for i in range(500):
        db.record_execution_telemetry(
            task_id=f"t_vet_{i}",
            workflow_id="wf",
            executor_id="veteran",
            success=(i < 455),
            duration_ms=500.0,
            cost_usd=0.001,
            quality_score=0.90,
        )

    # Lucky Rookie: 1 task, 1 success (100% raw success)
    db.record_execution_telemetry(
        task_id="t_rookie_0",
        workflow_id="wf",
        executor_id="rookie",
        success=True,
        duration_ms=500.0,
        cost_usd=0.001,
        quality_score=0.90,
    )

    registry = ExecutorRegistry()
    registry.register("veteran", ReliableExecutor(), [AgentCapability.CODING])
    registry.register("rookie", ReliableExecutor(), [AgentCapability.CODING])
    registry.set_health("veteran", True)
    registry.set_health("rookie", True)

    router = ExecutorRouter(registry, memory_manager=memory)

    req = TaskRequirements(
        task_id="task_cold_start",
        task_type=TaskClassification.CODING,
        required_capabilities=[AgentCapability.CODING],
    )

    chain, explanation = router.get_candidate_chain(req)

    # Veteran (500 runs @ 91%) must outrank Rookie (1 run @ 100%) due to Bayesian smoothing
    assert chain[0][0] == "veteran"
    assert chain[1][0] == "rookie"
    assert explanation.candidates[0].score > explanation.candidates[1].score



def test_orchestrator_fallback_execution(tmp_path):
    db_path = str(tmp_path / "test_fallback_db.db")
    db = Database(db_path)
    obsidian = ObsidianManager(str(tmp_path / "vault"))
    memory = MemoryManager(db, obsidian)
    memory.init_memory_systems()

    # Create agent registry with developer agent
    agent_reg = AgentRegistry()
    dev_contract = AgentContract(
        agent_id="developer",
        name="DeveloperAgent",
        display_name="Developer Agent",
        role="Implementation",
        description="Writes code",
        version="1.0",
        capabilities=[AgentCapability.CODING],
    )
    agent_reg.register(dev_contract, FlakyExecutor(should_succeed=False))

    # Executor registry with Primary (Flaky/Failing) and Fallback (Reliable)
    exec_reg = ExecutorRegistry()
    primary_failing = FlakyExecutor(should_succeed=False)
    fallback_reliable = ReliableExecutor()

    # Force primary to rank first by inserting higher prior telemetry
    db.record_execution_telemetry(
        task_id="seed_p",
        workflow_id="wf",
        executor_id="primary",
        success=True,
        quality_score=1.0,
    )

    exec_reg.register("primary", primary_failing, [AgentCapability.CODING])
    exec_reg.register("secondary", fallback_reliable, [AgentCapability.CODING])
    exec_reg.set_health("primary", True)
    exec_reg.set_health("secondary", True)

    router = ExecutorRouter(exec_reg, memory_manager=memory)
    engine = OrchestratorEngine(memory, agent_reg, executor_router=router)

    # Register workflow and task in DB
    db.execute(
        "INSERT INTO workflows (id, project, workflow_type, status) VALUES (?, ?, ?, ?)",
        ("wf_fb", "repo_fb", "feature", "pending"),
    )
    db.execute(
        "INSERT INTO tasks (id, project, task_type, title, description, assigned_workflow) VALUES (?, ?, ?, ?, ?, ?)",
        ("t_fb", "repo_fb", "developer", "Task Fallback", "Implement feature", "wf_fb"),
    )

    wf_def = WorkflowDefinition(
        id="wf_fb",
        repo_name="repo_fb",
        tasks=[
            WorkflowTask(
                id="t_fb",
                name="Task Fallback",
                description="Implement feature",
                agent_type="developer",
                priority=TaskPriority.MEDIUM,
            )
        ],

    )

    fallback_events = []
    emitter.on("router.fallback", lambda event: fallback_events.append(event))

    # Execute workflow - should try primary, fail, fallback to secondary, and complete!
    engine.execute_workflow(wf_def)

    assert wf_def.state == WorkflowStage.COMPLETE
    assert len(fallback_events) >= 1
    assert fallback_events[0].payload["from_executor"] == "primary"
    assert fallback_events[0].payload["to_executor"] == "secondary"


    # Check that telemetry recorded both attempts
    stats = memory.get_executor_stats()
    assert "primary" in stats
    assert stats["primary"]["total_runs"] == 2 # 1 seeded success + 1 runtime failure
    assert stats["primary"]["successful_runs"] == 1
    assert "secondary" in stats
    assert stats["secondary"]["total_runs"] == 1
    assert stats["secondary"]["successful_runs"] == 1

