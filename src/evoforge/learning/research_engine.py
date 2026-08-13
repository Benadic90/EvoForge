import json
from datetime import UTC, datetime

import structlog

from evoforge.agents.advanced.research import ResearchAgent
from evoforge.learning.models import ResearchJob
from evoforge.memory.database import Database
from evoforge.memory.obsidian import ObsidianManager

logger = structlog.get_logger(__name__)

class ResearchScheduler:
    def __init__(self, db: Database):
        self.db = db
        
    def get_due_research(self, limit: int = 5) -> list[ResearchJob]:
        """Returns research jobs that are queued, ordered by priority."""
        conn = self.db.get_connection()
        jobs = []
        try:
            cursor = conn.cursor()
            # We select Queued jobs, highest priority first
            cursor.execute(
                """
                SELECT research_id, agent_id, project_id, task_id, domain, topic, query, reason, priority, status, created_at, started_at, completed_at, source_ids, confidence, findings, skill_gap_id
                FROM research_jobs 
                WHERE status = 'QUEUED' 
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
                """,
                (limit,)
            )
            for row in cursor.fetchall():
                try:
                    jobs.append(ResearchJob(**dict(row)))
                except Exception as e:
                    logger.warning("failed_to_parse_research_job", research_id=row["research_id"], error=str(e))
        finally:
            conn.close()
        return jobs
        
    def schedule_research(self, job: ResearchJob) -> str:
        """Schedules a research job with deduplication based on domain+topic."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Deduplication: check if identical topic is already QUEUED or RUNNING
            cursor.execute(
                "SELECT research_id FROM research_jobs WHERE domain = ? AND topic = ? AND status IN ('QUEUED', 'RUNNING')",
                (job.domain, job.topic)
            )
            existing = cursor.fetchone()
            if existing:
                logger.info("research_deduplicated", topic=job.topic)
                return existing["research_id"]
                
            cursor.execute(
                """
                INSERT INTO research_jobs (research_id, agent_id, project_id, task_id, domain, topic, query, reason, priority, status, skill_gap_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'QUEUED', ?)
                """,
                (job.research_id, job.agent_id, job.project_id, job.task_id, job.domain, job.topic, job.query, job.reason, job.priority, job.skill_gap_id)
            )
            conn.commit()
            logger.info("research_scheduled", topic=job.topic, agent=job.agent_id, priority=job.priority)
            return job.research_id
        finally:
            conn.close()

    def update_job_status(self, research_id: str, status: str, findings: str = None, source_ids: list[str] = None):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            update_sql = "UPDATE research_jobs SET status = ?"
            params = [status]
            
            if status == "RUNNING":
                update_sql += ", started_at = CURRENT_TIMESTAMP"
            elif status in ("COMPLETED", "FAILED", "CANCELLED"):
                update_sql += ", completed_at = CURRENT_TIMESTAMP"
                
            if findings is not None:
                update_sql += ", findings = ?"
                params.append(findings)
            if source_ids is not None:
                update_sql += ", source_ids = ?"
                params.append(json.dumps(source_ids))
                
            update_sql += " WHERE research_id = ?"
            params.append(research_id)
            
            cursor.execute(update_sql, tuple(params))
            conn.commit()
        finally:
            conn.close()

class ResearchEngine:
    def __init__(self, scheduler: ResearchScheduler, research_agent: ResearchAgent, obsidian: ObsidianManager):
        self.scheduler = scheduler
        self.agent = research_agent
        self.obsidian = obsidian
        
    def run_research(self, job: ResearchJob) -> ResearchJob:
        """Executes the research via the ResearchAgent."""
        logger.info("research_started", topic=job.topic)
        self.scheduler.update_job_status(job.research_id, "RUNNING")
        
        try:
            # We would extract sources by parsing JSON from the agent, but for MVP we assume it returns text.
            result_text = self.agent.research_topic(job.query)
            
            # Save to Obsidian Inbox
            frontmatter = {
                "agent": job.agent_id,
                "domain": job.domain,
                "date": datetime.now(UTC).isoformat(),
                "research_id": job.research_id,
                "skill_gap_id": job.skill_gap_id
            }
            safe_topic = job.topic.replace("/", "_").replace("\\", "_")
            self.obsidian._write_note(
                self.obsidian.folders["research"] / "inbox" / f"{safe_topic}.md",
                result_text,
                frontmatter
            )
            
            self.scheduler.update_job_status(job.research_id, "COMPLETED", findings=result_text, source_ids=[])
            job.findings = result_text
            job.status = "COMPLETED"
            return job
            
        except Exception as e:
            logger.error("research_failed", topic=job.topic, error=str(e))
            self.scheduler.update_job_status(job.research_id, "FAILED", findings=str(e))
            job.status = "FAILED"
            job.findings = str(e)
            return job
