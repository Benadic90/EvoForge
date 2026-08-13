
import pytest

from evoforge.memory.database import Database
from evoforge.runtime.scheduler import SchedulerEngine


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    database = Database(str(db_path))
    return database

def test_scheduler_state(db):
    scheduler = SchedulerEngine(db, None, None)
    status = scheduler.get_status()
    assert status.get("status") == "STOPPED"
    
    scheduler.pause()
    assert scheduler.is_paused()
    
    scheduler.resume()
    assert not scheduler.is_paused()
    
    status = scheduler.get_status()
    assert status.get("status") == "RUNNING"
