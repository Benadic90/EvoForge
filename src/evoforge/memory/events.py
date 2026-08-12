import json
import uuid
from datetime import datetime
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class EventRecord(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    run_id: str | None = None
    workflow_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    repository_id: str | None = None
    
    payload: dict[str, Any] = Field(default_factory=dict)


class EventStore:
    """Abstract storage interface for durable events."""
    def record(self, event: EventRecord) -> None:
        raise NotImplementedError
        
    def get_events(self, workflow_id: str) -> list[EventRecord]:
        raise NotImplementedError


class SQLiteEventStore(EventStore):
    """SQLite implementation of the event store."""
    def __init__(self, db_manager):
        # We assume db_manager is a Database instance from evoforge.memory.database
        self.db = db_manager
        self._ensure_table()
        
    def _ensure_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            run_id TEXT,
            workflow_id TEXT,
            task_id TEXT,
            agent_id TEXT,
            repository_id TEXT,
            payload TEXT NOT NULL
        )
        """
        self.db.execute(query)
        
    def record(self, event: EventRecord) -> None:
        query = """
        INSERT INTO events (
            event_id, event_type, timestamp, run_id, workflow_id, 
            task_id, agent_id, repository_id, payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(
            query, 
            (
                event.event_id,
                event.event_type,
                event.timestamp.isoformat(),
                event.run_id,
                event.workflow_id,
                event.task_id,
                event.agent_id,
                event.repository_id,
                json.dumps(event.payload)
            )
        )
        
    def get_events(self, workflow_id: str) -> list[EventRecord]:
        query = "SELECT * FROM events WHERE workflow_id = ? ORDER BY timestamp ASC"
        rows = self.db.fetchall(query, (workflow_id,))
        events = []
        for row in rows:
            events.append(EventRecord(
                event_id=row["event_id"],
                event_type=row["event_type"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                run_id=row["run_id"],
                workflow_id=row["workflow_id"],
                task_id=row["task_id"],
                agent_id=row["agent_id"],
                repository_id=row["repository_id"],
                payload=json.loads(row["payload"])
            ))
        return events


class EventEmitter:
    """Central event emitter for the system."""
    def __init__(self, store: EventStore | None = None):
        self.store = store
        self._handlers: dict[str, list[Any]] = {}

    def on(self, event_type: str, handler: Any) -> None:
        """Register an in-memory listener callback for an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def subscribe(self, event_type: str, handler: Any) -> None:
        """Alias for on()."""
        self.on(event_type, handler)

    def emit(
        self,
        event_type: str,
        run_id: str | None = None,
        workflow_id: str | None = None,
        task_id: str | None = None,
        agent_id: str | None = None,
        repository_id: str | None = None,
        **payload
    ) -> EventRecord:
        
        event = EventRecord(
            event_type=event_type,
            run_id=run_id,
            workflow_id=workflow_id,
            task_id=task_id,
            agent_id=agent_id,
            repository_id=repository_id,
            payload=payload
        )
        
        # Log to structlog (stdout/file)
        logger.info(
            event_type,
            event_id=event.event_id,
            run_id=run_id,
            workflow_id=workflow_id,
            task_id=task_id,
            agent_id=agent_id,
            repository_id=repository_id,
            **payload
        )
        
        # Persist to store if configured
        if self.store:
            self.store.record(event)

        # Notify in-memory listeners
        for handler in self._handlers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.warning("event_handler_failed", event_type=event_type, error=str(e))
            
        return event

# Global emitter instance that can be configured with a store at startup
emitter = EventEmitter()

