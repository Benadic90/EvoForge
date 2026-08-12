import builtins
from collections.abc import Callable
from inspect import signature
from typing import Any

import structlog

from evoforge.agents.capabilities import AgentCapability
from evoforge.agents.contracts import AgentContract, AgentExecutor
from evoforge.memory.events import emitter

logger = structlog.get_logger(__name__)

class Tool:
    def __init__(self, name: str, description: str, func: Callable):
        self.name = name
        self.description = description
        self.func = func
        self.signature = signature(func)

    def execute(self, **kwargs) -> Any:
        try:
            return self.func(**kwargs)
        except Exception as e:
            logger.error("tool_execution_failed", tool=self.name, error=str(e))
            return f"Error executing {self.name}: {e!s}"

class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def register(self, name: str, description: str, func: Callable):
        self.tools[name] = Tool(name, description, func)
        logger.debug("tool_registered", tool=name)

    def get_tool(self, name: str) -> Tool:
        if name not in self.tools:
            raise ValueError(f"Tool {name} not found in registry.")
        return self.tools[name]

    def list_tools(self) -> list[dict[str, str]]:
        return [{"name": t.name, "description": t.description} for t in self.tools.values()]


class AgentRegistry:
    """
    Authoritative registry for AgentContracts and their Executors.
    """
    def __init__(self):
        self._agents: dict[str, tuple[AgentContract, AgentExecutor]] = {}

    def register(self, contract: AgentContract, executor: AgentExecutor):
        """Registers a new agent."""
        if contract.agent_id in self._agents:
            raise ValueError(f"Agent ID '{contract.agent_id}' is already registered.")
            
        self._validate_contract(contract)
        
        self._agents[contract.agent_id] = (contract, executor)
        logger.info("agent_registered", agent_id=contract.agent_id, version=contract.version)
        emitter.emit("agent.registered", agent_id=contract.agent_id, version=contract.version)

    def _validate_contract(self, contract: AgentContract):
        """Validates agent contract metadata."""
        if not contract.agent_id or not contract.version:
            raise ValueError(f"Agent {contract.name} is missing ID or version.")
            
        # Normally we'd validate required_tools against ToolRegistry here if we had a ref to it

    def get(self, agent_id: str) -> tuple[AgentContract, AgentExecutor]:
        """Retrieves an agent contract and executor by ID."""
        if agent_id not in self._agents:
            raise KeyError(f"Agent '{agent_id}' not found in registry.")
        return self._agents[agent_id]

    def list(self) -> list[AgentContract]:
        """Lists all registered agent contracts."""
        return [contract for contract, _ in self._agents.values()]

    def enable(self, agent_id: str):
        contract, _ = self.get(agent_id)
        contract.enabled = True
        emitter.emit("agent.enabled", agent_id=agent_id)

    def disable(self, agent_id: str):
        contract, _ = self.get(agent_id)
        contract.enabled = False
        emitter.emit("agent.disabled", agent_id=agent_id)

    def remove(self, agent_id: str):
        if agent_id in self._agents:
            del self._agents[agent_id]

    def has(self, agent_id: str) -> bool:
        return agent_id in self._agents

    def find_by_capability(self, capability: AgentCapability) -> builtins.list[AgentContract]:
        """Finds all agents that have a specific capability."""
        return [c for c, _ in self._agents.values() if capability in c.capabilities]

