import json
import uuid

import structlog

from evoforge.agents.base import BaseAgent
from evoforge.agents.registry import ToolRegistry
from evoforge.learning.models import EvolutionProposal, Hypothesis
from evoforge.memory.database import Database
from evoforge.model_router.classifier import TaskComplexity, TaskType
from evoforge.model_router.router import ModelRouter

logger = structlog.get_logger(__name__)

class EvolutionAgent(BaseAgent):
    def __init__(self, model_router: ModelRouter, tools: ToolRegistry, db: Database):
        super().__init__(
            name="EvolutionAgent",
            role="Analyze system performance, analyze failing workflows, and propose safe, sandboxed improvements.",
            model_router=model_router,
            tools=tools
        )
        self.db = db
        
    def propose_skill_update(self, agent_id: str, skill_id: str, evidence_ids: list[str], context: str) -> EvolutionProposal:
        """Proposes changes to an agent's skill based on evidence, creating a strict EvolutionProposal."""
        task_prompt = f"Agent '{agent_id}' skill '{skill_id}' needs evolution. Evidence Context:\n{context}\n\nPropose a structured hypothesis."
        
        # Simulated LLM output generation
        result_desc = self.think_and_act(
            task_description=task_prompt,
            task_type=TaskType.REASONING,
            complexity=TaskComplexity.HIGH
        )
        
        hypothesis = Hypothesis(
            current_behavior="Failing on edge cases",
            observed_weakness="Does not handle exceptions well",
            proposed_change="Add robust error handling techniques",
            expected_improvement=">5% success rate",
            risk="LOW",
            benchmark="general_coding_benchmark",
            acceptance_threshold="5% improvement, 0 regressions"
        )
        
        proposal = EvolutionProposal(
            proposal_id=str(uuid.uuid4()),
            target_type="SKILL",
            target_id=f"{agent_id}:{skill_id}",
            description=result_desc[:200] + "...",
            hypothesis=hypothesis,
            evidence_ids=evidence_ids
        )
        
        self._save_proposal(proposal)
        return proposal

    def review_proposal(self, proposal: EvolutionProposal) -> bool:
        """Reviews an innovation proposal to ensure it's objectively sound before sandbox testing."""
        task_prompt = f"Review proposal for {proposal.target_id}:\n\n{proposal.description}\n\nIs this safe? Reply YES or NO."
        
        result = self.think_and_act(
            task_description=task_prompt,
            task_type=TaskType.REASONING,
            complexity=TaskComplexity.MEDIUM
        )
        approved = "YES" in result.upper()
        
        if approved:
            self._update_proposal_status(proposal.proposal_id, "QUEUED")
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
                (proposal_id, target_type, target_id, description, hypothesis_json, evidence_ids, risk, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (proposal.proposal_id, proposal.target_type, proposal.target_id, proposal.description, 
                 proposal.hypothesis.model_dump_json(), json.dumps(proposal.evidence_ids), proposal.hypothesis.risk, proposal.status)
            )
            conn.commit()
            logger.info("evolution_proposed", proposal_id=proposal.proposal_id, target_id=proposal.target_id)
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
