from fastapi.testclient import TestClient

from evoforge.api.server import app

AUTH_HEADERS = {"Authorization": "Bearer test-worker-token"}


def test_api_status_endpoint(monkeypatch):
    """Verifies that /api/status returns typed real status without static hardcoded mock numbers."""
    monkeypatch.setenv("WORKER_SECRET_TOKEN", "test-worker-token")
    client = TestClient(app)
    resp = client.get("/api/status", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "success"
    assert "timestamp" in data
    assert "system_state" in data
    assert "active_workflows" in data
    assert "failed_workflows" in data
    assert "workflows" in data
    assert "queued_tasks" in data
    assert "workers" in data
    assert "agents" in data
    assert "scheduler" in data
    assert "compute_mode" in data
    assert "healthy_executors" in data
    assert "unhealthy_executors" in data
    assert "version" in data
    assert isinstance(data["active_workflows"], int)
    assert isinstance(data["healthy_executors"], int)


def test_api_status_requires_valid_worker_token(monkeypatch):
    monkeypatch.setenv("WORKER_SECRET_TOKEN", "test-worker-token")
    client = TestClient(app)

    missing = client.get("/api/status")
    wrong = client.get("/api/status", headers={"Authorization": "Bearer wrong-token"})

    assert missing.status_code == 401
    assert wrong.status_code == 401


def test_default_dev_token_rejected_without_explicit_local_opt_in(monkeypatch):
    monkeypatch.setenv("WORKER_SECRET_TOKEN", "default-dev-token")
    monkeypatch.delenv("EVOFORGE_ALLOW_DEFAULT_DEV_TOKEN", raising=False)
    client = TestClient(app)

    resp = client.get("/api/status", headers={"Authorization": "Bearer default-dev-token"})

    assert resp.status_code == 503


def test_compute_policy_endpoint_normalizes_mode_flags(monkeypatch):
    monkeypatch.setenv("WORKER_SECRET_TOKEN", "test-worker-token")
    client = TestClient(app)

    resp = client.put("/api/settings/compute", json={"mode": "CLOUD"}, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "CLOUD"
    assert data["allow_local"] is False
    assert data["allow_cloud"] is True

    restore = client.put("/api/settings/compute", json={"mode": "HYBRID"}, headers=AUTH_HEADERS)
    assert restore.status_code == 200


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
