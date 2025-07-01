"""AI escape functionality for StanzaFlow workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class AIEscapeError(Exception):
    """Raised when AI escape processing fails."""

    pass


def process_ai_escapes(ir: dict[str, Any], model: str = "gpt-4") -> dict[str, Any]:
    """Process AI escapes in workflow IR.

    This is a stub implementation that will be expanded with actual AI functionality.

    Args:
        ir: StanzaFlow IR dictionary
        model: Model to use for AI processing

    Returns:
        Modified IR with AI escapes processed

    Raises:
        AIEscapeError: If AI processing fails
    """
    # For now, just return the IR unchanged with a warning
    # TODO: Implement actual AI escape processing using LiteLLM

    workflow = ir.get("workflow", {})
    escape_blocks = workflow.get("escape_blocks", [])

    if escape_blocks:
        # In the future, this would:
        # 1. Analyze the escape blocks
        # 2. Use LiteLLM to generate appropriate code
        # 3. Validate the generated code in a sandbox
        # 4. Cache the results

        # For now, just add a comment to the escape blocks
        for escape_block in escape_blocks:
            original_code = escape_block.get("code", "")
            escape_block[
                "code"
            ] = f"""# AI-generated code (stub)
# Model: {model}
# Original request: {escape_block.get('target', 'unknown')}

{original_code}

# TODO: Replace with actual AI-generated implementation
"""

    return ir


def cache_escape_result(escape_hash: str, generated_code: str) -> None:
    """Cache an AI escape result for future use.

    Args:
        escape_hash: Hash of the escape block for cache key
        generated_code: The generated code to cache
    """
    import platformdirs

    cache_dir = Path(platformdirs.user_cache_dir("stanzaflow")) / "escapes"
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / f"{escape_hash}.py"
    cache_file.write_text(generated_code, encoding="utf-8")


def get_cached_escape(escape_hash: str) -> str | None:
    """Get a cached AI escape result.

    Args:
        escape_hash: Hash of the escape block

    Returns:
        Cached generated code or None if not found
    """
    import platformdirs

    cache_dir = Path(platformdirs.user_cache_dir("stanzaflow")) / "escapes"
    cache_file = cache_dir / f"{escape_hash}.py"

    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")

    return None


def validate_generated_code(code: str, target: str) -> bool:
    """Validate generated code in a sandbox environment.

    Args:
        code: The generated code to validate
        target: Target runtime (e.g., "langgraph")

    Returns:
        True if code is valid and safe

    Raises:
        AIEscapeError: If validation fails
    """
    import ast
    import time

    # Basic syntax checking
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        raise AIEscapeError(f"Generated code has syntax errors: {e}") from e

    # Security checks - scan AST for dangerous operations
    dangerous_nodes = []

    class SecurityVisitor(ast.NodeVisitor):
        def visit_Import(self, node: ast.Import) -> None:
            # Check for dangerous imports
            for alias in node.names:
                if alias.name in {
                    "os",
                    "subprocess",
                    "sys",
                    "importlib",
                    "__builtin__",
                    "builtins",
                }:
                    dangerous_nodes.append(f"Dangerous import: {alias.name}")
                # Check for aliased dangerous imports
                if alias.asname and alias.name in {
                    "os",
                    "subprocess",
                    "sys",
                    "importlib",
                }:
                    dangerous_nodes.append(
                        f"Dangerous aliased import: {alias.name} as {alias.asname}"
                    )

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            # Check for dangerous from imports
            if node.module in {
                "os",
                "subprocess",
                "sys",
                "importlib",
                "__builtin__",
                "builtins",
            }:
                dangerous_nodes.append(f"Dangerous import from: {node.module}")

        def visit_Call(self, node: ast.Call) -> None:
            # Check for dangerous function calls by name
            if isinstance(node.func, ast.Name):
                if node.func.id in {"exec", "eval", "compile", "__import__", "open"}:
                    dangerous_nodes.append(f"Dangerous function call: {node.func.id}")
            # Check for dangerous method calls
            elif isinstance(node.func, ast.Attribute):
                dangerous_methods = {
                    "system",
                    "popen",
                    "spawn",
                    "fork",
                    "execv",
                    "execve",
                    "spawnv",
                }
                if node.func.attr in dangerous_methods:
                    dangerous_nodes.append(f"Dangerous method call: {node.func.attr}")
                # Check for calls on single-letter variables (common alias pattern)
                if (
                    isinstance(node.func.value, ast.Name)
                    and len(node.func.value.id) == 1
                ):
                    if node.func.attr in dangerous_methods:
                        dangerous_nodes.append(
                            f"Suspicious aliased call: {node.func.value.id}.{node.func.attr}"
                        )
            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            # Check for dangerous attribute access
            if (
                isinstance(node.attr, str)
                and node.attr.startswith("__")
                and node.attr.endswith("__")
            ):
                dangerous_nodes.append(f"Dangerous dunder access: {node.attr}")
            self.generic_visit(node)

    # Run security scan with timeout
    start_time = time.time()
    visitor = SecurityVisitor()
    visitor.visit(tree)

    # Check for timeout (basic protection)
    if time.time() - start_time > 5.0:  # 5 second limit for AST analysis
        raise AIEscapeError("Code validation timed out - code too complex")

    if dangerous_nodes:
        raise AIEscapeError(
            f"Generated code contains dangerous operations: {', '.join(dangerous_nodes)}"
        )

    # Additional target-specific validation
    if target == "langgraph":
        # Check for required LangGraph patterns
        has_langgraph_imports = False
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("langgraph")
            ):
                has_langgraph_imports = True
                break
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("langgraph"):
                        has_langgraph_imports = True
                        break
                if has_langgraph_imports:
                    break

        if not has_langgraph_imports:
            raise AIEscapeError(
                "Generated LangGraph code must import langgraph modules"
            )

    return True


def create_escape_hash(escape_block: dict[str, Any]) -> str:
    """Create a hash for an escape block for caching.

    Args:
        escape_block: The escape block dictionary

    Returns:
        Hash string for cache key
    """
    import hashlib

    # Create hash from target and code content
    target = escape_block.get("target", "")
    code = escape_block.get("code", "")
    content = f"{target}:{code}"

    return hashlib.sha256(content.encode()).hexdigest()[:16]
