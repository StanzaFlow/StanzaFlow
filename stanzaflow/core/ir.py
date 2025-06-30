"""Utilities for working with StanzaFlow IR."""
from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any, Dict

from jsonschema import Draft202012Validator, exceptions

_SCHEMA_CACHE: Draft202012Validator | None = None


def _load_schema() -> Draft202012Validator:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        # Locate schema relative to project root (three levels up from this file)
        schema_path = Path(__file__).resolve().parent.parent.parent / "schemas" / "ir-0.2.json"
        with open(schema_path, "r", encoding="utf-8") as fp:
            schema = json.load(fp)
        _SCHEMA_CACHE = Draft202012Validator(schema)
    return _SCHEMA_CACHE


def validate_ir(ir: Dict[str, Any]) -> None:
    """Validate *ir* dict against bundled JSON Schema.

    Raises:
        jsonschema.exceptions.ValidationError: if IR does not conform.
    """
    validator = _load_schema()
    validator.validate(ir) 