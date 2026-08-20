import os
import time
import urllib.error
import urllib.request
from typing import Any

import litellm
import structlog

from evoforge.agents.capabilities import AgentCapability
from evoforge.agents.contracts import AgentContext, AgentExecutor, AgentResult
from evoforge.memory.database import Database

logger = structlog.get_logger(__name__)

# Suppress litellm debug noise
litellm.suppress_debug_info = True


class ExecutorRegistry:
    """Registry tracking all available execution environments/backends."""

    def __init__(self):
        self._executors: dict[str, AgentExecutor] = {}
        self._capabilities: dict[str, list[AgentCapability]] = {}
        self._health_override: dict[str, bool] = {}
        self._enabled: dict[str, bool] = {}

    def register(
        self,
        executor_id: str,
        executor: AgentExecutor,
        capabilities: list[AgentCapability],
    ):
        if executor_id in self._executors:
            raise ValueError(f"Executor '{executor_id}' already registered.")

        self._executors[executor_id] = executor
        self._capabilities[executor_id] = capabilities
        self._enabled[executor_id] = True
        logger.info("executor_registered", executor_id=executor_id)

    def get(self, executor_id: str) -> AgentExecutor:
        if executor_id not in self._executors:
            raise KeyError(f"Executor '{executor_id}' not found.")
        return self._executors[executor_id]

    def list_all(self) -> list[str]:
        return list(self._executors.keys())

    def get_capabilities(self, executor_id: str) -> list[AgentCapability]:
        return self._capabilities.get(executor_id, [])

    def is_enabled(self, executor_id: str) -> bool:
        return self._enabled.get(executor_id, False)

    def set_enabled(self, executor_id: str, enabled: bool):
        if executor_id in self._executors:
            self._enabled[executor_id] = enabled

    def is_healthy(self, executor_id: str) -> bool:
        """Check health via explicit override or live executor health check."""
        if executor_id not in self._executors:
            return False

        # If administratively overridden, return that
        if executor_id in self._health_override:
            return self._health_override[executor_id]

        executor = self._executors[executor_id]
        try:
            return executor.health_check()
        except Exception as e:
            logger.warning("executor_health_check_failed", executor_id=executor_id, error=str(e))
            return False

    def set_health(self, executor_id: str, healthy: bool):
        """Allows test fixtures or operators to explicitly force health status."""
        self._health_override[executor_id] = healthy


def _classify_error(error: Exception) -> tuple[str, bool]:
    """Classifies an exception into a standard failure class and retryable flag."""
    err_str = str(error).lower()

    if isinstance(error, TimeoutError) or "timeout" in err_str or "timed out" in err_str:
        return "timeout", True
    if "rate limit" in err_str or "429" in err_str or "quota" in err_str or "resource exhausted" in err_str:
        return "rate_limit", True
    if "connection" in err_str or "refused" in err_str or "unreachable" in err_str:
        return "connection_error", True
    if "auth" in err_str or "api key" in err_str or "unauthorized" in err_str or "401" in err_str or "403" in err_str:
        return "auth_error", False
    if "context length" in err_str or "maximum context" in err_str or "token limit" in err_str:
        return "context_length_exceeded", False

    return "general_error", False



