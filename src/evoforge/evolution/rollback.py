import structlog
from datetime import UTC, datetime

from evoforge.memory.database import Database
from evoforge.learning.skill_versioner import SkillVersioner
from evoforge.learning.skill_registry import SkillRegistry
from evoforge.learning.models import EvolutionTarget

logger = structlog.get_logger(__name__)


class RollbackManager:
    """Handles controlled rollback of deployed evolutionary changes."""

    def __init__(self, db: Database, skill_registry: SkillRegistry):
        self.db = db
        self.skill_versioner = SkillVersioner(db, skill_registry)

    def rollback_proposal(self, proposal_id: str, reason: str = "Manual rollback triggered") -> bool:
        """Rolls back the deployment of a specific proposal."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT target_type, target_id, rollback_version FROM evolution_proposals WHERE proposal_id = ?",
                (proposal_id,)
            )
            row = cursor.fetchone()

            if not row:
                logger.error("rollback_failed", reason="Proposal not found", proposal_id=proposal_id)
                return False

            target_type = row["target_type"]
            target_id = row["target_id"]
            rollback_version = row["rollback_version"]

            if rollback_version is None:
                logger.error("rollback_failed", reason="No rollback version recorded", proposal_id=proposal_id)
                return False

            # Execute the rollback based on target type
            if target_type == "SKILL":
                agent_name, skill_name = target_id.split(":", 1)
                self.skill_versioner.rollback(agent_name, skill_name, int(rollback_version))
            elif target_type in ["PROMPT", "ROUTING_POLICY", "AGENT_CONFIG"]:
                # Stubbed logic for future configuration rollback implementations
                logger.warning("rollback_stubbed", target_type=target_type, target_id=target_id, rollback_version=rollback_version)
            else:
                logger.error("rollback_unsupported", target_type=target_type)
                return False

            now = datetime.now(UTC)

            # Update proposal status
            cursor.execute(
                """
                UPDATE evolution_proposals 
                SET status = 'ROLLED_BACK', rolled_back_at = ?
                WHERE proposal_id = ?
                """,
                (now, proposal_id)
            )

            # Update deployments
            cursor.execute(
                """
                UPDATE evolution_deployments
                SET status = 'ROLLED_BACK', rolled_back_at = ?, rollback_reason = ?
                WHERE proposal_id = ? AND status = 'ACTIVE'
                """,
                (now, reason, proposal_id)
            )

            conn.commit()
            logger.info("rollback_success", proposal_id=proposal_id, target_type=target_type, version=rollback_version)
            return True

        except Exception as e:
            logger.exception("rollback_error", error=str(e), proposal_id=proposal_id)
            return False
        finally:
            conn.close()
