
import structlog

from .database import Database

logger = structlog.get_logger(__name__)

class IdempotencyManager:
    def __init__(self, db: Database):
        self.db = db

    def check_operation(self, workflow_id: str, action: str, task_id: str | None = None) -> str | None:
        """Checks if an operation has already succeeded. Returns the result if it did."""
        # operation_key is unique across workflow_id, task_id, action
        op_key = f"{workflow_id}:{task_id or 'none'}:{action}"
        
        query = "SELECT status, result FROM workflow_operations WHERE operation_key = ?"
        rows = self.db.fetchall(query, (op_key,))
        if rows:
            if rows[0]["status"] == "SUCCESS":
                logger.info("idempotency_hit", operation_key=op_key)
                return rows[0]["result"]
        return None

    def record_operation(self, workflow_id: str, action: str, task_id: str | None = None, result: str = ""):
        """Records a successful operation to prevent duplicates."""
        op_key = f"{workflow_id}:{task_id or 'none'}:{action}"
        query = """
            INSERT INTO workflow_operations (operation_key, workflow_id, task_id, action, status, result)
            VALUES (?, ?, ?, ?, 'SUCCESS', ?)
            ON CONFLICT(operation_key) DO UPDATE SET status='SUCCESS', result=excluded.result
        """
        self.db.execute(query, (op_key, workflow_id, task_id, action, result))
        logger.debug("idempotency_recorded", operation_key=op_key)
