from unittest.mock import MagicMock, patch

import pytest

from evoforge.agents.contracts import AgentContext
from evoforge.memory.state import WorkflowStage
from evoforge.model_router.executors import (
    AntigravityExecutor,
    GeminiExecutor,
    LocalModelExecutor,
    NvidiaExecutor,
)


@pytest.fixture
def mock_context():
    return AgentContext(
        run_id="run_123",
        workflow_id="wf_123",
        task_id="task_123",
        task_description="Refactor user authentication module",
        current_stage=WorkflowStage.IMPLEMENT,
        dry_run=False,
    )


def test_local_model_executor_dry_run(mock_context):
    executor = LocalModelExecutor(model_id="qwen2.5-coder:7b-instruct-q4_K_M")
    mock_context.dry_run = True
    result = executor.execute(mock_context)
    assert result.success is True
    assert "[DRY RUN]" in result.summary
    assert result.metrics["provider"] == "ollama"
    assert result.metrics["dry_run"] is True


@patch("litellm.completion")
def test_local_model_executor_success(mock_litellm, mock_context):
    mock_choice = MagicMock()
    mock_choice.message.content = "def authenticate(user, password): return True"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 40
    mock_response.usage.completion_tokens = 25
    mock_litellm.return_value = mock_response

    executor = LocalModelExecutor(model_id="qwen2.5-coder:7b-instruct-q4_K_M")
    result = executor.execute(mock_context)

    assert result.success is True
    assert "authenticate" in result.summary
    assert result.metrics["provider"] == "ollama"
    assert result.metrics["input_tokens"] == 40
    assert result.metrics["output_tokens"] == 25
    assert result.metrics["cost"] == 0.0


@patch("litellm.completion")
def test_local_model_executor_timeout_classification(mock_litellm, mock_context):
    mock_litellm.side_effect = TimeoutError("Request timed out after 60s")

    executor = LocalModelExecutor()
    result = executor.execute(mock_context)

    assert result.success is False
    assert result.metrics["failure_class"] == "timeout"
    assert result.metrics["retryable"] is True
    assert len(result.errors) > 0


def test_gemini_executor_missing_api_key(mock_context, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    executor = GeminiExecutor()
    assert executor.health_check() is False

    result = executor.execute(mock_context)
    assert result.success is False
    assert result.metrics["failure_class"] == "missing_credentials"
    assert result.metrics["retryable"] is False


@patch("litellm.completion")
@patch("litellm.completion_cost", return_value=0.0025)
def test_gemini_executor_success(mock_cost, mock_litellm, mock_context, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_test_key")

    mock_choice = MagicMock()
    mock_choice.message.content = "Gemini generated implementation code"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_litellm.return_value = mock_response

    executor = GeminiExecutor(model_id="gemini/gemini-2.5-flash")
    assert executor.health_check() is True

    result = executor.execute(mock_context)
    assert result.success is True
    assert "Gemini generated" in result.summary
    assert result.metrics["cost"] == 0.0025
    assert result.metrics["provider"] == "gemini"


@patch("litellm.completion")
def test_gemini_executor_rate_limit_classification(mock_litellm, mock_context, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_test_key")
    mock_litellm.side_effect = Exception("HTTP 429: Resource exhausted / rate limit exceeded")

    executor = GeminiExecutor()
    result = executor.execute(mock_context)

    assert result.success is False
    assert result.metrics["failure_class"] == "rate_limit"
    assert result.metrics["retryable"] is True


def test_nvidia_executor_missing_key(mock_context, monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    executor = NvidiaExecutor()
    assert executor.health_check() is False

    result = executor.execute(mock_context)
    assert result.success is False
    assert result.metrics["failure_class"] == "missing_credentials"


@patch("litellm.completion")
@patch("litellm.completion_cost", return_value=0.001)
def test_nvidia_executor_success(mock_cost, mock_litellm, mock_context, monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "dummy_nvidia_key")

    mock_choice = MagicMock()
    mock_choice.message.content = "NVIDIA NIM execution output"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 60
    mock_response.usage.completion_tokens = 30
    mock_litellm.return_value = mock_response

    executor = NvidiaExecutor()
    assert executor.health_check() is True

    result = executor.execute(mock_context)
    assert result.success is True
    assert "NVIDIA NIM" in result.summary
    assert result.metrics["provider"] == "nvidia"


def test_antigravity_boundary_unverified(mock_context):
    executor = AntigravityExecutor(enabled=False)
    assert executor.health_check() is False

    result = executor.execute(mock_context)
    assert result.success is False
    assert result.metrics["failure_class"] == "provider_unavailable"
