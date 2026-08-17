import structlog
import typer
from rich.console import Console
from rich.table import Table

from evoforge.agents.capabilities import CAPABILITY_REGISTRY, AgentCapability
from evoforge.agents.factory import build_agent_registry

# Initialize logger
logger = structlog.get_logger()
console = Console()

app = typer.Typer(help="EvoForge Autonomous AI Software Engineering Platform", no_args_is_help=True)
evolution_app = typer.Typer(help="Manage Phase 6 Controlled Self-Evolution", no_args_is_help=True)
app.add_typer(evolution_app, name="evolution")


def _control_plane_token() -> str:
    import os

    token = os.environ.get("WORKER_SECRET_TOKEN")
    if token:
        return token
    if os.environ.get("EVOFORGE_ALLOW_DEFAULT_DEV_TOKEN") == "1":
        return "default-dev-token"
    raise typer.BadParameter(
        "WORKER_SECRET_TOKEN is required. Set EVOFORGE_ALLOW_DEFAULT_DEV_TOKEN=1 only for local development."
    )


@app.command()
def run_daily():
    """
    Execute the daily autonomous loop.
    """
    logger.info("starting_daily_run")
    from evoforge.agents.factory import build_agent_registry
    from evoforge.github_integration.client import GitHubClient
    from evoforge.memory.database import Database
    from evoforge.memory.manager import MemoryManager
    from evoforge.model_router.executors import create_default_executor_registry
    from evoforge.model_router.routing import ExecutorRouter
    from evoforge.orchestrator.engine import OrchestratorEngine
    from evoforge.orchestrator.workflows import WorkflowDefinition, WorkflowTask
    from evoforge.portfolio.daily_planner import DailyPlanner
    from evoforge.portfolio.priority_engine import PortfolioPriorityEngine
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.portfolio.scanner import ProjectScanner
    from evoforge.portfolio.task_builder import PortfolioTaskRequirementsBuilder
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    registry = ProjectRegistry(db)
    gh_client = GitHubClient(db=db)
    scanner = ProjectScanner(db, gh_client, registry)
    priority_engine = PortfolioPriorityEngine(db, registry)
    
    console.print("[cyan]Starting daily portfolio scan...[/cyan]")
    for p in registry.list():
        if p.status in ("MANAGED", "ACTIVE"):
            console.print(f"Scanning {p.repository_full_name}...")
            res = scanner.scan_project(p.project_id, force_rescan=True)
            if res:
                report, raw_items = res
                if raw_items:
                    priority_engine.generate_backlog(p.project_id, raw_items)
                
    console.print("[cyan]Ranking portfolio items...[/cyan]")
    priority_engine.rank_projects()
    priority_engine.rank_tasks()
    
    planner = DailyPlanner(db, registry)
    plan = planner.generate_plan()
    
    console.print(f"[green]Daily plan generated with {len(plan.selected_tasks)} tasks.[/green]")
    
    if not plan.selected_tasks:
        console.print("No actionable tasks in plan. Exiting.")
        return
        
    executor_registry = create_default_executor_registry(cfg, db=db)
    router = ExecutorRouter(executor_registry)
    agent_registry = build_agent_registry(None, None)
    orchestrator = OrchestratorEngine(MemoryManager(db, ""), agent_registry, router)
    
    for task_id in plan.execution_order:
        query = "SELECT * FROM portfolio_tasks WHERE task_id = ?"
        rows = db.fetchall(query, (task_id,))
        if not rows:
            continue
            
        import json

        from evoforge.portfolio.models import PortfolioTask
        row = dict(rows[0])
        ptask = PortfolioTask(
            task_id=row["task_id"],
            canonical_task_id=row.get("canonical_task_id"),
            project_id=row["project_id"],
            repository_full_name=row.get("repository_full_name"),
            title=row["title"],
            description=row["description"],
            source=row["source"],
            source_type=row.get("source_type", "unknown"),
            source_id=row["source_id"],
            source_url=row.get("source_url"),
            priority=row["priority"],
            confidence=row.get("confidence", 1.0),
            risk=row["risk"],
            estimated_minutes=row.get("estimated_minutes"),
            dependencies=json.loads(row["dependencies"]) if row["dependencies"] else [],
            required_capabilities=json.loads(row["required_capabilities"]) if row["required_capabilities"] else [],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )
        
        req = PortfolioTaskRequirementsBuilder.build(ptask)
        
        # Route to see if we can execute
        try:
            chain, expl = router.get_candidate_chain(req)
            if not chain:
                console.print(f"[yellow]Skipping {task_id}: no valid routing candidates.[/yellow]")
                continue
                
            from evoforge.orchestrator.workflows import TaskPriority
            wtask = WorkflowTask(
                id=req.task_id,
                name=ptask.title,
                description=ptask.description,
                priority=TaskPriority.MEDIUM,
                agent_type="developer",
            )
            
            repo_name = ptask.repository_full_name or "unknown/repo"
            wdef = WorkflowDefinition(
                id=f"wf_{plan.plan_id}_{task_id}",
                repo_name=repo_name,
                tasks=[wtask],
                dry_run=False
            )
            
            console.print(f"[cyan]Executing {task_id} via Orchestrator...[/cyan]")
            # Update task status
            db.execute("UPDATE portfolio_tasks SET status = 'RUNNING' WHERE task_id = ?", (task_id,))
            
            # Must insert into workflows so lease can be acquired
            import json
            import time
            state_snapshot = json.dumps({"workflow_id": wdef.id, "run_id": f"run_{int(time.time())}", "repository_id": repo_name, "current_stage": "INITIALIZE", "dry_run": False, "attempt_count": 0, "history": []})
            db.execute(
                "INSERT INTO workflows (id, project, workflow_type, task_description, status, state_snapshot) VALUES (?, ?, ?, ?, 'pending', ?) ON CONFLICT(id) DO NOTHING",
                (wdef.id, ptask.project_id, "portfolio_task", ptask.title, state_snapshot)
            )
            
            orchestrator.execute_workflow(wdef)
            
            # Since execute_workflow is blocking for bounded execution, we can check state afterwards
            db.execute("UPDATE portfolio_tasks SET status = 'COMPLETED' WHERE task_id = ?", (task_id,))
            
        except Exception as e:
            console.print(f"[red]Error executing {task_id}: {e}[/red]")
            db.execute("UPDATE portfolio_tasks SET status = 'FAILED' WHERE task_id = ?", (task_id,))
            
    logger.info("daily_run_completed")

