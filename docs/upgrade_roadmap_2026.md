# EvoForge 2026 Upgrade Roadmap

**Status:** Proposed implementation baseline  
**Last reviewed:** 2026-08-12  
**Branch:** `evoforge/upgrade-roadmap-2026`

## Purpose

This roadmap turns the current EvoForge MVP into a persistent, observable, multi-agent software engineering platform that can continuously improve repositories while also learning, evaluating, and safely evolving its own agent skills.

The current repository already contains substantial foundations: model routing, GitHub integration, memory, policy enforcement, a base agent framework, core and advanced agents, orchestration, evolution, and a dedicated learning package. The next step is therefore **hardening and integration**, not creating another parallel framework.

## Current-state assessment

### Already present

- Python application with CLI and structured logging.
- LiteLLM-based model abstraction with Ollama, Gemini, and NVIDIA providers.
- GitHub repository/client, Git operations, scanning, and pull-request support.
- SQLite + Obsidian-oriented memory layer.
- Policy and shell-command controls.
- Base agent/tool framework.
- Core agents: Developer, QA, Reviewer, Security.
- Advanced agents: Planner, Architect, DevOps, Documentation, Research, Conflict Resolver.
- Orchestration and evolution modules.
- Learning modules for research, source verification, skills, lessons, experiments, benchmarks, knowledge sharing, and innovation.

### Main gap

The repository has many of the right **modules**, but the next engineering challenge is proving that these modules form one reliable lifecycle:

`discover -> plan -> execute -> test -> review -> PR -> learn -> measure -> improve -> resume`

The priority is to replace isolated capability with an integrated, observable, restartable runtime.

## Target architecture

```text
                         EvoForge Runtime
                              |
                        Orchestrator
                              |
        +---------------------+----------------------+
        |                     |                      |
   Workflow State        Model Router           Policy Engine
        |                     |                      |
      SQLite            Local / Gemini / NVIDIA      |
        |                     |                      |
        +---------------------+----------------------+
                              |
                     Specialized Agents
          +---------+---------+---------+---------+
          |         |         |         |         |
       Planner  Architect  Developer    QA     Security
          |         |         |         |         |
          +---------+---------+---------+---------+
                              |
                           Reviewer
                              |
                           GitHub PR
                              |
                       CI / human approval
                              |
                 +------------+------------+
                 |                         |
             Obsidian                  Metrics
                 |                         |
                 +------------+------------+
                              |
                       Learning Loop
                              |
        research -> verify -> practice -> benchmark -> adopt
                              |
                         Evolution PR
```

## Upgrade phases

### Phase A — Runtime integrity

**Goal:** make the existing system actually run as one coherent, restartable workflow.

Work:

- Standardize package interfaces and remove documentation/code path drift.
- Define a canonical `WorkflowState` and task lifecycle.
- Make every side effect idempotent or checkpointed.
- Add explicit run IDs, task IDs, agent IDs, and repository IDs to structured logs.
- Add workflow resume/retry semantics.
- Add integration tests covering a complete task from planning to PR creation.
- Add deterministic dry-run mode.

**Exit criteria:** one end-to-end workflow can be stopped and resumed without corrupting state or repeating already-completed side effects.

### Phase B — Repository portfolio engine

**Goal:** support multiple repositories intelligently.

Work:

- Repository inventory.
- Per-project health snapshot.
- Roadmap/backlog ingestion.
- Priority scoring.
- Daily portfolio selection.
- Per-repository policy profiles.
- Project-specific memory namespaces.

**Exit criteria:** EvoForge can explain why it selected a specific project/task today.

### Phase C — Agent contract system

**Goal:** make every agent replaceable, testable, and measurable.

Each agent should expose:

- identity and role
- capabilities/tools
- input schema
- output schema
- permissions
- model preferences
- metrics
- failure policy
- skill registry
- version

Add an `AgentContract` protocol and a common execution result format.

**Exit criteria:** any agent can be swapped without changing orchestrator code.

### Phase D — Tool and sandbox hardening

**Goal:** safely allow agents to work on real repositories.

Work:

- command allowlists by tool and repository
- repository workspace isolation
- secret scanning before push
- path deny/allow rules
- network policy for untrusted tasks
- safe handling of repository-provided instructions
- explicit approval gates for CI, merge, deploy, and destructive actions

