import uuid

import structlog

from evoforge.agents.base import BaseAgent
from evoforge.agents.registry import ToolRegistry
from evoforge.learning.models import EvolutionProposal
from evoforge.memory.database import Database
from evoforge.model_router.classifier import TaskComplexity, TaskType
from evoforge.model_router.router import ModelRouter

logger = structlog.get_logger(__name__)

class EvolutionAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry, db: Database):
        super().__init__(
            name="EvolutionAgent",
            role="Analyze system performance, analyze failing workflows, and propose safe, sandboxed skill improvements.",
            model_router=model_router,
            tools=tools
        )
        self.db = db
        
    def propose_skill_update(self, agent_name: str, skill_name: str, failure_logs: str) -> EvolutionProposal:
        """Proposes changes to an agent's skill based on failures, creating an EvolutionProposal."""
        task_prompt = f"Agent '{agent_name}' has failed repeatedly while using skill '{skill_name}'.\nFailure logs:\n{failure_logs}\n\nBased on these failures, propose specific additions to their techniques, patterns, or anti-patterns to prevent this."
        
        # In a real setup, we would parse JSON output.
        result = self.think_and_act(
            task_description=task_prompt,
            task_type=TaskType.REASONING,
            complexity=TaskComplexity.HIGH
        )
        
        proposal = EvolutionProposal(
            proposal_id=str(uuid.uuid4()),
            target=f"skill:{agent_name}:{skill_name}",
            change_type="SKILL_UPDATE",
            description=result[:200] + "...",  # Summarize for the proposal object
            evidence_ids=[],
            expected_improvement="Objective improvement in handling edge cases based on recent failures.",
            risk="LOW"
        )
        
        self._save_proposal(proposal)
        return proposal

    def review_proposal(self, proposal: EvolutionProposal) -> bool:
        """Reviews an innovation proposal to ensure it's objectively sound before sandbox testing."""
        task_prompt = f"Review the following skill update proposal for {proposal.target}:\n\n{proposal.description}\n\nIs this a safe and objectively measurable improvement? Reply only YES or NO."
        
        result = self.think_and_act(
            task_description=task_prompt,
            task_type=TaskType.REASONING,
            complexity=TaskComplexity.MEDIUM
        )
        approved = "YES" in result.upper()
        
        if approved:
            self._update_proposal_status(proposal.proposal_id, "TESTING")
        else:
            self._update_proposal_status(proposal.proposal_id, "REJECTED")
            
        return approved

    def _save_proposal(self, proposal: EvolutionProposal):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO evolution_proposals 
                (proposal_id, target, change_type, description, expected_improvement, risk, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (proposal.proposal_id, proposal.target, proposal.change_type, proposal.description, 
                 proposal.expected_improvement, proposal.risk, proposal.status)
            )
            conn.commit()
            logger.info("evolution_proposed", proposal_id=proposal.proposal_id, target=proposal.target)
        finally:
            conn.close()

    def _update_proposal_status(self, proposal_id: str, status: str):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE evolution_proposals SET status = ? WHERE proposal_id = ?", (status, proposal_id))
            conn.commit()
            logger.info("evolution_proposal_status_updated", proposal_id=proposal_id, status=status)
        finally:
            conn.close()
