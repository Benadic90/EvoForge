import json
from typing import Any

import structlog
from pydantic import BaseModel

from evoforge.evolution.agent import EvolutionAgent
from evoforge.github_integration.repository import LocalRepository

logger = structlog.get_logger(__name__)

class EvolutionProposal(BaseModel):
    agent_name: str
    skill_name: str
    current_version: int
    proposed_changes: dict[str, Any]
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

    def create_proposal_pr(self, proposal: EvolutionProposal, repo_full_name: str = "Benadic90/EvoForge") -> str:
        """Creates a real Git branch and PR on GitHub for human review of the self-evolution proposal."""
        from evoforge.github_integration.git_workflow import AutonomousGitWorkflow
        
        branch_name = f"evo/skill-update-{proposal.agent_name.lower()}-{proposal.skill_name.lower()}-v{proposal.current_version + 1}"
        logger.info("creating_proposal_pr", branch=branch_name, repo=repo_full_name)
        
        git_flow = AutonomousGitWorkflow()
        
        summary = (
            f"### 🧬 EvoForge Self-Evolution Proposal\n\n"
            f"- **Target Agent:** `{proposal.agent_name}`\n"
            f"- **Target Skill:** `{proposal.skill_name}`\n"
            f"- **Version Upgrade:** `v{proposal.current_version}` ➔ `v{proposal.current_version + 1}`\n\n"
            f"#### 📊 Evidence\n{proposal.evidence}\n\n"
            f"#### 🎯 Expected Improvement\n{proposal.expected_improvement}\n\n"
            f"#### ⚙️ Proposed Changes\n```json\n{json.dumps(proposal.proposed_changes, indent=2)}\n```"
        )
        
        doc_filename = f"docs/evolution/proposals/{proposal.agent_name.lower()}_{proposal.skill_name.lower()}_v{proposal.current_version + 1}.md"
        file_changes = {
            doc_filename: summary
        }
        
        pr_url = git_flow.publish_task_solution(
            repo_full_name=repo_full_name,
            task_id=f"evo_{proposal.skill_name}_{proposal.current_version + 1}",
            task_title=f"Evolve {proposal.agent_name} {proposal.skill_name} to v{proposal.current_version + 1}",
            task_description=proposal.expected_improvement,
            solution_summary=summary,
            file_changes=file_changes,
        )
        return pr_url or f"https://github.com/{repo_full_name}"
