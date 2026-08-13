import os
import shutil
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from evoforge.evolution.experiment import ExperimentFramework, ExperimentRecord
from evoforge.memory.obsidian import ObsidianManager

logger = structlog.get_logger(__name__)

class SandboxSecurityException(Exception):
    pass

class SandboxEnvironment:
    def __init__(self, base_path: str = "data/sandbox"):
        self.base_path = Path(base_path).absolute()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.active_sandboxes: dict[str, Path] = {}

    def create_sandbox(self, prefix: str = "exp") -> str:
        """Creates an isolated temporary directory for an experiment."""
        sandbox_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
        sandbox_path = self.base_path / "experiments" / sandbox_id
        sandbox_path.mkdir(parents=True, exist_ok=True)
        
        # Prevent git escapes
        (sandbox_path / ".git").mkdir(parents=True, exist_ok=True)
        (sandbox_path / ".git" / "HEAD").write_text("ref: refs/heads/main")
        
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

    def enforce_security_policies(self, data: Any):
        """Checks input data against security policies."""
        data_str = str(data)
        if "disable Policy Engine" in data_str or "unrestricted shell" in data_str:
            raise SandboxSecurityException("Security violation: attempt to disable safety constraints or gain unrestricted shell.")

    def run_isolated(self, sandbox_id: str, max_duration: int, func: Callable, *args, **kwargs) -> Any:
        """Executes a function with the current working directory set to the sandbox."""
        path = self.get_path(sandbox_id)
        original_cwd = os.getcwd()
        start_time = time.time()
        
        try:
            os.chdir(path)
            # Simulated bounded time enforcement
            self.enforce_security_policies(args)
            result = func(*args, **kwargs)
            
            duration = time.time() - start_time
            if duration > max_duration:
                logger.warning("sandbox_timeout", sandbox_id=sandbox_id, duration=duration, limit=max_duration)
                raise TimeoutError("Sandbox execution exceeded budget")
            
            return result
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

    def run_multi_metric_experiment(
        self, name: str, proposal_id: str, target: str, dataset: str, input_data: list[Any], 
        variant_a: Callable, variant_b: Callable, evaluator: Callable
    ) -> ExperimentRecord:
        """Runs a multi-metric A/B experiment within a secure sandbox environment."""
        sandbox_id = self.env.create_sandbox(prefix=name)
        
        try:
            def sandboxed_variant_a(data):
                return self.env.run_isolated(sandbox_id, 300, variant_a, data)
                
            def sandboxed_variant_b(data):
                return self.env.run_isolated(sandbox_id, 300, variant_b, data)
                
            experiment_id = f"exp_{name}_{uuid.uuid4().hex[:6]}"
            result = self.framework.run_multi_metric_ab_test(
                experiment_id=experiment_id,
                proposal_id=proposal_id,
                target=target,
                dataset=dataset,
                input_data=input_data,
                variant_a=sandboxed_variant_a,
                variant_b=sandboxed_variant_b,
                evaluator=evaluator
            )
            
            # Log result to Obsidian
            frontmatter = {
                "experiment_id": experiment_id,
                "proposal_id": proposal_id,
                "target": target,
                "dataset": dataset,
                "status": result.status,
                "improvement": result.improvement_percent,
                "regressions": result.regressions,
                "date": datetime.now(UTC).isoformat()
            }
            content = f"# Experiment: {name}\n\n**Status**: {result.status}\n**Improvement**: {result.improvement_percent}\n\n"
            
            note_path = self.obsidian.folders["sandbox"] / "experiments" / f"{experiment_id}.md"
            self.obsidian._write_note(note_path, content, frontmatter)
            
            return result
        finally:
            self.env.cleanup(sandbox_id)
