"""StanzaFlow adapters for different runtime targets."""

from __future__ import annotations

from .base import Adapter
from .langgraph.adapter import LangGraphAdapter

# Registry of available adapters
_ADAPTERS: dict[str, type[Adapter]] = {
    "langgraph": LangGraphAdapter,
}


def get_adapter(name: str) -> Adapter:
    """Get an adapter instance by name.

    Args:
        name: Name of the adapter

    Returns:
        Adapter instance

    Raises:
        UnknownAdapterError: If adapter name is not recognized
    """
    from stanzaflow.core.exceptions import UnknownAdapterError

    if name not in _ADAPTERS:
        available = list(_ADAPTERS.keys())
        raise UnknownAdapterError(name, available)

    return _ADAPTERS[name]()
