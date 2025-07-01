"""Tests for secrets handling."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from stanzaflow.core.ast import StanzaFlowCompiler
from stanzaflow.core.secrets import (
    get_safe_secrets_summary,
    mask_secret_value,
    resolve_secrets,
    validate_secrets,
)


class TestSecretsHandling:
    """Test secrets functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.compiler = StanzaFlowCompiler()

    def test_parse_secret_block(self):
        """Test parsing workflow with secret block."""
        content = """# Test Workflow

!env OPENAI_API_KEY

## Agent: Bot
- Step: Test
"""
        workflow = self.compiler.parse_string(content)

        assert len(workflow.secret_blocks) == 1
        secret = workflow.secret_blocks[0]
        assert secret.env_var == "OPENAI_API_KEY"

    def test_multiple_secrets(self):
        """Test parsing workflow with multiple secrets."""
        content = """# Test Workflow

!env OPENAI_API_KEY
!env ANTHROPIC_API_KEY

## Agent: Bot
- Step: Test
"""
        workflow = self.compiler.parse_string(content)

        assert len(workflow.secret_blocks) == 2
        env_vars = [s.env_var for s in workflow.secret_blocks]
        assert "OPENAI_API_KEY" in env_vars
        assert "ANTHROPIC_API_KEY" in env_vars

    def test_resolve_secrets_success(self):
        """Test successful secret resolution."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test",
                "agents": [],
                "secrets": [
                    {"env_var": "TEST_SECRET"},
                    {"env_var": "ANOTHER_SECRET"},
                ],
            },
        }

        with patch.dict(
            os.environ, {"TEST_SECRET": "value1", "ANOTHER_SECRET": "value2"}
        ):
            secrets = resolve_secrets(ir)
            assert secrets == {"TEST_SECRET": "value1", "ANOTHER_SECRET": "value2"}

    def test_resolve_secrets_missing(self):
        """Test secret resolution with missing environment variable."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test",
                "agents": [],
                "secrets": [{"env_var": "MISSING_SECRET"}],
            },
        }

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="MISSING_SECRET"):
                resolve_secrets(ir)

    def test_validate_secrets_success(self):
        """Test secret validation with all secrets present."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test",
                "agents": [],
                "secrets": [{"env_var": "PRESENT_SECRET"}],
            },
        }

        with patch.dict(os.environ, {"PRESENT_SECRET": "value"}):
            missing = validate_secrets(ir)
            assert missing == []

    def test_validate_secrets_missing(self):
        """Test secret validation with missing secrets."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test",
                "agents": [],
                "secrets": [
                    {"env_var": "PRESENT_SECRET"},
                    {"env_var": "MISSING_SECRET"},
                ],
            },
        }

        with patch.dict(os.environ, {"PRESENT_SECRET": "value"}, clear=True):
            missing = validate_secrets(ir)
            assert missing == ["MISSING_SECRET"]

    def test_emitter_includes_secrets(self):
        """Test that LangGraph emitter includes secret environment variables."""
        from stanzaflow.adapters.langgraph.emit import LangGraphEmitter

        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test Workflow",
                "agents": [
                    {"name": "Agent", "steps": [{"name": "Step", "attributes": {}}]}
                ],
                "secrets": [
                    {"env_var": "OPENAI_API_KEY"},
                    {"env_var": "ANTHROPIC_API_KEY"},
                ],
            },
        }

        emitter = LangGraphEmitter()
        code_lines = emitter._generate_code(ir)
        code = "\n".join(code_lines)

        # Check that secrets are included
        assert 'OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]' in code
        assert 'ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]' in code
        assert "# Environment variables (secrets)" in code

    def test_emitter_no_secrets(self):
        """Test that emitter works correctly with no secrets."""
        from stanzaflow.adapters.langgraph.emit import LangGraphEmitter

        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test Workflow",
                "agents": [
                    {"name": "Agent", "steps": [{"name": "Step", "attributes": {}}]}
                ],
                "secrets": [],
            },
        }

        emitter = LangGraphEmitter()
        code_lines = emitter._generate_code(ir)
        code = "\n".join(code_lines)

        # Check that no secret-related code is included
        assert "# Environment variables (secrets)" not in code
        assert "os.environ[" not in code

    def test_cli_validates_secrets(self):
        """Test that CLI validates secrets before compilation."""
        import typer

        from stanzaflow.cli.main import compile as cli_compile

        # Create a temporary workflow file with secrets
        content = """# Test Workflow

!env MISSING_SECRET

## Agent: Bot
- Step: Test
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".sf.md", delete=False) as f:
            f.write(content)
            f.flush()
            workflow_path = Path(f.name)

        try:
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(typer.Exit) as exc_info:
                    cli_compile(
                        file=workflow_path,
                        target="langgraph",
                        output=None,
                        outdir=None,
                        overwrite=False,
                        ai_escapes=False,
                        model="gpt-4",
                    )
                # Should exit with code 2 for configuration errors
                assert exc_info.value.exit_code == 2
        finally:
            workflow_path.unlink()

    def test_end_to_end_with_secrets(self):
        """Test end-to-end compilation with secrets."""
        from stanzaflow.adapters.langgraph.emit import LangGraphEmitter

        content = """# Test Workflow

