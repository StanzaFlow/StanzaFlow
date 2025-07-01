"""Tests for StanzaFlow tools (graph and audit)."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from stanzaflow.tools.audit import audit_workflow
from stanzaflow.tools.graph import _generate_mermaid_diagram, generate_workflow_graph


class TestGraphGeneration:
    """Test graph generation functionality."""

    def test_generate_mermaid_diagram_simple(self):
        """Test generating a basic Mermaid diagram."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test Workflow",
                "agents": [
                    {"name": "Agent1", "steps": [{"name": "Step1", "attributes": {}}]},
                    {"name": "Agent2", "steps": [{"name": "Step2", "attributes": {}}]},
                ],
            },
        }

        mermaid = _generate_mermaid_diagram(ir)

        assert "graph TD" in mermaid
        assert "Agent1" in mermaid
        assert "Agent2" in mermaid

    def test_generate_mermaid_diagram_empty(self):
        """Test generating Mermaid diagram for empty workflow."""
        ir = {
            "ir_version": "0.2",
            "workflow": {"title": "Empty Workflow", "agents": []},
        }

        mermaid = _generate_mermaid_diagram(ir)

        assert "graph TD" in mermaid
        assert "Empty Workflow" in mermaid

    @pytest.mark.parametrize(
        "mmdc_available,dot_available,expected_renderer",
        [
            (True, True, "mermaid"),
            (False, True, "graphviz"),
            (False, False, "text"),
        ],
    )
    def test_graph_generation_fallback_chain(
        self, tmp_path, monkeypatch, mmdc_available, dot_available, expected_renderer
    ):
        """Test the complete fallback chain: Mermaid → Graphviz → Text."""
        # Reset tool cache before test
        from stanzaflow.tools.graph import _reset_tool_cache

        _reset_tool_cache()

        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Fallback Test",
                "agents": [
                    {
                        "name": "TestAgent",
                        "steps": [{"name": "TestStep", "attributes": {}}],
                    }
                ],
            },
        }

        output_path = tmp_path / "test_graph.svg"

        # Mock tool availability
        def mock_which(tool):
            if tool == "mmdc":
                return "/usr/bin/mmdc" if mmdc_available else None
            elif tool == "dot":
                return "/usr/bin/dot" if dot_available else None
            return None

        # Mock subprocess.run for successful execution
        def mock_run(*args, **kwargs):
            mock_result = MagicMock()

            # Check if this is a version check
            if len(args) > 0 and isinstance(args[0], list):
                cmd = args[0]
                if "-V" in cmd or "--version" in cmd:
                    # Version check - fail if tool not available
                    if "mmdc" in cmd[0] and not mmdc_available:
                        mock_result.returncode = 1
                        raise subprocess.CalledProcessError(1, cmd)
                    elif "dot" in cmd[0] and not dot_available:
                        mock_result.returncode = 1
                        raise subprocess.CalledProcessError(1, cmd)
                    else:
                        mock_result.returncode = 0
                        mock_result.stderr = "graphviz version 2.50.0"
                        mock_result.stdout = "mermaid-cli version 10.6.1"
                        return mock_result

                # Actual rendering command
                if "-o" in cmd:
                    output_idx = cmd.index("-o") + 1
                    if output_idx < len(cmd):
                        output_file = Path(cmd[output_idx])
                        output_file.write_text("dummy content")
                        mock_result.returncode = 0
                        return mock_result

            mock_result.returncode = 0
            return mock_result

        monkeypatch.setattr("stanzaflow.tools.graph.shutil.which", mock_which)
        monkeypatch.setattr("stanzaflow.tools.graph.subprocess.run", mock_run)

        # Generate graph
        success = generate_workflow_graph(ir, output_path, "svg")

        # Should always succeed (even if falling back to text)
        assert success is True

        # Check that some output was created
        if expected_renderer == "text":
            # Text fallback creates a .txt file
            text_file = output_path.with_suffix(".txt")
            assert text_file.exists()
            content = text_file.read_text()
            assert "Fallback Test" in content
            assert "TestAgent" in content
        else:
            # Mermaid/Graphviz should create the requested file
            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_graph_generation_with_special_characters(self, tmp_path):
        """Test graph generation handles special characters in names."""
        # Reset tool cache before test
        from stanzaflow.tools.graph import _reset_tool_cache

        _reset_tool_cache()

        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Special <chars> & symbols",
                "agents": [
                    {
                        "name": "Agent@Home",
                        "steps": [{"name": 'Step "quoted"', "attributes": {}}],
                    }
                ],
            },
        }

        output_path = tmp_path / "special_chars.svg"

        # Mock tools as unavailable to force text fallback
        def mock_which(tool):
            return None

        def mock_run(*args, **kwargs):
            # All subprocess calls should fail to force text fallback
            raise subprocess.CalledProcessError(1, args[0] if args else [])

        with patch("stanzaflow.tools.graph.shutil.which", mock_which):
            with patch("stanzaflow.tools.graph.subprocess.run", mock_run):
                success = generate_workflow_graph(ir, output_path, "svg")

                # Should succeed with text fallback
                assert success is True

                # Should create text file with escaped content
                text_file = output_path.with_suffix(".txt")
                assert text_file.exists()
                content = text_file.read_text()
                assert "Special" in content  # Title should be present
                assert "Agent" in content  # Agent name should be present


