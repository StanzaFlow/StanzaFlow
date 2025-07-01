"""Secret handling for StanzaFlow workflows."""

from __future__ import annotations

import os
from typing import Any


def resolve_secrets(ir: dict[str, Any]) -> dict[str, str]:
    """Resolve secret environment variables from IR.
    
    Args:
        ir: StanzaFlow IR dictionary
        
    Returns:
        Dictionary mapping env_var names to their resolved values
        
    Raises:
        ValueError: If required environment variable is not set
    """
    secrets = {}
    workflow = ir.get("workflow", {})
    secret_blocks = workflow.get("secrets", [])
    
    for secret_block in secret_blocks:
        env_var = secret_block.get("env_var")
        if not env_var:
            continue
            
        value = os.environ.get(env_var)
        if value is None:
            raise ValueError(
                f"Required environment variable '{env_var}' is not set. "
                f"Please set it before compiling the workflow."
            )
        
        secrets[env_var] = value
    
    return secrets


def validate_secrets(ir: dict[str, Any]) -> list[str]:
    """Validate that all required secrets are available.
    
    Args:
        ir: StanzaFlow IR dictionary
        
    Returns:
        List of missing environment variable names
    """
    missing = []
    workflow = ir.get("workflow", {})
    secret_blocks = workflow.get("secrets", [])
    
    for secret_block in secret_blocks:
        env_var = secret_block.get("env_var")
        if env_var and os.environ.get(env_var) is None:
            missing.append(env_var)
    
    return missing


def mask_secret_value(value: str) -> str:
    """Mask a secret value for safe display.
    
    Args:
        value: The secret value to mask
        
    Returns:
        Masked version showing only first 2 and last 2 characters for longer secrets
    """
    if not value:
        return "***"
    
    # For very short secrets, mask completely to avoid revealing too much
    if len(value) < 6:
        return "***"
    
    return f"{value[:2]}***{value[-2:]}"


def get_safe_secrets_summary(ir: dict[str, Any]) -> dict[str, str]:
    """Get a safe summary of secrets for audit/logging purposes.
    
    Args:
        ir: StanzaFlow IR dictionary
        
    Returns:
        Dictionary mapping env_var names to masked status
    """
    secrets = {}
    workflow = ir.get("workflow", {})
    secret_blocks = workflow.get("secrets", [])
    
    for secret_block in secret_blocks:
        env_var = secret_block.get("env_var")
        if not env_var:
            continue
            
        value = os.environ.get(env_var)
        if value is None:
            secrets[env_var] = "NOT_SET"
        else:
            secrets[env_var] = mask_secret_value(value)
    
    return secrets 