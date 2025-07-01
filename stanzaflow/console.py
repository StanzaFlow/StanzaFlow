"""Centralized console for StanzaFlow output."""

from rich.console import Console

# Singleton console instance to avoid multiple Live outputs
console = Console()

__all__ = ["console"]