@app.command()
def status():
    """
    Show the current system status and metrics.
    """
    logger.info("fetching_status")
    # TODO: Implement status fetching


@app.command("antigravity-status")
def antigravity_status():
    """Show the availability and health of the Antigravity integration."""
    from evoforge.model_router.antigravity_runtime import AntigravityRuntimeDetector
    from evoforge.model_router.executors import create_default_executor_registry
    from evoforge.utils.config import load_config
    
    info = AntigravityRuntimeDetector.get_runtime_info()
    
    console.print("[bold cyan]Antigravity[/bold cyan]")
    if info.available:
        console.print("[green]Status: AVAILABLE[/green]")
        console.print(f"Runtime Type: {info.runtime_type}")
        console.print(f"Executable: {info.executable_path}")
        
        config = load_config()
        registry = create_default_executor_registry(config)
        caps = registry.get_capabilities("antigravity")
        console.print("\nCapabilities:")
        for c in caps:
            console.print(f"  {c.value}")
            
        console.print("\nHealth:")
        console.print("  [green]HEALTHY[/green]")
    else:
        console.print("[yellow]Status: UNAVAILABLE[/yellow]")
        console.print(f"\nReason:\n  {info.reason_unavailable}")
        console.print("\nExecution:\n  NOT ATTEMPTED")


@app.command("antigravity-test")
def antigravity_test():
    """Perform a harmless read-only test using the Antigravity integration, if available."""
    from evoforge.model_router.antigravity_runtime import AntigravityRuntimeDetector
    info = AntigravityRuntimeDetector.get_runtime_info()
    
    if not info.available:
        console.print("[yellow]Antigravity runtime is unavailable. Test cannot proceed.[/yellow]")
        return
        
    console.print("[green]Antigravity runtime is available. Proceeding with test...[/green]")
    # TODO: If a real runtime becomes available, this is where we would dispatch a harmless task.
    # We do not simulate success.
    console.print("[yellow]Test task dispatch not implemented for the real runtime yet.[/yellow]")


@app.command("agents")
def list_agents():
    """List all registered agents and their metadata."""
    registry = build_agent_registry(None, None)
    table = Table(title="Registered Agents")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Version")
    table.add_column("Status")
    table.add_column("Capabilities")
    
    for contract in sorted(registry.list(), key=lambda c: c.agent_id):
        status = "ENABLED" if contract.enabled else "DISABLED"
        caps = ", ".join([c.value for c in contract.capabilities])
        table.add_row(contract.agent_id, contract.name, contract.version, status, caps)
        
    console.print(table)


@app.command("agent-show")
def show_agent(agent_id: str):
    """Show detailed metadata for a specific agent."""
    registry = build_agent_registry(None, None)
    if not registry.has(agent_id):
        console.print(f"[red]Error: Agent '{agent_id}' not found.[/red]")
        raise typer.Exit(code=1)
        
    contract, _ = registry.get(agent_id)
    
    console.print(f"\n[bold green]{contract.name} Agent[/bold green]")
    console.print(f"Status: {'ENABLED' if contract.enabled else 'DISABLED'}")
    console.print(f"Version: {contract.version}")
    console.print(f"\n[bold]Description:[/bold] {contract.description}")
    
    console.print("\n[bold]Capabilities:[/bold]")
    for cap in contract.capabilities:
        console.print(f"  - {cap.value}")
        
    console.print("\n[bold]Tools:[/bold]")
    if not contract.tools:
        console.print("  (None defined)")
    for t in contract.tools:
        console.print(f"  - {t.name} ({'REQUIRED' if t.required else 'OPTIONAL'})")


@app.command("capabilities")
def list_capabilities():
    """List all available capability vocabularies."""
    table = Table(title="System Capabilities")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Risk Level", style="red")
    table.add_column("Description")
    
    for cap_id, meta in sorted(CAPABILITY_REGISTRY.items(), key=lambda x: x[0].value):
        table.add_row(meta.id.value, meta.name, meta.risk_level.value, meta.description)
        
    console.print(table)


