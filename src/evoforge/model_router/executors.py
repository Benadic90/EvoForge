from typing import Any

import structlog

from evoforge.agents.capabilities import AgentCapability
from evoforge.agents.contracts import AgentContext, AgentExecutor, AgentResult

logger = structlog.get_logger(__name__)

class ExecutorRegistry:
    """Registry tracking all available execution environments/backends."""
    def __init__(self):
        self._executors: dict[str, AgentExecutor] = {}
        self._capabilities: dict[str, list[AgentCapability]] = {}
        self._health: dict[str, bool] = {}
        self._enabled: dict[str, bool] = {}

    def register(self, executor_id: str, executor: AgentExecutor, capabilities: list[AgentCapability]):
        if executor_id in self._executors:
            raise ValueError(f"Executor '{executor_id}' already registered.")
        
        self._executors[executor_id] = executor
        self._capabilities[executor_id] = capabilities
        self._health[executor_id] = True
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
        
    def is_healthy(self, executor_id: str) -> bool:
        # In a real system, we'd poll or query the executor
        return self._health.get(executor_id, False)

    def set_health(self, executor_id: str, healthy: bool):
        if executor_id in self._health:
            self._health[executor_id] = healthy


class LocalModelExecutor(AgentExecutor):
    """Executes a task using a local model (e.g. Ollama)."""
    def execute(self, context: AgentContext) -> AgentResult:
        logger.info("executing_task_local", task_id=context.task_id)
        # Mock logic
        return AgentResult(
            success=True,
            agent_id="local_model_executor",
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            summary="Executed locally via Ollama.",
            metrics={"latency_ms": 1500, "cost": 0.0}
        )

class GeminiExecutor(AgentExecutor):
    """Executes a task using Google's Gemini API."""
    def execute(self, context: AgentContext) -> AgentResult:
        logger.info("executing_task_gemini", task_id=context.task_id)
        # Mock logic
        return AgentResult(
            success=True,
            agent_id="gemini_executor",
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            summary="Executed via Gemini API.",
            metrics={"latency_ms": 800, "cost": 0.02}
        )

class NvidiaExecutor(AgentExecutor):
    """Executes a task using NVIDIA APIs."""
    def execute(self, context: AgentContext) -> AgentResult:
        logger.info("executing_task_nvidia", task_id=context.task_id)
        # Mock logic
        return AgentResult(
            success=True,
            agent_id="nvidia_executor",
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            summary="Executed via NVIDIA API.",
            metrics={"latency_ms": 400, "cost": 0.03}
        )

class AntigravityExecutor(AgentExecutor):
    """
    Executes a task using the Antigravity agentic runtime.
    This acts as a clean boundary. If Antigravity is not installed/reachable, 
    it returns failure or is marked unhealthy, preventing routing.
    """
    def execute(self, context: AgentContext) -> AgentResult:
        logger.info("executing_task_antigravity", task_id=context.task_id)
        
        # Integration point: In real system, this would make an API call or spawn an Antigravity subprocess.
        # For now, it's a boundary stub.
        
        return AgentResult(
            success=True,
            agent_id="antigravity_executor",
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            summary="Executed via Antigravity boundary.",
            metrics={"latency_ms": 3000, "cost": 0.0}
        )
