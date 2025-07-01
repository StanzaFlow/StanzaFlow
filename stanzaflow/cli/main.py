"""Main CLI entry point for StanzaFlow."""

import sys
from pathlib import Path

import typer
from rich.traceback import install

from stanzaflow import __version__
from stanzaflow.console import console
from stanzaflow.core.exceptions import StanzaFlowError

# Install rich traceback handling
install(show_locals=True)

app = typer.Typer(
    name="stanzaflow",
    help="Write workflows the way you write stanzas.",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"StanzaFlow {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
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


def _assert_safe_output(path: Path, force: bool) -> None:
    """Refuse to overwrite *path* unless *force* is True."""
    if path.exists() and not force:
        console.print(f"[red]Error:[/red] File {path} already exists.")
        console.print(
            "💡 Use [bold]--overwrite[/bold] to replace it, or specify a different output path."
        )
        raise typer.Exit(1)


@app.command()
def graph(
    file: Path = typer.Argument(..., help="Path to .sf.md file"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    out_fmt: str = typer.Option(
        "svg", "--format", "-f", help="Output format (svg, png, pdf)"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite if output already exists"
    ),
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
        user_specified = output is not None
        if output is None:
            output = file.with_suffix(f".{out_fmt}")

        if user_specified:
            _assert_safe_output(output, overwrite)

        # Generate graph
        console.print("🎨 Generating graph...")
        success = generate_workflow_graph(ir, output, out_fmt)

        if success:
            console.print(f"✅ [green]Graph saved to:[/green] {output}")
        else:
            console.print("[red]Graph generation failed—no renderer available.[/red]")
            console.print(
                "💡 Install Mermaid CLI (mmdc) or Graphviz to enable graph rendering."
            )
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Graph generation failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def compile(
    file: Path = typer.Argument(..., help="Path to .sf.md file"),
    target: str = typer.Option("langgraph", "--target", "-t", help="Target runtime"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file path"),
    outdir: Path | None = typer.Option(
        None, "--outdir", help="Directory to write artifacts to"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing files"
    ),
    ai_escapes: bool = typer.Option(
        False,
        "--ai-escapes/--no-ai-escapes",
        help="Enable AI auto-patch for unsupported patterns (experimental)",
    ),
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
        workflow_title = ir.get("workflow", {}).get("title", "Untitled Workflow")
        console.print(f"✅ Parsed: {workflow_title}")

        # Validate secrets
        from stanzaflow.core.secrets import validate_secrets
        
        missing_secrets = validate_secrets(ir)
        if missing_secrets:
            console.print(f"[red]Error: Missing required environment variables:[/red]")
            for secret in missing_secrets:
                console.print(f"  ❌ {secret}")
            console.print("\n[yellow]Solution:[/yellow]")
            console.print("  Set the missing environment variables before compiling:")
            for secret in missing_secrets:
                console.print(f"    export {secret}=your_value_here")
            raise typer.Exit(2)

        # Determine output path
        user_specified = output is not None
        if output is None:
            dest_dir = outdir or file.parent
            output = dest_dir / f"{file.stem}.{target}.py"

        if user_specified:
            _assert_safe_output(output, overwrite)

        from stanzaflow.adapters import get_adapter

        adapter = get_adapter(target)

        # Check capability gaps
        capability_gaps = adapter.get_capability_gaps(ir)
        if capability_gaps and not ai_escapes:
            console.print(
                f"[red]Error: Adapter '{target}' does not support required features:[/red]"
            )
            for gap in sorted(capability_gaps):
                console.print(f"  ❌ {gap}")
            console.print("\n[yellow]Solutions:[/yellow]")
            console.print(
                "  • Enable AI escapes: [bold]--ai-escapes[/bold] (experimental)"
            )
            console.print("  • Use a different adapter that supports these features")
            console.print("  • Simplify your workflow to avoid unsupported patterns")
            raise typer.Exit(2)

        # Process AI escapes if enabled
        if ai_escapes:
            console.print(f"[blue]Processing AI escapes with model:[/blue] {model}")
            from stanzaflow.core.ai_escape import process_ai_escapes
            
            try:
                ir = process_ai_escapes(ir, model)
                console.print("✅ AI escapes processed")
            except Exception as e:
                console.print(f"[red]AI escape processing failed:[/red] {e}")
                raise typer.Exit(1)

        console.print(f"🔧 Generating {target} code…")
        entry_file = adapter.emit(ir, output.parent if output else Path.cwd())
        # If user supplied explicit output path ending with .py we move/rename
        if output and output.suffix == ".py" and output != entry_file:
            entry_file.rename(output)
            entry_file = output

        console.print(f"✅ [green]Successfully compiled to:[/green] {output}")

    except Exception as e:
        from stanzaflow.core.exceptions import UnknownAdapterError

        if isinstance(e, UnknownAdapterError):
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(2)  # Use exit code 2 for configuration errors
        elif isinstance(e, typer.Exit):
            # Let typer.Exit propagate with its intended exit code
            raise
        else:
            console.print(f"[red]Compilation failed:[/red] {e}")
            raise typer.Exit(1)


@app.command()
def audit(
    file: Path = typer.Argument(..., help="Path to .sf.md file"),
    target: str = typer.Option(
        "langgraph", "--target", "-t", help="Target adapter to audit against"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed audit information"
    ),
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
            console.print(
                f"\n[yellow]Found {len(audit_results['issues'])} issues:[/yellow]"
            )
            for issue in audit_results["issues"]:
                icon = "⚠️" if issue["severity"] == "warning" else "❌"
                console.print(
                    f"  {icon} [{issue['severity'].upper()}] {issue['message']}"
                )
                if verbose and issue.get("details"):
                    console.print(f"    💡 {issue['details']}")

        if audit_results["todos"]:
            console.print(
                f"\n[blue]Found {len(audit_results['todos'])} TODOs/escapes needed:[/blue]"
            )
            for todo in audit_results["todos"]:
                console.print(f"  🔄 {todo['type']}: {todo['description']}")
                if verbose and todo.get("location"):
                    console.print(f"    📍 Location: {todo['location']}")

        if audit_results["recommendations"]:
            console.print("\n[green]Recommendations:[/green]")
            for rec in audit_results["recommendations"]:
                console.print(f"  • {rec}")

        # Display statistics and summary
        stats = audit_results.get("statistics", {})
        summary = audit_results.get("summary", {})
        
        if stats and verbose:
            console.print("\n[cyan]📊 Workflow Statistics:[/cyan]")
            console.print(f"  • Agents: {stats.get('agents', 0)}")
            console.print(f"  • Total Steps: {stats.get('total_steps', 0)}")
            console.print(f"  • Average Steps per Agent: {stats.get('avg_steps_per_agent', 0)}")
            console.print(f"  • Secrets: {stats.get('secrets', 0)}")
            console.print(f"  • Escape Blocks: {stats.get('escape_blocks', 0)}")
            console.print(f"  • Complexity: {summary.get('complexity_score', 'unknown')}")
            
            attr_usage = stats.get("attribute_usage", {})
            if attr_usage:
                console.print("  • Attribute Usage:")
                for attr, count in sorted(attr_usage.items()):
                    console.print(f"    - {attr}: {count}")
            
            secret_status = stats.get("secret_status", {})
            if secret_status:
                console.print("  • Secret Status:")
                for env_var, status in sorted(secret_status.items()):
                    console.print(f"    - {env_var}: {status}")

        if summary:
            health = summary.get("health", "unknown")
            health_colors = {
                "excellent": "green",
                "good": "blue", 
                "fair": "yellow",
                "poor": "red",
            }
            health_color = health_colors.get(health, "white")
            
            console.print(f"\n[{health_color}]🏥 Workflow Health: {health.upper()}[/{health_color}]")

        # Summary
        total_issues = len(audit_results["issues"])
        total_todos = len(audit_results["todos"])

        if total_issues == 0 and total_todos == 0:
            console.print("\n✅ [green]Workflow audit passed! No issues found.[/green]")
        else:
            console.print(
                f"\n📊 [yellow]Audit summary: {total_issues} issues, {total_todos} TODOs[/yellow]"
            )

        # Determine exit code based on severity
        has_error = any(
            issue.get("severity") == "error" for issue in audit_results["issues"]
        )
        if has_error:
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Audit failed:[/red] {e}")
        if verbose:
            import traceback

            console.print(f"[red]Details:[/red] {traceback.format_exc()}")
        raise typer.Exit(1)


@app.command()
def init(
    file: Path = typer.Argument(
        Path("workflow.sf.md"), help="Destination .sf.md file to create"
    ),
) -> None:
    """Generate a starter workflow markdown file.

    The template contains one agent and one step plus example attribute lines
    so newcomers can immediately run `stz graph` or `stz compile`.
    """

    if file.exists():
        console.print(f"[red]Error:[/red] File {file} already exists")
        raise typer.Exit(1)

    template = (
        "# Workflow: Hello StanzaFlow\n\n"
        "## Agent: Bot\n"
        "- Step: Greet\n"
        "  artifact: greeting.txt\n"
        "  retry: 3\n"
        "  timeout: 30\n"
    )

    file.write_text(template, encoding="utf-8")
    console.print(f"✅ [green]Created starter workflow:[/green] {file}")
    console.print("Next ➜  stz graph", file)


@app.command()
def docs() -> None:
    """Open documentation or show documentation links."""
    import webbrowser
    
    docs_url = "https://github.com/stanzaflow/stanzaflow#readme"
    
    console.print("[green]📚 StanzaFlow Documentation[/green]")
    console.print(f"   Main docs: {docs_url}")
    console.print("   Spec: docs/spec-v0.md")
    console.print("   Examples: tests/fixtures/")
    
    # Try to open in browser
    try:
        webbrowser.open(docs_url)
        console.print(f"\n✅ Opened {docs_url} in your browser")
    except Exception:
        console.print(f"\n💡 Visit {docs_url} for full documentation")


def cli_main() -> None:
    """Main entry point that handles errors gracefully."""
    try:
        app()
    except typer.Exit:
        # Let typer.Exit propagate with its intended exit code
        raise
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
