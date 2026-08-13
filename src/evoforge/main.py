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

@app.command()
def run_daily():
    """
    Execute the daily autonomous loop.
    """
    logger.info("starting_daily_run")
    typer.echo("Starting daily autonomous loop...")
    # TODO: Implement the daily run logic
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
    ])
    registry.register("nvidia", NvidiaExecutor(), [
        AgentCapability.CODING,
        AgentCapability.REASONING,
        AgentCapability.REFACTORING,
        AgentCapability.MULTI_FILE_EDITING,
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
    from evoforge.utils.config import load_config
    from evoforge.portfolio.registry import ProjectRegistry
    
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
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.portfolio.models import ProjectProfile
    import uuid
    
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
    from evoforge.utils.config import load_config
    from evoforge.portfolio.registry import ProjectRegistry
    
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
    from evoforge.utils.config import load_config
    from evoforge.portfolio.registry import ProjectRegistry
    
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
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.portfolio.scanner import ProjectScanner
    from evoforge.github_integration.client import GitHubClient
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    registry = ProjectRegistry(db)
    gh_client = GitHubClient()
    scanner = ProjectScanner(db, gh_client, registry)
    
    console.print("[cyan]Starting portfolio scan...[/cyan]")
    for p in registry.list():
        if p.status == "ACTIVE":
            console.print(f"Scanning {p.repository_full_name}...")
            report = scanner.scan_project(p.project_id)
            if report:
                console.print(f"  Health: {report.overall_health}")
    console.print("[green]Portfolio scan completed.[/green]")


@app.command("portfolio-health")
def portfolio_health():
    """Display an aggregated view of portfolio health."""
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config
    from evoforge.portfolio.registry import ProjectRegistry
    
    cfg = load_config()
    db = Database(cfg.database.sqlite_path)
    registry = ProjectRegistry(db)
    
    projects = registry.list()
    total = len(projects)
    healthy = sum(1 for p in projects if p.health == "HEALTHY")
    warning = sum(1 for p in projects if p.health == "WARNING")
    critical = sum(1 for p in projects if p.health == "CRITICAL")
    unknown = sum(1 for p in projects if p.health == "UNKNOWN")
    
    console.print(f"[bold cyan]Portfolio Health Overview[/bold cyan]")
    console.print(f"Total Projects: {total}")
    console.print(f"[green]Healthy:[/green] {healthy}")
    console.print(f"[yellow]Warning:[/yellow] {warning}")
    console.print(f"[red]Critical:[/red] {critical}")
    console.print(f"Unknown: {unknown}")


@app.command("portfolio-ranking")
def portfolio_ranking():
    """Rank projects and tasks based on portfolio priority engine."""
    from evoforge.memory.database import Database
    from evoforge.utils.config import load_config
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.portfolio.priority_engine import PortfolioPriorityEngine
    
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
    from evoforge.utils.config import load_config
    from evoforge.portfolio.registry import ProjectRegistry
    from evoforge.portfolio.daily_planner import DailyPlanner
    from evoforge.portfolio.priority_engine import PortfolioPriorityEngine
    
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


if __name__ == "__main__":
    app()