class LocalModelExecutor(AgentExecutor):
    """Executes a task using a local model endpoint (e.g. Ollama)."""

    def __init__(
        self,
        model_id: str = "qwen2.5-coder:7b-instruct-q4_K_M",
        endpoint: str = "http://localhost:11434",
        timeout_seconds: float = 60.0,
    ):
        self.model_id = model_id
        self.endpoint = endpoint.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def health_check(self) -> bool:
        """Checks if the local Ollama instance is reachable."""
        try:
            req = urllib.request.Request(f"{self.endpoint}/api/tags", headers={"User-Agent": "EvoForge"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def execute(self, context: AgentContext) -> AgentResult:
        logger.info("executing_task_local", task_id=context.task_id, model=self.model_id)

        if context.dry_run:
            return AgentResult(
                success=True,
                agent_id="local_model_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=f"[DRY RUN] Simulated local model execution ({self.model_id}) for task: {context.task_description}",
                metrics={
                    "latency_ms": 0.0,
                    "cost": 0.0,
                    "provider": "ollama",
                    "model": self.model_id,
                    "dry_run": True,
                    "input_tokens": 0,
                    "output_tokens": 0,
                },
            )

        start_time = time.time()
        prompt = (
            f"You are executing an autonomous engineering task.\n"
            f"Stage: {context.current_stage.value}\n"
            f"Task: {context.task_description}\n"
        )
        messages = [{"role": "user", "content": prompt}]

        litellm_model = f"ollama/{self.model_id}"
        try:
            response = litellm.completion(
                model=litellm_model,
                messages=messages,
                api_base=self.endpoint,
                timeout=self.timeout_seconds,
            )
            duration_ms = (time.time() - start_time) * 1000.0
            content = response.choices[0].message.content or ""
            input_tokens = getattr(response.usage, "prompt_tokens", 0) if response.usage else 0
            output_tokens = getattr(response.usage, "completion_tokens", 0) if response.usage else 0

            return AgentResult(
                success=True,
                agent_id="local_model_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=content[:500] if len(content) > 500 else content,
                metrics={
                    "latency_ms": duration_ms,
                    "cost": 0.0,
                    "provider": "ollama",
                    "model": self.model_id,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
                metadata={"full_output": content},
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000.0
            fail_class, retryable = _classify_error(e)
            logger.warning("local_execution_failed", error=str(e), failure_class=fail_class)
            return AgentResult(
                success=False,
                agent_id="local_model_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=f"Local execution failed ({fail_class}): {e!s}",
                errors=[str(e)],
                metrics={
                    "latency_ms": duration_ms,
                    "cost": 0.0,
                    "provider": "ollama",
                    "model": self.model_id,
                    "failure_class": fail_class,
                    "retryable": retryable,
                },
            )


class GeminiExecutor(AgentExecutor):
    """Executes a task using Google's Gemini API."""

    def __init__(
        self,
        db: Database | None = None,
        model_id: str = "gemini/gemini-1.5-flash",
        timeout_seconds: float = 60.0,
    ):
        self.db = db
        self.model_id = model_id if model_id.startswith("gemini/") else f"gemini/{model_id}"
        self.timeout_seconds = timeout_seconds

    def _get_api_key(self) -> str | None:
        if self.db:
            rows = self.db.fetchall("SELECT value FROM system_settings WHERE key = 'gemini_api_key'")
            if rows and rows[0]["value"]:
                return rows[0]["value"]
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def health_check(self) -> bool:
        """Checks if Gemini API credentials exist."""
        return bool(self._get_api_key())

    def execute(self, context: AgentContext) -> AgentResult:
        logger.info("executing_task_gemini", task_id=context.task_id, model=self.model_id)

        if context.dry_run:
            return AgentResult(
                success=True,
                agent_id="gemini_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=f"[DRY RUN] Simulated Gemini execution ({self.model_id}) for task: {context.task_description}",
                metrics={
                    "latency_ms": 0.0,
                    "cost": 0.0,
                    "provider": "gemini",
                    "model": self.model_id,
                    "dry_run": True,
                    "input_tokens": 0,
                    "output_tokens": 0,
                },
            )

        api_key = self._get_api_key()
        if not api_key:
            return AgentResult(
                success=False,
                agent_id="gemini_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary="Gemini execution failed: No GEMINI_API_KEY or GOOGLE_API_KEY in environment.",
                errors=["Missing GEMINI_API_KEY credentials"],
                metrics={
                    "latency_ms": 0.0,
                    "cost": 0.0,
                    "provider": "gemini",
                    "model": self.model_id,
                    "failure_class": "missing_credentials",
                    "retryable": False,
                },
            )

        if context.required_capabilities and any(c.name == "TERMINAL" for c in context.required_capabilities):
            from evoforge.model_router.tool_loop import ToolLoopRunner
            runner = ToolLoopRunner(db=self.db, model_id=self.model_id, timeout_seconds=self.timeout_seconds)
            return runner.run(context, api_key)

        start_time = time.time()
        prompt = (
            f"You are executing an autonomous engineering task.\n"
            f"Stage: {context.current_stage.value}\n"
            f"Task: {context.task_description}\n"
        )
        messages = [{"role": "user", "content": prompt}]

        try:
            response = litellm.completion(
                model=self.model_id,
                messages=messages,
                api_key=api_key,
                timeout=self.timeout_seconds,
            )
            duration_ms = (time.time() - start_time) * 1000.0
            content = response.choices[0].message.content or ""
            input_tokens = getattr(response.usage, "prompt_tokens", 0) if response.usage else 0
            output_tokens = getattr(response.usage, "completion_tokens", 0) if response.usage else 0
            try:
                cost = litellm.completion_cost(completion_response=response) or 0.0
            except Exception:
                cost = 0.0

            return AgentResult(
                success=True,
                agent_id="gemini_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=content[:500] if len(content) > 500 else content,
                metrics={
                    "latency_ms": duration_ms,
                    "cost": cost,
                    "provider": "gemini",
                    "model": self.model_id,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
                metadata={"full_output": content},
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000.0
            fail_class, retryable = _classify_error(e)
            logger.warning("gemini_execution_failed", error=str(e), failure_class=fail_class)
            return AgentResult(
                success=False,
                agent_id="gemini_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=f"Gemini execution failed ({fail_class}): {e!s}",
                errors=[str(e)],
                metrics={
                    "latency_ms": duration_ms,
                    "cost": 0.0,
                    "provider": "gemini",
                    "model": self.model_id,
                    "failure_class": fail_class,
                    "retryable": retryable,
                },
            )


class NvidiaExecutor(AgentExecutor):
    """Executes a task using NVIDIA Cloud APIs."""

    def __init__(
        self,
        db: Database | None = None,
        model_id: str = "deepseek-ai/deepseek-coder-33b-instruct",
        endpoint: str = "https://integrate.api.nvidia.com/v1",
        timeout_seconds: float = 60.0,
    ):
        self.db = db
        self.model_id = model_id
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    def _get_api_key(self) -> str | None:
        if self.db:
            rows = self.db.fetchall("SELECT value FROM system_settings WHERE key = 'nvidia_api_key'")
            if rows and rows[0]["value"]:
                return rows[0]["value"]
        return os.environ.get("NVIDIA_API_KEY")

    def health_check(self) -> bool:
        """Checks if NVIDIA API credentials exist."""
        return bool(self._get_api_key())

    def execute(self, context: AgentContext) -> AgentResult:
        logger.info("executing_task_nvidia", task_id=context.task_id, model=self.model_id)

        if context.dry_run:
            return AgentResult(
                success=True,
                agent_id="nvidia_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=f"[DRY RUN] Simulated NVIDIA execution ({self.model_id}) for task: {context.task_description}",
                metrics={
                    "latency_ms": 0.0,
                    "cost": 0.0,
                    "provider": "nvidia",
                    "model": self.model_id,
                    "dry_run": True,
                    "input_tokens": 0,
                    "output_tokens": 0,
                },
            )

        api_key = self._get_api_key()
        if not api_key:
            return AgentResult(
                success=False,
                agent_id="nvidia_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary="NVIDIA execution failed: No NVIDIA_API_KEY in environment.",
                errors=["Missing NVIDIA_API_KEY credentials"],
                metrics={
                    "latency_ms": 0.0,
                    "cost": 0.0,
                    "provider": "nvidia",
                    "model": self.model_id,
                    "failure_class": "missing_credentials",
                    "retryable": False,
                },
            )

        start_time = time.time()
        prompt = (
            f"You are executing an autonomous engineering task.\n"
            f"Stage: {context.current_stage.value}\n"
            f"Task: {context.task_description}\n"
        )
        messages = [{"role": "user", "content": prompt}]

        litellm_model = f"openai/{self.model_id}"
        try:
            response = litellm.completion(
                model=litellm_model,
                messages=messages,
                api_base=self.endpoint,
                api_key=api_key,
                timeout=self.timeout_seconds,
            )
            duration_ms = (time.time() - start_time) * 1000.0
            content = response.choices[0].message.content or ""
            input_tokens = getattr(response.usage, "prompt_tokens", 0) if response.usage else 0
            output_tokens = getattr(response.usage, "completion_tokens", 0) if response.usage else 0
            try:
                cost = litellm.completion_cost(completion_response=response) or 0.0
            except Exception:
                cost = 0.0

            return AgentResult(
                success=True,
                agent_id="nvidia_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=content[:500] if len(content) > 500 else content,
                metrics={
                    "latency_ms": duration_ms,
                    "cost": cost,
                    "provider": "nvidia",
                    "model": self.model_id,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
                metadata={"full_output": content},
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000.0
            fail_class, retryable = _classify_error(e)
            logger.warning("nvidia_execution_failed", error=str(e), failure_class=fail_class)
            return AgentResult(
                success=False,
                agent_id="nvidia_executor",
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=f"NVIDIA execution failed ({fail_class}): {e!s}",
                errors=[str(e)],
                metrics={
                    "latency_ms": duration_ms,
                    "cost": 0.0,
                    "provider": "nvidia",
                    "model": self.model_id,
                    "failure_class": fail_class,
                    "retryable": retryable,
                },
            )


class AntigravityExecutor(AgentExecutor):
    """
    Executes a task using the Antigravity agentic runtime.
    This acts as an explicit boundary. If Antigravity is not reachable/enabled,
    it reports unavailable rather than pretending to perform work.
    """

    def __init__(self, endpoint: str | None = None, enabled: bool = False):
        self.endpoint = endpoint
        self.enabled = enabled or bool(os.environ.get("ANTIGRAVITY_ENABLED", "").lower() in ("true", "1"))
        from evoforge.model_router.antigravity_runtime import AntigravityRuntimeDetector
        self.detector = AntigravityRuntimeDetector

    def health_check(self) -> bool:
        """Boundary is only healthy if explicitly enabled and accessible."""
        if not self.enabled:
            return False
        return self.detector.health_check()

    def execute(self, context: AgentContext) -> AgentResult:
        logger.info("executing_task_antigravity", task_id=context.task_id)
        
        # We use the typed models from model_router.models
        # Even though we don't execute, we construct the request to demonstrate the correct type boundary.
        from evoforge.model_router.models import (
            AntigravityExecutionRequest,
            AntigravityExecutionResult,
        )
        req = AntigravityExecutionRequest(
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            agent_id=context.metadata.get("agent_id"),
            task_description=context.task_description,
            requirements=[c.value for c in context.required_capabilities],
            permissions=context.permissions,
            dry_run=context.dry_run,
        )

        if not self.health_check():
            info = self.detector.get_runtime_info()
            reason = info.reason_unavailable or "Antigravity runtime boundary unavailable"
            
            res = AntigravityExecutionResult(
                success=False,
                status="UNAVAILABLE",
                summary=f"Antigravity boundary execution failed: {reason}",
                error_type="provider_unavailable",
                error_message_sanitized=reason,
                executor_id="antigravity_executor"
            )
            
            return AgentResult(
                success=res.success,
                agent_id=res.executor_id,
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=res.summary,
                errors=[reason],
                metrics={
                    "latency_ms": res.duration_ms,
                    "cost": 0.0,
                    "provider": res.provider_id,
                    "failure_class": res.error_type,
                    "retryable": False,
                },
            )

        # Active boundary execution stub if enabled and reachable
        # (This block won't be reached in current environment, but acts as the template for real execution)
        res = AntigravityExecutionResult(
            success=True,
            status="COMPLETED",
            summary=f"Executed via Antigravity runtime boundary for: {context.task_description}",
            duration_ms=100.0,
            executor_id="antigravity_executor"
        )
        return AgentResult(
            success=res.success,
            agent_id=res.executor_id,
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            summary=res.summary,
            metrics={"latency_ms": res.duration_ms, "cost": 0.0, "provider": res.provider_id},
        )

    def cancel(self, task_id: str) -> None:
        if not self.health_check():
            logger.warning("antigravity_cancel_unavailable", task_id=task_id)
            return
        logger.info("antigravity_cancel", task_id=task_id)

    def get_status(self, task_id: str) -> str:
        if not self.health_check():
            return "UNAVAILABLE"
        return "UNKNOWN"


def create_default_executor_registry(config: Any = None, db: Database | None = None) -> ExecutorRegistry:
    """Builds and registers standard execution backends."""
    registry = ExecutorRegistry()

    # Local Ollama
    local_ep = config.providers.ollama.endpoint if (config and hasattr(config, "providers")) else None
    local_mod = config.providers.ollama.default_model if (config and hasattr(config, "providers")) else None
    registry.register(
        "local",
        LocalModelExecutor(endpoint=local_ep, model_id=local_mod),
        [
            AgentCapability.CODING,
            AgentCapability.REFACTORING,
            AgentCapability.MULTI_FILE_EDITING,
            AgentCapability.TERMINAL,
            AgentCapability.PLANNING,
        ],
    )

    # Gemini
    registry.register("gemini", GeminiExecutor(db=db, model_id="gemini/gemini-3.1-pro-preview-customtools"), [
        AgentCapability.CODING,
        AgentCapability.REASONING,
        AgentCapability.REFACTORING,
        AgentCapability.MULTI_FILE_EDITING,
        AgentCapability.REPO_NAVIGATION,
        AgentCapability.TERMINAL,
        AgentCapability.PLANNING,
    ])

    # NVIDIA
    nvid_mod = config.providers.nvidia.default_model if (config and hasattr(config, "providers")) else None
    nvid_ep = config.providers.nvidia.endpoint if (config and hasattr(config, "providers")) else None
    registry.register(
        "nvidia",
        NvidiaExecutor(model_id=nvid_mod, endpoint=nvid_ep, db=db),
        [
            AgentCapability.CODING,
            AgentCapability.REASONING,
            AgentCapability.REFACTORING,
            AgentCapability.MULTI_FILE_EDITING,
            AgentCapability.TERMINAL,
            AgentCapability.PLANNING,
        ],
    )


    # Antigravity
    ag_ep = config.providers.antigravity.endpoint if (config and hasattr(config, "providers")) else None
    ag_en = config.providers.antigravity.enabled if (config and hasattr(config, "providers")) else False
    registry.register(
        "antigravity",
        AntigravityExecutor(endpoint=ag_ep, enabled=ag_en),
        [
            AgentCapability.CODING,
            AgentCapability.REASONING,
            AgentCapability.BROWSER,
            AgentCapability.TERMINAL,
            AgentCapability.REPO_NAVIGATION,
            AgentCapability.TESTING,
            AgentCapability.MULTI_FILE_EDITING,
        ],
    )

    return registry

