"""
Correlation ID generation and validation.

Generates UUID v4 correlation IDs if not provided by client, validates format.
"""
import uuid
from typing import Optional


def generate_correlation_id() -> str:
    """
    Generate a new UUID v4 correlation ID.
    
    Returns:
        String representation of UUID v4 (lowercase, no braces)
    """
    return str(uuid.uuid4())


def validate_correlation_id(correlation_id: Optional[str]) -> str:
    """
    Validate a correlation ID or generate a new one if missing.
    
    Args:
        correlation_id: String UUID v4 to validate, or None to generate
    
    Returns:
        Valid UUID v4 correlation ID
    
    Raises:
        ValueError: If correlation_id is invalid format
    """
    if not correlation_id:
        return generate_correlation_id()
    
    # Validate UUID format
    try:
        uuid.UUID(correlation_id)
        return str(correlation_id)
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid correlation ID format: {correlation_id}. Must be valid UUID v4.")


def ensure_correlation_id(correlation_id: Optional[str]) -> str:
    """
    Ensure a correlation ID exists, generating if needed.
    
    This is a permissive variant that generates a new ID on invalid format
    instead of raising an exception.
    
    Args:
        correlation_id: String UUID v4 or None
    
    Returns:
        Valid UUID v4 correlation ID
    """
    if not correlation_id:
        return generate_correlation_id()
    
    try:
        uuid.UUID(correlation_id)
        return str(correlation_id)
    except (ValueError, AttributeError):
        # Log and regenerate on invalid format
        return generate_correlation_id()


__all__ = [
    "generate_correlation_id",
    "validate_correlation_id",
    "ensure_correlation_id",
]
