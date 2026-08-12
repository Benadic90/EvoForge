from fastapi.testclient import TestClient

from evoforge.api.server import app, db


def test_api_routing_recent_and_detail(tmp_path):
    """Verifies that /api/routing/recent and /api/routing/{task_id} return persisted decisions."""
    # Seed a decision
    db.record_routing_decision(
        task_id="task_api_test_01",
        workflow_id="wf_api_test",
        selected_executor_id="gemini",
        selected_score=0.91,
        decision_reason="Capability match 1.0; Empirical success 95%",
        agent_id="developer",
        task_type="coding",
    )

    client = TestClient(app)
    resp = client.get("/api/routing/recent?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0

    found = any(d["task_id"] == "task_api_test_01" for d in data)
    assert found

    # Query single decision
    single_resp = client.get("/api/routing/task_api_test_01")
    assert single_resp.status_code == 200
    single_data = single_resp.json()
    assert single_data["task_id"] == "task_api_test_01"
    assert single_data["selected_executor_id"] == "gemini"
    assert single_data["selected_score"] == 0.91


def test_api_routing_statistics():
    """Verifies that /api/routing/statistics aggregates selection counts and scores."""
    client = TestClient(app)
    resp = client.get("/api/routing/statistics")
    assert resp.status_code == 200
    data = resp.json()
    assert "policy_version" in data
    assert "total_decisions" in data
    assert "by_executor" in data
