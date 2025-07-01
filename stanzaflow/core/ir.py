"""Utilities for working with StanzaFlow IR."""

from __future__ import annotations

import json
from importlib.resources import files as _files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, exceptions

from stanzaflow.core.exceptions import ValidationError

_SCHEMA_CACHE: Draft202012Validator | None = None


def _load_schema() -> Draft202012Validator:
    """Load and cache the IR JSON schema validator."""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        try:
            # Use importlib.resources for proper package data access
            schema_file = _files("stanzaflow.schemas").joinpath("ir-0.2.json")
            with schema_file.open("r", encoding="utf-8") as fp:
                schema = json.load(fp)
        except (ModuleNotFoundError, FileNotFoundError):
            # Fallback for development/source installs
            fallback_path = (
                Path(__file__).resolve().parent.parent.parent
                / "schemas"
                / "ir-0.2.json"
            )
            if not fallback_path.exists():
                raise FileNotFoundError(
                    "Could not locate ir-0.2.json schema. "
                    "This indicates a packaging issue."
                ) from None
            with open(fallback_path, encoding="utf-8") as fp:
                schema = json.load(fp)

        _SCHEMA_CACHE = Draft202012Validator(schema)
    return _SCHEMA_CACHE


def validate_ir(ir: dict[str, Any]) -> None:
    """Validate *ir* dict against bundled JSON Schema.

    Raises:
        ValidationError: if IR does not conform, with user-friendly error message.
    """
    validator = _load_schema()
    try:
        validator.validate(ir)
    except exceptions.ValidationError as e:
        raise ValidationError.from_jsonschema_error(e) from e
