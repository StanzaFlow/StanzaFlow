"""Adapter contract tests."""

from pathlib import Path

import pytest

from stanzaflow.adapters import get_adapter
from stanzaflow.core.exceptions import UnknownAdapterError

# Minimal IR for tests
IR_MINIMAL = {
    "ir_version": "0.2",
    "workflow": {
        "title": "UnitTest Flow",
        "agents": [
            {
                "name": "Bot",
                "steps": [{"name": "Hello", "attributes": {"artifact": "out.txt"}}],
            }
        ],
    },
}


def test_get_adapter_langgraph():
    """Registry returns correct class instance."""
    adapter = get_adapter("langgraph")
    from stanzaflow.adapters.langgraph.adapter import LangGraphAdapter  # noqa: WPS433

    assert isinstance(adapter, LangGraphAdapter)


def test_langgraph_emit(tmp_path: Path):
    """LangGraph adapter emits valid Python file."""
    adapter = get_adapter("langgraph")
    entry_path = adapter.emit(IR_MINIMAL, tmp_path)

    assert entry_path.exists()
    content = entry_path.read_text()

    # Basic sanity checks
    assert "StateGraph" in content
    assert "def bot_agent(" in content
    assert "create_workflow" in content


def test_unknown_adapter():
    """Test that unknown adapters raise proper exception."""
    with pytest.raises(UnknownAdapterError) as exc_info:
        get_adapter("nonexistent")

    assert "nonexistent" in str(exc_info.value)
    assert "langgraph" in str(exc_info.value)


def test_adapter_capabilities():
    """Test adapter capabilities framework."""
    adapter = get_adapter("langgraph")

    # Test basic capabilities
    capabilities = adapter.capabilities
    assert "agents" in capabilities
    assert "steps" in capabilities
    assert "artifacts" in capabilities
    assert "retry" in capabilities
    assert "timeout" in capabilities
    assert "secrets" in capabilities

    # Test required features analysis
    ir_simple = {
        "ir_version": "0.2",
        "workflow": {
            "title": "Simple",
            "agents": [
                {"name": "Agent", "steps": [{"name": "Step", "attributes": {}}]}
            ],
        },
    }

    required = adapter.get_required_features(ir_simple)
    assert "agents" in required
    assert "steps" in required

    # Test with more complex IR
    ir_complex = {
        "ir_version": "0.2",
        "workflow": {
            "title": "Complex",
            "agents": [
                {
                    "name": "Agent",
                    "steps": [
                        {
                            "name": "Step",
                            "attributes": {"artifact": "test.txt", "branch": "condition"},
                        }
                    ],
                }
            ],
        },
    }

    required_complex = adapter.get_required_features(ir_complex)
    assert "artifacts" in required_complex
    assert "branch" in required_complex

    # Test capability gaps
    gaps = adapter.get_capability_gaps(ir_complex)
    assert "branch" in gaps  # LangGraph doesn't support branching yet
    assert "artifacts" not in gaps


def test_required_features():
    """Test required features analysis."""
    adapter = get_adapter("langgraph")

    ir = {
        "ir_version": "0.2",
        "workflow": {
            "title": "Test Workflow",
            "agents": [
                {
                    "name": "TestAgent",
                    "steps": [
                        {"name": "TestStep", "attributes": {"artifact": "test.txt", "retry": 3}}
                    ],
                }
            ],
        },
    }

    required = adapter.get_required_features(ir)
    assert "agents" in required
    assert "steps" in required
    assert "artifacts" in required
    assert "retry" in required
