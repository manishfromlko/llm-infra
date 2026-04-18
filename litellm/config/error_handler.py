"""
Error response handlers for gateway authentication and validation.

Provides standardized error responses for invalid API keys, missing headers, rate limits, etc.
"""
from enum import Enum
from typing import Dict, Any, Tuple


class ErrorCode(Enum):
    """Standard error codes."""
    INVALID_API_KEY = "invalid_api_key"
    MISSING_HEADER = "missing_header"
    INVALID_HEADER = "invalid_header"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    AUTHENTICATION_FAILED = "authentication_failed"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INTERNAL_ERROR = "internal_error"


def create_error_response(
    code: ErrorCode,
    message: str,
    details: Dict[str, Any] = None,
) -> Tuple[int, Dict[str, Any]]:
    """
    Create a standardized error response.
    
    Args:
        code: Error code enum
        message: Human-readable error message
        details: Optional additional details
    
    Returns:
        Tuple of (http_status_code, error_dict)
    """
    status_map = {
        ErrorCode.INVALID_API_KEY: 401,
        ErrorCode.MISSING_HEADER: 400,
        ErrorCode.INVALID_HEADER: 400,
        ErrorCode.RATE_LIMIT_EXCEEDED: 429,
        ErrorCode.AUTHENTICATION_FAILED: 401,
        ErrorCode.SERVICE_UNAVAILABLE: 503,
        ErrorCode.INTERNAL_ERROR: 500,
    }
    
    status_code = status_map.get(code, 500)
    
    error_dict = {
        "error": {
            "code": code.value,
            "message": message,
        }
    }
    
    if details:
        error_dict["error"]["details"] = details
    
    return status_code, error_dict


def error_invalid_api_key(provided_key: str = None) -> Tuple[int, Dict[str, Any]]:
    """Invalid or missing API key."""
    return create_error_response(
        ErrorCode.INVALID_API_KEY,
        "Invalid or missing API key. Provide X-Api-Key header.",
        {"provided_key_length": len(provided_key) if provided_key else 0},
    )


def error_missing_header(header_name: str) -> Tuple[int, Dict[str, Any]]:
    """Missing required header."""
    return create_error_response(
        ErrorCode.MISSING_HEADER,
        f"Missing required header: {header_name}",
        {"header": header_name},
    )


def error_invalid_header(header_name: str, reason: str) -> Tuple[int, Dict[str, Any]]:
    """Invalid header format or value."""
    return create_error_response(
        ErrorCode.INVALID_HEADER,
        f"Invalid {header_name} header: {reason}",
        {"header": header_name, "reason": reason},
    )


def error_rate_limit_exceeded(
    limit_type: str,
    current_value: int,
    limit: int,
) -> Tuple[int, Dict[str, Any]]:
    """Rate limit exceeded."""
    return create_error_response(
        ErrorCode.RATE_LIMIT_EXCEEDED,
        f"{limit_type} rate limit exceeded: {current_value}/{limit}",
        {
            "limit_type": limit_type,
            "current": current_value,
            "limit": limit,
        },
    )


def error_authentication_failed(reason: str = None) -> Tuple[int, Dict[str, Any]]:
    """Authentication failed."""
    message = f"Authentication failed: {reason}" if reason else "Authentication failed"
    return create_error_response(
        ErrorCode.AUTHENTICATION_FAILED,
        message,
        {"reason": reason} if reason else {},
    )


def error_service_unavailable(service: str = None) -> Tuple[int, Dict[str, Any]]:
    """Service unavailable."""
    message = f"{service} service unavailable" if service else "Service unavailable"
    return create_error_response(
        ErrorCode.SERVICE_UNAVAILABLE,
        message,
        {"service": service} if service else {},
    )


def error_internal_error(reason: str = None) -> Tuple[int, Dict[str, Any]]:
    """Internal server error."""
    message = f"Internal error: {reason}" if reason else "Internal server error"
    return create_error_response(
        ErrorCode.INTERNAL_ERROR,
        message,
        {"reason": reason} if reason else {},
    )


__all__ = [
    "ErrorCode",
    "create_error_response",
    "error_invalid_api_key",
    "error_missing_header",
    "error_invalid_header",
    "error_rate_limit_exceeded",
    "error_authentication_failed",
    "error_service_unavailable",
    "error_internal_error",
]
