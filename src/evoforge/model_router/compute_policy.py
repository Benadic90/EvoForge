import json
from typing import Literal

from pydantic import BaseModel, ValidationError, model_validator


class ComputePolicy(BaseModel):
    mode: Literal["LOCAL", "CLOUD", "HYBRID"] = "HYBRID"
    allow_local: bool = True
    allow_cloud: bool = True
    prefer_local: bool = False
    ollama_enabled: bool = True
    ollama_status: str | None = None  # Populated at runtime

    @model_validator(mode="after")
    def normalize_mode_flags(self) -> "ComputePolicy":
        """Keep legacy booleans consistent when clients send only `mode`."""
        if self.mode == "LOCAL":
            self.allow_local = True
            self.allow_cloud = False
            self.prefer_local = True
        elif self.mode == "CLOUD":
            self.allow_local = False
            self.allow_cloud = True
            self.prefer_local = False
        else:
            self.allow_local = True
            self.allow_cloud = True
        return self

    @classmethod
    def load_from_db(cls, db) -> "ComputePolicy":
        """Loads ComputePolicy from the database system_settings."""
        val = db.get_setting("compute_policy")
        if val:
            try:
                data = json.loads(val)
                return cls(**data)
            except (json.JSONDecodeError, TypeError, ValueError, ValidationError):
                return cls()
        return cls()

    def save_to_db(self, db) -> None:
        """Saves ComputePolicy to the database system_settings."""
        # don't save ephemeral fields like ollama_status
        data = self.model_dump(exclude={"ollama_status"})
        db.set_setting("compute_policy", json.dumps(data))
