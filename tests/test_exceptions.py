"""Test exception classes."""

from stanzaflow.core.exceptions import (
    CompileError,
    ParseError,
    StanzaFlowError,
    UnsupportedPattern,
)


def test_stanzaflow_error():
    """Test base StanzaFlowError."""
    error = StanzaFlowError("test message")
    assert error.message == "test message"
    assert error.context == {}
    assert str(error) == "test message"


def test_stanzaflow_error_with_context():
    """Test StanzaFlowError with context."""
    context = {"file": "test.sf.md", "line": 10}
    error = StanzaFlowError("test message", context)
    assert error.message == "test message"
    assert error.context == context


def test_parse_error():
    """Test ParseError."""
    error = ParseError("syntax error", line=5, column=10)
    assert error.message == "syntax error"
    assert error.line == 5
    assert error.column == 10


def test_compile_error():
    """Test CompileError."""
    error = CompileError("compilation failed", target="langgraph")
    assert error.message == "compilation failed"
    assert error.target == "langgraph"


def test_unsupported_pattern():
    """Test UnsupportedPattern."""
    error = UnsupportedPattern(
        "pattern not supported", pattern="parallel", target="langgraph"
    )
    assert error.message == "pattern not supported"
    assert error.pattern == "parallel"
    assert error.target == "langgraph"
