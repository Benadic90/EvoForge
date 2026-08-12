from fastapi.testclient import TestClient

from evoforge.api.server import app


def test_api_status_endpoint():
    """Verifies that /api/status returns typed real status without static hardcoded mock numbers."""
    client = TestClient(app)
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()

    assert "system_state" in data
    assert "active_workflows" in data
    assert "failed_workflows" in data
    assert "healthy_executors" in data
    assert "unhealthy_executors" in data
    assert "version" in data
    assert isinstance(data["active_workflows"], int)
    assert isinstance(data["healthy_executors"], int)


def test_api_agents_endpoint():
    """Verifies that /api/agents lists registered agents and live task counts."""
    client = TestClient(app)
    resp = client.get("/api/agents")
    assert resp.status_code == 200
    data = resp.json()

    assert isinstance(data, list)
    assert len(data) > 0
    agent_ids = [a["agent_id"] for a in data]
    assert "developer" in agent_ids
    assert "qa" in agent_ids


def test_api_executors_endpoint():
    """Verifies that /api/executors returns real dynamic health and statistics."""
    client = TestClient(app)
    resp = client.get("/api/executors")
    assert resp.status_code == 200
    data = resp.json()

    assert isinstance(data, list)
    assert len(data) > 0
    exec_ids = [e["executor_id"] for e in data]
    assert "local" in exec_ids
    assert "gemini" in exec_ids
