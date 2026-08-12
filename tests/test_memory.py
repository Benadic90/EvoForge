import os
import tempfile

from evoforge.memory.database import Database
from evoforge.memory.manager import MemoryManager
from evoforge.memory.obsidian import ObsidianManager


def test_obsidian_manager_init():
    with tempfile.TemporaryDirectory() as temp_dir:
        vault_path = os.path.join(temp_dir, "vault")
        obsidian = ObsidianManager(vault_path)
        obsidian.init_vault()
        
        # Check if folders created
        assert os.path.exists(os.path.join(vault_path, "Projects"))
        assert os.path.exists(os.path.join(vault_path, "Daily"))
        assert os.path.exists(os.path.join(vault_path, "EvoForge Index.md"))

def test_memory_manager_integration():
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        vault_path = os.path.join(temp_dir, "vault")
        
        db = Database(db_path)
        obsidian = ObsidianManager(vault_path)
        manager = MemoryManager(db, obsidian)
        
        manager.init_memory_systems()
        
        # Test project registration
        manager.register_project("user/my-repo", "https://github.com/user/my-repo", "python")
        
        project_note_path = os.path.join(vault_path, "Projects", "user_my-repo.md")
        assert os.path.exists(project_note_path)
        
        # Test daily summary logging
        manager.log_daily_summary("## Today\nDid some work.")
        daily_notes = os.listdir(os.path.join(vault_path, "Daily"))
        assert len(daily_notes) == 1
        
        # We don't have a test for SQLite workflows here as it requires schema updates. 
        # MVP MemoryManager checkpointing tests can be added later when workflows schema is built.