@app.command("capability-agents")
def capability_agents(capability: str):
    """List agents that provide a specific capability."""
    try:
        cap_enum = AgentCapability(capability)
    except ValueError:
        console.print(f"[red]Error: Unknown capability '{capability}'.[/red]")
        raise typer.Exit(code=1)
        
    registry = build_agent_registry(None, None)
    agents = registry.find_by_capability(cap_enum)
    
    if not agents:
        console.print(f"No agents provide capability '{capability}'.")
        return
        
    table = Table(title=f"Agents with '{capability}' capability")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Name", style="green")
    
    for contract in agents:
        table.add_row(contract.agent_id, contract.name)
        
    console.print(table)

    
@app.command("executors")
def list_executors():
    """List all available executors in the routing system."""
    from evoforge.model_router.executors import (
        AntigravityExecutor,
        ExecutorRegistry,
        GeminiExecutor,
        LocalModelExecutor,
        NvidiaExecutor,
    )
    registry = ExecutorRegistry()
    registry.register("local", LocalModelExecutor(), [AgentCapability.CODING])
    registry.register("gemini", GeminiExecutor(), [AgentCapability.CODING, AgentCapability.REASONING])
    registry.register("nvidia", NvidiaExecutor(), [AgentCapability.CODING, AgentCapability.REASONING])
    registry.register("antigravity", AntigravityExecutor(), [
        AgentCapability.CODING,
        AgentCapability.REASONING,
        AgentCapability.BROWSER,
        AgentCapability.TERMINAL,
        AgentCapability.REPO_NAVIGATION,
    ])

    table = Table(title="Registered Executors")
    table.add_column("Executor ID", style="cyan")
    table.add_column("Healthy")
    table.add_column("Enabled")
    table.add_column("Capabilities")

    for exc in sorted(registry.list_all()):
        healthy = "[green]Yes[/green]" if registry.is_healthy(exc) else "[red]No[/red]"
        enabled = "[green]Yes[/green]" if registry.is_enabled(exc) else "[red]No[/red]"
        caps = ", ".join([c.value for c in registry.get_capabilities(exc)])
        table.add_row(exc, healthy, enabled, caps)

    console.print(table)


@app.command("provider-health")
def provider_health():
    """Check live connectivity and credential configuration for all model providers."""
    from evoforge.model_router.executors import (
        AntigravityExecutor,
        GeminiExecutor,
        LocalModelExecutor,
        NvidiaExecutor,
    )

    table = Table(title="Model Provider Live Health Status")
    table.add_column("Provider", style="cyan")
    table.add_column("Endpoint / Mode")
    table.add_column("Status")
    table.add_column("Details")

    # Local Ollama
    local = LocalModelExecutor()
    local_ok = local.health_check()
    table.add_row(
        "Ollama (Local)",
        local.endpoint,
        "[green]HEALTHY[/green]" if local_ok else "[yellow]UNREACHABLE[/yellow]",
        "Local daemon active" if local_ok else "Ollama daemon not responding on localhost:11434",
    )

    # Gemini
    gemini = GeminiExecutor()
    gemini_ok = gemini.health_check()
    table.add_row(
        "Google Gemini",
        gemini.model_id,
        "[green]CONFIGURED[/green]" if gemini_ok else "[red]MISSING_KEY[/red]",
        "API key present in environment" if gemini_ok else "Set GEMINI_API_KEY or GOOGLE_API_KEY",
    )

    # NVIDIA
    nvidia = NvidiaExecutor()
    nvidia_ok = nvidia.health_check()
    table.add_row(
        "NVIDIA Cloud",
        nvidia.endpoint,
        "[green]CONFIGURED[/green]" if nvidia_ok else "[red]MISSING_KEY[/red]",
        "API key present in environment" if nvidia_ok else "Set NVIDIA_API_KEY",
    )

    # Antigravity
    ag = AntigravityExecutor()
    ag_ok = ag.health_check()
    table.add_row(
        "Antigravity Boundary",
        "Agentic Runtime",
        "[green]ACTIVE[/green]" if ag_ok else "[blue]STANDBY_BOUNDARY[/blue]",
        "Boundary connected" if ag_ok else "Explicit integration boundary (standby)",
    )

    console.print(table)


