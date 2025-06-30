"""Adapter base interface for StanzaFlow runtimes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Union

__all__ = ["Adapter"]


class Adapter(ABC):
    """Abstract compiler backend.

    Each adapter takes IR 0.2 and produces runnable assets for a
    concrete runtime (LangGraph, PromptFlow, etc.).
    """

    #: canonical lowercase identifier (e.g. ``"langgraph"``)
    target: str = ""

    @abstractmethod
    def emit(self, ir: Dict[str, Any], output_dir: Path) -> Path:  # noqa: D401 – verb imperative ok
        """Generate code for *ir* and return path to entry point file."""

    # Future-proof hook
    def supports_ai_escape(self) -> bool:  # pragma: no cover – default impl
        """Return *True* if adapter can receive %%escape blocks."""
        return False 