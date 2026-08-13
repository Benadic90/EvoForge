import uuid

import structlog

from evoforge.learning.models import SkillGap
from evoforge.memory.database import Database

logger = structlog.get_logger(__name__)

class SkillGapDetector:
    def __init__(self, db: Database):
        self.db = db

    def analyze_recent_failures(self, agent_id: str, threshold: int = 3) -> list[SkillGap]:
        """
        Analyzes recent execution telemetry and failures. 
        If an agent repeatedly fails a specific task type, it generates a SkillGap.
        """
        conn = self.db.get_connection()
        gaps = []
        try:
            cursor = conn.cursor()
            # Find task types where recent failures exceed threshold
            # and no active skill gap currently exists
            cursor.execute(
                """
                SELECT task_type, COUNT(*) as failure_count, GROUP_CONCAT(task_id) as evidence
                FROM (
                    SELECT task_type, task_id 
                    FROM execution_telemetry 
                    WHERE executor_id = ? AND success = 0 
                    ORDER BY created_at DESC 
                    LIMIT 20
                )
                GROUP BY task_type
                HAVING failure_count >= ?
                """,
                (agent_id, threshold)
            )
            rows = cursor.fetchall()
            
            for row in rows:
                task_type = row["task_type"]
                # Heuristic: the skill_id is often heavily correlated with task_type
                skill_id = task_type if task_type else "general"
                
                # Check if a gap is already open for this skill
                cursor.execute(
                    "SELECT 1 FROM skill_gaps WHERE agent_id = ? AND skill_id = ? AND status IN ('OPEN', 'IN_PRACTICE')",
                    (agent_id, skill_id)
                )
                if cursor.fetchone():
                    continue # Gap already exists
                    
                gap = SkillGap(
                    skill_gap_id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    skill_id=skill_id,
                    severity="HIGH" if row["failure_count"] >= 5 else "MEDIUM",
                    confidence=0.8,
                    evidence_ids=row["evidence"].split(",") if row["evidence"] else []
                )
                
                # Persist gap
                cursor.execute(
                    """
                    INSERT INTO skill_gaps (skill_gap_id, agent_id, skill_id, severity, confidence, evidence_ids, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
                    """,
                    (gap.skill_gap_id, gap.agent_id, gap.skill_id, gap.severity, gap.confidence, row["evidence"])
                )
                conn.commit()
                gaps.append(gap)
                logger.info("skill_gap_detected", agent=agent_id, skill=skill_id, count=row["failure_count"])
                
        finally:
            conn.close()
            
        return gaps