@app.command("route-test")
def route_test(task: str):
    """Dry-run the model router for a specific task description with candidate ranking and reasons."""
    from evoforge.model_router.executors import (
        AntigravityExecutor,
        ExecutorRegistry,
        GeminiExecutor,
        LocalModelExecutor,
        NvidiaExecutor,
    )
    from evoforge.model_router.requirements import TaskClassification, TaskRequirements
    from evoforge.model_router.routing import ExecutorRouter

    registry = ExecutorRegistry()
    registry.register("local", LocalModelExecutor(), [
        AgentCapability.CODING,
        AgentCapability.REFACTORING,
        AgentCapability.MULTI_FILE_EDITING,
    ])
    registry.register("gemini", GeminiExecutor(), [
        AgentCapability.CODING,
        AgentCapability.REASONING,
        AgentCapability.REFACTORING,
        AgentCapability.MULTI_FILE_EDITING,
        AgentCapability.REPO_NAVIGATION,
        AgentCapability.TERMINAL,
    ])
    registry.register("nvidia", NvidiaExecutor(), [
        AgentCapability.CODING,
        AgentCapability.REASONING,
        AgentCapability.REFACTORING,
        AgentCapability.MULTI_FILE_EDITING,
        AgentCapability.TERMINAL,
    ])
    registry.register("antigravity", AntigravityExecutor(), [
        AgentCapability.CODING,
        AgentCapability.REASONING,
        AgentCapability.BROWSER,
        AgentCapability.TERMINAL,
        AgentCapability.REPO_NAVIGATION,
        AgentCapability.TESTING,
        AgentCapability.MULTI_FILE_EDITING,
    ])

    # Allow local, gemini, nvidia to be eligible for route-test demo
    registry.set_health("local", True)
    registry.set_health("gemini", True)
    registry.set_health("nvidia", True)

    router = ExecutorRouter(registry)


    req_caps = [AgentCapability.CODING]
    if "test" in task.lower():
        req_caps.append(AgentCapability.TESTING)
    if "refactor" in task.lower():
        req_caps.append(AgentCapability.MULTI_FILE_EDITING)
    if "repo" in task.lower() or "analyze" in task.lower():
        req_caps.append(AgentCapability.REPO_NAVIGATION)

    req = TaskRequirements(
        task_id="route_test_demo",
        task_type=TaskClassification.CODING,
        required_capabilities=req_caps,
    )

    console.print(f"\n[bold cyan]Task Description:[/bold cyan] {task}")
    console.print("[bold]Required Capabilities:[/bold]")
    for c in req_caps:
        console.print(f"  • {c.value}")

    try:
        chain, explanation = router.get_candidate_chain(req)

        console.print("\n[bold]Eligible Candidates (Ranked):[/bold]")
        for c in explanation.candidates:
            console.print(f"  • [green]{c.executor_id}[/green] — Score: [bold]{c.score:.2f}[/bold]")
            for r in c.reasons:
                console.print(f"      - {r}")

        if explanation.rejected:
            console.print("\n[bold]Unavailable / Rejected Backends:[/bold]")
            for rej, reasons in explanation.rejected.items():
                console.print(f"  • [red]{rej}[/red]: {', '.join(reasons)}")

        console.print(f"\n[bold]Selected Primary Executor:[/bold] [bold green]{explanation.selected_executor_id}[/bold green]")
        console.print(f"[bold]Fallback Order:[/bold] {' → '.join([eid for eid, _ in chain])}")

    except RuntimeError as e:
        console.print(f"\n[bold red]Routing Failed:[/bold red] {e}")


@app.command("routing-history")
def routing_history(limit: int = 20):
    """Display recent persistent routing decisions with rankings and rationales."""
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config

    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    decisions = db.get_routing_decisions(limit=limit)

    table = Table(title=f"Recent Routing Decisions (Last {limit})")
    table.add_column("ID", style="dim")
    table.add_column("Task ID", style="cyan")
    table.add_column("Workflow", style="magenta")
    table.add_column("Agent / Type")
    table.add_column("Selected Executor", style="bold green")
    table.add_column("Score", justify="right")
    table.add_column("Policy")
    table.add_column("Decision Rationale")

    for d in decisions:
        agent_type = f"{d['agent_id'] or '-'} ({d['task_type'] or '-'})"
        table.add_row(
            str(d["id"]),
            d["task_id"][:16],
            d["workflow_id"][:16],
            agent_type,
            d["selected_executor_id"],
            f"{d['selected_score']:.2f}",
            d["routing_policy_version"] or "adaptive-v1",
            d["decision_reason"][:60] + "..." if d["decision_reason"] and len(d["decision_reason"]) > 60 else (d["decision_reason"] or "-"),
        )

    console.print(table)


@app.command("routing-stats")
def routing_stats():
    """Display aggregate routing performance, empirical success, and latency from SQLite."""
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config

    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    stats = db.get_executor_stats()

    table = Table(title="Executor Routing & Empirical Performance")
    table.add_column("Executor", style="bold cyan")
    table.add_column("Total Runs", justify="right")
    table.add_column("Success Rate", justify="right")
    table.add_column("Avg Quality", justify="right")
    table.add_column("Avg Latency", justify="right")
    table.add_column("Avg Cost", justify="right")
    table.add_column("Fallbacks", justify="right")

    if not stats:
        console.print("[yellow]No execution telemetry recorded yet in SQLite database.[/yellow]")
        return

    for exc_id, st in stats.items():
        total = int(st["total_runs"])
        succ_rate = f"{st['success_rate'] * 100:.1f}%" if total > 0 else "N/A"
        latency = f"{st['avg_duration_ms'] / 1000.0:.2f}s" if total > 0 else "-"
        cost = f"${st['avg_cost_usd']:.4f}" if total > 0 else "-"
        qual = f"{st['avg_quality_score']:.2f}" if total > 0 else "-"
        fallbacks = f"{st.get('fallback_count', 0)} ({st.get('fallback_rate', 0.0) * 100:.1f}%)"

        table.add_row(
            exc_id,
            str(total),
            succ_rate,
            qual,
            latency,
            cost,
            fallbacks,
        )

    console.print(table)


