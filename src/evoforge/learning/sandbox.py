import os
import shutil
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from evoforge.evolution.experiment import ExperimentFramework, ExperimentResult
from evoforge.memory.obsidian import ObsidianManager

logger = structlog.get_logger(__name__)

class SandboxEnvironment:
    def __init__(self, base_path: str = "data/sandbox"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.active_sandboxes: dict[str, Path] = {}

    def create_sandbox(self, prefix: str = "exp") -> str:
        """Creates an isolated temporary directory for an experiment."""
        sandbox_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
        sandbox_path = self.base_path / "experiments" / sandbox_id
        sandbox_path.mkdir(parents=True, exist_ok=True)
        self.active_sandboxes[sandbox_id] = sandbox_path
        logger.info("sandbox_created", sandbox_id=sandbox_id, path=str(sandbox_path))
        return sandbox_id
        
    def get_path(self, sandbox_id: str) -> Path:
        if sandbox_id not in self.active_sandboxes:
            raise ValueError(f"Sandbox {sandbox_id} not found or not active.")
        return self.active_sandboxes[sandbox_id]

    def cleanup(self, sandbox_id: str):
        """Removes the sandbox directory."""
        if sandbox_id in self.active_sandboxes:
            path = self.active_sandboxes[sandbox_id]
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
            del self.active_sandboxes[sandbox_id]
            logger.info("sandbox_cleaned_up", sandbox_id=sandbox_id)

    def run_in_sandbox(self, sandbox_id: str, func: Callable, *args, **kwargs) -> Any:
        """Executes a function with the current working directory set to the sandbox."""
        path = self.get_path(sandbox_id)
        original_cwd = os.getcwd()
        try:
            os.chdir(path)
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("sandbox_execution_failed", sandbox_id=sandbox_id, error=str(e))
            raise
        finally:
            os.chdir(original_cwd)

class ExperimentRunner:
    def __init__(self, env: SandboxEnvironment, framework: ExperimentFramework, obsidian: ObsidianManager):
        self.env = env
        self.framework = framework
        self.obsidian = obsidian

    def run_experiment(self, name: str, input_data: Any, variant_a: Callable, variant_b: Callable, evaluator: Callable) -> ExperimentResult:
        """Runs an A/B experiment within a secure sandbox environment."""
        sandbox_id = self.env.create_sandbox(prefix=name)
        
        try:
            # Wrap variants to ensure they execute inside the sandbox
            def sandboxed_variant_a(data):
                return self.env.run_in_sandbox(sandbox_id, variant_a, data)
                
            def sandboxed_variant_b(data):
                return self.env.run_in_sandbox(sandbox_id, variant_b, data)
                
            experiment_id = f"exp_{name}_{uuid.uuid4().hex[:6]}"
            result = self.framework.run_ab_test(
                experiment_id=experiment_id,
                input_data=input_data,
                variant_a=sandboxed_variant_a,
                variant_b=sandboxed_variant_b,
                evaluator=evaluator
            )
            
            # Log result to Obsidian
            frontmatter = {
                "experiment_id": experiment_id,
                "name": name,
                "winner": result.variant,
                "success": result.success,
                "score": result.score,
                "duration_ms": result.duration_ms,
                "date": datetime.now().isoformat()
            }
            content = f"# Experiment: {name}\n\n**Winner**: {result.variant}\n**Score**: {result.score}\n\n"
            content += f"Metadata:\n```json\n{result.metadata}\n```\n"
            
            note_path = self.obsidian.folders["sandbox"] / "experiments" / f"{experiment_id}.md"
            self.obsidian._write_note(note_path, content, frontmatter)
            
            return result
        finally:
            self.env.cleanup(sandbox_id)
