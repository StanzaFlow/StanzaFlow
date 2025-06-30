"""LangGraph adapter implementation using LangGraphEmitter."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from stanzaflow.adapters.base import Adapter
from .emit import LangGraphEmitter

__all__ = ["LangGraphAdapter"]


class LangGraphAdapter(Adapter):
    """Compile IR 0.2 to runnable LangGraph Python script."""

    target = "langgraph"

    def emit(self, ir: Dict[str, Any], output_dir: Path) -> Path:  # type: ignore[override]
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "workflow.py"
        LangGraphEmitter().emit(ir, output_path)
        return output_path 