from collections.abc import Callable
from inspect import signature
from typing import Any

import structlog

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
