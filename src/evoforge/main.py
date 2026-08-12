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

    
if __name__ == "__main__":
    app()