@app.command("executor-stats")
def executor_stats(task_type: str = typer.Option(None, "--task-type", "-t", help="Filter by task type")):
    """Display segmented historical task-type performance per executor."""
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config

    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    task_stats = db.get_task_type_stats(task_type=task_type)

    title = f"Task-Type Historical Performance ({task_type})" if task_type else "Task-Type Historical Performance"
    table = Table(title=title)
    table.add_column("Executor", style="cyan")
    table.add_column("Task Type", style="magenta")
    table.add_column("Total Runs", justify="right")
    table.add_column("Success Rate", justify="right")
    table.add_column("Avg Latency", justify="right")
    table.add_column("Quality", justify="right")
    table.add_column("Tests Passed", justify="right")

    if not task_stats:
        console.print("[yellow]No task-type telemetry recorded yet.[/yellow]")
        return

    for ts in task_stats:
        tot = int(ts["total_runs"])
        succ_rate = f"{ts['success_rate'] * 100:.1f}%" if tot > 0 else "N/A"
        latency = f"{ts['avg_duration_ms'] / 1000.0:.2f}s" if tot > 0 else "-"
        qual = f"{ts['avg_quality_score']:.2f}"
        tests = f"{ts['tests_passed_count']}/{tot}"

        table.add_row(
            ts["executor_id"],
            ts["task_type"],
            str(tot),
            succ_rate,
            latency,
            qual,
            tests,
        )

    console.print(table)


@app.command("projects")
def list_projects():
    """List all explicitly managed portfolio projects."""
    from evoforge.memory.database import Database
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    registry = ProjectRegistry(db)
    
    table = Table(title="Portfolio Projects")
    table.add_column("Project ID", style="cyan")
    table.add_column("Repository", style="green")
    table.add_column("Status")
    table.add_column("Priority Score")
    table.add_column("Health")
    
    for p in registry.list():
        table.add_row(
            p.project_id,
            p.repository_full_name,
            p.status,
            f"{p.priority_score:.2f}",
            p.health
        )
    console.print(table)


@app.command("project-add")
def project_add(repo: str):
    """Register a GitHub repository as a managed project."""
    import uuid

    from evoforge.memory.database import Database
    from evoforge.portfolio.models import ProjectProfile
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    registry = ProjectRegistry(db)
    
    # Check if already exists
    if registry.get_by_repo(repo):
        console.print(f"[yellow]Repository {repo} is already registered.[/yellow]")
        return
        
    project_id = f"proj_{uuid.uuid4().hex[:8]}"
    owner, name = repo.split('/') if '/' in repo else ("unknown", repo)
    
    profile = ProjectProfile(
        project_id=project_id,
        repository_full_name=repo,
        repository_url=f"https://github.com/{repo}",
        owner=owner,
        name=name,
        default_branch="main",  # Will be updated by scanner
        status="ACTIVE"
    )
    registry.register(profile)
    console.print(f"[green]Successfully registered {repo} with ID {project_id}[/green]")


@app.command("project-remove")
def project_remove(repo: str):
    """Remove a repository from the managed portfolio."""
    from evoforge.memory.database import Database
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    registry = ProjectRegistry(db)
    
    p = registry.get_by_repo(repo)
    if not p:
        console.print(f"[yellow]Repository {repo} is not registered.[/yellow]")
        return
        
    registry.remove(p.project_id)
    console.print(f"[green]Successfully removed {repo}[/green]")


@app.command("project-show")
def project_show(project_id: str):
    """Show detailed portfolio metrics for a project."""
    from evoforge.memory.database import Database
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    registry = ProjectRegistry(db)
    
    p = registry.get(project_id) or registry.get_by_repo(project_id)
    if not p:
        console.print(f"[red]Project {project_id} not found.[/red]")
        return
        
    console.print(f"[bold cyan]Project:[/bold cyan] {p.name}")
    console.print(f"Repository: {p.repository_full_name}")
    console.print(f"Status: {p.status}")
    console.print(f"Health: {p.health}")
    console.print(f"Priority Score: {p.priority_score:.2f}")
    if p.description:
        console.print(f"Description: {p.description}")


@app.command("portfolio-scan")
def portfolio_scan():
    """Scan all managed projects to update health and roadmap state."""
    from evoforge.github_integration.client import GitHubClient
    from evoforge.memory.database import Database
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.portfolio.scanner import ProjectScanner
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    registry = ProjectRegistry(db)
    gh_client = GitHubClient()
    scanner = ProjectScanner(db, gh_client, registry)
    console.print("[cyan]Starting portfolio scan...[/cyan]")
    for p in registry.list():
        if p.status == "ACTIVE":
            console.print(f"Scanning {p.repository_full_name}...")
            res = scanner.scan_project(p.project_id)
            if res:
                report, raw_items = res
                if report:
                    console.print(f"  Health: {report.overall_health}")
                    console.print(f"  Discovered items: {len(raw_items) if raw_items else 0}")
    console.print("[green]Portfolio scan completed.[/green]")


@app.command("portfolio-health")
def portfolio_health():
    """Display an aggregated view of portfolio health."""
    from evoforge.memory.database import Database
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    registry = ProjectRegistry(db)
    
    projects = registry.list()
    total = len(projects)
    healthy = sum(1 for p in projects if p.health == "HEALTHY")
    warning = sum(1 for p in projects if p.health == "WARNING")
    critical = sum(1 for p in projects if p.health == "CRITICAL")
    unknown = sum(1 for p in projects if p.health == "UNKNOWN")
    
    console.print("[bold cyan]Portfolio Health Overview[/bold cyan]")
    console.print(f"Total Projects: {total}")
    console.print(f"[green]Healthy:[/green] {healthy}")
    console.print(f"[yellow]Warning:[/yellow] {warning}")
    console.print(f"[red]Critical:[/red] {critical}")
    console.print(f"Unknown: {unknown}")


