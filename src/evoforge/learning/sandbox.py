import os
import shutil
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from evoforge.evolution.experiment import ExperimentFramework, ExperimentResult
from evoforge.learning.models import PracticePlan
from evoforge.memory.obsidian import ObsidianManager

logger = structlog.get_logger(__name__)

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

    def run_practice_plan(self, sandbox_id: str, plan: PracticePlan, func: Callable, *args, **kwargs) -> Any:
        """Executes a practice plan with the current working directory set to the sandbox."""
        path = self.get_path(sandbox_id)
        original_cwd = os.getcwd()
        start_time = time.time()
        
        max_duration = plan.budget.get("max_duration_seconds", 300)
        
        try:
            os.chdir(path)
            # A real implementation would run this in a thread or subprocess with a hard timeout.
            # For the local EvoForge architecture, we execute directly but simulate bounded time.
            result = func(*args, **kwargs)
            
            duration = time.time() - start_time
            if duration > max_duration:
                logger.warning("sandbox_execution_exceeded_budget", sandbox_id=sandbox_id, duration=duration, limit=max_duration)
            
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

    def run_experiment(self, name: str, input_data: Any, variant_a: Callable, variant_b: Callable, evaluator: Callable) -> ExperimentResult:
        """Runs an A/B experiment within a secure sandbox environment."""
        sandbox_id = self.env.create_sandbox(prefix=name)
        
        try:
            # We mock the plan here for A/B tests to use the run_practice_plan constraint
            plan = PracticePlan(
                practice_id=sandbox_id,
                agent_id="experiment",
                skill_id="test",
                objective=f"A/B Test {name}"
            )
            
            def sandboxed_variant_a(data):
                return self.env.run_practice_plan(sandbox_id, plan, variant_a, data)
                
            def sandboxed_variant_b(data):
                return self.env.run_practice_plan(sandbox_id, plan, variant_b, data)
                
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
                "date": datetime.now(UTC).isoformat()
            }
            content = f"# Experiment: {name}\n\n**Winner**: {result.variant}\n**Score**: {result.score}\n\n"
            content += f"Metadata:\n```json\n{result.metadata}\n```\n"
            
            note_path = self.obsidian.folders["sandbox"] / "experiments" / f"{experiment_id}.md"
            self.obsidian._write_note(note_path, content, frontmatter)
            
            return result
        finally:
            self.env.cleanup(sandbox_id)
