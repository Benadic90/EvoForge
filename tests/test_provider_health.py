from unittest.mock import MagicMock, patch

from evoforge.agents.capabilities import AgentCapability
from evoforge.model_router.executors import (
    AntigravityExecutor,
    ExecutorRegistry,
    GeminiExecutor,
    LocalModelExecutor,
    NvidiaExecutor,
)


def test_provider_health_checks_credentials(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    gemini = GeminiExecutor()
    nvidia = NvidiaExecutor()
    ag = AntigravityExecutor(enabled=False)

    assert gemini.health_check() is False
    assert nvidia.health_check() is False
    assert ag.health_check() is False

    monkeypatch.setenv("GEMINI_API_KEY", "valid_key")
    monkeypatch.setenv("NVIDIA_API_KEY", "valid_key")
    assert gemini.health_check() is True
    assert nvidia.health_check() is True


@patch("urllib.request.urlopen")
def test_local_provider_live_health_check(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    local = LocalModelExecutor(endpoint="http://localhost:11434")
    assert local.health_check() is True

    mock_urlopen.side_effect = Exception("Connection refused")
    assert local.health_check() is False


def test_executor_registry_dynamic_health():
    registry = ExecutorRegistry()
    gemini = GeminiExecutor()
    registry.register("gemini", gemini, [AgentCapability.CODING])

    # Dynamic delegation to executor health
    assert registry.is_healthy("gemini") == gemini.health_check()

    # Manual administrative override
    registry.set_health("gemini", False)
    assert registry.is_healthy("gemini") is False

    registry.set_health("gemini", True)
    assert registry.is_healthy("gemini") is True
