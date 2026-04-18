"""
Asynchronous trace buffer flusher.

Periodically retries submission of buffered traces to Langfuse.
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime
from .trace_buffer import TraceBuffer
from .trace_client import TraceClient


class TraceBufferFlusher:
    """Manages periodic flushing of buffered traces."""
    
    def __init__(
        self,
        trace_buffer: TraceBuffer,
        trace_client: TraceClient,
        flush_interval_seconds: int = 60,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize buffer flusher.
        
        Args:
            trace_buffer: TraceBuffer instance
            trace_client: TraceClient instance
            flush_interval_seconds: Interval between flush attempts
            logger: Optional logger instance
        """
        self.trace_buffer = trace_buffer
        self.trace_client = trace_client
        self.flush_interval = flush_interval_seconds
        self.logger = logger or logging.getLogger(__name__)
        self._running = False
        self._task = None
    
    async def start(self):
        """Start the buffer flusher background task."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._flush_loop())
        self.logger.info("Trace buffer flusher started")
    
    async def stop(self):
        """Stop the buffer flusher background task."""
        self._running = False
        if self._task:
            await self._task
        self.logger.info("Trace buffer flusher stopped")
    
    async def _flush_loop(self):
        """Main flush loop."""
        while self._running:
            try:
                await self.flush_buffer()
                await asyncio.sleep(self.flush_interval)
            except Exception as e:
                self.logger.error(f"Error in buffer flush loop: {e}")
                await asyncio.sleep(self.flush_interval)
    
    async def flush_buffer(self):
        """Flush all ready buffered traces."""
        traces = self.trace_buffer.read_buffered_traces()
        
        if not traces:
            return
        
        current_time = datetime.utcnow()
        
        for entry in traces:
            trace = entry.get('trace')
            next_retry_at = entry.get('next_retry_at')
            retry_count = entry.get('retry_count', 0)
            
            # Check if ready to retry
            if next_retry_at:
                try:
                    retry_time = datetime.fromisoformat(next_retry_at.replace('Z', '+00:00'))
                    if current_time < retry_time:
                        continue  # Not ready yet
                except Exception:
                    pass  # If parsing fails, retry anyway
            
            # Attempt submission
            success, error = await self.trace_client.submit_trace(trace)
            
            if success:
                self.logger.info(
                    f"Buffered trace submitted successfully: {trace.get('trace_id')}"
                )
                self.trace_buffer.remove_buffered_trace(trace.get('trace_id'))
            else:
                self.logger.warning(
                    f"Failed to submit buffered trace {trace.get('trace_id')}: {error}"
                )
                # Trace remains in buffer for next retry


def create_flusher(
    buffer_dir: str = "/app/data/trace_buffer",
    langfuse_host: str = "http://langfuse:3000",
    public_key: str = "",
    flush_interval: int = 60,
    logger: Optional[logging.Logger] = None,
) -> TraceBufferFlusher:
    """
    Factory function to create a configured buffer flusher.
    
    Args:
        buffer_dir: Path to trace buffer directory
        langfuse_host: Langfuse API host
        public_key: Langfuse public key
        flush_interval: Flush interval in seconds
        logger: Optional logger
    
    Returns:
        Configured TraceBufferFlusher instance
    """
    buffer = TraceBuffer(buffer_dir=buffer_dir)
    client = TraceClient(
        langfuse_host=langfuse_host,
        public_key=public_key,
        secret_key="",  # Not used yet
    )
    
    return TraceBufferFlusher(
        trace_buffer=buffer,
        trace_client=client,
        flush_interval_seconds=flush_interval,
        logger=logger,
    )


__all__ = [
    "TraceBufferFlusher",
    "create_flusher",
]
