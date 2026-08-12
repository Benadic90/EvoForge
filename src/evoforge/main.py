import structlog
import typer
from rich.console import Console
from rich.table import Table
from evoforge.agents.factory import build_agent_registry
from evoforge.agents.capabilities import CAPABILITY_REGISTRY, AgentCapability

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
    from evoforge.model_router.executors import ExecutorRegistry, LocalModelExecutor, GeminiExecutor, NvidiaExecutor, AntigravityExecutor
    registry = ExecutorRegistry()
    registry.register("local", LocalModelExecutor(), [AgentCapability.CODING])
    registry.register("gemini", GeminiExecutor(), [AgentCapability.CODING, AgentCapability.REASONING])
    registry.register("nvidia", NvidiaExecutor(), [AgentCapability.CODING, AgentCapability.REASONING])
    registry.register("antigravity", AntigravityExecutor(), [AgentCapability.CODING, AgentCapability.REASONING, AgentCapability.BROWSER, AgentCapability.TERMINAL, AgentCapability.REPO_NAVIGATION])
    
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


@app.command("route-test")
def route_test(task: str):
    """Dry-run the model router for a specific task description."""
    from evoforge.model_router.requirements import TaskRequirements, TaskClassification
    from evoforge.model_router.executors import ExecutorRegistry, LocalModelExecutor, GeminiExecutor, NvidiaExecutor, AntigravityExecutor
    from evoforge.model_router.routing import ExecutorRouter
    
    registry = ExecutorRegistry()
    registry.register("local", LocalModelExecutor(), [AgentCapability.CODING])
    registry.register("gemini", GeminiExecutor(), [AgentCapability.CODING, AgentCapability.REASONING])
    registry.register("nvidia", NvidiaExecutor(), [AgentCapability.CODING, AgentCapability.REASONING])
    registry.register("antigravity", AntigravityExecutor(), [AgentCapability.CODING, AgentCapability.REASONING, AgentCapability.BROWSER, AgentCapability.TERMINAL, AgentCapability.REPO_NAVIGATION, AgentCapability.TESTING, AgentCapability.MULTI_FILE_EDITING])
    
    router = ExecutorRouter(registry)
    
    # Infer capabilities from prompt just for this CLI mock test
    req_caps = [AgentCapability.CODING]
    if "test" in task.lower():
        req_caps.append(AgentCapability.TESTING)
    if "refactor" in task.lower():
        req_caps.append(AgentCapability.MULTI_FILE_EDITING)
    if "repo" in task.lower():
        req_caps.append(AgentCapability.REPO_NAVIGATION)
        
    req = TaskRequirements(
        task_id="test_task",
        task_type=TaskClassification.CODING,
        required_capabilities=req_caps
    )
    
    console.print(f"\n[bold]Task:[/bold] {task}")
    console.print("[bold]Required capabilities:[/bold]")
    for c in req_caps:
        console.print(f"  {c.value}")
    
    try:
        executor, explanation = router.select_executor(req)
        
        console.print("\n[bold]Candidates:[/bold]")
        # We can't easily print all candidates' scores here because select_executor returns the best one.
        # But we can print the rejected ones.
        for rej, reasons in explanation.rejected.items():
            console.print(f"  [red]{rej}[/red] (Rejected)")
        
        console.print(f"\n[bold]Selected:[/bold]\n  [green]{explanation.selected_executor_id}[/green]")
        console.print(f"\n[bold]Reason:[/bold] (Score: {explanation.score:.2f})")
        for reason in explanation.reasons:
            console.print(f"  {reason}")
            
    except RuntimeError as e:
        console.print(f"\n[bold red]Routing Failed:[/bold red] {e}")


if __name__ == "__main__":
    app()
