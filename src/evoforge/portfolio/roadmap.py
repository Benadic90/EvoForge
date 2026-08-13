import json
import uuid
from datetime import datetime

import structlog

from evoforge.memory.database import Database
from evoforge.memory.obsidian import ObsidianManager
from evoforge.portfolio.models import Milestone, ProjectRoadmap
from evoforge.portfolio.registry import ProjectRegistry

logger = structlog.get_logger(__name__)

class RoadmapSynchronizer:
    def __init__(self, db: Database, obsidian: ObsidianManager, registry: ProjectRegistry):
        self.db = db
        self.obsidian = obsidian
        self.registry = registry

    def sync_roadmap(self, project_id: str) -> ProjectRoadmap | None:
        """
        Syncs factual repository state with canonical planning state.
        This reads existing Obsidian memory and compares it against GitHub reality (mocked here
        as part of the DB fetch), then updates the canonical ProjectRoadmap without blindly
        overwriting Obsidian.
        """
        profile = self.registry.get(project_id)
        if not profile:
            logger.error("sync_roadmap_not_found", project_id=project_id)
            return None
            
        # 1. Fetch current canonical state from DB
        roadmap = self._get_db_roadmap(project_id)
        
        # 2. Read Obsidian projection (Project Vision & Memory)
        # Note: ObsidianManager expects note paths, usually `Projects/<name>.md`
        # For this boundary, we just extract vision if it exists.
        note_path = f"Projects/{profile.name}.md"
        obsidian_content = self.obsidian.read_note(note_path)
        
        vision = profile.vision or "Vision not defined."
        
        if not roadmap:
            roadmap = ProjectRoadmap(
                roadmap_id=f"rm_{uuid.uuid4().hex[:8]}",
                project_id=project_id,
                version="1.0",
                vision=vision,
                milestones=[],
                objectives=[],
                dependencies=[],
                status="DRAFT",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        # Update vision safely and check for drift
        if profile.vision:
            roadmap.vision = profile.vision
            
        # If the obsidian memory indicates a significant divergence, flag it for human review.
        if obsidian_content and len(obsidian_content) > 10:
            if roadmap.vision not in obsidian_content and profile.name in obsidian_content:
                logger.warning("roadmap_vision_drift", project_id=project_id)
                roadmap.status = "NEEDS_REVIEW"

        # 3. Synchronize Milestones (mocking GitHub state checking)
        for milestone in roadmap.milestones:
            if milestone.status not in ["COMPLETE", "STALE"]:
                # If we had real GitHub milestones mapped, we'd check their state here.
                # If all issues linked to evidence are closed -> COMPLETE
                pass
                
        # 4. Save back to canonical state
        self._save_db_roadmap(roadmap)
        
        # 5. We deliberately do NOT blindly write back to Obsidian here unless explicitly requested
        # to preserve human curation.
        
        logger.info("roadmap_synced", project_id=project_id, version=roadmap.version)
        return roadmap

    def _get_db_roadmap(self, project_id: str) -> ProjectRoadmap | None:
        query = "SELECT * FROM project_roadmaps WHERE project_id = ? ORDER BY updated_at DESC LIMIT 1"
        rows = self.db.fetchall(query, (project_id,))
        if not rows:
            return None
            
        row = rows[0]
        milestones_raw = json.loads(row["milestones"]) if row["milestones"] else []
        milestones = [Milestone(**m) for m in milestones_raw]
        
        return ProjectRoadmap(
            roadmap_id=row["roadmap_id"],
            project_id=row["project_id"],
            version=row["version"],
            vision=row["vision"],
            milestones=milestones,
            objectives=json.loads(row["objectives"]) if row["objectives"] else [],
            dependencies=json.loads(row["dependencies"]) if row["dependencies"] else [],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
        
    def _save_db_roadmap(self, roadmap: ProjectRoadmap) -> None:
        query = """
            INSERT INTO project_roadmaps (
                roadmap_id, project_id, version, vision, milestones,
                objectives, dependencies, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(roadmap_id) DO UPDATE SET
                version=excluded.version,
                vision=excluded.vision,
                milestones=excluded.milestones,
                objectives=excluded.objectives,
                dependencies=excluded.dependencies,
                status=excluded.status,
                updated_at=CURRENT_TIMESTAMP
        """
        params = (
            roadmap.roadmap_id,
            roadmap.project_id,
            roadmap.version,
            roadmap.vision,
            json.dumps([m.dict() for m in roadmap.milestones]),
            json.dumps(roadmap.objectives),
            json.dumps(roadmap.dependencies),
            roadmap.status,
            roadmap.created_at,
            datetime.utcnow()
        )
        self.db.execute(query, params)
