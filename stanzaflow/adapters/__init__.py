"""StanzaFlow runtime adapters.""" 

from __future__ import annotations

from typing import Dict, Type

from .base import Adapter

# Import concrete adapters here to auto-register

from .langgraph.adapter import LangGraphAdapter  # noqa: E402

_ADAPTERS: Dict[str, Type[Adapter]] = {
    LangGraphAdapter.target: LangGraphAdapter,
}


def get_adapter(name: str) -> Adapter:
    """Return an adapter instance by *name*.

    Raises:
        ValueError: if *name* is not a supported adapter key.
    """
    key = name.lower()
    cls = _ADAPTERS.get(key)
    if cls is None:
        raise ValueError(f"Unsupported adapter '{name}'. Supported: {list(_ADAPTERS)}")
    return cls() 