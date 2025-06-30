"""Package entry point so `python -m stanzaflow` works."""

from stanzaflow.cli.main import app

if __name__ == "__main__":
    # Typer's .__call__ turns CliRunner into main
    app() 