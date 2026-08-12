import json
import uuid

import structlog
from pydantic import BaseModel

from evoforge.memory.database import Database
from evoforge.memory.obsidian import ObsidianManager

logger = structlog.get_logger(__name__)

class Skill(BaseModel):
    name: str
    version: int = 1
    confidence: float = 0.5
    capability_level: str = "beginner"
    techniques: list[str] = []
    tools: list[str] = []
    patterns: list[str] = []
    anti_patterns: list[str] = []
    last_verified: str | None = None
    freshness: str = "unknown"
    sources: list[str] = []

class SkillProfile(BaseModel):
    agent_name: str
    skills: list[Skill] = []
    
    def render_skills_context(self) -> str:
        if not self.skills:
            return ""
            
        context = "\n\n### Your Current Skills & Knowledge:\n"
        for skill in self.skills:
            context += f"- **{skill.name}** (v{skill.version}, {skill.capability_level})\n"
            if skill.patterns:
                context += f"  - Known patterns: {', '.join(skill.patterns[:3])}\n"
            if skill.anti_patterns:
                context += f"  - Anti-patterns to avoid: {', '.join(skill.anti_patterns[:3])}\n"
        context += "\n"
        return context

class SkillRegistry:
    def __init__(self, db: Database, obsidian: ObsidianManager):
        self.db = db
        self.obsidian = obsidian
        
    def _save_skill_to_db(self, agent_name: str, skill: Skill):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            metadata = {
                "techniques": skill.techniques,
                "tools": skill.tools,
                "patterns": skill.patterns,
                "anti_patterns": skill.anti_patterns,
                "sources": skill.sources
            }
            cursor.execute(
                """
                INSERT INTO skills 
                (id, agent_name, skill_name, version, confidence, capability_level, last_verified, freshness, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_name, skill_name, version) DO UPDATE SET
                confidence=excluded.confidence,
                capability_level=excluded.capability_level,
                last_verified=excluded.last_verified,
                freshness=excluded.freshness,
                metadata=excluded.metadata,
                updated_at=CURRENT_TIMESTAMP
                """,
                (
                    str(uuid.uuid4()), agent_name, skill.name, skill.version, 
                    skill.confidence, skill.capability_level, skill.last_verified, 
                    skill.freshness, json.dumps(metadata)
                )
            )
            conn.commit()
        finally:
            conn.close()

    def _save_skill_to_obsidian(self, agent_name: str, skill: Skill):
        frontmatter = {
            "version": skill.version,
            "confidence": skill.confidence,
            "capability_level": skill.capability_level,
            "last_verified": skill.last_verified,
            "freshness": skill.freshness
        }
        
        content = f"# {skill.name}\n\n"
        if skill.techniques:
            content += "## Techniques\n" + "".join([f"- {t}\n" for t in skill.techniques]) + "\n"
        if skill.tools:
            content += "## Supported Tools\n" + "".join([f"- {t}\n" for t in skill.tools]) + "\n"
        if skill.patterns:
            content += "## Successful Patterns\n" + "".join([f"- {p}\n" for p in skill.patterns]) + "\n"
        if skill.anti_patterns:
            content += "## Failed Approaches / Anti-Patterns\n" + "".join([f"- {a}\n" for a in skill.anti_patterns]) + "\n"
        if skill.sources:
            content += "## Sources\n" + "".join([f"- {s}\n" for s in skill.sources]) + "\n"
            
        self.obsidian.write_skill_note(agent_name, skill.name, content, frontmatter)

    def create_or_update_skill(self, agent_name: str, skill: Skill):
        """Registers a skill in the database and updates the Obsidian vault."""
        self._save_skill_to_db(agent_name, skill)
        self._save_skill_to_obsidian(agent_name, skill)
        logger.info("skill_updated", agent=agent_name, skill=skill.name, version=skill.version)
        
    def build_profile(self, agent_name: str) -> SkillProfile:
        """Retrieves all active skills for an agent and returns a complete profile."""
        conn = self.db.get_connection()
        skills = []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT skill_name, version, confidence, capability_level, last_verified, freshness, metadata
                FROM skills 
                WHERE agent_name = ? AND status = 'active'
                -- We only want the latest version of each active skill
                GROUP BY skill_name 
                HAVING version = MAX(version)
                """,
                (agent_name,)
            )
            for row in cursor.fetchall():
                meta = json.loads(row["metadata"]) if row["metadata"] else {}
                skills.append(Skill(
                    name=row["skill_name"],
                    version=row["version"],
                    confidence=row["confidence"],
                    capability_level=row["capability_level"],
                    last_verified=row["last_verified"],
                    freshness=row["freshness"],
                    techniques=meta.get("techniques", []),
                    tools=meta.get("tools", []),
                    patterns=meta.get("patterns", []),
                    anti_patterns=meta.get("anti_patterns", []),
                    sources=meta.get("sources", [])
                ))
        finally:
            conn.close()
            
        profile = SkillProfile(agent_name=agent_name, skills=skills)
        
        # Update obsidian profile summary
        self.obsidian.write_agent_profile(
            agent_name, 
            f"# {agent_name} Profile\n\nActive skills: {len(skills)}\n\n" + "".join([f"- [[{s.name}]] (v{s.version})\n" for s in skills]),
            {"agent": agent_name, "skills_count": len(skills)}
        )
        
        return profile
