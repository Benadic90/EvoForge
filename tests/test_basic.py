import os
import tempfile

from evoforge.memory.database import Database
from evoforge.utils.config import load_config


def test_config_defaults():
    config = load_config("nonexistent_path.yaml")
    assert config.global_settings.max_retries_per_task == 3
    assert config.database.sqlite_path == "data/evoforge.db"

def test_database_initialization():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(db_path)
        
        # Check if file exists
        assert os.path.exists(db_path)
        
        # Check if tables were created
        conn = db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}
            assert "workflows" in tables
            assert "tasks" in tables
            assert "metrics" in tables
        finally:
            conn.close()
