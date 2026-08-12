# Capability System

EvoForge capabilities define *what* an executor or agent can do. They are distinct from *permissions* (what they are allowed to do) and *skills* (what they know how to do).

## Core Vocabulary

Capabilities are defined in `AgentCapability` enum (`src/evoforge/agents/capabilities.py`) to prevent naming drift. 

Examples:
- `coding`: Write and edit code.
- `terminal`: Execute shell commands.
- `browser`: Interact with websites.
- `testing`: Run software tests.
- `parallel_execution`: Spawn and coordinate multiple sub-agents.

## Capability Metadata

The `CAPABILITY_REGISTRY` stores metadata for each capability:
- `risk_level`: (LOW, MEDIUM, HIGH, CRITICAL)
- `description`: Human-readable explanation.
- `minimum_context`: Token requirements if applicable.

## Capability Matching

The `match_capabilities()` function determines if a provided set of capabilities satisfies a required set. It returns a `CapabilityMatchResult` containing:
- `matched`: Boolean indicating full satisfaction.
- `missing`: List of missing capabilities.
- `extra`: List of provided capabilities not required.
- `score`: A float `[0.0 - 1.0]` indicating how well the requirement is met.

## Role in Phase 3

In Phase 3, the Model Router will use `CapabilityMatchResult.score` alongside latency, cost, and quota metrics to dynamically select the best executor for a given task.
