"""Main CLI entry point for StanzaFlow."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.traceback import install

from stanzaflow import __version__
from stanzaflow.core.exceptions import StanzaFlowError

# Install rich traceback handling
install(show_locals=True)

app = typer.Typer(
    name="stanzaflow",
    help="Write workflows the way you write stanzas.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"StanzaFlow {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """StanzaFlow: Write workflows the way you write stanzas."""
    pass


@app.command()
def graph(
    file: Path = typer.Argument(..., help="Path to .sf.md file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    out_fmt: str = typer.Option("svg", "--format", "-f", help="Output format (svg, png, pdf)"),
) -> None:
    """Generate a visual graph of the workflow."""
    console.print(f"[green]Generating graph for:[/green] {file}")
    
    if not file.exists():
        console.print(f"[red]Error:[/red] File {file} does not exist")
        raise typer.Exit(1)
    
    try:
        from stanzaflow.core.ast import StanzaFlowCompiler
        from stanzaflow.tools.graph import generate_workflow_graph
        
        # Parse workflow to get IR
        compiler = StanzaFlowCompiler()
        console.print("📊 Parsing workflow...")
        ir = compiler.compile_file(file)
        
        # Determine output path
        if not output:
            output = file.with_suffix(f".{out_fmt}")
        
        # Generate graph
        console.print("🎨 Generating graph...")
        success = generate_workflow_graph(ir, output, out_fmt)
        
        if success:
            console.print(f"✅ [green]Graph saved to:[/green] {output}")
        else:
            console.print(f"[red]Graph generation failed—no renderer available.[/red]")
            console.print("💡 Install Mermaid CLI (mmdc) or Graphviz to enable graph rendering.")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Graph generation failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def compile(
    file: Path = typer.Argument(..., help="Path to .sf.md file"),
    target: str = typer.Option("langgraph", "--target", "-t", help="Target runtime"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    ai_escapes: bool = typer.Option(False, "--ai-escapes", help="Enable AI auto-patch"),
    model: str = typer.Option("gpt-4", "--model", help="Model for AI escapes"),
) -> None:
    """Compile workflow to target runtime."""
    console.print(f"[green]Compiling:[/green] {file} → {target}")
    
    if not file.exists():
        console.print(f"[red]Error:[/red] File {file} does not exist")
        raise typer.Exit(1)
    
    try:
        from stanzaflow.core.ast import StanzaFlowCompiler
        
        # Create compiler
        compiler = StanzaFlowCompiler()
        
        # Parse workflow and generate IR
        console.print("📝 Parsing workflow...")
        ir = compiler.compile_file(file)
        workflow_title = ir["workflow"]["title"]
        console.print(f"✅ Parsed: {workflow_title}")
        
        # Determine output path
        if not output:
            output = file.with_suffix(f".{target}.py")
        
        # Compile to target
        if target == "langgraph":
            from stanzaflow.adapters.langgraph.emit import compile_to_langgraph
            console.print("🔧 Generating LangGraph code...")
            compile_to_langgraph(ir, output)
        else:
            console.print(f"[red]Error:[/red] Unsupported target '{target}'. Supported: langgraph")
            raise typer.Exit(1)
        
        console.print(f"✅ [green]Successfully compiled to:[/green] {output}")
        
        if ai_escapes:
            console.print(f"[blue]AI escapes enabled with model:[/blue] {model}")
            console.print("[yellow]Note: AI escapes not yet implemented[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Compilation failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def audit(
    file: Path = typer.Argument(..., help="Path to .sf.md file"),
    target: str = typer.Option("langgraph", "--target", "-t", help="Target adapter to audit against"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed audit information"),
) -> None:
    """Audit workflow for escape usage and patterns."""
    console.print(f"[green]Auditing workflow:[/green] {file}")
    
    if not file.exists():
        console.print(f"[red]Error:[/red] File {file} does not exist")
        raise typer.Exit(1)
    
    try:
        from stanzaflow.core.ast import StanzaFlowCompiler
        from stanzaflow.tools.audit import audit_workflow
        
        # Parse workflow to get IR
        compiler = StanzaFlowCompiler()
        console.print("🔍 Parsing workflow...")
        ir = compiler.compile_file(file)
        
        # Run audit
        console.print(f"🔎 Auditing against {target} adapter...")
        audit_results = audit_workflow(ir, target, verbose)
        
        # Display results
        if audit_results["issues"]:
            console.print(f"\n[yellow]Found {len(audit_results['issues'])} issues:[/yellow]")
            for issue in audit_results["issues"]:
                icon = "⚠️" if issue["severity"] == "warning" else "❌"
                console.print(f"  {icon} [{issue['severity'].upper()}] {issue['message']}")
                if verbose and issue.get("details"):
                    console.print(f"    💡 {issue['details']}")
        
        if audit_results["todos"]:
            console.print(f"\n[blue]Found {len(audit_results['todos'])} TODOs/escapes needed:[/blue]")
            for todo in audit_results["todos"]:
                console.print(f"  🔄 {todo['type']}: {todo['description']}")
                if verbose and todo.get("location"):
                    console.print(f"    📍 Location: {todo['location']}")
        
        if audit_results["recommendations"]:
            console.print(f"\n[green]Recommendations:[/green]")
            for rec in audit_results["recommendations"]:
                console.print(f"  💡 {rec}")
        
        # Summary
        total_issues = len(audit_results["issues"])
        total_todos = len(audit_results["todos"])
        
        if total_issues == 0 and total_todos == 0:
            console.print("\n✅ [green]Workflow audit passed! No issues found.[/green]")
        else:
            console.print(f"\n📊 [yellow]Audit summary: {total_issues} issues, {total_todos} TODOs[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Audit failed:[/red] {e}")
        if verbose:
            import traceback
            console.print(f"[red]Details:[/red] {traceback.format_exc()}")
        raise typer.Exit(1)


def cli_main() -> None:
    """Main entry point that handles errors gracefully."""
    try:
        app()
    except StanzaFlowError as e:
        console.print(f"[red]StanzaFlow Error:[/red] {e.message}")
        if e.context:
            console.print(f"[dim]Context:[/dim] {e.context}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main() 