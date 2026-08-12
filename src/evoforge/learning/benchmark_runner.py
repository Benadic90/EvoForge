import json
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

import structlog
from pydantic import BaseModel

from evoforge.memory.database import Database
from evoforge.memory.obsidian import ObsidianManager

logger = structlog.get_logger(__name__)

class BenchmarkTask(BaseModel):
    id: str
    description: str
    expected_output_type: str
    # A lambda or callable that takes (result, expected) -> float (0.0 to 1.0)
    # Since we can't easily persist callables to sqlite natively, we usually
    # map these to predefined evaluator functions in actual deployment.
    evaluator_name: str

class BenchmarkSuite(BaseModel):
    name: str
    agent_name: str
    tasks: list[BenchmarkTask]
    baseline_score: float = 0.0

class BenchmarkResult(BaseModel):
    suite_name: str
    agent_name: str
    score: float
    improvement_pct: float
    success: bool
    details: dict[str, Any]

class BenchmarkRunner:
    def __init__(self, db: Database, obsidian: ObsidianManager):
        self.db = db
        self.obsidian = obsidian
        self._evaluators: dict[str, Callable] = {}
        
    def register_evaluator(self, name: str, func: Callable):
        self._evaluators[name] = func

    def run_suite(self, suite: BenchmarkSuite, agent_instance: Any) -> BenchmarkResult:
        """Runs the entire benchmark suite against an agent instance."""
        logger.info("benchmark_started", suite=suite.name, agent=suite.agent_name, tasks=len(suite.tasks))
        
        total_score = 0.0
        details = {}
        
        for task in suite.tasks:
            try:
                # In a real environment, we'd mock the model_router or use sandbox.
                # Here we simulate the agent processing the task description.
                # Assuming the agent has a think_and_act or similar method.
                if hasattr(agent_instance, 'implement_feature'):
                    result = agent_instance.implement_feature(task.description, [])
                elif hasattr(agent_instance, 'review_changes'):
                    result = agent_instance.review_changes(task.description)
                elif hasattr(agent_instance, 'think_and_act'):
                    # Generic fallback, using mock Enums for task type
                    from evoforge.model_router.classifier import TaskComplexity, TaskType
                    result = agent_instance.think_and_act(task.description, TaskType.CODE_GENERATION, TaskComplexity.MEDIUM)
                else:
                    raise NotImplementedError(f"Agent {suite.agent_name} lacks a standard execution method for benchmarking.")
                
                evaluator = self._evaluators.get(task.evaluator_name)
                if not evaluator:
                    logger.warning("missing_evaluator", name=task.evaluator_name)
                    score = 0.0
                else:
                    score = evaluator(result, task.expected_output_type)
                
                total_score += score
                details[task.id] = {"score": score, "result": result[:100] + "..."}
                
            except Exception as e:
                logger.error("benchmark_task_failed", task=task.id, error=str(e))
                details[task.id] = {"score": 0.0, "error": str(e)}

        max_possible = len(suite.tasks)
        final_score = (total_score / max_possible) if max_possible > 0 else 0.0
        
        improvement = final_score - suite.baseline_score
        success = final_score >= suite.baseline_score # Regression check
        
        result_obj = BenchmarkResult(
            suite_name=suite.name,
            agent_name=suite.agent_name,
            score=final_score,
            improvement_pct=improvement,
            success=success,
            details=details
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
                (id, agent_name, suite_name, task_count, baseline_score, current_score, improvement_pct, results)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (str(uuid.uuid4()), result.agent_name, result.suite_name, len(result.details), 
                 result.score - result.improvement_pct, result.score, result.improvement_pct, 
                 json.dumps(result.details))
            )
            conn.commit()
        finally:
            conn.close()
            
        # Write to Obsidian
        frontmatter = {
            "agent": result.agent_name,
            "suite": result.suite_name,
            "score": result.score,
            "improvement": result.improvement_pct,
            "success": result.success,
            "date": datetime.now().isoformat()
        }
        
        content = f"# Benchmark: {result.suite_name} ({result.agent_name})\n\n"
        content += f"**Final Score**: {result.score:.2f} (Improvement: {result.improvement_pct:+.2f})\n"
        content += f"**Status**: {'✅ PASS' if result.success else '❌ FAIL (Regression)'}\n\n"
        content += "## Details\n```json\n" + json.dumps(result.details, indent=2) + "\n```\n"
        
        file_name = f"{result.agent_name}_{result.suite_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        note_path = self.obsidian.folders["sandbox"] / "benchmarks" / file_name
        self.obsidian._write_note(note_path, content, frontmatter)
