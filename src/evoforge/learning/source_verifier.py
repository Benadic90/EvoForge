import json
from enum import Enum

import structlog

from evoforge.learning.models import KnowledgeItem, KnowledgeVerificationStatus
from evoforge.memory.database import Database
from evoforge.memory.obsidian import ObsidianManager

logger = structlog.get_logger(__name__)

class SourceType(Enum):
    OFFICIAL_DOCS = "OFFICIAL_DOCS"
    RESEARCH_PAPER = "RESEARCH_PAPER"
    STANDARD = "STANDARD"
    OFFICIAL_REPO = "OFFICIAL_REPO"
    TECHNICAL_PUBLICATION = "TECHNICAL_PUBLICATION"
    ENGINEERING_BLOG = "ENGINEERING_BLOG"
    COMMUNITY_DISCUSSION = "COMMUNITY_DISCUSSION"
    UNKNOWN = "UNKNOWN"

class SourceEvaluator:
    def __init__(self):
        # Base confidence scores based on source type hierarchy
        self.type_confidence = {
            SourceType.OFFICIAL_DOCS: 0.95,
            SourceType.RESEARCH_PAPER: 0.90,
            SourceType.STANDARD: 0.95,
            SourceType.OFFICIAL_REPO: 0.85,
            SourceType.TECHNICAL_PUBLICATION: 0.70,
            SourceType.ENGINEERING_BLOG: 0.60,
            SourceType.COMMUNITY_DISCUSSION: 0.40,
            SourceType.UNKNOWN: 0.20
        }

    def evaluate_source(self, url: str, content: str) -> SourceType:
        """Heuristic evaluation of source type from URL and content."""
        if not url:
            return SourceType.UNKNOWN
        url_lower = url.lower()
        if "docs." in url_lower or "/docs" in url_lower:
            return SourceType.OFFICIAL_DOCS
        if "github.com/" in url_lower and "/tree/master/docs" not in url_lower:
            return SourceType.OFFICIAL_REPO
        if "arxiv.org" in url_lower or "research" in url_lower:
            return SourceType.RESEARCH_PAPER
        if "stackoverflow.com" in url_lower or "reddit.com" in url_lower:
            return SourceType.COMMUNITY_DISCUSSION
        if "blog." in url_lower or "medium.com" in url_lower or "dev.to" in url_lower:
            return SourceType.ENGINEERING_BLOG
        return SourceType.UNKNOWN

    def calculate_confidence(self, source_type: SourceType, corroborating_sources: int = 0) -> float:
        """Calculates final confidence score. Corroborating sources add a small boost."""
        base = self.type_confidence.get(source_type, 0.2)
        boost = min(corroborating_sources * 0.05, 0.15) # Max 15% boost from corroboration
        return min(base + boost, 1.0)

class KnowledgeVerifier:
    def __init__(self, db: Database, obsidian: ObsidianManager):
        self.db = db
        self.obsidian = obsidian
        self.evaluator = SourceEvaluator()

    def ingest_knowledge(self, item: KnowledgeItem) -> str:
        """Ingests raw knowledge item as UNVERIFIED."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            
            # Detect contradiction (same topic, domain, but differing summary/evidence could be handled by a more advanced embedding similarity, 
            # but for MVP we flag it if there are conflicting confidence items or just rely on manual tagging)
            
            cursor.execute(
                """
                INSERT INTO knowledge_items 
                (knowledge_id, topic, domain, summary, source_ids, confidence, verification_status, tags, related_skills, related_projects, evidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (item.knowledge_id, item.topic, item.domain, item.summary, 
                 json.dumps(item.source_ids), item.confidence, item.verification_status, 
                 json.dumps(item.tags), json.dumps(item.related_skills), json.dumps(item.related_projects), item.evidence)
            )
            conn.commit()
            logger.info("knowledge_ingested", knowledge_id=item.knowledge_id, topic=item.topic)
        finally:
            conn.close()
        return item.knowledge_id

    def detect_contradiction(self, topic: str, domain: str) -> bool:
        """Simple contradiction detection based on differing active VERIFIED knowledge items on the same exact topic."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(knowledge_id) as count FROM knowledge_items WHERE topic = ? AND domain = ? AND verification_status IN ('VERIFIED', 'LIKELY_VALID')",
                (topic, domain)
            )
            row = cursor.fetchone()
            if row and row["count"] > 1:
                return True
            return False
        finally:
            conn.close()

    def verify_knowledge_item(self, knowledge_id: str, source_urls: list[str]) -> KnowledgeVerificationStatus:
        """Verifies an ingested item based on source reliability."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_items WHERE knowledge_id = ?", (knowledge_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Knowledge item {knowledge_id} not found.")

            # Evaluate the best source
            best_type = SourceType.UNKNOWN
            for url in source_urls:
                st = self.evaluator.evaluate_source(url, "")
                if self.evaluator.type_confidence.get(st, 0) > self.evaluator.type_confidence.get(best_type, 0):
                    best_type = st
            
            corroborating = max(0, len(source_urls) - 1)
            confidence = self.evaluator.calculate_confidence(best_type, corroborating)
            
            topic = row["topic"]
            domain = row["domain"]
            
            if self.detect_contradiction(topic, domain):
                status = "CONFLICTED"
            elif confidence >= 0.85:
                status = "VERIFIED"
            elif confidence >= 0.60:
                status = "LIKELY_VALID"
            elif confidence >= 0.40:
                status = "LOW_CONFIDENCE"
            else:
                status = "REJECTED"

            # Update DB
            cursor.execute(
                """
                UPDATE knowledge_items 
                SET confidence = ?, verification_status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE knowledge_id = ?
                """,
                (confidence, status, knowledge_id)
            )
            conn.commit()
            
            # Write to Obsidian Knowledge Base
            frontmatter = {
                "knowledge_id": knowledge_id,
                "domain": domain,
                "confidence": confidence,
                "status": status,
                "best_source_type": best_type.value
            }
            
            safe_title = topic.replace("/", "_").replace("\\", "_")
            note_path = self.obsidian.folders["knowledge"] / status.lower() / f"{safe_title}.md"
            self.obsidian._write_note(note_path, row["summary"], frontmatter)
            
            logger.info("knowledge_verified", knowledge_id=knowledge_id, status=status, confidence=confidence)
            return status
        finally:
            conn.close()
