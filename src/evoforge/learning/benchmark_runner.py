import json
import uuid
from collections.abc import Callable
from typing import Any

import structlog

from evoforge.learning.models import BenchmarkResult
from evoforge.memory.database import Database
from evoforge.memory.obsidian import ObsidianManager

logger = structlog.get_logger(__name__)

class BenchmarkTask:
    def __init__(self, id: str, description: str, evaluator: Callable[[Any], float]):
        self.id = id
        self.description = description
        self.evaluator = evaluator

class BenchmarkSuite:
    def __init__(self, name: str, agent_id: str, skill_id: str, environment: str, baseline_score: float = 0.0):
        self.name = name
        self.agent_id = agent_id
        self.skill_id = skill_id
        self.environment = environment
        self.baseline_score = baseline_score
        self.tasks: list[BenchmarkTask] = []
        
    def add_task(self, task: BenchmarkTask):
        self.tasks.append(task)

class BenchmarkRunner:
    def __init__(self, db: Database, obsidian: ObsidianManager):
        self.db = db
        self.obsidian = obsidian
        
    def run_suite(self, suite: BenchmarkSuite, agent_callable: Callable[[str], Any]) -> BenchmarkResult:
        """
        Runs the benchmark suite by passing each task description to the agent_callable.
        The agent_callable should be a function representing the agent's capability (e.g., in a sandbox).
        """
        logger.info("benchmark_started", suite=suite.name, agent=suite.agent_id, tasks=len(suite.tasks))
        
        total_score = 0.0
        details = {}
        
        for task in suite.tasks:
            try:
                # Execute the agent behavior inside the sandbox wrapper
                result = agent_callable(task.description)
                score = task.evaluator(result)
                
                # Cap score
                score = max(0.0, min(1.0, float(score)))
                
                total_score += score
                details[task.id] = {"score": score, "result": str(result)[:500]}
                
            except Exception as e:
                logger.error("benchmark_task_failed", task=task.id, error=str(e))
                details[task.id] = {"score": 0.0, "error": str(e)}

        max_possible = len(suite.tasks)
        final_score = (total_score / max_possible) if max_possible > 0 else 0.0
        
        # We record the candidate score against the baseline
        result_obj = BenchmarkResult(
            benchmark_id=str(uuid.uuid4()),
            agent_id=suite.agent_id,
            skill_id=suite.skill_id,
            environment=suite.environment,
            baseline_score=suite.baseline_score,
            candidate_score=final_score,
            sample_count=len(suite.tasks),
            evidence=json.dumps(details)
        )
        
        self._record_result(result_obj)
        return result_obj

    def _record_result(self, result: BenchmarkResult):
        """Records the benchmark result to SQLite and Obsidian."""
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO benchmarks 
                (benchmark_id, agent_id, skill_id, environment, baseline_score, candidate_score, sample_count, evidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (result.benchmark_id, result.agent_id, result.skill_id, result.environment, 
                 result.baseline_score, result.candidate_score, result.sample_count, result.evidence)
            )
            conn.commit()
        finally:
            conn.close()
            
        # Write to Obsidian
        improvement = result.candidate_score - result.baseline_score
        success = result.candidate_score >= result.baseline_score
        
        frontmatter = {
            "benchmark_id": result.benchmark_id,
            "agent": result.agent_id,
            "skill": result.skill_id,
            "environment": result.environment,
            "score": result.candidate_score,
            "improvement": improvement,
            "success": success,
            "date": result.timestamp.isoformat()
        }
        
        content = f"# Benchmark: {result.skill_id} ({result.agent_id})\n\n"
        content += f"**Final Score**: {result.candidate_score:.2f} (Improvement: {improvement:+.2f})\n"
        content += f"**Status**: {'✅ PASS' if success else '❌ FAIL (Regression)'}\n\n"
        content += "## Evidence\n```json\n" + result.evidence + "\n```\n"
        
        file_name = f"{result.agent_id}_{result.skill_id}_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        note_path = self.obsidian.folders["sandbox"] / "benchmarks" / file_name
        self.obsidian._write_note(note_path, content, frontmatter)
