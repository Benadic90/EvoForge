import shutil
from dataclasses import dataclass


@dataclass
class RuntimeInfo:
    available: bool
    runtime_type: str | None = None
    executable_path: str | None = None
    version: str | None = None
    reason_unavailable: str | None = None


class AntigravityRuntimeDetector:
    """Detects if a supported machine-callable Antigravity runtime exists."""

    @classmethod
    def detect(cls) -> RuntimeInfo:
        """
        Probes the environment for known Antigravity integration interfaces
        such as the 'agy' or 'antigravity' CLI commands.
        """
        agy_path = shutil.which("agy")
        if agy_path:
            return RuntimeInfo(
                available=True,
                runtime_type="CLI",
                executable_path=agy_path,
                reason_unavailable=None
            )
            
        ag_path = shutil.which("antigravity")
        if ag_path:
            return RuntimeInfo(
                available=True,
                runtime_type="CLI",
                executable_path=ag_path,
                reason_unavailable=None
            )
            
        return RuntimeInfo(
            available=False,
            runtime_type=None,
            executable_path=None,
            reason_unavailable="No supported machine-callable runtime (agy/antigravity) detected in PATH."
        )

    @classmethod
    def health_check(cls) -> bool:
        """Lightweight health check just verifying availability."""
        return cls.detect().available

    @classmethod
    def get_runtime_info(cls) -> RuntimeInfo:
        return cls.detect()
