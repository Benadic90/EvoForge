import json
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from evoforge.memory.database import Database


class WorkerType(str, Enum):
    CLOUD = "CLOUD"
    LAPTOP = "LAPTOP"

class WorkerStatus(str, Enum):
    REGISTERING = "REGISTERING"
    IDLE = "IDLE"
    BUSY = "BUSY"
    DRAINING = "DRAINING"
    OFFLINE = "OFFLINE"
    UNHEALTHY = "UNHEALTHY"

class WorkerHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"

class WorkerProfile(BaseModel):
    worker_id: str
    worker_type: WorkerType
    status: WorkerStatus = WorkerStatus.REGISTERING
    capabilities: list[str] = Field(default_factory=list)
    compute_mode: str = "HYBRID"
    hostname: str = "unknown"
    version: str = "1.0.0"
    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_heartbeat_at: datetime | None = None
    last_seen_at: datetime | None = None
    current_workflow_id: str | None = None
    current_task_id: str | None = None
    health: WorkerHealth = WorkerHealth.UNKNOWN
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkerRegistry:
    def __init__(self, db: Database, heartbeat_timeout_seconds: int = 120):
        self.db = db
        self.heartbeat_timeout = heartbeat_timeout_seconds

    def register(self, profile: WorkerProfile) -> WorkerProfile:
        profile.registered_at = datetime.now(UTC)
        profile.last_seen_at = datetime.now(UTC)
        profile.last_heartbeat_at = datetime.now(UTC)

        query = """
        INSERT INTO workers (
            worker_id, worker_type, status, capabilities, compute_mode, 
            hostname, version, registered_at, last_heartbeat_at, last_seen_at, 
            current_workflow_id, current_task_id, health, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(worker_id) DO UPDATE SET
            status=excluded.status,
            capabilities=excluded.capabilities,
            compute_mode=excluded.compute_mode,
            hostname=excluded.hostname,
            version=excluded.version,
            registered_at=excluded.registered_at,
            last_heartbeat_at=excluded.last_heartbeat_at,
            last_seen_at=excluded.last_seen_at,
            health=excluded.health,
            metadata=excluded.metadata
        """
        self.db.execute(
            query,
            (
                profile.worker_id,
                profile.worker_type.value,
                profile.status.value,
                json.dumps(profile.capabilities),
                profile.compute_mode,
                profile.hostname,
                profile.version,
                profile.registered_at.isoformat(),
                profile.last_heartbeat_at.isoformat(),
                profile.last_seen_at.isoformat(),
                profile.current_workflow_id,
                profile.current_task_id,
                profile.health.value,
                json.dumps(profile.metadata),
            ),
        )
        return profile

    def heartbeat(
        self, 
        worker_id: str, 
        status: WorkerStatus | None = None, 
        health: WorkerHealth | None = None,
        current_workflow_id: str | None = None,
        current_task_id: str | None = None
    ) -> bool:
        now = datetime.now(UTC).isoformat()
        
        # Build update query dynamically
        fields = ["last_heartbeat_at = ?", "last_seen_at = ?"]
        params = [now, now]
        
        if status:
            fields.append("status = ?")
            params.append(status.value)
        if health:
            fields.append("health = ?")
            params.append(health.value)
        
        # We always update the workflow/task if provided in heartbeat to ensure sync
        fields.append("current_workflow_id = ?")
        params.append(current_workflow_id)
        fields.append("current_task_id = ?")
        params.append(current_task_id)

        params.append(worker_id)
        
        query = f"UPDATE workers SET {', '.join(fields)} WHERE worker_id = ?"
        self.db.execute(query, tuple(params))
        
        # Log to heartbeat history
        hb_query = """
        INSERT INTO worker_heartbeats (worker_id, timestamp, status, health, current_workflow_id)
        VALUES (?, ?, ?, ?, ?)
        """
        self.db.execute(hb_query, (
            worker_id, 
            now, 
            status.value if status else None, 
            health.value if health else None, 
            current_workflow_id
        ))

        return True

    def get(self, worker_id: str) -> WorkerProfile | None:
        rows = self.db.fetchall("SELECT * FROM workers WHERE worker_id = ?", (worker_id,))
        if not rows:
            return None
        return self._row_to_profile(rows[0])

    def list_all(self) -> list[WorkerProfile]:
        # Perform staleness check on read
        self._check_staleness()
        rows = self.db.fetchall("SELECT * FROM workers ORDER BY last_seen_at DESC")
        return [self._row_to_profile(r) for r in rows]
        
    def list_active(self) -> list[WorkerProfile]:
        self._check_staleness()
        rows = self.db.fetchall(
            "SELECT * FROM workers WHERE status IN ('IDLE', 'BUSY', 'REGISTERING') ORDER BY last_seen_at DESC"
        )
        return [self._row_to_profile(r) for r in rows]

    def mark_offline(self, worker_id: str):
        self.db.execute("UPDATE workers SET status = 'OFFLINE' WHERE worker_id = ?", (worker_id,))

    def drain(self, worker_id: str):
        self.db.execute("UPDATE workers SET status = 'DRAINING' WHERE worker_id = ?", (worker_id,))

    def remove(self, worker_id: str):
        self.db.execute("DELETE FROM workers WHERE worker_id = ?", (worker_id,))

    def _check_staleness(self):
        """Mark workers as OFFLINE if they missed their heartbeat window."""
        stale_threshold = (datetime.now(UTC) - timedelta(seconds=self.heartbeat_timeout)).isoformat()
        query = """
        UPDATE workers 
        SET status = 'OFFLINE' 
        WHERE last_heartbeat_at < ? 
        AND status NOT IN ('OFFLINE')
        """
        self.db.execute(query, (stale_threshold,))

    def _row_to_profile(self, row: dict) -> WorkerProfile:
        return WorkerProfile(
            worker_id=row["worker_id"],
            worker_type=WorkerType(row["worker_type"]),
            status=WorkerStatus(row["status"]),
            capabilities=json.loads(row["capabilities"]) if row["capabilities"] else [],
            compute_mode=row["compute_mode"] or "HYBRID",
            hostname=row["hostname"] or "unknown",
            version=row["version"] or "1.0.0",
            registered_at=datetime.fromisoformat(row["registered_at"]),
            last_heartbeat_at=datetime.fromisoformat(row["last_heartbeat_at"]) if row["last_heartbeat_at"] else None,
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]) if row["last_seen_at"] else None,
            current_workflow_id=row["current_workflow_id"],
            current_task_id=row["current_task_id"],
            health=WorkerHealth(row["health"]) if row["health"] else WorkerHealth.UNKNOWN,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )
