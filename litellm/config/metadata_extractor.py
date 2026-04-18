"""
Metadata extraction from request headers.

Extracts team_id, user_id, api_key, use_case, and correlation_id from HTTP headers.
"""
from typing import Dict, Optional, Tuple
import re


class MetadataExtractionError(Exception):
    """Raised when required metadata is missing or invalid."""
    pass


def extract_metadata_from_headers(headers: Dict[str, str]) -> Dict[str, Optional[str]]:
    """
    Extract metadata from HTTP request headers.
    
    Args:
        headers: Dictionary of HTTP headers (case-insensitive recommended)
    
    Returns:
        Dictionary with keys: team_id, user_id, api_key, correlation_id, use_case
    
    Raises:
        MetadataExtractionError: If required headers are missing or invalid
    """
    # Normalize header keys to lowercase for lookup
    headers_lower = {k.lower(): v for k, v in headers.items()}
    
    # Extract required headers
    team_id = headers_lower.get('x-team-id', '').strip()
    user_id = headers_lower.get('x-user-id', '').strip()
    api_key = headers_lower.get('x-api-key', '').strip()
    
    # Validate required fields
    if not team_id:
        raise MetadataExtractionError("Missing required header: X-Team-Id")
    if not user_id:
        raise MetadataExtractionError("Missing required header: X-User-Id")
    if not api_key:
        raise MetadataExtractionError("Missing required header: X-Api-Key")
    
    # Validate format (alphanumeric + hyphens for team_id)
    if not re.match(r'^[a-zA-Z0-9_\-]+$', team_id):
        raise MetadataExtractionError("Invalid X-Team-Id format: must be alphanumeric with hyphens/underscores")
    
    # Extract optional headers
    correlation_id = headers_lower.get('x-correlation-id', '').strip() or None
    use_case = headers_lower.get('x-use-case', '').strip() or None
    
    return {
        'team_id': team_id,
        'user_id': user_id,
        'api_key': api_key,
        'correlation_id': correlation_id,
        'use_case': use_case,
    }


def validate_metadata_headers(headers: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Validate that all required metadata headers are present.
    
    Args:
        headers: Dictionary of HTTP headers
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        extract_metadata_from_headers(headers)
        return True, None
    except MetadataExtractionError as e:
        return False, str(e)


__all__ = [
    "extract_metadata_from_headers",
    "validate_metadata_headers",
    "MetadataExtractionError",
]
