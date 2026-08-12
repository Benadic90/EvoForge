from fastapi.testclient import TestClient

from evoforge.api.server import app, db
from evoforge.memory.events import emitter


def test_api_telemetry_endpoints(tmp_path):
    """Verifies that /api/telemetry/executions and /api/telemetry/statistics return real database records."""
    # Seed execution telemetry
    db.record_execution_telemetry(
        task_id="task_telem_01",
        workflow_id="wf_telem",
        executor_id="local",
        task_type="coding",
        success=True,
        duration_ms=450.0,
        cost_usd=0.0,
        quality_score=0.92,
        tests_passed=True,
    )

    client = TestClient(app)
    resp = client.get("/api/telemetry/executions?limit=10")
    assert resp.status_code == 200
    executions = resp.json()
    assert isinstance(executions, list)
    assert any(e["task_id"] == "task_telem_01" for e in executions)

    stats_resp = client.get("/api/telemetry/statistics")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "total_executions" in stats
    assert "overall_success_rate" in stats
    assert "by_executor" in stats
    assert "by_task_type" in stats


def test_api_events_recent():
    """Verifies that /api/events/recent queries SQLite EventStore."""
    emitter.emit("test.event.fired", source="unit_test", status="ok")

    client = TestClient(app)
    resp = client.get("/api/events/recent?limit=10")
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)
    assert len(events) > 0
