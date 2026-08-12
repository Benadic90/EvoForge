import structlog
from typing import Dict, Any, List, Optional
import json

from evoforge.model_router.router import ModelRouter, LLMRequest
from evoforge.model_router.classifier import TaskType, TaskComplexity
from evoforge.model_router.fallback import FallbackManager
from .registry import ToolRegistry

logger = structlog.get_logger(__name__)

class BaseAgent:
    def __init__(self, name: str, role: str, model_router: ModelRouter, tools: ToolRegistry, skill_profile=None):
        self.name = name
        self.role = role
        self.router = model_router
        self.fallback_manager = FallbackManager(self.router)
        self.tools = tools
        self.skill_profile = skill_profile
        self.memory: List[Dict[str, str]] = []

    def _get_system_prompt(self) -> str:
        """Generates the system prompt including tool descriptions and skills."""
        base_prompt = f"You are {self.name}, an AI software engineer. Your role is: {self.role}\n"
        
        if self.skill_profile:
            base_prompt += self.skill_profile.render_skills_context()
            
        base_prompt += "\nYou have access to the following tools. To use a tool, respond with a JSON object: {\"tool\": \"tool_name\", \"kwargs\": {\"arg1\": \"value\"}}\n"
        base_prompt += "Tools available:\n"
        
        for t in self.tools.list_tools():
            base_prompt += f"- {t['name']}: {t['description']}\n"
            
        return base_prompt

    def think_and_act(self, task_description: str, task_type: TaskType, complexity: TaskComplexity) -> str:
        """Core loop for an agent to process a task, use tools, and return a final answer."""
        self.memory.append({"role": "user", "content": task_description})
        
        # Max steps to prevent infinite loops
        max_steps = 10
        for step in range(max_steps):
            request = LLMRequest(
                prompt=json.dumps(self.memory),
                system_prompt=self._get_system_prompt(),
                task_type=task_type,
                complexity=complexity,
                max_tokens=2048,
                require_json=False # In a real implementation we might use tool calling API or JSON mode
            )
            
            try:
                response = self.fallback_manager.complete_with_fallback(request)
                content = response.content
                self.memory.append({"role": "assistant", "content": content})
                
                # Very basic manual tool parsing for MVP (Replace with LiteLLM tool calling in production)
                if '{"tool":' in content:
                    try:
                        # Find the JSON block
                        start = content.find('{"tool":')
                        end = content.rfind('}') + 1
                        tool_call = json.loads(content[start:end])
                        
                        tool_name = tool_call["tool"]
                        kwargs = tool_call.get("kwargs", {})
                        
                        logger.info("agent_using_tool", agent=self.name, tool=tool_name)
                        tool_result = self.tools.get_tool(tool_name).execute(**kwargs)
                        
                        self.memory.append({"role": "system", "content": f"Tool '{tool_name}' returned: {tool_result}"})
                    except Exception as e:
                        logger.error("tool_parsing_failed", error=str(e))
                        self.memory.append({"role": "system", "content": f"Failed to parse tool call: {str(e)}"})
                else:
                    # No tool called, we assume this is the final answer
                    return content
                    
            except Exception as e:
                logger.error("agent_execution_failed", error=str(e))
                return f"Agent failed: {str(e)}"
                
        return "Agent failed: Exceeded maximum steps."