class TestAuditFunctionality:
    """Test audit functionality."""

    def test_audit_simple_workflow(self):
        """Test auditing a simple, valid workflow."""
        ir = {
            "ir_version": "0.2",  # Add required IR version
            "workflow": {
                "title": "Simple Workflow",
                "agents": [
                    {
                        "name": "TestAgent",
                        "steps": [
                            {
                                "name": "TestStep",
                                "content": "Do something",
                                "attributes": {},
                            }
                        ],
                    }
                ],
            },
        }

        results = audit_workflow(ir, "langgraph", False)

        assert "issues" in results
        assert "todos" in results
        assert "recommendations" in results
        # Note: May have some issues (like missing description), but no critical errors

    def test_audit_empty_workflow(self):
        """Test auditing an empty workflow."""
        ir = {"ir_version": "0.2", "workflow": {"title": "", "agents": []}}

        results = audit_workflow(ir, "langgraph", False)

        # Should find issues
        assert len(results["issues"]) > 0

        # Should find missing title
        title_issues = [i for i in results["issues"] if "title" in i["message"]]
        assert len(title_issues) > 0

        # Should find no agents
        agent_issues = [i for i in results["issues"] if "no agents" in i["message"]]
        assert len(agent_issues) > 0

    def test_audit_workflow_with_attributes(self):
        """Test auditing workflow with unsupported attributes."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Complex Workflow",
                "agents": [
                    {
                        "name": "ComplexAgent",
                        "steps": [
                            {
                                "name": "ComplexStep",
                                "content": "Do complex things",
                                "attributes": {
                                    "retry": 3,
                                    "timeout": 30,
                                    "on_error": "escalate",
                                },
                            }
                        ],
                    }
                ],
            },
        }

        results = audit_workflow(ir, "langgraph", False)

        # Should identify TODO items for retry and timeout
        todo_types = [todo["type"] for todo in results["todos"]]
        assert "Retry Logic" in todo_types
        assert "Timeout Handling" in todo_types

    def test_audit_verbose_mode(self):
        """Test audit in verbose mode."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test Workflow",
                "agents": [
                    {
                        "name": "Agent",
                        "steps": [
                            {"name": "Step", "content": "Test", "attributes": {}}
                        ],
                    }
                ],
            },
        }

        results = audit_workflow(ir, "langgraph", True)

        # Should generate recommendations
        assert len(results["recommendations"]) > 0

    def test_audit_recommendations(self):
        """Test audit recommendation generation."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test Workflow",
                "agents": [
                    {
                        "name": "",  # Unnamed agent
                        "steps": [
                            {
                                "name": "",
                                "content": "Test",
                                "attributes": {},
                            }  # Unnamed step
                        ],
                    }
                ],
            },
        }

        results = audit_workflow(ir, "langgraph", False)

        # Should recommend naming things
        naming_recs = [r for r in results["recommendations"] if "naming" in r]
        assert len(naming_recs) > 0

    @patch("stanzaflow.adapters.langgraph.emit.LangGraphEmitter.emit")
    def test_audit_generated_code_todos(self, mock_emit):
        """Test audit detection of TODOs in generated code."""

        # Mock the emit method to write TODO content to a file
        def mock_emit_func(ir, output_path):
            with open(output_path, "w") as f:
                f.write(
                    """
# Generated code
def test():
    # TODO: implement retry logic
    # FIXME: handle timeout
    pass
"""
                )

        mock_emit.side_effect = mock_emit_func

        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test",
                "agents": [
                    {"name": "Agent", "steps": [{"name": "Step", "attributes": {}}]}
                ],
            },
        }

        results = audit_workflow(ir, "langgraph", True)

        # Should detect TODO items in generated code
        todo_items = [t for t in results["todos"] if "Generated Code" in t["type"]]
        assert len(todo_items) >= 1


class TestSanitizeName:
    """Test name sanitization for Python identifiers."""

    def test_sanitize_normal_names(self):
        """Test sanitizing normal agent names."""
        from stanzaflow.adapters.langgraph.emit import LangGraphEmitter

        emitter = LangGraphEmitter()

        assert emitter._sanitize_name("Agent") == "agent"
        assert emitter._sanitize_name("Bot Agent") == "bot_agent"
        assert emitter._sanitize_name("Agent-1") == "agent_1"
        assert emitter._sanitize_name("Complex/Name") == "complex_name"

    def test_sanitize_names_starting_with_digits(self):
        """Test sanitizing names that start with digits."""
        from stanzaflow.adapters.langgraph.emit import LangGraphEmitter

        emitter = LangGraphEmitter()

        assert emitter._sanitize_name("1Agent") == "item_1agent"
        assert emitter._sanitize_name("1Agent", "agent") == "agent_1agent"
        assert emitter._sanitize_name("2Bot") == "item_2bot"
        assert emitter._sanitize_name("123Test") == "item_123test"

    def test_sanitize_special_characters(self):
        """Test sanitizing names with special characters."""
        from stanzaflow.adapters.langgraph.emit import LangGraphEmitter

        emitter = LangGraphEmitter()

        assert emitter._sanitize_name("Agent@Bot") == "agent_bot"
        assert emitter._sanitize_name("Bot#1") == "bot_1"
        assert emitter._sanitize_name("Test!Agent") == "test_agent"
        assert emitter._sanitize_name("Agent$Bot%") == "agent_bot_"
