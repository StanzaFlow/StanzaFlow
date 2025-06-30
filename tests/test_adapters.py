"""Adapter contract tests."""
from pathlib import Path

from stanzaflow.adapters import get_adapter

# Minimal IR for tests
IR_MINIMAL = {
    "ir_version": "0.2",
    "workflow": {
        "title": "UnitTest Flow",
        "agents": [
            {
                "name": "Bot",
                "steps": [
                    {"name": "Hello", "attributes": {"artifact": "out.txt"}}
                ],
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