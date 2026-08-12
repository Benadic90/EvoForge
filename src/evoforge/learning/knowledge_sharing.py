import structlog
from typing import Dict, List, Set
from evoforge.memory.database import Database
from evoforge.learning.source_verifier import VerificationStatus

logger = structlog.get_logger(__name__)

class KnowledgeRegistry:
    def __init__(self, db: Database):
        self.db = db
        # Mapping of agent_name -> list of subscribed domains
        self.subscriptions: Dict[str, Set[str]] = {}

    def subscribe(self, agent_name: str, domains: List[str]):
        """Subscribes an agent to specific knowledge domains."""
        if agent_name not in self.subscriptions:
            self.subscriptions[agent_name] = set()
        self.subscriptions[agent_name].update(domains)
        logger.info("agent_subscribed", agent=agent_name, domains=domains)

    def publish(self, knowledge_id: str, source_agent: str):
        """Notifies the registry that a knowledge item has been validated by an agent."""
        logger.info("knowledge_published", knowledge_id=knowledge_id, source=source_agent)
        # Propagation happens asynchronously or on-demand
        pass

    def propagate(self):
        """Scans for VERIFIED knowledge and assigns it to subscribed agents."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            # Find all VERIFIED knowledge items
            cursor.execute(
                """
                SELECT id, title, domain, applicable_agents
                FROM knowledge_items
                WHERE verification_status = 'VERIFIED'
                """
            )
            
            for row in cursor.fetchall():
                domain = row["domain"]
                item_id = row["id"]
                
                import json
                applicable = json.loads(row["applicable_agents"]) if row["applicable_agents"] else []
                
                # Find subscribed agents for this domain
                for agent_name, domains in self.subscriptions.items():
                    if domain in domains and agent_name not in applicable:
                        applicable.append(agent_name)
                        logger.info("knowledge_propagated", item_id=item_id, agent=agent_name)
                        
                # Update applicable agents
                if applicable:
                    cursor.execute(
                        "UPDATE knowledge_items SET applicable_agents = ? WHERE id = ?",
                        (json.dumps(applicable), item_id)
                    )
            
            conn.commit()
        finally:
            conn.close()

    def get_shared_knowledge(self, agent_name: str) -> List[Dict]:
        """Retrieves all verified knowledge items applicable to the given agent."""
        conn = self.db.get_connection()
        results = []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, title, domain, content, source
                FROM knowledge_items
                WHERE verification_status = 'VERIFIED'
                AND applicable_agents LIKE ?
                """,
                (f"%{agent_name}%",)
            )
            for row in cursor.fetchall():
                results.append(dict(row))
        finally:
            conn.close()
        return results
