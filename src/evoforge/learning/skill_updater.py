from typing import Any

import structlog

from evoforge.learning.evaluator import EvaluationResult
from evoforge.learning.evolution_proposer import EvolutionProposal
from evoforge.learning.skill_registry import Skill, SkillRegistry
from evoforge.learning.skill_versioner import SkillVersioner
from evoforge.memory.obsidian import ObsidianManager

logger = structlog.get_logger(__name__)

class SkillUpdater:
    def __init__(self, registry: SkillRegistry, versioner: SkillVersioner, obsidian: ObsidianManager, agents_roster: dict[str, Any]):
        self.registry = registry
        self.versioner = versioner
        self.obsidian = obsidian
        self.agents_roster = agents_roster

    def deploy_skill_update(self, proposal: EvolutionProposal, evaluation: EvaluationResult) -> bool:
        """Deploys an approved skill update to production."""
        if not evaluation.approved:
            logger.warning("deploy_rejected", reason="Evaluation not approved.")
            return False
            
        logger.info("deploying_skill_update", agent=proposal.agent_name, skill=proposal.skill_name)
        
        # 1. Fetch current base skill (mocked here, we would normally get it from Registry)
        # Assuming we just have a dummy skill object for the sake of the API
        base_skill = Skill(name=proposal.skill_name)
        
        # 2. Create the new version in the database
        new_skill = self.versioner.create_version(
            agent_name=proposal.agent_name,
            skill=base_skill,
            changes=proposal.proposed_changes,
            benchmark_score=evaluation.benchmark_result.score
        )
        
        # 3. Hot-reload the agent's memory/profile
        self.hot_reload_agent(proposal.agent_name)
        
        # 4. Notify any dependent agents (e.g., cross-agent sharing system might pick this up)
        self.notify_dependent_agents(proposal.agent_name, new_skill)
        
        return True

    def hot_reload_agent(self, agent_name: str):
        """Re-fetches the agent's profile and updates the running instance."""
        if agent_name not in self.agents_roster:
            logger.warning("agent_not_found_for_reload", agent=agent_name)
            return
            
        agent_instance = self.agents_roster[agent_name]
        
        # Rebuild the skill profile from DB
        new_profile = self.registry.build_profile(agent_name)
        
        # Inject into agent instance
        agent_instance.skill_profile = new_profile
        logger.info("agent_hot_reloaded", agent=agent_name)

    def notify_dependent_agents(self, source_agent: str, skill: Skill):
        """Hook for notifying other agents of the new skill."""
        logger.debug("notifying_dependent_agents", source=source_agent, skill=skill.name)
        # This will be integrated with the KnowledgeSharing module in Phase L11
