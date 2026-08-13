# Phase 6 Current State Audit (Controlled Self-Evolution)

Based on a comprehensive review of the `src/evoforge` codebase and tests, the following is the baseline audit of existing self-evolution capabilities before commencing Phase 6.

### Components Status

- **`EvolutionAgent`**: **PARTIAL**
  Found in `src/evoforge/evolution/agent.py`. It has logic to propose skill updates based on failure logs (`propose_skill_update`) and review proposals (`review_proposal`) by delegating to LLM reasoning calls. It writes proposals to the `evolution_proposals` table, but it does not execute the actual application or orchestration of the full evolution lifecycle across arbitrary system targets.
- **`ExperimentFramework`**: **REAL**
  Found in `src/evoforge/evolution/experiment.py`. Fully implements A/B testing (`run_ab_test`) between baseline and candidate variants. It runs multiple samples, records scores and durations, strictly evaluates for statistical improvement (`min_improvement_pct`), and performs a strict per-sample non-regression check before declaring a winner.
- **`BenchmarkRunner`**: **REAL**
  Found in `src/evoforge/learning/benchmark_runner.py`. Executes `BenchmarkTask` suites against agent callables, evaluates the outputs using injected evaluator functions, caps scores (0.0 to 1.0), and records the final candidate vs. baseline metrics into both SQLite (`benchmarks` table) and Obsidian markdown files.
- **`SandboxEnvironment`**: **PARTIAL**
  Found in `src/evoforge/learning/sandbox.py`. It creates isolated temporary directories for experiments, sets up dummy `.git` refs to prevent git escapes, and scopes execution with `os.chdir`. However, strict runtime isolation (e.g., subprocesses, Docker, or hard process timeouts) is stubbed (simulates bounded time only).

### Database Schema (Evolution-related)
**State**: **REAL**
The schema in `src/evoforge/memory/database.py` heavily supports Phase 6:
- `evolution_proposals`: Tracks target, expected improvements, risk, status, and benchmark IDs.
- `benchmarks`: Stores baseline vs candidate scores and sample counts.
- `skill_versions`: Stores versioned snapshots for rollback.
- `failures`: Tracks failure reasons, corrections, and a `regression_passed` flag.
- `execution_telemetry` / `routing_decisions`: Extensive tracking of durations, costs, quality scores, and security/test passes to aid historical routing.

### Supported Evolution Targets
**State**: **REAL (but narrow)**
Targets are strongly typed via Pydantic models but currently limited strictly to **Agent Skills**. Evolving global architectures, core workflows, routing policies, or Python codebase logic is not implemented natively. 

### Advanced Phase 6 Features
- **Rollback**: **REAL**
  Implemented in `SkillVersioner.rollback()`. It successfully queries the `skill_versions` table for a specific snapshot and restores the `SkillRegistry` state to that version.
- **Regression Testing**: **REAL**
  `ExperimentFramework.run_ab_test()` performs a strict no-regression check. Regressions are also structurally tracked in the `failures` table.
- **GitHub PR Creation**: **STUB**
  `EvolutionProposer.create_proposal_pr()` creates a mocked URL. Branch checkout, file writing, and the GitHub API integration are completely mocked.
- **Canary / Shadow Mode**: **DOCUMENTATION-ONLY**
  No code or tests exist for shadow mode execution or canary deployments.
- **Multi-metric Promotion Evaluation**: **PARTIAL**
  While `execution_telemetry` tracks multiple dimensions (latency, cost, quality, tests), the promotion logic in `ExperimentFramework` and `BenchmarkRunner` solely relies on a single float `score` returned by a scalar evaluator function. Multi-dimensional trade-off logic does not exist yet.
