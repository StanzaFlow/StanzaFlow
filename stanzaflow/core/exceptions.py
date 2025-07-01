"""StanzaFlow exception classes."""

from typing import Any


class StanzaFlowError(Exception):
    """Base exception for all StanzaFlow errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}


class ParseError(StanzaFlowError):
    """Exception raised during parsing of .sf.md files."""

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the parse error.

        Args:
            message: Error message
            line: Line number where error occurred
            column: Column number where error occurred
            context: Additional context information
        """
        super().__init__(message, context)
        self.line = line
        self.column = column


class CompileError(StanzaFlowError):
    """Exception raised during compilation to target runtime."""

    def __init__(
        self,
        message: str,
        target: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the compile error.

        Args:
            message: Error message
            target: Target runtime that failed compilation
            context: Additional context information
        """
        super().__init__(message, context)
        self.target = target


class UnsupportedPattern(CompileError):
    """Exception raised when a pattern cannot be compiled without AI assistance."""

    def __init__(
        self,
        message: str,
        pattern: str,
        target: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the unsupported pattern error.

        Args:
            message: Error message
            pattern: The unsupported pattern/construct
            target: Target runtime
            context: Additional context information
        """
        super().__init__(message, target, context)
        self.pattern = pattern


class UnknownAdapterError(StanzaFlowError):
    """Exception raised when requesting an unknown adapter."""

    def __init__(
        self,
        adapter_name: str,
        available_adapters: list[str],
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the unknown adapter error.

        Args:
            adapter_name: The requested adapter name
            available_adapters: List of available adapter names
            context: Additional context information
        """
        message = f"Unknown adapter '{adapter_name}'. Available adapters: {', '.join(available_adapters)}"
        super().__init__(message, context)
        self.adapter_name = adapter_name
        self.available_adapters = available_adapters


class ValidationError(StanzaFlowError):
    """Raised when IR validation fails with user-friendly path information."""

    def __init__(
        self,
        message: str,
        path: str,
        value: Any = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.path = path
        self.value = value
        self.original_error = original_error

    @classmethod
    def from_jsonschema_error(cls, error: Any) -> "ValidationError":
        """Create ValidationError from jsonschema.ValidationError."""
        # Convert JSONPath to human-readable path
        path_parts = []
        for part in error.absolute_path:
            if isinstance(part, int):
                path_parts.append(f"[{part}]")
            else:
                if path_parts:  # Not the first part
                    path_parts.append(f" → {part}")
                else:
                    path_parts.append(str(part))

        human_path = "".join(path_parts) if path_parts else "root"

        # Create user-friendly message
        if error.validator == "required":
            missing_prop = (
                error.message.split("'")[1] if "'" in error.message else "property"
            )
            message = f"Missing required property '{missing_prop}' at {human_path}"
        elif error.validator == "type":
            expected_type = error.schema.get("type", "unknown")
            message = f"Expected {expected_type} at {human_path}, got {type(error.instance).__name__}"
        elif error.validator == "enum":
            allowed = error.schema.get("enum", [])
            message = f"Invalid value at {human_path}. Allowed values: {', '.join(map(str, allowed))}"
        else:
            message = f"Validation error at {human_path}: {error.message}"

        return cls(
            message=message, path=human_path, value=error.instance, original_error=error
        )
