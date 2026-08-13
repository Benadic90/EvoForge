# Phase 5: Learning & Skill Evolution Audit

## Current Baseline

### 1. SkillRegistry
* **Status**: **REAL**
* **File Path**: `src/evoforge/learning/skill_registry.py`
* **Description**: Fully implemented. Persists skills to the `skills` SQLite table tracking `last_verified`, `freshness`, and JSON metadata. It handles syncing agent profiles and writing versioned skill markdown files directly to the Obsidian vault.

### 2. ResearchEngine
* **Status**: **REAL**
* **File Path**: `src/evoforge/learning/research_engine.py`
* **Description**: Fully implemented. Features a `ResearchScheduler` that tracks and queries pending research topics from the `research_items` SQLite table. The `ResearchEngine` triggers a `ResearchAgent` to complete topics, updates the database status, and outputs findings directly to the Obsidian inbox.

### 3. SourceVerifier
* **Status**: **REAL**
* **File Path**: `src/evoforge/learning/source_verifier.py`
* **Description**: Fully implemented. Contains a `SourceEvaluator` that heuristically assigns confidence scores based on source URL formats (e.g. docs, arxiv, stackoverflow). The `KnowledgeVerifier` leverages this to ingest items into the `knowledge_items` table and transitions their statuses (VERIFIED, EXPERIMENTAL, REJECTED) while documenting the accepted knowledge into Obsidian.

### 4. BenchmarkRunner
* **Status**: **PARTIAL**
* **File Path**: `src/evoforge/learning/benchmark_runner.py`
* **Description**: Partially implemented. The persistence and reporting mechanisms are real; it saves calculated benchmark results directly to the `benchmarks` SQLite table and writes reports to Obsidian. However, task execution is somewhat stubbed, relying on `hasattr` checks and mock enums to forcefully invoke generic agent methods. 

### 5. SandboxEnvironment
* **Status**: **REAL**
* **File Path**: `src/evoforge/learning/sandbox.py`
* **Description**: Fully implemented using basic local directory isolation. It generates isolated temporary directories, forces function execution within them using `os.chdir` wrappers, manages cleanup, and writes A/B test results to the Obsidian sandbox folder.

### 6. LessonRecorder
* **Status**: **PARTIAL**
* **File Path**: `src/evoforge/learning/lesson_recorder.py`
* **Description**: Data persistence is fully implemented (saving success/failures to the `failures` and `lessons` SQLite tables and writing markdown to Obsidian). However, the auto-generation logic via the `_detect_patterns` method is strictly a **STUB**, with comments stating a real implementation would require LLM embeddings.

### 7. KnowledgeRegistry
* **Status**: **REAL**
* **File Path**: `src/evoforge/learning/knowledge_sharing.py`
* **Description**: Fully implemented. Exposes methods for agents to subscribe to domains. It runs propagation loops fetching 'VERIFIED' items from the `knowledge_items` table and updates the `applicable_agents` list, ensuring agents only see relevant validated data.

### 8. ExperimentFramework
* **Status**: **REAL**
* **File Path**: `src/evoforge/evolution/experiment.py`
* **Description**: Fully implemented. Acts as an in-memory execution harness to run A/B tests on inputs against two callable variants, evaluating results, catching runtime exceptions, measuring execution time in milliseconds, and correctly attributing a winner. 

### 9. EvolutionAgent
* **Status**: **PARTIAL / STUB**
* **File Path**: `src/evoforge/evolution/agent.py`
* **Description**: Heavily stubbed. While defined correctly as a subclass of `BaseAgent`, methods like `propose_skill_update` skip LLM output parsing entirely and return a hardcoded dictionary. `analyze_failures` and `review_proposal` simply act as pass-through prompt wrappers calling `think_and_act`.

### 10. PerformanceMonitor
* **Status**: **REAL**
* **File Path**: `src/evoforge/evolution/metrics.py`
* **Description**: Fully implemented. Writes incoming scalar metrics to the `metrics` table in SQLite. It accurately calculates moving baselines and averages over adjustable time windows leveraging native SQLite datetime functions.
