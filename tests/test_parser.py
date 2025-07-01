"""Test parser and compiler functionality."""

import json
from pathlib import Path

import pytest

from stanzaflow.core.ast import StanzaFlowCompiler
from stanzaflow.core.exceptions import ParseError


class TestStanzaFlowCompiler:
    """Test StanzaFlow compiler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.compiler = StanzaFlowCompiler()
        self.fixture_dir = Path(__file__).parent / "fixtures"

    def test_parse_ticket_triage_fixture(self):
        """Test parsing the ticket triage fixture."""
        fixture_path = self.fixture_dir / "ticket_triage.sf.md"
        workflow = self.compiler.parse_file(fixture_path)

        # Check workflow title
        assert workflow.title == "Workflow: Ticket Triage"

        # Check agents
        assert len(workflow.agents) == 2

        # Check Bot agent
        bot = workflow.agents[0]
        assert bot.name == "Bot"
        assert len(bot.steps) == 2

        # Check Bot steps
        hello_step = bot.steps[0]
        assert hello_step.name == "Hello"
        assert len(hello_step.attributes) == 2

        artifact_attr = hello_step.get_attribute("artifact")
        assert artifact_attr is not None
        assert artifact_attr.value == "hello.txt"

        timeout_attr = hello_step.get_attribute("timeout")
        assert timeout_attr is not None
        assert timeout_attr.value == 30

        analyze_step = bot.steps[1]
        assert analyze_step.name == "Analyze ticket"
        assert len(analyze_step.attributes) == 3

        # Check Human agent
        human = workflow.agents[1]
        assert human.name == "Human"
        assert len(human.steps) == 1

        review_step = human.steps[0]
        assert review_step.name == "Review analysis"
        assert len(review_step.attributes) == 2

        artifact_attr = review_step.get_attribute("artifact")
        assert artifact_attr is not None
        assert artifact_attr.value == "review.md"

        finally_attr = review_step.get_attribute("finally")
        assert finally_attr is not None
        assert finally_attr.value == "cleanup"

    def test_compile_to_ir(self):
        """Test compilation to IR format."""
        fixture_path = self.fixture_dir / "ticket_triage.sf.md"
        ir = self.compiler.compile_file(fixture_path)

        # Check IR structure
        assert ir["ir_version"] == "0.2"
        assert "workflow" in ir

        workflow = ir["workflow"]
        assert workflow["title"] == "Workflow: Ticket Triage"
        assert len(workflow["agents"]) == 2
        assert len(workflow["escape_blocks"]) == 0
        assert len(workflow["secrets"]) == 0

        # Check Bot agent in IR
        bot_ir = workflow["agents"][0]
        assert bot_ir["name"] == "Bot"
        assert len(bot_ir["steps"]) == 2

        hello_ir = bot_ir["steps"][0]
        assert hello_ir["name"] == "Hello"
        assert hello_ir["attributes"]["artifact"] == "hello.txt"
        assert hello_ir["attributes"]["timeout"] == 30

    def test_golden_fixture_match(self):
        """Test that compiled IR matches golden fixture."""
        fixture_path = self.fixture_dir / "ticket_triage.sf.md"
        golden_path = self.fixture_dir / "ticket_triage.ir.json"

        # Compile to IR
        compiled_ir = self.compiler.compile_file(fixture_path)

        # Load golden IR
        with open(golden_path) as f:
            golden_ir = json.load(f)

        # Compare
        assert compiled_ir == golden_ir

    def test_parse_string(self):
        """Test parsing from string."""
        content = """# Test Workflow

## Agent: TestBot
- Step: Test step
  artifact: test.txt
"""
        workflow = self.compiler.parse_string(content)

        assert workflow.title == "Test Workflow"
        assert len(workflow.agents) == 1
        assert workflow.agents[0].name == "TestBot"
        assert len(workflow.agents[0].steps) == 1
        assert workflow.agents[0].steps[0].name == "Test step"

    def test_parse_with_escape_block(self):
        """Test parsing workflow with escape block."""
        content = """# Test Workflow

## Agent: Bot
- Step: Test
  artifact: test.txt

%%escape langgraph
# Custom LangGraph code here
graph.add_node("custom", custom_function)
%%
"""
        workflow = self.compiler.parse_string(content)

        assert len(workflow.escape_blocks) == 1
        escape = workflow.escape_blocks[0]
        assert escape.target == "langgraph"
        assert "Custom LangGraph code" in escape.code

    def test_parse_with_secret(self):
        """Test parsing workflow with secret."""
        content = """# Test Workflow

!env OPENAI_API_KEY

## Agent: Bot
- Step: Test
  artifact: test.txt
"""
        workflow = self.compiler.parse_string(content)

        assert len(workflow.secret_blocks) == 1
        secret = workflow.secret_blocks[0]
        assert secret.env_var == "OPENAI_API_KEY"

    def test_parse_error_handling(self):
        """Test parse error handling."""
        with pytest.raises(ParseError):
            self.compiler.parse_string("Invalid syntax ###")

    def test_missing_file_error(self):
        """Test missing file error."""
        with pytest.raises(ParseError):
            self.compiler.parse_file(Path("nonexistent.sf.md"))

    def test_step_attributes_types(self):
        """Test different step attribute types."""
        content = """# Test Workflow

## Agent: Bot
- Step: Complex step
  artifact: output.json
  retry: 5
  timeout: 120
  on_error: handle_error
  branch: conditional_path
  finally: cleanup_step
"""
        workflow = self.compiler.parse_string(content)
        step = workflow.agents[0].steps[0]

        # Check all attribute types
        assert step.get_attribute("artifact").value == "output.json"
        assert step.get_attribute("retry").value == 5
        assert step.get_attribute("timeout").value == 120
        assert step.get_attribute("on_error").value == "handle_error"
        assert step.get_attribute("branch").value == "conditional_path"
        assert step.get_attribute("finally").value == "cleanup_step"
