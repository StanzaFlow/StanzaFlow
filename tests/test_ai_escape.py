"""Tests for AI escape functionality."""

from stanzaflow.core.ai_escape import (
    AIEscapeError,
    create_escape_hash,
    process_ai_escapes,
    validate_generated_code,
    cache_escape_result,
    get_cached_escape,
)
import pytest


class TestAIEscape:
    """Test AI escape functionality."""

    def test_process_ai_escapes_no_escapes(self):
        """Test processing IR with no escape blocks."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test",
                "agents": [],
                "escape_blocks": [],
            },
        }

        result = process_ai_escapes(ir, "gpt-4")
        assert result == ir  # Should be unchanged

    def test_process_ai_escapes_with_escapes(self):
        """Test processing IR with escape blocks."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test",
                "agents": [],
                "escape_blocks": [
                    {
                        "target": "langgraph",
                        "code": "# Custom code here\nprint('hello')",
                    }
                ],
            },
        }

        result = process_ai_escapes(ir, "gpt-4")

        # Should modify the escape block
        escape_block = result["workflow"]["escape_blocks"][0]
        assert "AI-generated code (stub)" in escape_block["code"]
        assert "Model: gpt-4" in escape_block["code"]
        assert "Original request: langgraph" in escape_block["code"]
        assert "print('hello')" in escape_block["code"]

    def test_create_escape_hash(self):
        """Test escape hash creation."""
        escape_block1 = {"target": "langgraph", "code": "Some AI escape content"}
        escape_block2 = {"target": "langgraph", "code": "Some AI escape content"}
        
        hash1 = create_escape_hash(escape_block1)
        hash2 = create_escape_hash(escape_block2)
        
        # Same content should produce same hash
        assert hash1 == hash2
        
        # Different content should produce different hash
        escape_block3 = {"target": "langgraph", "code": "Different content"}
        hash3 = create_escape_hash(escape_block3)
        assert hash1 != hash3
        
        # Hash should be reasonable length (SHA-256 truncated to 16 hex chars)
        assert len(hash1) == 16
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_validate_generated_code_valid(self):
        """Test validating valid Python code."""
        code = """
from langgraph.graph import StateGraph

def hello():
    print("Hello, world!")
    return True
"""
        assert validate_generated_code(code, "langgraph") is True

    def test_validate_generated_code_invalid(self):
        """Test validating invalid Python code."""
        code = """
def hello(
    print("Missing closing parenthesis"
"""
        try:
            validate_generated_code(code, "langgraph")
            assert False, "Should have raised AIEscapeError"
        except AIEscapeError as e:
            assert "syntax errors" in str(e)

    def test_escape_hash_consistency(self):
        """Test that escape hashes are consistent across calls."""
        escape_block = {
            "target": "test",
            "code": "example code",
        }

        # Multiple calls should return the same hash
        hashes = [create_escape_hash(escape_block) for _ in range(5)]
        assert all(h == hashes[0] for h in hashes)

    def test_process_escapes_preserves_other_fields(self):
        """Test that processing escapes preserves other IR fields."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test Workflow",
                "agents": [
                    {
                        "name": "TestAgent",
                        "steps": [{"name": "TestStep", "attributes": {}}],
                    }
                ],
                "escape_blocks": [
                    {
                        "target": "langgraph",
                        "code": "test code",
                    }
                ],
                "secrets": [{"env_var": "TEST_SECRET"}],
            },
        }

        result = process_ai_escapes(ir, "gpt-4")

        # Should preserve all other fields
        assert result["ir_version"] == "0.2"
        assert result["workflow"]["title"] == "Test Workflow"
        assert len(result["workflow"]["agents"]) == 1
        assert result["workflow"]["agents"][0]["name"] == "TestAgent"
        assert len(result["workflow"]["secrets"]) == 1
        assert result["workflow"]["secrets"][0]["env_var"] == "TEST_SECRET"

        # Only escape blocks should be modified
        assert len(result["workflow"]["escape_blocks"]) == 1
        assert "AI-generated code (stub)" in result["workflow"]["escape_blocks"][0]["code"]

    def test_validate_generated_code_aliased_imports(self):
        """Test detection of aliased dangerous imports."""
        dangerous_code = """
import subprocess as sp
import os as operating_system
sp.run(['echo', 'hello'])
operating_system.system('ls')
"""
        
        with pytest.raises(AIEscapeError) as exc_info:
            validate_generated_code(dangerous_code, "langgraph")
        
        error_msg = str(exc_info.value)
        assert "Dangerous aliased import" in error_msg or "Dangerous import" in error_msg

    def test_validate_generated_code_suspicious_calls(self):
        """Test detection of suspicious single-letter variable calls."""
        suspicious_code = """
from langgraph.graph import StateGraph
# This pattern might be used to hide dangerous calls
s.system('rm -rf /')
o.popen('dangerous command')
"""
        
        with pytest.raises(AIEscapeError) as exc_info:
            validate_generated_code(suspicious_code, "langgraph")
        
        error_msg = str(exc_info.value)
        assert "Suspicious aliased call" in error_msg

    def test_validate_generated_code_timeout_protection(self):
        """Test that validation has timeout protection."""
        # Create a simple valid code that should pass quickly
        simple_code = """
from langgraph.graph import StateGraph

def simple_function():
    return "hello"
"""
        
        # This should complete well under the 5-second timeout
        assert validate_generated_code(simple_code, "langgraph") is True

    def test_cache_functionality(self):
        """Test AI escape caching functionality."""
        test_hash = "test_hash_123"
        test_code = "# Test generated code"
        
        # Test caching
        cache_escape_result(test_hash, test_code)
        
        # Test retrieval
        cached_code = get_cached_escape(test_hash)
        assert cached_code == test_code
        
        # Test non-existent cache
        non_existent = get_cached_escape("non_existent_hash")
        assert non_existent is None 