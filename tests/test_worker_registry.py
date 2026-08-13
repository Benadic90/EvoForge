
import pytest

from evoforge.memory.database import Database
from evoforge.runtime.worker import WorkerProfile, WorkerRegistry, WorkerStatus, WorkerType


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    database = Database(str(db_path))
    return database

def test_worker_registration(db):
    registry = WorkerRegistry(db)
    profile = WorkerProfile(
        worker_id="test_cloud_worker",
        worker_type=WorkerType.CLOUD,
        capabilities=["coding"]
    )
    
    registry.register(profile)
    fetched = registry.get("test_cloud_worker")
    
    assert fetched is not None
    assert fetched.worker_id == "test_cloud_worker"
    assert fetched.worker_type == WorkerType.CLOUD
    assert "coding" in fetched.capabilities

def test_worker_heartbeat_and_staleness(db):
    registry = WorkerRegistry(db, heartbeat_timeout_seconds=1)
    profile = WorkerProfile(
        worker_id="test_staleness",
        worker_type=WorkerType.LAPTOP,
        status=WorkerStatus.IDLE
    )
    registry.register(profile)
    
    active = registry.list_active()
    assert len(active) == 1
    
    # Force timeout
    import time
    time.sleep(1.1)
    
    active_after = registry.list_active()
    assert len(active_after) == 0
    
    fetched = registry.get("test_staleness")
    assert fetched.status == WorkerStatus.OFFLINE
    
    # Recover heartbeat
    registry.heartbeat("test_staleness", status=WorkerStatus.IDLE)
    active_recovered = registry.list_active()
    assert len(active_recovered) == 1
