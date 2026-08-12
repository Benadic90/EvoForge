from typing import Any

import structlog

from evoforge.memory.database import Database

logger = structlog.get_logger(__name__)

class PerformanceMonitor:
    def __init__(self, db: Database):
        self.db = db
        
    def record_metric(self, name: str, value: float, metadata: dict[str, Any] = None):
        """Records a performance metric into the SQLite metrics table."""
        try:
            conn = self.db.get_connection()
            try:
                import json
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO metrics (metric_name, metric_value, tags) VALUES (?, ?, ?)",
                    (name, value, json.dumps(metadata) if metadata else "{}")
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            logger.error("metric_recording_failed", name=name, error=str(e))
            
    def get_baseline(self, name: str, window_days: int = 7) -> float:
        """Calculates the average baseline for a metric over a time window."""
        try:
            conn = self.db.get_connection()
            try:
                cursor = conn.cursor()
                # Basic SQLite date math
                cursor.execute(
                    "SELECT AVG(metric_value) FROM metrics WHERE metric_name = ? AND recorded_at >= datetime('now', ?)",
                    (name, f'-{window_days} days')
                )
                row = cursor.fetchone()
                return row[0] if row and row[0] is not None else 0.0
            finally:
                conn.close()
        except Exception as e:
            logger.error("baseline_calculation_failed", name=name, error=str(e))
            return 0.0
