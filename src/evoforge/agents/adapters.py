import time

from evoforge.agents.base import BaseAgent
from evoforge.agents.contracts import AgentContext, AgentContract, AgentExecutor, AgentResult
from evoforge.model_router.classifier import TaskComplexity, TaskType


class LegacyAgentAdapter(AgentExecutor):
    """
    Translates the new standard AgentContext into the ad-hoc method calls 
    used by the legacy BaseAgent subclasses (e.g. DeveloperAgent.implement_feature).
    """
    def __init__(self, contract: AgentContract, legacy_agent: BaseAgent):
        self.contract = contract
        self.legacy_agent = legacy_agent

    def execute(self, context: AgentContext) -> AgentResult:
        start_time = time.time()
        agent_id = self.contract.agent_id
        
        try:
            # Map legacy method calls
            if agent_id == "developer":
                # Assuming context_files can be passed via metadata or memory_context, defaulting to empty
                context_files = context.metadata.get("context_files", [])
                result_text = self.legacy_agent.implement_feature(context.task_description, context_files=context_files)
            elif agent_id == "qa":
                # Assuming test_output_path can be provided via metadata
                test_output_path = context.metadata.get("test_output_path", "test_output.py")
                # qa.py uses write_tests(self, description, test_file_path)
                # We handle it dynamically just in case it doesn't strictly match the type signature
                result_text = self.legacy_agent.write_tests(context.task_description, test_output_path)
            elif agent_id == "reviewer":
                result_text = self.legacy_agent.review_changes(context.task_description)
            elif agent_id == "security":
                result_text = self.legacy_agent.audit_code(context.task_description)
            else:
                # Default fallback for agents that just use think_and_act directly
                # We pass mock/default Enums if they are required by the legacy signature
                result_text = self.legacy_agent.think_and_act(
                    task_description=context.task_description,
                    task_type=TaskType.CODE_GENERATION, # Dummy default
                    complexity=TaskComplexity.MEDIUM      # Dummy default
                )
                
            success = "failed" not in result_text.lower()
            
            return AgentResult(
                success=success,
                agent_id=agent_id,
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=result_text,
                artifacts=[],
                metrics={"duration_seconds": time.time() - start_time},
                errors=[],
                warnings=[],
                metadata={}
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                agent_id=agent_id,
                task_id=context.task_id,
                workflow_id=context.workflow_id,
                summary=f"Legacy agent execution failed: {e!s}",
                artifacts=[],
                metrics={"duration_seconds": time.time() - start_time},
                errors=[str(e)],
                warnings=[],
                metadata={}
            )
