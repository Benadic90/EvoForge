# EvoForge Project Portfolio Intelligence

Phase 4 of EvoForge introduces **Project Portfolio Intelligence**, elevating EvoForge from a single-task automation tool into an autonomous portfolio manager.

## Core Capabilities

1. **GitHub Discovery**: Discovers and scans GitHub repositories (issues, PRs, commits, CI state).
2. **Project Memory**: Maintains long-term context and canonical health states for all managed projects in the portfolio using `ProjectProfile`.
3. **Roadmap Syncing**: Harmonizes factual GitHub evidence with strategic objectives defined in Obsidian via `RoadmapSynchronizer`.
4. **Health & Prioritization Engine**: Uses a configurable, weighted scoring model (`PortfolioPriorityEngine`) to assign priority rankings to projects and tasks, driven by evidence (e.g., CI failures, critical security issues).
5. **Daily Planning Loop**: Generates a bounded daily execution plan (`DailyPlanner`) that fits within defined throughput and budget limits, selecting the most critical tasks across the portfolio.

## Architecture

- **`src/evoforge/portfolio/models.py`**: Pydantic models for profiles, tasks, roadmaps, evidence, and rankings.
- **`src/evoforge/portfolio/registry.py`**: SQLite-backed CRUD for `ProjectProfile`.
- **`src/evoforge/portfolio/scanner.py`**: Gathers GitHub data and local analysis to compute health scores.
- **`src/evoforge/portfolio/roadmap.py`**: Synchronizes Obsidian memory with database planning state.
- **`src/evoforge/portfolio/priority_engine.py`**: Core mathematical ranking logic.
- **`src/evoforge/portfolio/daily_planner.py`**: Consumes rankings and outputs a deterministic plan for the orchestrator.

## Visual Brain Integration

The new `PortfolioView.jsx` in the Visual Brain provides a real-time command center for the portfolio. It visualizes the current health of all projects, the priority rankings, and the deterministic Daily Plan that EvoForge will execute.
