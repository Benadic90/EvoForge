from datetime import UTC, datetime

import pytest

from evoforge.memory.database import Database
from evoforge.portfolio.daily_planner import DailyPlanner
from evoforge.portfolio.models import PortfolioTask, ProjectProfile
from evoforge.portfolio.priority_engine import PortfolioPriorityEngine
from evoforge.portfolio.registry import ProjectRegistry


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    return Database(str(db_path))

@pytest.fixture
def registry(db):
    return ProjectRegistry(db)

def test_registry_crud(registry):
    profile = ProjectProfile(
        project_id="proj_1",
        repository_full_name="test/repo",
        repository_url="https://github.com/test/repo",
        owner="test",
        name="repo",
        default_branch="main"
    )
    registry.register(profile)
    
    fetched = registry.get("proj_1")
    assert fetched is not None
    assert fetched.repository_full_name == "test/repo"
    assert fetched.status == "MANAGED"
    
    registry.disable("proj_1")
    assert registry.get("proj_1").status == "PAUSED"
    
    registry.remove("proj_1")
    assert registry.get("proj_1") is None

def test_seeded_portfolio_ranking(db, registry):
    """
    Project A: high security severity, high importance
    Project B: healthy, medium roadmap value
    Project C: stale, low importance
    Verify that A > B > C.
    """
    pa = ProjectProfile(
        project_id="proj_a", repository_full_name="a/a", repository_url="", owner="a", name="A", default_branch="main",
        importance="HIGH", health="CRITICAL", ci_health=0.0
    )
    pb = ProjectProfile(
        project_id="proj_b", repository_full_name="b/b", repository_url="", owner="b", name="B", default_branch="main",
        importance="MEDIUM", health="HEALTHY", ci_health=1.0
    )
    pc = ProjectProfile(
        project_id="proj_c", repository_full_name="c/c", repository_url="", owner="c", name="C", default_branch="main",
        importance="LOW", health="WARNING", maintenance_health=0.1
    )
    registry.register(pa)
    registry.register(pb)
    registry.register(pc)

    engine = PortfolioPriorityEngine(db, registry)
    ranking = engine.rank_projects()
    
    # Check ordering
    assert ranking[0].item_id == "proj_a"
    assert ranking[2].item_id == "proj_c"

def test_daily_plan_budget_and_dependencies(db, registry):
    # Register project
    pa = ProjectProfile(
        project_id="proj_x", repository_full_name="x/x", repository_url="", owner="x", name="X", default_branch="main",
        importance="HIGH", health="CRITICAL"
    )
    registry.register(pa)
    
    engine = PortfolioPriorityEngine(db, registry)
    
    now = datetime.now(UTC)
    t1 = PortfolioTask(
        task_id="t1", project_id="proj_x", title="Task 1", description="", source="test", source_id="1",
        priority=0.9, status="NOT_STARTED", created_at=now, updated_at=now
    )
    t2 = PortfolioTask(
        task_id="t2", project_id="proj_x", title="Task 2", description="", source="test", source_id="2",
        priority=0.9, dependencies=["t1"], status="NOT_STARTED", created_at=now, updated_at=now
    )
    t3 = PortfolioTask(
        task_id="t3", project_id="proj_x", title="Task 3", description="", source="test", source_id="3",
        priority=0.1, status="NOT_STARTED", created_at=now, updated_at=now
    )
    
    # Save using engine so it's correct
    engine._save_task(t1)
    engine._save_task(t2)
    engine._save_task(t3)
    
    engine.rank_projects()
    engine.rank_tasks()
    
    planner = DailyPlanner(db, registry, max_tasks=1)
    plan = planner.generate_plan()
    
    assert plan is not None
    assert len(plan.execution_order) > 0
    if "t1" in plan.execution_order and "t2" in plan.execution_order:
        assert plan.execution_order.index("t1") < plan.execution_order.index("t2")
    # Should only select t1 because of budget, and t2 is skipped anyway because t1 is unmet dependency
    assert len(plan.selected_tasks) == 1
    assert plan.selected_tasks[0] == "t1"
    
    # Now set t1 as complete
    t1.status = "COMPLETE"
    engine._save_task(t1)
    engine.rank_tasks()

    # Re-plan with max 2 tasks
    planner2 = DailyPlanner(db, registry, max_tasks=2)
    plan2 = planner2.generate_plan()
    
    # Now t2 should be selected because t1 is complete
    assert "t2" in plan2.selected_tasks
