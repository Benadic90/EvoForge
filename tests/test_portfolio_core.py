import pytest
import sqlite3
import tempfile
from datetime import datetime

from evoforge.memory.database import Database
from evoforge.portfolio.models import ProjectProfile, PortfolioTask
from evoforge.portfolio.registry import ProjectRegistry
from evoforge.portfolio.priority_engine import PortfolioPriorityEngine
from evoforge.portfolio.daily_planner import DailyPlanner

@pytest.fixture
def db():
    # Use in-memory or temp file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        pass
    db_obj = Database(tmp.name)
    yield db_obj
    import os
    os.remove(tmp.name)

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
    assert fetched.status == "ACTIVE"
    
    registry.disable("proj_1")
    assert registry.get("proj_1").status == "DISABLED"
    
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
        importance=0.9, health="CRITICAL", ci_health=0.0
    )
    pb = ProjectProfile(
        project_id="proj_b", repository_full_name="b/b", repository_url="", owner="b", name="B", default_branch="main",
        importance=0.6, health="HEALTHY", ci_health=1.0
    )
    pc = ProjectProfile(
        project_id="proj_c", repository_full_name="c/c", repository_url="", owner="c", name="C", default_branch="main",
        importance=0.2, health="UNKNOWN", ci_health=None
    )
    registry.register(pa)
    registry.register(pb)
    registry.register(pc)
    
    engine = PortfolioPriorityEngine(db, registry)
    rankings = engine.rank_projects()
    
    assert len(rankings) == 3
    # A should be rank 1
    assert rankings[0].item_id == "proj_a"
    assert rankings[0].rank == 1
    # B should be rank 2
    assert rankings[1].item_id == "proj_b"
    assert rankings[1].rank == 2
    # C should be rank 3
    assert rankings[2].item_id == "proj_c"
    assert rankings[2].rank == 3

def test_daily_plan_budget_and_dependencies(db, registry):
    # Register project
    pa = ProjectProfile(
        project_id="proj_x", repository_full_name="x/x", repository_url="", owner="x", name="X", default_branch="main",
        importance=1.0, health="CRITICAL"
    )
    registry.register(pa)
    
    engine = PortfolioPriorityEngine(db, registry)
    
    # Task 1: High priority
    t1 = PortfolioTask(
        task_id="t1", project_id="proj_x", title="Task 1", description="", source="test", source_id="1",
        priority=0.9, status="NOT_STARTED", created_at=datetime.utcnow(), updated_at=datetime.utcnow()
    )
    # Task 2: High priority, depends on t1
    t2 = PortfolioTask(
        task_id="t2", project_id="proj_x", title="Task 2", description="", source="test", source_id="2",
        priority=0.9, dependencies=["t1"], status="NOT_STARTED", created_at=datetime.utcnow(), updated_at=datetime.utcnow()
    )
    # Task 3: Low priority
    t3 = PortfolioTask(
        task_id="t3", project_id="proj_x", title="Task 3", description="", source="test", source_id="3",
        priority=0.1, status="NOT_STARTED", created_at=datetime.utcnow(), updated_at=datetime.utcnow()
    )
    
    engine._save_task(t1)
    engine._save_task(t2)
    engine._save_task(t3)
    
    engine.rank_projects()
    engine.rank_tasks()
    
    # Set budget to max 1 task
    planner = DailyPlanner(db, registry, max_tasks=1)
    plan = planner.generate_plan()
    
    # Should only select t1 because of budget, and t2 is skipped anyway because t1 is unmet dependency
    assert len(plan.selected_tasks) == 1
    assert plan.selected_tasks[0] == "t1"
    
    # Now set t1 as complete
    t1.status = "COMPLETE"
    engine._save_task(t1)
    
    # Re-plan with max 2 tasks
    planner2 = DailyPlanner(db, registry, max_tasks=2)
    plan2 = planner2.generate_plan()
    
    # Now t2 should be selected because t1 is complete
    assert "t2" in plan2.selected_tasks
