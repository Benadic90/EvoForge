import structlog
from typing import Any
from datetime import UTC, datetime

from evoforge.memory.database import Database
from evoforge.learning.models import EvolutionProposal, ApprovalPolicy, EvolutionStatus
from evoforge.evolution.experiment import ExperimentFramework, ExperimentRecord
from evoforge.policy_engine.validator import CandidateSecurityGate
from evoforge.evolution.rollback import RollbackManager

logger = structlog.get_logger(__name__)

class EvolutionPipeline:
    """Central orchestrator for the Controlled Self-Evolution loop."""

    def __init__(self, db: Database, experiment_framework: ExperimentFramework, rollback_manager: RollbackManager, policy: ApprovalPolicy):
        self.db = db
        self.experiment_framework = experiment_framework
        self.rollback_manager = rollback_manager
        self.policy = policy
        self.security_gate = CandidateSecurityGate()

    def evaluate_proposal(self, proposal: EvolutionProposal, dataset: str, input_data: list[Any], variant_a, variant_b, evaluator) -> ExperimentRecord:
        """Runs a proposal through the security gate and sandbox benchmark."""
        # 1. Security Check
        is_safe, reason = self.security_gate.validate_proposal(proposal.target_type, str(proposal.candidate_version))
        if not is_safe:
            logger.error("proposal_failed_security", proposal_id=proposal.proposal_id, reason=reason)
            self._update_status(proposal.proposal_id, "REJECTED")
            raise ValueError(f"Security Gate Failed: {reason}")

        self._update_status(proposal.proposal_id, "TESTING")

        # 2. Experiment / Benchmark
        record = self.experiment_framework.run_multi_metric_ab_test(
            experiment_id=f"eval_{proposal.proposal_id}",
            proposal_id=proposal.proposal_id,
            target=proposal.target_id,
            dataset=dataset,
            input_data=input_data,
            variant_a=variant_a,
            variant_b=variant_b,
            evaluator=evaluator
        )

        # 3. Policy Threshold
        if record.status == "PASSED":
            if self.policy.requires_human:
                self._update_status(proposal.proposal_id, "PASSED") # Needs human approval
                logger.info("proposal_passed_pending_approval", proposal_id=proposal.proposal_id)
            else:
                self._update_status(proposal.proposal_id, "APPROVED")
                logger.info("proposal_auto_approved", proposal_id=proposal.proposal_id)
        else:
            self._update_status(proposal.proposal_id, "FAILED")

        return record

    def deploy_candidate(self, proposal: EvolutionProposal, deployment_type: str = "FULL"):
        """Deploys an approved candidate to the requested mode (SHADOW, CANARY, FULL)."""
        if proposal.status not in ["APPROVED", "PASSED"]: # PASSED allowed for manual CLI override
            raise ValueError(f"Cannot deploy proposal in status {proposal.status}")

        now = datetime.now(UTC)
        deployment_id = f"dep_{proposal.proposal_id}_{now.strftime('%Y%m%d%H%M%S')}"

        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO evolution_deployments (deployment_id, proposal_id, deployed_version, rollback_version, deployment_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (deployment_id, proposal.proposal_id, str(proposal.candidate_version), str(proposal.current_version), deployment_type)
            )
            cursor.execute(
                "UPDATE evolution_proposals SET status = 'DEPLOYED', deployed_at = ? WHERE proposal_id = ?",
                (now, proposal.proposal_id)
            )
            conn.commit()
            logger.info("candidate_deployed", proposal_id=proposal.proposal_id, mode=deployment_type)
        finally:
            conn.close()

    def _update_status(self, proposal_id: str, status: EvolutionStatus):
        conn = self.db.get_connection()
        try:
            conn.execute("UPDATE evolution_proposals SET status = ? WHERE proposal_id = ?", (status, proposal_id))
            conn.commit()
        finally:
            conn.close()
