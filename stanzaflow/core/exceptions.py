"""StanzaFlow exception classes."""

from typing import Any, Optional


class StanzaFlowError(Exception):
    """Base exception for all StanzaFlow errors."""

    def __init__(self, message: str, context: Optional[dict[str, Any]] = None) -> None:
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
        line: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[dict[str, Any]] = None,
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
        target: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
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
        context: Optional[dict[str, Any]] = None,
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