import uuid
import json
import structlog
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
from evoforge.memory.database import Database
from evoforge.memory.obsidian import ObsidianManager

logger = structlog.get_logger(__name__)

class EngineeringLesson(BaseModel):
    id: str
    agent_name: str
    problem: str
    evidence: str
    evidence_count: int
    learning: str
    status: str = "unverified"
    correction: Optional[str] = None

class LessonRecorder:
    def __init__(self, db: Database, obsidian: ObsidianManager):
        self.db = db
        self.obsidian = obsidian

    def record_outcome(self, agent_name: str, task_id: str, success: bool, details: Dict[str, Any]):
        """Records the outcome of a task execution."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            
            if not success:
                # Record in failures registry
                cursor.execute(
                    """
                    INSERT INTO failures 
                    (id, agent_name, task_id, task_description, context, attempted_solution, failure_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), agent_name, task_id, details.get("description", ""), 
                     json.dumps(details.get("context", {})), details.get("attempted_solution", ""), 
                     details.get("error_message", "Unknown error"))
                )
                
                # Check for patterns to auto-generate a lesson
                self._detect_patterns(cursor, agent_name, details.get("error_message", ""))
                
            conn.commit()
            logger.info("outcome_recorded", agent=agent_name, task_id=task_id, success=success)
        finally:
            conn.close()

    def _detect_patterns(self, cursor, agent_name: str, error_message: str):
        """Simple pattern detection: if similar error occurs multiple times, trigger a lesson."""
        # A real implementation would use LLM embedding similarity.
        # Here we just look for exact substring matches in recent failures.
        # Since this is MVP, we'll assume the EvolutionAgent handles the heavy lifting
        # when it analyzes failures, but we stub the DB integration here.
        pass

    def create_lesson(self, lesson: EngineeringLesson):
        """Creates a new engineering lesson in the database and Obsidian."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO lessons 
                (id, agent_name, problem, evidence, evidence_count, learning, correction, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (lesson.id, lesson.agent_name, lesson.problem, lesson.evidence, 
                 lesson.evidence_count, lesson.learning, lesson.correction, lesson.status)
            )
            conn.commit()
        finally:
            conn.close()
            
        self._write_lesson_to_obsidian(lesson)
        logger.info("lesson_created", id=lesson.id, agent=lesson.agent_name)

    def _write_lesson_to_obsidian(self, lesson: EngineeringLesson):
        frontmatter = {
            "id": lesson.id,
            "agent": lesson.agent_name,
            "status": lesson.status,
            "date": datetime.now().isoformat()
        }
        
        content = f"# Lesson: {lesson.id}\n\n"
        content += f"## Problem\n{lesson.problem}\n\n"
        content += f"## Evidence ({lesson.evidence_count} occurrences)\n{lesson.evidence}\n\n"
        content += f"## Learning\n{lesson.learning}\n\n"
        if lesson.correction:
            content += f"## Correction applied\n{lesson.correction}\n\n"
            
        note_path = self.obsidian.folders["agents"] / lesson.agent_name / "history" / f"Lesson_{lesson.id}.md"
        note_path.parent.mkdir(parents=True, exist_ok=True)
        self.obsidian._write_note(note_path, content, frontmatter)
