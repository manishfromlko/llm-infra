"""
Structured JSON logging for gateway operations.

All logs include metadata fields for tracing and debugging.
"""
import json
import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add custom attributes if present
        if hasattr(record, 'team_id'):
            log_obj['team_id'] = record.team_id
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
        if hasattr(record, 'correlation_id'):
            log_obj['correlation_id'] = record.correlation_id
        if hasattr(record, 'trace_id'):
            log_obj['trace_id'] = record.trace_id
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)


def configure_json_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Configure and return a JSON-formatted logger.
    
    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger with JSON formatter
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add JSON formatter handler to stdout
    handler = logging.StreamHandler(sys.stdout)
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


def log_with_metadata(
    logger: logging.Logger,
    level: str,
    message: str,
    team_id: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> None:
    """
    Log message with metadata context.
    
    Args:
        logger: Logger instance
        level: Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        team_id: Optional team identifier
        user_id: Optional user identifier
        request_id: Optional request identifier
        correlation_id: Optional correlation identifier
        trace_id: Optional trace identifier
    """
    log_func = getattr(logger, level.lower())
    
    # Create LogRecord with custom attributes
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level),
        "(trace)",
        0,
        message,
        (),
        None
    )
    
    # Attach metadata
    if team_id:
        record.team_id = team_id
    if user_id:
        record.user_id = user_id
    if request_id:
        record.request_id = request_id
    if correlation_id:
        record.correlation_id = correlation_id
    if trace_id:
        record.trace_id = trace_id
    
    logger.handle(record)


__all__ = [
    "configure_json_logger",
    "log_with_metadata",
    "JSONFormatter",
]