@app.command("portfolio-ranking")
def portfolio_ranking():
    """Rank projects and tasks based on portfolio priority engine."""
    from evoforge.memory.database import Database
    from evoforge.portfolio.priority_engine import PortfolioPriorityEngine
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    registry = ProjectRegistry(db)
    engine = PortfolioPriorityEngine(db, registry)
    
    console.print("[cyan]Generating Project Rankings...[/cyan]")
    rankings = engine.rank_projects()
    
    table = Table(title="Project Rankings")
    table.add_column("Rank", style="cyan")
    table.add_column("Project ID", style="green")
    table.add_column("Score")
    table.add_column("Top Reason")
    
    for r in rankings:
        reason = r.reasons[0] if r.reasons else "None"
        table.add_row(str(r.rank), r.item_id, f"{r.score:.2f}", reason)
        
    console.print(table)


@app.command("daily-plan")
def daily_plan():
    """Generate the daily portfolio plan for execution."""
    from evoforge.memory.database import Database
    from evoforge.portfolio.daily_planner import DailyPlanner
    from evoforge.portfolio.priority_engine import PortfolioPriorityEngine
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    registry = ProjectRegistry(db)
    
    # Refresh rankings
    engine = PortfolioPriorityEngine(db, registry)
    engine.rank_projects()
    engine.rank_tasks()
    
    # Generate plan
    planner = DailyPlanner(db, registry)
    plan = planner.generate_plan()
    
    console.print("[bold cyan]Daily Portfolio Plan[/bold cyan]")
    console.print(f"Date: {plan.date}")
    console.print(f"Projects to focus on: {len(plan.selected_projects)}")
    console.print(f"Tasks scheduled: {len(plan.selected_tasks)}")
    console.print("\n[bold]Execution Order:[/bold]")
    for idx, task_id in enumerate(plan.execution_order):
        console.print(f"{idx+1}. {task_id}")
    console.print(f"\n[bold]Budget:[/bold] max {plan.budget.get('max_tasks')} tasks")


# --- Phase 5 CLI Commands ---

@app.command("research")
def list_research_jobs():
    """List pending and completed research jobs."""
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    jobs = db.fetchall("SELECT * FROM research_jobs ORDER BY created_at DESC LIMIT 20")
    
    table = Table(title="Recent Research Jobs")
    table.add_column("ID", style="cyan")
    table.add_column("Agent")
    table.add_column("Topic")
    table.add_column("Status")
    
    for j in jobs:
        table.add_row(j["research_id"][:8], j["agent_id"], j["topic"], j["status"])
    console.print(table)

@app.command("skills")
def list_skills():
    """List agent skills and capability levels."""
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    skills = db.fetchall("SELECT * FROM skills ORDER BY agent_name ASC")
    
    table = Table(title="Agent Skills")
    table.add_column("Agent", style="cyan")
    table.add_column("Skill")
    table.add_column("Level")
    table.add_column("Confidence")
    
    for s in skills:
        table.add_row(s["agent_name"], s["skill_name"], s["capability_level"], f"{s['confidence']:.2f}")
    console.print(table)

@app.command("skill-gaps")
def list_skill_gaps():
    """List identified skill gaps from failed executions."""
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    gaps = db.fetchall("SELECT * FROM skill_gaps ORDER BY created_at DESC")
    
    table = Table(title="Skill Gaps")
    table.add_column("ID", style="cyan")
    table.add_column("Skill")
    table.add_column("Severity")
    table.add_column("Status")
    
    for g in gaps:
        table.add_row(g["skill_gap_id"][:8], g["skill_id"], g["severity"], g["status"])
    console.print(table)

@app.command("benchmarks")
def list_benchmarks():
    """List benchmark results for skill practice."""
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    benchmarks = db.fetchall("SELECT * FROM benchmarks ORDER BY timestamp DESC LIMIT 20")
    
    table = Table(title="Recent Benchmarks")
    table.add_column("ID", style="cyan")
    table.add_column("Agent/Skill")
    table.add_column("Candidate Score")
    table.add_column("Baseline")
    
    for b in benchmarks:
        table.add_row(b["benchmark_id"][:8], f"{b['agent_id']}/{b['skill_id']}", f"{b['candidate_score']:.2f}", f"{b['baseline_score']:.2f}")
    console.print(table)

@evolution_app.command("ls")
def evolution_ls():
    """List evolution proposals."""
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    proposals = db.fetchall("SELECT * FROM evolution_proposals ORDER BY created_at DESC")
    
    table = Table(title="Evolution Proposals")
    table.add_column("ID", style="cyan")
    table.add_column("Target Type")
    table.add_column("Target ID")
    table.add_column("Risk")
    table.add_column("Status")
    
    for p in proposals:
        table.add_row(p["proposal_id"][:8], p["target_type"], p["target_id"], p["risk"], p["status"])
    console.print(table)

