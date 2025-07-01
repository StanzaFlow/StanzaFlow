"""Adapter base interface for StanzaFlow runtimes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

__all__ = ["Adapter"]


class Adapter(ABC):
    """Abstract compiler backend.

    Each adapter takes IR 0.2 and produces runnable assets for a
    concrete runtime (LangGraph, PromptFlow, etc.).
    """

    #: canonical lowercase identifier (e.g. ``"langgraph"``)
    target: str = ""

    @property
    def capabilities(self) -> set[str]:
        """Return the set of capabilities this adapter supports.

        Standard capabilities include:
        - "sequential": Sequential workflow execution
        - "parallel": Parallel step execution
        - "branching": Conditional branching
        - "loops": Loop constructs
        - "artifacts": File/data artifacts
        - "retry": Retry logic
        - "timeout": Timeout handling
        - "secrets": Environment variable secrets
        - "ai_escape": AI-assisted code generation
        """
        return {"sequential", "artifacts"}

    @abstractmethod
    def emit(
        self, ir: dict[str, Any], output_dir: Path
    ) -> Path:  # noqa: D401 – verb imperative ok
        """Generate code for *ir* and return path to entry point file."""

    def get_required_features(self, ir: dict[str, Any]) -> set[str]:
        """Determine what features are required by the given IR.
        
        Args:
            ir: StanzaFlow IR dictionary
            
        Returns:
            Set of required feature names
        """
        features = set()
        
        workflow = ir.get("workflow", {})
        agents = workflow.get("agents", [])
        
        # Basic workflow features
        if agents:
            features.add("agents")
            
        # Check for steps
        has_steps = any(agent.get("steps") for agent in agents)
        if has_steps:
            features.add("steps")
            
        # Check for step-level features
        for agent in agents:
            for step in agent.get("steps", []):
                attributes = step.get("attributes", {})
                
                if "artifact" in attributes:
                    features.add("artifacts")
                if "retry" in attributes:
                    features.add("retry")
                if "timeout" in attributes:
                    features.add("timeout")
                if "branch" in attributes:
                    features.add("branch")
                if "parallel" in attributes:
                    features.add("parallel")
        
        # Check for secrets
        if workflow.get("secrets"):
            features.add("secrets")
            
        # Check for escape blocks
        if workflow.get("escape_blocks"):
            features.add("ai_escape")
            
        return features

    def get_capability_gaps(self, ir: dict[str, Any]) -> set[str]:
        """Return features required by IR but not supported by this adapter.

        Args:
            ir: StanzaFlow IR dictionary

        Returns:
            Set of unsupported feature names
        """
        required = self.get_required_features(ir)
        supported = self.capabilities
        return required - supported

    # Future-proof hook
    def supports_ai_escape(self) -> bool:  # pragma: no cover – default impl
        """Return *True* if adapter can receive %%escape blocks."""
        return False
