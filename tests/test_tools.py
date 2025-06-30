"""Tests for StanzaFlow tools (graph and audit)."""

import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from stanzaflow.tools.graph import generate_workflow_graph, _generate_mermaid_diagram
from stanzaflow.tools.audit import audit_workflow


class TestGraphGeneration:
    """Test graph generation functionality."""
    
    def test_generate_mermaid_diagram_simple(self):
        """Test Mermaid diagram generation for simple workflow."""
        ir = {
            "workflow": {
                "title": "Test Workflow",
                "agents": [
                    {
                        "name": "Bot",
                        "steps": [
                            {"name": "Hello", "attributes": {}},
                            {"name": "Process", "attributes": {"artifact": "output.txt"}}
                        ]
                    },
                    {
                        "name": "Human",
                        "steps": [
                            {"name": "Review", "attributes": {"retry": 3, "timeout": 30}}
                        ]
                    }
                ]
            }
        }
        
        mermaid = _generate_mermaid_diagram(ir)
        
        assert "graph TD" in mermaid
        assert "Test Workflow" in mermaid
        assert "Bot" in mermaid
        assert "Human" in mermaid
        assert "Hello" in mermaid
        assert "Process" in mermaid
        assert "Review" in mermaid
        assert "START([Start])" in mermaid
        assert "END([End])" in mermaid
        assert "output.txt" in mermaid  # Check for the actual file name instead of "artifact"
        assert "retry:3" in mermaid  # Check for the actual retry value
    
    def test_generate_mermaid_diagram_empty(self):
        """Test Mermaid diagram generation for empty workflow."""
        ir = {
            "workflow": {
                "title": "Empty Workflow",
                "agents": []
            }
        }
        
        mermaid = _generate_mermaid_diagram(ir)
        
        assert "graph TD" in mermaid
        assert "Empty Workflow" in mermaid
        assert "START([Start])" in mermaid
        assert "END([End])" in mermaid
        assert "START --> END" in mermaid
    
    def test_generate_workflow_graph_fallback(self, tmp_path, monkeypatch):
        """Test graph generation with all fallbacks."""
        # Reset tool cache before test
        from stanzaflow.tools.graph import _reset_tool_cache
        _reset_tool_cache()
        
        # Mock all external dependencies to be unavailable
        monkeypatch.setattr("stanzaflow.tools.graph.shutil.which", lambda x: None)
        
        ir = {
            "workflow": {
                "title": "Fallback Test",
                "agents": [
                    {"name": "Agent1", "steps": [{"name": "Step1", "attributes": {}}]}
                ]
            }
        }
        
        output_path = tmp_path / "test.svg"
        result = generate_workflow_graph(ir, output_path, "svg")
        
        # Should fall back to text format
        text_file = tmp_path / "test.txt"
        assert text_file.exists()
        content = text_file.read_text()
        assert "Fallback Test" in content
        assert "Agent1" in content
        assert "mermaid" in content
    
    @patch('stanzaflow.tools.graph.shutil.which')
    @patch('stanzaflow.tools.graph.subprocess.run')
    def test_mermaid_cli_success(self, mock_run, mock_which, tmp_path):
        """Test successful Mermaid CLI execution."""
        # Reset tool cache before test
        from stanzaflow.tools.graph import _reset_tool_cache
        _reset_tool_cache()
        
        mock_which.return_value = "/usr/local/bin/mmdc"
        mock_run.return_value = MagicMock()
        
        ir = {"workflow": {"title": "Test", "agents": []}}
        output_path = tmp_path / "test.svg"
        
        from stanzaflow.tools.graph import _try_mermaid_cli
        result = _try_mermaid_cli("graph TD\nA-->B", output_path, "svg")
        
        assert result is True
        assert mock_run.called
    
    @patch('stanzaflow.tools.graph.shutil.which')
    def test_mermaid_cli_unavailable(self, mock_which):
        """Test Mermaid CLI when not available."""
        # Reset tool cache before test
        from stanzaflow.tools.graph import _reset_tool_cache
        _reset_tool_cache()
        
        mock_which.return_value = None
        
        from stanzaflow.tools.graph import _try_mermaid_cli
        result = _try_mermaid_cli("graph TD\nA-->B", Path("test.svg"), "svg")
        
        assert result is False


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
                                "attributes": {}
                            }
                        ]
                    }
                ]
            }
        }
        
        results = audit_workflow(ir, "langgraph", False)
        
        assert "issues" in results
        assert "todos" in results
        assert "recommendations" in results
        # Note: May have some issues (like missing description), but no critical errors
    
    def test_audit_empty_workflow(self):
        """Test auditing an empty workflow."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "",
                "agents": []
            }
        }
        
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
                                    "on_error": "escalate"
                                }
                            }
                        ]
                    }
                ]
            }
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
                        ]
                    }
                ]
            }
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
                            {"name": "", "content": "Test", "attributes": {}}  # Unnamed step
                        ]
                    }
                ]
            }
        }
        
        results = audit_workflow(ir, "langgraph", False)
        
        # Should recommend naming things
        naming_recs = [r for r in results["recommendations"] if "naming" in r]
        assert len(naming_recs) > 0
    
    @patch('stanzaflow.adapters.langgraph.emit.LangGraphEmitter.emit')
    def test_audit_generated_code_todos(self, mock_emit):
        """Test audit detection of TODOs in generated code."""
        # Mock the emit method to write TODO content to a file
        def mock_emit_func(ir, output_path):
            with open(output_path, 'w') as f:
                f.write("""
# Generated code
def test():
    # TODO: implement retry logic
    # FIXME: handle timeout
    pass
""")
        
        mock_emit.side_effect = mock_emit_func
        
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test",
                "agents": [
                    {"name": "Agent", "steps": [{"name": "Step", "attributes": {}}]}
                ]
            }
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
        
        assert emitter._sanitize_name("1Agent") == "_1agent"
        assert emitter._sanitize_name("2Bot") == "_2bot"
        assert emitter._sanitize_name("123Test") == "_123test"
    
    def test_sanitize_special_characters(self):
        """Test sanitizing names with special characters."""
        from stanzaflow.adapters.langgraph.emit import LangGraphEmitter
        
        emitter = LangGraphEmitter()
        
        assert emitter._sanitize_name("Agent@Bot") == "agent_bot"
        assert emitter._sanitize_name("Bot#1") == "bot_1"
        assert emitter._sanitize_name("Test!Agent") == "test_agent"
        assert emitter._sanitize_name("Agent$Bot%") == "agent_bot_" 