@evolution_app.command("deploy")
def evolution_deploy(proposal_id: str, shadow: bool = False, canary: bool = False, full: bool = False):
    """Deploy an evolution proposal."""
    from evoforge.evolution.pipeline import EvolutionPipeline
    from evoforge.learning.models import ApprovalPolicy
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    # Instantiate with dummies for CLI action since we only call deploy
    pipeline = EvolutionPipeline(db, None, None, ApprovalPolicy(risk_level="LOW", requires_human=True, minimum_samples=3, minimum_improvement=0.05, maximum_regression=0.0))
    
    # Check proposal exists
    rows = db.fetchall("SELECT * FROM evolution_proposals WHERE proposal_id LIKE ? || '%'", (proposal_id,))
    if not rows:
        console.print(f"[red]Proposal starting with '{proposal_id}' not found.[/red]")
        return
        
    full_id = rows[0]["proposal_id"]
    from evoforge.learning.models import EvolutionProposal
    # Build dummy proposal object just for state check
    prop = EvolutionProposal(proposal_id=full_id, target_type=rows[0]["target_type"], target_id=rows[0]["target_id"], description="", status=rows[0]["status"], hypothesis={"current_behavior": "", "observed_weakness": "", "proposed_change": "", "expected_improvement": "", "risk": "", "benchmark": "", "acceptance_threshold": ""})
    
    mode = "FULL"
    if shadow: mode = "SHADOW"
    elif canary: mode = "CANARY"
    
    try:
        pipeline.deploy_candidate(prop, deployment_type=mode)
        console.print(f"[green]Successfully deployed {full_id} as {mode}.[/green]")
    except Exception as e:
        console.print(f"[red]Deployment failed: {e!s}[/red]")

@evolution_app.command("rollback")
def evolution_rollback(proposal_id: str):
    """Roll back a deployed evolution proposal."""
    from evoforge.evolution.rollback import RollbackManager
    from evoforge.learning.skill_registry import SkillRegistry
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    
    # Find full ID
    rows = db.fetchall("SELECT * FROM evolution_proposals WHERE proposal_id LIKE ? || '%'", (proposal_id,))
    if not rows:
        console.print(f"[red]Proposal starting with '{proposal_id}' not found.[/red]")
        return
    full_id = rows[0]["proposal_id"]
    
    # We need a SkillRegistry for rollback manager
    # Agents are loaded with skills internally in this mockup
    registry = SkillRegistry(db) 
    manager = RollbackManager(db, registry)
    
    if manager.rollback_proposal(full_id):
        console.print(f"[green]Successfully rolled back {full_id}.[/green]")
    else:
        console.print(f"[red]Failed to roll back {full_id}.[/red]")

@app.command("compute-status")
def compute_status():
    """Show current compute execution mode and settings."""
    from evoforge.memory.database import Database
    from evoforge.model_router.compute_policy import ComputePolicy
    from evoforge.model_router.executors import create_default_executor_registry
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    policy = ComputePolicy.load_from_db(db)
    registry = create_default_executor_registry(cfg)
    
    table = Table(title="Compute Mode Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Mode", policy.mode)
    table.add_row("Allow Local", str(policy.allow_local))
    table.add_row("Allow Cloud", str(policy.allow_cloud))
    table.add_row("Prefer Local", str(policy.prefer_local))
    table.add_row("Ollama Configured", str(policy.ollama_enabled))
    if "local" in registry.list_all():
        healthy = registry.is_healthy("local")
        table.add_row("Ollama Live Status", "[green]AVAILABLE[/green]" if healthy else "[red]DEGRADED/UNAVAILABLE[/red]")
    else:
        table.add_row("Ollama Live Status", "[yellow]UNAVAILABLE[/yellow]")
        
    console.print(table)


@app.command("compute-mode")
def compute_mode(mode: str = typer.Argument(..., help="Mode: local, cloud, or hybrid")):
    """Set the system compute execution mode."""
    mode = mode.upper()
    if mode not in ["LOCAL", "CLOUD", "HYBRID"]:
        console.print(f"[red]Invalid mode '{mode}'. Must be LOCAL, CLOUD, or HYBRID.[/red]")
        raise typer.Exit(code=1)
        
    from evoforge.memory.database import Database
    from evoforge.model_router.compute_policy import ComputePolicy
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    policy = ComputePolicy.load_from_db(db)
    
    policy.mode = mode
    policy.allow_local = mode in ["LOCAL", "HYBRID"]
    policy.allow_cloud = mode in ["CLOUD", "HYBRID"]
    
    policy.save_to_db(db)
    
    console.print(f"[green]Successfully updated compute mode to {mode}.[/green]")
    compute_status()

@app.command("server")
def run_server(
    port: int | None = typer.Option(None, help="Port to bind. Defaults to $PORT or 8000."),
    host: str | None = typer.Option(None, help="Host to bind. Defaults to $HOST or 0.0.0.0."),
):
    """Run the headless control plane API server."""
    import os

    import uvicorn
    resolved_host = host or os.environ.get("HOST") or "0.0.0.0"
    resolved_port = port or int(os.environ.get("PORT", "8000"))
    console.print(f"[green]Starting EvoForge Control Plane on {resolved_host}:{resolved_port}[/green]")
    uvicorn.run("evoforge.api.server:app", host=resolved_host, port=resolved_port, log_level="info")

