# EvoForge 2026 Target Architecture

## Architectural principle

EvoForge should remain a modular Python application at its current scale. Do not introduce microservices merely to make the diagram look advanced. The important boundaries are contracts, state, events, policies, and replaceable workers.

## Runtime layers

```text
Interface Layer
  Web / Telegram / Android / future Voice
             |
Application Layer
  commands / approvals / reports
             |
Orchestration Layer
  scheduler / workflow engine / task queue / recovery
             |
Agent Layer
  planner / architect / developer / QA / security / reviewer / research / evolution
             |
Capability Layer
  Git / filesystem / shell / GitHub / web research / model calls
             |
Policy Layer
  permissions / budgets / sandbox / secrets / approvals
             |
Persistence Layer
  SQLite execution state / Obsidian knowledge / artifacts / metrics
             |
Observability Layer
  structured events / traces / metrics / audit log
```

## Canonical workflow

Every autonomous task receives a stable workflow ID and passes through explicit states.

```text
CREATED
  -> PLANNED
  -> ARCHITECTED
  -> IMPLEMENTING
  -> TESTING
  -> SECURITY_REVIEW
  -> CODE_REVIEW
  -> READY_FOR_PR
  -> PR_OPEN
  -> CI_WAIT
  -> HUMAN_APPROVAL
  -> COMPLETED
```

Failure transitions must be explicit and resumable:

```text
ANY_STATE -> RETRY_PENDING
ANY_STATE -> BLOCKED
ANY_STATE -> NEEDS_HUMAN
ANY_STATE -> FAILED
FAILED -> RECOVERED
```

## Event model

Emit structured events for state changes and meaningful actions. Examples:

- `workflow.created`
- `workflow.resumed`
- `agent.started`
- `agent.completed`
- `tool.called`
- `tool.blocked`
- `model.requested`
- `model.completed`
- `git.branch_created`
- `git.commit_created`
- `github.pr_created`
- `ci.failed`
- `lesson.recorded`
- `research.completed`
- `benchmark.completed`
- `skill.proposed`
- `evolution.proposed`

Events should contain IDs, timestamps, project/repository identity, agent identity, and correlation IDs. Avoid storing secrets or raw private reasoning.

## Agent contract

A future common interface should look conceptually like:

```python
class AgentContract(Protocol):
    name: str
    version: str
    capabilities: list[str]

    def execute(self, request: AgentRequest) -> AgentResult: ...
```

`AgentResult` should contain structured status, artifacts, tool events, metrics, and a safe summary. Do not make the orchestrator depend on agent-specific implementation details.

## State and memory

SQLite is the authoritative execution-state store.

Obsidian is the human-readable long-term knowledge layer.

GitHub is the source of truth for repository source code.

Do not use Obsidian files as a substitute for transactional workflow state.

## Learning architecture

```text
Real work + external research
          |
      ingestion
          |
   source verification
          |
   knowledge registry
          |
    skill candidates
          |
 sandbox experiments
          |
     benchmarks
          |
    regression gate
          |
 skill version proposal
          |
       Git branch
          |
        PR/review
          |
       adoption
          |
    post-adoption metrics
```

A new skill is not considered learned merely because an LLM generated a plausible explanation. It becomes a candidate only after evidence and evaluation.

## Model router architecture

```text
Task
 |
Task classifier
 |
Capability requirements
 |
Candidate models
 |
Budget + availability + historical metrics
 |
Selected provider/model
 |
Execution
 |
Evaluation
 |
Outcome metrics
```

Keep provider adapters isolated. The rest of EvoForge should depend on a provider-neutral request/result model.

## Safety boundary

Agents should never receive unrestricted host privileges by default.

Actions should pass through a policy decision point that considers:

- repository
- branch
- agent
- action
- path
- command
- network requirement
- autonomy level
- budget
- approval state

Destructive actions, merges, deployment, secret access, and security-sensitive configuration changes should remain gated.

## Continuous operation

Do not depend on an immortal process. Treat execution as resumable jobs.

```text
Trigger
  -> Worker
  -> Load checkpoint
  -> Execute bounded step
  -> Persist checkpoint
  -> Emit events
  -> Exit
```

This supports laptop execution, GitHub Actions, and future hosted workers without changing the core workflow model.

## Visual brain

The dashboard should consume the event stream and state store. It should not invent activity.

Views:

- system overview
- project portfolio
- live workflow graph
- agent activity
- model routing
- GitHub/PR activity
- learning/evolution timeline
- failures/recovery
- metrics

Use graph visualization for actual relationships and event animation for actual events. Never expose private model chain-of-thought.