!env TEST_API_KEY

## Agent: Bot
- Step: Process
  artifact: result.txt
"""

        with patch.dict(os.environ, {"TEST_API_KEY": "secret_value"}):
            # Parse and compile
            workflow = self.compiler.parse_string(content)
            ir = self.compiler.workflow_to_ir(workflow)

            # Validate secrets are resolved
            secrets = resolve_secrets(ir)
            assert secrets == {"TEST_API_KEY": "secret_value"}

            # Generate code
            emitter = LangGraphEmitter()
            code_lines = emitter._generate_code(ir)
            code = "\n".join(code_lines)

            # Verify the generated code includes the secret
            assert 'TEST_API_KEY = os.environ["TEST_API_KEY"]' in code
            assert "# Environment variables (secrets)" in code

    def test_mask_secret_value_edge_cases(self):
        """Test secret masking with various edge cases."""

        # Empty string
        assert mask_secret_value("") == "***"

        # Very short secrets (should be fully masked)
        assert mask_secret_value("a") == "***"
        assert mask_secret_value("ab") == "***"
        assert mask_secret_value("abc") == "***"
        assert mask_secret_value("abcd") == "***"
        assert mask_secret_value("abcde") == "***"

        # Just long enough to show partial
        assert mask_secret_value("abcdef") == "ab***ef"
        assert mask_secret_value("1234567890") == "12***90"

        # Longer secrets
        assert mask_secret_value("sk-1234567890abcdef") == "sk***ef"
        assert mask_secret_value("very_long_secret_token_here") == "ve***re"

    def test_get_safe_secrets_summary(self):
        """Test getting safe secrets summary for audit purposes."""
        import os

        # Test with mixed secret states
        ir = {
            "workflow": {
                "secrets": [
                    {"env_var": "EXISTING_SECRET"},
                    {"env_var": "MISSING_SECRET"},
                    {"env_var": "SHORT_SECRET"},
                ]
            }
        }

        # Set up test environment
        os.environ["EXISTING_SECRET"] = "sk-1234567890abcdef"
        os.environ["SHORT_SECRET"] = "abc"
        if "MISSING_SECRET" in os.environ:
            del os.environ["MISSING_SECRET"]

        try:
            summary = get_safe_secrets_summary(ir)

            assert summary["EXISTING_SECRET"] == "sk***ef"
            assert summary["SHORT_SECRET"] == "***"  # Short secret fully masked
            assert summary["MISSING_SECRET"] == "NOT_SET"

        finally:
            # Clean up
            if "EXISTING_SECRET" in os.environ:
                del os.environ["EXISTING_SECRET"]
            if "SHORT_SECRET" in os.environ:
                del os.environ["SHORT_SECRET"]
