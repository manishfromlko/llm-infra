"""
Latency measurement and tracking.

Measures queue time, inference time, and total latency for requests.
"""
from typing import Tuple
from .langfuse_schema import LatencyBreakdown
import time


def calculate_latency_breakdown(
    start_time: float,
    end_time: float,
    queue_start: float = None,
    inference_start: float = None,
) -> LatencyBreakdown:
    """
    Calculate latency breakdown in milliseconds.
    
    Args:
        start_time: Unix timestamp (seconds) when request was received
        end_time: Unix timestamp (seconds) when response was received
        queue_start: Unix timestamp when inference started (optional)
        inference_start: Unix timestamp when inference started (optional)
    
    Returns:
        LatencyBreakdown with queue_ms, inference_ms, total_ms
    """
    total_ms = int((end_time - start_time) * 1000)
    
    # Calculate queue and inference times if available
    if queue_start and inference_start:
        queue_ms = int((inference_start - queue_start) * 1000)
        inference_ms = int((end_time - inference_start) * 1000)
    else:
        # Estimate: assume 80% inference, 20% queue (conservative estimate)
        queue_ms = int(total_ms * 0.2)
        inference_ms = int(total_ms * 0.8)
    
    # Validate values
    queue_ms = max(0, queue_ms)
    inference_ms = max(0, inference_ms)
    
    # Ensure total is consistent
    calculated_total = queue_ms + inference_ms
    if abs(calculated_total - total_ms) > 5:  # Allow 5ms tolerance for rounding
        inference_ms = total_ms - queue_ms
    
    return LatencyBreakdown(
        queue_ms=queue_ms,
        inference_ms=inference_ms,
        total_ms=total_ms,
    )


def get_current_timestamp() -> float:
    """
    Get current Unix timestamp (seconds since epoch).
    
    Returns:
        Current time as float (seconds)
    """
    return time.time()


class LatencyTracker:
    """Context manager for tracking request latency."""
    
    def __init__(self):
        """Initialize tracker."""
        self.start_time = None
        self.queue_start = None
        self.inference_start = None
        self.end_time = None
    
    def __enter__(self):
        """Start tracking on context entry."""
        self.start_time = get_current_timestamp()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Record end time on context exit."""
        self.end_time = get_current_timestamp()
        return False
    
    def mark_inference_start(self):
        """Mark when inference phase begins (end of queue phase)."""
        self.inference_start = get_current_timestamp()
    
    def get_breakdown(self) -> LatencyBreakdown:
        """Get latency breakdown."""
        if not self.end_time:
            self.end_time = get_current_timestamp()
        
        return calculate_latency_breakdown(
            self.start_time,
            self.end_time,
            self.queue_start,
            self.inference_start,
        )


__all__ = [
    "calculate_latency_breakdown",
    "get_current_timestamp",
    "LatencyTracker",
]
