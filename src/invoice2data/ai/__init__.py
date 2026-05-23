"""Optional, opt-in AI augmentation for invoice2data (provider-pluggable).

Deterministic templates remain the default extraction path; nothing here runs
unless explicitly configured (``INVOICE2DATA_AI_PROVIDER`` defaults to ``mock``).
See :mod:`invoice2data.ai.__interface__` for the ``AIProvider`` contract.
"""

from .__interface__ import AIProvider
from .__interface__ import get_provider
from .config import AIConfig
from .config import load_config
from .schema_json import invoice_json_schema


__all__ = [
    "AIConfig",
    "AIProvider",
    "get_provider",
    "invoice_json_schema",
    "load_config",
]