@app.command("scheduler")
def run_scheduler(interval: int = 3600):
    """Run the headless persistent cloud scheduler."""
    from evoforge.memory.database import Database
    from evoforge.runtime.scheduler import SchedulerEngine
    from evoforge.utils.config import load_config
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    # The actual gh_client and learning_system should ideally be built here, 
    # but for now we pass None or minimal mocks as done in run_daily.
    scheduler = SchedulerEngine(db, None, None)
    
    import signal
    import sys
    
    def signal_handler(sig, frame):
        console.print("[yellow]Stopping scheduler gracefully...[/yellow]")
        scheduler.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    console.print(f"[green]Starting EvoForge Scheduler (tick interval: {interval}s)[/green]")
    scheduler.start(interval_seconds=interval)

@app.command("worker")
def run_worker(type: str = typer.Option("cloud", help="Worker type: cloud or laptop"),
               worker_id: str = typer.Option(None, help="Unique worker ID"),
               control_plane: str = typer.Option("http://127.0.0.1:8000", help="Control Plane URL")):
    """Run a headless worker node."""
    import uuid

    from evoforge.agents.factory import build_agent_registry
    from evoforge.memory.database import Database
    from evoforge.memory.manager import MemoryManager
    from evoforge.model_router.executors import create_default_executor_registry
    from evoforge.model_router.routing import ExecutorRouter
    from evoforge.orchestrator.engine import OrchestratorEngine
    from evoforge.runtime.worker_node import CloudWorkerNode, LaptopWorkerNode
    from evoforge.utils.config import load_config
    
    if not worker_id:
        worker_id = f"worker-{uuid.uuid4().hex[:8]}"
        
    token = _control_plane_token()
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    
    exec_registry = create_default_executor_registry(cfg)
    # For a pure worker, it just executes, but it needs the router for sub-task model routing
    router = ExecutorRouter(exec_registry, MemoryManager(db, ""))
    agent_registry = build_agent_registry(None, None)
    orchestrator = OrchestratorEngine(MemoryManager(db, ""), agent_registry, router)
    
    if type.lower() == "laptop":
        node = LaptopWorkerNode(orchestrator, control_plane, worker_id, token)
    else:
        node = CloudWorkerNode(orchestrator, control_plane, worker_id, token)
        
    import signal
    import sys
    
    def signal_handler(sig, frame):
        console.print("[yellow]Stopping worker gracefully...[/yellow]")
        node.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    console.print(f"[green]Starting {type.upper()} worker ({worker_id}) connecting to {control_plane}...[/green]")
    node.run()

@app.command("worker-status")
def worker_status():
    """Show the status of all registered workers."""
    import httpx
    token = _control_plane_token()
    try:
        resp = httpx.get("http://127.0.0.1:8000/api/workers", headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
        workers = resp.json()
        table = Table(title="Worker Registry Status")
        table.add_column("Worker ID")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Health")
        table.add_column("Workflow")
        
        for w in workers:
            table.add_row(w["worker_id"], w["worker_type"], w["status"], w["health"], w.get("current_workflow_id") or "-")
            
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching worker status: {e}[/red]")

@app.command("worker-drain")
def worker_drain(worker_id: str):
    """Gracefully drain a worker."""
    import httpx
    token = _control_plane_token()
    try:
        resp = httpx.post(f"http://127.0.0.1:8000/api/workers/{worker_id}/drain", headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
        console.print(f"[green]Worker {worker_id} is draining.[/green]")
    except Exception as e:
        console.print(f"[red]Error draining worker: {e}[/red]")
        
@app.command("scheduler-status")
def scheduler_status():
    """Show the status of the cloud scheduler."""
    import httpx
    token = _control_plane_token()
    try:
        resp = httpx.get(
            "http://127.0.0.1:8000/api/scheduler/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        st = resp.json()
        table = Table(title="Scheduler Status")
        for k, v in st.items():
            table.add_row(str(k), str(v))
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error fetching scheduler status: {e}[/red]")

@app.command("runtime-status")
def runtime_status():
    """Show overall runtime status including workers and scheduler."""
    import httpx
    token = _control_plane_token()
    try:
        resp = httpx.get(
            "http://127.0.0.1:8000/api/runtime/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        st = resp.json()
        
        console.print("\n[bold cyan]EvoForge Runtime Status[/bold cyan]")
        console.print(f"Scheduler: {st['scheduler'].get('status', 'UNKNOWN')}")
        console.print(f"Workers Online: {st['workers_online']} / {st['workers_total']}\n")
    except Exception as e:
        console.print(f"[red]Error fetching runtime status: {e}[/red]")

@app.command("runtime-pause")
def runtime_pause():
    """Emergency global pause of the runtime scheduler."""
    from evoforge.memory.database import Database
    from evoforge.runtime.scheduler import SchedulerEngine
    from evoforge.utils.config import load_config
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    sch = SchedulerEngine(db, None, None)
    sch.pause()
    console.print("[yellow]Global Emergency Pause Activated.[/yellow]")

@app.command("runtime-resume")
def runtime_resume():
    """Resume the runtime scheduler."""
    from evoforge.memory.database import Database
    from evoforge.runtime.scheduler import SchedulerEngine
    from evoforge.utils.config import load_config
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    sch = SchedulerEngine(db, None, None)
    sch.resume()
    console.print("[green]Global Emergency Pause Deactivated.[/green]")

if __name__ == "__main__":
    app()

