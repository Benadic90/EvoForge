from evoforge.memory.database import Database
from evoforge.memory.manager import MemoryManager
from evoforge.memory.obsidian import ObsidianManager


def test_telemetry_persistence_and_stats(tmp_path):
    db_path = str(tmp_path / "test_telemetry.db")
    db = Database(db_path)

    # Insert sample telemetry
    db.record_execution_telemetry(
        task_id="t1",
        workflow_id="wf1",
        agent_id="developer",
        executor_id="local",
        provider_id="ollama",
        model_id="qwen2.5-coder",
        duration_ms=1200.0,
        success=True,
        cost_usd=0.0,
        input_tokens=100,
        output_tokens=50,
        quality_score=1.0,
    )
    db.record_execution_telemetry(
        task_id="t2",
        workflow_id="wf1",
        agent_id="developer",
        executor_id="local",
        provider_id="ollama",
        model_id="qwen2.5-coder",
        duration_ms=2000.0,
        success=False,
        failure_class="timeout",
        cost_usd=0.0,
        quality_score=0.0,
    )
    db.record_execution_telemetry(
        task_id="t3",
        workflow_id="wf1",
        agent_id="developer",
        executor_id="gemini",
        provider_id="gemini",
        model_id="gemini-2.5-flash",
        duration_ms=600.0,
        success=True,
        cost_usd=0.002,
        quality_score=0.95,
    )

    stats = db.get_executor_stats()

    assert "local" in stats
    assert stats["local"]["total_runs"] == 2
    assert stats["local"]["successful_runs"] == 1
    assert stats["local"]["success_rate"] == 0.5
    assert stats["local"]["avg_duration_ms"] == 1600.0

    assert "gemini" in stats
    assert stats["gemini"]["total_runs"] == 1
    assert stats["gemini"]["successful_runs"] == 1
    assert stats["gemini"]["success_rate"] == 1.0


def test_memory_manager_telemetry_integration(tmp_path):
    db_path = str(tmp_path / "test_memory_telemetry.db")
    vault_path = str(tmp_path / "vault")
    db = Database(db_path)
    obsidian = ObsidianManager(vault_path)
    memory = MemoryManager(db, obsidian)

    memory.record_execution_telemetry(
        task_id="task_mem",
        workflow_id="wf_mem",
        executor_id="nvidia",
        success=True,
        duration_ms=450.0,
    )

    stats = memory.get_executor_stats("nvidia")
    assert "nvidia" in stats
    assert stats["nvidia"]["total_runs"] == 1
    assert stats["nvidia"]["success_rate"] == 1.0
