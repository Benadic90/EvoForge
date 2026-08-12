import structlog
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from evoforge.memory.database import Database
from evoforge.memory.obsidian import ObsidianManager
from evoforge.agents.advanced.research import ResearchAgent

logger = structlog.get_logger(__name__)

class ResearchTopic(BaseModel):
    agent_name: str
    topic: str
    domain: str
    volatility: str = "medium"
    trigger: str = "scheduled"
    
class ResearchResult(BaseModel):
    topic: ResearchTopic
    findings: str
    sources: List[str]
    success: bool

class ResearchScheduler:
    def __init__(self, db: Database):
        self.db = db
        
    def get_due_research(self) -> List[ResearchTopic]:
        """Returns research topics that are scheduled and pending."""
        conn = self.db.get_connection()
        topics = []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT agent_name, topic, domain, volatility, trigger 
                FROM research_items 
                WHERE status = 'pending' AND scheduled_at <= CURRENT_TIMESTAMP
                """
            )
            for row in cursor.fetchall():
                topics.append(ResearchTopic(
                    agent_name=row["agent_name"],
                    topic=row["topic"],
                    domain=row["domain"],
                    volatility=row["volatility"],
                    trigger=row["trigger"]
                ))
        finally:
            conn.close()
        return topics
        
    def schedule_research(self, topic: ResearchTopic, delay_hours: int = 0):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            scheduled_at = (datetime.now() + timedelta(hours=delay_hours)).isoformat()
            cursor.execute(
                """
                INSERT INTO research_items (id, agent_name, topic, domain, volatility, trigger, status, scheduled_at)
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                """,
                (str(uuid.uuid4()), topic.agent_name, topic.topic, topic.domain, topic.volatility, topic.trigger, scheduled_at)
            )
            conn.commit()
            logger.info("research_scheduled", topic=topic.topic, agent=topic.agent_name)
        finally:
            conn.close()

    def mark_completed(self, topic: str, findings: str, sources: List[str]):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE research_items 
                SET status = 'completed', findings = ?, sources = ?, completed_at = CURRENT_TIMESTAMP
                WHERE topic = ? AND status = 'pending'
                """,
                (findings, json.dumps(sources), topic)
            )
            conn.commit()
        finally:
            conn.close()

class ResearchEngine:
    def __init__(self, scheduler: ResearchScheduler, research_agent: ResearchAgent, obsidian: ObsidianManager):
        self.scheduler = scheduler
        self.agent = research_agent
        self.obsidian = obsidian
        
    def run_research(self, topic: ResearchTopic) -> ResearchResult:
        """Executes the research via the ResearchAgent."""
        logger.info("research_started", topic=topic.topic)
        
        try:
            # We would extract sources by parsing JSON from the agent, but for MVP we assume it returns text.
            result_text = self.agent.research_topic(topic.topic)
            
            # Save to Obsidian Inbox
            frontmatter = {
                "agent": topic.agent_name,
                "domain": topic.domain,
                "date": datetime.now().isoformat()
            }
            safe_topic = topic.topic.replace("/", "_").replace("\\", "_")
            self.obsidian._write_note(
                self.obsidian.folders["research"] / "inbox" / f"{safe_topic}.md",
                result_text,
                frontmatter
            )
            
            self.scheduler.mark_completed(topic.topic, result_text, [])
            return ResearchResult(topic=topic, findings=result_text, sources=[], success=True)
            
        except Exception as e:
            logger.error("research_failed", topic=topic.topic, error=str(e))
            return ResearchResult(topic=topic, findings=str(e), sources=[], success=False)
