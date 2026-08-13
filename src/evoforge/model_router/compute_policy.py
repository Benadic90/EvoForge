import json
from typing import Literal

from pydantic import BaseModel


class ComputePolicy(BaseModel):
    mode: Literal["LOCAL", "CLOUD", "HYBRID"] = "HYBRID"
    allow_local: bool = True
    allow_cloud: bool = True
    prefer_local: bool = False
    ollama_enabled: bool = True
    ollama_status: str | None = None  # Populated at runtime

    @classmethod
    def load_from_db(cls, db) -> "ComputePolicy":
        """Loads ComputePolicy from the database system_settings."""
        val = db.get_setting("compute_policy")
        if val:
            try:
                data = json.loads(val)
                return cls(**data)
            except Exception:
                pass
        return cls()

    def save_to_db(self, db) -> None:
        """Saves ComputePolicy to the database system_settings."""
        # don't save ephemeral fields like ollama_status
        data = self.model_dump(exclude={"ollama_status"})
        db.set_setting("compute_policy", json.dumps(data))
