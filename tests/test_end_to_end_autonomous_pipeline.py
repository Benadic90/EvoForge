from unittest.mock import MagicMock, patch

import pytest

from evoforge.agents.contracts import AgentExecutor, AgentResult
from evoforge.memory.database import Database
from evoforge.model_router.executors import ExecutorRegistry
from evoforge.portfolio.daily_planner import DailyPlanner
from evoforge.portfolio.models import ProjectProfile
from evoforge.portfolio.priority_engine import PortfolioPriorityEngine
from evoforge.portfolio.registry import ProjectRegistry
from evoforge.portfolio.scanner import ProjectScanner
from evoforge.runtime.scheduler import SchedulerEngine


class MockPipelineExecutor(AgentExecutor):
    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed

    def execute(self, context) -> AgentResult:
        if self.should_succeed:
            return AgentResult(
                success=True,
                agent_id="mock_agent",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary="Mock pipeline task implementation complete with optimizations.",
                metrics={"latency_ms": 50.0, "cost": 0.001, "provider": "mock", "model": "mock-v1"}
            )
        return AgentResult(
            success=False, 
            agent_id="mock_agent",
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            summary="Mock failure", 
            metrics={"failure_class": "MODEL_ERROR"}
        )


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_pipeline.db"
    db = Database(str(db_file))
    return db


@pytest.fixture
def mock_github_client():
    client = MagicMock()
    client.get_open_issues.return_value = [
        {
            "id": 101,
            "title": "Fix memory leak in buffer pool",
            "body": "Detailed buffer pool memory leak report",
            "html_url": "https://github.com/test/repo/issues/101",
            "labels": ["bug", "priority-high"],
            "state": "open",
        }
    ]
    client.get_open_prs.return_value = []
    client.get_recent_commits.return_value = [{"sha": "abc1234", "message": "Initial commit"}]
    client.get_ci_state.return_value = "SUCCESS"
    return client


def test_end_to_end_autonomous_pipeline(temp_db, mock_github_client, tmp_path):
    # 1. Register a managed project
    registry = ProjectRegistry(temp_db)
    proj = ProjectProfile(
        project_id="proj_pipeline_test",
        owner="testorg",
        name="PipelineProject",
        repository_full_name="testorg/PipelineProject",
        repository_url="https://github.com/testorg/PipelineProject",
        default_branch="main",
        status="MANAGED",
        description="Autonomous test project",
    )
    registry.register(proj)

    # 2. Scanner: Force rescan bypasses 4h cache and gathers items + autonomous upgrades
    scanner = ProjectScanner(temp_db, mock_github_client, registry)
    report, raw_items = scanner.scan_project("proj_pipeline_test", force_rescan=True)
    assert report is not None
    assert raw_items is not None
    assert len(raw_items) >= 4  # 1 issue + 4 autonomous upgrades

    # 3. Priority Engine: Generate backlog & rank
    priority_engine = PortfolioPriorityEngine(temp_db, registry)
    tasks = priority_engine.generate_backlog("proj_pipeline_test", raw_items)
    assert len(tasks) >= 4
    
    # Verify deduplication on second run
    duplicate_tasks = priority_engine.generate_backlog("proj_pipeline_test", raw_items)
    assert len(duplicate_tasks) == 0  # No duplicate tasks created!

    # 4. Rank projects & tasks
    proj_rankings = priority_engine.rank_projects()
    assert len(proj_rankings) == 1
    assert proj_rankings[0].item_id == "proj_pipeline_test"

    task_rankings = priority_engine.rank_tasks()
    assert len(task_rankings) >= 4

    # 5. Daily Planner: Generates bounded daily plan
    planner = DailyPlanner(temp_db, registry, max_tasks=3)
    plan = planner.generate_plan()
    assert plan.plan_id.startswith("plan_")
    assert len(plan.selected_tasks) > 0
    assert len(plan.reasons) > 0

    # 6. Scheduler Engine: Enqueue tasks to workflows table
    scheduler = SchedulerEngine(temp_db, mock_github_client)
    scheduler.enqueue_portfolio_tasks()

    pending_workflows = temp_db.fetchall("SELECT * FROM workflows WHERE status = 'pending'")
    assert len(pending_workflows) > 0

    # 7. Worker Execution: Embedded worker consumes pending workflows
    from evoforge.agents.capabilities import AgentCapability
    def mock_registry_factory(cfg=None, db=None):
        reg = ExecutorRegistry()
        mock_exec = MockPipelineExecutor()
        reg.register("gemini", mock_exec, list(AgentCapability))
        reg.register("local", mock_exec, list(AgentCapability))
        reg.set_health("gemini", True)
        reg.set_health("local", True)
        return reg

    with patch("evoforge.model_router.executors.create_default_executor_registry", side_effect=mock_registry_factory), \
         patch("evoforge.github_integration.git_workflow.AutonomousGitWorkflow.publish_task_solution") as mock_publish:
        mock_publish.return_value = "https://github.com/testorg/PipelineProject/pull/99"
        
        scheduler.execute_pending_workflows()

        # All pending workflows should now be completed
        completed_workflows = temp_db.fetchall("SELECT * FROM workflows WHERE status = 'completed'")
        assert len(completed_workflows) == len(pending_workflows)
        
        # Portfolio tasks marked completed
        completed_tasks = temp_db.fetchall("SELECT * FROM portfolio_tasks WHERE status = 'COMPLETED'")
        assert len(completed_tasks) > 0
        
        # Git PR publisher was invoked
        assert mock_publish.call_count == len(pending_workflows)


def test_no_changes_does_not_create_fake_pr(temp_db):
    from evoforge.github_integration.git_workflow import AutonomousGitWorkflow
    git_flow = AutonomousGitWorkflow(db=temp_db)
    
    # When solution says NO_CHANGES_REQUIRED, it immediately returns NO_CHANGES_REQUIRED without calling GitHub
    res = git_flow.publish_task_solution(
        repo_full_name="testorg/PipelineProject",
        task_id="task_123",
        task_title="No Op Task",
        task_description="Nothing to do",
        solution_summary="NO_CHANGES_REQUIRED"
    )
    assert res == "NO_CHANGES_REQUIRED"


def test_pipeline_status_telemetry(temp_db):
    from evoforge.api.server import get_pipeline_status
    # Call get_pipeline_status
    status_data = get_pipeline_status()
    assert "managed_projects" in status_data
    assert "total_backlog_tasks" in status_data
    assert "pending_workflows" in status_data
    assert "workers_online" in status_data
