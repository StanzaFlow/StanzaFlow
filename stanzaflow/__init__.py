"""StanzaFlow: Flow-first AI workflow compiler."""

try:
    from importlib.metadata import version

    __version__ = version("stanzaflow")
except ImportError:
    # Fallback for development installs
    __version__ = "0.0.2-dev"

__author__ = "StanzaFlow Team"
__email__ = "team@stanzaflow.org"
__description__ = "Write workflows the way you write stanzas"

from stanzaflow.core.exceptions import StanzaFlowError

__all__ = ["StanzaFlowError", "__version__"]
