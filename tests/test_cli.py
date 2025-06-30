"""Test CLI functionality."""

from pathlib import Path
from typer.testing import CliRunner

from stanzaflow.cli.main import app

runner = CliRunner()


def test_version():
    """Test version command."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "StanzaFlow" in result.stdout


def test_graph_missing_file():
    """Test graph command with missing file."""
    result = runner.invoke(app, ["graph", "nonexistent.sf.md"])
    assert result.exit_code == 1
    assert "does not exist" in result.stdout


def test_graph_existing_file():
    """Test graph command with existing file."""
    fixture_path = Path(__file__).parent / "fixtures" / "simple_workflow_no_attrs.sf.md"
    result = runner.invoke(app, ["graph", str(fixture_path)])
    assert result.exit_code == 0
    assert "Generating graph" in result.stdout


def test_compile_existing_file():
    """Test compile command with existing file."""
    fixture_path = Path(__file__).parent / "fixtures" / "simple_workflow_no_attrs.sf.md"
    result = runner.invoke(app, ["compile", str(fixture_path)])
    assert result.exit_code == 0
    assert "Compiling" in result.stdout


def test_audit_existing_file():
    """Test audit command with existing file."""
    fixture_path = Path(__file__).parent / "fixtures" / "simple_workflow_no_attrs.sf.md"
    result = runner.invoke(app, ["audit", str(fixture_path)])
    assert result.exit_code == 0
    assert "Auditing" in result.stdout 