**Exit criteria:** hostile repository content cannot trivially escalate an agent into unrestricted control of the host.

### Phase E — Research and learning system

**Goal:** turn the existing learning package into a real continuous-learning lifecycle.

Work:

- research scheduler
- source freshness tracking
- source verification and confidence
- research inbox -> verified knowledge pipeline
- skill registry with versions
- lessons from real task outcomes
- sandbox experiments
- benchmark datasets
- regression gates for skill updates
- cross-agent knowledge sharing

**Exit criteria:** an agent can identify a skill gap, research it, run a safe experiment, compare against a baseline, and create a versioned improvement proposal.

### Phase F — Model intelligence

**Goal:** make model selection evidence-driven.

Work:

- task taxonomy
- per-model capability profiles
- quota tracking
- latency and reliability metrics
- benchmark-driven routing
- provider fallback
- circuit breakers
- model freshness/discovery
- budget enforcement

The router should support the currently available local, Gemini, and NVIDIA paths without coupling business logic to any provider.

**Exit criteria:** routing decisions can be explained from task requirements + measured model performance.

### Phase G — Visual observability brain

**Goal:** expose real agent execution rather than simulated activity.

Show:

- projects
- agents
- workflow state
- task queue
- model calls
- tool calls
- handoffs
- retries
- Git operations
- CI state
- PRs
- failures
- learning events
- evolution proposals

Do not expose private model chain-of-thought. Show safe execution traces, structured outputs, tool events, state transitions, and summaries.

**Exit criteria:** a user can trace a task from portfolio selection to PR and see where/why it failed or succeeded.

### Phase H — Always-on execution

**Goal:** continue work without requiring the laptop to remain online.

Use event-driven workers rather than a single infinite process.

Preferred pattern:

`scheduled/event trigger -> start worker -> load checkpoint -> execute bounded work -> persist state -> exit`

Potential execution backends:

- GitHub Actions for scheduled and event-triggered lightweight execution.
- Local laptop/Ollama when available.
- Cloud model APIs for inference.
- Future hosted worker if a later budget allows it.

**Exit criteria:** worker interruption does not lose progress and a later worker can resume from the last durable checkpoint.

### Phase I — Android / Telegram / voice interfaces

These are control and observability layers over the same EvoForge core, not separate brains.

Order:

1. Telegram status/approval bot.
2. Web dashboard.
3. Android control client.
4. Voice interface.

**Exit criteria:** interfaces can inspect and control the same workflow state without duplicating orchestration logic.

### Phase J — Safe self-evolution

**Goal:** EvoForge improves its own agents and infrastructure using measurable evidence.

Lifecycle:

`observe -> identify weakness -> research -> experiment -> benchmark -> propose -> branch -> test -> PR -> approval -> adopt -> monitor -> rollback if regression`

**Never:** arbitrary self-modification directly on the production branch.

**Exit criteria:** EvoForge can safely propose and validate a measurable improvement to one of its own agents.

## Daily autonomous operating loop

```text
1. inventory repositories
2. refresh project health
3. refresh time-sensitive research
4. load roadmap + backlog + previous lessons
5. score candidate tasks
6. choose bounded work item
7. architect
8. implement
9. run tests
10. run security checks
11. independent review
12. fix/retry within budget
13. commit + push branch
14. create/update PR
15. persist outcome
16. record lessons
17. update agent/project metrics
18. schedule next work
```

## 90-day implementation target

### Month 1 — Reliability

- runtime integration
- canonical workflow state
- end-to-end PR flow
- recovery/resume
- policy hardening
- CI

### Month 2 — Learning + model intelligence

- research scheduler
- source verification
- skill registry v2
- benchmark runner
- model routing metrics
- portfolio prioritization

### Month 3 — Observability + autonomy

- visual brain
- GitHub Actions execution
- Telegram interface
- safe evolution PRs
- daily reports

## Definition of success

EvoForge is successful when it can be given a portfolio of repositories and, without daily hand-holding, repeatedly:

1. understand project state;
2. choose useful work;
3. implement bounded changes;
4. validate and review them;
5. submit safe PRs;
6. remember what happened;
7. learn from failures and new research;
8. measure whether its learning actually helps; and
9. recover and continue after a worker or API failure.

The system should optimize for **useful engineering progress**, not commit count.
