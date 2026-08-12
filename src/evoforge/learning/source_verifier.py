import structlog
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime
import uuid
import json
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

class VerificationStatus(Enum):
    KNOWN = "KNOWN"
    VERIFIED = "VERIFIED"
    EXPERIMENTAL = "EXPERIMENTAL"
    UNVERIFIED = "UNVERIFIED"
    REJECTED = "REJECTED"
    DEPRECATED = "DEPRECATED"

class KnowledgeItem(BaseModel):
    title: str
    domain: str
    content: str
    source: str
    source_type: SourceType
    source_url: str
    publication_date: Optional[str] = None
    applicable_agents: List[str] = []
    
class VerificationResult(BaseModel):
    item_id: str
    status: VerificationStatus
    confidence: float
    reasoning: str

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
        item_id = str(uuid.uuid4())
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge_items 
                (id, title, domain, content, source, source_type, source_url, publication_date, 
                 verification_status, lifecycle_state, applicable_agents)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'UNVERIFIED', 'discovered', ?)
                """,
                (item_id, item.title, item.domain, item.content, item.source, 
                 item.source_type.value, item.source_url, item.publication_date, 
                 json.dumps(item.applicable_agents))
            )
            conn.commit()
            logger.info("knowledge_ingested", id=item_id, title=item.title)
        finally:
            conn.close()
        return item_id

    def verify_knowledge_item(self, item_id: str, corroborating_sources: int = 0) -> VerificationResult:
        """Verifies an ingested item based on source reliability."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Knowledge item {item_id} not found.")

            source_type = SourceType(row["source_type"])
            confidence = self.evaluator.calculate_confidence(source_type, corroborating_sources)
            
            # Determine status based on confidence thresholds
            if confidence >= 0.85:
                status = VerificationStatus.VERIFIED
                lifecycle = 'verified'
                reasoning = "High confidence source type with sufficient corroboration."
            elif confidence >= 0.60:
                status = VerificationStatus.EXPERIMENTAL
                lifecycle = 'experimental'
                reasoning = "Moderate confidence. Requires sandbox experimentation."
            else:
                status = VerificationStatus.REJECTED
                lifecycle = 'rejected'
                reasoning = "Low confidence source type. Rejected for safety."

            # Update DB
            cursor.execute(
                """
                UPDATE knowledge_items 
                SET confidence = ?, verification_status = ?, lifecycle_state = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (confidence, status.value, lifecycle, item_id)
            )
            conn.commit()
            
            # Write to Obsidian Knowledge Base
            frontmatter = {
                "id": item_id,
                "domain": row["domain"],
                "source": row["source"],
                "source_type": source_type.value,
                "confidence": confidence,
                "status": status.value
            }
            
            safe_title = row["title"].replace("/", "_").replace("\\", "_")
            note_path = self.obsidian.folders["knowledge"] / lifecycle / f"{safe_title}.md"
            self.obsidian._write_note(note_path, row["content"], frontmatter)
            
            logger.info("knowledge_verified", id=item_id, status=status.value, confidence=confidence)
            return VerificationResult(item_id=item_id, status=status, confidence=confidence, reasoning=reasoning)
        finally:
            conn.close()
