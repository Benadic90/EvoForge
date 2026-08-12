import json
import structlog
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from evoforge.memory.database import Database
from evoforge.learning.skill_registry import Skill, SkillRegistry

logger = structlog.get_logger(__name__)

class SkillVersion(BaseModel):
    version: int
    system_prompt_patch: str
    techniques: List[str]
    tools: List[str]
    patterns: List[str]
    anti_patterns: List[str]
    benchmark_score: float

class SkillVersioner:
    def __init__(self, db: Database, registry: SkillRegistry):
        self.db = db
        self.registry = registry

    def create_version(self, agent_name: str, skill: Skill, changes: Dict[str, Any], benchmark_score: float = 0.0) -> Skill:
        """Creates a new version of a skill with applied changes."""
        # 1. First ensure the base skill exists to get its internal ID
        # For simplicity, we query the DB to get the current skill's internal ID
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, version FROM skills WHERE agent_name = ? AND skill_name = ? ORDER BY version DESC LIMIT 1",
                (agent_name, skill.name)
            )
            row = cursor.fetchone()
            
            if not row:
                raise ValueError(f"Base skill {skill.name} not found for agent {agent_name}")
                
            skill_id = row["id"]
            current_version = row["version"]
            new_version = current_version + 1
            
            # Apply changes to create the new skill object
            new_skill = skill.copy(deep=True)
            new_skill.version = new_version
            if "techniques" in changes:
                new_skill.techniques.extend(changes["techniques"])
            if "patterns" in changes:
                new_skill.patterns.extend(changes["patterns"])
            if "anti_patterns" in changes:
                new_skill.anti_patterns.extend(changes["anti_patterns"])
                
            # Create snapshot of the NEW version
            cursor.execute(
                """
                INSERT INTO skill_versions 
                (skill_id, version, system_prompt_patch, techniques, tools, patterns, anti_patterns, benchmark_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    skill_id, new_version, changes.get("prompt_patch", ""), 
                    json.dumps(new_skill.techniques), json.dumps(new_skill.tools), 
                    json.dumps(new_skill.patterns), json.dumps(new_skill.anti_patterns), 
                    benchmark_score
                )
            )
            conn.commit()
            
            # Update the main registry
            self.registry.create_or_update_skill(agent_name, new_skill)
            
            logger.info("skill_version_created", agent=agent_name, skill=skill.name, version=new_version)
            return new_skill
            
        finally:
            conn.close()

    def get_history(self, agent_name: str, skill_name: str) -> List[SkillVersion]:
        """Retrieves the version history for a specific skill."""
        conn = self.db.get_connection()
        history = []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT sv.* FROM skill_versions sv
                JOIN skills s ON s.id = sv.skill_id
                WHERE s.agent_name = ? AND s.skill_name = ?
                ORDER BY sv.version DESC
                """,
                (agent_name, skill_name)
            )
            for row in cursor.fetchall():
                history.append(SkillVersion(
                    version=row["version"],
                    system_prompt_patch=row["system_prompt_patch"] or "",
                    techniques=json.loads(row["techniques"]) if row["techniques"] else [],
                    tools=json.loads(row["tools"]) if row["tools"] else [],
                    patterns=json.loads(row["patterns"]) if row["patterns"] else [],
                    anti_patterns=json.loads(row["anti_patterns"]) if row["anti_patterns"] else [],
                    benchmark_score=row["benchmark_score"] or 0.0
                ))
        finally:
            conn.close()
        return history

    def rollback(self, agent_name: str, skill_name: str, target_version: int):
        """Rolls back an agent's skill to a specific previous version."""
        history = self.get_history(agent_name, skill_name)
        target = next((v for v in history if v.version == target_version), None)
        
        if not target:
            raise ValueError(f"Version {target_version} not found in history for {skill_name}")
            
        # Reconstruct the skill and push to registry
        restored_skill = Skill(
            name=skill_name,
            version=target.version,
            techniques=target.techniques,
            tools=target.tools,
            patterns=target.patterns,
            anti_patterns=target.anti_patterns
        )
        
        self.registry.create_or_update_skill(agent_name, restored_skill)
        logger.info("skill_rolled_back", agent=agent_name, skill=skill_name, version=target_version)
