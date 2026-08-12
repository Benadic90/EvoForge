import structlog
from typing import Dict, Any, List
from pydantic import BaseModel
from evoforge.evolution.agent import EvolutionAgent
from evoforge.github_integration.repository import LocalRepository

logger = structlog.get_logger(__name__)

class EvolutionProposal(BaseModel):
    agent_name: str
    skill_name: str
    current_version: int
    proposed_changes: Dict[str, Any]
    evidence: str
    expected_improvement: str

class EvolutionProposer:
    def __init__(self, evo_agent: EvolutionAgent, repo: LocalRepository):
        self.evo_agent = evo_agent
        self.repo = repo

    def propose_improvement(self, agent_name: str, skill_name: str, failure_logs: str) -> EvolutionProposal:
        """Analyzes failures and proposes an improvement to a skill."""
        logger.info("proposing_improvement", agent=agent_name, skill=skill_name)
        
        # We delegate the actual analysis to the EvolutionAgent
        # The agent uses LLM to synthesize the failures into concrete skill patches.
        # MVP: stubbing the agent return
        if hasattr(self.evo_agent, 'propose_skill_update'):
            proposal_dict = self.evo_agent.propose_skill_update(agent_name, skill_name, failure_logs)
        else:
            # Fallback if agent doesn't have the new method yet
            proposal_dict = {
                "proposed_changes": {"patterns": ["Added missing error check."]},
                "evidence": "Observed 3 repeated crashes in module X.",
                "expected_improvement": "Reduced crash rate on edge cases."
            }
            
        return EvolutionProposal(
            agent_name=agent_name,
            skill_name=skill_name,
            current_version=1, # In reality we'd pull this from SkillRegistry
            proposed_changes=proposal_dict.get("proposed_changes", {}),
            evidence=proposal_dict.get("evidence", "No evidence provided"),
            expected_improvement=proposal_dict.get("expected_improvement", "Unknown")
        )

    def create_proposal_pr(self, proposal: EvolutionProposal) -> str:
        """Creates a Git branch and PR for a human to review the proposal."""
        branch_name = f"evo/skill-update-{proposal.agent_name}-{proposal.skill_name}-v{proposal.current_version + 1}"
        logger.info("creating_proposal_pr", branch=branch_name)
        
        # Here we would:
        # 1. Checkout new branch
        # 2. Write the proposed changes into the agent's prompt definition file (if file-based)
        # 3. Commit and push
        # 4. Create PR via GitHub API
        
        # For this MVP, we just mock the PR URL
        pr_url = f"https://github.com/Benadic90/EvoForge/pull/{proposal.current_version + 100}"
        return pr_url
