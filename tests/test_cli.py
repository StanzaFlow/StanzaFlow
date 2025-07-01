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


def test_init_creates_file(tmp_path):
    """`stz init` should scaffold a new file."""
    new_file = tmp_path / "demo.sf.md"
    result = runner.invoke(app, ["init", str(new_file)])
    assert result.exit_code == 0
    assert new_file.exists()
    content = new_file.read_text()
    assert "Workflow:" in content and "Agent:" in content


def test_compile_capability_gaps_without_escapes(tmp_path):
    """Test that compile fails when capability gaps exist and AI escapes are disabled."""
    # Create a workflow with unsupported features
    workflow_content = """# Complex Workflow

## Agent: TestAgent
- Step: TestStep
  branch: some_condition
"""

    workflow_file = tmp_path / "complex.sf.md"
    workflow_file.write_text(workflow_content)

    result = runner.invoke(
        app, ["compile", str(workflow_file), "--target", "langgraph"]
    )

    # Should fail with exit code 2 (configuration error)
    assert result.exit_code == 2
    assert "does not support required features" in result.stdout
    assert "branch" in result.stdout


def test_compile_capability_gaps_with_escapes(tmp_path):
    """Test that compile succeeds when capability gaps exist but AI escapes are enabled."""
    # Create a workflow with unsupported features
    workflow_content = """# Complex Workflow

## Agent: TestAgent
- Step: TestStep
  branch: some_condition
"""

    workflow_file = tmp_path / "complex.sf.md"
    workflow_file.write_text(workflow_content)

    result = runner.invoke(
        app, ["compile", str(workflow_file), "--target", "langgraph", "--ai-escapes"]
    )

    # Should succeed but show AI escapes are enabled
    assert result.exit_code == 0
    assert "Processing AI escapes" in result.stdout


def test_compile_no_capability_gaps(tmp_path):
    """Test that compile succeeds when no capability gaps exist."""
    # Create a simple workflow that LangGraph supports
    workflow_content = """# Simple Workflow

## Agent: TestAgent
- Step: TestStep
  artifact: output.txt
  retry: 3
"""

    workflow_file = tmp_path / "simple.sf.md"
    workflow_file.write_text(workflow_content)

    result = runner.invoke(
        app, ["compile", str(workflow_file), "--target", "langgraph"]
    )

    # Should succeed without any capability warnings
    assert result.exit_code == 0
    assert "Successfully compiled" in result.stdout
    assert "does not support" not in result.stdout
