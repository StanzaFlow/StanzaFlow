"""Tests for IR validation functionality."""

import pytest

from stanzaflow.core.exceptions import ValidationError
from stanzaflow.core.ir import _load_schema, validate_ir


def test_validate_ir_valid():
    """Test that valid IR passes validation."""
    valid_ir = {
        "ir_version": "0.2",
        "workflow": {
            "title": "Test Workflow",
            "agents": [
                {
                    "name": "TestAgent",
                    "steps": [
                        {
                            "name": "TestStep",
                            "attributes": {
                                "artifact": "output.txt",
                                "retry": 3,
                                "timeout": 30,
                            },
                        }
                    ],
                }
            ],
        },
    }

    # Should not raise any exception
    validate_ir(valid_ir)


def test_validate_ir_minimal():
    """Test that minimal valid IR passes validation."""
    minimal_ir = {
        "ir_version": "0.2",
        "workflow": {"title": "Minimal Workflow", "agents": []},
    }

    # Should not raise any exception
    validate_ir(minimal_ir)


def test_validate_ir_missing_version():
    """Test that IR without version fails validation."""
    invalid_ir = {"workflow": {"title": "Test Workflow", "agents": []}}

    with pytest.raises(ValidationError) as exc_info:
        validate_ir(invalid_ir)

    assert "ir_version" in str(exc_info.value)
    assert "required" in str(exc_info.value).lower()


def test_validate_ir_wrong_version():
    """Test that IR with wrong version fails validation."""
    invalid_ir = {
        "ir_version": "0.1",
        "workflow": {"title": "Test Workflow", "agents": []},
    }

    with pytest.raises(ValidationError) as exc_info:
        validate_ir(invalid_ir)

    assert "0.2" in str(exc_info.value)


def test_validate_ir_missing_workflow():
    """Test that IR without workflow fails validation."""
    invalid_ir = {"ir_version": "0.2"}

    with pytest.raises(ValidationError) as exc_info:
        validate_ir(invalid_ir)

    assert "workflow" in str(exc_info.value)
    assert "required" in str(exc_info.value).lower()


def test_validate_ir_invalid_step_attributes():
    """Test that invalid step attributes fail validation."""
    invalid_ir = {
        "ir_version": "0.2",
        "workflow": {
            "title": "Test Workflow",
            "agents": [
                {
                    "name": "TestAgent",
                    "steps": [
                        {
                            "name": "TestStep",
                            "attributes": {"invalid_attr": "should not be allowed"},
                        }
                    ],
                }
            ],
        },
    }

    with pytest.raises(ValidationError) as exc_info:
        validate_ir(invalid_ir)

    assert "invalid_attr" in str(exc_info.value)
    assert "not allowed" in str(exc_info.value).lower()


def test_validation_error_properties():
    """Test that ValidationError has proper properties."""
    invalid_ir = {"ir_version": "0.2"}

    with pytest.raises(ValidationError) as exc_info:
        validate_ir(invalid_ir)

    error = exc_info.value
    assert hasattr(error, "path")
    assert hasattr(error, "value")
    assert hasattr(error, "original_error")
    assert error.path == "root"


def test_schema_loading_fallback():
    """Test that schema loading falls back to file system when package resources fail."""
    from unittest.mock import MagicMock, patch

    # Mock importlib.resources to fail
    with patch("stanzaflow.core.ir._files") as mock_files:
        mock_files.side_effect = ModuleNotFoundError("Package not found")

        # Create a mock schema file content
        mock_schema_content = '{"type": "object", "required": ["ir_version"]}'

        # Mock the fallback file path
        with patch("stanzaflow.core.ir.Path") as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path_class.return_value.resolve.return_value.parent.parent.parent.__truediv__.return_value = (
                mock_path
            )

            with patch("builtins.open", create=True) as mock_open:
                mock_file = MagicMock()
                mock_file.read.return_value = mock_schema_content
                mock_open.return_value.__enter__.return_value = mock_file

                # Force reload of schema cache
                import stanzaflow.core.ir

                stanzaflow.core.ir._SCHEMA_CACHE = None

                # This should trigger the fallback path
                validator = _load_schema()
                assert validator is not None
