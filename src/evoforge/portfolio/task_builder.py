from evoforge.agents.capabilities import AgentCapability
from evoforge.model_router.requirements import TaskClassification, TaskRequirements
from evoforge.portfolio.models import PortfolioTask


class PortfolioTaskRequirementsBuilder:
    """Builds Phase 3 TaskRequirements from a Phase 4 PortfolioTask."""
    
    @staticmethod
    def build(task: PortfolioTask) -> TaskRequirements:
        req = TaskRequirements(
            task_id=task.task_id,
            task_type=PortfolioTaskRequirementsBuilder._infer_task_type(task),
            risk_level=task.risk,
            requires_repo_write=True, # In general, EvoForge portfolio tasks involve making changes.
            estimated_complexity="MEDIUM"
        )
        
        # We always want coding/refactoring tools for portfolio work if it's changing things
        req.required_capabilities = [AgentCapability.CODING, AgentCapability.REPO_NAVIGATION]
        req.requires_terminal = True
        
        # Incorporate required capabilities from task if mapped
        for cap_str in task.required_capabilities:
            try:
                cap = AgentCapability(cap_str)
                if cap not in req.required_capabilities:
                    req.required_capabilities.append(cap)
            except ValueError:
                pass
                
        # Heuristic rules based on task fields
        title_lower = task.title.lower()
        desc_lower = task.description.lower()
        
        if "test" in title_lower or "test" in desc_lower:
            req.required_capabilities.append(AgentCapability.TESTING)
            
        if "refactor" in title_lower or "cleanup" in title_lower:
            req.required_capabilities.append(AgentCapability.REFACTORING)
            req.required_capabilities.append(AgentCapability.MULTI_FILE_EDITING)
            
        if "security" in title_lower or "vulnerability" in title_lower:
            req.task_type = TaskClassification.SECURITY
            req.risk_level = "HIGH"
            req.quality_preference = 0.9 # We want the best model for security
            
        if task.risk == "HIGH":
            req.quality_preference = 0.9
            
        # Determine preferences
        if task.priority >= 0.8:
            req.latency_preference = 0.8
            req.cost_preference = 0.2
            req.quality_preference = max(req.quality_preference, 0.8)
            
        return req

    @staticmethod
    def _infer_task_type(task: PortfolioTask) -> TaskClassification:
        t = task.title.lower()
        if "fix" in t or "bug" in t:
            return TaskClassification.DEBUGGING
        if "test" in t:
            return TaskClassification.TESTING
        if "refactor" in t:
            return TaskClassification.REFACTORING
        if "docs" in t or "readme" in t:
            return TaskClassification.DOCUMENTATION
        if "security" in t or "cve" in t:
            return TaskClassification.SECURITY
        if "update" in t and "dependency" in t:
            return TaskClassification.DEPENDENCY_UPDATE
        
        return TaskClassification.CODING
