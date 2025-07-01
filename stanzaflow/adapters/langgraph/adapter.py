"""LangGraph adapter implementation using LangGraphEmitter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from stanzaflow.adapters.base import Adapter

from .emit import LangGraphEmitter

__all__ = ["LangGraphAdapter"]


class LangGraphAdapter(Adapter):
    """Compile IR 0.2 to runnable LangGraph Python script."""

    target = "langgraph"

    @property
    def capabilities(self) -> set[str]:
        """Return the set of features this adapter supports."""
        return {
            "agents",
            "steps",
            "artifacts",
            "retry",
            "timeout",
            "secrets",
            # Note: branching, loops, and parallel execution are planned for future releases
        }

    def emit(self, ir: dict[str, Any], output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "workflow.py"
        LangGraphEmitter().emit(ir, output_path)
        return output_path
